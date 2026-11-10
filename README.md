# BB84 Szimulátor

Interaktív BB84 kvantumkulcs-elosztási protokoll szimulátor Python + Qiskit + Streamlit alapon.

## Futtatás fejlesztőként

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Fájlszerkezet

```text
bb84-simulator/
├── app.py            # Streamlit felület (léptető, táblázat, QBER)
├── bb84.py           # Protokoll logika Qiskittel (nincs benne Streamlit)
├── run_app.py        # Belépési pont az .exe-hez
├── tests/
│   └── test_bb84.py
├── docs/             # Dokumentáció, képernyőképek
├── requirements.txt
├── .gitignore
└── README.md
```

## Tesztek

```bash
pytest
```

## Csomagolás (.exe)

```bash
pyinstaller --onedir --collect-all streamlit --collect-all qiskit --copy-metadata streamlit run_app.py
```
