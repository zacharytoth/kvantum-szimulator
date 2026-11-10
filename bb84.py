"""BB84 protokoll logika Qiskittel.

Ez a modul NEM tartalmaz Streamlit kódot – csak a kvantumlogikát.
Feladatok: CORE-01 ... CORE-08 (lásd BB84_Projektterv).
"""

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


def send_and_measure(bit: int, send_basis: str, measure_basis: str) -> int:
    """Egy foton küldése a send_basis bázisban, mérése a measure_basis bázisban.

    Args:
        bit: 0 vagy 1, a kódolt bit.
        send_basis: "z" (+) vagy "x" (×) – a küldő bázisa.
        measure_basis: "z" (+) vagy "x" (×) – a mérő bázisa.

    Returns:
        A mért bit (0 vagy 1).
    """
    qc = QuantumCircuit(1)
    if bit == 1:
        qc.x(0)                # |1>
    if send_basis == "x":
        qc.h(0)                # |+> vagy |->
    if measure_basis == "x":
        qc.h(0)                # visszaforgatás a mérés előtt
    outcome, _ = Statevector(qc).measure()
    return int(outcome)


# TODO: CORE-01 – Véletlen bitek és bázisok generálása
# TODO: CORE-03 – Eve intercept-resend támadás
# TODO: CORE-04 – Teljes futás: táblázat előállítása a beállításokból
# TODO: CORE-05 – Szitálás: egyező bázisú pozíciók kiválasztása
# TODO: CORE-06 – QBER számítása és döntés a küszöb alapján
# TODO: CORE-07 – Polarizáció -> nyíl szimbólum (↕ ↔ ↗ ↖)
# TODO: CORE-08 – (opcionális) Eve lehallgatási aránya 0-100%
