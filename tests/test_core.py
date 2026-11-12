"""A bb84_core.py teljes tesztkészlete (Q1-Q7).

Futtatás a projekt gyökeréből:  python -m pytest -v
"""
import math

import pytest

from bb84_core import (
    BB84Simulation,
    Basis,
    Photon,
    SimConfig,
    SimState,
    Step,
    apply_noise,
    expected_qber,
    undetected_probability,
    choose_eve_bases,
    parse_bases,
    parse_bits,
    encode_photon,
    estimate_qber,
    eve_intercept,
    extract_final_key,
    get_rng,
    measure_photon,
    select_sample,
    send_and_measure,
    should_intercept,
    sift,
)

PLUS = Basis.RECTILINEAR
CROSS = Basis.DIAGONAL
ALL_CASES = [(bit, basis) for bit in (0, 1) for basis in (PLUS, CROSS)]


def other(basis: Basis) -> Basis:
    return CROSS if basis == PLUS else PLUS


# =====================================================================
# Q1 - Adatmodell, RNG
# =====================================================================
class TestQ1DataModel:
    def test_basis_values(self):
        assert PLUS.value == "+"
        assert CROSS.value == "x"
        assert len(list(Basis)) == 2

    def test_step_has_10_ordered_states(self):
        assert [s.value for s in Step] == list(range(10))
        assert Step.SETUP == 0 and Step.RESULT == 9

    @pytest.mark.parametrize(
        "angle, expected",
        [(0, (1.0, 0.0)), (90, (0.0, 1.0)), (45, (math.sqrt(0.5), math.sqrt(0.5))),
         (135, (-math.sqrt(0.5), math.sqrt(0.5)))],
    )
    def test_photon_state_vector(self, angle, expected):
        x, y = Photon(angle, "?").state_vector
        assert x == pytest.approx(expected[0], abs=1e-9)
        assert y == pytest.approx(expected[1], abs=1e-9)

    def test_photon_state_vector_is_unit_length(self):
        for angle in (0, 45, 90, 135):
            x, y = Photon(angle, "?").state_vector
            assert x * x + y * y == pytest.approx(1.0)

    def test_photon_is_immutable(self):
        p = Photon(0, "→")
        with pytest.raises(Exception):
            p.angle = 90  # type: ignore[misc]

    def test_simconfig_defaults(self):
        c = SimConfig()
        assert c.n_bits == 32
        assert c.eve_present is False
        assert c.sample_ratio == 0.25
        assert c.qber_threshold == 0.11
        assert c.manual_alice_bits is None

    def test_simstate_defaults_are_independent(self):
        a, b = SimState(), SimState()
        a.alice_bits.append(1)
        assert b.alice_bits == []  # nincs közös mutable default
        assert a.step == Step.SETUP

    def test_rng_same_seed_same_sequence(self):
        r1, r2 = get_rng(42), get_rng(42)
        assert [r1.random() for _ in range(20)] == [r2.random() for _ in range(20)]

    def test_rng_different_seed_different_sequence(self):
        r1, r2 = get_rng(1), get_rng(2)
        assert [r1.random() for _ in range(20)] != [r2.random() for _ in range(20)]


# =====================================================================
# Q2 - Kódolás, mérés (Born-szabály, összeomlás)
# =====================================================================
class TestQ2EncodeMeasure:
    @pytest.mark.parametrize(
        "bit, basis, angle, symbol",
        [(0, PLUS, 0, "→"), (1, PLUS, 90, "↑"), (0, CROSS, 45, "↗"), (1, CROSS, 135, "↖")],
    )
    def test_encode_table(self, bit, basis, angle, symbol):
        p = encode_photon(bit, basis)
        assert p.angle == angle
        assert p.symbol == symbol

    @pytest.mark.parametrize("bit, basis", ALL_CASES)
    def test_same_basis_measurement_is_deterministic(self, bit, basis):
        rng = get_rng(0)
        photon = encode_photon(bit, basis)
        for _ in range(500):
            measured, _ = measure_photon(photon, basis, rng)
            assert measured == bit

    @pytest.mark.parametrize("bit, basis", ALL_CASES)
    def test_different_basis_is_50_50(self, bit, basis):
        """Projektterv Q2 'Kész, ha': eltérő bázisnál 50 ± 3% (N = 10 000)."""
        rng = get_rng(123)
        photon = encode_photon(bit, basis)
        n = 10_000
        zeros = sum(1 for _ in range(n) if measure_photon(photon, other(basis), rng)[0] == 0)
        assert abs(zeros / n - 0.5) <= 0.03

    @pytest.mark.parametrize("bit, basis", ALL_CASES)
    def test_measurement_collapses_into_measured_basis(self, bit, basis):
        rng = get_rng(7)
        photon = encode_photon(bit, basis)
        for b in (PLUS, CROSS):
            for _ in range(50):
                measured, collapsed = measure_photon(photon, b, rng)
                assert collapsed == encode_photon(measured, b)

    def test_repeated_measurement_after_collapse_is_stable(self):
        rng = get_rng(9)
        photon = encode_photon(0, PLUS)
        for _ in range(200):
            first, collapsed = measure_photon(photon, CROSS, rng)
            second, _ = measure_photon(collapsed, CROSS, rng)
            assert first == second


# =====================================================================
# Q3 - Eve intercept-resend
# =====================================================================
class TestQ3Eve:
    def test_should_intercept_never_when_eve_absent(self):
        rng = get_rng(1)
        cfg = SimConfig(eve_present=False, eve_ratio=1.0)
        assert not any(should_intercept(cfg, rng) for _ in range(1000))

    def test_should_intercept_always_at_ratio_1(self):
        rng = get_rng(1)
        cfg = SimConfig(eve_present=True, eve_ratio=1.0)
        assert all(should_intercept(cfg, rng) for _ in range(1000))

    def test_should_intercept_never_at_ratio_0(self):
        rng = get_rng(1)
        cfg = SimConfig(eve_present=True, eve_ratio=0.0)
        assert not any(should_intercept(cfg, rng) for _ in range(1000))

    def test_should_intercept_follows_ratio(self):
        rng = get_rng(5)
        cfg = SimConfig(eve_present=True, eve_ratio=0.3)
        n = 10_000
        hits = sum(should_intercept(cfg, rng) for _ in range(n))
        assert abs(hits / n - 0.3) <= 0.03

    def test_choose_eve_bases_manual(self):
        manual = [PLUS, CROSS, CROSS]
        cfg = SimConfig(manual_eve_bases=manual)
        assert choose_eve_bases(3, cfg, get_rng(0)) == manual

    def test_choose_eve_bases_random(self):
        bases = choose_eve_bases(200, SimConfig(), get_rng(0))
        assert len(bases) == 200
        assert set(bases) == {PLUS, CROSS}
        assert bases == choose_eve_bases(200, SimConfig(), get_rng(0))  # seed -> reprodukálható

    @pytest.mark.parametrize("bit, basis", ALL_CASES)
    def test_eve_right_basis_does_not_disturb(self, bit, basis):
        rng = get_rng(3)
        photon = encode_photon(bit, basis)
        eve_bit, resent = eve_intercept(photon, basis, rng)
        assert eve_bit == bit
        assert resent == photon

    @pytest.mark.parametrize("bit, basis", ALL_CASES)
    def test_eve_wrong_basis_resends_in_her_basis(self, bit, basis):
        rng = get_rng(3)
        photon = encode_photon(bit, basis)
        for _ in range(50):
            eve_bit, resent = eve_intercept(photon, other(basis), rng)
            assert resent == encode_photon(eve_bit, other(basis))

    def test_send_and_measure_without_eve(self):
        rng = get_rng(0)
        cfg = SimConfig(eve_present=False)
        photon = encode_photon(1, CROSS)
        orig, e_basis, e_bit, sent, bob_bit = send_and_measure(photon, CROSS, cfg, rng)
        assert orig == photon
        assert e_basis is None and e_bit is None
        assert sent == photon
        assert bob_bit == 1

    def test_send_and_measure_with_manual_eve_basis(self):
        rng = get_rng(0)
        cfg = SimConfig(eve_present=True, eve_ratio=1.0)
        photon = encode_photon(0, PLUS)
        _, e_basis, e_bit, sent, _ = send_and_measure(photon, PLUS, cfg, rng, eve_basis=CROSS)
        assert e_basis == CROSS
        assert e_bit in (0, 1)
        assert sent == encode_photon(e_bit, CROSS)

    @pytest.mark.parametrize("ratio, expected", [(0.0, 0.0), (0.5, 0.125), (1.0, 0.25)])
    def test_send_and_measure_qber_statistics(self, ratio, expected):
        """Projektterv Q3 'Kész, ha': teljes lehallgatásnál QBER ≈ 25%, Eve nélkül 0%."""
        rng = get_rng(2024)
        cfg = SimConfig(eve_present=ratio > 0, eve_ratio=ratio)
        errors = kept = 0
        for _ in range(20_000):
            a_bit, a_basis, b_basis = rng.randint(0, 1), rng.choice(list(Basis)), rng.choice(list(Basis))
            *_, bob_bit = send_and_measure(encode_photon(a_bit, a_basis), b_basis, cfg, rng)
            if a_basis == b_basis:
                kept += 1
                errors += bob_bit != a_bit
        assert abs(errors / kept - expected) <= 0.02


# =====================================================================
# Q4 - Csatornazaj
# =====================================================================
class TestQ4Noise:
    @pytest.mark.parametrize("bit, basis", ALL_CASES)
    def test_no_noise_keeps_photon(self, bit, basis):
        rng = get_rng(0)
        photon = encode_photon(bit, basis)
        assert all(apply_noise(photon, 0.0, rng) == photon for _ in range(200))

    @pytest.mark.parametrize("bit, basis", ALL_CASES)
    def test_full_noise_flips_to_orthogonal(self, bit, basis):
        rng = get_rng(0)
        flipped = apply_noise(encode_photon(bit, basis), 1.0, rng)
        assert flipped == encode_photon(1 - bit, basis)  # szög és szimbólum is

    def test_noise_rate_statistics(self):
        rng = get_rng(11)
        photon = encode_photon(0, PLUS)
        n = 10_000
        flips = sum(apply_noise(photon, 0.2, rng) != photon for _ in range(n))
        assert abs(flips / n - 0.2) <= 0.02

    def test_qber_equals_noise_without_eve(self):
        """Projektterv Q4 'Kész, ha': Eve nélkül a QBER ≈ a zaj értéke."""
        rng = get_rng(77)
        cfg = SimConfig(eve_present=False, noise_rate=0.1)
        errors = kept = 0
        for _ in range(20_000):
            a_bit, a_basis, b_basis = rng.randint(0, 1), rng.choice(list(Basis)), rng.choice(list(Basis))
            *_, bob_bit = send_and_measure(encode_photon(a_bit, a_basis), b_basis, cfg, rng)
            if a_basis == b_basis:
                kept += 1
                errors += bob_bit != a_bit
        assert abs(errors / kept - 0.1) <= 0.02


# =====================================================================
# Q5 - Sifting, QBER, végső kulcs
# =====================================================================
class TestQ5PostProcessing:
    def test_sifting_known_example(self):
        alice = [PLUS, PLUS, CROSS, CROSS, PLUS]
        bob = [PLUS, CROSS, CROSS, PLUS, PLUS]
        assert sift(alice, bob) == [0, 2, 4]

    def test_sifting_empty_and_disjoint(self):
        assert sift([], []) == []
        assert sift([PLUS, PLUS], [CROSS, CROSS]) == []

    def test_sifting_keeps_about_half(self):
        rng = get_rng(8)
        n = 10_000
        a = [rng.choice(list(Basis)) for _ in range(n)]
        b = [rng.choice(list(Basis)) for _ in range(n)]
        assert abs(len(sift(a, b)) / n - 0.5) <= 0.03

    def test_sample_qber_empty_sifted_no_exception(self):
        assert select_sample([], 0.25, get_rng(0)) == []

    def test_sample_qber_zero_ratio(self):
        assert select_sample([1, 2, 3], 0.0, get_rng(0)) == []

    def test_sample_qber_size_sorted_subset(self):
        sifted = list(range(0, 200, 2))  # 100 elem
        sample = select_sample(sifted, 0.25, get_rng(0))
        assert len(sample) == 25
        assert sample == sorted(sample)
        assert set(sample) <= set(sifted)
        assert len(set(sample)) == len(sample)

    def test_sample_qber_at_least_one(self):
        assert len(select_sample([5], 0.25, get_rng(0))) == 1

    def test_sample_qber_full_ratio_takes_all(self):
        assert select_sample([3, 1, 2], 1.0, get_rng(0)) == [1, 2, 3]

    def test_sample_qber_reproducible(self):
        sifted = list(range(100))
        assert select_sample(sifted, 0.3, get_rng(4)) == select_sample(sifted, 0.3, get_rng(4))

    def test_estimate_qber(self):
        alice = [0, 1, 0, 1, 0]
        bob = [0, 0, 0, 1, 1]
        assert estimate_qber(alice, bob, [0, 1, 2, 3]) == pytest.approx(0.25)
        assert estimate_qber(alice, bob, [1, 4]) == pytest.approx(1.0)
        assert estimate_qber(alice, bob, [0, 2]) == 0.0

    def test_estimate_qber_empty_sample_no_exception(self):
        assert estimate_qber([0, 1], [1, 0], []) == 0.0

    def test_final_key_excludes_sample(self):
        """Projektterv Q5 'Kész, ha': a mintabitek kikerülnek a végső kulcsból."""
        alice = [1, 0, 1, 1, 0, 0]
        sifted = [0, 2, 3, 5]
        sample = [2, 5]
        assert extract_final_key(alice, sifted, sample) == [1, 1]  # 0. és 3. index

    def test_final_key_empty_inputs(self):
        assert extract_final_key([1, 0], [], []) == []

    @pytest.mark.parametrize(
        "present, ratio, noise, expected",
        [(False, 1.0, 0.0, 0.0), (True, 1.0, 0.0, 0.25), (True, 0.5, 0.0, 0.125),
         (True, 0.5, 0.1, 0.225), (False, 1.0, 0.05, 0.05), (True, 1.0, 0.9, 1.0)],
    )
    def test_expected_qber(self, present, ratio, noise, expected):
        cfg = SimConfig(eve_present=present, eve_ratio=ratio, noise_rate=noise)
        assert expected_qber(cfg) == pytest.approx(expected)

    @pytest.mark.parametrize("k, expected", [(0, 1.0), (1, 0.75), (2, 0.5625), (10, 0.75 ** 10)])
    def test_undetected_probability(self, k, expected):
        assert undetected_probability(k) == pytest.approx(expected)


# =====================================================================
# Q7 - Manuális bevitel feldolgozása
# =====================================================================
class TestQ7Parsing:
    def test_bits_valid(self):
        assert parse_bits("0101") == [0, 1, 0, 1]

    def test_bits_strip_whitespace(self):
        assert parse_bits("  110 \n") == [1, 1, 0]

    def test_bits_length_ok(self):
        assert parse_bits("101", expected_len=3) == [1, 0, 1]

    @pytest.mark.parametrize("text", ["", "   "])
    def test_bits_empty(self, text):
        with pytest.raises(ValueError, match="üres"):
            parse_bits(text)

    @pytest.mark.parametrize("text, bad", [("01a1", "a"), ("0121", "2"), ("0+1", "+"), ("0 1", " ")])
    def test_bits_invalid_char(self, text, bad):
        with pytest.raises(ValueError, match="Érvénytelen karakter") as exc:
            parse_bits(text)
        assert f"'{bad}'" in str(exc.value)

    def test_bits_wrong_length(self):
        with pytest.raises(ValueError, match="nem egyezik"):
            parse_bits("0101", expected_len=5)

    def test_bases_valid(self):
        assert parse_bases("+x+X") == [PLUS, CROSS, PLUS, CROSS]

    def test_bases_length_ok(self):
        assert parse_bases("++", expected_len=2) == [PLUS, PLUS]

    @pytest.mark.parametrize("text", ["", "  "])
    def test_bases_empty(self, text):
        with pytest.raises(ValueError, match="bázislánc nem lehet üres"):
            parse_bases(text)

    @pytest.mark.parametrize("text, bad", [("+x-", "-"), ("+0", "0"), ("abc", "a")])
    def test_bases_invalid_char(self, text, bad):
        with pytest.raises(ValueError, match="Érvénytelen báziskarakter") as exc:
            parse_bases(text)
        assert f"'{bad}'" in str(exc.value)

    def test_bases_wrong_length(self):
        with pytest.raises(ValueError, match="nem egyezik"):
            parse_bases("+x", expected_len=3)


# =====================================================================
# Q6 - Állapotgép (BB84Simulation) + integráció
# =====================================================================
def make_sim(**kwargs) -> BB84Simulation:
    kwargs.setdefault("seed", 42)
    return BB84Simulation(SimConfig(**kwargs))


class TestQ6StateMachine:
    def test_initial_state(self):
        sim = make_sim()
        assert sim.step == Step.SETUP
        assert sim.state.step == Step.SETUP
        assert sim.state.alice_bits == []

    def test_default_config(self):
        sim = BB84Simulation()
        assert sim.config.n_bits == 32

    def test_steps_go_in_order(self):
        sim = make_sim()
        for expected in list(Step)[1:]:
            sim.next_step()
            assert sim.step == expected

    def test_next_at_result_is_noop(self):
        sim = make_sim()
        sim.run_to_end()
        before = sim.state
        sim.next_step()
        assert sim.step == Step.RESULT
        assert sim.state == before

    def test_prev_at_setup_is_noop(self):
        sim = make_sim()
        sim.prev_step()
        assert sim.step == Step.SETUP

    def test_prev_step_restores_previous_state(self):
        sim = make_sim()
        sim.next_step()
        sim.next_step()
        assert sim.state.alice_bases
        sim.prev_step()
        assert sim.step == Step.ALICE_BITS
        assert sim.state.alice_bases == []

    def test_back_then_forward_is_identical_at_every_step(self):
        """Projektterv Q6 'Kész, ha': a Vissza → Előre lépés ugyanazt az eredményt adja."""
        sim = make_sim(n_bits=64, eve_present=True, eve_ratio=0.5, noise_rate=0.05)
        while sim.step != Step.RESULT:
            sim.next_step()
            snapshot = sim.state
            sim.prev_step()
            sim.next_step()
            assert sim.state == snapshot, f"eltérés a(z) {sim.step.name} lépésnél"

    def test_back_all_the_way_then_forward(self):
        sim = make_sim(n_bits=64, eve_present=True)
        sim.run_to_end()
        final = sim.state
        for _ in range(20):
            sim.prev_step()
        assert sim.step == Step.SETUP
        sim.run_to_end()
        assert sim.state == final

    def test_history_snapshot_not_mutated(self):
        sim = make_sim()
        sim.next_step()
        bits = list(sim.state.alice_bits)
        sim.next_step()
        sim.prev_step()
        assert sim.state.alice_bits == bits

    def test_reset(self):
        sim = make_sim(n_bits=50)
        sim.run_to_end()
        final = sim.state
        sim.reset()
        assert sim.step == Step.SETUP
        assert sim.state.alice_bits == []
        sim.prev_step()  # üres history -> nincs hiba
        assert sim.step == Step.SETUP
        sim.run_to_end()
        assert sim.state == final  # azonos seed -> azonos futás

    def test_same_seed_same_run(self):
        a, b = make_sim(n_bits=100, eve_present=True), make_sim(n_bits=100, eve_present=True)
        a.run_to_end()
        b.run_to_end()
        assert a.state == b.state

    def test_different_seed_different_run(self):
        a, b = make_sim(n_bits=100, seed=1), make_sim(n_bits=100, seed=2)
        a.run_to_end()
        b.run_to_end()
        assert a.state.alice_bits != b.state.alice_bits

    def test_all_lists_have_length_n(self):
        n = 40
        sim = make_sim(n_bits=n, eve_present=True, eve_ratio=0.5)
        sim.run_to_end()
        s = sim.state
        for name in ("alice_bits", "alice_bases", "photons", "eve_bits", "eve_bases",
                     "sent_photons", "bob_bits", "bob_bases"):
            assert len(getattr(s, name)) == n, name

    def test_photons_match_alice_encoding(self):
        sim = make_sim(n_bits=30)
        sim.run_to_end()
        s = sim.state
        assert s.photons == [encode_photon(b, ba) for b, ba in zip(s.alice_bits, s.alice_bases)]

    def test_without_eve_eve_columns_empty_and_photons_unchanged(self):
        sim = make_sim(n_bits=50, eve_present=False)
        sim.run_to_end()
        s = sim.state
        assert all(x is None for x in s.eve_bits)
        assert all(x is None for x in s.eve_bases)
        assert s.sent_photons == s.photons

    def test_eve_none_pattern_consistent(self):
        sim = make_sim(n_bits=200, eve_present=True, eve_ratio=0.5)
        sim.run_to_end()
        s = sim.state
        for e_bit, e_basis, orig, sent in zip(s.eve_bits, s.eve_bases, s.photons, s.sent_photons):
            assert (e_bit is None) == (e_basis is None)
            if e_bit is None:
                assert sent == orig  # zaj nélkül változatlan
            else:
                assert sent == encode_photon(e_bit, e_basis)

    def test_no_eve_no_noise_key_accepted(self):
        sim = make_sim(n_bits=200)
        sim.run_to_end()
        s = sim.state
        assert s.qber == 0.0
        assert s.expected_qber == 0.0
        assert s.key_accepted is True
        assert len(s.final_key) == len(s.sifted_indices) - len(s.sample_indices)
        # Alice és Bob kulcsa megegyezik
        bob_key = extract_final_key(s.bob_bits, s.sifted_indices, s.sample_indices)
        assert s.final_key == bob_key

    def test_final_key_has_no_sample_bits(self):
        sim = make_sim(n_bits=200)
        sim.run_to_end()
        s = sim.state
        sample = set(s.sample_indices)
        kept = [i for i in s.sifted_indices if i not in sample]
        assert s.final_key == [s.alice_bits[i] for i in kept]
        assert sample <= set(s.sifted_indices)

    def test_full_eve_key_rejected(self):
        sim = make_sim(n_bits=1000, eve_present=True, eve_ratio=1.0)
        sim.run_to_end()
        s = sim.state
        assert abs(s.qber - 0.25) <= 0.08
        assert s.expected_qber == pytest.approx(0.25)
        assert s.key_accepted is False
        assert s.final_key == []

    def test_manual_inputs_are_used(self):
        bits = [0, 1, 1, 0]
        a_bases = [PLUS, CROSS, PLUS, CROSS]
        sim = make_sim(n_bits=4, manual_alice_bits=bits, manual_alice_bases=a_bases,
                       manual_bob_bases=list(a_bases), sample_ratio=0.25)
        sim.run_to_end()
        s = sim.state
        assert s.alice_bits == bits
        assert s.alice_bases == a_bases
        assert s.bob_bases == a_bases
        assert s.sifted_indices == [0, 1, 2, 3]
        assert s.bob_bits == bits
        assert s.key_accepted is True

    def test_manual_eve_bases_are_used(self):
        eve = [CROSS] * 8
        sim = make_sim(n_bits=8, eve_present=True, eve_ratio=1.0, manual_eve_bases=eve)
        sim.run_to_end()
        assert sim.state.eve_bases == eve

    def test_n_equals_1_no_exception(self):
        for seed in range(20):
            sim = make_sim(n_bits=1, seed=seed)
            sim.run_to_end()
            assert sim.step == Step.RESULT

    def test_large_n_runs(self):
        sim = make_sim(n_bits=5000, eve_present=True, eve_ratio=0.5)
        sim.run_to_end()
        assert sim.step == Step.RESULT
        assert abs(len(sim.state.sifted_indices) / 5000 - 0.5) <= 0.03

    def test_zero_sifted_bits_no_exception(self):
        sim = make_sim(n_bits=4, manual_alice_bases=[PLUS] * 4, manual_bob_bases=[CROSS] * 4)
        sim.run_to_end()  # nem dobhat kivételt
        s = sim.state
        assert s.sifted_indices == []
        assert s.sample_indices == []
        assert s.final_key == []

    def test_zero_sifted_bits_key_not_accepted(self):
        """0 sifted bitnél nincs kulcs, ezért nem lehet 'Kulcs elfogadva'."""
        sim = make_sim(n_bits=4, manual_alice_bases=[PLUS] * 4, manual_bob_bases=[CROSS] * 4)
        sim.run_to_end()
        assert sim.state.key_accepted is False
