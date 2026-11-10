"""BB84 tesztek.

Feladatok: TST-01 ... TST-03 (lásd BB84_Projektterv).
Futtatás:
    pytest
"""

import bb84


def test_same_basis_matches_without_eve() -> None:
    """TST-01: egyező bázisnál Bob bitje mindig egyezik Alice-éval (Eve nélkül)."""
    for bit in (0, 1):
        for basis in ("z", "x"):
            assert bb84.send_and_measure(bit, basis, basis) == bit


# TODO: TST-02 – Eve nélkül a QBER 0%
# TODO: TST-03 – Eve-vel, sok qubittel (pl. 2000) a QBER kb. 25% (+/-3%)
