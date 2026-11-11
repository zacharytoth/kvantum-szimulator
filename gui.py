import customtkinter as ctk
from bb84_core import BB84Simulation, SimConfig, Step, parse_bits, parse_bases
import random

def basis_to_symbol(basis) -> str:
    if basis is None:
        return "-"
    return "+" if basis.name == "RECTILINEAR" else "x"


def photon_to_symbol(photon) -> str:
    if photon is None:
        return "-"
    angle = round(photon.angle % 180)
    symbols = {
        0: "→",
        45: "↗",
        90: "↑",
        135: "↖"
    }
    return symbols.get(angle, "?")

STEP_DESCRIPTIONS = {
    Step.SETUP:
        "A szimuláció előkészítési fázisa. Állítsd be a bitek számát, a csatornazajt és Eve jelenlétét, "
        "majd kattints az Alkalmaz gombra vagy léptess előre az indításhoz."
    ,
    Step.ALICE_BITS:
        "Alice előállítja az N darab nyers véletlen klasszikus bitet. "
        "Ezek alkotják a leendő titkos kulcs alapját, és Alice privát memóriájában maradnak."
    ,
    Step.ALICE_BASES:
        "Alice minden egyes bithez véletlenszerűen kiválaszt egy polarizációs bázist (+ vagy x). "
        "Ezt a bázisválasztást egyelőre nem osztja meg senkivel."
    ,
    Step.ENCODE:
        "Alice a biteket és bázisokat fotonok polarizációs állapotává kódolja: "
        "+ bázisnál 0→→, 1→↑; x bázisnál 0→↗, 1→↖. A fotonok készen állnak az átvitelre."
    ,
    Step.TRANSMIT:
        "A fotonok áthaladnak a kvantumcsatornán, kitéve a csatornazajnak. "
        "Ha Eve aktív, elfogja és megméri a fotonokat, megváltoztatva az állapotukat a továbbküldés előtt."
    ,
    Step.BOB_BASES:
        "Bob függetlenül és véletlenszerűen választ mérési bázist (+ vagy x) minden egyes beérkező fotonhoz. "
        "Nem tudja előre, hogy Alice melyik pozícióban milyen bázist használt."
    ,
    Step.BOB_MEASURE:
        "Bob elvégzi a projektív kvantummérést a saját bázisaiban. "
        "Egyező bázisnál az eredmény determinisztikus, míg eltérő bázisnál 50% eséllyel hibás bitet kap."
    ,
    Step.SIFTING:
        "Alice és Bob nyilvánosan megosztják a mérési bázisaikat, de a bitek titkosak maradnak. "
        "Az eltérő bázisú pozíciókat kidobják; a megmaradt bitek képezik a szitált (sifted) kulcsot."
    ,
    Step.QBER:
        "A felek nyilvánosan feláldoznak és összehasonlítanak egy mintát a szitált bitekből a hibaarány (QBER) ellenőrzésére. "
        "A tesztelt biteket ezután véglegesen törlik a kulcsból."
    ,
    Step.RESULT:
        "Ha a mért QBER meghaladja a küszöbértéket, riasztás lép életbe és a felek eldobják a kulcsot. "
        "Megfelelően alacsony hiba esetén a megmaradt bitek adják a végleges, biztonságos titkos kulcsot."
    ,
}

FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_LABEL = ("Segoe UI", 15, "bold")
FONT_ENTRY = ("Consolas", 15)
FONT_BUTTON = ("Segoe UI", 15, "bold")
FONT_INFO = ("Segoe UI", 18)
FONT_TABLE_HEADER = ("Segoe UI", 14, "bold")
FONT_TABLE_CELL = ("Consolas", 15, "bold")

class BB84App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BB84 Kvantum-kriptográfiai Szimulátor")
        self.geometry("1150x740")
        self.minsize(960, 660)

        self.default_border = ctk.ThemeManager.theme["CTkEntry"]["border_color"]

        self.sim = BB84Simulation(SimConfig(n_bits=16))
        self.fields = {}

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.param_frame = ctk.CTkFrame(self, width=300, corner_radius=12)
        self.param_frame.grid(row=0, column=0, padx=(14, 8), pady=14, sticky="nsew")
        self.param_frame.grid_propagate(False)

        self.param_title = ctk.CTkLabel(self.param_frame, text="Beállítások", font=FONT_TITLE)
        self.param_title.pack(padx=14, pady=(16, 12))

        self.mode = ctk.CTkSegmentedButton(
            self.param_frame,
            values=["Automata", "Manuális"],
            font=FONT_BUTTON,
            height=36,
            command=self._on_mode_change
        )
        self.mode.set("Automata")
        self.mode.pack(fill="x", padx=14, pady=(0, 10))

        self.lbl_bits = ctk.CTkLabel(self.param_frame, text="Bitek száma (8-32):", font=FONT_LABEL, anchor="w")
        self.lbl_bits.pack(fill="x", padx=14, pady=(8, 2))

        self.bits_var = ctk.StringVar(value="16")
        self.bits_var.trace_add("write", lambda *_: self._revalidate())
        self.bits = ctk.CTkEntry(
            self.param_frame,
            textvariable=self.bits_var,
            font=FONT_ENTRY,
            height=36
        )
        self.bits.pack(fill="x", padx=14, pady=(0, 8))

        self.lbl_noise = ctk.CTkLabel(self.param_frame, text="Csatornazaj: 0.00", font=FONT_LABEL, anchor="w")
        self.lbl_noise.pack(fill="x", padx=14, pady=(8, 2))
        self.noise = ctk.CTkSlider(self.param_frame, from_=0.0, to=0.5, number_of_steps=50, command=self._on_noise_change)
        self.noise.set(0.0)
        self.noise.pack(fill="x", padx=14, pady=(2, 10))

        self.eve = ctk.CTkSwitch(self.param_frame, text="Eve jelen van", font=FONT_LABEL, command=self._on_eve_toggle)
        self.eve.pack(fill="x", padx=14, pady=(8, 10))
        self.lbl_eve_ratio = ctk.CTkLabel(self.param_frame, text="Eve arány: 1.00", font=FONT_LABEL, anchor="w")
        self.slider_eve_ratio = ctk.CTkSlider(self.param_frame, from_=0.0, to=1.0, number_of_steps=20, command=self._on_eve_ratio_change)
        self.slider_eve_ratio.set(1.0)

        self._make_field("alice_bits",  "Alice bitjei (0/1):",   parse_bits,  "01")
        self._make_field("alice_bases", "Alice bázisai (+/x):",  parse_bases, "+x")
        self._make_field("bob_bases",   "Bob bázisai (+/x):",    parse_bases, "+x")
        self._make_field("eve_bases",   "Eve bázisai (+/x):",    parse_bases, "+x")

        self.btn_apply = ctk.CTkButton(
            self.param_frame,
            text="Alkalmaz",
            font=FONT_BUTTON,
            height=40,
            corner_radius=8,
            command=self._on_apply_config
        )
        self.btn_apply.pack(fill="x", padx=14, pady=(16, 14))

        self.right_frame = ctk.CTkFrame(self, corner_radius=12)
        self.right_frame.grid(row=0, column=1, padx=(8, 14), pady=14, sticky="nsew")

        self.step_label = ctk.CTkLabel(self.right_frame, text="Lépés: 0/9 - SETUP", font=FONT_TITLE)
        self.step_label.pack(pady=(16, 10))

        self.table_frame = ctk.CTkScrollableFrame(self.right_frame, orientation="horizontal", height=250, corner_radius=10)
        self.table_frame.pack(fill="x", padx=14, pady=6)

        self.info_card = ctk.CTkFrame(self.right_frame, corner_radius=10)
        self.info_card.pack(fill="both", expand=True, padx=14, pady=10)
        self.info_label = ctk.CTkLabel(
            self.info_card,
            text="",
            wraplength=680,
            font=FONT_INFO,
            justify="center"
        )
        self.info_label.pack(expand=True, padx=20, pady=20)

        self.control_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.control_frame.pack(fill="x", padx=14, pady=(4, 14))

        self.btn_reset = ctk.CTkButton(self.control_frame, text="Reset", font=FONT_BUTTON, height=40, corner_radius=8, command=self._on_reset)
        self.btn_reset.pack(side="left", padx=6, pady=4, expand=True, fill="x")

        self.btn_prev = ctk.CTkButton(self.control_frame, text="<< Vissza", font=FONT_BUTTON, height=40, corner_radius=8, command=self._on_prev)
        self.btn_prev.pack(side="left", padx=6, pady=4, expand=True, fill="x")

        self.btn_next = ctk.CTkButton(self.control_frame, text="Előre >>", font=FONT_BUTTON, height=40, corner_radius=8, command=self._on_next)
        self.btn_next.pack(side="left", padx=6, pady=4, expand=True, fill="x")

        self.btn_run_to_end = ctk.CTkButton(self.control_frame, text="Végig >>", font=FONT_BUTTON, height=40, corner_radius=8, command=self._on_run_to_end)
        self.btn_run_to_end.pack(side="left", padx=6, pady=4, expand=True, fill="x")

        self.update_ui()
        self._refresh_layout()

    def _on_reset(self):
        self.sim.reset()
        self.update_ui()

    def _on_prev(self):
        self.sim.prev_step()
        self.update_ui()

    def _on_next(self):
        if not self._revalidate():
            return
        self.sim.next_step()
        self.update_ui()

    def _on_run_to_end(self):
        if not self._revalidate():
            return
        self.sim.run_to_end()
        self.update_ui()

    def update_ui(self):
        state = self.sim.state
        self.step_label.configure(text=f"Lépés: {int(state.step)}/9 - {state.step.name}")
        step = STEP_DESCRIPTIONS.get(state.step, "Ismeretlen lépés")
        self.info_label.configure(text=step)
        self._render_table()

    def _on_noise_change(self, value):
        self.lbl_noise.configure(text=f"Csatornazaj: {value:.2f}")

    def _on_apply_config(self):
        if not self._revalidate():
            return

        try:
            n = int(self.bits.get())
            n = max(8, min(n, 32))
        except ValueError:
            n = 16

        self.bits_var.set(str(n))

        noise = float(self.noise.get())
        eve = bool(self.eve.get())
        eve_ratio = float(self.slider_eve_ratio.get())

        manual_alice_bits = None
        manual_alice_bases = None
        manual_bob_bases = None
        manual_eve_bases = None

        if self.mode.get() == "Manuális":
            manual_alice_bits = self.fields["alice_bits"]["parser"](self.fields["alice_bits"]["var"].get(), n)
            manual_alice_bases = self.fields["alice_bases"]["parser"](self.fields["alice_bases"]["var"].get(), n)
            manual_bob_bases = self.fields["bob_bases"]["parser"](self.fields["bob_bases"]["var"].get(), n)
            if eve:
                manual_eve_bases = self.fields["eve_bases"]["parser"](self.fields["eve_bases"]["var"].get(), n)

        sc = SimConfig(
            n_bits=n,
            eve_present=eve,
            noise_rate=noise,
            eve_ratio=eve_ratio,
            manual_alice_bits=manual_alice_bits,
            manual_alice_bases=manual_alice_bases,
            manual_bob_bases=manual_bob_bases,
            manual_eve_bases=manual_eve_bases
        )
        self.sim = BB84Simulation(sc)
        self.update_ui()

    def _render_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        state = self.sim.state
        n = self.sim.config.n_bits

        rows = [
            ("Index:", list(range(n))),
            ("Alice bitjei:", state.alice_bits if state.alice_bits else ["-"] * n),
            ("Alice bázis:", [basis_to_symbol(b) for b in state.alice_bases] if state.alice_bases else ["-"] * n),
            ("Alice fotonjai:", [photon_to_symbol(p) for p in state.photons] if state.photons else ["-"] * n)
        ]

        if self.sim.config.eve_present:
            rows.append(("Eve bázis:", [basis_to_symbol(b) for b in state.eve_bases] if state.eve_bases else ["-"] * n))
            rows.append(("Eve észlelés:", [str(b) if b is not None else "-" for b in state.eve_bits] if state.eve_bits else ["-"] * n))

        rows.extend([
            ("Bob bázis:", [basis_to_symbol(b) for b in state.bob_bases] if state.bob_bases else ["-"] * n),
            ("Bob mérés:", [str(b) if b is not None else "-" for b in state.bob_bits] if state.bob_bits else ["-"] * n)
        ])

        row_count = len(rows)
        height = min(row_count * 34 + 45, 330)
        self.table_frame.configure(height=height)

        for r, (label_text, values) in enumerate(rows):
            header = ctk.CTkLabel(self.table_frame, text=label_text, width=110, anchor="w", font=FONT_TABLE_HEADER)
            header.grid(row=r, column=0, padx=(6, 12), pady=3, sticky="w")

            for c, val in enumerate(values):
                bgcolor = ("gray85", "gray25")

                eve_intercepted = (self.sim.config.eve_ratio and bool(state.eve_bases) and c < len(state.eve_bases) and state.eve_bases[c] is not None)
                photon_modified = (eve_intercepted and bool(state.alice_bases) and c < len(state.alice_bases) and state.alice_bases[c] != state.eve_bases[c])

                if photon_modified and "Eve" in label_text and str(val) != "-":
                    bgcolor = "#6A0DAD"
                elif eve_intercepted and "Eve" in label_text and str(val) != "-":
                    bgcolor = "#3A3A3C"

                cell = ctk.CTkLabel(
                    self.table_frame,
                    text=str(val),
                    width=34,
                    height=28,
                    fg_color=bgcolor,
                    corner_radius=6,
                    font=FONT_TABLE_CELL
                )
                cell.grid(row=r, column=c + 1, padx=2, pady=2)

    def _on_eve_ratio_change(self, value):
        self.lbl_eve_ratio.configure(text=f"Eve arány: {value:.2f}")

    def _on_eve_toggle(self):
        if self.eve.get() == 1:
            self.lbl_eve_ratio.pack(fill="x", padx=14, pady=(4, 2), before=self.btn_apply)
            self.slider_eve_ratio.pack(fill="x", padx=14, pady=(0, 8), before=self.btn_apply)
        else:
            self.lbl_eve_ratio.pack_forget()
            self.slider_eve_ratio.pack_forget()

        self._refresh_layout()

    def _make_field(self, key, label, parser, alphabet):
        frame = ctk.CTkFrame(self.param_frame, fg_color="transparent")
        ctk.CTkLabel(frame, text=label, font=FONT_LABEL, anchor="w").pack(fill="x", pady=(6, 2))
        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", pady=(0, 4))

        var = ctk.StringVar()
        entry = ctk.CTkEntry(row, textvariable=var, font=FONT_ENTRY, height=36)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_dice = ctk.CTkButton(
            row,
            text="🎲",
            width=38,
            height=36,
            font=("Segoe UI Emoji", 16),
            corner_radius=8,
            command=lambda: self._randomize(key)
        )
        btn_dice.pack(side="left")

        field_data = {
            "frame": frame,
            "var": var,
            "entry": entry,
            "parser": parser,
            "alphabet": alphabet
        }

        var.trace_add("write", lambda *_: self._revalidate())
        self.fields[key] = field_data

    def _refresh_layout(self, *args):
        for f in self.fields.values():
            f["frame"].pack_forget()

        if self.mode.get() == "Manuális":
            keys = ["alice_bits", "alice_bases", "bob_bases"] + (["eve_bases"] if self.eve.get() else [])
            for k in keys:
                self.fields[k]["frame"].pack(fill="x", padx=14, before=self.btn_apply)

        self._revalidate()

    def _on_mode_change(self, mode_value=None):
        self._refresh_layout()

    def _randomize(self, key):
        try:
            n = int(self.bits.get())
        except ValueError:
            n = 16
        f = self.fields[key]
        f["var"].set("".join(random.choice(f["alphabet"]) for _ in range(n)))

    def _revalidate(self) -> bool:
        if self.mode.get() != "Manuális":
            self.btn_apply.configure(state="normal")
            self.btn_next.configure(state="normal")
            self.btn_run_to_end.configure(state="normal")
            return True

        try:
            n = int(self.bits.get())
            if not (8 <= n <= 32):
                n = None
        except ValueError:
            n = None

        ok = True
        keys = ["alice_bits", "alice_bases", "bob_bases"] + (["eve_bases"] if self.eve.get() else [])

        for k in keys:
            f = self.fields[k]
            val = f["var"].get()

            if n is None:
                f["entry"].configure(border_color="red")
                ok = False
                continue

            try:
                f["parser"](val, n)
                f["entry"].configure(border_color=self.default_border)
            except ValueError:
                f["entry"].configure(border_color="red")
                ok = False

        state_str = "normal" if ok else "disabled"
        self.btn_apply.configure(state=state_str)
        self.btn_next.configure(state=state_str)
        self.btn_run_to_end.configure(state=state_str)

        return ok
