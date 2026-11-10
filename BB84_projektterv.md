# BB84 Kvantumkulcsszétosztó Szimulátor: Projektterv

> **Tantárgy:** egyetemi házi feladat
> **Csapat:** 2 fő
> **Becsült ráfordítás:** kb. 20 óra
> **Stack:** Python 3.12 · CustomTkinter · PyInstaller · pytest
> **Végtermék:** egyetlen fájlból álló, önállóan futó `BB84_Simulator.exe`

---

## Tartalomjegyzék

1. [Projekt Áttekintés & Célok](#1-projekt-áttekintés--célok)
2. [Technológiai Stack & Architektúra](#2-technológiai-stack--architektúra)
3. [Részletes Feladatlista (Task Backlog)](#3-részletes-feladatlista-task-backlog)
4. [Git és Együttműködési Szabályok](#4-git-és-együttműködési-szabályok)

---

## 1. Projekt Áttekintés & Célok

### 1.1 Rövid leírás

Asztali alkalmazást készítünk, amely lépésenként szemlélteti a **BB84 kvantumkulcsszétosztó protokollt** (Bennett–Brassard, 1984). A felhasználó követheti Alice bit- és bázisválasztását, a fotonok polarizációját, Bob mérését, a bázisegyeztetést (sifting), valamint a hibaarány (QBER) becslését. Bekapcsolható egy lehallgató (**Eve**), akinek a jelenléte a megnövekedett QBER-ből kimutatható.

A kvantumlogikát **tiszta Pythonban** valósítjuk meg: kétdimenziós valós állapotvektorokkal, projektív méréssel és a Born-szabállyal. Külső kvantumkönyvtárat nem használunk.

### 1.2 Célok és nem-célok

| # | Cél | Mérhető kritérium |
|---|-----|-------------------|
| C1 | Fizikailag helyes BB84-szimuláció | Eve nélkül és zaj nélkül QBER = 0%. Teljes lehallgatásnál QBER ≈ 25% (N ≥ 1000 esetén ±3%-on belül) |
| C2 | Hordozhatóság | Egyetlen `.exe` fájl, amely tiszta Windows 10/11 gépen Python nélkül elindul |
| C3 | Kis méret, gyors indulás | Az exe várhatóan 15–25 MB nagyságrendű. Hidegindítás < 5 s |
| C4 | Oktatási érték | Minden lépésnél magyarázó szöveg, színkódolt táblázat, előre és vissza léptetés |
| C5 | Tesztelhetőség | A `bb84_core.py` nem importál GUI-t, így önállóan, pytesttel tesztelhető |

**Nem-célok (scope-on kívül):**

- valódi hibajavítás (pl. Cascade) és privacy amplification (csak szövegesen említjük),
- hálózati kommunikáció két gép között,
- **Streamlit** (böngészőt és szerverfolyamatot igényel, a csomagolása nehézkes),
- **Qiskit** (több száz MB-os függőségi fa, NumPy/SciPy-verzióütközések, a PyInstaller-build törékeny).

> **Megjegyzés:** a választott stack mellett a program **böngészőt sem igényel**. Natív Tk-ablakként fut, így minden átlagos Windows gépen elindul.

### 1.3 Beadandók

| # | Beadandó | Formátum | Tartalom / követelmény |
|---|----------|----------|------------------------|
| B1 | Forráskód | Git repó (link) **és** `BB84_source_vX.Y.zip` | `bb84_core.py`, `gui.py`, `main.py`, `tests/`, `requirements.txt`, `bb84.spec`, `build.ps1`, `README.md` |
| B2 | Futtatható állomány | `BB84_Simulator.exe` (egyfájlos, `--onefile`) | Python nélkül indul Windows 10/11-en. GitHub Release-ben is csatolva |
| B3 | Dokumentáció | `docs/BB84_dokumentacio.pdf`, **legalább 3 oldal** (forrás: Markdown vagy DOCX) | Elmélet, architektúra, használati útmutató képernyőképekkel, tesztelés, mérési eredmények, korlátok |

**A dokumentáció tervezett szerkezete (B3):**

1. Bevezetés és motiváció (0,5 oldal)
2. A BB84 elméleti háttere: bázisok, polarizációk, Born-szabály, intercept-resend támadás, a 25%-os QBER levezetése (1 oldal)
3. Architektúra és megvalósítás: MVC, állapotgép (0,75 oldal)
4. Felhasználói útmutató képernyőképekkel (0,75 oldal)
5. Tesztelés és mérési eredmények: QBER az Eve-arány függvényében (táblázat) (0,5 oldal)
6. Korlátok, továbbfejlesztési lehetőségek, munkamegosztás, források (0,5 oldal)

### 1.4 Értékelési szempontok és a megvalósítás megfeleltetése

| Értékelési szempont | Konkrét megvalósítási elem | Hely | Task ID | Ellenőrzés módja |
|---------------------|----------------------------|------|---------|------------------|
| **Helyes működés** | Állapotvektoros kódolás (4 polarizáció), projektív mérés Born-szabállyal, sifting, QBER-becslés mintavétellel | `bb84_core.py` | Q1, Q2, Q5 | Unit és statisztikai tesztek (QBER = 0% / ≈25%, sifting ≈50%) |
| **Manuális bit- és bázisválasztás** | Beviteli mezők (`0101…`, `+x+x…`) Alice bitjeihez és bázisaihoz, Bob bázisaihoz, opcionálisan Eve bázisaihoz. Validálás azonnali hibaüzenettel | `gui.py` (bevitel), `bb84_core.py` (feldolgozás) | Q7, G3 | Parsing-tesztek + manuális tesztlista |
| **Automata bit- és bázisválasztás** | „🎲 Véletlen” gomb mezőnként, valamint „Teljes automata” mód. Seedelhető véletlenszám-generátor a reprodukálhatósághoz | `bb84_core.py`, `gui.py` | Q1, G3 | Azonos seed → azonos futás (teszt) |
| **Eve megjelenítése** | Külön „Eve” sáv és oszlopok a táblázatban (Eve bázisa, mért bitje, továbbküldött foton). Lila kiemelés azoknál a fotonoknál, amelyeket Eve megváltoztatott. Lehallgatási arány csúszkával (0–100%) | `gui.py` | Q3, G4 | Manuális tesztlista, képernyőképek |
| **Eve észlelhetősége** | Mintavételezett sifted bitek nyilvános összevetése. Az elméleti észlelési valószínűség kiírása: P(rejtve marad) = (3/4)^k, ahol k a mintabitek száma | `bb84_core.py`, `gui.py` | Q5, G5 | Statisztikai tesztek |
| **QBER számítás** | QBER = eltérő mintabitek száma / összes mintabit. Kijelzés %-ban, a várható értékkel együtt (Eve-arány · 25% + zaj) | `bb84_core.py`, `gui.py` | Q5, G5 | Unit + statisztikai teszt |
| **QBER riasztás** | Állítható küszöb (alapérték 11%). Túllépésnél piros banner („⚠ Lehallgatás gyanúja – kulcs eldobva”) és figyelmeztető ablak. Alatta zöld „✔ Kulcs elfogadva” | `gui.py` | G5 | Manuális tesztlista |
| **Lépésenkénti léptetés** | Állapotgép 10 állapottal, `Reset`, `Vissza`, `Előre` és `Végig` műveletekkel. A visszalépés snapshotokból történik | `bb84_core.py`, `gui.py` | Q6, G1 | Állapotgép-tesztek |
| **UX** | Lépésmagyarázó panel, színkódolás, tooltipek, billentyűparancsok (←/→), sötét és világos téma, hibabiztos bevitel, nagy N esetén görgethető táblázat | `gui.py` | G2, G6, G7 | Manuális tesztlista, peer review |

### 1.5 A protokoll lépései a léptetőben

A léptető 10 állapotból áll. Minden lépésnél frissül a táblázat (új oszlop jelenik meg), és a magyarázó panelen olvasható, **mi történik, ki végzi, és az információ nyilvános vagy titkos**.

| # | Állapot | Szereplő | Mi történik | Mit mutat a GUI | Csatorna / titkosság |
|---|---------|----------|-------------|-----------------|----------------------|
| 0 | `SETUP` | Felhasználó | Paraméterek: N, mód (manuális/auto), Eve be/ki és arány, zaj, mintaarány, QBER-küszöb, seed | Paraméterpanel, üres táblázat | – |
| 1 | `ALICE_BITS` | Alice | N darab véletlen (vagy megadott) bit | „Alice bit” oszlop | 🔒 titkos |
| 2 | `ALICE_BASES` | Alice | Bázisválasztás bitenként: `+` (rektilineáris) vagy `×` (diagonális) | „Alice bázis” oszlop | 🔒 titkos |
| 3 | `ENCODE` | Alice | Kódolás polarizációba: `+`: 0→`→` (0°), 1→`↑` (90°); `×`: 0→`↗` (45°), 1→`↖` (135°) | „Foton” oszlop szimbólumokkal | 🔒 kvantumállapot |
| 4 | `TRANSMIT` | (Eve) | Kvantumcsatorna. Ha Eve aktív, p valószínűséggel elfogja a fotont, véletlen bázisban megméri, és a mért állapotot küldi tovább (intercept-resend). Opcionális csatornazaj (bitflip) | „Eve bázis”, „Eve bit”, „Továbbküldött foton” oszlopok, lila kiemelés | ⚛ kvantumcsatorna |
| 5 | `BOB_BASES` | Bob | Bob véletlen (vagy megadott) mérési bázist választ | „Bob bázis” oszlop | 🔒 titkos |
| 6 | `BOB_MEASURE` | Bob | Projektív mérés. Egyező bázisnál determinisztikus, eltérőnél 50/50 | „Bob bit” oszlop | 🔒 titkos |
| 7 | `SIFTING` | Alice + Bob | Nyilvánosan közlik a **bázisokat** (a bitek titkosak maradnak). Az eltérő bázisú pozíciókat eldobják (kb. 50%) | Eldobott sorok szürkén, megtartottak zölden. Sifted kulcshossz | 📢 nyilvános, hitelesített |
| 8 | `QBER` | Alice + Bob | A sifted bitek egy véletlen mintáját (pl. 25%) felfedik és összevetik. QBER kiszámítása, majd a mintabitek eldobása | Mintabitek keretezve, hibák pirossal. QBER-mérő a várható értékkel | 📢 nyilvános |
| 9 | `RESULT` | Rendszer | Ha QBER > küszöb: 🚨 riasztás, a kulcsot eldobják. Különben a maradék bitek alkotják a közös kulcsot | Riasztó vagy elfogadó banner, végső kulcs (hex/bin), statisztikák | – |

**Példafutás (N = 8, Eve 100%-ban lehallgat, a `*` véletlen mérési kimenetet jelöl):**

| i | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Alice bit | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 1 |
| Alice bázis | + | + | × | × | + | × | + | × |
| Foton | → | ↑ | ↖ | ↗ | ↑ | ↗ | → | ↖ |
| Eve bázis | + | × | × | + | + | + | × | × |
| Eve bit | 0 | 1* | 1 | 0* | 1 | 1* | 0* | 1 |
| Továbbküldött | → | ↖ | ↖ | → | ↑ | ↑ | ↗ | ↖ |
| Bob bázis | + | + | × | × | × | × | × | × |
| Bob bit | 0 | 0* | 1 | 0* | 1* | 1* | 0 | 1 |
| Bázis egyezik? | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ |
| Hiba? | – | **✗** | – | – | (eldobva) | **✗** | (eldobva) | – |

Sifted hossz: 6, hibák: 2, QBER = 33%. Kis N mellett ez nagyobb a 25%-os várható értéknél, ezt a dokumentációban is megmagyarázzuk.

---

## 2. Technológiai Stack & Architektúra

### 2.1 Használt könyvtárak

| Könyvtár | Verzió (a setupkor rögzítjük) | Szerep | Bekerül az exe-be? |
|----------|-------------------------------|--------|--------------------|
| Python | 3.12.x (python.org installer, Tcl/Tk-val) | Futtatókörnyezet | ✔ (beágyazva) |
| `customtkinter` | `>=5.2,<6` | Modern megjelenésű Tk-widgetek, témák | ✔ |
| `tkinter.ttk` (stdlib) | – | `Treeview` a nagy táblázatokhoz (a CustomTkinterben nincs táblázat-widget) | ✔ |
| `random`, `math`, `dataclasses`, `enum` (stdlib) | – | Kvantumlogika, adatmodell | ✔ |
| `pyinstaller` | `>=6.0` | Egyfájlos exe készítése | ✘ (csak build) |
| `pytest` | `>=8.0` | Unit és statisztikai tesztek | ✘ (csak dev) |
| `ruff` (opcionális) | legfrissebb | Lint és formázás | ✘ (csak dev) |

A `requirements.txt` (futásidejű) és a `requirements-dev.txt` (build + teszt) külön fájlban van, így a buildbe nem kerül felesleges csomag. A pontos verziókat az S1 taskban rögzítjük.

### 2.2 Fájlszerkezet (MVC-szerű felépítés)

```text
bb84-simulator/
├── bb84_core.py          # MODEL + állapotgép: tiszta Python, NINCS GUI-import
├── gui.py                # VIEW + vékony CONTROLLER: CustomTkinter widgetek, eseménykezelők
├── main.py               # Belépési pont: erőforrás-útvonalak, alkalmazás indítása
├── assets/
│   └── icon.ico          # Alkalmazásikon (exe + ablak)
├── tests/
│   ├── test_core.py          # kódolás/mérés determinisztikus esetei
│   ├── test_statistics.py    # QBER ≈ 0% / 25%, sifting ≈ 50%
│   ├── test_state_machine.py # léptetés, visszalépés, reset
│   └── test_parsing.py       # manuális bevitel validálása
├── docs/
│   ├── BB84_dokumentacio.md  # forrás
│   ├── BB84_dokumentacio.pdf # beadandó (B3)
│   ├── screenshots/
│   └── manual_test_checklist.md
├── bb84.spec             # PyInstaller konfiguráció (verziókezelt)
├── build.ps1             # Reprodukálható Windows build szkript
├── requirements.txt
├── requirements-dev.txt
├── .github/
│   ├── workflows/ci.yml          # pytest + Windows build artifact
│   └── pull_request_template.md
├── .gitignore
└── README.md
```

**Rétegszabályok:**

| Réteg | Fájl | Szabad | Tilos |
|-------|------|--------|-------|
| Model | `bb84_core.py` | stdlib, adatosztályok, tiszta függvények, állapotgép | `tkinter`/`customtkinter` import, kiírás mint UI |
| View/Controller | `gui.py` | widgetek, eseménykezelés, a szimuláció publikus API-jának hívása | kvantumlogika újraimplementálása, közvetlen véletlenszám-generálás |
| Entry | `main.py` | erőforrás-útvonalak feloldása, DPI-beállítás, alkalmazás indítása | üzleti logika |

**Interfész-szerződés (a projekt elején közösen rögzítjük, ez teszi lehetővé a párhuzamos munkát):**

| Elem | Típus | Felelősség |
|------|-------|------------|
| `Basis` | felsorolás | A két bázis: `+` (rektilineáris), `×` (diagonális) |
| `Photon` | adatosztály | Polarizációs szög (0°, 45°, 90°, 135°), állapotvektor, megjelenítő szimbólum |
| `Step` | felsorolás | A léptető 10 állapota (`SETUP` … `RESULT`) |
| `SimConfig` | adatosztály | N, Eve be/ki, Eve-arány, zaj, mintaarány, QBER-küszöb, seed, opcionális manuális bitek és bázisok |
| `SimState` | adatosztály | Csak olvasható pillanatkép a GUI számára: aktuális lépés, összes oszlop adatai, sifted indexek, mintaindexek, QBER, végső kulcs |
| `BB84Simulation` | osztály | Állapotgép: `next_step`, `prev_step`, `reset`, `run_to_end`, `state`, `step` |
| `send_and_measure` | függvény | Egy foton teljes útja Alice → (Eve) → csatorna → Bob |
| `sift`, `estimate_qber`, `undetected_probability` | függvények | Bázisegyeztetés, mintavételes QBER-becslés, rejtve maradási valószínűség |
| `parse_bits`, `parse_bases` | függvények | Manuális bevitel feldolgozása és validálása |

### 2.3 Tiszta Python kvantumlogika

**Modell:** egy foton polarizációs állapota a (cos θ, sin θ) valós egységvektor. Egy {|m₀⟩, |m₁⟩} bázisban végzett mérésnél P(0) = |⟨m₀|ψ⟩|² (Born-szabály). A mérés után az állapot a mért bázisvektorba omlik össze.

| Bázis | Bit 0 | Bit 1 |
|-------|-------|-------|
| `+` rektilineáris | \|H⟩ = 0° `→` | \|V⟩ = 90° `↑` |
| `×` diagonális | \|D⟩ = 45° `↗` | \|A⟩ = 135° `↖` |

**A `send_and_measure` algoritmus lépései:**

1. **Kódolás:** Alice bitjéből és bázisából a táblázat alapján meghatározzuk a foton polarizációs szögét.
2. **Lehallgatás (opcionális):** ha Eve aktív erre a fotonra, saját bázisában megméri, majd a mért bitnek megfelelő, a saját bázisában lévő új fotont küldi tovább.
3. **Csatornazaj (opcionális):** adott valószínűséggel a foton az ortogonális állapotba fordul (+90°), ami bitflipnek felel meg.
4. **Bob mérése:** a Born-szabály alapján kiszámítjuk a 0-s kimenet valószínűségét (a foton állapotvektorának és Bob bázisa 0-s vektorának skalárszorzata, négyzetre emelve), majd egy véletlenszám alapján eldöntjük a kimenetet.
5. **Eredmény:** visszaadjuk az eredeti fotont, Eve bázisát és bitjét, a továbbított fotont és Bob bitjét.

**Implementációs megjegyzések:**

- A lebegőpontos pontatlanságot kezelni kell: pl. cos(90°) nem pontosan 0, ezért a valószínűséget kerekítjük, hogy egyező bázisnál a mérés valóban determinisztikus legyen.
- Egyetlen, seedelhető véletlenszám-generátort használunk a szimuláció egészében, így azonos seed azonos futást ad.
- A léptető a `TRANSMIT` és `BOB_MEASURE` lépésekben ugyanazokat a primitíveket (kódolás, mérés, bitflip) hívja, mint a `send_and_measure`. Így a fizika egyetlen helyen van.
- A visszalépéshez minden lépés előtt elmentjük az állapotot **és a véletlenszám-generátor állapotát** is, így a Vissza → Előre lépés ugyanazt az eredményt adja.

**Miért éppen 25% a QBER teljes lehallgatásnál?** Eve az esetek ½-ében rossz bázist választ. Ilyenkor a továbbküldött foton Bob (helyes) bázisában ½ valószínűséggel ad rossz bitet. Így ½ · ½ = **¼**. Ha Eve a fotonoknak csak p arányát fogja el, a várható QBER p · 25%. Ezt az értéket a GUI a mért QBER mellett is kiírja.

**GUI-vázlat:**

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ BB84 QKD Szimulátor                                    [☾ Téma] [? Súgó] │
├───────────────────────┬──────────────────────────────────────────────────┤
│ PARAMÉTEREK           │  LÉPÉS 4/9 – Átvitel a kvantumcsatornán          │
│ N bit:      [ 32 ]    │  Eve a fotonok 100%-át elfogja, véletlen bázisban│
│ Mód: (•)Auto ( )Kézi  │  megméri, és a mért állapotot küldi tovább...    │
│ Alice bitek: [0101…]🎲│──────────────────────────────────────────────────│
│ Alice bázis: [+x+x…]🎲│  # │A.bit│A.báz│Foton│Eve b.│Eve bit│Tov.│Bob b.│..│
│ Bob bázis:   [x++x…]🎲│  1 │  0  │  +  │  →  │  +   │   0   │ →  │      │  │
│ ☑ Eve  arány [====80%]│  2 │  1  │  +  │  ↑  │  x   │   1   │ ↖  │      │  │
│ Zaj:        [ 0 % ]   │  … (görgethető, színkódolt sorok)                │
│ Minta:      [ 25 % ]  │──────────────────────────────────────────────────│
│ Küszöb:     [ 11 % ]  │  QBER: ██████░░░░ 24,0 %  (várható: 20,0 %)      │
│ Seed:       [ 42 ]    │  ┌────────────────────────────────────────────┐  │
│                       │  │ 🚨 LEHALLGATÁS GYANÚJA – a kulcs eldobva   │  │
│                       │  └────────────────────────────────────────────┘  │
├───────────────────────┴──────────────────────────────────────────────────┤
│        [⏮ Reset]   [◀ Vissza]   ●●●●○○○○○○   [Előre ▶]   [⏭ Végig]       │
└──────────────────────────────────────────────────────────────────────────┘
```

**Színkódolás:** 🟢 megtartott (egyező bázis) · ⚪ eldobott · 🟣 Eve által módosított · 🔴 hiba a mintában · 🔲 mintabit (felfedve).

### 2.4 Csomagolási stratégia PyInstallerrel

**Alapelvek:**

1. **Smoke teszt a projekt elején (S2):** egy minimális CustomTkinter-ablakot azonnal `--onefile` exe-be csomagolunk, és **tiszta Windows gépen** (Windows Sandbox vagy VM, Python nélkül) kipróbáljuk. A csomagolási kockázatot így az elején kezeljük, nem a végén.
2. **Tiszta, dedikált build-venv:** csak a `requirements.txt` és a `pyinstaller` kerül bele, így az exe kicsi marad, és nem kerül bele véletlenül a pytest.
3. **A buildet Windowson futtatjuk.** A PyInstaller nem keresztfordító: Windows exe csak Windowson (helyben vagy a GitHub Actions `windows-latest` futtatón) készíthető.
4. **A CustomTkinter adatfájljai** (témák `.json`, betűtípusok) nem `.py` fájlok, ezért explicit módon be kell gyűjteni őket.
5. **Erőforrás-útvonalak:** a `main.py` az ikont és egyéb fájlokat fejlesztéskor a projektmappából, az exe-ben a PyInstaller ideiglenes kicsomagolási mappájából (`sys._MEIPASS`) tölti be.
6. **Az exe nem kerül a repóba,** csak GitHub Release-be és a beadott csomagba.

**Tervezett PyInstaller-beállítások (`build.ps1` / `bb84.spec`):**

| Beállítás | Cél |
|-----------|-----|
| `--onefile` | Egyetlen exe fájl |
| `--windowed` | Nincs konzolablak indításkor |
| `--name BB84_Simulator` | A kimeneti fájl neve |
| `--icon assets\icon.ico` | Exe-ikon |
| `--add-data "assets\icon.ico;assets"` | Az ablakikon futásidőben is elérhető |
| `--collect-data customtkinter` | CustomTkinter témák és betűtípusok begyűjtése |
| `--clean --noconfirm` | Reprodukálható, tiszta build |

**Csomagolási kockázatok és kezelésük:**

| Kockázat | Valószínűség | Hatás | Megelőzés / B-terv |
|----------|--------------|-------|--------------------|
| Hiányzó CustomTkinter téma- vagy betűfájl („FileNotFoundError …json”) | közepes | magas | `--collect-data customtkinter`, smoke teszt az elején |
| A régebbi CustomTkinter-leírások `--onedir`-t javasolnak | alacsony | közepes | Ha a `--onefile` mégis hibás, B-terv: `--onedir` + ZIP. A smoke teszt ezt időben kideríti |
| Vírusirtó vagy SmartScreen téves riasztás az onefile exe-re | közepes | közepes | UPX nélkül buildelünk, tiszta venv-ből, ikon és verzióinfó beállításával. A dokumentációban leírjuk a „További információ → Futtatás mindenképp” lépést |
| Lassú első indulás (kicsomagolás a `%TEMP%`-be) | biztos | alacsony | Elfogadható (pár mp). A dokumentációban megemlítjük |
| Python-verzió vagy Tcl/Tk eltérés a két gépen | alacsony | közepes | Mindketten Python 3.12.x-et használunk, a release-buildet a CI készíti |

---

## 3. Részletes Feladatlista (Task Backlog)

> **Jelölés:** `ID` · feladat · **becsült óra** · *Kész, ha:* elfogadási feltétel.
> Minden taskhoz GitHub Issue tartozik, a branch neve tartalmazza az ID-t (lásd 4. fejezet).

### 3.1 Setup & Csomagolásbiztosítás (2,5 óra)

- [ ] **S1** · Repó létrehozása, mappaszerkezet, `.gitignore`, `requirements*.txt`, venv, verziók rögzítése · **0,5 ó**
  *Kész, ha:* mindkét gépen a dev-függőségek telepítése után a `pytest` lefut (0 teszt).
- [ ] **S2** · Minimális CustomTkinter-ablak, PyInstaller `--onefile` smoke build, futtatás **tiszta Windows gépen** · **1,0 ó**
  *Kész, ha:* az exe Python nélküli Windows Sandboxban elindul, és megjelenik a CTk-ablak témával.
- [ ] **S3** · `build.ps1` és `bb84.spec` véglegesítése, ikon, verzióinfó · **0,5 ó**
  *Kész, ha:* egyetlen paranccsal reprodukálható a build, és a méret dokumentálva van.
- [ ] **S4** · CI (GitHub Actions: pytest + Windows build artifact), PR-sablon, `README.md`-váz · **0,5 ó**
  *Kész, ha:* a PR-eken zöld pipa jelenik meg, és az artifactból letölthető exe fut.

### 3.2 Kvantumlogika & Állapotgép (5,0 óra)

- [ ] **Q1** · Adatmodell: `Basis`, `Photon`, `SimConfig`, `SimState`, seedelt véletlenszám-generátor · **0,5 ó**
  *Kész, ha:* az interfész-szerződés (2.2) kódban is létezik, és a GUI mockolni tudja.
- [ ] **Q2** · Kódolás, mérés (Born-szabály, összeomlás), bitflip · **1,0 ó**
  *Kész, ha:* egyező bázisnál 100% egyezés, eltérő bázisnál 50 ± 3% (N = 10 000).
- [ ] **Q3** · Eve intercept-resend támadás, lehallgatási arány, manuális Eve-bázisok · **0,75 ó**
  *Kész, ha:* teljes lehallgatás mellett QBER ≈ 25%, Eve nélkül 0%.
- [ ] **Q4** · Csatornazaj (bitflip valószínűség) · **0,25 ó**
  *Kész, ha:* Eve nélkül a QBER ≈ a zaj értéke.
- [ ] **Q5** · Sifting, mintavételes QBER-becslés, végső kulcs, rejtve maradási valószínűség, várható QBER · **0,75 ó**
  *Kész, ha:* a mintabitek kikerülnek a végső kulcsból, és üres sifted listánál sincs kivétel.
- [ ] **Q6** · Állapotgép: előre, vissza (snapshot + RNG-állapot), reset, végig futtatás · **1,25 ó**
  *Kész, ha:* a Vissza → Előre lépés ugyanazt az eredményt adja, és a határoknál nincs hiba.
- [ ] **Q7** · Manuális bevitel feldolgozása (bitek, bázisok), hosszellenőrzés, beszédes hibák · **0,5 ó**
  *Kész, ha:* hibás karakternél vagy rossz hossznál magyar nyelvű hibaüzenet keletkezik.

### 3.3 Grafikus Felület (UI/UX) (6,0 óra)

- [ ] **G1** · Főablak elrendezése: paraméterpanel, magyarázó panel, léptetősáv (Reset/Vissza/Előre/Végig), progress-pöttyök · **1,0 ó**
  *Kész, ha:* a gombok az állapotgépet hívják, és a kijelzett lépésszám helyes.
- [ ] **G2** · Fotontáblázat (`ttk.Treeview` CTk-stílussal): oszlopok lépésenkénti megjelenése, színkódolt sorok, görgetés · **1,5 ó**
  *Kész, ha:* N = 1000 mellett is akadás nélkül görget, és a színek a jelmagyarázatnak megfelelnek.
- [ ] **G3** · Manuális/auto mód kapcsoló, beviteli mezők, „🎲” gombok, valós idejű validálás · **0,75 ó**
  *Kész, ha:* hibás bevitelnél piros keret és tooltip jelenik meg, és a futtatás nem indul el.
- [ ] **G4** · Eve megjelenítése: be/ki kapcsoló, aránycsúszka, Eve-oszlopok, lila kiemelés, Eve-ikon a csatornán · **0,75 ó**
  *Kész, ha:* kikapcsolt Eve-nél az Eve-oszlopok rejtve vannak, bekapcsoltnál a módosított fotonok ki vannak emelve.
- [ ] **G5** · QBER-kijelző (progress bar + %, várható érték), riasztó/elfogadó banner, figyelmeztető ablak, a rejtve maradás valószínűsége · **0,75 ó**
  *Kész, ha:* a küszöb túllépésekor piros banner jelenik meg, alatta zöld, és a végső kulcs csak elfogadásnál látszik.
- [ ] **G6** · Lépésmagyarázó szövegek (10 állapot), tooltipek, ←/→ billentyűk, sötét/világos téma, súgóablak · **0,75 ó**
  *Kész, ha:* minden lépésnél van legalább 2 mondatos magyarázat a nyilvános/titkos jelöléssel.
- [ ] **G7** · Hibakezelés és szélsőséges esetek: N = 1, N = 5000, 0 sifted bit, paraméterváltás futás közben (automatikus reset) · **0,5 ó**
  *Kész, ha:* a manuális tesztlista „Edge case” szakasza hiba nélkül lefut.

### 3.4 Tesztelés & Validáció (3,0 óra)

- [ ] **T1** · Core tesztek: a 4 polarizáció × 2 bázis determinisztikus és valószínűségi esetei · **0,75 ó**
- [ ] **T2** · Statisztikai tesztek fix seeddel: QBER = 0% (Eve nélkül), ≈25% (Eve 100%), ≈12,5% (Eve 50%), sifting ≈ 50% · **0,75 ó**
- [ ] **T3** · Állapotgép- és parsing-tesztek: léptetés, visszalépés, reset, reprodukálhatóság, bevitel validálása · **0,5 ó**
- [ ] **T4** · `docs/manual_test_checklist.md` összeállítása és végrehajtása (az összes értékelési szempontra) · **0,5 ó**
- [ ] **T5** · A kész exe tesztelése tiszta Windows 10/11 gépen: indulás, futás, méret és indulási idő mérése · **0,5 ó**

### 3.5 Dokumentáció & Build (3,5 óra)

- [ ] **D1** · Dokumentáció: bevezetés + elméleti háttér (bázisok, Born-szabály, intercept-resend, a 25% levezetése) · **1,0 ó**
- [ ] **D2** · Dokumentáció: architektúra (MVC, állapotgép) + felhasználói útmutató képernyőképekkel · **1,0 ó**
- [ ] **D3** · Dokumentáció: tesztelés és mérési eredmények (QBER az Eve-arány függvényében táblázatban), korlátok · **0,5 ó**
- [ ] **D4** · Végső release-build (`v1.0.0` tag), GitHub Release az exe-vel, forráskód-ZIP · **0,5 ó**
- [ ] **D5** · Közös végső átnézés, PDF-export (≥ 3 oldal ellenőrzése), beadás · **0,5 ó**

### 3.6 Óraösszesítő

| Kategória | Taskok | Óra |
|-----------|--------|-----|
| Setup & Csomagolásbiztosítás | S1–S4 | 2,5 |
| Kvantumlogika & Állapotgép | Q1–Q7 | 5,0 |
| Grafikus Felület (UI/UX) | G1–G7 | 6,0 |
| Tesztelés & Validáció | T1–T5 | 3,0 |
| Dokumentáció & Build | D1–D5 | 3,5 |
| **Összesen** | **28 task** | **20,0** |

---

## 4. Git és Együttműködési Szabályok

### 4.1 Branching stratégia (GitHub Flow)

| Branch | Cél | Szabály |
|--------|-----|---------|
| `main` | Mindig működő, buildelhető állapot | Védett: közvetlen push tilos, csak PR-ral, zöld CI-jal és 1 jóváhagyással |
| `feat/<ID>-<rövid-leírás>` | Új funkció | pl. `feat/Q3-eve-intercept`, `feat/G5-qber-alarm` |
| `fix/<ID>-<leírás>` | Hibajavítás | pl. `fix/G7-empty-sifted-crash` |
| `test/<ID>-<leírás>` | Csak tesztek | pl. `test/T2-statistics` |
| `docs/<ID>-<leírás>` | Dokumentáció | pl. `docs/D1-theory` |
| `build/<ID>-<leírás>` | Csomagolás, CI | pl. `build/S3-pyinstaller-spec` |

**Szabályok:**

- Egy branch egy taskot (Issue-t) fed le. Élettartama legfeljebb 2–3 nap.
- Munka kezdése előtt `git pull --rebase origin main`.
- Release-ek: `v0.1.0` (smoke exe), `v0.5.0` (alapverzió Eve nélkül), `v1.0.0` (beadás). Ezek annotált tagek GitHub Release-szel.

### 4.2 Commit konvenciók (Conventional Commits)

Formátum: `<típus>(<scope>): <rövid leírás felszólító módban>`, és a láblécben az issue-hivatkozás (pl. `Closes #12`).

| Típus | Mikor | Példa |
|-------|-------|-------|
| `feat` | Új funkció | `feat(core): add intercept-resend attack for Eve` |
| `fix` | Hibajavítás | `fix(gui): prevent crash when sifted key is empty` |
| `test` | Teszt | `test(core): verify QBER ≈ 25% with full interception` |
| `docs` | Dokumentáció | `docs: add QBER derivation to theory chapter` |
| `build` | PyInstaller, függőségek | `build: collect customtkinter data files in onefile build` |
| `ci` | GitHub Actions | `ci: build Windows exe artifact on PRs` |
| `refactor` | Viselkedést nem változtató átírás | `refactor(core): extract bit flip from send_and_measure` |
| `style` | Formázás | `style: apply ruff format` |

A commitok nyelve angol (rövid, egységes), az Issue-k és a dokumentáció nyelve magyar.

### 4.3 Pull Request és review szabályok

**A PR-sablon tartalma (`.github/pull_request_template.md`):**

- **Mit változtat?** 1–3 mondatos leírás
- **Kapcsolódó task:** `Closes #<issue>` és a Task ID
- **Ellenőrzőlista:**
  - [ ] `pytest` lokálisan zöld
  - [ ] A `bb84_core.py` nem importál GUI-modult
  - [ ] Új logikához van teszt
  - [ ] GUI-változásnál képernyőkép csatolva
  - [ ] Ha a build érintett: az exe lokálisan elindul
  - [ ] Az interfész-szerződés nem változott (vagy egyeztetve lett)

**Review szabályok:**

| Szabály | Részlet |
|---------|---------|
| Kötelező jóváhagyás | 1 (a másik tag). Saját PR-t nem lehet merge-elni jóváhagyás nélkül |
| Válaszidő | 24 órán belül, beadás előtti héten 12 órán belül |
| PR-méret | Legfeljebb kb. 300 változtatott sor. A nagyobbakat bontani kell |
| CI | A `pytest` és a Windows build job zöld, különben nincs merge |
| Merge-módszer | **Squash and merge** (a `main`-en egy task = egy commit). Branch törlése merge után |
| Review fókusz | Fizikai helyesség (core), réteghatárok, olvashatóság, UX-konzisztencia |
| Megjegyzések | `nit:` = nem blokkoló apróság, `blocking:` = javítani kell merge előtt |
| Interfész-szerződés | Módosítása csak közös egyeztetés után, külön PR-ban |

### 4.4 Egyéb szabályok

- **`.gitignore`:** `.venv*/`, `__pycache__/`, `build/`, `dist/`, `*.exe`, `.pytest_cache/`, `.idea/`, `.vscode/`. A `bb84.spec` fájl **verziókezelt**.
- **Issue-tábla:** GitHub Projects, oszlopok: `Backlog` → `In progress` → `Review` → `Done`. Minden kártya címe a Task ID-val kezdődik.
- **Titkok:** nincsenek. Tokent vagy jelszót nem commitolunk.
- **Kódstílus:** PEP 8, típusannotációk a publikus API-n, `ruff format` commit előtt.
