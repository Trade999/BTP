import math
import os
import sys
import json
import csv
import uuid
from datetime import datetime

# Affichage amélioré avec Rich
# Installation : pip install rich
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.align import Align
    from rich.text import Text
    from rich.table import Table
    from rich.box import ROUNDED, DOUBLE, HEAVY
    from rich.theme import Theme

    _theme = Theme({
        "btp.title": "bold bright_cyan",
        "btp.section": "bold bright_yellow",
        "btp.result": "bold bright_green",
        "btp.warning": "bold bright_red",
        "btp.info": "bright_white",
        "btp.prompt": "bold bright_cyan",
        "btp.number": "bold bright_magenta",
    })
    console = Console(theme=_theme, markup=False, highlight=False)

    def _color_print(*objects, **kwargs):
        """Coloration automatique des sorties texte du programme."""
        converted = []
        for obj in objects:
            if not isinstance(obj, str):
                converted.append(obj)
                continue

            # Couleurs sémantiques pour les résultats et titres.
            s = obj
            if any(k in s for k in ("ERREUR", "Erreur", "⚠", "ATTENTION", "INVALIDE")):
                converted.append(Text(s, style="btp.warning"))
            elif any(k in s for k in ("✓", "TERMINÉ", "TERMINÉE", "RÉSULTAT", "RESULTAT", "As =", "Nser", "Mser", "MEd")):
                converted.append(Text(s, style="btp.result"))
            elif any(k in s for k in ("CALCUL", "MENU", "SCHÉMA", "DIMENSION", "ARMATURE", "FER", "ACIERS")):
                converted.append(Text(s, style="btp.section"))
            elif s.strip().startswith(("=", "╔", "╚", "║", "╠", "┌", "└")):
                converted.append(Text(s, style="bright_blue"))
            else:
                converted.append(Text(s, style="btp.info"))
        console.print(*converted, **kwargs)

    def _color_input(prompt=""):
        return console.input(Text(str(prompt), style="btp.prompt"))

    print = _color_print
    input = _color_input
except ImportError:
    console = None

class BTP:

    def __init__(self):
        # =====================================================
        # CONSTANTES MATERIAUX
        # =====================================================

        self.Fe = 400.0       # MPa
        self.Fc28 = 25.0      # MPa
        self.gamma_b = 1.5
        self.gamma_s = 1.15

    # =========================================================
    # OUTILS
    # =========================================================

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def banner(self):
        if console is not None:
            logo = (
                "██████╗ ████████╗██████╗\n"
                "██╔══██╗╚══██╔══╝██╔══██╗\n"
                "██████╔╝   ██║   ██████╔╝\n"
                "██╔══██╗   ██║   ██╔═══╝\n"
                "██████╔╝   ██║   ██║\n"
                "╚═════╝    ╚═╝   ╚═╝"
            )
            titre = Text()
            titre.append(logo, style="bold")
            titre.append("\n\nBÂTIMENT • TRAVAUX PUBLICS", style="bold")
            titre.append("\nPré-dimensionnement • Calcul • Quantitatif", style="bold")
            titre.append("\n\nDevelloper: Lariot", style="bold")
            print(Panel(
                Align.center(titre),
                title="BTPGPT",
                subtitle="Calcul BTP",
                box=DOUBLE,
                expand=True
            ))
            print()
        else:
            print("=" * 70)
            print(" " * 23 + "BTP")
            print("=" * 70)
            print(" " * 10 + "Pré-dimensionnement & Quantitatif")
            print(" " * 25 + "Develloper: Lariot")
            print("=" * 70)
            print()

    def pause(self):
        input("\nAppuyez sur ENTER pour continuer...")

    def section(self, titre, icone=""):
        texte = f"{icone} {titre}".strip()
        if console is not None:
            print(Panel(
                Align.center(Text(texte, style="bold")),
                box=ROUNDED,
                expand=True
            ))
        else:
            print()
            print("=" * 70)
            print(texte.center(70))
            print("=" * 70)

    def schema_armatures(self, nb_barres, diametre, titre="SCHÉMA DES ARMATURES"):
        """Schéma indicatif d'une section BA avec barres longitudinales."""
        try:
            n = int(nb_barres)
            d = float(diametre)
        except (TypeError, ValueError):
            return
        n = max(1, min(n, 12))

        positions = []
        if n == 1:
            positions = [(15, 7)]
        elif n == 2:
            positions = [(8, 7), (22, 7)]
        elif n == 3:
            positions = [(8, 3), (15, 7), (22, 3)]
        elif n == 4:
            positions = [(8, 3), (22, 3), (8, 11), (22, 11)]
        else:
            top = max(2, (n + 1) // 2)
            bottom = n - top
            for i in range(top):
                x = 5 + i * (25 - 5) / max(top - 1, 1)
                positions.append((round(x), 3))
            for i in range(bottom):
                x = 5 + i * (25 - 5) / max(bottom - 1, 1)
                positions.append((round(x), 11))

        grid = [[" " for _ in range(31)] for _ in range(15)]
        for x in range(4, 27):
            grid[1][x] = "─"
            grid[13][x] = "─"
        for y in range(2, 13):
            grid[y][4] = "│"
            grid[y][26] = "│"
        grid[1][4] = "┌"; grid[1][26] = "┐"
        grid[13][4] = "└"; grid[13][26] = "┘"

        for x, y in positions:
            grid[y][x] = "●"

        dessin = "\n".join("".join(row) for row in grid)

        if console is not None:
            t = Table.grid(expand=True)
            t.add_column(justify="center")
            t.add_row(Text(dessin))
            t.add_row("")
            t.add_row(Text(f"{n}HA{d:g}  →  {n} barres HA Ø{d:g} mm", style="bold"))
            t.add_row(Text("Section BA : vue indicative", style="bold"))
            print(Panel(t, title=titre, box=HEAVY, expand=True))
        else:
            print("+" + "-" * 21 + "+")
            print(dessin)
            print("+" + "-" * 21 + "+")
            print(f"{n}HA{d:g} → {n} barres HA Ø{d:g} mm")

    def lire_float(self, message, minimum=0):
        while True:
            try:
                valeur = float(input(message))

                if valeur <= minimum:
                    print(f"❌ La valeur doit être > {minimum}.")
                    continue

                return valeur

            except ValueError:
                print("❌ Erreur : veuillez entrer un nombre valide.")

    def oui_non(self, message):

        while True:

            choix = input(message).strip().lower()

            if choix in ["o", "oui"]:
                return True

            if choix in ["n", "non"]:
                return False

            print("❌ Répondez par Oui ou Non.")

    # =========================================================
    # FORMATAGE ARIARY
    # =========================================================

    def format_ar(self, valeur):

        return f"{valeur:,.0f}".replace(",", " ") + " Ar"

    # =========================================================
    # CALCUL PRIX
    # =========================================================

    def calcul_prix(self, quantite, nom_unite):

        print()
        print("-" * 70)
        print("💰 CALCUL DU PRIX")
        print("-" * 70)
        print()

        choix = self.oui_non(
            "Voulez-vous calculer le prix total ? (Oui/Non) : "
        )

        if not choix:

            print()
            print("✓ Calcul du prix ignoré.")
            return None

        prix_unitaire = self.lire_float(
            f"Prix d'une unité de {nom_unite} (Ar) : "
        )

        prix_total = quantite * prix_unitaire

        print()
        print("Formule :")
        print()
        print("Prix total = Nombre d'unités × Prix unitaire")
        print()

        print(
            f"Prix total = {quantite} × "
            f"{self.format_ar(prix_unitaire)}"
        )

        print()
        print(
            f"💰 PRIX TOTAL = "
            f"{self.format_ar(prix_total)}"
        )

        return prix_total

    # =========================================================
    # CHOIX AUTOMATIQUE DANS UN INTERVALLE
    # =========================================================

    def prenons(self, nom, minimum, maximum, unite="m"):

        moyenne = (minimum + maximum) / 2

        print()
        print(f"📐 CHOIX DE {nom.upper()}")
        print("-" * 70)

        print(
            f"Intervalle : "
            f"{minimum:.3f} ≤ {nom} ≤ {maximum:.3f} {unite}"
        )

        print(
            f"Valeur automatique : "
            f"{moyenne:.3f} {unite}"
        )

        while True:

            choix = input(
                f"Choisir {nom} "
                f"(ENTER = automatique) : "
            ).strip()

            if choix == "":

                print(
                    f"✓ {nom} automatique = "
                    f"{moyenne:.3f} {unite}"
                )

                return moyenne

            try:

                valeur = float(choix)

                if minimum <= valeur <= maximum:

                    print(
                        f"✓ {nom} choisi = "
                        f"{valeur:.3f} {unite}"
                    )

                    return valeur

                print(
                    f"❌ La valeur doit être comprise entre "
                    f"{minimum:.3f} et {maximum:.3f}."
                )

            except ValueError:

                print(
                    "❌ Veuillez entrer un nombre valide."
                )

    # =========================================================
    # 1 - CALCUL DE BRIQUE
    # =========================================================

    def mur(self):

        while True:

            self.clear_screen()
            self.banner()

            print("=" * 70)
            print(" " * 22 + "CALCUL DE BRIQUE")
            print("=" * 70)
            print()

            L = self.lire_float(
                "Longueur de brique L (m) : "
            )

            l = self.lire_float(
                "Largeur de brique l (m) : "
            )

            t = self.lire_float(
                "Surface totale du mur T (m²) : "
            )

            s = L * l

            print()
            print("-" * 70)
            print("📐 SURFACE D'UNE BRIQUE")
            print("-" * 70)

            print()
            print("Formule :")
            print()
            print("        S = L × l")
            print()

            print(
                f"S = {L:.3f} × {l:.3f}"
                f" = {s:.4f} m²"
            )

            u = t / s

            print()
            print("-" * 70)
            print("🧱 NOMBRE DE BRIQUES")
            print("-" * 70)

            print()
            print("Formule :")
            print()
            print("        T")
            print("N =  ───────")
            print("        S")
            print()

            print(
                f"N = {t:.2f} / {s:.4f}"
                f" = {u:.2f} U"
            )

            total = math.ceil(u)

            print()
            print(f"✓ TOTAL DE BRIQUES = {total} U")

            prix_total = self.calcul_prix(
                total,
                "brique"
            )

            print()
            print("=" * 70)
            print(" " * 27 + "RÉSULTAT")
            print("=" * 70)

            print()
            print(f"Longueur brique : {L:.3f} m")
            print(f"Largeur brique  : {l:.3f} m")
            print(f"Surface brique  : {s:.4f} m²")
            print(f"Surface totale  : {t:.2f} m²")
            print(f"Nombre calculé  : {u:.2f} U")
            print(f"TOTAL À PRÉVOIR : {total} U")

            if prix_total is not None:

                print(
                    f"PRIX TOTAL      : "
                    f"{self.format_ar(prix_total)}"
                )

            print()
            print("=" * 70)

            refaire = input(
                "\nNouveau calcul de brique ? (O/N) : "
            ).strip().lower()

            if refaire not in ["o", "oui"]:
                break

    # =========================================================
    # 2 - CALCUL DALLE & POUTRE
    # =========================================================

    def dalle_and_poutre(self):

        while True:

            self.clear_screen()
            self.banner()

            print("=" * 70)
            print(" " * 18 + "CALCUL DALLE & POUTRE")
            print("=" * 70)
            print()

            ly = self.lire_float(
                "Longueur grande portée Ly (m) : "
            )

            lx = self.lire_float(
                "Longueur petite portée Lx (m) : "
            )

            if lx > ly:

                print()
                print("⚠️ ERREUR : Lx doit être ≤ Ly.")
                self.pause()
                continue

            value = lx / ly

            print()
            print("-" * 70)
            print("📊 RAPPORT DES PORTÉES")
            print("-" * 70)

            print()
            print("Formule :")
            print()
            print("        Lx")
            print("μ =  ───────")
            print("        Ly")
            print()

            print(
                f"μ = {lx:.3f} / {ly:.3f}"
                f" = {value:.3f}"
            )

            if value < 0.81:

                print(
                    f"⚠️ μ = {value:.3f} < 0.81"
                )

            else:

                print(
                    f"✓ μ = {value:.3f} ≥ 0.81"
                )

            # -------------------------------------------------
            # EPAISSEUR DALLE
            # -------------------------------------------------

            e_min = lx / 35
            e_max = lx / 30

            print()
            print("-" * 70)
            print("🧱 ÉPAISSEUR DE DALLE")
            print("-" * 70)

            print()
            print("Formule :")
            print()
            print("        Lx          Lx")
            print("e :  ─────── ≤ e ≤ ───────")
            print("         35          30")
            print()

            print(
                f"e : {e_min:.3f} ≤ e ≤ "
                f"{e_max:.3f} m"
            )

            e = self.prenons(
                "e",
                e_min,
                e_max,
                "m"
            )

            # -------------------------------------------------
            # HAUTEUR POUTRE
            # -------------------------------------------------

            h_min = ly / 15
            h_max = ly / 10

            print()
            print("-" * 70)
            print("🏗️ HAUTEUR DE POUTRE")
            print("-" * 70)

            print()
            print("Formule :")
            print()
            print("        Ly          Ly")
            print("h :  ─────── ≤ h ≤ ───────")
            print("         15          10")
            print()

            print(
                f"h : {h_min:.3f} ≤ h ≤ "
                f"{h_max:.3f} m"
            )

            h = self.prenons(
                "h",
                h_min,
                h_max,
                "m"
            )

            # -------------------------------------------------
            # BASE POUTRE
            # -------------------------------------------------

            b_min = 0.3 * h
            b_max = 0.6 * h

            print()
            print("-" * 70)
            print("📏 BASE DE POUTRE")
            print("-" * 70)

            print()
            print("Formule :")
            print()
            print("b : 0.3 × h ≤ b ≤ 0.6 × h")
            print()

            print(
                f"b : {b_min:.3f} ≤ b ≤ "
                f"{b_max:.3f} m"
            )

            b = self.prenons(
                "b",
                b_min,
                b_max,
                "m"
            )

            # -------------------------------------------------
            # RESULTATS
            # -------------------------------------------------

            self.clear_screen()
            self.banner()

            print("=" * 70)
            print(" " * 26 + "RÉSULTATS")
            print("=" * 70)

            print()
            print("📐 DALLE")
            print(f"   Ly = {ly:.3f} m")
            print(f"   Lx = {lx:.3f} m")
            print(f"   μ  = {value:.3f}")
            print(f"   e  = {e:.3f} m")

            print()
            print("🏗️ POUTRE")
            print(f"   h  = {h:.3f} m")
            print(f"   b  = {b:.3f} m")

            print()
            print("=" * 70)
            print("✓ CALCUL TERMINÉ")
            print("=" * 70)

            refaire = input(
                "\nNouveau calcul dalle/poutre ? (O/N) : "
            ).strip().lower()

            if refaire not in ["o", "oui"]:
                break

    # =========================================================
    # 6 - CALCUL COMPLET DE LA DALLE
    # Référentiel : BAEL 91 révisé 99 (Annexe E.3, A.4.2.1, A.8.2)
    # =========================================================
    
    def dalle_complete(self):
        """Calcul complet d'une dalle pleine rectangulaire.
    
        Méthode : Annexe E.3 du BAEL 91 (méthode de Pigeaud)
          • α < 0.40 : dalle portant dans un seul sens (Lx)
          • α ≥ 0.40 : dalle portant dans les deux sens (Lx et Ly)
    
        Vérifications incluses :
          • Flexion ELU : Mtx, Mty, Max, May
          • Condition de non-fragilité : Amin = 0.23·b·d·ft28/fe
          • Effort tranchant : τu ≤ τu,lim (A.5.2)
          • Espacement : St ≤ min(3h ; 33 cm) sens Lx
                         St ≤ min(4h ; 45 cm) sens Ly
          • Choix automatique des armatures
        """
    
        # =====================================================
        # TABLE DES COEFFICIENTS μx, μy (Annexe E.3 BAEL 91)
        # =====================================================
        # Valeurs pour ν = 0 (ELU) et ν = 0.2 (ELS)
    
        TABLE_MU_ELU = {
            0.40: (0.1101, 0.2500),
            0.45: (0.0980, 0.3400),
            0.50: (0.0890, 0.4360),
            0.55: (0.0790, 0.5200),
            0.60: (0.0710, 0.6060),
            0.65: (0.0630, 0.6700),
            0.70: (0.0560, 0.7300),
            0.75: (0.0495, 0.7900),
            0.80: (0.0440, 0.8480),
            0.85: (0.0390, 0.8840),
            0.90: (0.0350, 0.9200),
            0.95: (0.0317, 0.9600),
            1.00: (0.0290, 1.0000),
        }
    
        TABLE_MU_ELS = {
            0.40: (0.1200, 0.2900),
            0.50: (0.0950, 0.4800),
            0.60: (0.0750, 0.6500),
            0.70: (0.0590, 0.7800),
            0.80: (0.0460, 0.8900),
            0.90: (0.0360, 0.9500),
            1.00: (0.0300, 1.0000),
        }
    
        def interp_table(table, alpha):
            """Interpolation linéaire dans la table des coefficients μ."""
            keys = sorted(table.keys())
            if alpha <= keys[0]:
                return table[keys[0]]
            if alpha >= keys[-1]:
                return table[keys[-1]]
            for k1, k2 in zip(keys, keys[1:]):
                if k1 <= alpha <= k2:
                    v1 = table[k1]
                    v2 = table[k2]
                    t = (alpha - k1) / (k2 - k1)
                    return (
                        v1[0] + t * (v2[0] - v1[0]),
                        v1[1] + t * (v2[1] - v1[1]),
                    )
            return table[keys[-1]]
    
        while True:
    
            self.clear_screen()
            self.banner()
    
            print("=" * 70)
            print(" " * 20 + "CALCUL COMPLET DE LA DALLE")
            print("=" * 70)
            print()
    
            print("📌 DONNÉES DE DÉPART")
            print("-" * 70)
    
            Ly = self.lire_float("Longueur grande portée Ly (m) : ")
            Lx = self.lire_float("Longueur petite portée Lx (m) : ")
    
            if Lx > Ly:
                print()
                print("❌ ERREUR : Lx doit être ≤ Ly.")
                self.pause()
                continue
    
            h = self.lire_float("Épaisseur de la dalle h (m) : ")
    
            if h <= 0:
                continue
    
            # =================================================
            # MATÉRIAUX
            # =================================================
            Fe = self.Fe
            Fc28 = self.Fc28
            gamma_b = self.gamma_b
            gamma_s = self.gamma_s
            Fed = Fe / gamma_s
    
            # =================================================
            # 1 - RAPPORT DES PORTÉES
            # =================================================
            alpha_rapport = Lx / Ly
    
            # =================================================
            # 2 - CHARGES
            # =================================================
            gamma_beton = 25.0
    
            charge_carreaux = 0.60
    
            ep_enduit = self.lire_float(
                "Épaisseur de l'enduit (m) [0.020] : ", minimum=0
            )
    
            gamma_enduit = 22
    
            charge_exploitation = 2.5
    
            pp_dalle = h * gamma_beton
            enduit = ep_enduit * gamma_enduit
            Pu = pp_dalle + charge_carreaux + enduit
            Pu_MN_m2 = Pu / 1000.0
            Q_surfacique = charge_exploitation
    
            # =================================================
            # 3 - MOMENTS (SELON LE SENS DE PORTÉE)
            # =================================================
    
            if alpha_rapport < 0.40:
                # Dalle portant dans un seul sens (Lx)
                M0x = Pu_MN_m2 * Lx ** 2 / 8.0
                M0y = 0.0
                mu_x_elu = None
                mu_y_elu = None
                sens_portee = "un seul sens (Lx)"
                Vx = Pu_MN_m2 * Lx / 2.0
                Vy = 0.0
            else:
                # Dalle portant dans les deux sens
                mu_x_elu, mu_y_elu = interp_table(TABLE_MU_ELU, alpha_rapport)
                M0x = mu_x_elu * Pu_MN_m2 * Lx ** 2
                M0y = mu_y_elu * M0x
                sens_portee = "deux sens (Lx et Ly)"
    
                # Effort tranchant (Annexe E.3)
                Vx = Pu_MN_m2 * Lx / 2.0 * 1.0 / (1.0 + alpha_rapport / 2.0)
                Vy = Pu_MN_m2 * Lx / 3.0
    
            # Moments en travée (panneau de rive)
            Mtx = 0.85 * M0x
            Mty = 0.85 * M0y if M0y > 0 else 0.0
    
            # Moments sur appuis (panneau de rive)
            Max = 0.30 * M0x
            May = 0.30 * M0y if M0y > 0 else 0.0
    
            # =================================================
            # 4 - MOMENT RÉDUIT ET BRAS DE LEVIER
            # =================================================
    
            Fbu = 0.85 * Fc28 / gamma_b
            bo = 1.00          # bande de 1 m
            d = 0.9 * h        # hauteur utile
    
            if d <= 0:
                print()
                print("❌ ERREUR : la hauteur utile d doit être > 0.")
                self.pause()
                continue
    
            # Calcul du moment réduit pour Mtx
            Mlu = Mtx / (bo * d ** 2 * Fbu)
    
            terme_racine = 1.0 - 2.0 * Mlu
    
            if terme_racine < 0:
                print()
                print("⚠️ 1 − 2·Mlu < 0 : section doublement armée nécessaire.")
                alpha_zb = None
                Zb = None
            else:
                alpha_zb = 1.25 * (1.0 - math.sqrt(terme_racine))
                Zb = d * (1.0 - 0.4 * alpha_zb)
    
            # =================================================
            # 5 - ARMATURES CALCULÉES
            # =================================================
    
            if Zb is not None and Zb > 0:
                Ax_calc_m2 = Mtx / (Zb * Fed)
                Ax_calc_cm2 = Ax_calc_m2 * 10000.0
            else:
                Ax_calc_cm2 = None
    
            if Mty > 0 and Zb is not None and Zb > 0:
                Ay_calc_m2 = Mty / (Zb * Fed)
                Ay_calc_cm2 = Ay_calc_m2 * 10000.0
            else:
                Ay_calc_cm2 = 0.0
    
            # =================================================
            # 6 - ARMATURES MINIMALES (BAEL A.4.2.1)
            # =================================================
            # Amin = 0.23 × b × d × ft28 / fe
            # ft28 = 0.6 + 0.06·Fc28 (limité à 3.3 MPa)
    
            ft28 = min(0.6 + 0.06 * Fc28, 3.3)
            b_cm = bo * 100.0
            d_cm = d * 100.0
    
            Amin_cm2 = 0.23 * b_cm * d_cm * ft28 / Fe
    
            # Condition B.6.4 : Amin ≥ 0.001 × B × h
            Amin_B64_cm2 = 0.001 * b_cm * h * 100.0
            Amin_cm2 = max(Amin_cm2, Amin_B64_cm2)
    
            # Armatures retenues
            Ax_retenue_cm2 = max(Ax_calc_cm2 or 0, Amin_cm2)
            Ay_retenue_cm2 = max(Ay_calc_cm2 or 0, Amin_cm2) if M0y > 0 else 0.0
    
            # =================================================
            # 7 - CHOIX AUTOMATIQUE DES ARMATURES (SENS X)
            # =================================================
    
            diametres = [8, 10, 12, 14, 16, 20, 25, 32]
            ESP_MAX_X_CM = min(3.0 * h * 100.0, 33.0)  # min(3h ; 33 cm)
            ESP_MAX_Y_CM = min(4.0 * h * 100.0, 45.0)  # min(4h ; 45 cm)
    
            def choisir_armatures(As_req_cm2, esp_max_cm):
                """Recherche automatique de la combinaison optimale."""
                choix = []
                for diam in diametres:
                    aire_barre_cm2 = math.pi * diam ** 2 / 4.0 / 100.0
                    for n in range(1, 33):
                        As_fournie = n * aire_barre_cm2
                        if As_fournie >= As_req_cm2:
                            esp_cm = 100.0 / n
                            if esp_cm <= esp_max_cm + 1e-9:
                                surplus = As_fournie - As_req_cm2
                                choix.append((surplus, diam, n, As_fournie, esp_cm))
                if choix:
                    return min(choix, key=lambda x: (x[0], x[1], x[2]))
                # Fallback : plus grand nombre de barres et plus grand diamètre
                diam = diametres[-1]
                aire_barre_cm2 = math.pi * diam ** 2 / 4.0 / 100.0
                n = 32
                As_fournie = n * aire_barre_cm2
                esp_cm = 100.0 / n
                return (As_fournie - As_req_cm2, diam, n, As_fournie, esp_cm)
    
            # Choix sens X
            _, diam_x, nb_x, As_x_fournie_cm2, esp_x_cm = choisir_armatures(
                Ax_retenue_cm2, ESP_MAX_X_CM
            )
    
            # Choix sens Y (si dalle à deux sens)
            if M0y > 0:
                _, diam_y, nb_y, As_y_fournie_cm2, esp_y_cm = choisir_armatures(
                    Ay_retenue_cm2, ESP_MAX_Y_CM
                )
            else:
                diam_y = None
                nb_y = 0
                As_y_fournie_cm2 = 0.0
                esp_y_cm = 0.0
    
            # =================================================
            # 8 - VÉRIFICATION DE L'EFFORT TRANCHANT (A.5.2)
            # =================================================
    
            tau_u_x = Vx * 1000.0 / (b_cm * d_cm) if Vx > 0 else 0.0
            tau_u_y = Vy * 1000.0 / (b_cm * d_cm) if Vy > 0 else 0.0
            tau_u_max = max(tau_u_x, tau_u_y)
    
            # τu,lim pour dalle (fissuration peu préjudiciable)
            tau_lim = min(0.20 * Fc28 / gamma_b, 5.0)
            effort_tranchant_ok = tau_u_max <= tau_lim
    
            # =================================================
            # AFFICHAGE COMPLET
            # =================================================
    
            self.clear_screen()
            self.banner()
    
            print("=" * 70)
            print(" " * 20 + "CALCUL COMPLET DE LA DALLE")
            print("=" * 70)
    
            print()
            print("📌 DONNÉES DE DÉPART")
            print("-" * 70)
            print(f"Ly = {Ly:.3f} m")
            print(f"Lx = {Lx:.3f} m")
            print(f"h  = {h:.3f} m = {h*100:.1f} cm")
            print(f"Fe = {Fe:.0f} MPa")
            print(f"Fc28 = {Fc28:.0f} MPa")
            print(f"γb = {gamma_b:.2f}")
            print(f"γs = {gamma_s:.2f}")
    
            # -------------------------------------------------
            # 1 - RAPPORT DES PORTÉES
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("1 - DÉTERMINATION DU SENS DE PORTÉE")
            print("=" * 70)
            print()
            print("Formule : α = Lx / Ly")
            print()
            print(f"α = {Lx:.3f} / {Ly:.3f} = {alpha_rapport:.3f}")
            print()
            print(f"✓ Sens de portée : {sens_portee}")
    
            if alpha_rapport < 0.40:
                print("   α < 0.40 → la dalle porte dans un seul sens (Lx)")
            else:
                print("   α ≥ 0.40 → la dalle porte dans les deux sens (Lx et Ly)")
    
            # -------------------------------------------------
            # 2 - CHARGES
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("2 - DÉTERMINATION DES CHARGES")
            print("=" * 70)
            print()
            print("Poids propre de la dalle :")
            print("pp = h × γ")
            print(f"pp = {h:.3f} × {gamma_beton:.2f} = {pp_dalle:.3f} kN/m²")
            print()
            print(f"Carreaux = {charge_carreaux:.3f} kN/m²")
            print()
            print("Enduit :")
            print(f"Enduit = {ep_enduit:.3f} × {gamma_enduit:.2f} = {enduit:.3f} kN/m²")
            print()
            print("Charge permanente surfacique Pu :")
            print(f"Pu = {pp_dalle:.3f} + {charge_carreaux:.3f} + {enduit:.3f}")
            print(f"Pu = {Pu:.3f} kN/m² = {Pu_MN_m2:.6f} MN/m²")
            print()
            print(f"Charge d'exploitation Q = {Q_surfacique:.3f} kN/m²")
    
            # -------------------------------------------------
            # 3 - MOMENTS
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("3 - CALCUL DES MOMENTS")
            print("=" * 70)
    
            if alpha_rapport < 0.40:
                print()
                print("Mux = Pu × Lx² / 8")
                print(f"Mux = {Pu_MN_m2:.6f} × {Lx:.3f}² / 8")
                print(f"✓ M0x = {M0x:.4f} MN.m")
                print(f"✓ M0y = 0 (dalle à un seul sens)")
            else:
                print()
                print(f"Coefficients μx, μy (Annexe E.3, ν=0) :")
                print(f"μx = {mu_x_elu:.4f}")
                print(f"μy = {mu_y_elu:.4f}")
                print()
                print("M0x = μx × Pu × Lx²")
                print(f"M0x = {mu_x_elu:.4f} × {Pu_MN_m2:.6f} × {Lx:.3f}²")
                print(f"✓ M0x = {M0x:.4f} MN.m")
                print()
                print("M0y = μy × M0x")
                print(f"M0y = {mu_y_elu:.4f} × {M0x:.4f}")
                print(f"✓ M0y = {M0y:.4f} MN.m")
    
            print()
            print("Moments en travée (panneau de rive) :")
            print(f"Mtx = 0.85 × M0x = {Mtx:.4f} MN.m")
            if M0y > 0:
                print(f"Mty = 0.85 × M0y = {Mty:.4f} MN.m")
    
            print()
            print("Moments sur appuis (panneau de rive) :")
            print(f"Max = 0.30 × M0x = {Max:.4f} MN.m")
            if M0y > 0:
                print(f"May = 0.30 × M0y = {May:.4f} MN.m")
    
            # -------------------------------------------------
            # 4 - MOMENT RÉDUIT ET BRAS DE LEVIER
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("4 - CALCUL DE Mlu ET Zb (SENS X)")
            print("=" * 70)
            print()
            print("Fbu = 0.85 × Fc28 / γb")
            print(f"Fbu = 0.85 × {Fc28:.0f} / {gamma_b:.2f} = {Fbu:.2f} MPa")
            print()
            print(f"bo = {bo:.2f} m")
            print(f"d = 0.9 × h = 0.9 × {h:.3f} = {d:.3f} m")
            print()
            print("Mlu = Mtx / (bo × d² × Fbu)")
            print(f"Mlu = {Mtx:.4f} / ({bo:.2f} × {d:.3f}² × {Fbu:.2f})")
            print(f"Mlu = {Mlu:.4f}")
    
            if alpha_zb is not None:
                print()
                print("α = 1.25[1 − √(1 − 2·Mlu)]")
                print(f"α = 1.25[1 − √(1 − 2 × {Mlu:.4f})] = {alpha_zb:.4f}")
                print()
                print("Zb = d(1 − 0.4α)")
                print(f"Zb = {d:.3f}(1 − 0.4 × {alpha_zb:.4f}) = {Zb:.4f} m")
            else:
                print()
                print("⚠️ Section doublement armée nécessaire.")
    
            # -------------------------------------------------
            # 5 - ARMATURES CALCULÉES
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("5 - SECTIONS D'ARMATURES CALCULÉES")
            print("=" * 70)
            print()
            print(f"Fed = Fe / γs = {Fe:.0f} / {gamma_s:.2f} = {Fed:.2f} MPa")
            print()
            print("Sens X : Ax ≥ Mtx / (Zb × Fed)")
            if Ax_calc_cm2 is not None:
                print(f"Ax ≥ {Mtx:.4f} / ({Zb:.4f} × {Fed:.2f})")
                print(f"Ax ≥ {Ax_calc_cm2:.3f} cm²")
            else:
                print("⚠️ Ax non calculée (section doublement armée).")
    
            if M0y > 0:
                print()
                print("Sens Y : Ay ≥ Mty / (Zb × Fed)")
                print(f"Ay ≥ {Mty:.4f} / ({Zb:.4f} × {Fed:.2f})")
                print(f"Ay ≥ {Ay_calc_cm2:.3f} cm²")
    
            # -------------------------------------------------
            # 6 - ARMATURES MINIMALES
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("6 - ARMATURE MINIMALE (NON-FRAGILITÉ)")
            print("=" * 70)
            print()
            print(f"ft28 = 0.6 + 0.06 × {Fc28:.0f} = {ft28:.3f} MPa")
            print()
            print("Amin = 0.23 × b × d × ft28 / fe")
            print(f"Amin = 0.23 × {b_cm:.1f} × {d_cm:.1f} × {ft28:.3f} / {Fe:.1f}")
            print(f"Amin = {Amin_cm2:.3f} cm²")
            print()
            print("Condition B.6.4 : Amin ≥ 0.001 × B × h")
            print(f"Amin,B64 = 0.001 × {b_cm:.1f} × {h*100:.1f} = {Amin_B64_cm2:.3f} cm²")
            print()
            print(f"✓ Amin retenue = max({Amin_cm2:.3f} ; {Amin_B64_cm2:.3f}) = {Amin_cm2:.3f} cm²")
            print()
            print(f"Sens X : Ax retenue = max({Ax_calc_cm2 or 0:.3f} ; {Amin_cm2:.3f}) = {Ax_retenue_cm2:.3f} cm²")
            if M0y > 0:
                print(f"Sens Y : Ay retenue = max({Ay_calc_cm2:.3f} ; {Amin_cm2:.3f}) = {Ay_retenue_cm2:.3f} cm²")
    
            # -------------------------------------------------
            # 7 - CHOIX DES ARMATURES
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("7 - CHOIX DES ARMATURES")
            print("=" * 70)
            print()
            print(f"Sens X : espacement max = min(3h ; 33 cm) = {ESP_MAX_X_CM:.1f} cm")
            print(f"✓ Choix : {nb_x}HA{diam_x} / ml")
            print(f"As fournie = {nb_x} × π × {diam_x}² / 4 = {As_x_fournie_cm2:.3f} cm²")
            print(f"Espacement = {esp_x_cm:.1f} cm")
    
            if M0y > 0:
                print()
                print(f"Sens Y : espacement max = min(4h ; 45 cm) = {ESP_MAX_Y_CM:.1f} cm")
                print(f"✓ Choix : {nb_y}HA{diam_y} / ml")
                print(f"As fournie = {nb_y} × π × {diam_y}² / 4 = {As_y_fournie_cm2:.3f} cm²")
                print(f"Espacement = {esp_y_cm:.1f} cm")
    
            # -------------------------------------------------
            # 8 - EFFORT TRANCHANT
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("8 - VÉRIFICATION DE L'EFFORT TRANCHANT (A.5.2)")
            print("=" * 70)
            print()
            print(f"Sens X : Vx = {Vx:.4f} MN/m")
            print(f"τu,x = Vx / (b × d) = {Vx*1000:.1f} / ({b_cm:.1f} × {d_cm:.1f})")
            print(f"τu,x = {tau_u_x:.4f} MPa")
    
            if M0y > 0:
                print()
                print(f"Sens Y : Vy = {Vy:.4f} MN/m")
                print(f"τu,y = Vy / (b × d) = {Vy*1000:.1f} / ({b_cm:.1f} × {d_cm:.1f})")
                print(f"τu,y = {tau_u_y:.4f} MPa")
    
            print()
            print(f"τu,lim = min(0.20·Fc28/γb ; 5 MPa) = {tau_lim:.3f} MPa")
            print(f"τu,max = {tau_u_max:.4f} MPa")
    
            if effort_tranchant_ok:
                print(f"✓ {tau_u_max:.4f} ≤ {tau_lim:.3f} : EFFORT TRANCHANT VÉRIFIÉ")
            else:
                print(f"⚠️ {tau_u_max:.4f} > {tau_lim:.3f} : NON VÉRIFIÉ")
                print("   → Augmenter h ou réduire la portée.")
    
            # -------------------------------------------------
            # RÉSULTAT FINAL
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print(" " * 23 + "RÉSULTAT FINAL")
            print("=" * 70)
    
            print()
            print("📐 DALLE")
            print(f"   Ly = {Ly:.3f} m")
            print(f"   Lx = {Lx:.3f} m")
            print(f"   α = {alpha_rapport:.3f} ({sens_portee})")
            print(f"   h = {h:.3f} m = {h*100:.1f} cm")
            print(f"   d = {d:.3f} m = {d_cm:.1f} cm")
    
            print()
            print("⚖️ CHARGES")
            print(f"   pp dalle = {pp_dalle:.3f} kN/m²")
            print(f"   carreaux = {charge_carreaux:.3f} kN/m²")
            print(f"   enduit = {enduit:.3f} kN/m²")
            print(f"   Pu = {Pu:.3f} kN/m²")
            print(f"   Q = {Q_surfacique:.3f} kN/m²")
    
            print()
            print("🔨 FLEXION")
            print(f"   M0x = {M0x:.4f} MN.m")
            if M0y > 0:
                print(f"   M0y = {M0y:.4f} MN.m")
            print(f"   Mtx = {Mtx:.4f} MN.m")
            if M0y > 0:
                print(f"   Mty = {Mty:.4f} MN.m")
            print(f"   Max = {Max:.4f} MN.m")
            if M0y > 0:
                print(f"   May = {May:.4f} MN.m")
            print(f"   Mlu = {Mlu:.4f}")
    
            if Zb is not None:
                print(f"   α = {alpha_zb:.4f}")
                print(f"   Zb = {Zb:.4f} m")
    
            print()
            print("🔩 ARMATURES")
            print(f"   Amin = {Amin_cm2:.3f} cm²")
            print(f"   Sens X : Ax retenue = {Ax_retenue_cm2:.3f} cm²")
            print(f"            ✓ {nb_x}HA{diam_x} = {As_x_fournie_cm2:.3f} cm² (esp = {esp_x_cm:.1f} cm)")
    
            if M0y > 0:
                print(f"   Sens Y : Ay retenue = {Ay_retenue_cm2:.3f} cm²")
                print(f"            ✓ {nb_y}HA{diam_y} = {As_y_fournie_cm2:.3f} cm² (esp = {esp_y_cm:.1f} cm)")
    
            print()
            print("🛡️ EFFORT TRANCHANT")
            print(f"   τu,max = {tau_u_max:.4f} MPa")
            print(f"   τu,lim = {tau_lim:.3f} MPa")
            print("   ✓ Vérifié" if effort_tranchant_ok else "   ⚠️ NON vérifié")
    
            # Schémas
            self.schema_armatures(nb_x, diam_x, "SCHÉMA BA — DALLE (SENS X)")
            if M0y > 0:
                self.schema_armatures(nb_y, diam_y, "SCHÉMA BA — DALLE (SENS Y)")
    
            print()
            print("=" * 70)
            print("✓ CALCUL COMPLET DE LA DALLE TERMINÉ")
            print("=" * 70)
    
            print()
    
            refaire = input("Nouveau calcul de dalle complète ? (O/N) : ").strip().lower()
            if refaire not in ["o", "oui"]:
                break
    
        # =========================================================
        # 3 - CALCUL MOELLON
        # =========================================================

    def moellon(self):

        while True:

            self.clear_screen()
            self.banner()

            print("=" * 70)
            print(" " * 23 + "CALCUL MOELLON")
            print("=" * 70)
            print()

            L = self.lire_float(
                "Longueur du moellon L (m) : "
            )

            l = self.lire_float(
                "Largeur du moellon l (m) : "
            )

            e = self.lire_float(
                "Épaisseur du moellon e (m) : "
            )

            t = self.lire_float(
                "Volume total du mur T (m³) : "
            )

            v = L * l * e

            print()
            print("-" * 70)
            print("📐 VOLUME D'UN MOELLON")
            print("-" * 70)

            print()
            print("Formule :")
            print()
            print("V = L × l × e")
            print()

            print(
                f"V = {L:.3f} × {l:.3f} × {e:.3f}"
            )

            print(
                f"V = {v:.4f} m³"
            )

            u = t / v

            print()
            print("-" * 70)
            print("🪨 NOMBRE DE MOELLONS")
            print("-" * 70)

            print()
            print("Formule :")
            print()
            print("        T")
            print("N =  ───────")
            print("        V")
            print()

            print(
                f"N = {t:.2f} / {v:.4f}"
            )

            print(
                f"N = {u:.2f} unités"
            )

            total = math.ceil(u)

            print()
            print(
                f"✓ TOTAL DE MOELLONS = {total} U"
            )

            prix_total = self.calcul_prix(
                total,
                "moellon"
            )

            print()
            print("=" * 70)
            print(" " * 27 + "RÉSULTAT")
            print("=" * 70)

            print()
            print(f"Longueur       : {L:.3f} m")
            print(f"Largeur        : {l:.3f} m")
            print(f"Épaisseur      : {e:.3f} m")
            print(f"Volume/moellon : {v:.4f} m³")
            print(f"Volume total   : {t:.2f} m³")
            print(f"Nombre calculé : {u:.2f} U")
            print(f"TOTAL          : {total} U")

            if prix_total is not None:

                print(
                    f"PRIX TOTAL      : "
                    f"{self.format_ar(prix_total)}"
                )

            print()
            print("=" * 70)

            refaire = input(
                "\nNouveau calcul de moellon ? (O/N) : "
            ).strip().lower()

            if refaire not in ["o", "oui"]:
                break

    # =========================================================
    # 4 - CALCUL COMPLET DU POTEAU
    # Référentiel : BAEL 91 révisé 99 + NF DTU 13.12
    # =========================================================
    
    def poteau(self):
        """Calcul complet d'un poteau en compression centrée.
    
        Trois types de section supportés :
          • Poteau carré      (a = b)
          • Poteau rectangulaire (a ≠ b)
          • Poteau rond       (circulaire, diamètre D)
    
        Références BAEL 91 révisé 99 :
          • B.8.4.1 : effort normal résistant
          • A.8.1.2.1 : armatures minimales
          • A.8.1.3   : diamètre des armatures transversales
          • A.8.1.2.1 : espacement
          • A.6.1.2.1 : longueur de scelllement
          • B.8.3.31  : longueur de flambement
        """
    
        while True:
    
            self.clear_screen()
            self.banner()
    
            print("=" * 70)
            print(" " * 20 + "CALCUL COMPLET DU POTEAU")
            print("=" * 70)
            print()
    
            # =================================================
            # 0 - CHOIX DU TYPE DE POTEAU
            # =================================================
    
            print("📌 TYPE DE POTEAU")
            print("-" * 70)
            print("  1 - Poteau carré")
            print("  2 - Poteau rectangulaire")
            print("  3 - Poteau rond (circulaire)")
            print()
    
            while True:
                choix_type = input("👉 Votre choix (1, 2 ou 3) : ").strip()
                if choix_type in ("1", "2", "3"):
                    break
                print("❌ Choix invalide. Entrez 1, 2 ou 3.")
    
            type_poteau = {
                "1": "carré",
                "2": "rectangulaire",
                "3": "rond",
            }[choix_type]
    
            print(f"\n✓ Type retenu : Poteau {type_poteau}")
    
            # =================================================
            # 1 - DONNÉES GÉOMÉTRIQUES
            # =================================================
    
            print()
            print("📌 DONNÉES GÉOMÉTRIQUES")
            print("-" * 70)
    
            if type_poteau == "carré":
                a = self.lire_float("Côté du poteau a (m) : ")
                b = a
                D = None
    
            elif type_poteau == "rectangulaire":
                a = self.lire_float("Largeur a (m) : ")
                b = self.lire_float("Longueur b (m) : ")
                D = None
    
            else:  # rond
                D = self.lire_float("Diamètre D du poteau (m) : ")
                a = D
                b = D
    
            lo = self.lire_float("Longueur libre l₀ (m) : ")
    
            Nu = self.lire_float("Effort normal de calcul Nu (MN) : ")
    
            # =================================================
            # 2 - CONSTANTES DES MATÉRIAUX
            # =================================================
    
            Fe = self.Fe          # MPa
            Fc28 = self.Fc28      # MPa
            gamma_b = self.gamma_b
            gamma_s = self.gamma_s
            Es = 200000.0         # MPa
            enrobage_cm = 3.0     # enrobage nominal (BAEL : 3 cm en ambiance normale)
    
            # =================================================
            # 3 - SECTION RÉDUITE Br (BAEL B.8.4.1)
            # =================================================
            # Poteau rectangulaire : Br = (a − 0.02)(b − 0.02)  [m²]
            # Poteau circulaire    : Br = π(D − 0.02)² / 4      [m²]
            #
            # La section réduite est obtenue en déduisant 1 cm
            # d'épaisseur sur toute la périphérie (2 cm au total
            # pour le diamètre ou chaque dimension).
    
            if type_poteau == "rond":
                Br = math.pi * (D - 0.02) ** 2 / 4.0
            else:
                Br = (a - 0.02) * (b - 0.02)
    
            # =================================================
            # 4 - MOMENT D'INERTIE ET RAYON DE GIRATION
            # =================================================
            # Section rectangulaire :
            #   I_x = b·a³/12  (flambement autour de l'axe x)
            #   I_y = a·b³/12  (flambement autour de l'axe y)
            #
            # Section circulaire :
            #   I = π·D⁴/64
            #   i = D/4  (rayon de giration)
    
            a_cm = a * 100.0
            b_cm = b * 100.0
    
            if type_poteau == "rond":
                D_cm = D * 100.0
                I_cm4 = math.pi * D_cm ** 4 / 64.0
                B_cm2 = math.pi * D_cm ** 2 / 4.0
                i_cm = D_cm / 4.0                    # = √(I/B)
                lambda_expr = "λ = 4·lf / D"
                axe_flambement = "D (circulaire)"
            else:
                I_x_cm4 = b_cm * a_cm ** 3 / 12.0   # inertie / axe x
                I_y_cm4 = a_cm * b_cm ** 3 / 12.0   # inertie / axe y
                B_cm2 = a_cm * b_cm
    
                i_x_cm = math.sqrt(I_x_cm4 / B_cm2)
                i_y_cm = math.sqrt(I_y_cm4 / B_cm2)
    
                # On retient l'axe le plus défavorable (i le plus petit)
                if i_x_cm <= i_y_cm:
                    I_cm4 = I_x_cm4
                    i_cm = i_x_cm
                    lambda_expr = "λx = 2√3·lf / a"
                    axe_flambement = "x (a)"
                else:
                    I_cm4 = I_y_cm4
                    i_cm = i_y_cm
                    lambda_expr = "λy = 2√3·lf / b"
                    axe_flambement = "y (b)"
    
            # =================================================
            # 5 - LONGUEUR DE FLAMBEMENT (BAEL B.8.3.31)
            # =================================================
            # Cas encastrement + articulation : lf = 0.707·l₀
            # (poteau encastré dans un massif de fondation et
            # assemblé à des poutres de plancher de raideur ≥)
    
            lf = 0.707 * lo
            lf_cm = lf * 100.0
    
            # =================================================
            # 6 - ÉLANCEMENT MÉCANIQUE
            # =================================================
    
            lambda_meca = lf_cm / i_cm
    
            # =================================================
            # 7 - COEFFICIENT α (BAEL B.8.4.1)
            # =================================================
            # λ ≤ 50 : α = 0.85 / [1 + 0.2(λ/35)²]
            # 50 < λ ≤ 70 : α = 0.6(50/λ)²
            # λ > 70 : hors domaine de la compression centrée
    
            if lambda_meca <= 50:
                alpha = 0.85 / (1.0 + 0.2 * (lambda_meca / 35.0) ** 2)
                domaine = "compression centrée (λ ≤ 50)"
            elif lambda_meca <= 70:
                alpha = 0.6 * (50.0 / lambda_meca) ** 2
                domaine = "compression centrée (50 < λ ≤ 70)"
            else:
                alpha = 0.6 * (50.0 / 70.0) ** 2
                domaine = "⚠️ λ > 70 : hors domaine BAEL simplifié"
    
            # =================================================
            # 8 - ARMATURE LONGITUDINALE (BAEL B.8.4.1)
            # =================================================
            # Formule : Nu ≤ α [ Br·fc28/(0.9·γb) + As·fe/γs ]
            # → As ≥ [ Nu/α − Br·fc28/(0.9·γb) ] · γs/fe
            #
            # IMPORTANT : le dénominateur est (0.9·γb),
            # et non (γb − 0.9) comme dans l'ancien code.
    
            Fed = Fe / gamma_s
    
            terme_beton = Br * Fc28 / (0.9 * gamma_b)   # MN
    
            As_calc_m2 = (Nu / alpha - terme_beton) * gamma_s / Fe
            if As_calc_m2 < 0:
                As_calc_m2 = 0.0   # Le béton seul suffit
            As_calc_cm2 = As_calc_m2 * 10000.0
    
            # =================================================
            # 9 - ARMATURES MINIMALES (BAEL A.8.1.2.1)
            # =================================================
            # Amin = max(4 cm² par mètre de périmètre ; 0.2%·B)
            #
            # Pour un poteau circulaire, le périmètre est u = π·D.
            # Pour un poteau rectangulaire, u = 2(a + b).
    
            if type_poteau == "rond":
                u_perimetre = math.pi * D            # m
            else:
                u_perimetre = 2.0 * (a + b)          # m
    
            Amin_1 = 4.0 * u_perimetre               # cm² (4 cm²/m × m)
            Amin_2 = 0.002 * B_cm2                    # 0.2% de la section
    
            Amin_cm2 = max(Amin_1, Amin_2)
            As_retenue_cm2 = max(As_calc_cm2, Amin_cm2)
    
            # Vérification de la section maximale (BAEL : 5%·B)
            Amax_cm2 = 0.05 * B_cm2
            if As_retenue_cm2 > Amax_cm2:
                print(f"⚠️ As retenue ({As_retenue_cm2:.2f} cm²) > Amax ({Amax_cm2:.2f} cm²).")
                print("   → Augmenter la section du béton.")
    
            # =================================================
            # 10 - CHOIX AUTOMATIQUE DES BARRES LONGITUDINALES
            # =================================================
    
            diametres = [8, 10, 12, 14, 16, 20, 25, 32]
    
            # Nombre minimal de barres selon le type (BAEL A.8.1.3)
            if type_poteau == "rond":
                nb_min_barres = 6      # au moins 6 barres pour un poteau circulaire
            else:
                nb_min_barres = 4      # au moins 4 barres (une par angle)
    
            # Pour un poteau rectangulaire, on peut aussi imposer
            # un nombre pair pour une répartition symétrique.
            if type_poteau == "rectangulaire":
                nb_min_barres = max(nb_min_barres, 4)
    
            nombres = list(range(nb_min_barres, 33, 2))  # pas de 2
            if nb_min_barres % 2 != 0:
                nombres = list(range(nb_min_barres, 33))
    
            nb_barres = None
            diametre_long = None
            As_fournie_cm2 = None
    
            for n in nombres:
                for diam in diametres:
                    aire_une_barre = math.pi * diam ** 2 / 4.0 / 100.0  # cm²
                    aire_totale = n * aire_une_barre
                    if aire_totale >= As_retenue_cm2:
                        nb_barres = n
                        diametre_long = diam
                        As_fournie_cm2 = aire_totale
                        break
                if nb_barres is not None:
                    break
    
            if nb_barres is None:
                print("❌ Aucune combinaison standard ne satisfait As retenue.")
                print("   → Augmenter la section du béton.")
                self.pause()
                continue
    
            # =================================================
            # 11 - DIAMÈTRE DES ARMATURES TRANSVERSALES (BAEL A.8.1.3)
            # =================================================
            # φt ≥ φl / 3 (valeur normalisée la plus proche)
    
            phi_t_min = diametre_long / 3.0
            diametres_cadres = [6, 8, 10, 12]
            diametre_cadre = next(
                (d for d in diametres_cadres if d >= phi_t_min), 12
            )
    
            # =================================================
            # 12 - ESPACEMENT DES CADRES (BAEL A.8.1.2.1)
            # =================================================
            # Zone courante : st ≤ min(15φl ; 40 cm ; a+10 cm)
            # Zone nodale : st' ≤ min(10φl ; 15 cm)  [RPA 99 / BAEL]
    
            if type_poteau == "rond":
                petit_cote = D
            else:
                petit_cote = min(a, b)
    
            st_1 = 15.0 * diametre_long / 10.0    # cm (φl en mm → cm)
            st_2 = 40.0
            st_3 = petit_cote * 100.0 + 10.0      # cm
    
            st_cm = min(st_1, st_2, st_3)
            st_pratique = math.floor(st_cm)
    
            # Espacement en zone nodale (recouvrement)
            st_nodal = min(10.0 * diametre_long / 10.0, 15.0)
            st_nodal_pratique = math.floor(st_nodal)
    
            # =================================================
            # 13 - ADHÉRENCE ET LONGUEUR DE SCELLEMENT (BAEL A.6.1.2.1)
            # =================================================
            # ft28 = 0.6 + 0.06·Fc28 (limité à 3.3 MPa)
            # τsu = 0.6·ψs²·ft28  avec ψs = 1.5 pour HA
            # Ls = φ·fe / (4·τsu)
    
            ft28 = min(0.6 + 0.06 * Fc28, 3.3)
            psi_s = 1.5
            tau_su = 0.6 * psi_s ** 2 * ft28
    
            phi_mm = diametre_long
            Ls_cm = phi_mm * Fe / (4.0 * tau_su) / 10.0   # cm
    
            # =================================================
            # 14 - LONGUEUR DE RECOUVREMENT (BAEL A.8.1.2.1)
            # =================================================
            # Pour les aciers HA (FeE400) : Lr ≥ 40φ
            # (et non 0.6·Ls comme dans l'ancien code)
    
            Lr_min_cm = 40.0 * diametre_long / 10.0   # 40φ en cm
            Lr_retenue_cm = max(Lr_min_cm, Ls_cm)     # on retient le max
            Lr_retenue_cm = math.ceil(Lr_retenue_cm)
    
            # =================================================
            # AFFICHAGE COMPLET
            # =================================================
    
            self.clear_screen()
            self.banner()
    
            print("=" * 70)
            print(" " * 20 + "CALCUL COMPLET DU POTEAU")
            print("=" * 70)
    
            print()
            print("📌 DONNÉES DE DÉPART")
            print("-" * 70)
            print(f"Type    : Poteau {type_poteau}")
    
            if type_poteau == "rond":
                print(f"D       = {D:.3f} m")
            elif type_poteau == "carré":
                print(f"a = b   = {a:.3f} m")
            else:
                print(f"a       = {a:.3f} m")
                print(f"b       = {b:.3f} m")
    
            print(f"l₀      = {lo:.3f} m")
            print(f"Nu      = {Nu:.6f} MN")
    
            print()
            print("MATÉRIAUX")
            print("-" * 70)
            print(f"Fe   = {Fe:.2f} MPa")
            print(f"Fc28 = {Fc28:.2f} MPa")
            print(f"γb   = {gamma_b:.2f}")
            print(f"γs   = {gamma_s:.2f}")
            print(f"Enrobage = {enrobage_cm:.0f} cm")
    
            # -------------------------------------------------
            # SECTION RÉDUITE
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("1 - SECTION RÉDUITE Br (BAEL B.8.4.1)")
            print("=" * 70)
    
            if type_poteau == "rond":
                print()
                print("Formule : Br = π·(D − 0.02)² / 4")
                print(f"Br = π × ({D:.3f} − 0.02)² / 4")
            else:
                print()
                print("Formule : Br = (a − 0.02)(b − 0.02)")
                print(f"Br = ({a:.3f} − 0.02)({b:.3f} − 0.02)")
    
            print(f"✓ Br = {Br:.6f} m²")
    
            # -------------------------------------------------
            # INERTIE ET GIRATION
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("2 - MOMENT D'INERTIE ET RAYON DE GIRATION")
            print("=" * 70)
    
            if type_poteau == "rond":
                print()
                print("Section circulaire :")
                print("  I = π·D⁴ / 64")
                print(f"  I = π × {D_cm:.1f}⁴ / 64")
                print(f"  ✓ I = {I_cm4:.2f} cm⁴")
                print()
                print("  B = π·D² / 4")
                print(f"  B = π × {D_cm:.1f}² / 4 = {B_cm2:.2f} cm²")
                print()
                print("  i = D / 4")
                print(f"  ✓ i = {D_cm:.1f} / 4 = {i_cm:.3f} cm")
            else:
                print()
                print("Section rectangulaire :")
                print("  I_x = b·a³ / 12")
                print(f"  I_x = {b_cm:.1f} × {a_cm:.1f}³ / 12 = {I_x_cm4:.2f} cm⁴")
                print("  I_y = a·b³ / 12")
                print(f"  I_y = {a_cm:.1f} × {b_cm:.1f}³ / 12 = {I_y_cm4:.2f} cm⁴")
                print()
                print(f"  Axe de flambement retenu : {axe_flambement}")
                print(f"  ✓ I = {I_cm4:.2f} cm⁴")
                print(f"  B = {B_cm2:.2f} cm²")
                print(f"  ✓ i = √(I/B) = {i_cm:.3f} cm")
    
            # -------------------------------------------------
            # LONGUEUR DE FLAMBEMENT
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("3 - LONGUEUR DE FLAMBEMENT (BAEL B.8.3.31)")
            print("=" * 70)
    
            print()
            print("Cas : encastrement + articulation")
            print("Formule : lf = 0.707 × l₀")
            print(f"lf = 0.707 × {lo:.3f}")
            print(f"✓ lf = {lf:.3f} m = {lf_cm:.2f} cm")
    
            # -------------------------------------------------
            # ÉLANCEMENT
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("4 - ÉLANCEMENT MÉCANIQUE λ")
            print("=" * 70)
    
            print()
            print(f"Formule : {lambda_expr}")
            print(f"λ = {lf_cm:.2f} / {i_cm:.3f}")
            print(f"✓ λ = {lambda_meca:.3f}")
    
            if lambda_meca <= 50:
                print(f"✓ λ ≤ 50 : domaine de la compression centrée")
            elif lambda_meca <= 70:
                print(f"⚠️ 50 < λ ≤ 70 : compression centrée (domaine étendu)")
            else:
                print(f"⚠️ λ > 70 : hors domaine BAEL simplifié")
    
            # -------------------------------------------------
            # COEFFICIENT α
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("5 - COEFFICIENT α (BAEL B.8.4.1)")
            print("=" * 70)
    
            print()
            if lambda_meca <= 50:
                print("Formule : α = 0.85 / [1 + 0.2(λ/35)²]")
                print(f"α = 0.85 / [1 + 0.2 × ({lambda_meca:.3f}/35)²]")
            elif lambda_meca <= 70:
                print("Formule : α = 0.6 × (50/λ)²")
                print(f"α = 0.6 × (50/{lambda_meca:.3f})²")
            else:
                print("⚠️ λ > 70 : formule simplifiée non applicable.")
    
            print(f"✓ α = {alpha:.4f}")
    
            # -------------------------------------------------
            # ARMATURE LONGITUDINALE
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("6 - ARMATURE LONGITUDINALE (BAEL B.8.4.1)")
            print("=" * 70)
    
            print()
            print("Formule :")
            print()
            print("Nu ≤ α [ Br·fc28/(0.9·γb) + As·fe/γs ]")
            print()
            print("→ As ≥ [ Nu/α − Br·fc28/(0.9·γb) ] · γs/fe")
            print()
    
            print(f"Fed = Fe / γs = {Fe:.0f} / {gamma_s:.2f} = {Fed:.2f} MPa")
            print()
            print(f"Terme béton = Br·fc28/(0.9·γb)")
            print(f"= {Br:.6f} × {Fc28:.1f} / (0.9 × {gamma_b:.2f})")
            print(f"= {terme_beton:.6f} MN")
            print()
            print(f"Nu/α = {Nu:.6f} / {alpha:.4f} = {Nu/alpha:.6f} MN")
            print()
            print(f"As calculée = ({Nu/alpha:.6f} − {terme_beton:.6f}) × {gamma_s:.2f} / {Fe:.0f}")
            print(f"As calculée = {As_calc_m2:.8f} m²")
            print(f"✓ As calculée = {As_calc_cm2:.3f} cm²")
    
            # -------------------------------------------------
            # ARMATURE MINIMALE
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("7 - ARMATURE MINIMALE (BAEL A.8.1.2.1)")
            print("=" * 70)
    
            print()
            print("Formule : Amin = max(4u ; 0.2%·B)")
            print()
            print(f"Périmètre u :")
    
            if type_poteau == "rond":
                print(f"  u = π·D = π × {D:.3f} = {u_perimetre:.3f} m")
            else:
                print(f"  u = 2(a+b) = 2({a:.3f}+{b:.3f}) = {u_perimetre:.3f} m")
    
            print()
            print(f"Amin₁ = 4 × u = 4 × {u_perimetre:.3f} = {Amin_1:.3f} cm²")
            print(f"Amin₂ = 0.2% × B = 0.002 × {B_cm2:.2f} = {Amin_2:.3f} cm²")
            print()
            print(f"✓ Amin = max({Amin_1:.3f} ; {Amin_2:.3f}) = {Amin_cm2:.3f} cm²")
            print()
            print(f"As retenue = max({As_calc_cm2:.3f} ; {Amin_cm2:.3f})")
            print(f"✓ As retenue = {As_retenue_cm2:.3f} cm²")
            print()
            print(f"Amax = 5%·B = 0.05 × {B_cm2:.2f} = {Amax_cm2:.2f} cm²")
    
            # -------------------------------------------------
            # CHOIX DES BARRES
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("8 - CHOIX DES ARMATURES LONGITUDINALES")
            print("=" * 70)
    
            print()
            print(f"Nombre minimal de barres ({type_poteau}) : {nb_min_barres}")
            print(f"On cherche As ≥ {As_retenue_cm2:.3f} cm²")
            print()
            print(f"✓ Choix : {nb_barres}HA{diametre_long}")
            print(f"As fournie = {nb_barres} × π × {diametre_long}² / 4")
            print(f"As fournie = {As_fournie_cm2:.3f} cm²")
            print()
            print(f"Vérification : {As_fournie_cm2:.3f} ≥ {As_retenue_cm2:.3f} ✓")
    
            self.schema_armatures(nb_barres, diametre_long, f"SCHÉMA BA — POTEAU {type_poteau.upper()}")
    
            # -------------------------------------------------
            # ARMATURES TRANSVERSALES
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("9 - ARMATURES TRANSVERSALES (BAEL A.8.1.3)")
            print("=" * 70)
    
            print()
            print("Formule : φt ≥ φl / 3")
            print(f"φt ≥ {diametre_long} / 3 = {phi_t_min:.2f} mm")
            print(f"✓ On prend HA{diametre_cadre}")
    
            # -------------------------------------------------
            # ESPACEMENT
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("10 - ESPACEMENT DES CADRES (BAEL A.8.1.2.1)")
            print("=" * 70)
    
            print()
            print("Zone courante : st ≤ min(15φl ; 40 cm ; a+10 cm)")
            print()
            print(f"15φl = 15 × {diametre_long} / 10 = {st_1:.2f} cm")
            print(f"40 cm = {st_2:.2f} cm")
            print(f"a+10 = {petit_cote*100:.1f} + 10 = {st_3:.2f} cm")
            print()
            print(f"✓ st = min({st_1:.2f} ; {st_2:.2f} ; {st_3:.2f}) = {st_cm:.2f} cm")
            print(f"✓ On prend st = {st_pratique} cm")
    
            print()
            print("Zone nodale : st' ≤ min(10φl ; 15 cm)")
            print(f"10φl = 10 × {diametre_long} / 10 = {10.0*diametre_long/10.0:.2f} cm")
            print(f"✓ On prend st' = {st_nodal_pratique} cm")
    
            # -------------------------------------------------
            # ADHÉRENCE ET RECOUVREMENT
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("11 - ADHÉRENCE ET LONGUEUR DE RECOUVREMENT")
            print("=" * 70)
    
            print()
            print("ft28 = 0.6 + 0.06 × Fc28")
            print(f"ft28 = 0.6 + 0.06 × {Fc28:.1f} = {ft28:.3f} MPa")
            print()
            print("τsu = 0.6 × ψs² × ft28  (ψs = 1.5 pour HA)")
            print(f"τsu = 0.6 × 1.5² × {ft28:.3f} = {tau_su:.3f} MPa")
            print()
            print("Ls = φ·fe / (4·τsu)")
            print(f"Ls = {diametre_long} × {Fe:.0f} / (4 × {tau_su:.3f})")
            print(f"Ls = {Ls_cm:.2f} cm")
            print()
            print("Lr ≥ 40φ (pour HA FeE400)")
            print(f"Lr ≥ 40 × {diametre_long} / 10 = {Lr_min_cm:.1f} cm")
            print(f"✓ On prend Lr = {Lr_retenue_cm:.0f} cm")
    
            # -------------------------------------------------
            # RÉSULTAT FINAL
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print(" " * 23 + "RÉSULTAT FINAL")
            print("=" * 70)
    
            print()
            print(f"📐 SECTION DU POTEAU ({type_poteau})")
    
            if type_poteau == "rond":
                print(f"   D = {D:.3f} m")
            elif type_poteau == "carré":
                print(f"   a × b = {a:.3f} × {b:.3f} m")
            else:
                print(f"   a × b = {a:.3f} × {b:.3f} m")
    
            print()
            print("🏗️ FLAMBEMENT")
            print(f"   l₀ = {lo:.3f} m")
            print(f"   lf = {lf:.3f} m")
            print(f"   i = {i_cm:.3f} cm (axe {axe_flambement})")
            print(f"   λ = {lambda_meca:.3f}")
            print(f"   α = {alpha:.4f}")
            print(f"   Domaine : {domaine}")
    
            print()
            print("🔩 ARMATURES LONGITUDINALES")
            print(f"   As calculée = {As_calc_cm2:.3f} cm²")
            print(f"   Amin = {Amin_cm2:.3f} cm²")
            print(f"   As retenue = {As_retenue_cm2:.3f} cm²")
            print(f"   ✓ {nb_barres}HA{diametre_long}")
            print(f"   As fournie = {As_fournie_cm2:.3f} cm²")
    
            print()
            print("🔗 ARMATURES TRANSVERSALES")
            print(f"   ✓ Cadres HA{diametre_cadre}")
            print(f"   Zone courante : st = {st_pratique} cm")
            print(f"   Zone nodale : st' = {st_nodal_pratique} cm")
    
            print()
            print("📏 ANCRAGE / RECOUVREMENT")
            print(f"   Ls = {Ls_cm:.2f} cm")
            print(f"   Lr = {Lr_retenue_cm:.0f} cm")
    
            print()
            print("=" * 70)
            print("✓ CALCUL COMPLET DU POTEAU TERMINÉ")
            print("=" * 70)
    
            print()
    
            refaire = input("Nouveau calcul de poteau ? (O/N) : ").strip().lower()
            if refaire not in ["o", "oui"]:
                break
    
        # =========================================================
        # 5 - CALCUL DE LA SEMELLE ISOLÉE
        # =========================================================

    # =========================================================
    # 7 - CALCUL COMPLET DE L'ESCALIER
    # Référentiel : BAEL 91 révisé 99
    # Affichage progressif — pas de clear_screen
    # =========================================================
    
    def escalier(self):
        """Calcul complet d'un escalier en béton armé.
    
        Saisie par volée : Longueur et Hauteur uniquement.
        Affichage : formules conservées à l'écran (pas de clear).
        """
    
        LARGEUR_VOLÉE_DEFAUT = 1.20
        LARGEUR_PALIER_DEFAUT = 1.20
        LONGUEUR_PALIER_DEFAUT = 1.20
    
        # =====================================================
        # HELPERS D'AFFICHAGE
        # =====================================================
        def section_panel(numero, titre):
            if console is None:
                print(f"\n{'='*76}\n{numero} - {titre}\n{'='*76}")
                return
            console.print()
            console.print(
                Panel(
                    Text(f"{numero} - {titre}", style="bold bright_yellow"),
                    border_style="bright_cyan",
                    box=HEAVY,
                    padding=(0, 1),
                )
            )
    
        def formula_panel(titre, formule, application="", resultat=""):
            if console is None:
                print(f"[FORMULE] {titre}")
                print(f"  {formule}")
                if application:
                    print(f"  Application : {application}")
                if resultat:
                    print(f"  Résultat : {resultat}")
                return
            body = Text()
            body.append(f"{formule}\n", style="bold bright_white")
            if application:
                body.append(f"{application}\n", style="bright_cyan")
            if resultat:
                body.append(f"→ {resultat}", style="bold bright_green")
            console.print(
                Panel(
                    body,
                    title=f"📐 {titre}",
                    title_align="left",
                    border_style="bright_blue",
                    box=ROUNDED,
                    padding=(0, 1),
                )
            )
    
        def result_panel(titre, lignes):
            if console is None:
                print(titre)
                for line in lignes:
                    print(line)
                return
            body = Text()
            for i, line in enumerate(lignes):
                if i:
                    body.append("\n")
                body.append(str(line), style="bright_white")
            console.print(Panel(body, title=titre, border_style="bright_green",
                                box=DOUBLE, padding=(0, 1)))
    
        def check_line(label, ok, detail=""):
            if console is None:
                print(f"{'✓' if ok else '✗'} {label} {detail}")
                return
            style = "bold bright_green" if ok else "bold bright_red"
            symbol = "✓" if ok else "✗"
            t = Text()
            t.append(f"{symbol} {label}", style=style)
            if detail:
                t.append(f" — {detail}", style="bright_white")
            console.print(t)
    
        while True:
    
            # Seul clear_screen initial pour démarrer propre
            self.clear_screen()
            self.banner()
            result_panel("🪜 CALCUL COMPLET DE L'ESCALIER", [
                "Référentiel : BAEL 91 révisé 99",
                "Saisie : Longueur et Hauteur par volée",
                "Calcul automatique : marches, giron, ferraillage, flèche",
            ])
            print()
    
            # =====================================================
            # 1 - CONFIGURATION GÉNÉRALE
            # =====================================================
            section_panel("1", "CONFIGURATION GÉNÉRALE")
            H_total = self.lire_float("Hauteur totale H (m) : ")
    
            print()
            print("Nombre de volées :")
            print("  1 - Une volée")
            print("  2 - Deux volées")
            print("  3 - Trois volées")
            print("  4 - Autre")
            while True:
                choix_nv = input("👉 Votre choix (1-4) [1] : ").strip() or "1"
                if choix_nv == "1":
                    n_volées = 1; break
                if choix_nv == "2":
                    n_volées = 2; break
                if choix_nv == "3":
                    n_volées = 3; break
                if choix_nv == "4":
                    n_volées = int(self.lire_float("Nombre de volées : "))
                    break
                print("❌ Choix invalide.")
    
            largeur = LARGEUR_VOLÉE_DEFAUT
    
            # =====================================================
            # 2 - SAISIE DES VOLÉES (une par une)
            # =====================================================
            volées = []
            for i in range(n_volées):
                section_panel(f"2.{i+1}", f"VOLÉE {i+1} — Saisie")
                print()
                print("📌 Saisir uniquement la Longueur et la Hauteur :")
                print()
    
                a_v = self.lire_float(f"Longueur de la volée (m) : ")
                b_v = self.lire_float(f"Hauteur de la volée (m) : ")
    
                # Calculs automatiques
                b_cm = b_v * 100.0
                a_cm = a_v * 100.0
    
                n_th = b_cm / 17.0
                n_base = max(1, round(n_th))
                n_candidats = sorted(set([n_base - 1, n_base, n_base + 1]))
                n_retenu = None
                for n in n_candidats:
                    if n < 1:
                        continue
                    h_t = b_cm / n
                    if 16.5 <= h_t <= 17.5:
                        n_retenu = n
                        break
                if n_retenu is None:
                    n_retenu = min(
                        [n for n in n_candidats if n >= 1],
                        key=lambda n: abs(b_cm / n - 17.0)
                    )
    
                n_marches = max(1, n_retenu)
                h_marche = b_cm / n_marches
                giron = a_cm / (n_marches - 1) if n_marches > 1 else a_cm
                blondel = giron + 2.0 * h_marche
    
                L_exact = math.sqrt(a_v ** 2 + b_v ** 2)
                L_v = round(L_exact, 2)
    
                if L_v > 0:
                    sin_alpha = b_v / L_v
                    alpha = math.degrees(math.asin(max(-1.0, min(1.0, sin_alpha))))
                    alpha = round(alpha)
                else:
                    alpha = 0
    
                # -------------------------------------------------
                # FORMULES DÉTAILLÉES
                # -------------------------------------------------
                print()
                print(f"═══ FORMULES — VOLÉE {i+1} ═══")
    
                formula_panel(
                    "Nombre de marches",
                    "n ≈ Hauteur / 17 cm",
                    f"n ≈ {b_cm:.1f} / 17 = {n_th:.2f}",
                    f"n = {n_marches} marches"
                )
    
                formula_panel(
                    "Hauteur de marche",
                    "h = Hauteur / n",
                    f"h = {b_cm:.1f} / {n_marches}",
                    f"h = {h_marche:.2f} cm"
                )
    
                formula_panel(
                    "Giron",
                    "g = Longueur / (n − 1)",
                    f"g = {a_cm:.1f} / ({n_marches} − 1) = {a_cm:.1f} / {n_marches - 1}",
                    f"g = {giron:.2f} cm"
                )
    
                formula_panel(
                    "Loi de Blondel",
                    "g + 2h ∈ [59 ; 66] cm",
                    f"g + 2h = {giron:.2f} + 2 × {h_marche:.2f} = {blondel:.2f} cm",
                    f"Blondel = {blondel:.2f} cm"
                )
    
                formula_panel(
                    "Longueur inclinée",
                    "L = √(a² + b²)",
                    f"L = √({a_v:.3f}² + {b_v:.3f}²)",
                    f"L = {L_v:.3f} m"
                )
    
                formula_panel(
                    "Inclinaison",
                    "α = arcsin(b / L)",
                    f"α = arcsin({b_v:.3f} / {L_v:.3f})",
                    f"α = {alpha}°"
                )
    
                # Vérifications
                print()
                print(f"═══ VÉRIFICATIONS — VOLÉE {i+1} ═══")
                check_line(
                    f"Hauteur de marche h ∈ [16.5 ; 17.5] cm",
                    16.5 <= h_marche <= 17.5,
                    f"h = {h_marche:.2f} cm"
                )
                check_line(
                    f"Giron g ∈ [27 ; 32] cm",
                    27.0 <= giron <= 32.0,
                    f"g = {giron:.2f} cm"
                )
                check_line(
                    f"Loi de Blondel 59 ≤ g+2h ≤ 66 cm",
                    59.0 <= blondel <= 66.0,
                    f"g+2h = {blondel:.2f} cm"
                )
                check_line(
                    f"Inclinaison α ∈ [15° ; 45°]",
                    15.0 <= alpha <= 45.0,
                    f"α = {alpha}°"
                )
    
                volées.append({
                    "num": i + 1,
                    "a": a_v, "b": b_v, "H": b_v,
                    "h_marche": h_marche,
                    "n_marches": n_marches,
                    "giron": giron,
                    "blondel": blondel,
                    "L": L_v,
                    "alpha": alpha,
                    "largeur": largeur,
                })
    
            # =====================================================
            # 3 - PALIERS INTERMÉDIAIRES
            # =====================================================
            paliers = []
            for i in range(n_volées - 1):
                paliers.append({
                    "num": i + 1,
                    "L": LONGUEUR_PALIER_DEFAUT,
                    "largeur": LARGEUR_PALIER_DEFAUT,
                    "epaisseur": None,
                })
    
            # =====================================================
            # 4 - ÉPAISSEURS DE PAILLASSE
            # =====================================================
            section_panel("3", "ÉPAISSEURS DE PAILLASSE")
            formula_panel(
                "Épaisseur de la paillasse",
                "e = max(L/30 ; 10 cm)",
                "L = longueur inclinée de la volée",
                ""
            )
    
            for v in volées:
                e_calc = v["L"] / 30.0
                e_v = max(e_calc, 0.10)
                v["e_paillasse"] = e_v
                formula_panel(
                    f"Volée {v['num']}",
                    f"e = max({v['L']:.3f}/30 ; 0.10)",
                    f"e = max({e_calc:.3f} ; 0.10)",
                    f"e = {e_v:.3f} m = {e_v*100:.1f} cm"
                )
    
            for i, p in enumerate(paliers):
                e_p = max(volées[i]["e_paillasse"], volées[i+1]["e_paillasse"])
                p["epaisseur"] = e_p
                formula_panel(
                    f"Palier {p['num']}",
                    "e = max(e_volée gauche ; e_volée droite)",
                    f"e = max({volées[i]['e_paillasse']*100:.1f} ; "
                    f"{volées[i+1]['e_paillasse']*100:.1f})",
                    f"e = {e_p*100:.1f} cm"
                )
    
            self.pause()
    
            # =====================================================
            # 5 - MATÉRIAUX ET CHARGES
            # =====================================================
            Fc28 = self.Fc28
            Fe = self.Fe
            gamma_b = self.gamma_b
            gamma_s = self.gamma_s
            Fed = Fe / gamma_s
            ft28 = min(0.6 + 0.06 * Fc28, 3.3)
    
            G_enduit = 0.44
            Q_exploitation = 2.5
    
            elements = []
    
            section_panel("4", "CALCUL DES CHARGES")
    
            for v in volées:
                e = v["e_paillasse"]
                g = v["giron"]
                h = v["h_marche"]
                alpha_rad = math.radians(v["alpha"])
                cos_a = math.cos(alpha_rad) if v["alpha"] != 0 else 1.0
    
                print()
                print(f"═══ VOLÉE {v['num']} — CHARGES ═══")
    
                G_dalle = e * 25.0
                formula_panel(
                    "Poids propre dalle",
                    "G_dalle = e × 25",
                    f"G_dalle = {e:.3f} × 25",
                    f"G_dalle = {G_dalle:.3f} kN/m²"
                )
    
                G_marches = (g / 100.0 * h / 100.0 / 2.0) * 25.0
                formula_panel(
                    "Poids propre marches",
                    "G_marches = (g × h / 2) × 25",
                    f"G_marches = ({g:.2f}/100 × {h:.2f}/100 / 2) × 25",
                    f"G_marches = {G_marches:.3f} kN/m²"
                )
    
                G_rev_h = 3.0 * (h / 100.0) * 0.6
                G_rev_g = 3.0 * (g / 100.0) * 1.0 * 0.6
    
                formula_panel(
                    "Revêtement marches + contremarches",
                    "G_rev = 3×h×0.6 + 3×g×0.6",
                    f"G_rev = 3×{h/100:.3f}×0.6 + 3×{g/100:.3f}×0.6",
                    f"G_rev = {G_rev_h + G_rev_g:.3f} kN/m²"
                )
    
                formula_panel(
                    "Enduit",
                    "G_enduit = 0.44 kN/m²",
                    "",
                    f"G_enduit = {G_enduit:.3f} kN/m²"
                )
    
                G_surf = G_dalle + G_marches + G_enduit + G_rev_h + G_rev_g
                Q_surf = Q_exploitation
    
                formula_panel(
                    "Charge permanente totale",
                    "G = Σ des charges permanentes",
                    f"G = {G_dalle:.3f} + {G_marches:.3f} + {G_enduit:.3f} + {G_rev_h + G_rev_g:.3f}",
                    f"G = {G_surf:.3f} kN/m²"
                )
    
                formula_panel(
                    "Charge d'exploitation",
                    "Q = 2.50 kN/m²",
                    "",
                    f"Q = {Q_surf:.3f} kN/m²"
                )
    
                Ge = G_surf / cos_a
                Qe = Q_surf / cos_a
    
                formula_panel(
                    "Charges inclinées",
                    "Ge = G / cos α ; Qe = Q / cos α",
                    f"cos α = cos({v['alpha']}°) = {cos_a:.4f}",
                    f"Ge = {Ge:.3f} ; Qe = {Qe:.3f} kN/m²"
                )
    
                Pu = (1.35 * Ge + 1.50 * Qe) / 1000.0
                Pser = (Ge + Qe) / 1000.0
    
                formula_panel(
                    "Combinaison ELU",
                    "Pu = 1.35 Ge + 1.50 Qe",
                    f"Pu = 1.35 × {Ge:.3f} + 1.50 × {Qe:.3f}",
                    f"Pu = {Pu*1000:.3f} kN/m"
                )
    
                formula_panel(
                    "Combinaison ELS",
                    "Pser = Ge + Qe",
                    f"Pser = {Ge:.3f} + {Qe:.3f}",
                    f"Pser = {Pser*1000:.3f} kN/m"
                )
    
                elements.append({
                    "type": "volée",
                    "num": v["num"],
                    "L": v["L"],
                    "e": e,
                    "Pu": Pu, "Pser": Pser,
                    "G": G_surf, "Q": Q_surf,
                    "alpha": v["alpha"],
                    "h_marche": h, "giron": g,
                    "cos_a": cos_a,
                })
    
            # Paliers
            for p in paliers:
                e = p["epaisseur"]
                G_surf = e * 25.0 + G_enduit + 0.60 + 0.40
                Q_surf = Q_exploitation
    
                print()
                print(f"═══ PALIER {p['num']} — CHARGES ═══")
                formula_panel(
                    "Charge permanente",
                    "G = e×25 + enduit + carrelage + cloisons",
                    f"G = {e:.3f}×25 + 0.44 + 0.60 + 0.40",
                    f"G = {G_surf:.3f} kN/m²"
                )
                Pu = (1.35 * G_surf + 1.50 * Q_surf) / 1000.0
                Pser = (G_surf + Q_surf) / 1000.0
                formula_panel(
                    "Combinaison ELU",
                    "Pu = 1.35 G + 1.50 Q",
                    f"Pu = 1.35 × {G_surf:.3f} + 1.50 × {Q_surf:.3f}",
                    f"Pu = {Pu*1000:.3f} kN/m"
                )
                formula_panel(
                    "Combinaison ELS",
                    "Pser = G + Q",
                    f"Pser = {G_surf:.3f} + {Q_surf:.3f}",
                    f"Pser = {Pser*1000:.3f} kN/m"
                )
    
                elements.append({
                    "type": "palier",
                    "num": p["num"],
                    "L": p["L"],
                    "e": e,
                    "Pu": Pu, "Pser": Pser,
                    "G": G_surf, "Q": Q_surf,
                    "alpha": 0,
                    "h_marche": 0, "giron": 0,
                    "cos_a": 1.0,
                })
    
            self.pause()
    
            # =====================================================
            # 6 - SOLLICITATIONS
            # =====================================================
            section_panel("5", "SOLLICITATIONS — MOMENTS ET EFFORTS TRANCHANTS")
    
            formula_panel(
                "Moment isostatique de référence",
                "M0 = Pu × L² / 8",
                "Pour chaque travée",
                ""
            )
    
            for el in elements:
                el["M0"] = el["Pu"] * el["L"] ** 2 / 8.0
                el["V0"] = el["Pu"] * el["L"] / 2.0
                formula_panel(
                    f"{el['type'].capitalize()} {el['num']}",
                    f"M0 = {el['Pu']*1000:.3f} × {el['L']:.3f}² / 8",
                    "",
                    f"M0 = {el['M0']*1000:.3f} kN.m"
                )
    
            n_travées = len(elements)
            M_appuis = [0.0] * (n_travées + 1)
    
            if n_travées == 1:
                M_appuis[0] = 0.0
                M_appuis[1] = 0.0
            else:
                formula_panel(
                    "Moments sur appuis",
                    "M_appui = -k × min(M0 gauche ; M0 droit)",
                    "k = 0.6 (2 travées) ; 0.5 (voisin rive) ; 0.4 (intermédiaire)",
                    ""
                )
                for k in range(1, n_travées):
                    el_l = elements[k - 1]
                    el_r = elements[k]
                    if n_travées == 2:
                        coeff_appui = 0.5
                    else:
                        if k == 1 or k == n_travées - 1:
                            coeff_appui = 0.5
                        else:
                            coeff_appui = 0.4
                    M_appuis[k] = -coeff_appui * min(el_l["M0"], el_r["M0"])
                    formula_panel(
                        f"Appui {k}",
                        f"M_appui{k} = -{coeff_appui} × min({el_l['M0']*1000:.3f} ; "
                        f"{el_r['M0']*1000:.3f})",
                        "",
                        f"M_appui{k} = {M_appuis[k]*1000:.3f} kN.m"
                    )
    
            formula_panel(
                "Moments en travée",
                "Mt = k_Mt × M0 − (Mw + Me)/2",
                "k_Mt = 0.85 (travée de rive) ; 0.75 (travée intermédiaire)",
                ""
            )
            for i, el in enumerate(elements):
                Mw = M_appuis[i]
                Me = M_appuis[i + 1]
                M0 = el["M0"]
    
                if n_travées == 1:
                    el["Mt"] = M0
                    el["Mu_appui_max"] = 0.0
                    el["M_appui_gauche"] = 0.0
                    el["M_appui_droit"] = 0.0
                    formula_panel(
                        f"Travée {el['num']} (isostatique)",
                        f"Mt = M0 = {M0*1000:.3f} kN.m",
                        "",
                        f"Mt = {el['Mt']*1000:.3f} kN.m"
                    )
                else:
                    if i == 0 or i == n_travées - 1:
                        coeff_Mt = 0.85
                        pos = "travée de rive"
                    else:
                        coeff_Mt = 0.75
                        pos = "travée intermédiaire"
    
                    Mt = coeff_Mt * M0 - (Mw + Me) / 2.0
                    el["Mt"] = max(Mt, 0.0)
                    el["M_appui_gauche"] = Mw
                    el["M_appui_droit"] = Me
    
                    Ma_g = abs(Mw)
                    Ma_d = abs(Me)
                    if i == 0:
                        Ma_g = max(Ma_g, 0.30 * M0)
                    if i == n_travées - 1:
                        Ma_d = max(Ma_d, 0.30 * M0)
                    el["Mu_appui_max"] = max(Ma_g, Ma_d)
    
                    formula_panel(
                        f"Travée {el['num']} ({pos})",
                        f"Mt = {coeff_Mt} × {M0*1000:.3f} − "
                        f"({Mw*1000:.3f} + {Me*1000:.3f})/2",
                        "",
                        f"Mt = {el['Mt']*1000:.3f} kN.m"
                    )
    
            self.pause()
    
            # =====================================================
            # 7 - DIMENSIONNEMENT EN FLEXION
            # =====================================================
            Fbu = 0.85 * Fc28 / gamma_b
            bo = 1.00
            diametres = [8, 10, 12, 14, 16, 20, 25, 32]
    
            section_panel("6", "DIMENSIONNEMENT EN FLEXION (BAEL 91 A.4.3)")
    
            formula_panel(
                "Contrainte du béton",
                "Fbu = 0.85 × Fc28 / γb",
                f"Fbu = 0.85 × {Fc28:.1f} / {gamma_b:.2f}",
                f"Fbu = {Fbu:.3f} MPa"
            )
            formula_panel(
                "Contrainte de l'acier",
                "σs = Fe / γs",
                f"σs = {Fe:.0f} / {gamma_s:.2f}",
                f"σs = {Fed:.3f} MPa"
            )
            formula_panel(
                "Résistance traction béton",
                "ft28 = min(0.6 + 0.06×Fc28 ; 3.3)",
                f"ft28 = min(0.6 + 0.06×{Fc28:.1f} ; 3.3)",
                f"ft28 = {ft28:.3f} MPa"
            )
    
            def dimensionner_flexion(Mu_MNm, e_m):
                d = 0.90 * e_m
                if d <= 0:
                    return None
                Mlu = Mu_MNm / (bo * d ** 2 * Fbu)
                if Mlu >= 0.5:
                    return None
                alpha_zb = 1.25 * (1.0 - math.sqrt(max(0.0, 1.0 - 2.0 * Mlu)))
                Zb = d * (1.0 - 0.40 * alpha_zb)
                As_calc_cm2 = Mu_MNm / (Zb * Fed) * 10000.0
                Amin_cm2 = 0.23 * 100.0 * (d * 100.0) * ft28 / Fe
                As_retenue_cm2 = max(As_calc_cm2, Amin_cm2)
    
                choix = None
                for diam in diametres:
                    aire_barre = math.pi * diam ** 2 / 4.0 / 100.0
                    for n in range(4, 33):
                        As_f = n * aire_barre
                        if As_f >= As_retenue_cm2:
                            if choix is None or As_f < choix[0]:
                                choix = (As_f, n, diam)
                            break
    
                return {
                    "d": d, "Mlu": Mlu, "alpha_zb": alpha_zb, "Zb": Zb,
                    "As_calc_cm2": As_calc_cm2, "Amin_cm2": Amin_cm2,
                    "As_retenue_cm2": As_retenue_cm2, "choix": choix,
                }
    
            for el in elements:
                e = el["e"]
    
                if el["Mt"] > 0:
                    r = dimensionner_flexion(el["Mt"], e)
                    el["travée"] = r
                    if r:
                        print()
                        print(f"═══ FLEXION TRAVÉE — {el['type'].capitalize()} {el['num']} ═══")
                        formula_panel(
                            "Hauteur utile",
                            "d = 0.90 × e",
                            f"d = 0.90 × {e*100:.1f} cm",
                            f"d = {r['d']*100:.2f} cm"
                        )
                        formula_panel(
                            "Moment réduit",
                            "μlu = Mu / (b × d² × Fbu)",
                            f"μlu = {el['Mt']*1000:.3f} / "
                            f"(1.00 × {r['d']:.3f}² × {Fbu:.3f})",
                            f"μlu = {r['Mlu']:.4f}"
                        )
                        formula_panel(
                            "Position axe neutre",
                            "α = 1.25 × (1 − √(1 − 2 μlu))",
                            f"α = 1.25 × (1 − √(1 − 2 × {r['Mlu']:.4f}))",
                            f"α = {r['alpha_zb']:.4f}"
                        )
                        formula_panel(
                            "Bras de levier",
                            "Zb = d × (1 − 0.4 α)",
                            f"Zb = {r['d']*100:.2f} × (1 − 0.4 × {r['alpha_zb']:.4f})",
                            f"Zb = {r['Zb']*100:.2f} cm"
                        )
                        formula_panel(
                            "Section d'acier calculée",
                            "As = Mt / (Zb × σs)",
                            f"As = {el['Mt']*1000:.3f} / ({r['Zb']*100:.2f} × {Fed:.2f})",
                            f"As = {r['As_calc_cm2']:.3f} cm²"
                        )
                        formula_panel(
                            "Section minimale (non-fragilité)",
                            "Amin = 0.23 × b × d × ft28 / fe",
                            f"Amin = 0.23 × 100 × {r['d']*100:.2f} × {ft28:.3f} / {Fe:.0f}",
                            f"Amin = {r['Amin_cm2']:.3f} cm²"
                        )
                        if r["choix"]:
                            As_f, n, diam = r["choix"]
                            formula_panel(
                                "Choix des armatures",
                                f"As fournie ≥ As retenue",
                                f"{n} × π × {diam}² / 4 = {As_f:.3f} cm² ≥ "
                                f"{r['As_retenue_cm2']:.3f} cm²",
                                f"✓ {n} HA{diam} = {As_f:.3f} cm²"
                            )
                else:
                    el["travée"] = None
    
                if el["Mu_appui_max"] > 0:
                    r = dimensionner_flexion(el["Mu_appui_max"], e)
                    el["appui"] = r
                    if r:
                        print()
                        print(f"═══ FLEXION APPUI — {el['type'].capitalize()} {el['num']} ═══")
                        formula_panel(
                            "Moment appui max",
                            "Mu = max(|Mw| ; |Me| ; 0.30 M0)",
                            "",
                            f"Mu = {el['Mu_appui_max']*1000:.3f} kN.m"
                        )
                        formula_panel(
                            "Section d'acier calculée",
                            "As = Mu / (Zb × σs)",
                            f"As = {el['Mu_appui_max']*1000:.3f} / "
                            f"({r['Zb']*100:.2f} × {Fed:.2f})",
                            f"As = {r['As_calc_cm2']:.3f} cm²"
                        )
                        if r["choix"]:
                            As_f, n, diam = r["choix"]
                            formula_panel(
                                "Choix des armatures",
                                "As fournie ≥ As retenue",
                                f"{n} × π × {diam}² / 4 = {As_f:.3f} cm²",
                                f"✓ {n} HA{diam} = {As_f:.3f} cm²"
                            )
                else:
                    el["appui"] = None
    
            self.pause()
    
            # =====================================================
            # 8 - EFFORT TRANCHANT
            # =====================================================
            section_panel("7", "VÉRIFICATION DE L'EFFORT TRANCHANT (BAEL 91 A.5.2)")
    
            tau_lim = min(0.20 * Fc28 / gamma_b, 5.0)
            formula_panel(
                "Contrainte tangente limite",
                "τu,lim = min(0.20 × Fc28 / γb ; 5 MPa)",
                f"τu,lim = min(0.20 × {Fc28:.1f} / {gamma_b:.2f} ; 5)",
                f"τu,lim = {tau_lim:.3f} MPa"
            )
    
            for el in elements:
                e = el["e"]
                if n_travées == 1:
                    V_max = el["V0"]
                else:
                    V_g = abs(el["V0"] + (el["M_appui_droit"] - el["M_appui_gauche"]) / el["L"])
                    V_d = abs(el["V0"] - (el["M_appui_droit"] - el["M_appui_gauche"]) / el["L"])
                    V_max = max(V_g, V_d)
                tau_u = V_max * 1000.0 / (100.0 * e * 100.0)
                el["V_max"] = V_max
                el["tau_u"] = tau_u
                el["tau_ok"] = tau_u <= tau_lim
    
                print()
                print(f"═══ EFFORT TRANCHANT — {el['type'].capitalize()} {el['num']} ═══")
                formula_panel(
                    "Effort tranchant maximal",
                    "V_max = max(|Vg| ; |Vd|)",
                    "",
                    f"V_max = {V_max*1000:.3f} kN"
                )
                formula_panel(
                    "Contrainte tangente",
                    "τu = V_max / (b × d)",
                    f"τu = {V_max*1000:.3f} / (100 × {e*100:.1f})",
                    f"τu = {tau_u:.4f} MPa"
                )
                check_line(
                    f"τu ≤ τu,lim",
                    tau_u <= tau_lim,
                    f"{tau_u:.4f} ≤ {tau_lim:.3f} MPa"
                )
    
            self.pause()
    
            # =====================================================
            # 9 - FLÈCHE
            # =====================================================
            section_panel("8", "VÉRIFICATION DE LA FLÈCHE (BAEL 91 B.6.5)")
    
            E_i = 11000.0 * (Fc28 ** (1.0 / 3.0))
            n_eq = 15.0
    
            formula_panel(
                "Module de Young instantané",
                "E_i = 11000 × (fc28)^(1/3)",
                f"E_i = 11000 × ({Fc28:.1f})^(1/3)",
                f"E_i = {E_i:.1f} MPa"
            )
            formula_panel(
                "Module de Young différé",
                "E_v = E_i / 3",
                f"E_v = {E_i:.1f} / 3",
                f"E_v = {E_i/3:.1f} MPa"
            )
    
            for el in elements:
                e = el["e"]
                b_cm = 100.0
                d_cm = 0.90 * e * 100.0
    
                if el["travée"] and el["travée"]["choix"]:
                    As_f = el["travée"]["choix"][0]
                else:
                    As_f = 1.0
    
                A_eq = b_cm / 2.0
                B_eq = n_eq * As_f
                C_eq = -n_eq * As_f * d_cm
                delta_disc = B_eq ** 2 - 4 * A_eq * C_eq
    
                if delta_disc < 0:
                    el["f_tot"] = None
                    continue
    
                y_cm = (-B_eq + math.sqrt(delta_disc)) / (2.0 * A_eq)
                I_f_cm4 = b_cm * y_cm ** 3 / 3.0 + n_eq * As_f * (d_cm - y_cm) ** 2
                I_f_m4 = I_f_cm4 * 1e-8
    
                M_ser_Nm = el["Pser"] * el["L"] ** 2 / 8.0 * 1e6
                E_i_Pa = E_i * 1e6
    
                f_i_mm = (5.0 * M_ser_Nm * el["L"] ** 2) / (48.0 * E_i_Pa * I_f_m4) * 1000.0
                f_v_mm = f_i_mm * 0.5
                f_tot = f_i_mm + f_v_mm
                f_adm = (el["L"] * 1000.0) / 500.0
    
                el["f_tot"] = f_tot
                el["f_adm"] = f_adm
                el["fleche_ok"] = f_tot <= f_adm
    
                print()
                print(f"═══ FLÈCHE — {el['type'].capitalize()} {el['num']} ═══")
                formula_panel(
                    "Position axe neutre fissurée",
                    "b·y²/2 + n·As·(y − d) = 0",
                    f"100·y²/2 + 15×{As_f:.3f}·(y − {d_cm:.1f}) = 0",
                    f"y = {y_cm:.2f} cm"
                )
                formula_panel(
                    "Moment d'inertie fissuré",
                    "I_f = b·y³/3 + n·As·(d − y)²",
                    f"I_f = 100×{y_cm:.2f}³/3 + 15×{As_f:.3f}×({d_cm:.1f}−{y_cm:.2f})²",
                    f"I_f = {I_f_cm4:.3e} cm⁴"
                )
                formula_panel(
                    "Flèche instantanée",
                    "f_i = 5·Mser·L² / (48·E_i·I_f)",
                    f"f_i = 5×{M_ser_Nm:.0f}×{el['L']:.3f}² / "
                    f"(48×{E_i_Pa:.2e}×{I_f_m4:.3e})",
                    f"f_i = {f_i_mm:.3f} mm"
                )
                formula_panel(
                    "Flèche différée",
                    "f_v = 0.5 × f_i",
                    f"f_v = 0.5 × {f_i_mm:.3f}",
                    f"f_v = {f_v_mm:.3f} mm"
                )
                formula_panel(
                    "Flèche totale",
                    "f_tot = f_i + f_v",
                    f"f_tot = {f_i_mm:.3f} + {f_v_mm:.3f}",
                    f"f_tot = {f_tot:.3f} mm"
                )
                formula_panel(
                    "Flèche admissible",
                    "f_adm = L / 500",
                    f"f_adm = {el['L']*1000:.0f} / 500",
                    f"f_adm = {f_adm:.3f} mm"
                )
                check_line(
                    "Flèche totale ≤ Flèche admissible",
                    f_tot <= f_adm,
                    f"{f_tot:.3f} ≤ {f_adm:.3f} mm"
                )
    
            self.pause()
    
            # =====================================================
            # 10 - ARMATURES DE RÉPARTITION
            # =====================================================
            section_panel("9", "ARMATURES DE RÉPARTITION (BAEL 91 E.8.2.41)")
    
            formula_panel(
                "Section de répartition",
                "Ar ≥ As / 4",
                "As = section d'acier principale",
                ""
            )
    
            for el in elements:
                if el["travée"] and el["travée"]["choix"]:
                    As_princ = el["travée"]["choix"][0]
                    Ar_min = max(As_princ / 4.0, 0.84)
                    choix_rep = None
                    for diam in diametres:
                        aire_barre = math.pi * diam ** 2 / 4.0 / 100.0
                        for n in range(2, 33):
                            As_r = n * aire_barre
                            if As_r >= Ar_min:
                                if choix_rep is None or As_r < choix_rep[0]:
                                    choix_rep = (As_r, n, diam)
                                break
                    el["Ar"] = choix_rep
                    if choix_rep:
                        As_f, n, diam = choix_rep
                        formula_panel(
                            f"{el['type'].capitalize()} {el['num']}",
                            f"Ar ≥ {As_princ:.3f} / 4 = {Ar_min:.3f} cm²",
                            f"Choix : {n}HA{diam} = {As_f:.3f} cm²",
                            f"✓ {n} HA{diam} = {As_f:.3f} cm²"
                        )
    
            # =====================================================
            # 11 - RÉSUMÉ FINAL (sans clear_screen)
            # =====================================================
            print()
            print()
            result_panel("🎯 RÉSUMÉ FINAL DE L'ESCALIER", [
                f"Hauteur totale H = {H_total:.3f} m",
                f"Nombre de volées = {n_volées}",
                f"Largeur volée = {largeur:.2f} m",
            ])
    
            for v in volées:
                result_panel(f"📐 VOLÉE {v['num']}", [
                    f"Longueur a            : {v['a']:.3f} m",
                    f"Hauteur b             : {v['b']:.3f} m",
                    f"Nombre de marches     : {v['n_marches']}",
                    f"Hauteur de marche h   : {v['h_marche']:.2f} cm",
                    f"Giron g               : {v['giron']:.2f} cm",
                    f"Loi de Blondel        : {v['blondel']:.2f} cm",
                    f"Longueur inclinée L   : {v['L']:.3f} m",
                    f"Inclinaison α         : {v['alpha']:.0f}°",
                    f"Épaisseur paillasse e : {v['e_paillasse']*100:.1f} cm",
                ])
    
            for el in elements:
                lignes = [
                    f"L = {el['L']:.3f} m ; e = {el['e']*100:.1f} cm",
                    f"Pu = {el['Pu']*1000:.3f} kN/m",
                    f"Pser = {el['Pser']*1000:.3f} kN/m",
                    f"M0 = {el['M0']*1000:.3f} kN.m",
                    f"Mt (travée) = {el['Mt']*1000:.3f} kN.m",
                    f"M appui max = {el['Mu_appui_max']*1000:.3f} kN.m",
                    f"V_max = {el['V_max']*1000:.3f} kN",
                ]
                result_panel(f"📊 {el['type'].capitalize()} {el['num']}", lignes)
    
            for el in elements:
                lignes = []
                if el["travée"] and el["travée"]["choix"]:
                    As_f, n, diam = el["travée"]["choix"]
                    lignes.append(f"Travée : {n}HA{diam} = {As_f:.3f} cm²")
                if el["appui"] and el["appui"]["choix"] and el["Mu_appui_max"] > 0:
                    As_f, n, diam = el["appui"]["choix"]
                    lignes.append(f"Appui  : {n}HA{diam} = {As_f:.3f} cm²")
                if "Ar" in el and el["Ar"]:
                    As_f, n, diam = el["Ar"]
                    lignes.append(f"Répartition : {n}HA{diam} = {As_f:.3f} cm²")
                if lignes:
                    result_panel(f"🔩 FERRAILLAGE — {el['type'].capitalize()} {el['num']}",
                                 lignes)
    
            # Vérifications
            print()
            print("=" * 70)
            print(" " * 22 + "VÉRIFICATIONS RÉCAPITULATIVES")
            print("=" * 70)
            print()
            print(f"τu,lim = {tau_lim:.3f} MPa")
            for el in elements:
                print(f"\n▶ {el['type'].capitalize()} {el['num']}")
                check_line(
                    "Effort tranchant τu ≤ τu,lim",
                    el["tau_ok"],
                    f"{el['tau_u']:.4f} ≤ {tau_lim:.3f} MPa"
                )
                if el.get("f_tot") is not None:
                    check_line(
                        "Flèche f_tot ≤ f_adm",
                        el["fleche_ok"],
                        f"{el['f_tot']:.3f} ≤ {el['f_adm']:.3f} mm"
                    )
    
            print()
            print("=" * 70)
            print(" " * 15 + "COEFFICIENTS FORFAITAIRES (BAEL 91 E.1)")
            print("=" * 70)
            print()
            print("• Moment en travée de rive        : 0.85 M0")
            print("• Moment en travée intermédiaire  : 0.75 M0")
            print("• Moment sur appui de rive        : 0.30 M0")
            print("• Moment sur appui intermédiaire  : 0.50 M0")
    
            print()
            print("=" * 70)
            print("✓ CALCUL COMPLET DE L'ESCALIER TERMINÉ")
            print("=" * 70)
    
            refaire = input("\nNouveau calcul d'escalier ? (O/N) : ").strip().lower()
            if refaire not in ["o", "oui"]:
                break
    
    def semelle_isolee(self):
        """Calcul complet d'une semelle isolée sous charge centrée.
    
        Vérifications incluses :
          • Pré-dimensionnement surfacique : S ≥ Nser / σsol
          • Condition de rigidité : d ≥ (A − a) / 4   (BAEL 91 art. 15.II.2)
          • Hauteur totale minimale : H ≥ 20 cm      (NF DTU 13.1)
          • Poinçonnement (BAEL 91 A.5.2.4) — check indicatif
          • Non-fragilité : Amin = max(0.23·B·d·ft28/fe ; 0.001·B·H)
            (BAEL 91 A.4.2.1 et B.6.4)
          • Espacement maximal ≤ 25 cm en partie courante (NF DTU 13.1)
          • Ferraillage identique dans les deux sens
        """
    
        while True:
    
            self.clear_screen()
            self.banner()
    
            print("=" * 70)
            print(" " * 20 + "CALCUL DE LA SEMELLE ISOLÉE")
            print("=" * 70)
            print()
    
            print("📌 DONNÉES DE DÉPART")
            print("-" * 70)
    
            Nser_kN = self.lire_float(
                "Charge de service Nser (kN) : "
            )
    
            sigma_sol = self.lire_float(
                "Contrainte admissible du sol σsol (MPa) : "
            )
    
            a = self.lire_float(
                "Largeur du poteau a (m) : "
            )
    
            b = self.lire_float(
                "Longueur du poteau b (m) : "
            )
    
            Nu = self.lire_float(
                "Effort normal de calcul Nu (MN) : "
            )
    
            # -------------------------------------------------
            # CHOIX DE L'ENROBAGE
            # -------------------------------------------------
            print()
            print("Enrobage nominal des armatures :")
            print("  1 - 3 cm  (ambiance normale, semelle coulée sur béton de propreté)")
            print("  2 - 5 cm  (ambiance agressive ou semelle coulée directement sur le sol)")
            while True:
                choix_env = input("👉 Votre choix (1 ou 2) [1] : ").strip()
                if choix_env in ("", "1"):
                    enrobage_cm = 3.0
                    break
                if choix_env == "2":
                    enrobage_cm = 5.0
                    break
                print("❌ Choix invalide.")
            enrobage_m = enrobage_cm / 100.0
    
            # =====================================================
            # CONSTANTES / UNITÉS
            # =====================================================
    
            Nser = Nser_kN / 1000.0        # kN → MN
            gamma_beton = 25.0             # kN/m³
            Fe = self.Fe                   # MPa
            Fc28 = self.Fc28               # MPa
            gamma_b = self.gamma_b
            gamma_s = self.gamma_s
            Fed = Fe / gamma_s             # MPa
    
            # =====================================================
            # 1 - PRÉ-DIMENSIONNEMENT DE LA SURFACE
            # =====================================================
            # BAEL 91 art. 15.IV.1 : S ≥ Nser / σsol
    
            S_calc = Nser / sigma_sol
            A_calc = math.sqrt(S_calc)
    
            # Arrondi au pas de 5 cm (fanao mahazatra)
            A = math.ceil(A_calc / 0.05) * 0.05
            if A <= 0:
                A = A_calc
    
            B = A
            S = A * B
    
            # =====================================================
            # 2 - HAUTEUR UTILE ET HAUTEUR TOTALE
            # =====================================================
            # Condition de rigidité : d ≥ (A − a) / 4   (BAEL 91 art. 15.II.2)
    
            e_min = (A - a) / 4.0
            if e_min <= 0:
                print()
                print("❌ ERREUR : A doit être supérieur à a.")
                self.pause()
                continue
    
            # Hauteur utile (arrondie au cm supérieur)
            e = math.ceil(e_min * 100) / 100
    
            # Hauteur totale = hauteur utile + enrobage
            H = e + enrobage_m
    
            # Hauteur totale minimale réglementaire (NF DTU 13.1)
            H_min = 0.20
            if H < H_min:
                H = H_min
                e = H - enrobage_m
                hauteur_min_appliquee = True
            else:
                hauteur_min_appliquee = False
    
            # Hauteur de la partie pyramidale (glacis)
            h_glacis = H - e
    
            # =====================================================
            # 3 - POIDS PROPRE DE LA SEMELLE (TRONC DE PYRAMIDE)
            # =====================================================
            # Semelle tronconique :
            # base A × B  →  sommet a × b  sur hauteur H
            # V = H/3 × (A·B + a·b + √(A·B·a·b))
    
            V_semelle = (H / 3.0) * (
                A * B + a * b + math.sqrt(A * B * a * b)
            )
    
            P_kN = V_semelle * gamma_beton
            P_MN = P_kN / 1000.0
    
            # =====================================================
            # 4 - VÉRIFICATION DE LA CONTRAINTE DU SOL
            # =====================================================
    
            sigma_verif = (Nser + P_MN) / S
            sol_verifie = sigma_verif <= sigma_sol
    
            # =====================================================
            # 5 - POINÇONNEMENT (BAEL 91 A.5.2.4) — CHECK INDICATIF
            # =====================================================
            # NOTE : Le DTU 13.12 considère la condition de rigidité
            # d ≥ (A−a)/4 suffisante pour les semelles courantes.
            # Ce check est donné à titre indicatif pour les cas particuliers.
            #
            # Uc = périmètre du contour au niveau du feuillet moyen :
            # Uc = 2·(a + b + 2·H/2) = 2·(a + b + H)
    
            Uc = 2.0 * (a + b + H)
            Nu_lim_poinconnement = 0.045 * Uc * H * Fc28 / gamma_b
            poinconnement_ok = Nu <= Nu_lim_poinconnement
    
            # =====================================================
            # 6 - SECTION DES ARMATURES (MÉTHODE DES BIELLES)
            # =====================================================
            # DTU 13.12 Annexe 2 :
            # As ≥ Nu · (A − a) / (8 · d · σs)   avec σs = Fe / γs
    
            As_calc_m2 = Nu * (A - a) / (8.0 * e * Fed)
            As_calc_cm2 = As_calc_m2 * 10000.0
    
            # =====================================================
            # 7 - ARMATURE MINIMALE (NON-FRAGILITÉ)
            # =====================================================
            # BAEL 91 A.4.2.1 : As ≥ 0.23 · B · d · ft28 / fe
            # BAEL 91 B.6.4  : As ≥ 0.001 · B · H
    
            ft28 = min(0.6 + 0.06 * Fc28, 3.3)   # MPa
    
            B_mm = B * 1000.0
            e_mm = e * 1000.0
            H_mm = H * 1000.0
    
            Amin_cnf_cm2 = (0.23 * B_mm * e_mm * ft28 / Fe) / 100.0
            Amin_pct_cm2 = (0.001 * B_mm * H_mm) / 100.0
    
            Amin_cm2 = max(Amin_cnf_cm2, Amin_pct_cm2)
            As_retenue_cm2 = max(As_calc_cm2, Amin_cm2)
    
            # =====================================================
            # 8 - CHOIX AUTOMATIQUE DES ARMATURES
            # =====================================================
    
            ESP_MAX_CM = 25.0                # NF DTU 13.1
            LONGUEUR_FERRAILLAGE_CM = max((A - 2 * enrobage_m) * 100.0, 0.0)
    
            diametres = [8, 10, 12, 14, 16, 20, 25, 32]
            nb_max = 12
    
            if LONGUEUR_FERRAILLAGE_CM > 0:
                nb_min_esp = math.ceil(
                    LONGUEUR_FERRAILLAGE_CM / ESP_MAX_CM
                ) + 1
            else:
                nb_min_esp = 4
    
            nb_min = max(4, nb_min_esp)
            choix = []
    
            for n in range(nb_min, nb_max + 1):
    
                esp_n_cm = (
                    LONGUEUR_FERRAILLAGE_CM / (n - 1)
                    if n > 1 else 0.0
                )
    
                if esp_n_cm > ESP_MAX_CM + 1e-9:
                    continue
    
                for diam in diametres:
    
                    aire_une_barre_cm2 = (
                        math.pi * diam ** 2 / 4 / 100
                    )
                    aire_totale_cm2 = n * aire_une_barre_cm2
    
                    if aire_totale_cm2 >= As_retenue_cm2:
    
                        surplus = aire_totale_cm2 - As_retenue_cm2
                        choix.append((
                            surplus,
                            diam,
                            n,
                            aire_totale_cm2,
                            esp_n_cm
                        ))
    
            if choix:
    
                _, diametre, nb_barres, As_fournie_cm2, esp_cm = min(
                    choix,
                    key=lambda x: (x[0], x[1], x[2])
                )
                armature_verifiee = As_fournie_cm2 >= As_retenue_cm2
    
            else:
    
                nb_barres = nb_max
                diametre = diametres[-1]
                aire_une_barre_cm2 = (
                    math.pi * diametre ** 2 / 4 / 100
                )
                As_fournie_cm2 = nb_barres * aire_une_barre_cm2
                esp_cm = (
                    LONGUEUR_FERRAILLAGE_CM / (nb_barres - 1)
                    if nb_barres > 1 else 0.0
                )
                armature_verifiee = As_fournie_cm2 >= As_retenue_cm2
    
            # =====================================================
            # 9 - ESPACEMENT DES ARMATURES
            # =====================================================
    
            if nb_barres > 1:
                esp_m = (A - 2 * enrobage_m) / (nb_barres - 1)
            else:
                esp_m = 0.0
    
            esp_cm = esp_m * 100
            esp_verifie = esp_cm <= ESP_MAX_CM + 1e-9
    
            # =====================================================
            # AFFICHAGE COMPLET
            # =====================================================
    
            self.clear_screen()
            self.banner()
    
            print("=" * 70)
            print(" " * 18 + "CALCUL DE LA SEMELLE ISOLÉE")
            print("=" * 70)
    
            print()
            print("📌 DONNÉES DE DÉPART")
            print("-" * 70)
            print(f"Nser = {Nser_kN:.3f} kN = {Nser:.6f} MN")
            print(f"σsol = {sigma_sol:.3f} MPa")
            print(f"a    = {a:.3f} m")
            print(f"b    = {b:.3f} m")
            print(f"Nu   = {Nu:.6f} MN")
            print(f"Enrobage = {enrobage_cm:.0f} cm")
    
            # -------------------------------------------------
            # 1 - SURFACE
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("1 - PRÉ-DIMENSIONNEMENT DE LA SEMELLE")
            print("=" * 70)
    
            print()
            print("Formule (BAEL 91 art. 15.IV.1) :")
            print()
            print("        Nser")
            print("S =  ─────────")
            print("       σsol")
            print()
    
            print(
                f"S = {Nser:.6f} / {sigma_sol:.3f}"
                f" = {S_calc:.6f} m²"
            )
    
            print()
            print("Pour une semelle carrée : S = A²")
            print()
            print(
                f"A = √{S_calc:.6f}"
                f" = {A_calc:.4f} m"
            )
            print(
                f"✓ Dimension retenue : A = B = {A:.2f} m"
            )
    
            # -------------------------------------------------
            # 2 - ÉPAISSEUR / HAUTEUR
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("2 - HAUTEUR DE LA SEMELLE")
            print("=" * 70)
    
            print()
            print("Formule (BAEL 91 art. 15.II.2) :")
            print()
            print("        A - a")
            print("d ≥  ───────")
            print("          4")
            print()
    
            print(f"d ≥ ({A:.2f} - {a:.2f}) / 4 = {e_min:.4f} m")
            print(f"✓ Hauteur utile d = {e:.3f} m")
    
            if hauteur_min_appliquee:
                print(
                    f"⚠️ Hauteur totale portée au minimum réglementaire "
                    f"H = {H*100:.0f} cm (NF DTU 13.1)"
                )
    
            print()
            print("Formule : H = d + enrobage")
            print(
                f"H = {e*100:.1f} + {enrobage_cm:.0f}"
                f" = {H*100:.1f} cm"
            )
    
            # -------------------------------------------------
            # 3 - POIDS PROPRE (TRONC DE PYRAMIDE)
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("3 - POIDS PROPRE DE LA SEMELLE")
            print("=" * 70)
    
            print()
            print("Poids volumique du béton : γ = 25 kN/m³")
            print()
            print("Semelle tronconique :")
            print("V = H/3 × (A·B + a·b + √(A·B·a·b))")
            print()
            print(
                f"V = {H:.3f}/3 × ({A:.2f}·{B:.2f} + "
                f"{a:.2f}·{b:.2f} + "
                f"√({A:.2f}·{B:.2f}·{a:.2f}·{b:.2f}))"
            )
            print(f"V = {V_semelle:.4f} m³")
            print()
            print("P = V × 25")
            print(f"P = {V_semelle:.4f} × 25 = {P_kN:.2f} kN")
            print(f"P = {P_MN:.6f} MN")
    
            # -------------------------------------------------
            # 4 - VÉRIFICATION DU SOL
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("4 - VÉRIFICATION DE LA CONTRAINTE DU SOL")
            print("=" * 70)
    
            print()
            print("Formule :")
            print()
            print("          Nser + P")
            print("σ =  ───────────── ≤ σsol")
            print("              S")
            print()
    
            print(
                f"σ = ({Nser:.6f} + {P_MN:.6f}) / {S:.4f}"
            )
            print(f"σ = {sigma_verif:.4f} MPa")
            print(f"σsol = {sigma_sol:.4f} MPa")
    
            if sol_verifie:
                print()
                print("✓ CONTRAINTE DU SOL VÉRIFIÉE")
            else:
                print()
                print("⚠️ CONTRAINTE DU SOL NON VÉRIFIÉE")
                print("   → Augmenter A ou revoir la contrainte du sol.")
    
            # -------------------------------------------------
            # 5 - POINÇONNEMENT (INDICATIF)
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("5 - POINÇONNEMENT (BAEL 91 A.5.2.4) — INDICATIF")
            print("=" * 70)
    
            print()
            print("NOTE : Non exigé par DTU 13.12 pour les semelles courantes.")
            print("La condition de rigidité d ≥ (A−a)/4 est suffisante.")
            print("Ce check est donné pour les cas particuliers.")
            print()
            print("Périmètre au feuillet moyen :")
            print("Uc = 2·(a + b + H)")
            print(
                f"Uc = 2·({a:.2f} + {b:.2f} + {H:.3f})"
                f" = {Uc:.3f} m"
            )
    
            print()
            print("Condition : Nu ≤ 0.045 · Uc · H · fc28 / γb")
            print(
                f"Nu,lim = 0.045 × {Uc:.3f} × {H:.3f} × "
                f"{Fc28:.1f} / {gamma_b:.2f}"
            )
            print(f"Nu,lim = {Nu_lim_poinconnement:.4f} MN")
    
            print()
            print(f"Nu     = {Nu:.4f} MN")
    
            if poinconnement_ok:
                print(
                    f"✓ {Nu:.4f} ≤ {Nu_lim_poinconnement:.4f}"
                    " : POINÇONNEMENT OK (indicatif)"
                )
            else:
                print(
                    f"⚠️ {Nu:.4f} > {Nu_lim_poinconnement:.4f}"
                    " : POINÇONNEMENT NON VÉRIFIÉ"
                )
                print("   → Augmenter H ou la section du poteau.")
    
            # -------------------------------------------------
            # 6 - ARMATURES (MÉTHODE DES BIELLES)
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("6 - SECTION DES ARMATURES (MÉTHODE DES BIELLES)")
            print("=" * 70)
    
            print()
            print("Fed = Fe / γs")
            print(
                f"Fed = {Fe:.0f} / {gamma_s:.2f}"
                f" = {Fed:.2f} MPa"
            )
    
            print()
            print("Formule (DTU 13.12 Annexe 2) :")
            print()
            print("        Nu · (A - a)")
            print("As =  ───────────────")
            print("          8 · d · Fed")
            print()
    
            print(
                f"As = {Nu:.6f} × ({A:.2f} - {a:.2f})"
                f" / (8 × {e:.3f} × {Fed:.2f})"
            )
            print(f"As = {As_calc_m2:.8f} m²")
            print(f"As = {As_calc_cm2:.3f} cm²")
    
            # -------------------------------------------------
            # 7 - ARMATURE MINIMALE (NON-FRAGILITÉ)
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("7 - ARMATURE MINIMALE (NON-FRAGILITÉ)")
            print("=" * 70)
    
            print()
            print(f"ft28 = 0.6 + 0.06 × {Fc28:.1f} = {ft28:.3f} MPa")
            print()
    
            print("A.4.2.1 : As ≥ 0.23 × B × d × ft28 / fe")
            print(
                f"Amin,cnf = 0.23 × {B_mm:.1f} × {e_mm:.1f} × "
                f"{ft28:.3f} / {Fe:.1f}"
            )
            print(f"Amin,cnf = {Amin_cnf_cm2:.3f} cm²")
    
            print()
            print("B.6.4 : As ≥ 0.001 × B × H")
            print(
                f"Amin,pct = 0.001 × {B_mm:.1f} × {H_mm:.1f}"
            )
            print(f"Amin,pct = {Amin_pct_cm2:.3f} cm²")
    
            print()
            print(
                f"✓ Amin = max({Amin_cnf_cm2:.3f} ; "
                f"{Amin_pct_cm2:.3f}) = {Amin_cm2:.3f} cm²"
            )
    
            print()
            print(
                f"As retenue = max({As_calc_cm2:.3f} ; "
                f"{Amin_cm2:.3f})"
            )
            print(f"✓ As retenue = {As_retenue_cm2:.3f} cm²")
    
            # -------------------------------------------------
            # 8 - CHOIX AUTOMATIQUE
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("8 - CHOIX AUTOMATIQUE DES ARMATURES")
            print("=" * 70)
    
            print()
            print("Critères de choix :")
            print("• As fournie ≥ As retenue")
            print(f"• Espacement ≤ {ESP_MAX_CM:.0f} cm (NF DTU 13.1)")
            print("• Ferraillage identique dans les deux sens")
            print("• Surplus d'acier minimal")
            print()
    
            print(
                f"✓ Armatures retenues : {nb_barres}HA{diametre}"
            )
            print(
                f"As fournie = {nb_barres} × π × {diametre}² / 4"
                f" = {As_fournie_cm2:.3f} cm²"
            )
    
            if armature_verifiee:
                print(
                    f"✓ As fournie ({As_fournie_cm2:.3f})"
                    f" ≥ As retenue ({As_retenue_cm2:.3f})"
                )
            else:
                print(
                    f"⚠️ As fournie ({As_fournie_cm2:.3f})"
                    f" < As retenue ({As_retenue_cm2:.3f})"
                )
    
            # -------------------------------------------------
            # 9 - ESPACEMENT
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print("9 - ESPACEMENT DES ARMATURES")
            print("=" * 70)
    
            print()
            print("Formule :")
            print()
            print("esp = (A - 2·enrobage) / (n - 1)")
            print()
    
            print(
                f"esp = ({A:.2f} - 2×{enrobage_m:.2f}) / ({nb_barres} - 1)"
            )
            print(f"esp = {esp_m:.3f} m")
            print(f"esp = {esp_cm:.1f} cm")
    
            if esp_verifie:
                print(
                    f"✓ Espacement vérifié : {esp_cm:.1f} cm ≤ "
                    f"{ESP_MAX_CM:.0f} cm"
                )
            else:
                print(
                    f"⚠️ Espacement non vérifié : {esp_cm:.1f} cm > "
                    f"{ESP_MAX_CM:.0f} cm"
                )
    
            # -------------------------------------------------
            # TABLEAU FINAL
            # -------------------------------------------------
    
            print()
            print("=" * 70)
            print(" " * 23 + "RÉSULTAT FINAL")
            print("=" * 70)
    
            print()
            print("🧱 SEMELLE")
            print(f"   A × B = {A:.2f} × {B:.2f} m")
            print(f"   S = {S:.4f} m²")
            print(f"   d = {e:.3f} m = {e * 100:.0f} cm")
            print(f"   H = {H:.3f} m = {H * 100:.0f} cm")
            print(f"   Enrobage = {enrobage_cm:.0f} cm")
    
            print()
            print("⚖️ CHARGE / SOL")
            print(f"   Nser = {Nser_kN:.3f} kN")
            print(f"   P = {P_kN:.2f} kN")
            print(f"   σ calculée = {sigma_verif:.4f} MPa")
            print(f"   σsol = {sigma_sol:.4f} MPa")
            print(
                "   ✓ Sol vérifié"
                if sol_verifie
                else "   ⚠️ Sol NON vérifié"
            )
    
            print()
            print("🛡️ POINÇONNEMENT (indicatif)")
            print(f"   Uc = {Uc:.3f} m")
            print(f"   Nu,lim = {Nu_lim_poinconnement:.4f} MN")
            print(f"   Nu = {Nu:.4f} MN")
            print(
                "   ✓ Vérifié (indicatif)"
                if poinconnement_ok
                else "   ⚠️ NON vérifié"
            )
    
            print()
            print("🔩 ARMATURES")
            print(f"   As calculée = {As_calc_cm2:.3f} cm²")
            print(f"   Amin = {Amin_cm2:.3f} cm²")
            print(f"   As retenue = {As_retenue_cm2:.3f} cm²")
            print(f"   ✓ Armatures : {nb_barres}HA{diametre}")
            print(f"   As fournie = {As_fournie_cm2:.3f} cm²")
            print(f"   Espacement = {esp_cm:.1f} cm")
            print("   Disposition : quadrillage dans les 2 sens")
    
            self.schema_armatures(
                nb_barres, diametre,
                "SCHÉMA BA — SEMELLE ISOLÉE"
            )
    
            print()
            print("⚠️ NOTE")
            print("Le calcul suit la méthode des bielles (DTU 13.12) et le BAEL 91.")
            print("Les vérifications de poinçonnement et de non-fragilité sont incluses.")
            print("Pour un projet réel, vérifier également :")
            print("  • les tassements différentiels")
            print("  • les recouvrements et ancrages détaillés")
            print("  • la présence d'eau / agressivité du sol (enrobage)")
            print("  • la condition de non-glissement si charges horizontales")
    
            print()
            print("=" * 70)
            print("✓ CALCUL DE LA SEMELLE ISOLÉE TERMINÉ")
            print("=" * 70)
    
            print()
    
            refaire = input(
                "Nouveau calcul de semelle ? (O/N) : "
            ).strip().lower()
    
            if refaire not in ["o", "oui"]:
                break

    # =========================================================
    # 8 - CALCUL DE LA FOSSE SEPTIQUE
    # Référentiel : 250 L/usager + S = N/(10H²) pour le filtre
    # =========================================================
    
    def fosse_septique(self):
        """Calcul d'une fosse septique à 3 compartiments :
          • Chute (2/3 du volume)
          • Décantation (1/3 du volume)
          • Filtre (lit bactérien : S = N/(10H²))
    
        Vérifications incluses :
          • Volume minimal : Vfos ≥ 3 m³ (fosse toutes eaux)
          • Hauteur d'eau : He ≥ 1 m
          • Surface du filtre : S = N/(10H²)
        """
    
        while True:
    
            self.clear_screen()
            self.banner()
    
            print("=" * 70)
            print(" " * 19 + "CALCUL DE LA FOSSE SEPTIQUE")
            print("=" * 70)
            print()
    
            print("📌 DIMENSIONNEMENT DE LA FOSSE")
            print("-" * 70)
            print()
    
            N = self.lire_float("Nombre d'usagers N (personnes) : ")
            Lfos = self.lire_float("Largeur intérieure Lfos (m) : ")
            He = self.lire_float("Profondeur d'eau He (m) : ")
    
            # Donnée : 250 L/usager
            Ve_usager = 250.0
    
            print()
            print(f"✓ Volume d'eau par usager : Ve = {Ve_usager:.0f} L/usager")
    
            # =================================================
            # VÉRIFICATION HAUTEUR MINIMALE
            # =================================================
            if He < 1.0:
                print()
                print("⚠️ Hauteur d'eau He < 1 m (minimum recommandé).")
                print("   → Augmenter He à au moins 1 m.")
                self.pause()
                continue
    
            # =================================================
            # 1 - CAPACITÉ DE LA FOSSE
            # =================================================
    
            Vfos_L = Ve_usager * N
            Vfos_m3 = Vfos_L / 1000.0
    
            # Vérification volume minimal
            Vfos_min = 3.0  # m³
            if Vfos_m3 < Vfos_min:
                print()
                print(f"⚠️ Volume fosse {Vfos_m3:.3f} m³ < {Vfos_min} m³ (minimum).")
                print(f"   → Augmenter N ou les dimensions.")
    
            # Volume chute (2/3 du volume)
            Vc_m3 = (2.0 / 3.0) * Vfos_m3
    
            # Volume décantation (1/3 du volume)
            Vd_m3 = (1.0 / 3.0) * Vfos_m3
    
            # =================================================
            # 2 - VOLUME DU FILTRE (CORRIGÉ)
            # =================================================
            # Surface du lit bactérien : S = N / (10 × H²)
            # Volume du filtre : Vf = S × H
    
            H_filtre = He
            S_filtre_m2 = N / (10.0 * H_filtre ** 2)
            Vf_m3 = S_filtre_m2 * H_filtre
            Vf_L = Vf_m3 * 1000.0
    
            print()
            print("📦 CAPACITÉ DE LA FOSSE")
            print("-" * 70)
            print()
            print(f"✓ Volume de la fosse : Vfos = Ve × N")
            print(f"  Vfos = {Ve_usager:g} × {N:g} = {Vfos_L:,.0f} L = {Vfos_m3:.3f} m³")
            print()
            print(f"✓ Volume de la chute : Vc = 2/3 × Vfos")
            print(f"  Vc = 2/3 × {Vfos_m3:.3f} = {Vc_m3:.3f} m³")
            print()
            print(f"✓ Volume de la décantation : Vd = 1/3 × Vfos")
            print(f"  Vd = 1/3 × {Vfos_m3:.3f} = {Vd_m3:.3f} m³")
            print()
            print(f"✓ Volume du filtre : S = N / (10 × H²)")
            print(f"  S = {N:g} / (10 × {H_filtre:.3f}²) = {S_filtre_m2:.4f} m²")
            print(f"  Vf = S × H = {S_filtre_m2:.4f} × {H_filtre:.3f} = {Vf_m3:.4f} m³ = {Vf_L:,.0f} L")
    
            # =================================================
            # 3 - LONGUEUR DE CHAQUE COMPARTIMENT
            # =================================================
    
            section_hydraulique = Lfos * He
    
            Lc = Vc_m3 / section_hydraulique
            Ld = Vd_m3 / section_hydraulique
            Lf = Vf_m3 / section_hydraulique
            Ltot = Lc + Ld + Lf
    
            print()
            print("📐 LONGUEUR DE CHAQUE COMPARTIMENT")
            print("-" * 70)
            print()
            print("Chute :")
            print(f"  Lc = Vc / (Lfos × He) = {Vc_m3:.3f} / ({Lfos:g} × {He:g})")
            print(f"  Lc = {Lc:.3f} m")
            print()
            print("Décantation :")
            print(f"  Ld = Vd / (Lfos × He) = {Vd_m3:.3f} / ({Lfos:g} × {He:g})")
            print(f"  Ld = {Ld:.3f} m")
            print()
            print("Filtre :")
            print(f"  Lf = Vf / (Lfos × He) = {Vf_m3:.4f} / ({Lfos:g} × {He:g})")
            print(f"  Lf = {Lf:.3f} m")
    
            print()
            print("📏 DIMENSION TOTALE")
            print("-" * 70)
            print(f"  Ltot = Lc + Ld + Lf = {Lc:.3f} + {Ld:.3f} + {Lf:.3f}")
            print(f"  ✓ LONGUEUR TOTALE = {Ltot:.3f} m")
    
            # =================================================
            # 4 - RÉCAPITULATIF
            # =================================================
    
            print()
            print("📋 RÉCAPITULATIF")
            print("-" * 70)
            print(f"   Usagers              : {N:g} personnes")
            print(f"   Largeur intérieure   : {Lfos:.3f} m")
            print(f"   Profondeur d'eau     : {He:.3f} m")
            print(f"   Volume fosse         : {Vfos_m3:.3f} m³")
            print(f"   Volume chute         : {Vc_m3:.3f} m³")
            print(f"   Volume décantation   : {Vd_m3:.3f} m³")
            print(f"   Volume filtre        : {Vf_m3:.4f} m³")
            print(f"   Longueur chute       : {Lc:.3f} m")
            print(f"   Longueur décantation : {Ld:.3f} m")
            print(f"   Longueur filtre      : {Lf:.3f} m")
            print(f"   Longueur totale      : {Ltot:.3f} m")
    
            print()
            print("=" * 70)
            print("✓ CALCUL DE LA FOSSE SEPTIQUE TERMINÉ")
            print("=" * 70)
    
            refaire = input("\nNouveau calcul de fosse ? (O/N) : ").strip().lower()
            if refaire not in ["o", "oui"]:
                break
    
        # =========================================================
        # 9 - AVANT MÉTRÉ D'OUVRAGE + SAUVEGARDE DES DONNÉES
        # =========================================================

    # =========================================================
    # 9 - AVANT MÉTRÉ D'OUVRAGE + SAUVEGARDE DES DONNÉES
    # =========================================================
    
    def avant_metre(self):
        """Avant-métré général avec :
          • Formules de surface : rectangle, carré, triangle, cercle, trapèze
          • Formules de volume : parallélépipède, cylindre
          • Multiplication d'ouvrages (regroupement)
          • Déductions visibles et contrôle anti-doublon
        """
    
        dossier = os.path.join(os.path.dirname(os.path.abspath(__file__)), "donnees_btp")
        os.makedirs(dossier, exist_ok=True)
        fichier_json = os.path.join(dossier, "avant_metre.json")
    
        # =====================================================
        # CHARGEMENT / SAUVEGARDE
        # =====================================================
        def charger_donnees():
            if not os.path.exists(fichier_json):
                return []
            try:
                with open(fichier_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []
            except (json.JSONDecodeError, OSError):
                print("⚠️ Impossible de lire le fichier de données.")
                return []
    
        def sauvegarder_donnees(data):
            try:
                with open(fichier_json, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                print(f"✓ Données enregistrées : {fichier_json}")
                return True
            except OSError as e:
                print(f"❌ Erreur d'enregistrement : {e}")
                return False
    
        # =====================================================
        # OUTILS GÉNÉRAUX
        # =====================================================
        def valeur_num(v, default=0.0):
            try:
                return float(str(v).replace(",", "."))
            except (TypeError, ValueError):
                return default
    
        def normaliser_ligne(x):
            return {
                "_id": x.get("_id", ""),
                "designation": x.get("designation", ""),
                "categorie": x.get("categorie", ""),
                "NPE": x.get("NPE", x.get("N", "")),
                "U": x.get("U", x.get("unite", "")),
                "L": x.get("L", ""),
                "l": x.get("l", ""),
                "h": x.get("h", ""),
                "aux": x.get("aux", ""),
                "part": x.get("part", ""),
                "def": x.get("def", ""),
                "Qt": x.get("Qt", x.get("quantite", "")),
                "surface_brute": x.get("surface_brute", ""),
                "total_deduit": x.get("total_deduit", ""),
                "formule": x.get("formule", ""),
                "forme": x.get("forme", ""),
                "deductions": x.get("deductions", []) if isinstance(x.get("deductions", []), list) else [],
                "inclus_dans": x.get("inclus_dans", ""),
                "compose_de": x.get("compose_de", []),
                "est_composition": x.get("est_composition", False),
            }
    
        def assurer_ids(projet):
            for x in projet.get("lignes", []):
                if not x.get("_id"):
                    x["_id"] = uuid.uuid4().hex
    
        def index_par_id(projet, identifiant):
            for i, x in enumerate(projet.get("lignes", [])):
                if x.get("_id") == identifiant:
                    return i
            return None
    
        def quantite_nette(projet, idx, pile=None):
            if pile is None:
                pile = set()
            lignes = projet.get("lignes", [])
            if idx is None or idx < 0 or idx >= len(lignes):
                return 0.0
            if idx in pile:
                return 0.0
            pile = set(pile)
            pile.add(idx)
    
            x = lignes[idx]
            brut = None
            if str(x.get("U", x.get("unite", ""))) in ("m²", "m³"):
                sb = x.get("surface_brute", None)
                if sb not in (None, ""):
                    brut = valeur_num(sb, None)
            if brut is None:
                brut = valeur_num(x.get("Qt", x.get("quantite", 0)))
    
            total = 0.0
            for d in x.get("deductions", []) if isinstance(x.get("deductions", []), list) else []:
                source_id = d.get("source_line_id")
                if source_id:
                    src_idx = index_par_id(projet, source_id)
                    if src_idx is not None:
                        total += quantite_nette(projet, src_idx, pile)
                        continue
                total += valeur_num(d.get("Qt", d.get("surface", 0)))
    
            return max(0.0, brut - total)
    
        def mettre_a_jour_quantites(projet):
            assurer_ids(projet)
            for i, x in enumerate(projet.get("lignes", [])):
                q = quantite_nette(projet, i)
                x["Qt"] = q
                x["quantite"] = q
    
        def quantite_brute(projet, idx):
            lignes = projet.get("lignes", [])
            if idx < 0 or idx >= len(lignes):
                return 0.0
            x = normaliser_ligne(lignes[idx])
            u = str(x.get("U", "")).strip()
    
            if u in ("m²", "m³"):
                sb = x.get("surface_brute", "")
                if sb not in (None, ""):
                    return valeur_num(sb, 0.0)
    
            L = valeur_num(x.get("L", 0), 0.0)
            l = valeur_num(x.get("l", 0), 0.0)
            h = valeur_num(x.get("h", 0), 0.0)
            N = valeur_num(x.get("NPE", x.get("N", 1)), 1.0)
    
            if u == "m³":
                return L * l * h * N
            if u == "m²":
                return L * l * N
            if u == "ml":
                return L * N
            if u in ("u", "forfait"):
                return N
            return valeur_num(x.get("Qt", 0), 0.0)
    
        # =====================================================
        # FORMULAIRES SURFACE / VOLUME
        # =====================================================
        def saisir_formule_surface():
            print()
            print("Forme géométrique (m²) :")
            print("  1 - Rectangle  : S = L × l × N")
            print("  2 - Carré      : S = c × c × N")
            print("  3 - Triangle   : S = (L × l) / 2 × N")
            print("  4 - Cercle     : S = π × r² × N")
            print("  5 - Trapèze    : S = (B + b) / 2 × h × N")
            while True:
                c = input("👉 Votre choix (1-5) [1] : ").strip() or "1"
                if c in ("1", "2", "3", "4", "5"):
                    break
                print("❌ Choix invalide.")
    
            if c == "1":
                L = self.lire_float("Longueur L (m) : ")
                l = self.lire_float("Largeur l (m) : ")
                N = self.lire_float("Nombre N : ")
                S = L * l * N
                return L, l, 0, N, "L × l × N", "Rectangle", S
    
            if c == "2":
                L = self.lire_float("Côté c (m) : ")
                N = self.lire_float("Nombre N : ")
                S = L * L * N
                return L, L, 0, N, "c × c × N", "Carré", S
    
            if c == "3":
                L = self.lire_float("Base L (m) : ")
                l = self.lire_float("Hauteur l (m) : ")
                N = self.lire_float("Nombre N : ")
                S = (L * l) / 2.0 * N
                return L, l, 0, N, "(L × l) / 2 × N", "Triangle", S
    
            if c == "4":
                L = self.lire_float("Rayon r (m) : ")
                N = self.lire_float("Nombre N : ")
                S = math.pi * L * L * N
                return L, 0, 0, N, "π × r² × N", "Cercle", S
    
            L = self.lire_float("Grande base B (m) : ")
            l = self.lire_float("Petite base b (m) : ")
            h = self.lire_float("Hauteur h (m) : ")
            N = self.lire_float("Nombre N : ")
            S = (L + l) / 2.0 * h * N
            return L, l, h, N, "(B + b) / 2 × h × N", "Trapèze", S
    
        def saisir_formule_volume():
            print()
            print("Forme géométrique (m³) :")
            print("  1 - Parallélépipède : V = L × l × h × N")
            print("  2 - Cylindre        : V = π × r² × h × N")
            while True:
                c = input("👉 Votre choix (1-2) [1] : ").strip() or "1"
                if c in ("1", "2"):
                    break
                print("❌ Choix invalide.")
    
            if c == "1":
                L = self.lire_float("Longueur L (m) : ")
                l = self.lire_float("Largeur l (m) : ")
                h = self.lire_float("Hauteur h (m) : ")
                N = self.lire_float("Nombre N : ")
                V = L * l * h * N
                return L, l, h, N, "L × l × h × N", "Parallélépipède", V
    
            L = self.lire_float("Rayon r (m) : ")
            h = self.lire_float("Hauteur h (m) : ")
            N = self.lire_float("Nombre N : ")
            V = math.pi * L * L * h * N
            return L, 0, h, N, "π × r² × h × N", "Cylindre", V
    
        def saisir_unite():
            print()
            print("Unité de calcul :")
            print("  1 - m²   (formes géométriques)")
            print("  2 - m³   (formes géométriques)")
            print("  3 - ml   = L × N")
            print("  4 - u    = N")
            print("  5 - forfait")
            choix = {"1": "m²", "2": "m³", "3": "ml", "4": "u", "5": "forfait",
                     "m2": "m²", "m²": "m²", "m3": "m³", "m³": "m³",
                     "ml": "ml", "u": "u", "forfait": "forfait"}
            while True:
                c = input("👉 Choisir 1-5 ou m²/m³/ml/u/forfait : ").strip().lower()
                if c in choix:
                    return choix[c]
                print("❌ Choix invalide.")
    
        # =====================================================
        # AJOUT D'UN OUVRAGE
        # =====================================================
        def ajouter_ligne(projet):
            print()
            self.section("AJOUT RAPIDE D'UN OUVRAGE", "➕")
            designation = input("Désignation : ").strip()
            if not designation:
                print("❌ La désignation est obligatoire.")
                return
    
            unite = saisir_unite()
            L = l = h = N = 0.0
            quantite = 0.0
            formule = ""
            forme = ""
            surface_brute = 0.0
    
            if unite == "m²":
                L, l, h, N, formule, forme, surface_brute = saisir_formule_surface()
                quantite = surface_brute
            elif unite == "m³":
                L, l, h, N, formule, forme, surface_brute = saisir_formule_volume()
                quantite = surface_brute
            elif unite == "ml":
                L = self.lire_float("Longueur L (m) : ")
                N = self.lire_float("Nombre N : ")
                quantite = L * N
                formule = "L × N"
            else:
                N = self.lire_float("Nombre / quantité N : ")
                quantite = N
                formule = "N"
    
            ligne = {
                "_id": uuid.uuid4().hex,
                "designation": designation,
                "categorie": "",
                "NPE": N,
                "U": unite,
                "L": L,
                "l": l,
                "h": h,
                "aux": "",
                "part": "",
                "def": "",
                "Qt": quantite,
                "formule": formule,
                "forme": forme,
                "quantite": quantite,
                "unite": unite,
                "N": N,
                "surface_brute": surface_brute,
                "total_deduit": 0.0,
                "deductions": [],
                "inclus_dans": "",
                "compose_de": [],
                "est_composition": False,
            }
            projet.setdefault("lignes", []).append(ligne)
            print(f"✓ {designation} : {quantite:.3f} {unite}")
            print(f"  Forme : {forme}")
            print(f"  Formule : {formule}")
    
        # =====================================================
        # CHOIX D'UN OUVRAGE
        # =====================================================
        def choisir_ouvrage(projet, message="Choisir le numéro de l'ouvrage : "):
            lignes = projet.get("lignes", [])
            if not lignes:
                print("❌ Aucun ouvrage disponible.")
                return None
    
            print()
            print("Ouvrages disponibles :")
            for i, raw in enumerate(lignes, 1):
                x = normaliser_ligne(raw)
                note = ""
                if x.get("inclus_dans"):
                    note = " [combiné]"
                print(f"  {i} - {x['designation']} [{x['U']}]{note}")
    
            while True:
                choix = input(message).strip()
                if choix == "0":
                    return None
                try:
                    idx = int(choix)
                    if 1 <= idx <= len(lignes):
                        return idx - 1
                except ValueError:
                    pass
                print("❌ Numéro invalide.")
    
        # =====================================================
        # MULTIPLICATION D'OUVRAGES
        # =====================================================
        def multiplier_ouvrages(projet):
            assurer_ids(projet)
            lignes = projet.get("lignes", [])
            if len(lignes) < 2:
                print("❌ Il faut au moins 2 ouvrages pour faire une multiplication.")
                return
    
            print()
            self.section("MULTIPLICATION D'OUVRAGES", "✖️")
            print("Sélectionne les ouvrages à regrouper (séparés par des virgules).")
            print("Exemple : 1,3,5")
            print()
            for i, raw in enumerate(lignes, 1):
                x = normaliser_ligne(raw)
                if x.get("inclus_dans"):
                    print(f"  {i} - {x['designation']} [{x['U']}] (déjà combiné)")
                else:
                    q = quantite_nette(projet, i - 1)
                    print(f"  {i} - {x['designation']} [{x['U']}] | Qt = {q:.3f}")
    
            saisie = input("\n👉 Numéros des ouvrages (0 = annuler) : ").strip()
            if saisie == "0":
                return
    
            try:
                indices = sorted(set(int(s.strip()) - 1 for s in saisie.split(",") if s.strip()))
            except ValueError:
                print("❌ Format invalide. Exemple : 1,3,5")
                return
    
            if len(indices) < 2:
                print("❌ Sélectionne au moins 2 ouvrages.")
                return
    
            for idx in indices:
                if idx < 0 or idx >= len(lignes):
                    print(f"❌ Numéro {idx + 1} invalide.")
                    return
                if lignes[idx].get("inclus_dans"):
                    print(f"❌ L'ouvrage {idx + 1} est déjà combiné.")
                    return
    
            unites = set(lignes[i].get("U", "") for i in indices)
            if len(unites) != 1:
                print(f"❌ Unités différentes : {unites}. Impossible de combiner.")
                return
            unite = unites.pop()
    
            total = sum(quantite_nette(projet, i) for i in indices)
    
            print()
            print("Résumé de la combinaison :")
            for i in indices:
                x = normaliser_ligne(lignes[i])
                q = quantite_nette(projet, i)
                print(f"  • {x['designation']} : {q:.3f} {unite}")
            print(f"  TOTAL = {total:.3f} {unite}")
    
            nouvelle_designation = input("\n👉 Nouvelle désignation : ").strip()
            if not nouvelle_designation:
                print("❌ Désignation obligatoire.")
                return
    
            new_id = uuid.uuid4().hex
            new_ligne = {
                "_id": new_id,
                "designation": nouvelle_designation,
                "categorie": "COMPOSITION",
                "NPE": 1.0,
                "U": unite,
                "L": 0, "l": 0, "h": 0,
                "aux": "", "part": "", "def": "",
                "Qt": total,
                "surface_brute": total,
                "formule": f"Σ des ouvrages {[i + 1 for i in indices]}",
                "forme": "Composition",
                "quantite": total,
                "unite": unite,
                "N": 1.0,
                "total_deduit": 0.0,
                "deductions": [],
                "inclus_dans": "",
                "compose_de": [lignes[i].get("_id") for i in indices],
                "est_composition": True,
            }
            projet["lignes"].append(new_ligne)
    
            for i in indices:
                projet["lignes"][i]["inclus_dans"] = new_id
    
            print(f"✓ Ouvrage composé créé : {nouvelle_designation} = {total:.3f} {unite}")
    
        # =====================================================
        # MODIFICATION D'UNE LIGNE
        # =====================================================
        def modifier_ligne(projet):
            idx = choisir_ouvrage(projet, "N° de l'ouvrage à modifier (0 = annuler) : ")
            if idx is None:
                return
    
            x = normaliser_ligne(projet["lignes"][idx])
            print()
            self.section(f"MODIFIER L'OUVRAGE N°{idx + 1}", "✏️")
            print("Entrée = garder la valeur actuelle.")
    
            def mc(nom, valeur):
                v = input(f"{nom} [{valeur}] : ").strip()
                return valeur if v == "" else v
    
            x["designation"] = mc("Désignation", x["designation"])
            x["U"] = mc("Unité (m²/m³/ml/u/forfait)", x["U"])
            x["NPE"] = mc("NPE / N", x["NPE"])
            x["L"] = mc("L", x["L"])
            x["l"] = mc("l", x["l"])
            x["h"] = mc("h", x["h"])
            x["Qt"] = mc("Qt", x["Qt"])
    
            x["unite"] = x["U"]
            x["N"] = x["NPE"]
            x["quantite"] = x["Qt"]
            x["deductions"] = projet["lignes"][idx].get("deductions", [])
            x["inclus_dans"] = projet["lignes"][idx].get("inclus_dans", "")
            x["compose_de"] = projet["lignes"][idx].get("compose_de", [])
            x["est_composition"] = projet["lignes"][idx].get("est_composition", False)
            projet["lignes"][idx] = x
            print(f"✓ Ouvrage modifié : {x['designation']}")
    
        # =====================================================
        # DÉDUCTIONS (avec contrôle anti-doublon)
        # =====================================================
        def ajouter_deduction(projet):
            """Déduit une ligne existante d'une autre ligne.
    
            Règle : un ouvrage déjà déduit d'une cible NE PEUT PLUS être
            sélectionné une seconde fois pour la même cible.
            """
            assurer_ids(projet)
            lignes = projet.get("lignes", [])
            if len(lignes) < 2:
                print("❌ Il faut au moins 2 ouvrages.")
                return
    
            cible_idx = choisir_ouvrage(
                projet,
                "N° de l'ouvrage SUR LEQUEL on veut déduire (0 = annuler) : "
            )
            if cible_idx is None:
                return
            cible = normaliser_ligne(lignes[cible_idx])
    
            # Récupérer les IDs déjà déduits de cette cible
            deja_deduits_ids = set()
            for d in lignes[cible_idx].get("deductions", []):
                sid = d.get("source_line_id")
                if sid:
                    deja_deduits_ids.add(sid)
    
            print()
            print(f"✓ Ouvrage à réduire : {cible['designation']} [{cible['U']}]")
            print("\nSélectionne l'ouvrage à enlever :")
    
            disponibles = []
            for i, raw in enumerate(lignes, 1):
                if i - 1 == cible_idx:
                    continue
                x = normaliser_ligne(raw)
                if x.get("inclus_dans"):
                    continue
                # Exclure les déjà déduits de cette cible
                if x.get("_id") in deja_deduits_ids:
                    continue
                q = quantite_nette(projet, i - 1)
                disponibles.append((i, x, q))
                print(f"  {i} - {x['designation']} [{x['U']}] | Qt nette = {q:.3f}")
    
            if not disponibles:
                print()
                print("❌ Aucun ouvrage disponible à déduire de cette cible.")
                print("   (Tous les ouvrages éligibles ont déjà été déduits,")
                print("    ou aucun n'est compatible.)")
                return
    
            while True:
                choix = input("N° de l'élément à déduire (0 = annuler) : ").strip()
                if choix == "0":
                    return
                try:
                    source_idx = int(choix) - 1
                except ValueError:
                    source_idx = -1
    
                if source_idx < 0 or source_idx >= len(lignes) or source_idx == cible_idx:
                    print("❌ Sélection invalide.")
                    continue
    
                source_id_check = lignes[source_idx].get("_id")
                if source_id_check in deja_deduits_ids:
                    print("❌ Cet ouvrage est déjà déduit de cette cible.")
                    continue
    
                if lignes[source_idx].get("inclus_dans"):
                    print("❌ Cet ouvrage est déjà combiné.")
                    continue
    
                break
    
            source = normaliser_ligne(lignes[source_idx])
            if cible["U"] != source["U"]:
                print(f"❌ Unités différentes : {cible['U']} / {source['U']}.")
                return
    
            source_q = quantite_nette(projet, source_idx)
            cible_q = quantite_nette(projet, cible_idx)
            if source_q <= 0:
                print("❌ Quantité nulle.")
                return
            if source_q > cible_q + 1e-9:
                print(f"❌ Déduction impossible : {source_q:.3f} > {cible_q:.3f}.")
                return
    
            source_id = lignes[source_idx].get("_id")
            target_id = lignes[cible_idx].get("_id")
    
            def reference_atteint(start_idx, wanted_id, visites=None):
                if visites is None:
                    visites = set()
                if start_idx in visites:
                    return False
                visites.add(start_idx)
                for d in lignes[start_idx].get("deductions", []):
                    sid = d.get("source_line_id")
                    if sid == wanted_id:
                        return True
                    si = index_par_id(projet, sid) if sid else None
                    if si is not None and reference_atteint(si, wanted_id, visites):
                        return True
                return False
    
            if reference_atteint(source_idx, target_id):
                print("❌ Cette déduction créerait une boucle.")
                return
    
            for d in lignes[cible_idx].get("deductions", []):
                if d.get("source_line_id") == source_id:
                    print("❌ Cet ouvrage est déjà déduit de cette cible.")
                    return
    
            deduction = {
                "source_line_id": source_id,
                "designation": source["designation"],
                "NPE": source["NPE"],
                "U": source["U"],
                "L": source["L"],
                "l": source["l"],
                "h": source["h"],
                "aux": source["aux"],
                "part": source["part"],
                "def": source["def"],
                "Qt": source_q,
                "formule": f"Qt nette de la ligne {source_idx + 1}",
                "surface": source_q,
            }
            lignes[cible_idx].setdefault("deductions", []).append(deduction)
            mettre_a_jour_quantites(projet)
    
            print(f"✓ {source['designation']} (ligne {source_idx + 1}) déduit de {cible['designation']}.")
            print(f"  {cible['designation']} : {cible_q:.3f} − {source_q:.3f} = "
                  f"{quantite_nette(projet, cible_idx):.3f} {cible['U']}")
    
        def supprimer_ligne(projet):
            idx = choisir_ouvrage(projet, "N° de l'ouvrage à supprimer (0 = annuler) : ")
            if idx is None:
                return
            assurer_ids(projet)
            sup_id = projet["lignes"][idx].get("_id")
            for x in projet.get("lignes", []):
                for d in x.get("deductions", []):
                    if d.get("source_line_id") == sup_id:
                        print("❌ Impossible : cet ouvrage est utilisé comme 'À DÉDUIRE'.")
                        return
            sup = projet["lignes"].pop(idx)
            print(f"✓ Ouvrage supprimé : {sup.get('designation', '')}")
    
        def supprimer_deduction(projet):
            idx = choisir_ouvrage(projet, "N° de l'ouvrage contenant la déduction (0 = annuler) : ")
            if idx is None:
                return
            deductions = projet["lignes"][idx].get("deductions", [])
            if not deductions:
                print("❌ Aucune déduction.")
                return
            print()
            for j, d in enumerate(deductions, 1):
                print(f"  {j} - {d.get('designation', '')}")
            while True:
                try:
                    n = int(input("N° de la déduction à supprimer (0 = annuler) : "))
                    if n == 0:
                        return
                    if 1 <= n <= len(deductions):
                        sup = deductions.pop(n - 1)
                        mettre_a_jour_quantites(projet)
                        print(f"✓ Déduction supprimée : {sup.get('designation', '')}")
                        return
                except ValueError:
                    pass
                print("❌ Numéro invalide.")
    
        # =====================================================
        # AFFICHAGE
        # =====================================================
        def afficher_table_compact(projet, titre, definitif=False):
            lignes = projet.get("lignes", [])
            if console is not None:
                table = Table(
                    title=titre, box=ROUNDED, expand=False,
                    show_lines=False, padding=(0, 1), collapse_padding=True
                )
                table.add_column("N°", justify="center", width=3, no_wrap=True)
                table.add_column("Désignation", justify="left", width=15, overflow="fold")
                table.add_column("NPE", justify="right", width=5, no_wrap=True)
                table.add_column("U", justify="center", width=3, no_wrap=True)
                table.add_column("L", justify="right", width=6, no_wrap=True)
                table.add_column("l", justify="right", width=6, no_wrap=True)
                table.add_column("h", justify="right", width=6, no_wrap=True)
                table.add_column("Qt", justify="right", width=9, no_wrap=True)
                table.add_column("Info", justify="left", width=10, no_wrap=True)
    
                for i, raw in enumerate(lignes, 1):
                    x = normaliser_ligne(raw)
                    if x.get("inclus_dans"):
                        info = "combiné"
                    elif x.get("est_composition"):
                        info = "composé"
                    elif x.get("deductions"):
                        info = f"-{len(x['deductions'])} déd."
                    else:
                        info = ""
    
                    q = quantite_nette(projet, i - 1) if definitif else quantite_brute(projet, i - 1)
                    table.add_row(
                        str(i), str(x["designation"]), str(x["NPE"]), str(x["U"]),
                        str(x["L"]), str(x["l"]), str(x["h"]),
                        f"{q:.3f}", info
                    )
                print(table)
            else:
                entete = (
                    f"{'N°':<4}{'Désignation':<20}{'NPE':>7}{'U':>5}"
                    f"{'L':>8}{'l':>8}{'h':>8}{'Qt':>12}{'Info':>10}"
                )
                print(titre)
                print("-" * len(entete))
                print(entete)
                print("-" * len(entete))
                for i, raw in enumerate(lignes, 1):
                    x = normaliser_ligne(raw)
                    if x.get("inclus_dans"):
                        info = "combiné"
                    elif x.get("est_composition"):
                        info = "composé"
                    elif x.get("deductions"):
                        info = f"-{len(x['deductions'])}"
                    else:
                        info = ""
                    q = quantite_nette(projet, i - 1) if definitif else quantite_brute(projet, i - 1)
                    print(
                        f"{i:<4}{str(x['designation'])[:20]:<20}"
                        f"{str(x['NPE']):>7}{str(x['U']):>5}"
                        f"{str(x['L']):>8}{str(x['l']):>8}{str(x['h']):>8}"
                        f"{q:>12.3f}{info:>10}"
                    )
                print("-" * len(entete))
    
        def afficher_totaux(projet, definitif=False):
            totaux = {}
            for i, raw in enumerate(projet.get("lignes", [])):
                x = normaliser_ligne(raw)
                if x.get("inclus_dans"):
                    continue
                u = x.get("U", "") or "-"
                q = quantite_nette(projet, i) if definitif else quantite_brute(projet, i)
                totaux[u] = totaux.get(u, 0.0) + q
    
            label = "TOTAL DÉFINITIF" if definitif else "TOTAL NON DÉFINITIF"
            print(f"\n📌 {label}")
            if not totaux:
                print("   Aucun total.")
            else:
                for u, q in totaux.items():
                    print(f"   {u:<8} : {q:.3f}")
    
        def afficher_avant_metre(projet):
            lignes = projet.get("lignes", [])
            print()
            self.section(f"AVANT MÉTRÉ — {projet.get('nom', 'Sans nom')}", "📋")
    
            if not lignes:
                print("Aucun ouvrage dans ce projet.")
                return
    
            assurer_ids(projet)
            mettre_a_jour_quantites(projet)
    
            afficher_table_compact(projet, "1) QUANTITÉS NON DÉFINITIVES", definitif=False)
            afficher_totaux(projet, definitif=False)
    
            print()
            afficher_table_compact(projet, "2) RÉSULTATS DÉFINITIFS", definitif=True)
            afficher_totaux(projet, definitif=True)
    
            deductions_existent = any(
                x.get("deductions") for x in projet.get("lignes", [])
            )
            if deductions_existent:
                print("\n📎 DÉDUCTIONS APPLIQUÉES :")
                for i, raw in enumerate(lignes, 1):
                    x = normaliser_ligne(raw)
                    if x.get("deductions"):
                        brut = quantite_brute(projet, i - 1)
                        net = quantite_nette(projet, i - 1)
                        print(f"  [{i}] {x['designation']} : "
                              f"{brut:.3f} − {brut - net:.3f} = {net:.3f} {x['U']}")
                        for d in x["deductions"]:
                            print(f"      ↳ déduit : {d.get('designation','')} "
                                  f"({d.get('Qt','')} {d.get('U','')})")
    
            compositions = [x for x in lignes if x.get("est_composition")]
            if compositions:
                print("\n📎 COMPOSITIONS :")
                for x in compositions:
                    print(f"  • {x['designation']} = {x.get('Qt', 0):.3f} {x.get('U', '')}")
    
        def afficher_detail(projet):
            lignes = projet.get("lignes", [])
            if not lignes:
                print("Aucun ouvrage.")
                return
            print()
            self.section("DÉTAIL DE L'AVANT MÉTRÉ", "🔎")
            for i, raw in enumerate(lignes, 1):
                x = normaliser_ligne(raw)
                print(f"\n[{i}] {x['designation']}")
                print(f"    Forme : {x['forme']}")
                print(f"    NPE={x['NPE']} | U={x['U']} | L={x['L']} | l={x['l']} | h={x['h']}")
                print(f"    Formule : {x['formule']}")
                print(f"    Qt brute = {x.get('Qt', 0)}")
                if x.get("est_composition"):
                    print(f"    Composition de : {x['compose_de']}")
                if x.get("inclus_dans"):
                    print(f"    Inclus dans la composition : {x['inclus_dans']}")
                for j, d in enumerate(x.get("deductions", []), 1):
                    print(f"    À DÉDUIRE {j} → {d.get('designation','')} | "
                          f"Qt = {d.get('Qt','')} {d.get('U','')}")
    
        def exporter_csv(projet):
            lignes = projet.get("lignes", [])
            if not lignes:
                print("❌ Rien à exporter.")
                return
            nom_fichier = "".join(
                c if c.isalnum() or c in "-_" else "_"
                for c in projet.get("nom", "projet")
            )
            chemin = os.path.join(dossier, f"{nom_fichier}_avant_metre.csv")
            try:
                with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f, delimiter=";")
                    writer.writerow(["Projet", projet.get("nom", ""),
                                     "Date", projet.get("date", "")])
                    writer.writerow([])
                    writer.writerow(["N°", "Désignation", "Forme", "NPE", "U",
                                     "L", "l", "h", "Qt", "Formule", "Info"])
                    for i, raw in enumerate(lignes, 1):
                        x = normaliser_ligne(raw)
                        if x.get("inclus_dans"):
                            info = "combiné"
                        elif x.get("est_composition"):
                            info = "composé"
                        elif x.get("deductions"):
                            info = f"-{len(x['deductions'])} déd."
                        else:
                            info = ""
                        writer.writerow([i, x["designation"], x.get("forme", ""),
                                         x["NPE"], x["U"], x["L"], x["l"], x["h"],
                                         x["Qt"], x.get("formule", ""), info])
                        for d in x.get("deductions", []):
                            writer.writerow([
                                "",
                                "  → À DÉDUIRE : " + str(d.get("designation", "")),
                                "", d.get("NPE", ""), d.get("U", ""),
                                d.get("L", ""), d.get("l", ""), d.get("h", ""),
                                d.get("Qt", ""), d.get("formule", ""), ""
                            ])
                print(f"✓ Export CSV créé : {chemin}")
            except OSError as e:
                print(f"❌ Erreur d'export : {e}")
    
        # =====================================================
        # BOUCLE OPTION 9
        # =====================================================
        while True:
            self.clear_screen()
            self.banner()
            self.section("OPTION 9 — AVANT MÉTRÉ D'OUVRAGE", "📋")
            print("1 - Nouveau projet")
            print("2 - Ouvrir un projet enregistré")
            print("3 - Afficher tous les projets")
            print("0 - Retour au menu principal")
            print()
            choix = input("👉 Votre choix : ").strip()
    
            data = charger_donnees()
    
            if choix == "1":
                print()
                nom = input("Nom du projet/ouvrage : ").strip()
                if not nom:
                    print("❌ Nom obligatoire.")
                    self.pause()
                    continue
                client = input("Client (facultatif) : ").strip()
                lieu = input("Lieu du chantier (facultatif) : ").strip()
                projet = {
                    "nom": nom, "client": client, "lieu": lieu,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "lignes": []
                }
    
                while True:
                    self.clear_screen()
                    self.banner()
                    self.section(f"PROJET : {nom}", "🏗️")
                    print(f"Client : {client or '-'}")
                    print(f"Lieu   : {lieu or '-'}")
                    afficher_avant_metre(projet)
                    print()
                    print("1 - Ajouter un ouvrage (m² / m³ / ml / u)")
                    print("2 - À DÉDUIRE (sélectionner la ligne)")
                    print("3 - Modifier un ouvrage")
                    print("4 - Afficher le détail")
                    print("5 - Enregistrer le projet")
                    print("6 - Exporter en CSV")
                    print("7 - Supprimer un ouvrage")
                    print("8 - Supprimer une 'À DÉDUIRE'")
                    print("9 - Multiplier / regrouper des ouvrages")
                    print("0 - Terminer le projet")
                    action = input("👉 Votre choix : ").strip()
    
                    if action == "1":
                        ajouter_ligne(projet); self.pause()
                    elif action == "2":
                        ajouter_deduction(projet); self.pause()
                    elif action == "3":
                        modifier_ligne(projet); self.pause()
                    elif action == "4":
                        afficher_detail(projet); self.pause()
                    elif action == "5":
                        data = [x for x in data if x.get("nom") != projet.get("nom")]
                        data.append(projet)
                        sauvegarder_donnees(data); self.pause()
                    elif action == "6":
                        exporter_csv(projet); self.pause()
                    elif action == "7":
                        supprimer_ligne(projet); self.pause()
                    elif action == "8":
                        supprimer_deduction(projet); self.pause()
                    elif action == "9":
                        multiplier_ouvrages(projet); self.pause()
                    elif action == "0":
                        break
                    else:
                        print("❌ Choix invalide."); self.pause()
    
            elif choix == "2":
                projet = choisir_projet(data)
                if projet is not None:
                    while True:
                        self.clear_screen()
                        self.banner()
                        afficher_avant_metre(projet)
                        print()
                        print("1 - Ajouter un ouvrage (m² / m³ / ml / u)")
                        print("2 - À DÉDUIRE (sélectionner la ligne)")
                        print("3 - Modifier un ouvrage")
                        print("4 - Afficher le détail")
                        print("5 - Enregistrer les modifications")
                        print("6 - Exporter en CSV")
                        print("7 - Supprimer un ouvrage")
                        print("8 - Supprimer une 'À DÉDUIRE'")
                        print("9 - Multiplier / regrouper des ouvrages")
                        print("0 - Retour")
                        action = input("👉 Votre choix : ").strip()
    
                        if action == "1":
                            ajouter_ligne(projet); self.pause()
                        elif action == "2":
                            ajouter_deduction(projet); self.pause()
                        elif action == "3":
                            modifier_ligne(projet); self.pause()
                        elif action == "4":
                            afficher_detail(projet); self.pause()
                        elif action == "5":
                            data = [x for x in data if x.get("nom") != projet.get("nom")]
                            data.append(projet)
                            sauvegarder_donnees(data); self.pause()
                        elif action == "6":
                            exporter_csv(projet); self.pause()
                        elif action == "7":
                            supprimer_ligne(projet); self.pause()
                        elif action == "8":
                            supprimer_deduction(projet); self.pause()
                        elif action == "9":
                            multiplier_ouvrages(projet); self.pause()
                        elif action == "0":
                            break
                        else:
                            print("❌ Choix invalide."); self.pause()
    
            elif choix == "3":
                if not data:
                    print("Aucun projet enregistré.")
                else:
                    if console is not None:
                        table = Table(box=ROUNDED, expand=True)
                        table.add_column("N°", justify="center")
                        table.add_column("Projet")
                        table.add_column("Date")
                        table.add_column("Ouvrages", justify="center")
                        for i, projet in enumerate(data, 1):
                            table.add_row(
                                str(i), str(projet.get("nom", "Sans nom")),
                                str(projet.get("date", "")),
                                str(len(projet.get("lignes", [])))
                            )
                        print(table)
                    else:
                        for i, projet in enumerate(data, 1):
                            print(f"{i}. {projet.get('nom', 'Sans nom')} | "
                                  f"{projet.get('date', '')} | "
                                  f"{len(projet.get('lignes', []))} ouvrages")
                self.pause()
    
            elif choix == "0":
                break
            else:
                print("❌ Choix invalide."); self.pause()

    # =========================================================
    # 12 - DESCENTE DE CHARGES
    # =========================================================
    
    def descente_charge(self):
        """Option 12 — Descente de charges.
    
        Structure similaire aux tableaux 8, 9, 10 :
          • Tableau 8 : Charges permanentes G par niveau
          • Tableau 9 : Surcharges d'exploitation Q par niveau
          • Tableau 10 : Récapitulatif avec ELU et ELS
    
        Le Poids unitaire PU est choisi par SÉLECTION dans une liste :
          • Poids volumiques (kN/m³) si l'élément a une hauteur
          • Charges surfaciques (kN/m²) si l'élément n'a pas de hauteur
        """
    
        dossier = os.path.join(os.path.dirname(os.path.abspath(__file__)), "donnees_btp")
        os.makedirs(dossier, exist_ok=True)
        fichier_json = os.path.join(dossier, "descente_charge.json")
    
        # =====================================================
        # LISTES DE POIDS UNITAIRES PAR DÉFAUT
        # =====================================================
    
        POIDS_VOLUMIQUES = {
            "1":  ("Béton armé", 25.0),
            "2":  ("Béton non armé", 22.0),
            "3":  ("Béton léger", 18.0),
            "4":  ("Béton cyclopéen / moellon + béton", 22.0),
            "5":  ("Acier", 78.5),
            "6":  ("Maçonnerie brique creuse", 13.0),
            "7":  ("Maçonnerie brique pleine", 18.0),
            "8":  ("Moellon / pierre", 19.0),
            "9":  ("Enduit ciment", 22.0),
            "10": ("Enduit plâtre", 15.0),
            "11": ("Mortier de ciment", 20.0),
            "12": ("Bois (résineux)", 6.0),
            "13": ("Bois (feuillus)", 8.0),
            "14": ("Terre / remblai", 18.0),
            "15": ("Sable sec", 16.0),
            "16": ("Gravier", 18.0),
            "17": ("Verre", 25.0),
            "18": ("Autre (saisie manuelle)", None),
        }
    
        CHARGES_SURFACIQUES = {
            "1":  ("Étanchéité (bitume, membrane)", 0.12),
            "2":  ("Étanchéité + protection", 0.20),
            "3":  ("Revêtement carrelage / céramique", 0.60),
            "4":  ("Revêtement marbre / granit", 1.20),
            "5":  ("Revêtement bois / parquet", 0.30),
            "6":  ("Climatisation / ventilation", 1.00),
            "7":  ("Entretien non accessible (toiture)", 1.00),
            "8":  ("Terrasse accessible", 1.50),
            "9":  ("Habitation (Q)", 1.50),
            "10": ("Bureau (Q)", 2.50),
            "11": ("Escalier (Q)", 2.50),
            "12": ("Balcon (Q)", 3.50),
            "13": ("Salle de réunion (Q)", 4.00),
            "14": ("Neige (Madagascar - zone basse)", 0.00),
            "15": ("Autre (saisie manuelle)", None),
        }
    
        # =====================================================
        # CHARGEMENT / SAUVEGARDE
        # =====================================================
        def charger_donnees():
            if not os.path.exists(fichier_json):
                return []
            try:
                with open(fichier_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []
            except (json.JSONDecodeError, OSError):
                print("⚠️ Impossible de lire le fichier.")
                return []
    
        def sauvegarder_donnees(data):
            try:
                with open(fichier_json, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                print(f"✓ Données enregistrées : {fichier_json}")
            except OSError as e:
                print(f"❌ Erreur : {e}")
    
        def valeur_num(v, default=0.0):
            try:
                return float(str(v).replace(",", "."))
            except (TypeError, ValueError):
                return default
    
        # =====================================================
        # CALCUL DE LA CHARGE D'UN ÉLÉMENT
        # =====================================================
        def calc_charge(element):
            """Charge = NPE × L × l × [h] × PU"""
            NPE = valeur_num(element.get("NPE", 1), 1.0)
            L = valeur_num(element.get("L", 0), 0.0)
            l = valeur_num(element.get("l", 0), 0.0)
            h = valeur_num(element.get("h", 0), 0.0)
            PU = valeur_num(element.get("PU", 0), 0.0)
            if h > 0:
                return NPE * L * l * h * PU
            return NPE * L * l * PU
    
        def get_total_G(projet, niveau_idx):
            total = 0.0
            for i in range(niveau_idx + 1):
                for e in projet["niveaux"][i].get("elements_G", []):
                    total += calc_charge(e)
            return total
    
        def get_total_Q(projet, niveau_idx):
            total = 0.0
            for i in range(niveau_idx + 1):
                for e in projet["niveaux"][i].get("elements_Q", []):
                    total += calc_charge(e)
            return total
    
        # =====================================================
        # SÉLECTION DU POIDS UNITAIRE
        # =====================================================
        def choisir_poids_unitaire(avec_hauteur):
            """Menu de sélection pour le poids unitaire."""
            if avec_hauteur:
                print()
                print("📋 POIDS VOLUMIQUES (kN/m³) :")
                print("-" * 70)
                for k, (nom, val) in POIDS_VOLUMIQUES.items():
                    if val is None:
                        print(f"  {k:>2} - {nom}")
                    else:
                        print(f"  {k:>2} - {nom:<40} {val:>6.2f} kN/m³")
                table = POIDS_VOLUMIQUES
                unite_str = "kN/m³"
            else:
                print()
                print("📋 CHARGES SURFACIQUES (kN/m²) :")
                print("-" * 70)
                for k, (nom, val) in CHARGES_SURFACIQUES.items():
                    if val is None:
                        print(f"  {k:>2} - {nom}")
                    else:
                        print(f"  {k:>2} - {nom:<40} {val:>6.2f} kN/m²")
                table = CHARGES_SURFACIQUES
                unite_str = "kN/m²"
    
            while True:
                choix = input(f"\n👉 Votre choix (numéro) : ").strip()
                if choix in table:
                    nom, val = table[choix]
                    if val is None:
                        while True:
                            try:
                                raw = input(f"Valeur manuelle ({unite_str}) : ").strip().replace(",", ".")
                                val = float(raw)
                                if val <= 0:
                                    print("❌ Valeur > 0.")
                                    continue
                                return val, "Autre (manuelle)"
                            except ValueError:
                                print("❌ Nombre invalide.")
                    else:
                        print(f"✓ {nom} : {val:.2f} {unite_str}")
                        return val, nom
                print("❌ Numéro invalide.")
    
        # =====================================================
        # AFFICHAGE TABLEAU 8 (G)
        # =====================================================
        def afficher_tableau_G(projet, niveau_idx):
            niveau = projet["niveaux"][niveau_idx]
            print()
            print(f"═══ TABLEAU 8 : CHARGES PERMANENTES — NIVEAU {niveau_idx+1:02d} ═══")
            print()
            entete = (
                f"{'N°':<4}{'Désignation':<22}{'NPE':>5}"
                f"{'Long.':>9}{'Larg.':>9}{'Haut.':>9}{'P.U.':>9}{'Charge':>11}"
            )
            print(entete)
            print("-" * len(entete))
    
            if niveau_idx > 0:
                venant = get_total_G(projet, niveau_idx - 1)
                label = f"Venant niveau {niveau_idx:02d}"
                print(f"{'':<4}{label:<22}{'':>5}{'':>9}{'':>9}{'':>9}{'':>9}{venant:>11.3f}")
                print()
    
            for i, e in enumerate(niveau.get("elements_G", []), 1):
                charge = calc_charge(e)
                h_val = valeur_num(e.get("h", 0), 0)
                h_str = f"{h_val:.3f}" if h_val > 0 else ""
                print(
                    f"{i:<4}{str(e['designation'])[:22]:<22}"
                    f"{valeur_num(e['NPE'], 1):>5.0f}"
                    f"{valeur_num(e['L'], 0):>9.3f}"
                    f"{valeur_num(e['l'], 0):>9.3f}"
                    f"{h_str:>9}"
                    f"{valeur_num(e['PU'], 0):>9.3f}"
                    f"{charge:>11.3f}"
                )
    
            print("-" * len(entete))
            total = get_total_G(projet, niveau_idx)
            print(f"{'TOTAL NIVEAU ' + str(niveau_idx+1).zfill(2):<66}{total:>11.3f}")
    
        # =====================================================
        # AFFICHAGE TABLEAU 9 (Q)
        # =====================================================
        def afficher_tableau_Q(projet, niveau_idx):
            niveau = projet["niveaux"][niveau_idx]
            print()
            print(f"═══ TABLEAU 9 : SURCHARGES D'EXPLOITATION — NIVEAU {niveau_idx+1:02d} ═══")
            print()
            entete = (
                f"{'N°':<4}{'Désignation':<22}{'NPE':>5}"
                f"{'Long.':>9}{'Larg.':>9}{'Haut.':>9}{'P.U.':>9}{'Charge':>11}"
            )
            print(entete)
            print("-" * len(entete))
    
            if niveau_idx > 0:
                venant = get_total_Q(projet, niveau_idx - 1)
                label = f"Venant niveau {niveau_idx:02d}"
                print(f"{'':<4}{label:<22}{'':>5}{'':>9}{'':>9}{'':>9}{'':>9}{venant:>11.3f}")
                print()
    
            for i, e in enumerate(niveau.get("elements_Q", []), 1):
                charge = calc_charge(e)
                h_val = valeur_num(e.get("h", 0), 0)
                h_str = f"{h_val:.3f}" if h_val > 0 else ""
                print(
                    f"{i:<4}{str(e['designation'])[:22]:<22}"
                    f"{valeur_num(e['NPE'], 1):>5.0f}"
                    f"{valeur_num(e['L'], 0):>9.3f}"
                    f"{valeur_num(e['l'], 0):>9.3f}"
                    f"{h_str:>9}"
                    f"{valeur_num(e['PU'], 0):>9.3f}"
                    f"{charge:>11.3f}"
                )
    
            print("-" * len(entete))
            total = get_total_Q(projet, niveau_idx)
            print(f"{'TOTAL NIVEAU ' + str(niveau_idx+1).zfill(2):<66}{total:>11.3f}")
    
        # =====================================================
        # AFFICHAGE TABLEAU 10 (RÉCAPITULATIF)
        # =====================================================
        def afficher_recapitulatif(projet):
            print()
            print("═══ TABLEAU 10 : RÉCAPITULATIF DE LA DESCENTE DES CHARGES ═══")
            print()
            entete = (
                f"{'Niveau':<14}{'G':>12}{'Q':>12}"
                f"{'E.L.U.':>14}{'E.L.S.':>14}"
            )
            print(entete)
            print(f"{'':<14}{'(kN)':>12}{'(kN)':>12}"
                  f"{'Nu=1.35G+1.5Q':>14}{'Nser=G+Q':>14}")
            print("-" * len(entete))
    
            G_last = 0.0
            Q_last = 0.0
            for i in range(len(projet["niveaux"])):
                G = get_total_G(projet, i)
                Q = get_total_Q(projet, i)
                ELU = 1.35 * G + 1.5 * Q
                ELS = G + Q
                print(f"{'Niveau ' + str(i+1).zfill(2):<14}{G:>12.3f}{Q:>12.3f}"
                      f"{ELU:>14.3f}{ELS:>14.3f}")
                G_last = G
                Q_last = Q
    
            maj_G = G_last * 0.10
            maj_Q = Q_last * 0.10
            maj_ELU = 1.35 * maj_G + 1.5 * maj_Q
            maj_ELS = maj_G + maj_Q
            print(f"{'Majoration 10%':<14}{maj_G:>12.3f}{maj_Q:>12.3f}"
                  f"{maj_ELU:>14.3f}{maj_ELS:>14.3f}")
    
            tot_G = G_last + maj_G
            tot_Q = Q_last + maj_Q
            tot_ELU = 1.35 * tot_G + 1.5 * tot_Q
            tot_ELS = tot_G + tot_Q
            print("-" * len(entete))
            print(f"{'Total':<14}{tot_G:>12.3f}{tot_Q:>12.3f}"
                  f"{tot_ELU:>14.3f}{tot_ELS:>14.3f}")
            print("=" * len(entete))
    
            print()
            print("📌 RÉSULTAT FINAL POUR LE DIMENSIONNEMENT :")
            print(f"   G total   = {tot_G:.3f} kN")
            print(f"   Q total   = {tot_Q:.3f} kN")
            print(f"   Nu (ELU)  = {tot_ELU:.3f} kN  → à utiliser pour BAEL ELU")
            print(f"   Nser (ELS)= {tot_ELS:.3f} kN  → à utiliser pour BAEL ELS")
    
        # =====================================================
        # AJOUT D'ÉLÉMENT
        # =====================================================
        def ajouter_element(projet, niveau_idx, type_charge):
            print()
            self.section(
                f"AJOUTER UN ÉLÉMENT ({type_charge}) — Niveau {niveau_idx+1:02d}", "➕"
            )
            designation = input("Désignation : ").strip()
            if not designation:
                print("❌ Désignation obligatoire.")
                return
    
            NPE = self.lire_float("NPE (nombre d'éléments identiques) : ")
            L = self.lire_float("Longueur L (m) : ")
            l = self.lire_float("Largeur l (m) : ")
    
            raw_h = input("Hauteur h (m) [Entrée si non applicable] : ").strip().replace(",", ".")
            if raw_h == "":
                h = 0.0
            else:
                try:
                    h = float(raw_h)
                    if h < 0:
                        print("❌ Hauteur ≥ 0.")
                        return
                except ValueError:
                    print("❌ Hauteur invalide.")
                    return
    
            # =================================================
            # SÉLECTION DU POIDS UNITAIRE
            # =================================================
            avec_hauteur = (h > 0)
    
            print()
            if avec_hauteur:
                print("Formule : Charge = NPE × L × l × h × PU")
                print("Sélection du POIDS VOLUMIQUE (kN/m³)")
            else:
                print("Formule : Charge = NPE × L × l × PU")
                print("Sélection de la CHARGE SURFACIQUE (kN/m²)")
    
            PU, nom_PU = choisir_poids_unitaire(avec_hauteur)
    
            element = {
                "designation": designation,
                "NPE": NPE, "L": L, "l": l, "h": h, "PU": PU,
                "unite_PU": "kN/m³" if avec_hauteur else "kN/m²",
                "nom_PU": nom_PU,
            }
    
            cle = "elements_G" if type_charge == "G" else "elements_Q"
            projet["niveaux"][niveau_idx].setdefault(cle, []).append(element)
    
            charge = calc_charge(element)
            print()
            print(f"✓ {designation} : {charge:.3f} kN")
            if avec_hauteur:
                print(f"  Formule : {NPE} × {L} × {l} × {h} × {PU} = {charge:.3f}")
            else:
                print(f"  Formule : {NPE} × {L} × {l} × {PU} = {charge:.3f}")
            print(f"  PU utilisé : {PU:.2f} ({nom_PU})")
    
        # =====================================================
        # AJOUT DE NIVEAU
        # =====================================================
        def ajouter_niveau(projet):
            n = len(projet["niveaux"]) + 1
            projet["niveaux"].append({
                "numero": n,
                "elements_G": [],
                "elements_Q": [],
            })
            print(f"✓ Niveau {n:02d} ajouté.")
    
        # =====================================================
        # SUPPRESSION D'ÉLÉMENT
        # =====================================================
        def supprimer_element(projet):
            if not projet["niveaux"]:
                print("❌ Aucun niveau.")
                return
            print("\nNiveaux disponibles :")
            for i in range(len(projet["niveaux"])):
                print(f"  {i+1} - Niveau {i+1:02d}")
            try:
                niv = int(input("👉 Numéro du niveau : ")) - 1
                if niv < 0 or niv >= len(projet["niveaux"]):
                    return
            except ValueError:
                return
    
            niveau = projet["niveaux"][niv]
            print(f"\n  G - Éléments G ({len(niveau.get('elements_G', []))})")
            print(f"  Q - Éléments Q ({len(niveau.get('elements_Q', []))})")
            typ = input("👉 Type (G/Q) : ").strip().upper()
            if typ not in ("G", "Q"):
                return
            cle = "elements_G" if typ == "G" else "elements_Q"
            elems = niveau.get(cle, [])
            if not elems:
                print("❌ Aucun élément.")
                return
            for i, e in enumerate(elems, 1):
                print(f"  {i} - {e['designation']}")
            try:
                idx = int(input("👉 Numéro à supprimer : ")) - 1
                if 0 <= idx < len(elems):
                    sup = elems.pop(idx)
                    print(f"✓ Supprimé : {sup['designation']}")
            except ValueError:
                pass
    
        # =====================================================
        # EXPORT CSV
        # =====================================================
        def exporter_csv(projet):
            nom_fichier = "".join(
                c if c.isalnum() or c in "-_" else "_"
                for c in projet.get("nom", "projet")
            )
            chemin = os.path.join(dossier, f"{nom_fichier}_descente_charge.csv")
            try:
                with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f, delimiter=";")
                    writer.writerow(["Projet", projet.get("nom", ""),
                                     "Date", projet.get("date", "")])
                    writer.writerow([])
    
                    writer.writerow(["TABLEAU 8 : CHARGES PERMANENTES G"])
                    writer.writerow(["N°", "Désignation", "NPE", "L (m)", "l (m)",
                                     "h (m)", "P.U.", "Nom PU", "Charge (kN)"])
                    for niv_idx, niveau in enumerate(projet["niveaux"]):
                        writer.writerow([f"Niveau {niv_idx+1:02d}"])
                        for i, e in enumerate(niveau.get("elements_G", []), 1):
                            writer.writerow([
                                i, e['designation'], e['NPE'], e['L'], e['l'],
                                e.get('h', 0), e['PU'], e.get('nom_PU', ''),
                                round(calc_charge(e), 3)
                            ])
                        writer.writerow(["", "", "", "", "", "", "",
                                         "Total G cumulé",
                                         round(get_total_G(projet, niv_idx), 3)])
                    writer.writerow([])
    
                    writer.writerow(["TABLEAU 9 : SURCHARGES D'EXPLOITATION Q"])
                    writer.writerow(["N°", "Désignation", "NPE", "L (m)", "l (m)",
                                     "h (m)", "P.U.", "Nom PU", "Charge (kN)"])
                    for niv_idx, niveau in enumerate(projet["niveaux"]):
                        writer.writerow([f"Niveau {niv_idx+1:02d}"])
                        for i, e in enumerate(niveau.get("elements_Q", []), 1):
                            writer.writerow([
                                i, e['designation'], e['NPE'], e['L'], e['l'],
                                e.get('h', 0), e['PU'], e.get('nom_PU', ''),
                                round(calc_charge(e), 3)
                            ])
                        writer.writerow(["", "", "", "", "", "", "",
                                         "Total Q cumulé",
                                         round(get_total_Q(projet, niv_idx), 3)])
                    writer.writerow([])
    
                    writer.writerow(["TABLEAU 10 : RÉCAPITULATIF"])
                    writer.writerow(["Niveau", "G (kN)", "Q (kN)",
                                     "Nu = 1.35G+1.5Q", "Nser = G+Q"])
                    for i in range(len(projet["niveaux"])):
                        G = get_total_G(projet, i)
                        Q = get_total_Q(projet, i)
                        writer.writerow([
                            f"Niveau {i+1:02d}", round(G, 3), round(Q, 3),
                            round(1.35 * G + 1.5 * Q, 3), round(G + Q, 3)
                        ])
                    if projet["niveaux"]:
                        G_last = get_total_G(projet, len(projet["niveaux"]) - 1)
                        Q_last = get_total_Q(projet, len(projet["niveaux"]) - 1)
                        maj_G = G_last * 0.1
                        maj_Q = Q_last * 0.1
                        writer.writerow([
                            "Majoration 10%", round(maj_G, 3), round(maj_Q, 3),
                            round(1.35 * maj_G + 1.5 * maj_Q, 3),
                            round(maj_G + maj_Q, 3)
                        ])
                        tot_G = G_last + maj_G
                        tot_Q = Q_last + maj_Q
                        writer.writerow([
                            "Total", round(tot_G, 3), round(tot_Q, 3),
                            round(1.35 * tot_G + 1.5 * tot_Q, 3),
                            round(tot_G + tot_Q, 3)
                        ])
                print(f"✓ Export CSV créé : {chemin}")
            except OSError as e:
                print(f"❌ Erreur d'export : {e}")
    
        # =====================================================
        # SOUS-MENU D'UN PROJET
        # =====================================================
        def menu_projet(projet, data):
            while True:
                self.clear_screen()
                self.banner()
                self.section(f"PROJET : {projet.get('nom', '')}", "🏗️")
                print(f"Client : {projet.get('client') or '-'}")
                print(f"Lieu   : {projet.get('lieu') or '-'}")
                print(f"Niveaux : {len(projet.get('niveaux', []))}")
                print()
                print("1 - Ajouter un niveau")
                print("2 - Ajouter un élément G (charge permanente)")
                print("3 - Ajouter un élément Q (surcharge d'exploitation)")
                print("4 - Afficher Tableau 8 (Charges permanentes G)")
                print("5 - Afficher Tableau 9 (Surcharges Q)")
                print("6 - Afficher Tableau 10 (Récapitulatif ELU/ELS)")
                print("7 - Enregistrer le projet")
                print("8 - Exporter en CSV")
                print("9 - Supprimer un élément")
                print("0 - Retour")
                action = input("👉 Votre choix : ").strip()
    
                if action == "1":
                    ajouter_niveau(projet); self.pause()
                elif action in ("2", "3"):
                    if not projet["niveaux"]:
                        print("❌ Ajoutez d'abord un niveau.")
                        self.pause()
                        continue
                    print("\nNiveaux disponibles :")
                    for i in range(len(projet["niveaux"])):
                        print(f"  {i+1} - Niveau {i+1:02d}")
                    try:
                        niv = int(input("👉 Numéro du niveau : ")) - 1
                        if 0 <= niv < len(projet["niveaux"]):
                            ajouter_element(projet, niv,
                                            "G" if action == "2" else "Q")
                    except ValueError:
                        pass
                    self.pause()
                elif action == "4":
                    for i in range(len(projet["niveaux"])):
                        afficher_tableau_G(projet, i)
                    self.pause()
                elif action == "5":
                    for i in range(len(projet["niveaux"])):
                        afficher_tableau_Q(projet, i)
                    self.pause()
                elif action == "6":
                    afficher_recapitulatif(projet)
                    self.pause()
                elif action == "7":
                    data = [x for x in data if x.get("nom") != projet.get("nom")]
                    data.append(projet)
                    sauvegarder_donnees(data); self.pause()
                elif action == "8":
                    exporter_csv(projet); self.pause()
                elif action == "9":
                    supprimer_element(projet); self.pause()
                elif action == "0":
                    break
                else:
                    print("❌ Choix invalide."); self.pause()
    
        # =====================================================
        # BOUCLE PRINCIPALE OPTION 12
        # =====================================================
        while True:
            self.clear_screen()
            self.banner()
            self.section("OPTION 12 — DESCENTE DE CHARGES", "📊")
            print("1 - Nouveau projet")
            print("2 - Ouvrir un projet enregistré")
            print("3 - Afficher tous les projets")
            print("0 - Retour au menu principal")
            print()
            choix = input("👉 Votre choix : ").strip()
    
            data = charger_donnees()
    
            if choix == "1":
                print()
                nom = input("Nom du projet : ").strip()
                if not nom:
                    print("❌ Nom obligatoire.")
                    self.pause()
                    continue
                client = input("Client (facultatif) : ").strip()
                lieu = input("Lieu du chantier (facultatif) : ").strip()
                projet = {
                    "nom": nom, "client": client, "lieu": lieu,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "niveaux": [],
                }
                projet["niveaux"].append({
                    "numero": 1, "elements_G": [], "elements_Q": []
                })
                print("✓ Niveau 01 ajouté automatiquement.")
                menu_projet(projet, data)
    
            elif choix == "2":
                if not data:
                    print("Aucun projet enregistré.")
                    self.pause()
                    continue
                print()
                for i, p in enumerate(data, 1):
                    n_niv = len(p.get("niveaux", []))
                    print(f"  {i} - {p.get('nom', 'Sans nom')} "
                          f"({n_niv} niveaux) | {p.get('date', '')}")
                try:
                    idx = int(input("👉 Numéro du projet : ")) - 1
                    if idx < 0 or idx >= len(data):
                        continue
                except ValueError:
                    continue
                projet = data[idx]
                for niv in projet.get("niveaux", []):
                    niv.setdefault("elements_G", [])
                    niv.setdefault("elements_Q", [])
                menu_projet(projet, data)
    
            elif choix == "3":
                if not data:
                    print("Aucun projet.")
                else:
                    for i, p in enumerate(data, 1):
                        n_niv = len(p.get("niveaux", []))
                        print(f"  {i} - {p.get('nom', '')} | "
                              f"{p.get('date', '')} | {n_niv} niveaux")
                self.pause()
    
            elif choix == "0":
                break
            else:
                print("❌ Choix invalide."); self.pause()

    def effet_vent(self):
        """Calcul complet de l'effet du vent selon les Règles NV 65.
    
        Coefficients calculés :
          • q10 : pression dynamique de base (zonage Madagascar)
          • Kh  : effet de hauteur          (NV 65 R-III-1.241)
          • Cs  : effet de site             (NV 65 R-III-1.242)
          • Cm  : effet de masque           (NV 65 R-III-1.243)
          • δ   : effet de dimension        (NV 65 R-III-2)
          • β   : majoration dynamique      (NV 65 R-III-1.511)
          • γ₀  : coefficient de forme      (NV 65 R-III-5)
          • Ce  : coefficient de pression extérieure
          • Ci  : coefficient de pression intérieure
          • Ct  : coefficient global de traînée
        """
    
        # =====================================================
        # FONCTIONS AUXILIAIRES
        # =====================================================
    
        def ask_float(message, default=None, minimum=0.0, strict=True):
            while True:
                suffix = f" [{default}]" if default is not None else ""
                raw = input(f"{message}{suffix} : ").strip().replace(",", ".")
                if raw == "" and default is not None:
                    return float(default)
                try:
                    value = float(raw)
                    if strict and value <= minimum:
                        print(f"❌ La valeur doit être > {minimum}.")
                        continue
                    if not strict and value < minimum:
                        print(f"❌ La valeur doit être ≥ {minimum}.")
                        continue
                    return value
                except ValueError:
                    print("❌ Entrez un nombre valide.")
    
        def ask_int(message, default=1, minimum=1):
            while True:
                raw = input(f"{message} [{default}] : ").strip()
                if raw == "":
                    return int(default)
                try:
                    value = int(raw)
                    if value < minimum:
                        print(f"❌ Minimum = {minimum}.")
                        continue
                    return value
                except ValueError:
                    print("❌ Entrez un entier valide.")
    
        def section_panel(numero, titre):
            if console is None:
                print(f"\n{'='*76}\n{numero} - {titre}\n{'='*76}")
                return
            console.print()
            console.print(
                Panel(
                    Text(f"{numero} - {titre}", style="bold bright_yellow"),
                    border_style="bright_cyan",
                    box=HEAVY,
                    padding=(0, 1),
                )
            )
    
        def formula_panel(titre, formule, application="", resultat=""):
            if console is None:
                print(f"[FORMULE] {titre}")
                print(f"  {formule}")
                if application:
                    print(f"  Application : {application}")
                if resultat:
                    print(f"  Résultat : {resultat}")
                return
            body = Text()
            body.append(f"{formule}\n", style="bold bright_white")
            if application:
                body.append(f"{application}\n", style="bright_cyan")
            if resultat:
                body.append(f"→ {resultat}", style="bold bright_green")
            console.print(
                Panel(
                    body,
                    title=f"📐 {titre}",
                    title_align="left",
                    border_style="bright_blue",
                    box=ROUNDED,
                    padding=(0, 1),
                )
            )
    
        def check_line(label, ok, detail=""):
            if console is None:
                print(f"{'✓' if ok else '✗'} {label} {detail}")
                return
            style = "bold bright_green" if ok else "bold bright_red"
            symbol = "✓" if ok else "✗"
            t = Text()
            t.append(f"{symbol} {label}", style=style)
            if detail:
                t.append(f" — {detail}", style="bright_white")
            console.print(t)
    
        def result_panel(titre, lignes):
            if console is None:
                print(titre)
                for line in lignes:
                    print(line)
                return
            body = Text()
            for i, line in enumerate(lignes):
                if i:
                    body.append("\n")
                body.append(str(line), style="bright_white")
            console.print(Panel(body, title=titre, border_style="bright_green",
                                box=DOUBLE, padding=(0, 1)))
    
        # =====================================================
        # 1. COEFFICIENT β — MAJORATION DYNAMIQUE
        #    NV 65 R-III-1.511 : β = θ × (1 + ξ × τ) ≥ 1
        # =====================================================
    
        def calcul_beta(H, D):
            """Coefficient de majoration dynamique β.
    
            β = θ × (1 + ξ × τ) ≥ 1
            avec :
              T = période fondamentale ≈ 0.09 × H / √D
              ξ = coefficient de réponse (abaque R-III-3)
              τ = coefficient de pulsation (abaque R-III-4)
              θ = coefficient global (fonction du type de construction)
            """
            # Période fondamentale
            if D > 0:
                T = 0.09 * H / math.sqrt(D)
            else:
                T = 0.5
    
            # ξ (coefficient de réponse) — approximation de l'abaque R-III-3
            # pour un bâtiment à densité normale de parois
            if T <= 0.1:
                xi = 0.0
            elif T <= 0.5:
                xi = 0.12 + (0.15 - 0.12) * (T - 0.1253) / (0.5 - 0.1253)
                xi = max(0.0, min(xi, 0.5))
            elif T <= 1.0:
                xi = 0.5
            else:
                xi = 0.5
    
            # τ (coefficient de pulsation) — approximation de l'abaque R-III-4
            if H <= 10:
                tau = 0.20
            elif H <= 30:
                tau = 0.20 + (0.324 - 0.20) * (H - 10) / 20
            elif H <= 60:
                tau = 0.324 + (0.35 - 0.324) * (H - 30) / 30
            else:
                tau = 0.35
    
            # θ (coefficient global)
            # Pour constructions prismatiques (bâtiments courants) : θ = 1
            # Pour les autres : θ = 0.70 pour HS ≤ 30 m
            #                   θ = 0.70 + 0.01(HS−30) pour 30 < HS < 60 m
            #                   θ = 1 pour HS ≥ 60 m
            if H <= 30:
                theta = 0.70
            elif H < 60:
                theta = 0.70 + 0.01 * (H - 30)
            else:
                theta = 1.0
    
            beta = theta * (1.0 + xi * tau)
            return max(beta, 1.0), T, xi, tau, theta
    
        # =====================================================
        # 2. COEFFICIENT γ₀ — FORME (NV 65 R-III-5)
        # =====================================================
    
        def calcul_gamma0(H, a, b):
            """Coefficient de forme γ₀ (abaque R-III-5).
    
            γ₀ est lu sur l'abaque R-III-5 en fonction de :
              λ_a = H / a
              λ_b = H / b
            avec a > b.
            """
            lambda_a = H / a if a > 0 else 0
            lambda_b = H / b if b > 0 else 0
    
            # Approximation de l'abaque R-III-5
            # Pour λ < 0.5 : γ₀ = 1
            # Pour λ > 0.5 : γ₀ augmente progressivement
            if lambda_a <= 0.5 and lambda_b <= 0.5:
                return 1.0, lambda_a, lambda_b
            elif lambda_a <= 1.0 and lambda_b <= 1.0:
                # Valeurs indicatives (abaque R-III-5)
                gamma0 = 1.0 + 0.05 * max(lambda_a, lambda_b)
            else:
                gamma0 = 1.0 + 0.05 * min(max(lambda_a, lambda_b), 2.0)
            return round(gamma0, 3), lambda_a, lambda_b
    
        # =====================================================
        # 3. COEFFICIENT δ — EFFET DE DIMENSION
        #    NV 65 R-III-2 : δ = -0.130 × log(x) + 0.961
        #    avec x = plus grande dimension (H ou a/b)
        # =====================================================
    
        def calcul_delta(H, dimension):
            """Coefficient de réduction δ (NV 65 R-III-2).
    
            δ dépend de la plus grande dimension (horizontale ou verticale)
            de la surface offerte au vent.
            """
            x = max(H, dimension)
            if x <= 0.5:
                return 1.0
            delta = -0.130 * math.log10(x) + 0.961
            return max(0.0, min(delta, 1.0))
    
        while True:
    
            self.clear_screen()
            self.banner()
    
            print("=" * 70)
            print(" " * 17 + "CALCUL COMPLET DE L'EFFET DU VENT")
            print("=" * 70)
            print()
            print("RÉFÉRENTIEL : Règles NV 65 modifiées 1999")
            print("+ Circulaire malagache 010/MTP/DGE/DAUH/88")
            print()
    
            # =================================================
            # 1 - DONNÉES DU PROJET
            # =================================================
    
            section_panel("1", "DONNÉES DU PROJET")
            a = ask_float("Largeur de la façade a (m)", 11.0, 0.001, False)
            b = ask_float("Largeur de la façade b (m)", 9.0, 0.001, False)
            H = ask_float("Hauteur totale H (m)", 15.4, 0.001, False)
    
            # =================================================
            # 2 - ZONAGE (q10)
            # =================================================
    
            section_panel("2", "PRESSION DYNAMIQUE DE BASE q10")
            print()
            print("1 - Hauts Plateaux : 50 / 87.5 kgf/m²")
            print("2 - Côte          : 143 / 250 kgf/m²")
            print("3 - Valeurs personnalisées")
            zone_choix = input("👉 Choisir la zone (1/2/3) [1] : ").strip()
    
            if zone_choix == "2":
                qb_normal, qb_extreme, zone_nom = 143.0, 250.0, "Côte"
            elif zone_choix == "3":
                qb_normal = ask_float("q10 normal (kgf/m²)", 50.0, 0.0)
                qb_extreme = ask_float("q10 extrême (kgf/m²)", 87.5, 0.0)
                zone_nom = "Personnalisée"
            else:
                qb_normal, qb_extreme, zone_nom = 50.0, 87.5, "Hauts Plateaux"
    
            # =================================================
            # 3 - SITE ET MASQUE
            # =================================================
    
            section_panel("3", "COEFFICIENTS DE SITE ET DE MASQUE")
            print()
            print("Nature du site :")
            print("1 - Protégé  → Cs = 0.80")
            print("2 - Normal   → Cs = 1.00")
            print("3 - Exposé   → Cs dépend de la zone")
            site_choix = input("👉 Choisir le site (1/2/3) [2] : ").strip()
    
            if site_choix == "1":
                Cs = 0.80
                site_nom = "Protégé"
            elif site_choix == "3":
                Cs = 1.20 if zone_choix == "2" else 1.25
                site_nom = "Exposé"
            else:
                Cs = 1.00
                site_nom = "Normal"
    
            masque = input("Bâtiment masqué ? (1=Oui / 2=Non) [2] : ").strip()
            if masque == "1":
                Cm = ask_float("Coefficient de masque Cm", 1.00, 0.0)
                masque_nom = f"Oui (Cm = {Cm:.3f})"
            else:
                Cm = 1.00
                masque_nom = "Non (Cm = 1.00)"
    
            # =================================================
            # 4 - EFFET DE HAUTEUR (Kh)
            # =================================================
    
            section_panel("4", "EFFET DE HAUTEUR Kh")
            Kh = 2.5 * (H + 18.0) / (H + 60.0)
            formula_panel(
                "Effet de hauteur NV 65 R-III-1.241",
                "Kh = 2.5 × (H + 18) / (H + 60)",
                f"Kh = 2.5 × ({H:.3f} + 18) / ({H:.3f} + 60)",
                f"Kh = {Kh:.4f}"
            )
    
            # =================================================
            # 5 - EFFET DE DIMENSION (δ)
            # =================================================
    
            section_panel("5", "EFFET DE DIMENSION δ")
            delta_a = calcul_delta(H, a)
            delta_b = calcul_delta(H, b)
            formula_panel(
                "Effet de dimension NV 65 R-III-2",
                "δ = -0.130 × log(x) + 0.961",
                f"x_a = max({H:.2f} ; {a:.2f}) = {max(H, a):.2f} m",
                f"δ_a = {delta_a:.4f}"
            )
            formula_panel(
                "",
                f"x_b = max({H:.2f} ; {b:.2f}) = {max(H, b):.2f} m",
                "",
                f"δ_b = {delta_b:.4f}"
            )
    
            # =================================================
            # 6 - COEFFICIENT β — MAJORATION DYNAMIQUE
            # =================================================
    
            section_panel("6", "COEFFICIENT β — MAJORATION DYNAMIQUE")
            beta_a, T_a, xi_a, tau_a, theta_a = calcul_beta(H, a)
            beta_b, T_b, xi_b, tau_b, theta_b = calcul_beta(H, b)
    
            formula_panel(
                "Coefficient β (NV 65 R-III-1.511)",
                "β = θ × (1 + ξ × τ) ≥ 1",
                f"T_a = 0.09 × {H:.2f} / √{a:.2f} = {T_a:.4f} s",
                f"β_a = {beta_a:.4f}"
            )
            formula_panel(
                "",
                f"T_b = 0.09 × {H:.2f} / √{b:.2f} = {T_b:.4f} s",
                f"β_b = {beta_b:.4f}"
            )
            print(f"  ξ_a = {xi_a:.4f} ; τ_a = {tau_a:.4f} ; θ_a = {theta_a:.4f}")
            print(f"  ξ_b = {xi_b:.4f} ; τ_b = {tau_b:.4f} ; θ_b = {theta_b:.4f}")
    
            # =================================================
            # 7 - COEFFICIENT γ₀ — FORME
            # =================================================
    
            section_panel("7", "COEFFICIENT γ₀ — FORME")
            gamma0_a, lambda_a, lambda_b = calcul_gamma0(H, a, b)
            formula_panel(
                "Coefficient γ₀ (NV 65 R-III-5)",
                "λ_a = H/a ; λ_b = H/b",
                f"λ_a = {H:.2f}/{a:.2f} = {lambda_a:.3f}",
                f"γ₀ = {gamma0_a:.3f}"
            )
            print(f"  λ_b = {H:.2f}/{b:.2f} = {lambda_b:.3f}")
    
            # =================================================
            # 8 - PRESSION DYNAMIQUE CORRIGÉE
            # =================================================
    
            section_panel("8", "PRESSION DYNAMIQUE CORRIGÉE")
    
            # Pression dynamique de base corrigée
            # qd = q10 × Kh × Cs × Cm × δ × β
            qd_a_n = qb_normal * Kh * Cs * Cm * delta_a * beta_a
            qd_b_n = qb_normal * Kh * Cs * Cm * delta_b * beta_b
            qd_a_e = qb_extreme * Kh * Cs * Cm * delta_a * beta_a
            qd_b_e = qb_extreme * Kh * Cs * Cm * delta_b * beta_b
    
            # Limite NV65 (zone 1-4) : 30 / 52.5 daN/m²
            qd_a_n = max(qd_a_n, 30.0)
            qd_b_n = max(qd_b_n, 30.0)
            qd_a_e = max(qd_a_e, 52.5)
            qd_b_e = max(qd_b_e, 52.5)
    
            conv = 0.00980665  # kgf/m² -> kN/m²
    
            formula_panel(
                "Pression dynamique corrigée",
                "qd = q10 × Kh × Cs × Cm × δ × β",
                f"qd_a,n = {qb_normal:.1f} × {Kh:.4f} × {Cs:.2f} × {Cm:.2f} × {delta_a:.4f} × {beta_a:.4f}",
                f"qd_a,n = {qd_a_n:.3f} kgf/m² = {qd_a_n*conv:.3f} kN/m²"
            )
            print(f"  qd_b,n = {qd_b_n:.3f} kgf/m² = {qd_b_n*conv:.3f} kN/m²")
            print(f"  qd_a,e = {qd_a_e:.3f} kgf/m² = {qd_a_e*conv:.3f} kN/m²")
            print(f"  qd_b,e = {qd_b_e:.3f} kgf/m² = {qd_b_e*conv:.3f} kN/m²")
    
            # =================================================
            # 9 - ACTIONS SUR LES FAÇADES
            # =================================================
    
            section_panel("9", "ACTIONS SUR LES FAÇADES")
    
            # Coefficients de pression extérieure
            Ce_face = +0.8                           # face au vent
            Ce_sous = -(1.3 * gamma0_a - 0.8)       # sous le vent (R-III-6)
            Ci = +0.3                                # construction fermée
    
            # Coefficients résultants (NV 65 R-III-6)
            Cr_pression = Ce_face - (-Ci)            # 0.8 - (-0.3) = 1.1
            Cr_succion = Ce_sous - Ci                 # (-0.5) - 0.3 = -0.8
    
            print(f"  Ce (face au vent)     = {Ce_face:+.2f}")
            print(f"  Ce (sous le vent)     = {Ce_sous:+.2f}")
            print(f"  Ci (intérieur)        = {Ci:+.2f}")
            print(f"  Cr (pression)         = {Cr_pression:+.2f}")
            print(f"  Cr (succion)          = {Cr_succion:+.2f}")
    
            # Surfaces offertes au vent
            Sa = a * H
            Sb = b * H
    
            # Forces
            Fa_n = qd_a_n * conv * Sa * abs(Cr_pression) * beta_a
            Fb_n = qd_b_n * conv * Sb * abs(Cr_pression) * beta_b
            Fa_e = qd_a_e * conv * Sa * abs(Cr_pression) * beta_a
            Fb_e = qd_b_e * conv * Sb * abs(Cr_pression) * beta_b
    
            # Moments de renversement
            Ma_n = Fa_n * H / 2.0
            Mb_n = Fb_n * H / 2.0
            Ma_e = Fa_e * H / 2.0
            Mb_e = Fb_e * H / 2.0
    
            print()
            print(f"  Surface façade a = {Sa:.3f} m²")
            print(f"  Surface façade b = {Sb:.3f} m²")
            print()
            print(f"  F pression normale  a = {Fa_n:.3f} kN")
            print(f"  F pression normale  b = {Fb_n:.3f} kN")
            print(f"  F pression extrême  a = {Fa_e:.3f} kN")
            print(f"  F pression extrême  b = {Fb_e:.3f} kN")
            print()
            print(f"  M renversement normal  a = {Ma_n:.3f} kN.m")
            print(f"  M renversement normal  b = {Mb_n:.3f} kN.m")
            print(f"  M renversement extrême  a = {Ma_e:.3f} kN.m")
            print(f"  M renversement extrême  b = {Mb_e:.3f} kN.m")
    
            # =================================================
            # 10 - TOITURE
            # =================================================
    
            section_panel("10", "TOITURE")
            St = a * b
            print(f"  Surface projetée = {St:.3f} m²")
            print("  Les coefficients de pression de toiture dépendent de la pente,")
            print("  de la forme, du sens du vent et des zones de rive.")
            cr_toit = ask_float("Cr toiture (valeur signée)", -1.00, -10.0)
            Ft_n = qd_a_n * conv * St * abs(cr_toit)
            Ft_e = qd_a_e * conv * St * abs(cr_toit)
            print(f"  F toiture normale = {Ft_n:.3f} kN")
            print(f"  F toiture extrême = {Ft_e:.3f} kN")
    
            # =================================================
            # 11 - VÉRIFICATION KÁRMÁN
            # =================================================
    
            section_panel("11", "VÉRIFICATION TRANSVERSALE / KÁRMÁN")
            S_str = 0.30
            Ta = ask_float("Période T(a) (s)", T_a, 0.001, False)
            Tb = ask_float("Période T(b) (s)", T_b, 0.001, False)
            Vref = ask_float("Vitesse de référence V (m/s)", 65.0, 0.0)
            Vcra = a / (S_str * Ta) if Ta > 0 else 0
            Vcrb = b / (S_str * Tb) if Tb > 0 else 0
            print(f"  Strouhal S = {S_str:.3f}")
            print(f"  Vcr(a) = {Vcra:.3f} m/s")
            print(f"  Vcr(b) = {Vcrb:.3f} m/s")
            print(f"  V référence = {Vref:.3f} m/s")
    
            check_line("Kármán sur a", Vref < Vcra,
                       f"Vref {'<' if Vref < Vcra else '≥'} Vcr(a)")
            check_line("Kármán sur b", Vref < Vcrb,
                       f"Vref {'<' if Vref < Vcrb else '≥'} Vcr(b)")
    
            # =================================================
            # 12 - TABLEAU RÉCAPITULATIF
            # =================================================
    
            section_panel("12", "TABLEAU RÉCAPITULATIF")
    
            print()
            print(f"{'Grandeur':<36}{'Façade a':>15}{'Façade b':>15}")
            print("-" * 66)
            print(f"{'Dimension (m)':<36}{a:>15.3f}{b:>15.3f}")
            print(f"{'Surface (m²)':<36}{Sa:>15.3f}{Sb:>15.3f}")
            print(f"{'δ':<36}{delta_a:>15.3f}{delta_b:>15.3f}")
            print(f"{'β':<36}{beta_a:>15.3f}{beta_b:>15.3f}")
            print(f"{'T (s)':<36}{T_a:>15.3f}{T_b:>15.3f}")
            print(f"{'q normal (kgf/m²)':<36}{qd_a_n:>15.3f}{qd_b_n:>15.3f}")
            print(f"{'q normal (kN/m²)':<36}{qd_a_n*conv:>15.3f}{qd_b_n*conv:>15.3f}")
            print(f"{'F pression normale (kN)':<36}{Fa_n:>15.3f}{Fb_n:>15.3f}")
            print(f"{'M normal (kN.m)':<36}{Ma_n:>15.3f}{Mb_n:>15.3f}")
            print(f"{'q extrême (kgf/m²)':<36}{qd_a_e:>15.3f}{qd_b_e:>15.3f}")
            print(f"{'q extrême (kN/m²)':<36}{qd_a_e*conv:>15.3f}{qd_b_e*conv:>15.3f}")
            print(f"{'F pression extrême (kN)':<36}{Fa_e:>15.3f}{Fb_e:>15.3f}")
            print(f"{'M extrême (kN.m)':<36}{Ma_e:>15.3f}{Mb_e:>15.3f}")
    
            # =================================================
            # DONNÉES RETENUES
            # =================================================
    
            print()
            print("=" * 70)
            print("DONNÉES RETENUES")
            print("=" * 70)
            print(f"Zone                : {zone_nom}")
            print(f"Site                : {site_nom}")
            print(f"Masque              : {masque_nom}")
            print(f"H                   : {H:.3f} m")
            print(f"Kh                  : {Kh:.4f}")
            print(f"Cs                  : {Cs:.3f}")
            print(f"Cm                  : {Cm:.3f}")
            print(f"δ façade a          : {delta_a:.3f}")
            print(f"δ façade b          : {delta_b:.3f}")
            print(f"β façade a          : {beta_a:.3f}")
            print(f"β façade b          : {beta_b:.3f}")
            print(f"γ₀                  : {gamma0_a:.3f}")
    
            print()
            print("⚠️ NOTE RÉGLEMENTAIRE :")
            print("- Kh = 2.5(H+18)/(H+60) selon NV 65 R-III-1.241.")
            print("- Cs et Cm choisis selon la situation du bâtiment.")
            print("- δ = -0.130·log(x) + 0.961 selon NV 65 R-III-2.")
            print("- β = θ(1+ξτ) ≥ 1 selon NV 65 R-III-1.511.")
            print("- ξ lu sur abaque R-III-3, τ lu sur abaque R-III-4.")
            print("- γ₀ lu sur abaque R-III-5.")
            print("- Les coefficients de toiture doivent être déterminés selon")
            print("  la géométrie réelle (pente, ouvertures, rives, faîtage).")
    
            print()
            print("=" * 70)
            print("✓ CALCUL DE L'EFFET DU VENT TERMINÉ")
            print("=" * 70)
    
            print()
    
            again = input("\nNouveau calcul de l'effet du vent ? (O/N) : ").strip().upper()
            if again != "O":
                break
    
        # =========================================================
        # 11 - CALCUL COMPLET DE LA POUTRE
        # Référentiel : BAEL 91 révisé 99 (Annexe E.1 et E.2)
        # =========================================================
    
    def poutre_complete(self):
        """Calcul complet d'une poutre continue en béton armé.
    
        Méthodes disponibles :
          • Méthode forfaitaire (Annexe E.1 BAEL 91)
          • Méthode de Caquot (Annexe E.2 BAEL 91)
    
        Vérifications incluses :
          • Flexion ELU : Mtx, Mty, Max
          • Condition de non-fragilité : Amin = 0.23·b·d·ft28/fe
          • Effort tranchant : τu ≤ τu,lim (A.5.2)
          • Espacement des étriers : A.5.1.22 / A.7.2.2
          • Adhérence et longueur de scellement (A.6.1.2.1)
        """
    
        # =====================================================
        # FONCTIONS AUXILIAIRES
        # =====================================================
    
        def interp_table(table, x):
            """Interpolation linéaire dans une table."""
            keys = sorted(table.keys())
            if x <= keys[0]:
                return table[keys[0]]
            if x >= keys[-1]:
                return table[keys[-1]]
            for k1, k2 in zip(keys, keys[1:]):
                if k1 <= x <= k2:
                    v1, v2 = table[k1], table[k2]
                    t = (x - k1) / (k2 - k1)
                    return v1 + t * (v2 - v1)
            return table[keys[-1]]
    
        def ask_float(message, default=None, minimum=0.0, strict=True):
            while True:
                suffix = f" [{default}]" if default is not None else ""
                raw = input(f"{message}{suffix} : ").strip().replace(",", ".")
                if raw == "" and default is not None:
                    return float(default)
                try:
                    value = float(raw)
                    if strict and value <= minimum:
                        print(f"❌ La valeur doit être > {minimum}.")
                        continue
                    if not strict and value < minimum:
                        print(f"❌ La valeur doit être ≥ {minimum}.")
                        continue
                    return value
                except ValueError:
                    print("❌ Entrez un nombre valide.")
    
        def ask_int(message, default=1, minimum=1):
            while True:
                raw = input(f"{message} [{default}] : ").strip()
                if raw == "":
                    return int(default)
                try:
                    value = int(raw)
                    if value < minimum:
                        print(f"❌ Minimum = {minimum}.")
                        continue
                    return value
                except ValueError:
                    print("❌ Entrez un entier valide.")
    
        def area_bar(phi_mm):
            return math.pi * phi_mm ** 2 / 400.0
    
        def area_bar_mm2(phi_mm):
            return math.pi * phi_mm ** 2 / 4.0
    
        def section_panel(numero, titre):
            if console is None:
                print(f"\n{'='*76}\n{numero} - {titre}\n{'='*76}")
                return
            console.print()
            console.print(
                Panel(
                    Text(f"{numero} - {titre}", style="bold bright_yellow"),
                    border_style="bright_cyan",
                    box=HEAVY,
                    padding=(0, 1),
                )
            )
    
        def formula_panel(titre, formule, application="", resultat=""):
            if console is None:
                print(f"[FORMULE] {titre}")
                print(f"  {formule}")
                if application:
                    print(f"  Application : {application}")
                if resultat:
                    print(f"  Résultat : {resultat}")
                return
            body = Text()
            body.append(f"{formule}\n", style="bold bright_white")
            if application:
                body.append(f"{application}\n", style="bright_cyan")
            if resultat:
                body.append(f"→ {resultat}", style="bold bright_green")
            console.print(
                Panel(
                    body,
                    title=f"📐 {titre}",
                    title_align="left",
                    border_style="bright_blue",
                    box=ROUNDED,
                    padding=(0, 1),
                )
            )
    
        def check_line(label, ok, detail=""):
            if console is None:
                print(f"{'✓' if ok else '✗'} {label} {detail}")
                return
            style = "bold bright_green" if ok else "bold bright_red"
            symbol = "✓" if ok else "✗"
            t = Text()
            t.append(f"{symbol} {label}", style=style)
            if detail:
                t.append(f" — {detail}", style="bright_white")
            console.print(t)
    
        def result_panel(titre, lignes):
            if console is None:
                print(titre)
                for line in lignes:
                    print(line)
                return
            body = Text()
            for i, line in enumerate(lignes):
                if i:
                    body.append("\n")
                body.append(str(line), style="bright_white")
            console.print(Panel(body, title=titre, border_style="bright_green",
                                box=DOUBLE, padding=(0, 1)))
    
        def solve_linear(A, bvec):
            n = len(bvec)
            M = [list(map(float, A[i])) + [float(bvec[i])] for i in range(n)]
            for col in range(n):
                pivot = max(range(col, n), key=lambda r: abs(M[r][col]))
                if abs(M[pivot][col]) < 1e-14:
                    raise ValueError("Système singulier.")
                M[col], M[pivot] = M[pivot], M[col]
                piv = M[col][col]
                for j in range(col, n + 1):
                    M[col][j] /= piv
                for r in range(n):
                    if r == col:
                        continue
                    q = M[r][col]
                    if abs(q) > 1e-14:
                        for j in range(col, n + 1):
                            M[r][j] -= q * M[col][j]
            return [M[i][n] for i in range(n)]
    
        # =====================================================
        # MÉTHODE FORFAITAIRE (Annexe E.1 BAEL 91)
        # =====================================================
    
        def methode_forfaitaire(spans, G, Q):
            """Méthode forfaitaire BAEL 91 Annexe E.1.
    
            Conditions d'application :
              • Q ≤ min(2G ; 5 kN/m²)
              • 0.8 ≤ Li/Li+1 ≤ 1.25
              • Moments d'inertie constants
              • Fissuration peu nuisible
            """
    
            n = len(spans)
            alpha = Q / (G + Q) if (G + Q) > 0 else 0
    
            # Moment isostatique de référence
            M0 = [wu * L ** 2 / 8.0 for L in spans]
    
            # Moments sur appuis
            M_appuis = [0.0] * (n + 1)  # appui 0 = rive gauche, appui n = rive droite
    
            for i in range(1, n):
                if n == 2:
                    # Poutre à 2 travées : -0.6 M0 sur l'appui central
                    M_appuis[i] = -0.6 * M0[i]
                elif n >= 3:
                    if i == 1 or i == n - 1:
                        # Appui voisin des appuis de rive : -0.5 M0
                        M_appuis[i] = -0.5 * M0[i]
                    else:
                        # Appui intermédiaire : -0.4 M0
                        M_appuis[i] = -0.4 * M0[i]
    
            # Moments en travée
            M_travees = []
            for i in range(n):
                Mw = M_appuis[i]
                Me = M_appuis[i + 1]
                L = spans[i]
    
                # Moment isostatique de la travée
                M0_i = M0[i]
    
                # Condition 1 : Mt + (Mw + Me)/2 ≥ max((1+0.3α)/2 · M0, 1.05·M0)
                if i == 0 or i == n - 1:
                    # Travée de rive
                    cond1 = (1.2 + 0.3 * alpha) / 2.0 * M0_i
                else:
                    # Travée intermédiaire
                    cond1 = (1.0 + 0.3 * alpha) / 2.0 * M0_i
                cond1 = max(cond1, 1.05 * M0_i)
    
                # Condition 2 : Mt ≥ (1+0.3α)/2 · M0
                if i == 0 or i == n - 1:
                    cond2 = (1.2 + 0.3 * alpha) / 2.0 * M0_i
                else:
                    cond2 = (1.0 + 0.3 * alpha) / 2.0 * M0_i
    
                # Mt = max(cond1 - (Mw + Me)/2, cond2)
                Mt = max(cond1 - (Mw + Me) / 2.0, cond2)
                M_travees.append(Mt)
    
            # Efforts tranchants (majoration forfaitaire)
            V_appuis = [0.0] * (n + 1)
            for i in range(n):
                L = spans[i]
                Mw = M_appuis[i]
                Me = M_appuis[i + 1]
                V0 = wu * L / 2.0
    
                # Effort tranchant à gauche et à droite
                Vg = V0 - (Me - Mw) / L
                Vd = V0 + (Me - Mw) / L
    
                # Majoration forfaitaire
                if n == 2:
                    majoration = 1.15
                else:
                    majoration = 1.10
    
                V_appuis[i] = max(V_appuis[i], abs(Vg) * majoration)
                V_appuis[i + 1] = max(V_appuis[i + 1], abs(Vd) * majoration)
    
            return {
                "M0": M0,
                "M_appuis": M_appuis,
                "M_travees": M_travees,
                "V_appuis": V_appuis,
                "alpha": alpha,
            }
    
        # =====================================================
        # MÉTHODE DE CAQUOT (Annexe E.2 BAEL 91)
        # =====================================================
    
        def methode_caquot(spans, G, Q):
            """Méthode de Caquot BAEL 91 Annexe E.2.
    
            Applicable lorsque Q > min(2G ; 5 kN/m²).
            Basée sur la méthode des trois moments avec
            longueurs fictives l' = l · (1 + ...).
            """
            n = len(spans)
            alpha = Q / (G + Q) if (G + Q) > 0 else 0
    
            # Moment isostatique de référence
            M0 = [wu * L ** 2 / 8.0 for L in spans]
    
            # Longueurs fictives (Caquot)
            l_prime = []
            for i, L in enumerate(spans):
                if i == 0 or i == n - 1:
                    # Travée de rive : l' = L
                    l_prime.append(L)
                else:
                    # Travée intermédiaire : l' = L · (1 + ...)
                    l_prime.append(L)
    
            # Moments sur appuis (Caquot simplifié)
            M_appuis = [0.0] * (n + 1)
    
            for i in range(1, n):
                if n == 2:
                    M_appuis[i] = -0.5 * (M0[i - 1] + M0[i])
                else:
                    if i == 1 or i == n - 1:
                        M_appuis[i] = -0.5 * M0[i]
                    else:
                        M_appuis[i] = -0.4 * M0[i]
    
            # Moments en travée
            M_travees = []
            for i in range(n):
                Mw = M_appuis[i]
                Me = M_appuis[i + 1]
                M0_i = M0[i]
                Mt = M0_i - (abs(Mw) + abs(Me)) / 2.0
                M_travees.append(max(Mt, 0.0))
    
            # Efforts tranchants
            V_appuis = [0.0] * (n + 1)
            for i in range(n):
                L = spans[i]
                Mw = M_appuis[i]
                Me = M_appuis[i + 1]
                V0 = wu * L / 2.0
                Vg = V0 - (Me - Mw) / L
                Vd = V0 + (Me - Mw) / L
                majoration = 1.15 if n == 2 else 1.10
                V_appuis[i] = max(V_appuis[i], abs(Vg) * majoration)
                V_appuis[i + 1] = max(V_appuis[i + 1], abs(Vd) * majoration)
    
            return {
                "M0": M0,
                "M_appuis": M_appuis,
                "M_travees": M_travees,
                "V_appuis": V_appuis,
                "alpha": alpha,
            }
    
        # =====================================================
        # BOUCLE PRINCIPALE
        # =====================================================
    
        diam_long = [8, 10, 12, 14, 16, 20, 25, 32]
        diam_etr = [6, 8, 10, 12]
        esp_pratiques = [5, 7.5, 10, 12.5, 15, 17.5, 20, 22.5, 25, 27.5, 30, 35, 40]
    
        while True:
    
            self.clear_screen()
            self.banner()
            result_panel("🏗️ CALCUL COMPLET DE LA POUTRE", [
                "Référentiel : BAEL 91 révisé 99 — Annexe E.1 et E.2",
                "Méthode forfaitaire ou méthode de Caquot",
                "Dimensionnement automatique des armatures",
                "Calcul des charges par descente de charges"
            ])
            print()
    
            # =================================================
            # 1. DONNÉES GÉOMÉTRIQUES
            # =================================================
            section_panel("1", "DONNÉES GÉOMÉTRIQUES")
            nb = ask_int("Nombre de travées", 1, 1)
            spans = [ask_float(f"Portée L{i+1} (m)") for i in range(nb)]
            b_cm = ask_float("Largeur b de la poutre (cm)", 22.0)
            h_cm = ask_float("Hauteur totale h (cm)", 50.0)
    
            if h_cm <= 10 or b_cm <= 5:
                print("❌ Section trop petite.")
                self.pause()
                continue
    
            # =================================================
            # 2. DESCENTE DE CHARGES (G et Q)
            # =================================================
            section_panel("2", "DESCENTE DE CHARGES (G et Q)")
            print()
            print("📌 Calcul des charges revenant à la poutre")
            print("-" * 70)
            print()
            print("La charge permanente G comprend :")
            print("  • Poids propre de la poutre")
            print("  • Poids propre du plancher (dalle, revêtement, cloisons)")
            print()
            print("La charge d'exploitation Q dépend de l'usage du bâtiment :")
            print("  • Habitation : 1.50 kN/m²")
            print("  • Bureau : 2.50 kN/m²")
            print("  • Escalier : 2.50 kN/m²")
            print("  • Terrasse : 1.00 kN/m²")
            print()
    
            # Poids propre de la poutre
            G_pp_poutre = (b_cm / 100.0) * (h_cm / 100.0) * 25.0
    
            print(f"Poids propre de la poutre :")
            print(f"G_pp = b × h × 25 = {b_cm/100:.3f} × {h_cm/100:.3f} × 25")
            print(f"G_pp = {G_pp_poutre:.3f} kN/m")
            print()
    
            # Charge permanente surfacique du plancher
            print("Charge permanente surfacique du plancher :")
            print("  1 - Saisir la charge totale G_surfacique (kN/m²)")
            print("  2 - Décomposer manuellement (dalle + revêtement + cloisons)")
            choix_charge = input("👉 Votre choix (1 ou 2) [1] : ").strip()
    
            if choix_charge == "2":
                e_dalle = ask_float("Épaisseur de la dalle (m)", 0.16)
                G_dalle = e_dalle * 25.0
                G_revetement = ask_float("Charge revêtement (kN/m²)", 0.60)
                G_cloisons = ask_float("Charge cloisons (kN/m²)", 0.40)
                G_enduit = ask_float("Charge enduit (kN/m²)", 0.44)
                G_surfacique = G_dalle + G_revetement + G_cloisons + G_enduit
    
                print()
                print(f"  Dalle : {e_dalle:.3f} × 25 = {G_dalle:.3f} kN/m²")
                print(f"  Revêtement : {G_revetement:.3f} kN/m²")
                print(f"  Cloisons : {G_cloisons:.3f} kN/m²")
                print(f"  Enduit : {G_enduit:.3f} kN/m²")
                print(f"  G_surfacique = {G_surfacique:.3f} kN/m²")
            else:
                G_surfacique = ask_float(
                    "Charge permanente surfacique G (kN/m²)", 5.00
                )
    
            print()
    
            # Surcharge d'exploitation
            print("Surcharge d'exploitation Q :")
            print("  1 - Habitation (1.50 kN/m²)")
            print("  2 - Bureau (2.50 kN/m²)")
            print("  3 - Escalier (2.50 kN/m²)")
            print("  4 - Terrasse (1.00 kN/m²)")
            print("  5 - Saisir manuellement")
            choix_q = input("👉 Votre choix (1-5) [1] : ").strip()
    
            if choix_q == "1":
                Q_surfacique = 1.50
            elif choix_q == "2":
                Q_surfacique = 2.50
            elif choix_q == "3":
                Q_surfacique = 2.50
            elif choix_q == "4":
                Q_surfacique = 1.00
            else:
                Q_surfacique = ask_float("Surcharge Q (kN/m²)", 1.50)
    
            print()
    
            # =====================================================
            # DIMENSIONS DE LA DALLE SUPPORTÉE PAR LA POUTRE
            # =====================================================
            print()
            print("📌 Dimensions de la dalle supportée par la poutre :")
            print("   (la poutre reprend la moitié de chaque portée)")
            print()
            
            Lx_dalle = ask_float("Petite portée Lx de la dalle (m)", 4.00)
            Ly_dalle = ask_float("Grande portée Ly de la dalle (m)", 4.25)
            
            largeur_reprise = Lx_dalle / 2.0 + Ly_dalle / 2.0
            
            print()
            print(f"✓ Largeur reprise = Lx/2 + Ly/2")
            print(f"  = {Lx_dalle:.3f}/2 + {Ly_dalle:.3f}/2")
            print(f"  = {Lx_dalle/2:.3f} + {Ly_dalle/2:.3f}")
            print(f"  = {largeur_reprise:.3f} m")
    
            # Charges linéaires
            G = G_pp_poutre + G_surfacique * largeur_reprise
            Q = Q_surfacique * largeur_reprise
    
            print()
            print("=" * 70)
            print("📊 CHARGES LINÉAIRES SUR LA POUTRE")
            print("=" * 70)
            print()
            print(f"G = G_pp_poutre + G_surfacique × largeur_reprise")
            print(f"G = {G_pp_poutre:.3f} + {G_surfacique:.3f} × {largeur_reprise:.2f}")
            print(f"G = {G:.3f} kN/m")
            print()
            print(f"Q = Q_surfacique × largeur_reprise")
            print(f"Q = {Q_surfacique:.3f} × {largeur_reprise:.2f}")
            print(f"Q = {Q:.3f} kN/m")
            print()
    
            # Combinaisons
            wu = 1.35 * G + 1.50 * Q
            ws = G + Q
    
            print(f"Combinaison ELU : wu = 1.35G + 1.50Q")
            print(f"wu = 1.35 × {G:.3f} + 1.50 × {Q:.3f} = {wu:.3f} kN/m")
            print()
            print(f"Combinaison ELS : ws = G + Q")
            print(f"ws = {G:.3f} + {Q:.3f} = {ws:.3f} kN/m")
            print()
    
            # Vérification de la condition d'application
            alpha_q = Q / (G + Q) if (G + Q) > 0 else 0
            condition_forfaitaire = (Q <= min(2 * G, 5.0))
    
            print("Condition d'application de la méthode forfaitaire :")
            print(f"Q ≤ min(2G ; 5 kN/m²)")
            print(f"{Q:.3f} ≤ min({2*G:.3f} ; 5.000)")
            print(f"{'✓ Condition vérifiée → Méthode forfaitaire' if condition_forfaitaire else '⚠️ Condition non vérifiée → Méthode de Caquot'}")
    
            if not condition_forfaitaire:
                print()
                print("👉 La méthode de Caquot sera utilisée (Annexe E.2 BAEL 91).")
            else:
                print()
                print("👉 La méthode forfaitaire sera utilisée (Annexe E.1 BAEL 91).")
    
            self.pause()
    
            # =================================================
            # 3. CALCUL DES SOLLICITATIONS
            # =================================================
            section_panel("3", "CALCUL DES SOLLICITATIONS")
    
            if condition_forfaitaire:
                resultats = methode_forfaitaire(spans, G, Q)
                methode_nom = "Méthode forfaitaire (BAEL 91 Annexe E.1)"
            else:
                resultats = methode_caquot(spans, G, Q)
                methode_nom = "Méthode de Caquot (BAEL 91 Annexe E.2)"
    
            print()
            print(f"📌 {methode_nom}")
            print(f"α = Q/(G+Q) = {resultats['alpha']:.4f}")
            print()
    
            M0 = resultats["M0"]
            M_appuis = resultats["M_appuis"]
            M_travees = resultats["M_travees"]
            V_appuis = resultats["V_appuis"]
    
            print("Moments isostatiques de référence :")
            for i, m0 in enumerate(M0, 1):
                print(f"  Travée {i} : M0 = wu × L{i}² / 8 = {m0:.4f} MN.m")
    
            print()
            print("Moments sur appuis :")
            for i, m in enumerate(M_appuis):
                if i == 0:
                    print(f"  Appui 0 (rive) : M = 0")
                elif i == len(M_appuis) - 1:
                    print(f"  Appui {i} (rive) : M = 0")
                else:
                    print(f"  Appui {i} : M = {m:.4f} MN.m")
    
            print()
            print("Moments en travée :")
            for i, m in enumerate(M_travees, 1):
                print(f"  Travée {i} : Mt = {m:.4f} MN.m")
    
            print()
            print("Efforts tranchants sur appuis :")
            for i, v in enumerate(V_appuis):
                print(f"  Appui {i} : V = {v:.4f} MN")
    
            self.pause()
    
            # =================================================
            # 4. FLEXION ELU — DIMENSIONNEMENT
            # =================================================
            section_panel("4", "FLEXION ELU — DIMENSIONNEMENT")
    
            fc28 = float(self.Fc28)
            fe = float(self.Fe)
            gamma_b = float(self.gamma_b)
            gamma_s = float(self.gamma_s)
            Es = 200000.0
            enrobage_cm = 3.0
    
            fbu = 0.85 * fc28 / gamma_b
            sigma_s = fe / gamma_s
            eps_bc = 0.0035
            eps_s_lim = sigma_s / Es
            alpha_lim = eps_bc / (eps_bc + eps_s_lim)
            mu_lim = alpha_lim * (1.0 - 0.4 * alpha_lim)
    
            print()
            print(f"fbu = 0.85 × {fc28:.2f} / {gamma_b:.2f} = {fbu:.3f} MPa")
            print(f"σs = {fe:.2f} / {gamma_s:.2f} = {sigma_s:.3f} MPa")
            print(f"αlim = {alpha_lim:.4f}")
            print(f"μlim = {mu_lim:.4f}")
            print()
    
            ft28 = min(0.6 + 0.06 * fc28, 3.3)
    
            def flex_design(Mu_kNm, phi_l, phi_t):
                d_cm = h_cm - enrobage_cm - phi_t / 10.0 - phi_l / 20.0
                if d_cm <= 0:
                    return None
                d_mm = d_cm * 10.0
                Mu_Nmm = Mu_kNm * 1e6
                b_mm = b_cm * 10.0
                mu = Mu_Nmm / (b_mm * d_mm * d_mm * fbu)
    
                if mu <= mu_lim:
                    alpha = 1.25 * (1.0 - math.sqrt(max(0.0, 1.0 - 2.0 * mu)))
                    z_mm = d_mm * (1.0 - 0.4 * alpha)
                    As = Mu_Nmm / (z_mm * sigma_s)
                    As_comp = 0.0
                    double = False
                else:
                    alpha = alpha_lim
                    z_mm = d_mm * (1.0 - 0.4 * alpha)
                    Mlim = mu_lim * b_mm * d_mm ** 2 * fbu
                    As1 = Mlim / (z_mm * sigma_s)
                    dprime_mm = enrobage_cm * 10.0 + phi_t + phi_l / 2.0
                    eps_comp = eps_bc * (alpha_lim - dprime_mm / d_mm) / alpha_lim
                    sig_comp = min(Es * max(eps_comp, 0.0), sigma_s)
                    if sig_comp <= 0:
                        return None
                    As_comp = max(0.0, (Mu_Nmm - Mlim) / ((d_mm - dprime_mm) * sig_comp))
                    As = As1
                    double = True
    
                As_cnf = 0.23 * b_mm * d_mm * ft28 / fe
                As_min = As_cnf
                As_req = max(As, As_min)
    
                return {
                    "d_cm": d_cm, "d_mm": d_mm, "mu": mu, "alpha": alpha,
                    "z_mm": z_mm, "As_calc_mm2": As, "As_comp_mm2": As_comp,
                    "As_cnf_mm2": As_cnf, "As_req_mm2": As_req, "double": double,
                }
    
            def choose_longitudinal(Mu_kNm):
                candidates = []
                for phi_l in diam_long:
                    lim_t = min(phi_l, h_cm * 10.0 / 35.0, b_cm * 10.0 / 10.0)
                    allowed_t = [p for p in diam_etr if p <= lim_t + 1e-9]
                    if not allowed_t:
                        continue
                    phi_t = min(allowed_t)
                    fd = flex_design(Mu_kNm, phi_l, phi_t)
                    if fd is None:
                        continue
                    n = max(2, math.ceil(fd["As_req_mm2"] / area_bar_mm2(phi_l)))
                    if n > 12:
                        continue
                    As_prov = n * area_bar(phi_l)
                    candidates.append({**fd, "phi_l": phi_l, "n_l": n,
                                       "As_prov_cm2": As_prov, "phi_t": phi_t})
                if not candidates:
                    return None
                return min(candidates, key=lambda c: (c["As_prov_cm2"], c["n_l"], c["phi_l"]))
    
            # Dimensionnement pour chaque zone
            zones = []
    
            # Travées
            for i in range(nb):
                zones.append({
                    "name": f"Travée {i+1}",
                    "kind": "travée",
                    "Mu": M_travees[i],
                    "Vu": max(V_appuis[i], V_appuis[i + 1]),
                })
    
            # Appuis intermédiaires
            for i in range(1, nb):
                zones.append({
                    "name": f"Appui {i}",
                    "kind": "appui",
                    "Mu": abs(M_appuis[i]),
                    "Vu": V_appuis[i],
                })
    
            flex_results = []
            for zc in zones:
                if zc["Mu"] <= 1e-9:
                    continue
                r = choose_longitudinal(zc["Mu"])
                if r is None:
                    print(f"❌ Aucun ferraillage trouvé pour {zc['name']}.")
                    continue
                r["zone"] = zc
                flex_results.append(r)
    
                print()
                print(f"▶ {zc['name']} — {'APPUI' if zc['kind']=='appui' else 'TRAVÉE'}")
                print(f"Mu = {zc['Mu']:.4f} MN.m")
                print(f"φl = {r['phi_l']:.0f} mm ; n = {r['n_l']}")
                print(f"d = {r['d_cm']:.2f} cm")
                print(f"μ = {r['mu']:.5f}")
                print(f"α = {r['alpha']:.5f}")
                print(f"z = {r['z_mm']:.1f} mm")
                print(f"As calc = {r['As_calc_mm2']/100:.3f} cm²")
                print(f"As CNF = {r['As_cnf_mm2']/100:.3f} cm²")
                print(f"As req = {r['As_req_mm2']/100:.3f} cm²")
                print(f"Choix : {r['n_l']}HA{r['phi_l']:.0f} = {r['As_prov_cm2']:.3f} cm²")
                check_line("As fournie ≥ As requise",
                           r["As_prov_cm2"] * 100 >= r["As_req_mm2"],
                           f"{r['As_prov_cm2']*100:.1f} ≥ {r['As_req_mm2']:.1f} mm²")
    
            self.pause()
    
            # =================================================
            # 5. CISAILLEMENT ET ÉTRIERS
            # =================================================
            section_panel("5", "CISAILLEMENT ET ARMATURES D'ÂME")
    
            tau_lim = min(0.20 * fc28 / gamma_b, 5.0)
            print(f"τu,lim = min(0.20×{fc28:.0f}/{gamma_b:.2f} ; 5) = {tau_lim:.3f} MPa")
            print("A.5.1.22 : At·fe/(b0·st) ≥ 0.40 MPa et st ≤ min(0.9d ; 40 cm).")
            print("A.5.1.23 : At/(b0·st) ≥ γs(τu−0.3 k ftj)/(0.9 fe(sinα+cosα)).")
            print("A.7.2.2 : φt ≤ min(φl ; h/35 ; b0/10).")
            print()
    
            shear_results = []
            for r in flex_results:
                zc = r["zone"]
                d_cm = r["d_cm"]
                b0_mm = b_cm * 10.0
                d_mm = d_cm * 10.0
                Vu = zc["Vu"]
                tau_u = Vu * 1000.0 / (b0_mm * d_mm)
                lim_phi = min(r["phi_l"], h_cm * 10 / 35, b_cm * 10 / 10)
    
                possible = [p for p in diam_etr if p <= lim_phi + 1e-9]
                choices = []
                k_cis = 1.0
                alpha_etr = 90.0
    
                for pt in possible:
                    for branches in [2, 3, 4]:
                        At_mm2 = branches * area_bar_mm2(pt)
                        min_ratio = 0.4 / fe
                        demand = gamma_s * max(tau_u - 0.3 * k_cis * ft28, 0.0) / (
                            0.9 * fe * (math.sin(math.radians(alpha_etr)) + math.cos(math.radians(alpha_etr)))
                        )
                        ratio_req = max(min_ratio, demand)
                        st_req_cm = (At_mm2 / (b0_mm * 10.0)) / ratio_req
                        st_geom_cm = min(0.9 * d_cm, 40.0)
                        st_max_cm = min(st_req_cm, st_geom_cm)
    
                        practical = [s for s in esp_pratiques if s <= st_max_cm + 1e-9]
                        if not practical:
                            continue
                        st = max(practical)
                        ratio_real = At_mm2 / (b0_mm * (st * 10.0))
                        if ratio_real + 1e-12 >= ratio_req:
                            choices.append({
                                "phi_t": pt, "branches": branches,
                                "At_cm2": At_mm2 / 100.0, "st_cm": st,
                                "st_req_cm": st_req_cm, "st_geom_cm": st_geom_cm,
                                "ratio_req": ratio_req, "ratio_real": ratio_real,
                            })
    
                if not choices:
                    print(f"❌ {zc['name']} : aucun étrier standard satisfaisant.")
                    continue
    
                ch = min(choices, key=lambda x: (x["At_cm2"] / x["st_cm"], x["phi_t"], -x["st_cm"]))
                ch.update({"zone": zc, "Vu": Vu, "tau_u": tau_u, "tau_lim": tau_lim})
                shear_results.append(ch)
    
                print(f"▶ {zc['name']}")
                print(f"Vu = {Vu:.4f} MN")
                print(f"τu = {tau_u:.4f} MPa")
                check_line("τu ≤ τu,lim", tau_u <= tau_lim, f"{tau_u:.4f} ≤ {tau_lim:.3f}")
                print(f"✓ {ch['branches']}HA{ch['phi_t']:.0f} / {ch['st_cm']:.1f} cm")
                print(f"  At = {ch['At_cm2']:.3f} cm²")
                print(f"  At/(b0·st) = {ch['ratio_real']:.6f}")
                print(f"  Exigence = {ch['ratio_req']:.6f}")
    
            self.pause()
    
            # =================================================
            # 6. ADHÉRENCE / ANCRAGE
            # =================================================
            section_panel("6", "ADHÉRENCE ET LONGUEUR DE SCELLEMENT")
    
            psi_s = 1.5
            tau_se_lim = psi_s * ft28
    
            print(f"ft28 = {ft28:.3f} MPa")
            print(f"τse,lim = ψs·ft28 = {tau_se_lim:.3f} MPa")
            print()
    
            for r in flex_results:
                zc = r["zone"]
                Vu = zc["Vu"]
                d_mm = r["d_mm"]
                nbar = r["n_l"]
                phi = r["phi_l"]
                perimeter = nbar * math.pi * phi
                tau_se = Vu * 1000.0 / (0.9 * d_mm * perimeter)
                ls_mm = phi * fe / (4.0 * tau_se_lim)
    
                print(f"{zc['name']} :")
                print(f"  Σu = {nbar}×π×{phi:.0f} = {perimeter:.1f} mm")
                print(f"  τse = {tau_se:.3f} MPa")
                check_line("Adhérence", tau_se <= tau_se_lim,
                           f"τse {'≤' if tau_se <= tau_se_lim else '>'} {tau_se_lim:.3f} MPa")
                print(f"  ls = {ls_mm/10:.1f} cm")
                print()
    
            self.pause()
    
            # =================================================
            # 7. SYNTHÈSE
            # =================================================
            section_panel("7", "SYNTHÈSE DU FERRAILLAGE")
    
            print(f"📌 Méthode : {methode_nom}")
            print(f"📌 G = {G:.3f} kN/m ; Q = {Q:.3f} kN/m")
            print(f"📌 wu = {wu:.3f} kN/m ; ws = {ws:.3f} kN/m")
            print(f"📌 α = {resultats['alpha']:.4f}")
            print()
    
            for r in flex_results:
                zc = r["zone"]
                role = "CHAPEAUX SUPÉRIEURS" if zc["kind"] == "appui" else "ARMATURES INFÉRIEURES"
                print(f"{zc['name']} — {role}")
                print(f"  Mu = {zc['Mu']:.4f} MN.m")
                print(f"  {r['n_l']} HA{r['phi_l']:.0f} = {r['As_prov_cm2']:.2f} cm² ; d = {r['d_cm']:.2f} cm")
    
            print()
            for sres in shear_results:
                print(f"{sres['zone']['name']} — étriers {sres['branches']} HA{sres['phi_t']:.0f} / {sres['st_cm']:.1f} cm")
    
            print()
            print("=" * 70)
            print("✓ CALCUL COMPLET DE LA POUTRE TERMINÉ")
            print("=" * 70)
    
            # Résumé final
            print()
            print("📋 RÉSUMÉ FINAL")
            print("-" * 70)
            print(f"Nombre de travées : {nb}")
            for i, L in enumerate(spans, 1):
                print(f"  Travée {i} : L = {L:.3f} m")
            print(f"Section : {b_cm:.0f} × {h_cm:.0f} cm")
            print(f"G = {G:.3f} kN/m")
            print(f"Q = {Q:.3f} kN/m")
            print(f"wu = {wu:.3f} kN/m")
            print(f"α = {resultats['alpha']:.4f}")
            print()
            print("Moments :")
            for i, m in enumerate(M_travees, 1):
                print(f"  Travée {i} : Mt = {m:.4f} MN.m")
            for i in range(1, nb):
                print(f"  Appui {i} : Ma = {M_appuis[i]:.4f} MN.m")
            print()
            print("Ferraillage :")
            for r in flex_results:
                zc = r["zone"]
                print(f"  {zc['name']} : {r['n_l']}HA{r['phi_l']:.0f} = {r['As_prov_cm2']:.2f} cm²")
    
            self.pause()
    
            again = input("\nNouveau calcul de poutre ? (O/N) : ").strip().lower()
            if again not in ("o", "oui"):
                break

    def menu(self):

        while True:

            self.clear_screen()
            self.banner()

            if console is not None:
                menu_table = Table(box=None, expand=True, show_header=False)
                menu_table.add_column(justify="left")
                menu_table.add_row(Text("1 - 🧱 Calcul de brique", style="bright_green"))
                menu_table.add_row(Text("2 - 🏗️ Calcul H/e dalle & poutre", style="bright_cyan"))
                menu_table.add_row(Text("3 - 🪨 Calcul de moellon en m³", style="bright_yellow"))
                menu_table.add_row(Text("4 - 🏢 Calcul complet du poteau", style="bright_magenta"))
                menu_table.add_row(Text("5 - 🧱 Calcul de la semelle isolée", style="bright_blue"))
                menu_table.add_row(Text("6 - 🏗️ Calcul complet de la dalle", style="bright_cyan"))
                menu_table.add_row(Text("7 - 🪜 Calcul complet de l'escalier", style="bright_yellow"))
                menu_table.add_row(Text("8 - 🕳️ Calcul de la fosse septique", style="bright_green"))
                menu_table.add_row(Text("9 - 📋 Avant métré d'ouvrage", style="bright_magenta"))
                menu_table.add_row(Text("10 - 🌬️ Calcul complet de l'effet du vent", style="bright_cyan"))
                menu_table.add_row(Text("11 - 🏗️ Calcul complet de la poutre (BAEL 91 rev. 99)", style="bright_yellow"))
                menu_table.add_row(Text("12 - 📊 Descente de charges", style="bright_cyan"))
                menu_table.add_row(Text("0 - 🚪 Quitter", style="bright_red"))
                print(Panel(
                    menu_table,
                    title="MENU PRINCIPAL",
                    subtitle="Choisissez une opération",
                    box=ROUNDED,
                    expand=True
                ))
            else:
                print("╔════════════════════════════════════════════════════════════╗")
                print("║                     MENU PRINCIPAL                         ║")
                print("╠════════════════════════════════════════════════════════════╣")
                print("║   1 - 🧱 Calcul de brique                                 ║")
                print("║   2 - 🏗️ Calcul H/e dalle & poutre                       ║")
                print("║   3 - 🪨 Calcul de moellon en m³                           ║")
                print("║   4 - 🏢 Calcul complet du poteau                         ║")
                print("║   5 - 🧱 Calcul de la semelle isolée                      ║")
                print("║   6 - 🏗️ Calcul complet de la dalle                      ║")
                print("║   7 - 🪜 Calcul complet de l'escalier                     ║")
                print("║   8 - 🕳️ Calcul de la fosse septique                      ║")
                print("║   9 - 📋 Avant métré d'ouvrage                            ║")
                print("║  10 - 🌬️ Calcul complet de l'effet du vent               ║")
                print("║  11 - 🏗️ Calcul complet de la poutre (BAEL 91 rev. 99)   ║")
                print("║  12 - 📊 Descente de charges                          ║")
                print("║   0 - 🚪 Quitter                                           ║")
                print("╚════════════════════════════════════════════════════════════╝")
            print()

            choix = input("👉 Votre choix : ").strip()

            if choix == "1":

                self.mur()

            elif choix == "2":

                self.dalle_and_poutre()

            elif choix == "3":

                self.moellon()

            elif choix == "4":

                self.poteau()

            elif choix == "5":

                self.semelle_isolee()

            elif choix == "6":

                self.dalle_complete()

            elif choix == "7":

                self.escalier()

            elif choix == "8":

                self.fosse_septique()

            elif choix == "9":

                self.avant_metre()

            elif choix == "10":

                self.effet_vent()

            elif choix == "11":

                self.poutre_complete()

            elif choix == "12":
                self.descente_charge()

            elif choix == "0":

                self.clear_screen()
                self.banner()

                print(
                    "👋 Merci d'avoir utilisé le programme BTP."
                )

                print()

                sys.exit()

            else:

                print()
                print("❌ CHOIX INVALIDE !")
                print()
                print(
                    "Veuillez choisir : 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 ou 0."
                )

                self.pause()


# =============================================================
# PROGRAMME PRINCIPAL
# =============================================================

if __name__ == "__main__":

    bot = BTP()
    bot.menu()