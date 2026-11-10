from dataclasses import dataclass, field
from enum import Enum, IntEnum
import math
import random
from typing import List, Optional

class Basis(str, Enum):
    RECTILINEAR = "+"
    DIAGONAL = "x"

class Step(IntEnum):
    SETUP = 0
    ALICE_BITS = 1
    ALICE_BASES = 2
    ENCODE = 3
    TRANSMIT = 4
    BOB_BASES = 5
    BOB_MEASURE = 6
    SIFTING = 7
    QBER = 8
    RESULT = 9

@dataclass(frozen=True)
class Photon:
    angle: float
    symbol: str

    @property
    def state_vector(self) -> tuple[float, float]:
        rad = math.radians(self.angle)
        return (math.cos(rad), math.sin(rad))

@dataclass
class SimConfig:
    n_bits: int = 32
    eve_present: bool = False
    eve_ratio: float = 1.0
    noise_rate: float = 0.0
    sample_ratio: float = 0.25
    qber_threshold: float = 0.11
    seed: Optional[int] = None
    manual_alice_bits: Optional[List[int]] = None
    manual_alice_bases: Optional[List[Basis]] = None
    manual_bob_bases: Optional[List[Basis]] = None
    manual_eve_bases: Optional[List[Basis]] = None


#Az adott állapotnak a gui-nak küldött adatai
@dataclass
class SimState:
    step: Step = Step.SETUP
    config: SimConfig = field(default_factory=SimConfig)

    #Alice adatai
    alice_bits: List[int] = field(default_factory=list)
    alice_bases: List[Basis] = field(default_factory=list)
    photons: List[Photon] = field(default_factory=list)

    #Eve adatai 
    eve_bits: List[Optional[int]] = field(default_factory=list)
    eve_bases: List[Optional[Basis]] = field(default_factory=list)
    sent_photons: List[Photon] = field(default_factory=list)

    #Bob adatai
    bob_bits: List[int] = field(default_factory=list)
    bob_bases: List[Basis] = field(default_factory=list)

    #Utofeldolgozas
    sifted_indices: List[int] = field(default_factory=list)
    sample_indices: List[int] = field(default_factory=list)

    #Eredmenyek
    qber: Optional[float] = None
    expected_qber: Optional[float] = None
    key_accepted: Optional[bool] = None
    final_key: Optional[List[int]] = None

def get_rng(seed: Optional[int] = None) -> random.Random:
    return random.Random(seed)

def eve_intercept(photon, eve_basis, rng):
    bit, collapsed = measure_photon(photon, eve_basis, rng)
    return bit, collapsed

def should_intercept(config, rng) -> bool:
    return config.eve_present and rng.random() < config.eve_ratio

def choose_eve_bases(n, config, rng) -> list[Basis]:
    if config.manual_eve_bases is not None:
        return config.manual_eve_bases
    else:
        return [rng.choice(list(Basis)) for _ in range(n)]
def encode_photon(bit: int, basis: Basis) -> Photon:
    if basis == Basis.RECTILINEAR and bit == 0:
        return Photon(0, "→")
    elif basis == Basis.RECTILINEAR and bit == 1:
        return Photon(90, "↑")
    elif basis == Basis.DIAGONAL and bit == 0:
        return Photon(45, "↗")
    elif basis == Basis.DIAGONAL and bit == 1:
        return Photon(135, "↖")

def measure_photon(photon: Photon, basis: Basis, rng: random.Random) -> tuple[int, Photon]:
    statevector = encode_photon(0, basis=basis).state_vector
    px, py = photon.state_vector
    dot_product = statevector[0]*px + statevector[1]*py
    p = round(dot_product**2, 9)
    if p > 1.0:
        p = 1.0
    elif p < 0.0:
        p = 0.0
    if rng.random() < p:
        bit = 0
    else:
        bit = 1

    collapsed = encode_photon(bit=bit, basis=basis)
    return bit, collapsed

def apply_noise(photon: Photon, noise_rate: float, rng: random.Random) -> Photon:
    if rng.random() < noise_rate:
        new_angle = (photon.angle+90) % 180
        if new_angle == 0:
            new_symbol = "→"
        elif new_angle == 45:
            new_symbol = "↗"
        elif new_angle == 90:
            new_symbol = "↑"
        elif new_angle == 135:
            new_symbol = "↖"
        return Photon(new_angle, new_symbol)
    else:
        return photon

def send_and_measure(photon:Photon, bob_basis: Basis, config: SimConfig, rng: random.Random, eve_basis: Optional[Basis]=None):
    if should_intercept(config=config, rng=rng):
        if eve_basis is None:
            eve_basis = rng.choice(list(Basis))
        eve_bit, current_photon = eve_intercept(photon=photon, eve_basis=eve_basis, rng=rng)
    else:
        eve_basis = None
        eve_bit = None
        current_photon = photon
    
    current_photon = apply_noise(current_photon, config.noise_rate, rng)
    bob_bit, _ = measure_photon(current_photon, bob_basis, rng)
    return photon,eve_basis, eve_bit, current_photon, bob_bit

def sifting(alice_bases: list[Basis], bob_bases: list[Basis]) -> list[int]:
    return [i for i in range(min(len(alice_bases), len(bob_bases)))
            if alice_bases[i] == bob_bases[i]]

def sample_qber(sift_indices, sample_ratio, rng) -> list[int]:
    if not sift_indices or sample_ratio <= 0:
        return []

    k = max(1, round(len(sift_indices) * sample_ratio))
    k = min(k, len(sift_indices))

    return sorted(rng.sample(sift_indices, k))

def estimate_qber(alice_bits, bob_bits, sample_indices) -> float:
    if not sample_indices:
        return 0.0
    else:
        errors = sum([1 for i in sample_indices if alice_bits[i] != bob_bits[i]])
        return errors / len(sample_indices)

def get_final_key(alice_bits, sift_indices, sample_indices):
    return [alice_bits[i] for i in sift_indices if i not in sample_indices]

def calculate_expected_qber(config: SimConfig) -> float:
    eve_contribution = (config.eve_ratio * 0.25) if config.eve_present else 0.0
    return min(1.0, eve_contribution + config.noise_rate)


def calculate_undetected_probability(sample_size: int) -> float:
    return (0.75) ** sample_size