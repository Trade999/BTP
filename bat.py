import math
import os
import sys
import json
import csv
import uuid
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class BTPtk:
    """Interface 100% Tkinter pour les calculs BTP. Pas de terminal."""

    # Palette
    BG = "#1e1e2e"
    BG2 = "#181825"
    FG = "#cdd6f4"
    ACCENT = "#89b4fa"
    GREEN = "#a6e3a1"
    YELLOW = "#f9e2af"
    RED = "#f38ba8"
    BTN = "#313244"
    BTN_HOVER = "#45475a"
    TEXT_BG = "#11111b"

    def __init__(self, root):
        self.root = root
        self.root.title("BTPGPT — Calcul BTP")
        self.root.geometry("1280x820")
        self.root.minsize(1000, 640)
        self.root.configure(bg=self.BG)

        # Constantes matériaux
        self.Fe = 400.0
        self.Fc28 = 25.0
        self.gamma_b = 1.5
        self.gamma_s = 1.15

        try:
            st = ttk.Style()
            st.theme_use("clam")
            st.configure("Treeview", background=self.BG2, fieldbackground=self.BG2,
                         foreground=self.FG, rowheight=24)
            st.configure("Treeview.Heading", background=self.BTN, foreground=self.ACCENT)
            st.map("Treeview", background=[("selected", self.ACCENT)],
                   foreground=[("selected", self.BG)])
            st.configure("TCombobox", fieldbackground=self.BTN, background=self.BTN,
                         foreground=self.FG)
        except Exception:
            pass

        self.show_menu()

    # =========================================================
    # UI FRAMEWORK
    # =========================================================
    def clear_root(self):
        for w in self.root.winfo_children():
            w.destroy()

    def make_header(self, title, on_back):
        bar = tk.Frame(self.root, bg=self.BTN, height=54)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)
        tk.Button(bar, text="⬅ Retour", font=("Segoe UI", 10),
                  bg=self.BTN_HOVER, fg=self.FG,
                  activebackground=self.ACCENT, activeforeground=self.BG,
                  relief=tk.FLAT, padx=14, pady=6, cursor="hand2",
                  command=on_back).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Label(bar, text=title, font=("Segoe UI", 14, "bold"),
                 fg=self.ACCENT, bg=self.BTN).pack(side=tk.LEFT, padx=10)

    def show_menu(self):
        self.clear_root()
        outer = tk.Frame(self.root, bg=self.BG)
        outer.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

        tk.Label(outer, text="BTPGPT", font=("Segoe UI", 30, "bold"),
                 fg=self.ACCENT, bg=self.BG).pack()
        tk.Label(outer,
                 text="Bâtiment • Travaux Publics — Pré-dimensionnement • Calcul • Quantitatif",
                 font=("Segoe UI", 10), fg=self.FG, bg=self.BG).pack(pady=(0, 18))

        grid = tk.Frame(outer, bg=self.BG)
        grid.pack(fill=tk.BOTH, expand=True)

        items = [
            ("🧱", "Calcul de brique", self.calc_mur),
            ("🏗️", "Calcul H/e dalle & poutre", self.calc_dalle_poutre),
            ("🪨", "Calcul de moellon en m³", self.calc_moellon),
            ("🏢", "Calcul complet du poteau", self.calc_poteau),
            ("🧱", "Calcul de la semelle isolée", self.calc_semelle),
            ("🏗️", "Calcul complet de la dalle", self.calc_dalle_complete),
            ("🪜", "Calcul complet de l'escalier", self.calc_escalier),
            ("🕳️", "Calcul de la fosse septique", self.calc_fosse),
            ("📋", "Avant métré d'ouvrage", self.avant_metre),
            ("🌬️", "Calcul complet de l'effet du vent", self.calc_vent),
            ("🏗️", "Calcul complet de la poutre", self.calc_poutre_complete),
            ("📊", "Descente de charges", self.descente_charge),
        ]

        for i, (icon, label, cmd) in enumerate(items):
            r, c = divmod(i, 3)
            tk.Button(grid, text=f"{icon}  {label}",
                      font=("Segoe UI", 12), bg=self.BTN, fg=self.FG,
                      activebackground=self.ACCENT, activeforeground=self.BG,
                      relief=tk.FLAT, anchor="w", padx=18, pady=18,
                      cursor="hand2", command=cmd).grid(
                row=r, column=c, sticky="nsew", padx=6, pady=6)

        for c in range(3):
            grid.grid_columnconfigure(c, weight=1)
        for r in range((len(items) + 2) // 3):
            grid.grid_rowconfigure(r, weight=1)

        tk.Button(outer, text="🚪  Quitter", font=("Segoe UI", 12, "bold"),
                  bg=self.RED, fg=self.BG,
                  activebackground="#eba0ac", activeforeground=self.BG,
                  relief=tk.FLAT, padx=20, pady=10, cursor="hand2",
                  command=self.root.destroy).pack(fill=tk.X, pady=(16, 0))

    # =========================================================
    # Generic calculation screen
    #   field_groups : [(group_title, [(key, label, default), ...]), ...]
    #   on_compute   : f(values_dict) -> (text_result, schema_info|None)
    #   schema_drawer: f(canvas, schema_info) -> None  (optional)
    # =========================================================
    def show_calc(self, title, field_groups, on_compute, schema_drawer=None):
        self.clear_root()
        self.make_header(title, self.show_menu)

        main = tk.Frame(self.root, bg=self.BG)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # LEFT : form
        left = tk.Frame(main, bg=self.BG2, width=380)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        left.pack_propagate(False)

        canvas_form = tk.Canvas(left, bg=self.BG2, highlightthickness=0)
        vsb = ttk.Scrollbar(left, orient="vertical", command=canvas_form.yview)
        form_frame = tk.Frame(canvas_form, bg=self.BG2)
        win_id = canvas_form.create_window((0, 0), window=form_frame, anchor="nw")
        canvas_form.configure(yscrollcommand=vsb.set)

        def _on_cfg(e):
            canvas_form.configure(scrollregion=canvas_form.bbox("all"))
            canvas_form.itemconfig(win_id, width=canvas_form.winfo_width())
        form_frame.bind("<Configure>", _on_cfg)
        canvas_form.bind("<Configure>", _on_cfg)

        canvas_form.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(form_frame, text="📝 Données d'entrée",
                 font=("Segoe UI", 13, "bold"),
                 fg=self.YELLOW, bg=self.BG2).pack(anchor="w", padx=14, pady=(14, 6))

        entries = {}
        for group_title, fields in field_groups:
            if group_title:
                tk.Label(form_frame, text=group_title,
                         font=("Segoe UI", 10, "bold"),
                         fg=self.ACCENT, bg=self.BG2).pack(anchor="w", padx=14, pady=(10, 4))
            for key, label, default in fields:
                row = tk.Frame(form_frame, bg=self.BG2)
                row.pack(fill=tk.X, padx=14, pady=3)
                tk.Label(row, text=label, font=("Segoe UI", 9),
                         fg=self.FG, bg=self.BG2, anchor="w", width=24,
                         justify="left").pack(side=tk.LEFT)
                e = tk.Entry(row, font=("Consolas", 10), bg=self.BTN, fg=self.FG,
                             insertbackground=self.ACCENT, relief=tk.FLAT, width=12)
                e.insert(0, str(default))
                e.pack(side=tk.RIGHT, ipady=4, padx=(4, 0))
                entries[key] = e

        # RIGHT : results (top) + schema canvas (bottom)
        right = tk.Frame(main, bg=self.BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        result_text = tk.Text(right, wrap=tk.WORD, font=("Consolas", 10),
                              bg=self.TEXT_BG, fg=self.FG,
                              insertbackground=self.ACCENT,
                              relief=tk.FLAT, padx=10, pady=10,
                              state=tk.DISABLED)
        result_text.pack(fill=tk.BOTH, expand=True)

        schema_canvas = None
        if schema_drawer is not None:
            sf = tk.LabelFrame(right, text=" 📐 Schéma ",
                               font=("Segoe UI", 10, "bold"),
                               fg=self.ACCENT, bg=self.BG2,
                               labelanchor="nw", bd=0)
            sf.pack(fill=tk.X, pady=(8, 0))
            schema_canvas = tk.Canvas(sf, bg=self.TEXT_BG, height=280,
                                      highlightthickness=0)
            schema_canvas.pack(fill=tk.X, expand=False, padx=6, pady=6)

        def compute():
            vals = {}
            for k, e in entries.items():
                vals[k] = e.get().strip().replace(",", ".")
            try:
                text_res, schema_info = on_compute(vals)
            except Exception as ex:
                import traceback
                text_res = f"❌ Erreur : {ex}\n\n{traceback.format_exc()}"
                schema_info = None

            result_text.config(state=tk.NORMAL)
            result_text.delete("1.0", tk.END)
            result_text.insert(tk.END, text_res)
            result_text.config(state=tk.DISABLED)

            if schema_canvas is not None and schema_info is not None:
                schema_canvas.delete("all")
                try:
                    schema_drawer(schema_canvas, schema_info)
                except Exception as ex:
                    schema_canvas.create_text(
                        10, 10, anchor="nw",
                        text=f"Erreur schéma : {ex}",
                        fill=self.RED, font=("Consolas", 9))

        # Buttons row
        bf = tk.Frame(form_frame, bg=self.BG2)
        bf.pack(fill=tk.X, padx=14, pady=14)
        tk.Button(bf, text="🧮 Calculer",
                  font=("Segoe UI", 11, "bold"),
                  bg=self.GREEN, fg=self.BG,
                  activebackground="#94e2d5", activeforeground=self.BG,
                  relief=tk.FLAT, padx=14, pady=8, cursor="hand2",
                  command=compute).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        tk.Button(bf, text="🔄 Reset",
                  font=("Segoe UI", 10),
                  bg=self.BTN_HOVER, fg=self.FG,
                  activebackground=self.ACCENT, activeforeground=self.BG,
                  relief=tk.FLAT, padx=10, pady=8, cursor="hand2",
                  command=lambda: self.show_calc(title, field_groups,
                                                 on_compute, schema_drawer)
                  ).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))

    # =========================================================
    # PARSING HELPERS
    # =========================================================
    @staticmethod
    def _f(vals, key, default=None, allow_zero=True, positive=False):
        raw = vals.get(key, "")
        if raw is None or raw == "":
            if default is not None:
                return default
            raise ValueError(f"Le champ « {key} » est obligatoire.")
        try:
            x = float(raw)
        except ValueError:
            raise ValueError(f"« {key} » n'est pas un nombre valide : {raw!r}")
        if positive and x <= 0:
            raise ValueError(f"« {key} » doit être > 0.")
        if not allow_zero and x == 0:
            raise ValueError(f"« {key} » ne peut pas être 0.")
        return x

    @staticmethod
    def _i(vals, key, default=None):
        raw = vals.get(key, "")
        if raw is None or raw == "":
            if default is not None:
                return default
            raise ValueError(f"Le champ « {key} » est obligatoire.")
        try:
            return int(round(float(raw)))
        except ValueError:
            raise ValueError(f"« {key} » doit être un entier.")

    @staticmethod
    def _opt_float(vals, key):
        raw = vals.get(key, "")
        if raw is None or raw.strip() == "":
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    # =========================================================
    # TEXT FORMATTING
    # =========================================================
    def hr(self, ch="═", n=68):
        return ch * n

    def head(self, title):
        return f"\n{self.hr()}\n  {title}\n{self.hr()}\n"

    def sub(self, title):
        return f"\n── {title} ──\n"

    def line(self, label, value):
        return f"  {label:<32}: {value}"

    def ok(self, label, cond, detail=""):
        mark = "✓" if cond else "✗"
        return f"  {mark} {label}" + (f" — {detail}" if detail else "")

    # =========================================================
    # SCHEMA DRAWER — reinforced concrete section
    # info = {
    #    "sections": [ {"n":4, "dia":12, "b":30, "h":40, "label":"..."} , ... ]
    # }
    # =========================================================
    def draw_rebar_section(self, canvas, info):
        """Draw one or more reinforcement sections side by side."""
        canvas.delete("all")
        try:
            W = canvas.winfo_width() or 800
            H = canvas.winfo_height() or 280
        except Exception:
            W, H = 800, 280

        sections = info.get("sections", [])
        if not sections:
            return

        n_sec = len(sections)
        gap = 30
        sec_w = max(160, (W - gap * (n_sec + 1)) // n_sec)
        sec_h = H - 40

        for idx, sec in enumerate(sections):
            ox = gap + idx * (sec_w + gap)
            oy = 30

            # Répartition des barres
            n = int(sec.get("n", 4))
            n = max(1, min(n, 20))
            b_cm = float(sec.get("b", 30))
            h_cm = float(sec.get("h", 40))
            dia = sec.get("dia", 12)
            label = sec.get("label", f"{n}HA{dia}")

            # Dessiner le rectangle de béton
            rect_w = min(sec_w - 20, 140)
            rect_h = min(sec_h - 40, 160)
            # Scale à partir des dimensions réelles (b x h)
            ratio = b_cm / h_cm if h_cm > 0 else 1.0
            if ratio > 1:
                rect_w = min(rect_w, 170)
                rect_h = int(rect_w / ratio)
            else:
                rect_h = min(rect_h, 170)
                rect_w = int(rect_h * ratio)

            cx = ox + sec_w // 2
            cy = oy + (sec_h - 30) // 2
            x0, y0 = cx - rect_w // 2, cy - rect_h // 2
            x1, y1 = cx + rect_w // 2, cy + rect_h // 2

            # Fond béton
            canvas.create_rectangle(x0, y0, x1, y1,
                                    fill="#45475a", outline=self.ACCENT, width=2)

            # Enrobage (ligne pointillée intérieure)
            env = 10
            canvas.create_rectangle(x0 + env, y0 + env, x1 - env, y1 - env,
                                    outline="#6c7086", dash=(2, 3), width=1)

            # Barres
            pts = self._bar_positions(n, x0 + env, y0 + env, x1 - env, y1 - env)
            r_bar = max(4, min(8, int(dia / 2) + 3))
            for (bx, by) in pts:
                canvas.create_oval(bx - r_bar, by - r_bar, bx + r_bar, by + r_bar,
                                   fill=self.YELLOW, outline="#f9e2af")

            # Étiquettes
            canvas.create_text(cx, oy + 10, text=label,
                               fill=self.GREEN, font=("Segoe UI", 11, "bold"))
            canvas.create_text(cx, y1 + 20,
                               text=f"{b_cm:.0f} × {h_cm:.0f} cm",
                               fill=self.FG, font=("Consolas", 9))
            if sec.get("sous_label"):
                canvas.create_text(cx, y1 + 36, text=sec["sous_label"],
                                   fill=self.YELLOW, font=("Consolas", 9))

    def _bar_positions(self, n, x0, y0, x1, y1):
        """Return bar center positions for n bars around rectangle perimeter."""
        pts = []
        if n <= 0:
            return pts
        if n == 1:
            return [(x0, y0)]
        # Répartir uniformément sur le périmètre (sens horaire depuis coin haut-gauche)
        perimeter = 2 * ((x1 - x0) + (y1 - y0))
        for i in range(n):
            d = i * perimeter / n
            if d < (x1 - x0):
                pts.append((x0 + d, y0))
            elif d < (x1 - x0) + (y1 - y0):
                pts.append((x1, y0 + (d - (x1 - x0))))
            elif d < 2 * (x1 - x0) + (y1 - y0):
                pts.append((x1 - (d - (x1 - x0) - (y1 - y0)), y1))
            else:
                pts.append((x0, y1 - (d - 2 * (x1 - x0) - (y1 - y0))))
        return pts

    # =========================================================
    # 1 - CALCUL DE BRIQUE
    # =========================================================
    def calc_mur(self):
        fields = [
            ("Dimensions", [
                ("L", "Longueur brique L (m)", "0.22"),
                ("l", "Largeur brique l (m)", "0.11"),
                ("T", "Surface totale du mur T (m²)", "20"),
            ]),
            ("Prix (optionnel)", [
                ("pu", "Prix unitaire / brique (Ar)", ""),
            ]),
        ]

        def compute(v):
            L = self._f(v, "L", positive=True)
            l = self._f(v, "l", positive=True)
            T = self._f(v, "T", positive=True)
            pu = self._opt_float(v, "pu")

            s = L * l
            u = T / s
            total = math.ceil(u)

            lines = []
            lines.append(self.head("CALCUL DE BRIQUE"))
            lines.append(self.sub("Surface d'une brique"))
            lines.append("  Formule : S = L × l")
            lines.append(f"  Calcul  : {L} × {l} = {s:.4f} m²")

            lines.append(self.sub("Nombre de briques"))
            lines.append("  Formule : N = T / S")
            lines.append(f"  Calcul  : {T} / {s:.4f} = {u:.2f} U")
            lines.append(f"  ✓ TOTAL À PRÉVOIR : {total} U")

            if pu is not None and pu > 0:
                lines.append(self.sub("Prix"))
                lines.append(f"  Prix total = {total} × {pu:,.0f} Ar")
                lines.append(f"  💰 = {total*pu:,.0f} Ar".replace(",", " "))

            lines.append(f"\n{self.hr('═')}")
            lines.append("  ✓ CALCUL TERMINÉ")
            lines.append(self.hr("═"))
            return "\n".join(lines), None

        self.show_calc("Calcul de brique", fields, compute)

    # =========================================================
    # 2 - CALCUL DALLE & POUTRE (pré-dim)
    # =========================================================
    def calc_dalle_poutre(self):
        fields = [
            ("Portées", [
                ("Ly", "Longueur grande portée Ly (m)", "4.5"),
                ("Lx", "Longueur petite portée Lx (m)", "4.0"),
            ]),
        ]

        def compute(v):
            Ly = self._f(v, "Ly", positive=True)
            Lx = self._f(v, "Lx", positive=True)
            if Lx > Ly:
                raise ValueError("Lx doit être ≤ Ly.")

            mu = Lx / Ly
            e_min, e_max = Lx / 35, Lx / 30
            e = (e_min + e_max) / 2
            h_min, h_max = Ly / 15, Ly / 10
            h = (h_min + h_max) / 2
            b_min, b_max = 0.3 * h, 0.6 * h
            b = (b_min + b_max) / 2

            lines = []
            lines.append(self.head("CALCUL DALLE & POUTRE"))
            lines.append(self.sub("Rapport des portées"))
            lines.append("  Formule : μ = Lx / Ly")
            lines.append(f"  Calcul  : {Lx} / {Ly} = {mu:.3f}")
            lines.append(self.ok("μ ≥ 0.81", mu >= 0.81, f"μ = {mu:.3f}"))

            lines.append(self.sub("Épaisseur de la dalle"))
            lines.append("  Lx/35 ≤ e ≤ Lx/30")
            lines.append(f"  {e_min:.3f} ≤ e ≤ {e_max:.3f} m")
            lines.append(f"  ✓ e = {e:.3f} m = {e*100:.1f} cm")

            lines.append(self.sub("Hauteur de poutre"))
            lines.append("  Ly/15 ≤ h ≤ Ly/10")
            lines.append(f"  {h_min:.3f} ≤ h ≤ {h_max:.3f} m")
            lines.append(f"  ✓ h = {h:.3f} m = {h*100:.1f} cm")

            lines.append(self.sub("Base de poutre"))
            lines.append("  0.3·h ≤ b ≤ 0.6·h")
            lines.append(f"  {b_min:.3f} ≤ b ≤ {b_max:.3f} m")
            lines.append(f"  ✓ b = {b:.3f} m = {b*100:.1f} cm")

            lines.append(f"\n{self.hr('═')}")
            lines.append("  ✓ CALCUL TERMINÉ")
            lines.append(self.hr("═"))
            return "\n".join(lines), None

        self.show_calc("Calcul H/e dalle & poutre", fields, compute)

    # =========================================================
    # 3 - CALCUL MOELLON
    # =========================================================
    def calc_moellon(self):
        fields = [
            ("Dimensions", [
                ("L", "Longueur moellon L (m)", "0.40"),
                ("l", "Largeur moellon l (m)", "0.20"),
                ("e", "Épaisseur moellon e (m)", "0.20"),
                ("T", "Volume total du mur T (m³)", "10"),
            ]),
            ("Prix (optionnel)", [
                ("pu", "Prix unitaire / moellon (Ar)", ""),
            ]),
        ]

        def compute(v):
            L = self._f(v, "L", positive=True)
            l = self._f(v, "l", positive=True)
            e = self._f(v, "e", positive=True)
            T = self._f(v, "T", positive=True)
            pu = self._opt_float(v, "pu")

            vol = L * l * e
            u = T / vol
            total = math.ceil(u)

            lines = []
            lines.append(self.head("CALCUL MOELLON"))
            lines.append(self.sub("Volume d'un moellon"))
            lines.append("  Formule : V = L × l × e")
            lines.append(f"  Calcul  : {L} × {l} × {e} = {vol:.4f} m³")

            lines.append(self.sub("Nombre de moellons"))
            lines.append("  Formule : N = T / V")
            lines.append(f"  Calcul  : {T} / {vol:.4f} = {u:.2f} U")
            lines.append(f"  ✓ TOTAL : {total} U")

            if pu is not None and pu > 0:
                lines.append(self.sub("Prix"))
                lines.append(f"  💰 {total} × {pu:,.0f} = {total*pu:,.0f} Ar".replace(",", " "))

            lines.append(f"\n{self.hr('═')}")
            lines.append("  ✓ CALCUL TERMINÉ")
            lines.append(self.hr("═"))
            return "\n".join(lines), None

        self.show_calc("Calcul de moellon", fields, compute)

    # =========================================================
    # 4 - POTEAU (compression centrée BAEL 91)
    # =========================================================
    def calc_poteau(self):
        fields = [
            ("Type", [
                ("type", "Type (carre / rect / rond)", "carre"),
            ]),
            ("Géométrie", [
                ("a", "Côté a ou diamètre (m)", "0.30"),
                ("b", "Côté b (m, rect uniquement)", "0.30"),
                ("lo", "Longueur libre l₀ (m)", "3.00"),
            ]),
            ("Charges", [
                ("Nu", "Effort normal Nu (MN)", "0.80"),
            ]),
        ]

        def compute(v):
            typ = str(v.get("type", "carre")).strip().lower()
            if typ not in ("carre", "carré", "rect", "rectangulaire", "rond"):
                typ = "carre"
            a = self._f(v, "a", positive=True)
            b = self._f(v, "b", default=a, positive=True)
            lo = self._f(v, "lo", positive=True)
            Nu = self._f(v, "Nu", positive=True)

            Fe, Fc28 = self.Fe, self.Fc28
            gb, gs = self.gamma_b, self.gamma_s

            if typ in ("rond",):
                D = a
                Br = math.pi * (D - 0.02) ** 2 / 4
                D_cm = D * 100
                B_cm2 = math.pi * D_cm ** 2 / 4
                i_cm = D_cm / 4
                u_perim = math.pi * D
                type_nom = "rond"
                geom_label = f"D = {D:.3f} m"
                b_repr = D * 100
                h_repr = D * 100
            else:
                if typ in ("carre", "carré"):
                    b = a
                Br = (a - 0.02) * (b - 0.02)
                a_cm, b_cm = a * 100, b * 100
                B_cm2 = a_cm * b_cm
                Ix = b_cm * a_cm ** 3 / 12
                Iy = a_cm * b_cm ** 3 / 12
                i_x = math.sqrt(Ix / B_cm2)
                i_y = math.sqrt(Iy / B_cm2)
                i_cm = min(i_x, i_y)
                u_perim = 2 * (a + b)
                type_nom = "carré" if abs(a - b) < 1e-9 else "rectangulaire"
                geom_label = f"a×b = {a:.3f} × {b:.3f} m"
                b_repr = a_cm
                h_repr = b_cm

            lf = 0.707 * lo
            lf_cm = lf * 100
            lam = lf_cm / i_cm

            if lam <= 50:
                alpha = 0.85 / (1 + 0.2 * (lam / 35) ** 2)
                domaine = "compression centrée (λ ≤ 50)"
            elif lam <= 70:
                alpha = 0.6 * (50 / lam) ** 2
                domaine = "50 < λ ≤ 70"
            else:
                alpha = 0.6 * (50 / 70) ** 2
                domaine = "⚠ λ > 70 (hors domaine)"

            Fed = Fe / gs
            terme_beton = Br * Fc28 / (0.9 * gb)
            As_calc_m2 = (Nu / alpha - terme_beton) * gs / Fe
            if As_calc_m2 < 0:
                As_calc_m2 = 0
            As_calc_cm2 = As_calc_m2 * 10000

            Amin_1 = 4 * u_perim
            Amin_2 = 0.002 * B_cm2
            Amin = max(Amin_1, Amin_2)
            As_req = max(As_calc_cm2, Amin)

            diam_list = [8, 10, 12, 14, 16, 20, 25, 32]
            nb_min = 6 if type_nom == "rond" else 4
            best = None
            for n in range(nb_min, 25):
                for d in diam_list:
                    aire_un = math.pi * d ** 2 / 4 / 100
                    As_f = n * aire_un
                    if As_f >= As_req:
                        if best is None or As_f < best[0]:
                            best = (As_f, n, d)
                        break
                if best is not None and best[1] <= n:
                    break
            if best is None:
                As_f, n_bar, dia = As_req, 0, 0
            else:
                As_f, n_bar, dia = best

            phi_t_min = dia / 3 if dia else 0
            for pt in [6, 8, 10, 12]:
                if pt >= phi_t_min:
                    dia_cadre = pt
                    break
            else:
                dia_cadre = 12

            if type_nom == "rond":
                petit = a * 100
            else:
                petit = min(a, b) * 100
            st1 = 15 * dia / 10
            st2 = 40
            st3 = petit + 10
            st_cm = min(st1, st2, st3)
            st_prat = math.floor(st_cm)
            st_nod = math.floor(min(10 * dia / 10, 15))

            ft28 = min(0.6 + 0.06 * Fc28, 3.3)
            tau_su = 0.6 * 1.5 ** 2 * ft28
            Ls = dia * Fe / (4 * tau_su) / 10
            Lr = max(40 * dia / 10, Ls)

            lines = []
            lines.append(self.head("CALCUL COMPLET DU POTEAU"))
            lines.append(self.sub("Données"))
            lines.append(self.line("Type", type_nom))
            lines.append(self.line("Géométrie", geom_label))
            lines.append(self.line("l₀", f"{lo:.3f} m"))
            lines.append(self.line("Nu", f"{Nu:.6f} MN"))

            lines.append(self.sub("Section réduite Br (B.8.4.1)"))
            lines.append(f"  Br = {Br:.6f} m²")

            lines.append(self.sub("Flambement"))
            lines.append(f"  lf = 0.707 × {lo:.3f} = {lf:.3f} m")
            lines.append(f"  i  = {i_cm:.3f} cm")
            lines.append(f"  λ  = {lam:.3f}   → {domaine}")
            lines.append(f"  α  = {alpha:.4f}")

            lines.append(self.sub("Armature longitudinale (B.8.4.1)"))
            lines.append(f"  Fed = {Fed:.2f} MPa")
            lines.append(f"  Terme béton = {terme_beton:.6f} MN")
            lines.append(f"  As calculée = {As_calc_cm2:.3f} cm²")

            lines.append(self.sub("Armature minimale (A.8.1.2.1)"))
            lines.append(f"  Amin₁ = 4u = {Amin_1:.3f} cm²")
            lines.append(f"  Amin₂ = 0.2%B = {Amin_2:.3f} cm²")
            lines.append(f"  ✓ Amin = {Amin:.3f} cm²")
            lines.append(f"  ✓ As retenue = {As_req:.3f} cm²")

            lines.append(self.sub("Choix des barres"))
            if n_bar > 0:
                lines.append(f"  ✓ {n_bar} HA{dia}  =  {As_f:.3f} cm²")
            lines.append(self.sub("Cadres et espacement"))
            lines.append(f"  ✓ Cadres HA{dia_cadre}")
            lines.append(f"  Zone courante  : st = {st_prat} cm")
            lines.append(f"  Zone nodale    : st' = {st_nod} cm")

            lines.append(self.sub("Ancrage / recouvrement"))
            lines.append(f"  Ls = {Ls:.2f} cm")
            lines.append(f"  ✓ Lr = {math.ceil(Lr):.0f} cm")

            lines.append(f"\n{self.hr('═')}")
            lines.append("  ✓ CALCUL TERMINÉ")
            lines.append(self.hr("═"))

            schema = None
            if n_bar > 0:
                schema = {"sections": [{
                    "n": n_bar, "dia": dia,
                    "b": b_repr, "h": h_repr,
                    "label": f"{n_bar}HA{dia}",
                    "sous_label": f"cadres HA{dia_cadre} / {st_prat} cm"
                }]}
            return "\n".join(lines), schema

        self.show_calc("Calcul du poteau (BAEL 91)", fields, compute,
                       schema_drawer=self.draw_rebar_section)

    # =========================================================
    # 5 - SEMELLE ISOLÉE
    # =========================================================
    def calc_semelle(self):
        fields = [
            ("Charges", [
                ("Nser", "Charge de service Nser (kN)", "800"),
                ("Nu", "Effort normal Nu (MN)", "1.20"),
            ]),
            ("Sol et poteau", [
                ("sigma", "Contrainte sol σsol (MPa)", "0.20"),
                ("a", "Largeur poteau a (m)", "0.30"),
                ("b", "Longueur poteau b (m)", "0.30"),
                ("env", "Enrobage (cm)", "3"),
            ]),
        ]

        def compute(v):
            Nser_kN = self._f(v, "Nser", positive=True)
            Nu = self._f(v, "Nu", positive=True)
            sigma = self._f(v, "sigma", positive=True)
            a = self._f(v, "a", positive=True)
            b = self._f(v, "b", positive=True)
            env_cm = self._f(v, "env", default=3, positive=True)

            Fe, Fc28 = self.Fe, self.Fc28
            gb, gs = self.gamma_b, self.gamma_s
            Fed = Fe / gs
            env_m = env_cm / 100

            Nser = Nser_kN / 1000
            S_calc = Nser / sigma
            A_calc = math.sqrt(S_calc)
            A = math.ceil(A_calc / 0.05) * 0.05
            if A <= 0:
                A = A_calc
            B = A
            S = A * B

            e_min = (A - a) / 4
            if e_min <= 0:
                raise ValueError("A doit être > a.")
            e = math.ceil(e_min * 100) / 100
            H = e + env_m
            if H < 0.20:
                H = 0.20
                e = H - env_m

            V_sem = (H / 3) * (A * B + a * b + math.sqrt(A * B * a * b))
            P_kN = V_sem * 25
            P_MN = P_kN / 1000
            sigma_v = (Nser + P_MN) / S
            sol_ok = sigma_v <= sigma

            Uc = 2 * (a + b + H)
            Nu_lim = 0.045 * Uc * H * Fc28 / gb
            poin_ok = Nu <= Nu_lim

            As_m2 = Nu * (A - a) / (8 * e * Fed)
            As_cm2 = As_m2 * 10000
            ft28 = min(0.6 + 0.06 * Fc28, 3.3)
            B_mm = B * 1000
            e_mm = e * 1000
            H_mm = H * 1000
            Amin_1 = (0.23 * B_mm * e_mm * ft28 / Fe) / 100
            Amin_2 = (0.001 * B_mm * H_mm) / 100
            Amin = max(Amin_1, Amin_2)
            As_req = max(As_cm2, Amin)

            Lfer = max((A - 2 * env_m) * 100, 0)
            ESP_MAX = 25
            nb_min = max(4, math.ceil(Lfer / ESP_MAX) + 1) if Lfer > 0 else 4

            best = None
            for n in range(nb_min, 14):
                esp = Lfer / (n - 1) if n > 1 else 0
                if esp > ESP_MAX + 1e-9:
                    continue
                for d in [8, 10, 12, 14, 16, 20, 25, 32]:
                    aire = math.pi * d ** 2 / 4 / 100
                    As_f = n * aire
                    if As_f >= As_req:
                        if best is None or As_f < best[0]:
                            best = (As_f, n, d, esp)
                        break
            if best:
                As_f, n_bar, dia, esp_cm = best
            else:
                As_f, n_bar, dia, esp_cm = As_req, 0, 0, 0

            lines = []
            lines.append(self.head("SEMELLE ISOLÉE"))
            lines.append(self.sub("Pré-dimensionnement (15.IV.1)"))
            lines.append("  S = Nser / σsol")
            lines.append(f"  S = {Nser:.6f} / {sigma:.3f} = {S_calc:.4f} m²")
            lines.append(f"  ✓ A = B = {A:.2f} m")

            lines.append(self.sub("Hauteur (15.II.2)"))
            lines.append("  d ≥ (A − a) / 4")
            lines.append(f"  d ≥ ({A:.2f} − {a:.2f}) / 4 = {e_min:.4f} m")
            lines.append(f"  ✓ d = {e:.3f} m")
            lines.append(f"  ✓ H = d + enrobage = {H:.3f} m = {H*100:.1f} cm")

            lines.append(self.sub("Poids propre"))
            lines.append(f"  V = {V_sem:.4f} m³")
            lines.append(f"  P = {P_kN:.2f} kN")

            lines.append(self.sub("Vérification sol"))
            lines.append(f"  σ = {sigma_v:.4f} MPa  ≤  {sigma:.4f}")
            lines.append(self.ok("Sol vérifié", sol_ok))

            lines.append(self.sub("Poinçonnement (indicatif)"))
            lines.append(f"  Uc = {Uc:.3f} m")
            lines.append(f"  Nu,lim = {Nu_lim:.4f} MN")
            lines.append(self.ok("Poinçonnement", poin_ok, f"Nu={Nu:.4f}"))

            lines.append(self.sub("Armatures (méthode des bielles)"))
            lines.append(f"  As calculée = {As_cm2:.3f} cm²")
            lines.append(f"  Amin = {Amin:.3f} cm²")
            lines.append(f"  ✓ As retenue = {As_req:.3f} cm²")
            if n_bar > 0:
                lines.append(f"  ✓ {n_bar} HA{dia} = {As_f:.3f} cm²  (esp. {esp_cm:.1f} cm)")

            lines.append(f"\n{self.hr('═')}")
            lines.append("  ✓ CALCUL TERMINÉ")
            lines.append(self.hr("═"))

            schema = None
            if n_bar > 0:
                schema = {"sections": [{
                    "n": n_bar, "dia": dia,
                    "b": A * 100, "h": H * 100,
                    "label": f"{n_bar}HA{dia} (quadrillage 2 sens)",
                    "sous_label": f"A×B = {A:.2f}×{B:.2f} m ; H={H*100:.0f} cm"
                }]}
            return "\n".join(lines), schema

        self.show_calc("Semelle isolée (DTU 13.12)", fields, compute,
                       schema_drawer=self.draw_rebar_section)

    # =========================================================
    # Placeholders pour les 7 autres fonctions.
    # =========================================================
    # 6 - DALLE COMPLÈTE (Pigeaud, BAEL 91 E.3)
    # =========================================================
    def calc_dalle_complete(self):
        TABLE_MU_ELU = {
            0.40: (0.1101, 0.2500), 0.45: (0.0980, 0.3400),
            0.50: (0.0890, 0.4360), 0.55: (0.0790, 0.5200),
            0.60: (0.0710, 0.6060), 0.65: (0.0630, 0.6700),
            0.70: (0.0560, 0.7300), 0.75: (0.0495, 0.7900),
            0.80: (0.0440, 0.8480), 0.85: (0.0390, 0.8840),
            0.90: (0.0350, 0.9200), 0.95: (0.0317, 0.9600),
            1.00: (0.0290, 1.0000),
        }
    
        def interp(table, alpha):
            keys = sorted(table.keys())
            if alpha <= keys[0]:
                return table[keys[0]]
            if alpha >= keys[-1]:
                return table[keys[-1]]
            for k1, k2 in zip(keys, keys[1:]):
                if k1 <= alpha <= k2:
                    v1, v2 = table[k1], table[k2]
                    t = (alpha - k1) / (k2 - k1)
                    return (v1[0] + t*(v2[0]-v1[0]), v1[1] + t*(v2[1]-v1[1]))
            return table[keys[-1]]
    
        fields = [
            ("Géométrie", [
                ("Ly", "Grande portée Ly (m)", "5.00"),
                ("Lx", "Petite portée Lx (m)", "4.00"),
                ("h", "Épaisseur dalle h (m)", "0.15"),
            ]),
            ("Charges", [
                ("ep_enduit", "Épaisseur enduit (m)", "0.020"),
                ("G_car", "Carreaux (kN/m²)", "0.60"),
                ("Q", "Exploitation Q (kN/m²)", "2.50"),
            ]),
        ]
    
        def compute(v):
            Ly = self._f(v, "Ly", positive=True)
            Lx = self._f(v, "Lx", positive=True)
            h = self._f(v, "h", positive=True)
            ep_enduit = self._f(v, "ep_enduit", default=0.02)
            G_car = self._f(v, "G_car", default=0.6)
            Q = self._f(v, "Q", default=2.5)
            if Lx > Ly:
                raise ValueError("Lx doit être ≤ Ly.")
    
            Fe, Fc28 = self.Fe, self.Fc28
            gb, gs = self.gamma_b, self.gamma_s
            Fed = Fe / gs
    
            alpha = Lx / Ly
            pp = h * 25
            enduit = ep_enduit * 22
            Pu = pp + G_car + enduit
            Pu_MNm2 = Pu / 1000
    
            if alpha < 0.40:
                M0x = Pu_MNm2 * Lx**2 / 8
                M0y = 0.0
                mux = muy = None
                sens = "un seul sens (Lx)"
                Vx = Pu_MNm2 * Lx / 2
                Vy = 0.0
            else:
                mux, muy = interp(TABLE_MU_ELU, alpha)
                M0x = mux * Pu_MNm2 * Lx**2
                M0y = muy * M0x
                sens = "deux sens (Lx et Ly)"
                Vx = Pu_MNm2 * Lx / 2 / (1 + alpha / 2)
                Vy = Pu_MNm2 * Lx / 3
    
            Mtx = 0.85 * M0x
            Mty = 0.85 * M0y if M0y > 0 else 0.0
            Max = 0.30 * M0x
            May = 0.30 * M0y if M0y > 0 else 0.0
    
            Fbu = 0.85 * Fc28 / gb
            bo = 1.0
            d = 0.9 * h
            Mlu = Mtx / (bo * d**2 * Fbu)
            terme = 1 - 2 * Mlu
            if terme < 0:
                alpha_zb = Zb = None
            else:
                alpha_zb = 1.25 * (1 - math.sqrt(terme))
                Zb = d * (1 - 0.4 * alpha_zb)
    
            if Zb and Zb > 0:
                Ax_cm2 = Mtx / (Zb * Fed) * 10000
            else:
                Ax_cm2 = 0
    
            if M0y > 0 and Zb and Zb > 0:
                Ay_cm2 = Mty / (Zb * Fed) * 10000
            else:
                Ay_cm2 = 0
    
            ft28 = min(0.6 + 0.06 * Fc28, 3.3)
            b_cm = bo * 100
            d_cm = d * 100
            Amin = 0.23 * b_cm * d_cm * ft28 / Fe
            Amin_B64 = 0.001 * b_cm * h * 100
            Amin = max(Amin, Amin_B64)
    
            Ax_req = max(Ax_cm2, Amin)
            Ay_req = max(Ay_cm2, Amin) if M0y > 0 else 0
    
            ESP_MAX_X = min(3 * h * 100, 33)
            ESP_MAX_Y = min(4 * h * 100, 45)
    
            def choose(As_req, esp_max):
                best = None
                for dia in [8, 10, 12, 14, 16, 20, 25, 32]:
                    aire = math.pi * dia**2 / 4 / 100
                    for n in range(1, 33):
                        As_f = n * aire
                        if As_f >= As_req:
                            esp = 100 / n
                            if esp <= esp_max + 1e-9:
                                surplus = As_f - As_req
                                if best is None or (surplus, dia, n) < best[0]:
                                    best = ((surplus, dia, n), dia, n, As_f, esp)
                            break
                if best:
                    return best[1], best[2], best[3], best[4]
                return 32, 32, 32 * math.pi * 32**2 / 4 / 100, 100 / 32
    
            dx, nx, Asx, espx = choose(Ax_req, ESP_MAX_X)
            if M0y > 0:
                dy, ny, Asy, espy = choose(Ay_req, ESP_MAX_Y)
            else:
                dy = ny = 0; Asy = espy = 0
    
            tau_x = Vx * 1000 / (b_cm * d_cm) if Vx > 0 else 0
            tau_y = Vy * 1000 / (b_cm * d_cm) if Vy > 0 else 0
            tau_max = max(tau_x, tau_y)
            tau_lim = min(0.20 * Fc28 / gb, 5.0)
            et_ok = tau_max <= tau_lim
    
            lines = []
            lines.append(self.head("CALCUL COMPLET DE LA DALLE"))
            lines.append(self.sub("1. Sens de portée"))
            lines.append(f"  α = Lx/Ly = {Lx}/{Ly} = {alpha:.3f}")
            lines.append(f"  ✓ Sens : {sens}")
    
            lines.append(self.sub("2. Charges"))
            lines.append(f"  pp dalle = {h} × 25 = {pp:.3f} kN/m²")
            lines.append(f"  enduit   = {ep_enduit} × 22 = {enduit:.3f} kN/m²")
            lines.append(f"  carreaux = {G_car:.3f} kN/m²")
            lines.append(f"  ✓ Pu = {Pu:.3f} kN/m² = {Pu_MNm2:.6f} MN/m²")
    
            lines.append(self.sub("3. Moments"))
            if alpha < 0.40:
                lines.append(f"  M0x = Pu·Lx²/8 = {M0x:.4f} MN.m")
                lines.append("  M0y = 0 (un seul sens)")
            else:
                lines.append(f"  μx = {mux:.4f}, μy = {muy:.4f}")
                lines.append(f"  M0x = {M0x:.4f} MN.m")
                lines.append(f"  M0y = {M0y:.4f} MN.m")
            lines.append(f"  Mtx = {Mtx:.4f} MN.m")
            if M0y > 0:
                lines.append(f"  Mty = {Mty:.4f} MN.m")
            lines.append(f"  Max = {Max:.4f} MN.m")
    
            lines.append(self.sub("4. Mlu et Zb"))
            lines.append(f"  Fbu = {Fbu:.2f} MPa")
            lines.append(f"  d = 0.9h = {d:.3f} m")
            lines.append(f"  Mlu = {Mlu:.4f}")
            if Zb:
                lines.append(f"  α = {alpha_zb:.4f}")
                lines.append(f"  Zb = {Zb:.4f} m")
            else:
                lines.append("  ⚠ Section doublement armée nécessaire")
    
            lines.append(self.sub("5. Armatures calculées"))
            lines.append(f"  Fed = {Fed:.2f} MPa")
            lines.append(f"  Ax ≥ {Ax_cm2:.3f} cm²")
            if M0y > 0:
                lines.append(f"  Ay ≥ {Ay_cm2:.3f} cm²")
    
            lines.append(self.sub("6. Amin"))
            lines.append(f"  ft28 = {ft28:.3f} MPa")
            lines.append(f"  Amin,cnf = {0.23*b_cm*d_cm*ft28/Fe:.3f} cm²")
            lines.append(f"  Amin,B64 = {Amin_B64:.3f} cm²")
            lines.append(f"  ✓ Amin = {Amin:.3f} cm²")
    
            lines.append(self.sub("7. Choix des armatures"))
            lines.append(f"  Sens X : ✓ {nx} HA{dx} / ml  →  {Asx:.3f} cm²  (esp {espx:.1f} cm)")
            if M0y > 0:
                lines.append(f"  Sens Y : ✓ {ny} HA{dy} / ml  →  {Asy:.3f} cm²  (esp {espy:.1f} cm)")
    
            lines.append(self.sub("8. Effort tranchant"))
            lines.append(f"  τu,max = {tau_max:.4f} MPa")
            lines.append(f"  τu,lim = {tau_lim:.3f} MPa")
            lines.append(self.ok("Effort tranchant", et_ok))
    
            lines.append(f"\n{self.hr()}\n  ✓ CALCUL TERMINÉ\n{self.hr()}")
    
            sections = [{
                "n": nx, "dia": dx, "b": 100, "h": h * 100,
                "label": f"Sens X : {nx}HA{dx}",
                "sous_label": f"e = {h*100:.0f} cm"
            }]
            if M0y > 0:
                sections.append({
                    "n": ny, "dia": dy, "b": 100, "h": h * 100,
                    "label": f"Sens Y : {ny}HA{dy}",
                    "sous_label": f"e = {h*100:.0f} cm"
                })
    
            return "\n".join(lines), {"sections": sections}
    
        self.show_calc("Dalle complète (BAEL 91 E.3)", fields, compute,
                       schema_drawer=self.draw_rebar_section)
    
    # =========================================================
    # 7 - ESCALIER
    # =========================================================
    def calc_escalier(self):
        fields = [
            ("Données générales", [
                ("H", "Hauteur totale H (m)", "2.80"),
                ("nb", "Nombre de volées (1-4)", "2"),
            ]),
            ("Volée 1", [
                ("a1", "Longueur (m)", "2.50"),
                ("b1", "Hauteur (m)", "1.40"),
            ]),
            ("Volée 2 (vide si unused)", [
                ("a2", "Longueur (m)", "2.50"),
                ("b2", "Hauteur (m)", "1.40"),
            ]),
            ("Volée 3 (vide si unused)", [
                ("a3", "Longueur (m)", ""),
                ("b3", "Hauteur (m)", ""),
            ]),
            ("Volée 4 (vide si unused)", [
                ("a4", "Longueur (m)", ""),
                ("b4", "Hauteur (m)", ""),
            ]),
        ]
    
        def compute(v):
            H = self._f(v, "H", positive=True)
            nb = self._i(v, "nb", default=1)
            nb = max(1, min(nb, 4))
    
            Fe, Fc28 = self.Fe, self.Fc28
            gb, gs = self.gamma_b, self.gamma_s
            Fed = Fe / gs
            ft28 = min(0.6 + 0.06 * Fc28, 3.3)
    
            volées = []
            for i in range(nb):
                a_v = self._f(v, f"a{i+1}", positive=True)
                b_v = self._f(v, f"b{i+1}", positive=True)
                b_cm = b_v * 100
                a_cm = a_v * 100
    
                n_th = b_cm / 17
                n_base = max(1, round(n_th))
                n_retenu = None
                for n in sorted({n_base-1, n_base, n_base+1}):
                    if n < 1:
                        continue
                    if 16.5 <= b_cm / n <= 17.5:
                        n_retenu = n
                        break
                if n_retenu is None:
                    n_retenu = min(
                        [n for n in {n_base-1, n_base, n_base+1} if n >= 1],
                        key=lambda n: abs(b_cm/n - 17))
                n_marches = max(1, n_retenu)
                h_marche = b_cm / n_marches
                giron = a_cm / (n_marches - 1) if n_marches > 1 else a_cm
                blondel = giron + 2 * h_marche
                L_v = round(math.sqrt(a_v**2 + b_v**2), 2)
                if L_v > 0:
                    sin_a = max(-1, min(1, b_v / L_v))
                    alpha = round(math.degrees(math.asin(sin_a)))
                else:
                    alpha = 0
    
                e_paillasse = max(L_v / 30, 0.10)
    
                volées.append({
                    "num": i+1, "a": a_v, "b": b_v,
                    "n": n_marches, "h_m": h_marche, "g": giron,
                    "blondel": blondel, "L": L_v, "alpha": alpha,
                    "e": e_paillasse,
                })
    
            elements = []
            for vv in volées:
                cos_a = math.cos(math.radians(vv["alpha"])) if vv["alpha"] else 1.0
                G_dalle = vv["e"] * 25
                G_marches = (vv["g"]/100 * vv["h_m"]/100 / 2) * 25
                G_rev = 3*(vv["h_m"]/100)*0.6 + 3*(vv["g"]/100)*1.0*0.6
                G_enduit = 0.44
                G_surf = G_dalle + G_marches + G_enduit + G_rev
                Q_surf = 2.5
                Ge = G_surf / cos_a
                Qe = Q_surf / cos_a
                Pu = (1.35*Ge + 1.50*Qe) / 1000
                Pser = (Ge + Qe) / 1000
                elements.append({
                    "type": "Volée", "num": vv["num"],
                    "L": vv["L"], "e": vv["e"],
                    "Pu": Pu, "Pser": Pser,
                })
    
            for i in range(nb - 1):
                e_p = max(volées[i]["e"], volées[i+1]["e"])
                G_surf = e_p*25 + 0.44 + 0.60 + 0.40
                Q_surf = 2.5
                Pu = (1.35*G_surf + 1.50*Q_surf) / 1000
                Pser = (G_surf + Q_surf) / 1000
                elements.append({
                    "type": "Palier", "num": i+1,
                    "L": 1.20, "e": e_p,
                    "Pu": Pu, "Pser": Pser,
                })
    
            for el in elements:
                el["M0"] = el["Pu"] * el["L"]**2 / 8
                el["V0"] = el["Pu"] * el["L"] / 2
    
            nT = len(elements)
            M_appuis = [0.0] * (nT + 1)
            if nT > 1:
                for k in range(1, nT):
                    if nT == 2:
                        coef = 0.5
                    else:
                        coef = 0.5 if (k == 1 or k == nT - 1) else 0.4
                    M_appuis[k] = -coef * min(elements[k-1]["M0"], elements[k]["M0"])
    
            for i, el in enumerate(elements):
                Mw, Me, M0i = M_appuis[i], M_appuis[i+1], el["M0"]
                if nT == 1:
                    el["Mt"] = M0i
                    el["Ma_max"] = 0.0
                else:
                    coef = 0.85 if (i == 0 or i == nT-1) else 0.75
                    Mt = coef * M0i - (Mw + Me) / 2
                    el["Mt"] = max(Mt, 0)
                    Ma_g = abs(Mw); Ma_d = abs(Me)
                    if i == 0:
                        Ma_g = max(Ma_g, 0.30 * M0i)
                    if i == nT - 1:
                        Ma_d = max(Ma_d, 0.30 * M0i)
                    el["Ma_max"] = max(Ma_g, Ma_d)
    
            Fbu = 0.85 * Fc28 / gb
            bo = 1.0
    
            def dim_flex(Mu, e_m):
                d = 0.9 * e_m
                if d <= 0:
                    return None
                Mlu = Mu / (bo * d**2 * Fbu)
                if Mlu >= 0.5:
                    return None
                alpha_zb = 1.25 * (1 - math.sqrt(max(0, 1 - 2*Mlu)))
                Zb = d * (1 - 0.4*alpha_zb)
                As_cm2 = Mu / (Zb * Fed) * 10000
                Amin = 0.23 * 100 * (d*100) * ft28 / Fe
                As_req = max(As_cm2, Amin)
                best = None
                for dia in [8, 10, 12, 14, 16, 20, 25, 32]:
                    aire = math.pi * dia**2 / 4 / 100
                    for n in range(4, 33):
                        As_f = n * aire
                        if As_f >= As_req:
                            if best is None or As_f < best[0]:
                                best = (As_f, n, dia)
                            break
                return {"d": d, "Mlu": Mlu, "Zb": Zb,
                        "As_calc": As_cm2, "Amin": Amin,
                        "As_req": As_req, "choix": best}
    
            for el in elements:
                el["flex_tr"] = dim_flex(el["Mt"], el["e"]) if el["Mt"] > 0 else None
                el["flex_ap"] = dim_flex(el["Ma_max"], el["e"]) if el["Ma_max"] > 0 else None
    
            tau_lim = min(0.20 * Fc28 / gb, 5.0)
            for el in elements:
                if nT == 1:
                    V_max = el["V0"]
                else:
                    Vg = abs(el["V0"] + (M_appuis[i+1] - M_appuis[i]) / el["L"]) if False else el["V0"]
                    V_max = el["V0"]
                tau_u = V_max * 1000 / (100 * el["e"] * 100)
                el["V_max"] = V_max
                el["tau_u"] = tau_u
                el["tau_ok"] = tau_u <= tau_lim
    
            E_i = 11000 * Fc28 ** (1/3)
            for el in elements:
                e_m = el["e"]
                d_cm = 0.9 * e_m * 100
                As_f = el["flex_tr"]["choix"][0] if (el["flex_tr"] and el["flex_tr"]["choix"]) else 1.0
                A_eq = 100 / 2
                B_eq = 15 * As_f
                C_eq = -15 * As_f * d_cm
                disc = B_eq**2 - 4*A_eq*C_eq
                if disc < 0:
                    el["f_tot"] = None
                    continue
                y_cm = (-B_eq + math.sqrt(disc)) / (2*A_eq)
                I_f_cm4 = 100*y_cm**3/3 + 15*As_f*(d_cm - y_cm)**2
                I_f_m4 = I_f_cm4 * 1e-8
                M_ser = el["Pser"] * el["L"]**2 / 8 * 1e6
                E_i_Pa = E_i * 1e6
                f_i = (5 * M_ser * el["L"]**2) / (48 * E_i_Pa * I_f_m4) * 1000
                f_tot = f_i + 0.5 * f_i
                f_adm = el["L"] * 1000 / 500
                el["f_tot"] = f_tot
                el["f_adm"] = f_adm
                el["fleche_ok"] = f_tot <= f_adm
    
            lines = []
            lines.append(self.head("CALCUL COMPLET DE L'ESCALIER"))
            lines.append(f"  Hauteur totale H = {H:.3f} m")
            lines.append(f"  Nombre de volées = {nb}")
    
            for vv in volées:
                lines.append(self.sub(f"Volée {vv['num']}"))
                lines.append(f"  a = {vv['a']:.3f} m  |  b = {vv['b']:.3f} m")
                lines.append(f"  Marches : n = {vv['n']}")
                lines.append(f"  h marche = {vv['h_m']:.2f} cm")
                lines.append(f"  giron    = {vv['g']:.2f} cm")
                lines.append(f"  Blondel  = {vv['blondel']:.2f} cm")
                lines.append(self.ok("h ∈ [16.5;17.5]", 16.5 <= vv["h_m"] <= 17.5))
                lines.append(self.ok("g ∈ [27;32]", 27 <= vv["g"] <= 32))
                lines.append(self.ok("Blondel ∈ [59;66]", 59 <= vv["blondel"] <= 66))
                lines.append(f"  L inclinée = {vv['L']:.3f} m")
                lines.append(f"  α = {vv['alpha']}°")
                lines.append(f"  e paillasse = {vv['e']*100:.1f} cm")
    
            lines.append(self.sub("Efforts et ferraillage"))
            for el in elements:
                lines.append(f"\n  ▶ {el['type']} {el['num']}")
                lines.append(f"     L = {el['L']:.3f} m   e = {el['e']*100:.1f} cm")
                lines.append(f"     Pu = {el['Pu']*1000:.3f} kN/m   Pser = {el['Pser']*1000:.3f} kN/m")
                lines.append(f"     M0 = {el['M0']*1000:.3f} kN.m")
                lines.append(f"     Mt = {el['Mt']*1000:.3f} kN.m")
                lines.append(f"     Ma,max = {el['Ma_max']*1000:.3f} kN.m")
                lines.append(f"     V_max = {el['V_max']*1000:.3f} kN")
                if el["flex_tr"] and el["flex_tr"]["choix"]:
                    As_f, n_b, dia = el["flex_tr"]["choix"]
                    lines.append(f"     ✓ Travée : {n_b} HA{dia} = {As_f:.3f} cm²")
                if el["flex_ap"] and el["flex_ap"]["choix"]:
                    As_f, n_b, dia = el["flex_ap"]["choix"]
                    lines.append(f"     ✓ Appui  : {n_b} HA{dia} = {As_f:.3f} cm²")
                lines.append(self.ok("τu ≤ τu,lim", el["tau_ok"],
                                     f"{el['tau_u']:.4f} ≤ {tau_lim:.3f}"))
                if el.get("f_tot") is not None:
                    lines.append(self.ok("Flèche OK", el["fleche_ok"],
                                         f"{el['f_tot']:.2f} ≤ {el['f_adm']:.2f} mm"))
    
            lines.append(f"\n{self.hr()}\n  ✓ CALCUL TERMINÉ\n{self.hr()}")
    
            sections = []
            for el in elements:
                if el["flex_tr"] and el["flex_tr"]["choix"]:
                    As_f, n_b, dia = el["flex_tr"]["choix"]
                    sections.append({
                        "n": n_b, "dia": dia,
                        "b": 100, "h": el["e"] * 100,
                        "label": f"{el['type']} {el['num']} (travée)",
                        "sous_label": f"{n_b}HA{dia}"
                    })
            if not sections:
                sections = [{"n": 4, "dia": 12, "b": 100, "h": 15,
                             "label": "Escalier", "sous_label": ""}]
            return "\n".join(lines), {"sections": sections[:4]}
    
        self.show_calc("Escalier complet (BAEL 91)", fields, compute,
                       schema_drawer=self.draw_rebar_section)
    
    # =========================================================
    # 8 - FOSSE SEPTIQUE
    # =========================================================
    def calc_fosse(self):
        fields = [
            ("Données", [
                ("N", "Nombre d'usagers N", "8"),
                ("Lfos", "Largeur intérieure Lfos (m)", "1.20"),
                ("He", "Profondeur d'eau He (m)", "1.50"),
            ]),
        ]
    
        def compute(v):
            N = self._f(v, "N", positive=True)
            Lfos = self._f(v, "Lfos", positive=True)
            He = self._f(v, "He", positive=True)
    
            if He < 1.0:
                raise ValueError("He doit être ≥ 1.00 m (minimum recommandé).")
    
            Ve_u = 250.0
            Vfos_L = Ve_u * N
            Vfos_m3 = Vfos_L / 1000
            Vc_m3 = 2/3 * Vfos_m3
            Vd_m3 = 1/3 * Vfos_m3
    
            S_filtre = N / (10 * He**2)
            Vf_m3 = S_filtre * He
            Vf_L = Vf_m3 * 1000
    
            sect = Lfos * He
            Lc = Vc_m3 / sect
            Ld = Vd_m3 / sect
            Lf = Vf_m3 / sect
            Ltot = Lc + Ld + Lf
    
            warn = Vfos_m3 < 3.0
    
            lines = []
            lines.append(self.head("CALCUL DE LA FOSSE SEPTIQUE"))
            lines.append(self.sub("Fosse"))
            lines.append(f"  Vfos = {Ve_u:.0f} × {N:g} = {Vfos_L:,.0f} L = {Vfos_m3:.3f} m³")
            if warn:
                lines.append("  ⚠ Volume < 3 m³ (minimum recommandé)")
            lines.append(f"  Vc (2/3) = {Vc_m3:.3f} m³")
            lines.append(f"  Vd (1/3) = {Vd_m3:.3f} m³")
    
            lines.append(self.sub("Filtre"))
            lines.append(f"  S = N / (10·H²) = {N:g} / (10 × {He}²)")
            lines.append(f"  S = {S_filtre:.4f} m²")
            lines.append(f"  Vf = {Vf_m3:.4f} m³ = {Vf_L:,.0f} L")
    
            lines.append(self.sub("Longueurs"))
            lines.append(f"  Lc (chute)       = {Lc:.3f} m")
            lines.append(f"  Ld (décantation) = {Ld:.3f} m")
            lines.append(f"  Lf (filtre)      = {Lf:.3f} m")
            lines.append(f"  ✓ Ltot = {Ltot:.3f} m")
    
            lines.append(f"\n{self.hr()}\n  ✓ CALCUL TERMINÉ\n{self.hr()}")
    
            schema = {"sections": [{
                "n": 4, "dia": 10, "b": Lfos * 100, "h": Ltot * 100,
                "label": "Fosse septique",
                "sous_label": f"L = {Ltot:.2f} m × l = {Lfos:.2f} m × He = {He:.2f} m"
            }]}
            return "\n".join(lines), schema
    
        self.show_calc("Fosse septique", fields, compute,
                       schema_drawer=self.draw_rebar_section)
    
    # =========================================================
    # 10 - EFFET DU VENT (NV 65)
    # =========================================================
    def calc_vent(self):
        fields = [
            ("Géométrie", [
                ("a", "Façade a (m)", "11.0"),
                ("b", "Façade b (m)", "9.0"),
                ("H", "Hauteur totale H (m)", "15.4"),
            ]),
            ("Zonage q10", [
                ("q10", "q10 normal (kgf/m²) [50=HP, 143=Côte]", "50"),
                ("q10e", "q10 extrême (kgf/m²) [87.5 / 250]", "87.5"),
            ]),
            ("Site et masque", [
                ("Cs", "Cs (0.8 protégé / 1.0 normal / 1.25 exposé)", "1.0"),
                ("Cm", "Cm masque (1.0 si non masqué)", "1.0"),
            ]),
            ("Vérification Kármán", [
                ("Vref", "Vitesse référence V (m/s)", "65"),
            ]),
        ]
    
        def calcul_beta(H, D):
            T = 0.09 * H / math.sqrt(D) if D > 0 else 0.5
            if T <= 0.1:
                xi = 0.0
            elif T <= 0.5:
                xi = 0.12 + (0.15 - 0.12) * (T - 0.1253) / (0.5 - 0.1253)
                xi = max(0.0, min(xi, 0.5))
            else:
                xi = 0.5
            if H <= 10:
                tau = 0.20
            elif H <= 30:
                tau = 0.20 + (0.324 - 0.20) * (H - 10) / 20
            elif H <= 60:
                tau = 0.324 + (0.35 - 0.324) * (H - 30) / 30
            else:
                tau = 0.35
            if H <= 30:
                theta = 0.70
            elif H < 60:
                theta = 0.70 + 0.01 * (H - 30)
            else:
                theta = 1.0
            beta = max(theta * (1 + xi * tau), 1.0)
            return beta, T, xi, tau, theta
    
        def calcul_gamma0(H, a, b):
            la = H / a if a > 0 else 0
            lb = H / b if b > 0 else 0
            if la <= 0.5 and lb <= 0.5:
                return 1.0, la, lb
            elif la <= 1.0 and lb <= 1.0:
                return round(1.0 + 0.05 * max(la, lb), 3), la, lb
            return round(1.0 + 0.05 * min(max(la, lb), 2.0), 3), la, lb
    
        def calcul_delta(H, dim):
            x = max(H, dim)
            if x <= 0.5:
                return 1.0
            return max(0.0, min(-0.130 * math.log10(x) + 0.961, 1.0))
    
        def compute(v):
            a = self._f(v, "a", positive=True)
            b = self._f(v, "b", positive=True)
            H = self._f(v, "H", positive=True)
            q10 = self._f(v, "q10", positive=True)
            q10e = self._f(v, "q10e", positive=True)
            Cs = self._f(v, "Cs", positive=True)
            Cm = self._f(v, "Cm", positive=True)
            Vref = self._f(v, "Vref", default=65)
    
            Kh = 2.5 * (H + 18) / (H + 60)
            d_a = calcul_delta(H, a)
            d_b = calcul_delta(H, b)
            beta_a, Ta, xi_a, tau_a, theta_a = calcul_beta(H, a)
            beta_b, Tb, xi_b, tau_b, theta_b = calcul_beta(H, b)
            g0, la, lb = calcul_gamma0(H, a, b)
    
            qd_an = max(q10 * Kh * Cs * Cm * d_a * beta_a, 30.0)
            qd_bn = max(q10 * Kh * Cs * Cm * d_b * beta_b, 30.0)
            qd_ae = max(q10e * Kh * Cs * Cm * d_a * beta_a, 52.5)
            qd_be = max(q10e * Kh * Cs * Cm * d_b * beta_b, 52.5)
    
            conv = 0.00980665
            Ce = 0.8
            Ce_sous = -(1.3 * g0 - 0.8)
            Ci = 0.3
            Cr_p = Ce - (-Ci)
            Cr_s = Ce_sous - Ci
    
            Sa = a * H
            Sb = b * H
            Fa_n = qd_an * conv * Sa * abs(Cr_p) * beta_a
            Fb_n = qd_bn * conv * Sb * abs(Cr_p) * beta_b
            Fa_e = qd_ae * conv * Sa * abs(Cr_p) * beta_a
            Fb_e = qd_be * conv * Sb * abs(Cr_p) * beta_b
    
            Ma_n = Fa_n * H / 2
            Mb_n = Fb_n * H / 2
            Ma_e = Fa_e * H / 2
            Mb_e = Fb_e * H / 2
    
            S_str = 0.30
            Vcra = a / (S_str * Ta) if Ta > 0 else 0
            Vcrb = b / (S_str * Tb) if Tb > 0 else 0
            karman_a = Vref < Vcra
            karman_b = Vref < Vcrb
    
            lines = []
            lines.append(self.head("EFFET DU VENT — NV 65"))
            lines.append(self.sub("Coefficient Kh (R-III-1.241)"))
            lines.append(f"  Kh = 2.5·(H+18)/(H+60)")
            lines.append(f"  Kh = 2.5 × ({H}+18) / ({H}+60) = {Kh:.4f}")
    
            lines.append(self.sub("Effet de dimension δ (R-III-2)"))
            lines.append(f"  δ_a = {d_a:.4f}   (x = max({H}, {a}) = {max(H,a):.2f})")
            lines.append(f"  δ_b = {d_b:.4f}   (x = max({H}, {b}) = {max(H,b):.2f})")
    
            lines.append(self.sub("Majoration dynamique β (R-III-1.511)"))
            lines.append(f"  β = θ·(1 + ξ·τ) ≥ 1")
            lines.append(f"  β_a = {beta_a:.4f}   (T_a = {Ta:.4f} s, ξ={xi_a:.4f}, τ={tau_a:.4f}, θ={theta_a:.4f})")
            lines.append(f"  β_b = {beta_b:.4f}   (T_b = {Tb:.4f} s, ξ={xi_b:.4f}, τ={tau_b:.4f}, θ={theta_b:.4f})")
    
            lines.append(self.sub("Coefficient de forme γ₀ (R-III-5)"))
            lines.append(f"  λ_a = H/a = {la:.3f}")
            lines.append(f"  λ_b = H/b = {lb:.3f}")
            lines.append(f"  γ₀ = {g0:.3f}")
    
            lines.append(self.sub("Pression dynamique corrigée"))
            lines.append(f"  qd = q10 × Kh × Cs × Cm × δ × β")
            lines.append(f"  qd_a,n = {qd_an:.3f} kgf/m² = {qd_an*conv:.3f} kN/m²")
            lines.append(f"  qd_b,n = {qd_bn:.3f} kgf/m² = {qd_bn*conv:.3f} kN/m²")
            lines.append(f"  qd_a,e = {qd_ae:.3f} kgf/m² = {qd_ae*conv:.3f} kN/m²")
            lines.append(f"  qd_b,e = {qd_be:.3f} kgf/m² = {qd_be*conv:.3f} kN/m²")
    
            lines.append(self.sub("Coefficients de pression"))
            lines.append(f"  Ce (face au vent) = {Ce:+.2f}")
            lines.append(f"  Ce (sous le vent) = {Ce_sous:+.2f}")
            lines.append(f"  Ci (intérieur)    = {Ci:+.2f}")
            lines.append(f"  Cr (pression)     = {Cr_p:+.2f}")
            lines.append(f"  Cr (succion)      = {Cr_s:+.2f}")
    
            lines.append(self.sub("Forces et moments (pression)"))
            lines.append(f"  Surface a = {Sa:.3f} m²   |   Surface b = {Sb:.3f} m²")
            lines.append(f"  F_a,n = {Fa_n:.3f} kN   →   M_a,n = {Ma_n:.3f} kN.m")
            lines.append(f"  F_b,n = {Fb_n:.3f} kN   →   M_b,n = {Mb_n:.3f} kN.m")
            lines.append(f"  F_a,e = {Fa_e:.3f} kN   →   M_a,e = {Ma_e:.3f} kN.m")
            lines.append(f"  F_b,e = {Fb_e:.3f} kN   →   M_b,e = {Mb_e:.3f} kN.m")
    
            lines.append(self.sub("Vérification Kármán"))
            lines.append(f"  Vcr(a) = {Vcra:.3f} m/s")
            lines.append(f"  Vcr(b) = {Vcrb:.3f} m/s")
            lines.append(f"  Vref   = {Vref:.3f} m/s")
            lines.append(self.ok("Kármán sur a", karman_a))
            lines.append(self.ok("Kármán sur b", karman_b))
    
            lines.append(f"\n{self.hr()}\n  ✓ CALCUL TERMINÉ\n{self.hr()}")
    
            sections = [{
                "n": 4, "dia": 12, "b": a * 100, "h": H * 100,
                "label": f"Façade a — β={beta_a:.2f}",
                "sous_label": f"F={Fa_n:.2f} kN | M={Ma_n:.2f} kN.m"
            }, {
                "n": 4, "dia": 12, "b": b * 100, "h": H * 100,
                "label": f"Façade b — β={beta_b:.2f}",
                "sous_label": f"F={Fb_n:.2f} kN | M={Mb_n:.2f} kN.m"
            }]
            return "\n".join(lines), {"sections": sections}
    
        self.show_calc("Effet du vent (NV 65)", fields, compute,
                       schema_drawer=self.draw_rebar_section)
    
    # =========================================================
    # 11 - POUTRE COMPLÈTE
    # =========================================================
    def calc_poutre_complete(self):
        fields = [
            ("Géométrie", [
                ("nb", "Nombre de travées", "2"),
                ("L1", "Portée L1 (m)", "4.00"),
                ("L2", "Portée L2 (m)", "4.00"),
                ("L3", "Portée L3 (m, si > 2 travées)", ""),
                ("L4", "Portée L4 (m, si > 3 travées)", ""),
                ("b", "Largeur b (cm)", "22"),
                ("h", "Hauteur totale h (cm)", "50"),
            ]),
            ("Charges", [
                ("G", "Charge permanente G (kN/m)", "18.0"),
                ("Q", "Surcharge Q (kN/m)", "7.5"),
            ]),
        ]
    
        def compute(v):
            nb = self._i(v, "nb", default=1)
            nb = max(1, min(nb, 4))
            spans = []
            for i in range(nb):
                spans.append(self._f(v, f"L{i+1}", positive=True))
            b_cm = self._f(v, "b", positive=True)
            h_cm = self._f(v, "h", positive=True)
            G = self._f(v, "G", positive=True)
            Q = self._f(v, "Q", positive=True)
    
            Fe, Fc28 = self.Fe, self.Fc28
            gb, gs = self.gamma_b, self.gamma_s
            Fed = Fe / gs
            ft28 = min(0.6 + 0.06 * Fc28, 3.3)
    
            wu = 1.35 * G + 1.50 * Q
            alpha_q = Q / (G + Q) if (G + Q) > 0 else 0
            cond_ff = Q <= min(2 * G, 5.0)
    
            M0 = [wu * L**2 / 8 for L in spans]
            n = nb
            M_appuis = [0.0] * (n + 1)
    
            if cond_ff:
                for i in range(1, n):
                    if n == 2:
                        M_appuis[i] = -0.6 * M0[i]
                    else:
                        if i == 1 or i == n - 1:
                            M_appuis[i] = -0.5 * M0[i]
                        else:
                            M_appuis[i] = -0.4 * M0[i]
                M_travees = []
                for i in range(n):
                    Mw, Me, M0i = M_appuis[i], M_appuis[i+1], M0[i]
                    if i == 0 or i == n - 1:
                        cond1 = (1.2 + 0.3 * alpha_q) / 2 * M0i
                        cond2 = (1.2 + 0.3 * alpha_q) / 2 * M0i
                    else:
                        cond1 = (1.0 + 0.3 * alpha_q) / 2 * M0i
                        cond2 = (1.0 + 0.3 * alpha_q) / 2 * M0i
                    cond1 = max(cond1, 1.05 * M0i)
                    Mt = max(cond1 - (Mw + Me) / 2, cond2)
                    M_travees.append(Mt)
                methode = "Forfaitaire (E.1)"
            else:
                for i in range(1, n):
                    if n == 2:
                        M_appuis[i] = -0.5 * (M0[i-1] + M0[i])
                    else:
                        if i == 1 or i == n - 1:
                            M_appuis[i] = -0.5 * M0[i]
                        else:
                            M_appuis[i] = -0.4 * M0[i]
                M_travees = []
                for i in range(n):
                    Mw, Me, M0i = M_appuis[i], M_appuis[i+1], M0[i]
                    Mt = M0i - (abs(Mw) + abs(Me)) / 2
                    M_travees.append(max(Mt, 0))
                methode = "Caquot (E.2)"
    
            V_appuis = [0.0] * (n + 1)
            for i in range(n):
                L = spans[i]
                V0 = wu * L / 2
                Vg = V0 - (M_appuis[i+1] - M_appuis[i]) / L
                Vd = V0 + (M_appuis[i+1] - M_appuis[i]) / L
                maj = 1.15 if n == 2 else 1.10
                V_appuis[i] = max(V_appuis[i], abs(Vg) * maj)
                V_appuis[i+1] = max(V_appuis[i+1], abs(Vd) * maj)
    
            fbu = 0.85 * Fc28 / gb
            eps_bc = 0.0035
            eps_s = Fed / 200000
            alpha_lim = eps_bc / (eps_bc + eps_s)
            mu_lim = alpha_lim * (1 - 0.4 * alpha_lim)
            enrob = 3.0
    
            def flex_design(Mu_kNm, phi_l, phi_t):
                d_cm = h_cm - enrob - phi_t / 10 - phi_l / 20
                if d_cm <= 0:
                    return None
                d_mm = d_cm * 10
                b_mm = b_cm * 10
                Mu_Nmm = Mu_kNm * 1e6
                mu = Mu_Nmm / (b_mm * d_mm**2 * fbu)
                if mu > mu_lim:
                    return None
                alpha = 1.25 * (1 - math.sqrt(max(0, 1 - 2*mu)))
                z = d_mm * (1 - 0.4 * alpha)
                As_mm2 = Mu_Nmm / (z * Fed)
                As_cnf = 0.23 * b_mm * d_mm * ft28 / Fe
                As_req = max(As_mm2, As_cnf)
                return {"d_cm": d_cm, "d_mm": d_mm, "mu": mu, "z": z,
                        "As_calc": As_mm2, "As_cnf": As_cnf, "As_req": As_req}
    
            def choose_long(Mu_kNm):
                best = None
                for phi_l in [8, 10, 12, 14, 16, 20, 25, 32]:
                    lim_t = min(phi_l, h_cm * 10 / 35, b_cm * 10 / 10)
                    allowed = [p for p in [6, 8, 10, 12] if p <= lim_t + 1e-9]
                    if not allowed:
                        continue
                    phi_t = min(allowed)
                    fd = flex_design(Mu_kNm, phi_l, phi_t)
                    if fd is None:
                        continue
                    n_need = max(2, math.ceil(fd["As_req"] / (math.pi * phi_l**2 / 4)))
                    if n_need > 12:
                        continue
                    As_prov = n_need * math.pi * phi_l**2 / 4 / 100
                    if best is None or As_prov < best[0]:
                        best = (As_prov, n_need, phi_l, phi_t, fd)
                return best
    
            zones = []
            for i in range(n):
                zones.append({"name": f"Travée {i+1}", "Mu": M_travees[i],
                              "Vu": max(V_appuis[i], V_appuis[i+1]), "kind": "T"})
            for i in range(1, n):
                zones.append({"name": f"Appui {i}", "Mu": abs(M_appuis[i]),
                              "Vu": V_appuis[i], "kind": "A"})
    
            flex_results = []
            for zc in zones:
                if zc["Mu"] <= 1e-9:
                    continue
                r = choose_long(zc["Mu"])
                if r:
                    flex_results.append({**r, "zone": zc})
    
            tau_lim = min(0.20 * Fc28 / gb, 5.0)
            shear_results = []
            for r in flex_results:
                zc = r["zone"]
                d_mm = r[4]["d_mm"]
                b_mm = b_cm * 10
                Vu = zc["Vu"]
                tau = Vu * 1000 / (b_mm * d_mm)
                At = 2 * math.pi * 8**2 / 4
                min_ratio = 0.4 / Fe
                dem = gs * max(tau - 0.3 * ft28, 0) / (0.9 * Fe)
                ratio_req = max(min_ratio, dem)
                st_req = (At / (b_mm * 10)) / ratio_req
                st_max = min(st_req, 0.9 * r[4]["d_cm"], 40)
                st_prat = [s for s in [5, 7.5, 10, 12.5, 15, 17.5, 20, 22.5, 25, 30, 35] if s <= st_max]
                st = max(st_prat) if st_prat else 15
                shear_results.append({
                    "zone": zc, "tau": tau, "tau_lim": tau_lim,
                    "phi_t": 8, "branches": 2, "st": st,
                    "ok": tau <= tau_lim
                })
    
            lines = []
            lines.append(self.head("POUTRE COMPLÈTE — BAEL 91"))
            lines.append(self.sub("Données"))
            lines.append(f"  Nombre de travées : {n}")
            for i, L in enumerate(spans):
                lines.append(f"    L{i+1} = {L:.3f} m")
            lines.append(f"  Section : {b_cm:.0f} × {h_cm:.0f} cm")
            lines.append(f"  G = {G:.3f} kN/m   |   Q = {Q:.3f} kN/m")
            lines.append(f"  wu = {wu:.3f} kN/m")
            lines.append(f"  α = Q/(G+Q) = {alpha_q:.4f}")
            lines.append(f"  Méthode : {methode}")
            lines.append(self.ok("Condition forfaitaire", cond_ff,
                                 f"Q ≤ min(2G;5) = {min(2*G,5):.3f}"))
    
            lines.append(self.sub("Moments isostatiques"))
            for i, m in enumerate(M0):
                lines.append(f"  M0({i+1}) = {m:.4f} MN.m")
    
            lines.append(self.sub("Moments sur appuis"))
            for i in range(1, n):
                lines.append(f"  Appui {i} : M = {M_appuis[i]:.4f} MN.m")
    
            lines.append(self.sub("Moments en travée"))
            for i, m in enumerate(M_travees):
                lines.append(f"  Travée {i+1} : Mt = {m:.4f} MN.m")
    
            lines.append(self.sub("Ferraillage flexion"))
            lines.append(f"  fbu = {fbu:.3f} MPa   σs = {Fed:.2f} MPa")
            lines.append(f"  αlim = {alpha_lim:.4f}   μlim = {mu_lim:.4f}")
            for r in flex_results:
                As_prov, n_b, phi_l, phi_t, fd = r[0], r[1], r[2], r[3], r[4]
                zc = r["zone"]
                role = "CHAPEAUX (appui)" if zc["kind"] == "A" else "INFÉRIEURES (travée)"
                lines.append(f"\n  ▶ {zc['name']} [{role}]")
                lines.append(f"     Mu = {zc['Mu']:.4f} MN.m")
                lines.append(f"     d  = {fd['d_cm']:.2f} cm   μ = {fd['mu']:.5f}")
                lines.append(f"     z  = {fd['z']:.1f} mm")
                lines.append(f"     As calc = {fd['As_calc']/100:.3f} cm²")
                lines.append(f"     As CNF  = {fd['As_cnf']/100:.3f} cm²")
                lines.append(f"     ✓ {n_b} HA{phi_l} = {As_prov:.3f} cm²")
    
            lines.append(self.sub("Effort tranchant et étriers"))
            lines.append(f"  τu,lim = {tau_lim:.3f} MPa")
            for s in shear_results:
                zc = s["zone"]
                lines.append(f"\n  ▶ {zc['name']}")
                lines.append(f"     Vu = {zc['Vu']:.4f} MN")
                lines.append(f"     τu = {s['tau']:.4f} MPa")
                lines.append(self.ok("τu ≤ τu,lim", s["ok"]))
                lines.append(f"     ✓ {s['branches']} HA{s['phi_t']} / {s['st']:.1f} cm")
    
            lines.append(self.sub("Adhérence"))
            psi_s = 1.5
            tau_se_lim = psi_s * ft28
            for r in flex_results:
                zc = r["zone"]
                n_b, phi_l = r[1], r[2]
                perim = n_b * math.pi * phi_l
                d_mm = r[4]["d_mm"]
                tau_se = zc["Vu"] * 1000 / (0.9 * d_mm * perim)
                ls_cm = phi_l * Fe / (4 * tau_se_lim) / 10
                lines.append(f"  {zc['name']} : τse = {tau_se:.3f} MPa, ls = {ls_cm:.1f} cm")
                lines.append(self.ok("Adhérence", tau_se <= tau_se_lim))
    
            lines.append(f"\n{self.hr()}\n  ✓ CALCUL TERMINÉ\n{self.hr()}")
    
            sections = []
            for r in flex_results[:4]:
                As_prov, n_b, phi_l = r[0], r[1], r[2]
                zc = r["zone"]
                sections.append({
                    "n": n_b, "dia": phi_l,
                    "b": b_cm, "h": h_cm,
                    "label": f"{zc['name']} — {n_b}HA{phi_l}",
                    "sous_label": f"Mu={zc['Mu']*1000:.2f} kN.m"
                })
            return "\n".join(lines), {"sections": sections}
    
        self.show_calc("Poutre continue (BAEL 91 E.1/E.2)", fields, compute,
                       schema_drawer=self.draw_rebar_section)
    
    # =========================================================
    # 9 - AVANT MÉTRÉ (custom multi-screen)
    # =========================================================
    def avant_metre(self):
        import os as _os
        dossier = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "donnees_btp")
        _os.makedirs(dossier, exist_ok=True)
        fichier = _os.path.join(dossier, "avant_metre.json")
    
        def load():
            if not _os.path.exists(fichier):
                return []
            try:
                with open(fichier, "r", encoding="utf-8") as f:
                    d = json.load(f)
                return d if isinstance(d, list) else []
            except Exception:
                return []
    
        def save(data):
            try:
                with open(fichier, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("OK", f"Enregistré : {fichier}")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))
    
        self.clear_root()
        self.make_header("Avant métré d'ouvrage", self.show_menu)
    
        body = tk.Frame(self.root, bg=self.BG)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
    
        # Top : project info
        info = tk.LabelFrame(body, text=" 📋 Projet ",
                             font=("Segoe UI", 10, "bold"),
                             fg=self.ACCENT, bg=self.BG2, labelanchor="nw")
        info.pack(fill=tk.X)
    
        row = tk.Frame(info, bg=self.BG2)
        row.pack(fill=tk.X, padx=10, pady=8)
    
        tk.Label(row, text="Nom :", fg=self.FG, bg=self.BG2).pack(side=tk.LEFT)
        e_nom = tk.Entry(row, bg=self.BTN, fg=self.FG, insertbackground=self.ACCENT,
                         relief=tk.FLAT, width=24)
        e_nom.pack(side=tk.LEFT, padx=6, ipady=4)
    
        tk.Label(row, text="Client :", fg=self.FG, bg=self.BG2).pack(side=tk.LEFT, padx=(12, 0))
        e_cli = tk.Entry(row, bg=self.BTN, fg=self.FG, insertbackground=self.ACCENT,
                         relief=tk.FLAT, width=20)
        e_cli.pack(side=tk.LEFT, padx=6, ipady=4)
    
        tk.Label(row, text="Lieu :", fg=self.FG, bg=self.BG2).pack(side=tk.LEFT, padx=(12, 0))
        e_lieu = tk.Entry(row, bg=self.BTN, fg=self.FG, insertbackground=self.ACCENT,
                          relief=tk.FLAT, width=20)
        e_lieu.pack(side=tk.LEFT, padx=6, ipady=4)
    
        # Tree
        tree_frame = tk.Frame(body, bg=self.BG)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 6))
    
        cols = ("N", "Designation", "NPE", "U", "L", "l", "h", "Qt", "Info")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=12)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=80, anchor="w")
        tree.column("N", width=40, anchor="center")
        tree.column("Designation", width=220)
        tree.column("Qt", width=90, anchor="e")
        tree.column("Info", width=110)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=vsb.set)
    
        # State
        state = {"projet": {"nom": "", "client": "", "lieu": "",
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "lignes": []}}
    
        def refresh():
            tree.delete(*tree.get_children())
            for i, x in enumerate(state["projet"]["lignes"], 1):
                q = x.get("Qt", 0)
                if x.get("inclus_dans"):
                    info = "combiné"
                elif x.get("est_composition"):
                    info = "composé"
                elif x.get("deductions"):
                    info = f"-{len(x['deductions'])} déd."
                else:
                    info = ""
                tree.insert("", "end", values=(
                    i, x.get("designation", ""), x.get("NPE", ""),
                    x.get("U", ""), x.get("L", ""), x.get("l", ""),
                    x.get("h", ""), f"{q:.3f}", info))
    
        # === Actions ===
        def dialog_add():
            win = tk.Toplevel(self.root)
            win.title("Ajouter un ouvrage")
            win.configure(bg=self.BG)
            win.transient(self.root)
            win.grab_set()
    
            fields = [
                ("Designation", ""),
                ("NPE (nombre)", "1"),
                ("L (m)", ""),
                ("l (m)", ""),
                ("h (m)", ""),
                ("Qte (Qt direct)", ""),
            ]
            entries = {}
            for i, (lab, dft) in enumerate(fields):
                tk.Label(win, text=lab, fg=self.FG, bg=self.BG).grid(
                    row=i, column=0, sticky="w", padx=10, pady=4)
                e = tk.Entry(win, bg=self.BTN, fg=self.FG, insertbackground=self.ACCENT,
                             relief=tk.FLAT, width=20)
                e.insert(0, dft)
                e.grid(row=i, column=1, padx=10, pady=4, ipady=4)
                entries[lab] = e
    
            tk.Label(win, text="Unité", fg=self.FG, bg=self.BG).grid(
                row=len(fields), column=0, sticky="w", padx=10, pady=4)
            unit = ttk.Combobox(win, values=["m²", "m³", "ml", "u", "forfait"],
                                state="readonly", width=17)
            unit.set("m²")
            unit.grid(row=len(fields), column=1, padx=10, pady=4)
    
            def ok():
                try:
                    des = entries["Designation"].get().strip()
                    if not des:
                        raise ValueError("Désignation obligatoire")
                    NPE = float(entries["NPE (nombre)"].get().replace(",", ".") or 1)
                    L = float(entries["L (m)"].get().replace(",", ".") or 0)
                    l = float(entries["l (m)"].get().replace(",", ".") or 0)
                    h = float(entries["h (m)"].get().replace(",", ".") or 0)
                    U = unit.get()
                    Qt_raw = entries["Qte (Qt direct)"].get().strip()
    
                    if Qt_raw:
                        Qt = float(Qt_raw.replace(",", "."))
                    elif U == "m²":
                        Qt = L * l * NPE
                    elif U == "m³":
                        Qt = L * l * h * NPE
                    elif U == "ml":
                        Qt = L * NPE
                    else:
                        Qt = NPE
                    x = {
                        "_id": uuid.uuid4().hex,
                        "designation": des, "NPE": NPE, "U": U,
                        "L": L, "l": l, "h": h,
                        "Qt": Qt, "deductions": [],
                        "inclus_dans": "", "compose_de": [],
                        "est_composition": False,
                    }
                    state["projet"]["lignes"].append(x)
                    refresh()
                    win.destroy()
                except Exception as e:
                    messagebox.showerror("Erreur", str(e), parent=win)
    
            tk.Button(win, text="Ajouter", bg=self.GREEN, fg=self.BG,
                      relief=tk.FLAT, padx=14, pady=6, command=ok).grid(
                row=len(fields)+1, column=0, columnspan=2, pady=12)
    
        def dialog_deduce():
            if len(state["projet"]["lignes"]) < 2:
                messagebox.showinfo("Info", "Il faut au moins 2 ouvrages.")
                return
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Info", "Sélectionnez l'ouvrage CIBLE dans la liste.")
                return
            cible_idx = tree.index(sel[0])
            cible = state["projet"]["lignes"][cible_idx]
            deja = {d.get("source_line_id") for d in cible.get("deductions", [])}
    
            win = tk.Toplevel(self.root)
            win.title("Déduire un ouvrage")
            win.configure(bg=self.BG)
            win.transient(self.root)
            win.grab_set()
    
            tk.Label(win, text=f"Cible : {cible['designation']}",
                     fg=self.ACCENT, bg=self.BG, font=("Segoe UI", 10, "bold")).pack(padx=10, pady=8)
    
            lb = tk.Listbox(win, bg=self.BTN, fg=self.FG, width=50, height=10)
            lb.pack(padx=10, pady=6)
            dispo_idx = []
            for i, x in enumerate(state["projet"]["lignes"]):
                if i == cible_idx or x.get("inclus_dans") or x.get("_id") in deja:
                    continue
                if x.get("U") != cible.get("U"):
                    continue
                dispo_idx.append(i)
                lb.insert(tk.END, f"[{i+1}] {x['designation']} ({x['Qt']:.3f} {x['U']})")
    
            def ok():
                if not lb.curselection():
                    return
                j = lb.curselection()[0]
                src_idx = dispo_idx[j]
                src = state["projet"]["lignes"][src_idx]
                if src["Qt"] > cible["Qt"] + 1e-9:
                    messagebox.showerror("Erreur", "Qt source > Qt cible", parent=win)
                    return
                cible.setdefault("deductions", []).append({
                    "source_line_id": src["_id"],
                    "designation": src["designation"],
                    "Qt": src["Qt"], "U": src["U"],
                })
                cible["Qt"] = max(0, cible["Qt"] - src["Qt"])
                refresh()
                win.destroy()
    
            tk.Button(win, text="Déduire", bg=self.YELLOW, fg=self.BG,
                      relief=tk.FLAT, padx=14, pady=6, command=ok).pack(pady=10)
    
        def compose():
            sel = tree.selection()
            if len(sel) < 2:
                messagebox.showinfo("Info", "Sélectionnez 2 ouvrages ou plus (Ctrl+clic).")
                return
            idxs = [tree.index(s) for s in sel]
            unites = {state["projet"]["lignes"][i].get("U") for i in idxs}
            if len(unites) != 1:
                messagebox.showerror("Erreur", f"Unités différentes : {unites}")
                return
            U = unites.pop()
            total = sum(state["projet"]["lignes"][i].get("Qt", 0) for i in idxs)
    
            win = tk.Toplevel(self.root)
            win.title("Composer")
            win.configure(bg=self.BG)
            win.transient(self.root)
            win.grab_set()
            tk.Label(win, text=f"Total : {total:.3f} {U}",
                     fg=self.ACCENT, bg=self.BG).pack(pady=8)
            tk.Label(win, text="Désignation :", fg=self.FG, bg=self.BG).pack()
            e = tk.Entry(win, bg=self.BTN, fg=self.FG, insertbackground=self.ACCENT, width=30)
            e.pack(pady=6, ipady=4)
    
            def ok():
                des = e.get().strip()
                if not des:
                    return
                new_id = uuid.uuid4().hex
                state["projet"]["lignes"].append({
                    "_id": new_id, "designation": des,
                    "NPE": 1, "U": U, "L": 0, "l": 0, "h": 0,
                    "Qt": total, "deductions": [], "inclus_dans": "",
                    "compose_de": [state["projet"]["lignes"][i]["_id"] for i in idxs],
                    "est_composition": True,
                })
                for i in idxs:
                    state["projet"]["lignes"][i]["inclus_dans"] = new_id
                refresh()
                win.destroy()
    
            tk.Button(win, text="OK", bg=self.GREEN, fg=self.BG,
                      relief=tk.FLAT, padx=14, pady=6, command=ok).pack(pady=10)
    
        def delete_line():
            sel = tree.selection()
            if not sel:
                return
            idx = tree.index(sel[0])
            x = state["projet"]["lignes"].pop(idx)
            messagebox.showinfo("OK", f"Supprimé : {x.get('designation', '')}")
            refresh()
    
        def save_project():
            state["projet"]["nom"] = e_nom.get().strip() or "Sans nom"
            state["projet"]["client"] = e_cli.get().strip()
            state["projet"]["lieu"] = e_lieu.get().strip()
            data = load()
            data = [p for p in data if p.get("nom") != state["projet"]["nom"]]
            data.append(state["projet"])
            save(data)
    
        def export_csv():
            if not state["projet"]["lignes"]:
                return
            path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV", "*.csv")],
                initialfile=f"{e_nom.get().strip() or 'projet'}_avant_metre.csv")
            if not path:
                return
            try:
                with open(path, "w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f, delimiter=";")
                    w.writerow(["N°", "Designation", "NPE", "U", "L", "l", "h", "Qt", "Info"])
                    for i, x in enumerate(state["projet"]["lignes"], 1):
                        info = "combiné" if x.get("inclus_dans") else (
                            "composé" if x.get("est_composition") else (
                            f"-{len(x['deductions'])}" if x.get("deductions") else ""))
                        w.writerow([i, x["designation"], x["NPE"], x["U"],
                                    x["L"], x["l"], x["h"], x["Qt"], info])
                messagebox.showinfo("OK", f"Export CSV : {path}")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))
    
        # Boutons
        btns = tk.Frame(body, bg=self.BG)
        btns.pack(fill=tk.X)
        btn_cfg = dict(font=("Segoe UI", 10), bg=self.BTN, fg=self.FG,
                       activebackground=self.ACCENT, activeforeground=self.BG,
                       relief=tk.FLAT, padx=12, pady=8, cursor="hand2")
        tk.Button(btns, text="➕ Ajouter", command=dialog_add, **btn_cfg).pack(side=tk.LEFT, padx=3)
        tk.Button(btns, text="➖ Déduire", command=dialog_deduce, **btn_cfg).pack(side=tk.LEFT, padx=3)
        tk.Button(btns, text="🔗 Composer", command=compose, **btn_cfg).pack(side=tk.LEFT, padx=3)
        tk.Button(btns, text="🗑 Supprimer", command=delete_line, **btn_cfg).pack(side=tk.LEFT, padx=3)
        tk.Button(btns, text="💾 Enregistrer", command=save_project,
                  font=("Segoe UI", 10, "bold"), bg=self.GREEN, fg=self.BG,
                  relief=tk.FLAT, padx=12, pady=8).pack(side=tk.LEFT, padx=3)
        tk.Button(btns, text="📤 CSV", command=export_csv, **btn_cfg).pack(side=tk.LEFT, padx=3)
    
        refresh()
    
    # =========================================================
    # 12 - DESCENTE DE CHARGES (custom)
    # =========================================================
    def descente_charge(self):
        import os as _os
        dossier = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "donnees_btp")
        _os.makedirs(dossier, exist_ok=True)
        fichier = _os.path.join(dossier, "descente_charge.json")
    
        def load():
            if not _os.path.exists(fichier):
                return []
            try:
                with open(fichier, "r", encoding="utf-8") as f:
                    d = json.load(f)
                return d if isinstance(d, list) else []
            except Exception:
                return []
    
        def save(data):
            try:
                with open(fichier, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("OK", f"Enregistré : {fichier}")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))
    
        self.clear_root()
        self.make_header("Descente de charges", self.show_menu)
    
        body = tk.Frame(self.root, bg=self.BG)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
    
        state = {"projet": {"nom": "", "niveaux": [
            {"numero": 1, "elements_G": [], "elements_Q": []}]}}
    
        # Top
        top = tk.Frame(body, bg=self.BG2)
        top.pack(fill=tk.X)
        tk.Label(top, text="Nom projet :", fg=self.FG, bg=self.BG2).pack(side=tk.LEFT, padx=8, pady=8)
        e_nom = tk.Entry(top, bg=self.BTN, fg=self.FG, insertbackground=self.ACCENT, width=24)
        e_nom.pack(side=tk.LEFT, pady=8, ipady=4)
    
        tk.Label(top, text="Niveau :", fg=self.FG, bg=self.BG2).pack(side=tk.LEFT, padx=(16, 4))
        niv_var = tk.StringVar(value="1")
        niv_cb = ttk.Combobox(top, textvariable=niv_var, state="readonly", width=6)
        niv_cb.pack(side=tk.LEFT, pady=8)
    
        type_var = tk.StringVar(value="G")
        tk.Radiobutton(top, text="G (permanent)", variable=type_var, value="G",
                       bg=self.BG2, fg=self.FG, selectcolor=self.BTN).pack(side=tk.LEFT, padx=8)
        tk.Radiobutton(top, text="Q (exploitation)", variable=type_var, value="Q",
                       bg=self.BG2, fg=self.FG, selectcolor=self.BTN).pack(side=tk.LEFT)
    
        # Tree
        tf = tk.Frame(body, bg=self.BG)
        tf.pack(fill=tk.BOTH, expand=True, pady=8)
        cols = ("Niv", "Type", "Designation", "NPE", "L", "l", "h", "PU", "Charge")
        tree = ttk.Treeview(tf, columns=cols, show="headings", height=12)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=85, anchor="w")
        tree.column("Designation", width=180)
        tree.column("Charge", width=100, anchor="e")
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=vsb.set)
    
        # Tableau récap
        recap = tk.LabelFrame(body, text=" Récapitulatif ELU/ELS ",
                              font=("Segoe UI", 10, "bold"),
                              fg=self.ACCENT, bg=self.BG2, labelanchor="nw")
        recap.pack(fill=tk.X, pady=6)
        recap_txt = tk.Text(recap, height=8, font=("Consolas", 9),
                            bg=self.TEXT_BG, fg=self.FG, relief=tk.FLAT)
        recap_txt.pack(fill=tk.X, padx=6, pady=6)
    
        def calc_charge(e):
            NPE = float(e.get("NPE", 1) or 1)
            L = float(e.get("L", 0) or 0)
            l = float(e.get("l", 0) or 0)
            h = float(e.get("h", 0) or 0)
            PU = float(e.get("PU", 0) or 0)
            if h > 0:
                return NPE * L * l * h * PU
            return NPE * L * l * PU
    
        def refresh():
            tree.delete(*tree.get_children())
            total_G = 0; total_Q = 0
            for niv in state["projet"]["niveaux"]:
                n = niv["numero"]
                for t, key in (("G", "elements_G"), ("Q", "elements_Q")):
                    for e in niv.get(key, []):
                        ch = calc_charge(e)
                        tree.insert("", "end", values=(
                            f"N{n:02d}", t, e["designation"], e["NPE"],
                            e["L"], e["l"], e.get("h", 0), e["PU"], f"{ch:.3f}"))
                        if t == "G":
                            total_G += ch
                        else:
                            total_Q += ch
    
            # mise à jour combobox niveaux
            niv_cb["values"] = [str(i+1) for i in range(len(state["projet"]["niveaux"]))]
    
            recap_txt.config(state=tk.NORMAL)
            recap_txt.delete("1.0", tk.END)
            recap_txt.insert(tk.END,
                f"{'Niveau':<10}{'G(kN)':>12}{'Q(kN)':>12}{'ELU':>14}{'ELS':>14}\n")
            recap_txt.insert(tk.END, "-" * 62 + "\n")
            cum_G = 0; cum_Q = 0
            for niv in state["projet"]["niveaux"]:
                g = sum(calc_charge(e) for e in niv.get("elements_G", []))
                q = sum(calc_charge(e) for e in niv.get("elements_Q", []))
                cum_G += g
                cum_Q += q
                elu = 1.35*cum_G + 1.5*cum_Q
                els = cum_G + cum_Q
                recap_txt.insert(tk.END,
                    f"N{niv['numero']:02d}{'':<7}{cum_G:>12.3f}{cum_Q:>12.3f}"
                    f"{elu:>14.3f}{els:>14.3f}\n")
            maj_G = cum_G * 0.10
            maj_Q = cum_Q * 0.10
            recap_txt.insert(tk.END, "-" * 62 + "\n")
            recap_txt.insert(tk.END,
                f"{'Maj 10%':<10}{maj_G:>12.3f}{maj_Q:>12.3f}"
                f"{1.35*maj_G+1.5*maj_Q:>14.3f}{maj_G+maj_Q:>14.3f}\n")
            tG = cum_G + maj_G; tQ = cum_Q + maj_Q
            recap_txt.insert(tk.END,
                f"{'TOTAL':<10}{tG:>12.3f}{tQ:>12.3f}"
                f"{1.35*tG+1.5*tQ:>14.3f}{tG+tQ:>14.3f}\n")
            recap_txt.config(state=tk.DISABLED)
    
        PU_VOL = [
            ("Béton armé", 25.0), ("Béton non armé", 22.0),
            ("Maçonnerie brique creuse", 13.0), ("Maçonnerie brique pleine", 18.0),
            ("Moellon / pierre", 19.0), ("Enduit ciment", 22.0),
            ("Mortier ciment", 20.0), ("Terre / remblai", 18.0),
            ("Sable sec", 16.0), ("Gravier", 18.0),
            ("Acier", 78.5), ("Bois (résineux)", 6.0),
            ("Autre (manuel)", None),
        ]
        PU_SURF = [
            ("Étanchéité", 0.12), ("Étanchéité + protection", 0.20),
            ("Carrelage / céramique", 0.60), ("Marbre / granit", 1.20),
            ("Parquet", 0.30), ("Habitation (Q)", 1.50),
            ("Bureau (Q)", 2.50), ("Escalier (Q)", 2.50),
            ("Balcon (Q)", 3.50), ("Terrasse accessible", 1.50),
            ("Autre (manuel)", None),
        ]
    
        def dialog_add():
            niv = int(niv_var.get()) - 1
            t = type_var.get()
            win = tk.Toplevel(self.root)
            win.title("Ajouter élément")
            win.configure(bg=self.BG)
            win.transient(self.root)
            win.grab_set()
    
            tk.Label(win, text="Désignation", fg=self.FG, bg=self.BG).grid(row=0, column=0, sticky="w", padx=8, pady=4)
            e_des = tk.Entry(win, bg=self.BTN, fg=self.FG, insertbackground=self.ACCENT, width=22)
            e_des.grid(row=0, column=1, padx=8, pady=4, ipady=4)
    
            tk.Label(win, text="NPE", fg=self.FG, bg=self.BG).grid(row=1, column=0, sticky="w", padx=8, pady=4)
            e_npe = tk.Entry(win, bg=self.BTN, fg=self.FG, insertbackground=self.ACCENT, width=22)
            e_npe.insert(0, "1")
            e_npe.grid(row=1, column=1, padx=8, pady=4, ipady=4)
    
            tk.Label(win, text="L (m)", fg=self.FG, bg=self.BG).grid(row=2, column=0, sticky="w", padx=8, pady=4)
            e_L = tk.Entry(win, bg=self.BTN, fg=self.FG, insertbackground=self.ACCENT, width=22)
            e_L.grid(row=2, column=1, padx=8, pady=4, ipady=4)
    
            tk.Label(win, text="l (m)", fg=self.FG, bg=self.BG).grid(row=3, column=0, sticky="w", padx=8, pady=4)
            e_l = tk.Entry(win, bg=self.BTN, fg=self.FG, insertbackground=self.ACCENT, width=22)
            e_l.grid(row=3, column=1, padx=8, pady=4, ipady=4)
    
            tk.Label(win, text="h (m, vide si non)", fg=self.FG, bg=self.BG).grid(row=4, column=0, sticky="w", padx=8, pady=4)
            e_h = tk.Entry(win, bg=self.BTN, fg=self.FG, insertbackground=self.ACCENT, width=22)
            e_h.grid(row=4, column=1, padx=8, pady=4, ipady=4)
    
            tk.Label(win, text="Poids unitaire", fg=self.FG, bg=self.BG).grid(row=5, column=0, sticky="w", padx=8, pady=4)
            cb_var = tk.StringVar()
            cb = ttk.Combobox(win, textvariable=cb_var, state="readonly", width=20)
            cb.grid(row=5, column=1, padx=8, pady=4)
    
            tk.Label(win, text="PU valeur", fg=self.FG, bg=self.BG).grid(row=6, column=0, sticky="w", padx=8, pady=4)
            e_pu = tk.Entry(win, bg=self.BTN, fg=self.FG, insertbackground=self.ACCENT, width=22)
            e_pu.grid(row=6, column=1, padx=8, pady=4, ipady=4)
    
            def upd_pu_list(*args):
                h_txt = e_h.get().strip()
                try:
                    has_h = h_txt != "" and float(h_txt.replace(",", ".")) > 0
                except ValueError:
                    has_h = False
                if has_h:
                    labels = [f"{n} — {v:.2f} kN/m³" if v is not None else n for n, v in PU_VOL]
                    win._pu = PU_VOL
                else:
                    labels = [f"{n} — {v:.2f} kN/m²" if v is not None else n for n, v in PU_SURF]
                    win._pu = PU_SURF
                cb["values"] = labels
                if labels:
                    cb.current(0)
                    if win._pu[0][1] is not None:
                        e_pu.delete(0, tk.END)
                        e_pu.insert(0, str(win._pu[0][1]))
    
            e_h.bind("<FocusOut>", upd_pu_list)
            e_h.bind("<Return>", upd_pu_list)
            upd_pu_list()
    
            def on_cb(*a):
                i = cb.current()
                if i >= 0 and win._pu[i][1] is not None:
                    e_pu.delete(0, tk.END)
                    e_pu.insert(0, str(win._pu[i][1]))
            cb.bind("<<ComboboxSelected>>", on_cb)
    
            def ok():
                try:
                    des = e_des.get().strip() or "Élément"
                    NPE = float(e_npe.get().replace(",", ".") or 1)
                    L = float(e_L.get().replace(",", ".") or 0)
                    l = float(e_l.get().replace(",", ".") or 0)
                    hraw = e_h.get().strip()
                    h = float(hraw.replace(",", ".")) if hraw else 0
                    PU = float(e_pu.get().replace(",", ".") or 0)
                    el = {"designation": des, "NPE": NPE, "L": L, "l": l,
                          "h": h, "PU": PU}
                    key = "elements_G" if t == "G" else "elements_Q"
                    state["projet"]["niveaux"][niv].setdefault(key, []).append(el)
                    refresh()
                    win.destroy()
                except Exception as e:
                    messagebox.showerror("Erreur", str(e), parent=win)
    
            tk.Button(win, text="Ajouter", bg=self.GREEN, fg=self.BG,
                      relief=tk.FLAT, padx=14, pady=6, command=ok).grid(
                row=7, column=0, columnspan=2, pady=10)
    
        def add_niveau():
            n = len(state["projet"]["niveaux"]) + 1
            state["projet"]["niveaux"].append(
                {"numero": n, "elements_G": [], "elements_Q": []})
            refresh()
    
        def del_sel():
            sel = tree.selection()
            if not sel:
                return
            # parcours pour retrouver
            for s in sel:
                vals = tree.item(s, "values")
                niv_n = int(vals[0][1:])
                t = vals[1]
                des = vals[2]
                key = "elements_G" if t == "G" else "elements_Q"
                lst = state["projet"]["niveaux"][niv_n-1].get(key, [])
                for i, e in enumerate(lst):
                    if e["designation"] == des:
                        lst.pop(i)
                        break
            refresh()
    
        def save_proj():
            state["projet"]["nom"] = e_nom.get().strip() or "Sans nom"
            state["projet"]["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            data = load()
            data = [p for p in data if p.get("nom") != state["projet"]["nom"]]
            data.append(state["projet"])
            save(data)
    
        # Boutons
        bf = tk.Frame(body, bg=self.BG)
        bf.pack(fill=tk.X)
        cfg = dict(font=("Segoe UI", 10), bg=self.BTN, fg=self.FG,
                   activebackground=self.ACCENT, activeforeground=self.BG,
                   relief=tk.FLAT, padx=12, pady=8, cursor="hand2")
        tk.Button(bf, text="➕ Ajouter élément", command=dialog_add, **cfg).pack(side=tk.LEFT, padx=3)
        tk.Button(bf, text="➕ Niveau", command=add_niveau, **cfg).pack(side=tk.LEFT, padx=3)
        tk.Button(bf, text="🗑 Supprimer", command=del_sel, **cfg).pack(side=tk.LEFT, padx=3)
        tk.Button(bf, text="💾 Enregistrer", command=save_proj,
                  font=("Segoe UI", 10, "bold"), bg=self.GREEN, fg=self.BG,
                  relief=tk.FLAT, padx=12, pady=8).pack(side=tk.LEFT, padx=3)
    
        refresh()
    
    
    # =============================================================
    # PROGRAMME PRINCIPAL
    # =============================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = BTPtk(root)
    root.mainloop()