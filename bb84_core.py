from dataclasses import dataclass, field
from enum import Enum, IntEnum
import math
import random
from typing import Optional
import copy

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
    manual_alice_bits: Optional[list[int]] = None
    manual_alice_bases: Optional[list[Basis]] = None
    manual_bob_bases: Optional[list[Basis]] = None
    manual_eve_bases: Optional[list[Basis]] = None


@dataclass
class SimState:
    step: Step = Step.SETUP
    config: SimConfig = field(default_factory=SimConfig)

    alice_bits: list[int] = field(default_factory=list)
    alice_bases: list[Basis] = field(default_factory=list)
    photons: list[Photon] = field(default_factory=list)

    eve_bits: list[Optional[int]] = field(default_factory=list)
    eve_bases: list[Optional[Basis]] = field(default_factory=list)
    sent_photons: list[Photon] = field(default_factory=list)

    bob_bits: list[int] = field(default_factory=list)
    bob_bases: list[Basis] = field(default_factory=list)

    sifted_indices: list[int] = field(default_factory=list)
    sample_indices: list[int] = field(default_factory=list)

    qber: Optional[float] = None
    expected_qber: Optional[float] = None
    key_accepted: Optional[bool] = None
    final_key: Optional[list[int]] = None

def get_rng(seed: Optional[int] = None) -> random.Random:
    return random.Random(seed)

def eve_intercept(photon: Photon, eve_basis: Basis, rng: random.Random) -> tuple[int, Photon]:
    bit, collapsed = measure_photon(photon, eve_basis, rng)
    return bit, collapsed

def should_intercept(config: SimConfig, rng: random.Random) -> bool:
    return config.eve_present and rng.random() < config.eve_ratio

def choose_eve_bases(n: int, config: SimConfig, rng: random.Random) -> list[Basis]:
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

def send_and_measure(
    photon: Photon,
    bob_basis: Basis,
    config: SimConfig,
    rng: random.Random,
    eve_basis: Optional[Basis] = None,
) -> tuple[Photon, Optional[Basis], Optional[int], Photon, int]:
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
    return photon, eve_basis, eve_bit, current_photon, bob_bit

def sift(alice_bases: list[Basis], bob_bases: list[Basis]) -> list[int]:
    return [i for i in range(min(len(alice_bases), len(bob_bases)))
            if alice_bases[i] == bob_bases[i]]

def select_sample(sifted_indices: list[int], sample_ratio: float, rng: random.Random) -> list[int]:
    if not sifted_indices or sample_ratio <= 0:
        return []

    k = max(1, round(len(sifted_indices) * sample_ratio))
    k = min(k, len(sifted_indices))

    return sorted(rng.sample(sifted_indices, k))

def estimate_qber(alice_bits: list[int], bob_bits: list[int], sample_indices: list[int]) -> float:
    if not sample_indices:
        return 0.0
    else:
        errors = sum([1 for i in sample_indices if alice_bits[i] != bob_bits[i]])
        return errors / len(sample_indices)

def extract_final_key(alice_bits: list[int], sifted_indices: list[int], sample_indices: list[int]) -> list[int]:
    sample_set = set(sample_indices)
    return [alice_bits[i] for i in sifted_indices if i not in sample_set]

def expected_qber(config: SimConfig) -> float:
    eve_contribution = (config.eve_ratio * 0.25) if config.eve_present else 0.0
    return min(1.0, eve_contribution + config.noise_rate)


def undetected_probability(sample_size: int) -> float:
    return (0.75) ** sample_size

def parse_bits(text: str, expected_len: Optional[int] = None) -> list[int]:
    bit_text = text.strip()
    if not bit_text:
        raise ValueError("A bitlánc nem lehet üres!")

    bits = []
    for c in bit_text:
        if c == '0':
            bits.append(0)
        elif c == '1':
            bits.append(1)
        else:
            raise ValueError(f"Érvénytelen karakter a bitláncban: '{c}'. Csak '0' és '1' megengedett.")

    if expected_len is not None and len(bits) != expected_len:
        raise ValueError(f"A megadott bitek száma ({len(bits)}) nem egyezik az elvárt hosszal ({expected_len}).")

    return bits

def parse_bases(text: str, expected_len: Optional[int] = None) -> list[Basis]:
    base_text = text.strip()
    if not base_text:
        raise ValueError("A bázislánc nem lehet üres!")

    bases = []
    for c in base_text:
        if c == '+':
            bases.append(Basis.RECTILINEAR)
        elif c in ('x', 'X'):
            bases.append(Basis.DIAGONAL)
        else:
            raise ValueError(f"Érvénytelen báziskarakter a bázisláncban: '{c}'. Csak '+' és 'x' megengedett.")

    if expected_len is not None and len(bases) != expected_len:
        raise ValueError(
            f"A megadott bázisok száma ({len(bases)}) nem egyezik az elvárt hosszal ({expected_len})."
        )

    return bases


class BB84Simulation:
    def __init__(self, config: Optional[SimConfig] = None):
        if config is None:
            config = SimConfig()
        self.config = config
        self.rng = get_rng(config.seed)
        self._state = SimState(step=Step.SETUP, config=config)
        self._history: list[tuple[SimState, tuple]] = []

    @property
    def state(self) -> SimState:
        return self._state

    @property
    def step(self) -> Step:
        return self._state.step

    def prev_step(self):
        if not self._history:
            return
        previous_state, previous_rng_state = self._history.pop()
        self._state = previous_state
        self.rng.setstate(previous_rng_state)

    def reset(self):
        self._history.clear()
        self.rng = get_rng(self.config.seed)
        self._state = SimState(step=Step.SETUP, config=self.config)

    def next_step(self):
        if self._state.step == Step.RESULT:
            return
        self._history.append((copy.deepcopy(self._state), self.rng.getstate()))

        n = self.config.n_bits
        
        match self._state.step:
            case Step.SETUP:
                if self.config.manual_alice_bits is not None:
                    self._state.alice_bits = list(self.config.manual_alice_bits)
                else:
                    self._state.alice_bits = [self.rng.choice([0, 1]) for _ in range(n)]
                self._state.step = Step.ALICE_BITS
            case Step.ALICE_BITS:
                if self.config.manual_alice_bases is not None:
                    self._state.alice_bases = list(self.config.manual_alice_bases)
                else:
                    self._state.alice_bases = [self.rng.choice(list(Basis)) for _ in range(n)]
                self._state.step = Step.ALICE_BASES
            case Step.ALICE_BASES:
                self._state.photons = [
                    encode_photon(bit, basis)
                    for bit, basis in zip(self._state.alice_bits, self._state.alice_bases)
                ]
                self._state.step = Step.ENCODE
            case Step.ENCODE:
                self._state.eve_bases = []
                self._state.eve_bits = []
                self._state.sent_photons = []
                for i, photon in enumerate(self._state.photons):
                    if should_intercept(self.config, self.rng):
                        if self.config.manual_eve_bases and i < len(self.config.manual_eve_bases):
                            e_basis = self.config.manual_eve_bases[i]
                        else:
                            e_basis = self.rng.choice(list(Basis))
                        e_bit, collapsed = eve_intercept(photon, e_basis, self.rng)
                        self._state.eve_bases.append(e_basis)
                        self._state.eve_bits.append(e_bit)
                        transmitted = collapsed
                    else:
                        self._state.eve_bases.append(None)
                        self._state.eve_bits.append(None)
                        transmitted = photon
                    transmitted = apply_noise(transmitted, self.config.noise_rate, self.rng)
                    self._state.sent_photons.append(transmitted)
                self._state.step = Step.TRANSMIT
            case Step.TRANSMIT:
                if self.config.manual_bob_bases is not None:
                    self._state.bob_bases = list(self.config.manual_bob_bases)
                else:
                    self._state.bob_bases = [self.rng.choice(list(Basis)) for _ in range(n)]
                self._state.step = Step.BOB_BASES
            case Step.BOB_BASES:
                self._state.bob_bits = []
                for photon, basis in zip(self._state.sent_photons, self._state.bob_bases):
                    bit, _ = measure_photon(photon, basis, self.rng)
                    self._state.bob_bits.append(bit)
                self._state.step = Step.BOB_MEASURE
            case Step.BOB_MEASURE:
                self._state.sifted_indices = sift(self._state.alice_bases, self._state.bob_bases)
                self._state.step = Step.SIFTING
            case Step.SIFTING:
                self._state.sample_indices = select_sample(
                    self._state.sifted_indices, self.config.sample_ratio, self.rng
                )
                self._state.qber = estimate_qber(
                    self._state.alice_bits, self._state.bob_bits, self._state.sample_indices
                )
                self._state.expected_qber = expected_qber(self.config)
                self._state.step = Step.QBER
            case Step.QBER:
                has_key = bool(self._state.sifted_indices) and len(self._state.sifted_indices) > len(self._state.sample_indices)
                if has_key and self._state.qber is not None and self._state.qber <= self.config.qber_threshold:
                    self._state.key_accepted = True
                    self._state.final_key = extract_final_key(
                        self._state.alice_bits,
                        self._state.sifted_indices,
                        self._state.sample_indices
                    )
                else:
                    self._state.key_accepted = False
                    self._state.final_key = []
                self._state.step = Step.RESULT
    
    def run_to_end(self):
        while self._state.step != Step.RESULT:
            self.next_step()
