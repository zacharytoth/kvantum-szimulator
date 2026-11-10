# BB84 Szimulátor: Fejlesztői Munkafolyamat és Build Útmutató

Ez az útmutató összefoglalja a mindennapi fejlesztői teendőket: hogyan tartsd szinkronban a lokális környezetedet a repó frissítésekor (`git pull`), hogyan futtasd a projektet fejlesztői módban, és hogyan készíts önálló `.exe` állományt egy új funkció elkészülte után.

---

## 1. Frissítés (`git pull`) utáni lépések

Amikor a csapattársad beolvaszt egy új funkciót vagy javítást, a saját gépeden hajtsd végre az alábbi lépéseket:

### 1.1. Frissítések letöltése a repóból

Győződj meg róla, hogy a `main` ágon vagy, majd kérd le a legújabb állapotot:

```powershell
git checkout main
git pull --rebase origin main
```

*(Ha éppen egy közös feature-ágon dolgoztok, a saját ágadon állva add ki a `git pull` parancsot.)*

### 1.2. Virtuális környezet aktiválása

Mindig a projekt virtuális környezetében (`.venv`) dolgozz!

```powershell
.\.venv\Scripts\Activate.ps1
```

> **Megjegyzés:** Ha a PowerShell biztonsági hibát jelez (`running scripts is disabled`), futtasd az alábbi parancsot a terminálban:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

### 1.3. Függőségek szinkronizálása

Ha a csapattársad új könyvtárat adott a projekthez, a `requirements.txt` vagy `requirements-dev.txt` megváltozott. Frissítsd a saját csomagjaidat:

```powershell
pip install -r requirements-dev.txt
```

### 1.4. Gyors működés-ellenőrzés

Futtasd le az automatizált teszteket, majd indítsd el a programot Pythonból:

```powershell
# 1. Tesztek ellenőrzése (mindnek zöldnek kell lennie)
pytest

# 2. Alkalmazás indítása tesztüzemmódban
python main.py
```

Ha a tesztek lefutottak és a grafikus ablak elindult, a lokális rendszered készen áll a fejlesztésre.

---

## 2. Első klónozás (ha új gépen kezdesz)

Amennyiben a projektet még nem állítottad be a gépeden:

```powershell
git clone <GITHUB_REPO_URL>
cd bb84-simulator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

---

## 3. Új funkció elkészítése után: Tesztelés és Exe Build

Ha megírtál egy új funkciót (feature) vagy javítottál egy hibát, a kód feltöltése és a végleges build előtt kövesd az alábbi lépéseket:

### 3.1. Kód formázása és tesztelés

```powershell
# Kódformázás és ellenőrzés
ruff check . --fix
ruff format .

# Unit és statisztikai tesztek futtatása
pytest
```

### 3.2. Exe fordítás a `build.ps1` szkripttel

A leggyorsabb és legbiztonságosabb mód az automatizált build szkript futtatása:

```powershell
# Tiszta build a korábbi cache törlésével:
.\build.ps1 -Clean
```

### 3.3. Exe fordítás manuálisan (ha nincs build.ps1 vagy hibát keresel)

Mindig a virtuális környezet Python moduljaként hívd meg a PyInstallert a CustomTkinter beágyazásával:

**Végleges, ablakos futtatható állomány:**
```powershell
python -m PyInstaller --noconfirm --clean --onefile --windowed --name BB84_Simulator --collect-all customtkinter main.py
```

**Debug verzió (ha az exe összeomlana és látni akarod a hibaüzenetet a fekete ablakban):**
```powershell
python -m PyInstaller --noconfirm --clean --onefile --name BB84_Simulator_Debug --collect-all customtkinter main.py
```

---

## 4. Az elkészült Exe futtatása és ellenőrzése

A PyInstaller a lefordított fájlt a `dist/` mappába helyezi:

```powershell
.\dist\BB84_Simulator.exe
```

### Ellenőrzőlista smoke teszthez:
1. **Elindulás:** Megjelenik a CustomTkinter ablak a megfelelő témával és stílusokkal.
2. **Konzolablak hiánya:** A végleges build nem nyit felesleges fekete parancssor ablakot.
3. **Funkcionalitás:** Az új funkció nem dob kezeletlen kivételt a GUI-ban.
4. **Tiszta környezet (opcionális, de javasolt release előtt):** Másold be az exe-t egy **Windows Sandboxba** vagy olyan gépre, ahol nincs telepítve Python, és ellenőrizd a függőségmentes indulást.

---

## 5. Gyakori hibák és gyors elhárításuk

| Hibaüzenet / Jelenség | Kiváltó ok | Megoldás |
|---|---|---|
| `running scripts is disabled on this system` | PowerShell biztonsági házirend blokkolja a venv aktiválást. | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `ModuleNotFoundError: No module named 'customtkinter'` | A build a globális Pythonból futott le, vagy hiányzik a `.venv`-ből. | Aktiváld a venv-et: `.\.venv\Scripts\Activate.ps1`, majd használd a `python -m PyInstaller ...` parancsot `--collect-all customtkinter` kapcsolóval. |
| Az exe kattintásra azonnal bezáródik | A `--windowed` kapcsoló miatt elnyelődött egy futásidejű hiba. | Fordítsd le a debug verziót (`--windowed` nélkül), és indítsd el PowerShellből a hibaüzenet megtekintéséhez. |
| Windows Defender / SmartScreen figyelmeztetés | Nem aláírt, frissen csomagolt onefile exe. | Kattints a *További információ* → *Futtatás mindenképp* gombra. |
