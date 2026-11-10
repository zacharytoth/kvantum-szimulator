"""BB84 Szimulátor – Streamlit felület.

Léptető, qubit táblázat, QBER kijelző.
Feladatok: UI-01 ... UI-07 (lásd BB84_Projektterv).

Futtatás fejlesztőként:
    streamlit run app.py
"""

import streamlit as st

import bb84


def main() -> None:
    st.set_page_config(page_title="BB84 Szimulátor", page_icon="🔐", layout="wide")
    st.title("🔐 BB84 Kvantumkulcs-elosztás Szimulátor")

    # TODO: UI-01 – Oldalsáv: qubitszám, Eve be/ki, véletlen/kézi mód, "Új futás"
    # TODO: UI-02 – Léptető: lépésindex a st.session_state-ben, Előző/Következő/Újra
    # TODO: UI-03 – Qubit táblázat a lépésnek megfelelő oszlopokkal
    # TODO: UI-04 – Kézi mód: st.data_editor a bitek és bázisok szerkesztéséhez
    # TODO: UI-05 – Színezés: egyező / eldobott / hibás bitek, Eve oszlopai kiemelve
    # TODO: UI-06 – Magyarázó szöveg minden lépéshez (st.info)
    # TODO: UI-07 – QBER kijelző és eredmény (st.metric, st.success / st.error)

    st.info("A felület még fejlesztés alatt áll. Lásd a projekttervet (UI-01 ... UI-07).")


if __name__ == "__main__":
    main()
