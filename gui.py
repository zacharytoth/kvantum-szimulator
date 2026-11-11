import customtkinter as ctk
from bb84_core import BB84Simulation,SimConfig, Step

class BB84App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BB84 Kvantum-kriptográfiai Szimulátor")
        self.geometry("1100x700")
        self.sim = BB84Simulation()
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0 , weight=1)

        self.param_frame = ctk.CTkFrame(self, width=240)
        self.param_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.param_title = ctk.CTkLabel(self.param_frame, text="Beállítások", font=("Arial",16, "bold"))
        self.param_title.pack(padx=10, pady=10)

        self.lbl_bits = ctk.CTkLabel(self.param_frame, text="Bitek száma (8-32):", anchor="w")
        self.lbl_bits.pack(fill="x", padx=10, pady=(10,0))
        self.bits = ctk.CTkEntry(self.param_frame)
        self.bits.insert(0, "16")
        self.bits.pack(fill="x", padx=10, pady=5)

        #Csatornazaj csuszka
        self.lbl_noise = ctk.CTkLabel(self.param_frame, text="Csatornazaj: 0.0", anchor="w")
        self.lbl_noise.pack(fill="x", padx=10, pady=(10,0))
        self.noise = ctk.CTkSlider(self.param_frame,from_=0.0, to=0.5, number_of_steps=50, command=self._on_noise_change)
        self.noise.set(0.0)
        self.noise.pack(fill="x", padx=10, pady=5)

        #Eve lehallgatas
        self.eve = ctk.CTkSwitch(self.param_frame, text="Eve jelen van")
        self.eve.pack(fill="x", padx=10, pady=(10,15))

        #Alkalmaz gomb
        self.btn_apply = ctk.CTkButton(self.param_frame, text="Alkalmaz", command=self._on_apply_config)
        self.btn_apply.pack(fill="x", padx=10, pady=20)

        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.step_label = ctk.CTkLabel(self.right_frame, text="Lépés: 0/9 - SETUP", font=("Arial", 16, "bold"))
        self.step_label.pack(pady=10)

        self.info_card = ctk.CTkFrame(self.right_frame)
        self.info_card.pack(fill="both", expand=True, padx=10, pady=10)
        self.info_label = ctk.CTkLabel(self.info_card, text="A szimuláció indításra kész.", wraplength=600)
        self.info_label.pack(padx=10, pady=10)

        self.control_frame = ctk.CTkFrame(self.right_frame)
        self.control_frame.pack(fill="x", padx=10, pady=10)

        self.btn_reset = ctk.CTkButton(self.control_frame, text="Reset", command=self._on_reset)
        self.btn_reset.pack(side="left", padx=5, pady=5, expand=True)

        self.btn_prev = ctk.CTkButton(self.control_frame, text="<< Vissza", command=self._on_prev)
        self.btn_prev.pack(side="left", padx=5, pady=5, expand=True)

        self.btn_next = ctk.CTkButton(self.control_frame, text="Előre >>", command=self._on_next)
        self.btn_next.pack(side="left", padx=5, pady=5, expand=True)

        self.btn_run_to_end = ctk.CTkButton(self.control_frame, text="Végig >>", command=self._on_run_to_end)
        self.btn_run_to_end.pack(side="left", padx=5, pady=5, expand=True)


    def _on_reset(self):
        self.sim.reset()
        self.update_ui()

    def _on_prev(self):
        self.sim.prev_step()
        self.update_ui()

    def _on_next(self):
        self.sim.next_step()
        self.update_ui()

    def _on_run_to_end(self):
        self.sim.run_to_end()
        self.update_ui()

    def update_ui(self):
        state = self.sim.state
        self.step_label.configure(text=f"Lépés: {int(state.step)}/9 - {state.step.name}")

    def _on_noise_change(self, value):
        self.lbl_noise.configure(text=f"Csatornazaj: {value:.2f}")

    def _on_apply_config(self):
        try:
            n = int(self.bits.get())
            if n < 8:
                n = 8
            elif n>32:
                n=32
        except ValueError:
            n=16
        self.bits.delete(0, "end")
        self.bits.insert(0, str(n))

        noise = float(self.noise.get())
        eve = bool(self.eve.get())

        sc = SimConfig(n_bits=n, eve_present=eve, noise_rate=noise)
        self.sim = BB84Simulation(sc)
        self.update_ui()