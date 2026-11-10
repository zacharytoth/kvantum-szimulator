# BB84 Szimulátor – Projektterv (egyszerűsített)

> **Csapat:** 2 fő (**F1** és **F2**)
> **Időkeret:** kb. **10 óra / fő**, összesen ~20 óra
> **Nyelv:** Python + Qiskit
> **Verziókezelés:** Git + GitHub

---

## 1. Projekt Áttekintés & Célok

### 1.1 Mit kell beadni?

| Beadandó | Hogyan teljesítjük |
|----------|--------------------|
| **Forráskód** | GitHub repó (`app.py`, `bb84.py`, tesztek, README) |
| **Futtatható szimulátor** | ZIP, amelyben egy `BB84.exe` (vagy `start.bat`) van. Dupla kattintásra elindul és megnyílik a böngészőben, Python telepítése nélkül. |
| **Dokumentáció** | 3–5 oldalas PDF: rövid elmélet, használati útmutató képernyőképekkel, felhasznált könyvtárak |

### 1.2 Értékelési szempontok → funkciók

| Szempont | Megvalósítás |
|----------|--------------|
| **Helyes működés** | A kvantumállapotok előkészítése és mérése Qiskittel történik, néhány teszt ellenőrzi |
| **Manuális bit- és bázisválasztás** | Szerkeszthető táblázat (`st.data_editor`), amelyben Alice bitjei és bázisai, Bob és Eve bázisai átírhatók |
| **Eve megjelenik** | Be/ki kapcsoló, külön oszlopok Eve bázisával és mért bitjével, kiemelve |
| **Eve hatása érzékelhető (QBER)** | QBER kijelző (`st.metric`), a hibás bitek pirossal, küszöb (11%) felett figyelmeztetés |
| **Léptethető** | „Előző / Következő” gombok, folyamatjelző, minden lépésnél rövid magyarázó szöveg |
| **UX** | Polarizációs nyilak (↕ ↔ ↗ ↖), színkódolt táblázat (zöld: egyezik, szürke: eldobva, piros: hiba), átlátható elrendezés |

### 1.3 A protokoll lépései a léptetőben

1. **Beállítás:** qubitszám (pl. 8–32), Eve be/ki, véletlen vagy kézi mód
2. **Alice:** bitek és bázisok (+ vagy ×), polarizáció megjelenítése
3. **Küldés:** ha Eve aktív, minden fotont elfog, megmér a saját bázisában és újraküld
4. **Bob:** bázisválasztás és mérés
5. **Bázisok egyeztetése:** az eltérő bázisú pozíciókat eldobják (szitálás)
6. **QBER:** a megmaradt bitek egy részének összevetése, hibaarány
7. **Eredmény:** a kulcs elfogadva, vagy a protokoll megszakad Eve gyanúja miatt

---

## 2. Technológiai Stack & Architektúra

### 2.1 Választott stack

| Eszköz | Szerep |
|--------|--------|
| **Python 3.11 / 3.12** | Nyelv |
| **Qiskit** | Qubit előkészítése és mérése (`QuantumCircuit` + `Statevector`) |
| **Streamlit** | Böngészős felület, egyszerű Python kóddal |
| **pandas** | A qubitek táblázata, színezés |
| **pytest** | Néhány egyszerű teszt |
| **PyInstaller** | `.exe` készítése a beadáshoz |

**Miért elég ennyi:** A Streamlit böngészőben fut, ami pont megfelel a „böngészővel rendelkező Windows gép” feltételnek. HTML/JS tudás nem kell hozzá. A `qiskit-aer` szimulátor sem kell: a `Statevector` mérése elég egy qubithez, és így kisebb és könnyebben csomagolható a program.

### 2.2 Alternatívák röviden

| Opció | Mikor válasszuk |
|-------|-----------------|
| **Streamlit** *(ajánlott)* | Leggyorsabb fejlesztés, szép alapértelmezett megjelenés |
| **Gradio** vagy **NiceGUI** | Ha a Streamlit nem tetszik. A NiceGUI-hoz van saját csomagoló parancs (`nicegui-pack`). |
| **Tkinter** | Böngésző nélküli asztali ablak. Csúnyább, és nem használja ki, hogy a feladat böngészőt említ. |

### 2.3 Fájlszerkezet

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

A logika és a felület **két külön fájlban** van, így ketten nagyrészt egymástól függetlenül tudtok dolgozni.

### 2.4 A protokoll magja Qiskittel (kiindulópont)

```python
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

def send_and_measure(bit: int, send_basis: str, measure_basis: str) -> int:
    """Egy foton küldése a send_basis bázisban, mérése a measure_basis bázisban."""
    qc = QuantumCircuit(1)
    if bit == 1:
        qc.x(0)                # |1>
    if send_basis == "x":
        qc.h(0)                # |+> vagy |->
    if measure_basis == "x":
        qc.h(0)                # visszaforgatás a mérés előtt
    outcome, _ = Statevector(qc).measure()
    return int(outcome)

# Eve nélkül:   bob_bit = send_and_measure(a_bit, a_basis, b_basis)
# Eve-vel:      eve_bit = send_and_measure(a_bit, a_basis, e_basis)
#               bob_bit = send_and_measure(eve_bit, e_basis, b_basis)
```

### 2.5 A legnagyobb kockázat: a csomagolás

A Streamlit és a Qiskit PyInstallerrel csomagolva nem mindig indul el elsőre. Ezért a csomagolást **az elején, egy „Hello World” appal ki kell próbálni** (SET-04 feladat).

- **A terv:** `run_app.py` indítja a Streamlitet, a buildhez a `pyinstaller --onedir --collect-all streamlit --collect-all qiskit --copy-metadata streamlit ...` kapcsolók kellenek.
- **B terv, ha a PyInstaller nem működik:** a [Windows embeddable Python](https://www.python.org/downloads/windows/) ZIP-be a csomagok előre feltelepítve, mellé egy `start.bat`, ami elindítja az appot. Ez is fut telepítés nélkül, csak kicsomagolás kell.

---

## 3. Feladatlista (Task Backlog)

> Zárójelben a becsült idő. Összesen ~20 óra.

### 3.1 Setup & Git (~1,5 óra)

- [ ] **SET-01** GitHub repó, mindketten collaboratorok (0,25 ó)
- [ ] **SET-02** Virtuális környezet, `requirements.txt` (`qiskit`, `streamlit`, `pandas`, `pytest`, `pyinstaller`) (0,25 ó)
- [ ] **SET-03** `.gitignore` (`.venv/`, `__pycache__/`, `build/`, `dist/`), README váz (0,25 ó)
- [ ] **SET-04** **Csomagolási próba:** egy „Hello World” Streamlit app + Qiskit import `.exe`-be csomagolva, elindítva Windows-on (0,75 ó)

### 3.2 Kvantumlogika – `bb84.py` (~3,5 óra)

- [ ] **CORE-01** Véletlen bitek és bázisok generálása (0,25 ó)
- [ ] **CORE-02** `send_and_measure()` Qiskittel (0,5 ó)
- [ ] **CORE-03** Eve intercept-resend támadás (0,5 ó)
- [ ] **CORE-04** Teljes futás: egy függvény, ami a beállításokból (és kézi bemenetekből) visszaadja a qubitek táblázatát (1 ó)
- [ ] **CORE-05** Szitálás: egyező bázisú pozíciók kiválasztása (0,25 ó)
- [ ] **CORE-06** QBER számítása és döntés a küszöb alapján (0,5 ó)
- [ ] **CORE-07** Polarizáció → nyíl szimbólum (↕ ↔ ↗ ↖) segédfüggvény (0,25 ó)
- [ ] **CORE-08** *(opcionális)* Eve lehallgatási aránya 0–100% között (0,25 ó)

### 3.3 Felület – `app.py` (~5 óra)

- [ ] **UI-01** Oldalsáv: qubitszám, Eve be/ki, véletlen/kézi mód, „Új futás” gomb (0,5 ó)
- [ ] **UI-02** Léptető: lépésindex a `st.session_state`-ben, „Előző / Következő / Újra” gombok, folyamatjelző (1 ó)
- [ ] **UI-03** Qubit táblázat, amelyben a lépésnek megfelelő oszlopok jelennek meg (1 ó)
- [ ] **UI-04** Kézi mód: `st.data_editor` a bitek és bázisok szerkesztéséhez, a hibás bevitel jelzése (1 ó)
- [ ] **UI-05** Színezés: egyező, eldobott, hibás bitek, Eve oszlopai kiemelve (0,5 ó)
- [ ] **UI-06** Magyarázó szöveg minden lépéshez (`st.info`) (0,5 ó)
- [ ] **UI-07** QBER kijelző és eredmény: `st.metric`, „Kulcs elfogadva” (`st.success`) vagy „Eve gyanú!” (`st.error`) (0,5 ó)

### 3.4 Tesztelés (~2 óra)

- [ ] **TST-01** Teszt: egyező bázisnál Bob bitje mindig egyezik Alice-éval (Eve nélkül) (0,25 ó)
- [ ] **TST-02** Teszt: Eve nélkül a QBER 0% (0,25 ó)
- [ ] **TST-03** Teszt: Eve-vel, sok qubittel (pl. 2000) a QBER kb. 25% (±3%) (0,5 ó)
- [ ] **TST-04** Kézi végigkattintás: minden lépés, kézi mód, Eve be/ki (0,5 ó)
- [ ] **TST-05** A kész `.exe` kipróbálása egy másik Windows gépen (0,5 ó)

### 3.5 Dokumentáció & Csomagolás (~8 óra)

- [ ] **DOC-01** Elméleti rész: qubit, bázisok, BB84 lépései, miért okoz Eve hibát (kb. 1 oldal) (1,5 ó)
- [ ] **DOC-02** Használati útmutató képernyőképekkel: indítás, beállítások, léptetés, kézi mód, Eve, QBER (kb. 1,5–2 oldal) (2 ó)
- [ ] **DOC-03** Felhasznált könyvtárak táblázata (név, verzió, szerep) és rendszerkövetelmények (0,5 ó)
- [ ] **DOC-04** Rövid leírás a program felépítéséről (`bb84.py` / `app.py`) (0,5 ó)
- [ ] **DOC-05** Forrásjegyzék, végleges PDF, oldalszám ellenőrzése (min. 3 oldal) (0,5 ó)
- [ ] **PKG-01** Végleges `.exe` build (vagy B terv: embeddable Python + `start.bat`) (1,5 ó)
- [ ] **PKG-02** Beadási ZIP: futtatható program + PDF + forráskód (0,5 ó)
- [ ] **PKG-03** README: futtatás fejlesztőként (`pip install -r requirements.txt`, `streamlit run app.py`) (0,5 ó)
- [ ] **PKG-04** Közös próbabemutató (0,5 ó)

---

## 4. Munkamegosztási Stratégiák

### Approach A: Horizontális felosztás (Felület vs. Kvantumlogika) ⭐ ajánlott

| Ki | Mit | Kb. idő |
|----|-----|---------|
| **F1** | `bb84.py` (CORE-01…08), tesztek (TST-01…03), doksi: elmélet + könyvtárak (DOC-01, DOC-03) | 10 ó |
| **F2** | `app.py` (UI-01…07), doksi: használati útmutató + felépítés (DOC-02, DOC-04) | 10 ó |
| **Közösen** | Setup (SET-*), csomagolás (PKG-*), kézi teszt (TST-04, TST-05), végleges PDF (DOC-05) | |

**Git:** F1 szinte csak a `bb84.py`-hoz és a `tests/`-hez nyúl, F2 csak az `app.py`-hoz, ezért alig lesz konfliktus. Az első órában közösen rögzítitek, milyen függvényeket ad a `bb84.py` (név, paraméterek, visszatérési érték). Addig F2 egy kamu táblázattal dolgozhat.

### Approach B: Vertikális felosztás (Alap protokoll + Kézi mód vs. Eve + QBER)

| Ki | Mit |
|----|-----|
| **F1** | Alap protokoll Eve nélkül (logika + felület), léptető, kézi mód |
| **F2** | Eve támadás (logika + oszlopok a táblázatban), QBER számítás és kijelzés, tesztek |
| **Közösen** | Setup, csomagolás, dokumentáció |

**Git:** Mindketten mindkét fájlhoz hozzányúltok, ezért gyakrabban lesz konfliktus. F1 előbb merge-elje az alap protokollt, és F2 erre építsen. Munka előtt mindig `git pull`.

### Approach C: Hacker és Menedzser

| Ki | Mit |
|----|-----|
| **F1 – Hacker** | Teljes kód: `bb84.py` és `app.py` |
| **F2 – Menedzser** | Tesztelés, csomagolás, a teljes dokumentáció, a felület finomítása (szövegek, színek), beadási ZIP |

**Git:** F1 a kódon dolgozik, F2 a `docs/`, `tests/` mappán és a buildön, és ő nézi át F1 commitjait. Hátránya, hogy a védésen F2-nek is értenie kell a kódot, ezért a végén F1 menjen végig vele rajta.

### Összehasonlítás

| | A | B | C |
|--|---|---|---|
| Konfliktus kockázat | Alacsony | Közepes | Alacsony |
| Mindketten értik a kódot | Részben | Igen | Kevésbé |
| Egyenletes terhelés | Igen | Igen | Kevésbé |

---

## 5. Git és Együttműködési Szabályok

1. **Branchek:** a `main` mindig működjön. Mindenki saját branchen dolgozik (pl. `feature/eve`, `feature/stepper`, `docs/user-guide`), és Pull Requesttel merge-el.
2. **Munka előtt `git pull`**, kis és gyakori commitok. Egy branch ne éljen 1–2 napnál tovább.
3. **Commit üzenetek** rövid előtaggal: `feat: Eve támadás`, `fix: QBER nullával osztás`, `docs: használati útmutató`, `test: QBER teszt`.
4. **Review:** a PR-t a másik fél nézi át és merge-eli. Ez segít abban is, hogy mindketten ismerjétek a teljes kódot a védésre.
5. **Tag a beadáskor:** `git tag -a v1.0 -m "Beadott verzió"` majd `git push origin v1.0`. Egy GitHub Release-hez csatolható a beadási ZIP.

---

## Javasolt ütemezés

| Alkalom | Teendő |
|---------|--------|
| **1. (közös, ~1,5 ó)** | Setup, a `bb84.py` függvényeinek rögzítése, csomagolási próba |
| **2–3. (külön, ~5 ó/fő)** | Logika és felület párhuzamosan |
| **4. (közös, ~1,5 ó)** | Összekötés, kézi tesztelés, javítások |
| **5. (külön, ~2 ó/fő)** | Dokumentáció, végleges build, beadás |
