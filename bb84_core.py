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
    bit, collapsed = measure(photon, eve_basis, rng)
    return bit, collapsed

def should_intercept(config, rng) -> bool:
    return config.eve_present and rng.random() < config.eve_ratio

def choose_eve_bases(n, config, rng) -> list[Basis]:
    if config.manual_eve_bases is not None:
        return config.manual_eve_bases
    else:
        return [rng.choice(list(Basis)) for _ in range(n)]