import customtkinter as ctk
from bb84_core import BB84Simulation, SimConfig, Step, parse_bits, parse_bases, estimate_qber
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
FONT_INFO = ("Segoe UI", 16)
FONT_SUBINFO = ("Segoe UI", 14, "italic")
FONT_TABLE_HEADER = ("Segoe UI", 14, "bold")
FONT_TABLE_CELL = ("Consolas", 15, "bold")
FONT_KEY_VALUE = ("Consolas", 17, "bold")

class BB84App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BB84 Kvantum-kriptográfiai Szimulátor")
        self.geometry("1150x790")
        self.minsize(960, 660)

        self.default_border = ctk.ThemeManager.theme["CTkEntry"]["border_color"]

        self.sim = BB84Simulation(SimConfig(n_bits=16))
        self.fields = {}
        self._config_dirty = False

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
        self.bits_var.trace_add("write", lambda *_: self._on_param_edited())
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
        self.step_label.pack(pady=(12, 6))

        self.table_frame = ctk.CTkScrollableFrame(self.right_frame, orientation="horizontal", height=240, corner_radius=10)
        self.table_frame.pack(fill="x", padx=14, pady=4)

        self.control_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.control_frame.pack(side="bottom", fill="x", padx=14, pady=(4, 12))

        self.btn_reset = ctk.CTkButton(self.control_frame, text="Reset", font=FONT_BUTTON, height=40, corner_radius=8, command=self._on_reset)
        self.btn_reset.pack(side="left", padx=6, pady=4, expand=True, fill="x")

        self.btn_prev = ctk.CTkButton(self.control_frame, text="<< Vissza", font=FONT_BUTTON, height=40, corner_radius=8, command=self._on_prev)
        self.btn_prev.pack(side="left", padx=6, pady=4, expand=True, fill="x")

        self.btn_next = ctk.CTkButton(self.control_frame, text="Előre >>", font=FONT_BUTTON, height=40, corner_radius=8, command=self._on_next)
        self.btn_next.pack(side="left", padx=6, pady=4, expand=True, fill="x")

        self.btn_run_to_end = ctk.CTkButton(self.control_frame, text="Végig >>", font=FONT_BUTTON, height=40, corner_radius=8, command=self._on_run_to_end)
        self.btn_run_to_end.pack(side="left", padx=6, pady=4, expand=True, fill="x")

        self.info_card = ctk.CTkFrame(self.right_frame, corner_radius=10)
        self.info_card.pack(fill="both", expand=True, padx=14, pady=8)
        self.info_label = ctk.CTkLabel(
            self.info_card,
            text="",
            wraplength=720,
            font=FONT_INFO,
            justify="center"
        )
        self.info_label.pack(padx=16, pady=(12, 6))

        self.stats_frame = ctk.CTkFrame(self.info_card, fg_color="transparent")
        self.stats_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.update_ui()
        self._refresh_layout()

    def _on_param_edited(self):
        self._config_dirty = True
        if self._revalidate() and self.sim.step != Step.SETUP:
            self._on_apply_config()

    def _on_reset(self):
        self.sim.reset()
        self.update_ui()

    def _on_prev(self):
        self.sim.prev_step()
        self.update_ui()

    def _on_next(self):
        if not self._revalidate():
            return
        if self._config_dirty:
            self._on_apply_config()
        self.sim.next_step()
        self.update_ui()

    def _on_run_to_end(self):
        if not self._revalidate():
            return
        if self._config_dirty:
            self._on_apply_config()
        self.sim.run_to_end()
        self.update_ui()

    def update_ui(self):
        state = self.sim.state
        self.step_label.configure(text=f"Lépés: {int(state.step)}/9 - {state.step.name}")
        step = STEP_DESCRIPTIONS.get(state.step, "Ismeretlen lépés")
        if state.step == Step.SIFTING and not state.sifted_indices:
            step += "\nEgyetlen bázis sem egyezett (0 szitált bit)!"
        self.info_label.configure(text=step)
        self._render_table()
        self._render_info_card()
        self._revalidate()

    def _on_noise_change(self, value):
        self.lbl_noise.configure(text=f"Csatornazaj: {value:.2f}")
        self._on_param_edited()

    def _on_apply_config(self):
        if not self._revalidate():
            return

        try:
            n = int(self.bits.get())
            n = max(8, min(n, 32))
        except ValueError:
            n = 16

        if self.bits_var.get() != str(n):
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
        self._config_dirty = False
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
        height = min(row_count * 34 + 35, 310)
        self.table_frame.configure(height=height)

        for r, (label_text, values) in enumerate(rows):
            header = ctk.CTkLabel(self.table_frame, text=label_text, width=110, anchor="w", font=FONT_TABLE_HEADER)
            header.grid(row=r, column=0, padx=(6, 12), pady=2, sticky="w")

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
        self._on_param_edited()

    def _on_eve_toggle(self):
        if self.eve.get() == 1:
            self.lbl_eve_ratio.pack(fill="x", padx=14, pady=(4, 2), before=self.btn_apply)
            self.slider_eve_ratio.pack(fill="x", padx=14, pady=(0, 8), before=self.btn_apply)
        else:
            self.lbl_eve_ratio.pack_forget()
            self.slider_eve_ratio.pack_forget()

        self._refresh_layout()
        self._on_param_edited()

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
            text="⚄",
            width=38,
            height=36,
            font=FONT_BUTTON,
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

        var.trace_add("write", lambda *_: self._on_param_edited())
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
        self._on_param_edited()

    def _randomize(self, key):
        try:
            n = int(self.bits.get())
            if not (8 <= n <= 32):
                n = 16
        except ValueError:
            n = 16
        f = self.fields[key]
        f["var"].set("".join(random.choice(f["alphabet"]) for _ in range(n)))

    def _revalidate(self) -> bool:
        try:
            n = int(self.bits.get())
            if not (8 <= n <= 32):
                n = None
        except ValueError:
            n = None

        if n is None:
            self.bits.configure(border_color="red")
            ok = False
        else:
            self.bits.configure(border_color=self.default_border)
            ok = True

        if self.mode.get() == "Manuális":
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

        at_start = self.sim.step == Step.SETUP
        at_end = self.sim.step == Step.RESULT

        self.btn_apply.configure(state="normal" if ok else "disabled")
        self.btn_prev.configure(state="disabled" if at_start else "normal")
        self.btn_next.configure(state="normal" if (ok and not at_end) else "disabled")
        self.btn_run_to_end.configure(state="normal" if (ok and not at_end) else "disabled")

        return ok

    def _render_info_card(self):
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        state = self.sim.state
        config = self.sim.config

        if getattr(state, "qber", None) is None:
            return

        threshold = getattr(config, "qber_threshold", 0.11)
        sifted = state.sifted_indices

        qber = estimate_qber(state.alice_bits, state.bob_bits, sifted) if sifted else 0.0
        has_enough_bits = bool(sifted) and len(sifted) > len(state.sample_indices)
        is_safe = has_enough_bits and qber <= threshold
        bgcolor = "#2E7D32" if is_safe else "#C62828"

        qber_card = ctk.CTkFrame(self.stats_frame, fg_color=("gray88", "gray20"), corner_radius=8)
        qber_card.pack(fill="x", padx=6, pady=(2, 6))

        qber_header = ctk.CTkFrame(qber_card, fg_color="transparent")
        qber_header.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(
            qber_header,
            text=f"Mért QBER: {qber*100:.1f}%",
            font=FONT_LABEL,
            anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            qber_header,
            text=f"Küszöbérték: {threshold*100:.1f}%",
            font=FONT_TABLE_HEADER,
            text_color=("gray35", "gray70"),
            anchor="e"
        ).pack(side="right")

        pb_container = ctk.CTkFrame(qber_card, fg_color="transparent")
        pb_container.pack(fill="x", padx=12, pady=(2, 8))

        pb = ctk.CTkProgressBar(pb_container, height=14, corner_radius=7, progress_color=bgcolor)
        pb.pack(fill="x")
        pb.set(min(qber, 1.0))

        threshold_marker = ctk.CTkFrame(pb_container, width=3, height=18, fg_color="white", corner_radius=0)
        threshold_marker.place(relx=threshold, rely=0.5, anchor="center")

        if config.eve_present:
            intercepted_sifted = sum(
                1 for i in sifted
                if i < len(state.eve_bases) and state.eve_bases[i] is not None
            )
            p_hidden = (0.75) ** intercepted_sifted

            lbl_eve_sneaky = ctk.CTkLabel(
                qber_card,
                text=f"Eve rejtve maradásának esélye: {p_hidden*100:.2f}%",
                text_color="#FFB74D",
                font=FONT_SUBINFO
            )
            lbl_eve_sneaky.pack(fill="x", padx=12, pady=(0, 8))

        if state.step == Step.RESULT:
            if is_safe:
                lbl_text = "Biztonságos! A kulcs el lett fogadva!"
            elif not has_enough_bits:
                lbl_text = "Nem maradt elég szitált bit – a kulcs el lett dobva!"
            else:
                lbl_text = "VESZÉLY! Magas lehallgatásra utaló jelek miatt a kulcs el lett dobva!"

            lbl_banner = ctk.CTkLabel(
                self.stats_frame,
                fg_color=bgcolor,
                text=lbl_text,
                text_color="white",
                font=FONT_BUTTON,
                corner_radius=8
            )
            lbl_banner.pack(fill="x", padx=6, pady=(2, 6), ipady=6)

            if is_safe and getattr(state, "final_key", None):
                key_card = ctk.CTkFrame(self.stats_frame, fg_color=("gray88", "gray20"), corner_radius=8)
                key_card.pack(fill="x", padx=6, pady=(2, 4))

                ctk.CTkLabel(
                    key_card,
                    text="Végső közös kulcs:",
                    font=FONT_LABEL,
                    anchor="w"
                ).pack(side="left", padx=(12, 8), pady=8)

                key_str = " ".join(map(str, state.final_key))
                ctk.CTkLabel(
                    key_card,
                    text=key_str,
                    font=FONT_KEY_VALUE,
                    fg_color=("gray80", "gray28"),
                    corner_radius=6,
                    padx=10,
                    pady=4
                ).pack(side="left", padx=(0, 12), pady=8)
