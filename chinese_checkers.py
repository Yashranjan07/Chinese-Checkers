import tkinter as tk
import math
import random
import time
import sys

# ---------------- HIGH-DPI AWARENESS (SHARP TEXT & GRAPHICS) ----------------
try:
    if sys.platform == "win32":
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

# ---------------- STAR-BOARD TOPOLOGY ----------------
def build_star_points():
    points = []
    row_patterns = [
        (0, [0]),
        (1, [-1, 1]),
        (2, [-2, 0, 2]),
        (3, [-3, -1, 1, 3]),
        (4, list(range(-8, 9, 2))),
        (5, list(range(-7, 8, 2))),
        (6, list(range(-6, 7, 2))),
        (7, list(range(-7, 8, 2))),
        (8, list(range(-8, 9, 2))),
        (9, [-3, -1, 1, 3]),
        (10, [-2, 0, 2]),
        (11, [-1, 1]),
        (12, [0]),
    ]
    for r, cols in row_patterns:
        for c in cols:
            points.append((r, c))
    return set(points)

BOARD_POINTS = build_star_points()

TOP_CAMP = {(0, 0), (1, -1), (1, 1), (2, -2), (2, 0), (2, 2)}
BOTTOM_CAMP = {(12, 0), (11, -1), (11, 1), (10, -2), (10, 0), (10, 2)}

NEIGHBORS = [
    (-1, -1), (-1, 1),
    (0, -2),  (0, 2),
    (1, -1),  (1, 1)
]

EMPTY = 0
HUMAN = 1
AI = 2

# Typography is selected at runtime from fonts that are actually installed.
# Bahnschrift gives the interface a compact, contemporary game/HUD feel on Windows
# without depending on any external font package.
FONT_NAME = "Segoe UI" if sys.platform == "win32" else "Helvetica Neue"
FONT_TEXT = "Segoe UI" if sys.platform == "win32" else "Helvetica Neue"

def select_game_fonts(root):
    """Choose a polished display/body pair without requiring downloaded fonts."""
    global FONT_NAME, FONT_TEXT
    try:
        families = {name.lower(): name for name in root.tk.call("font", "families")}
    except Exception:
        return

    display_candidates = (
        "Bahnschrift SemiBold", "Bahnschrift", "Segoe UI Semibold",
        "Aptos Display", "Segoe UI"
    )
    body_candidates = (
        "Segoe UI", "Aptos", "Arial"
    )

    for candidate in display_candidates:
        if candidate.lower() in families:
            FONT_NAME = families[candidate.lower()]
            break

    for candidate in body_candidates:
        if candidate.lower() in families:
            FONT_TEXT = families[candidate.lower()]
            break

PALETTES = {
    "ruby":     {"name": "Red",      "base": "#dc2626", "mid": "#ef4444", "glow": "#f87171", "rim": "#991b1b"},
    "sapphire": {"name": "Blue",     "base": "#2563eb", "mid": "#3b82f6", "glow": "#60a5fa", "rim": "#1e3a8a"},
    "yellow":   {"name": "Yellow",   "base": "#ca8a04", "mid": "#eab308", "glow": "#facc15", "rim": "#854d0e"},
    "emerald":  {"name": "Green",    "base": "#059669", "mid": "#10b981", "glow": "#34d399", "rim": "#064e3b"},
    "amethyst": {"name": "Purple",   "base": "#7c3aed", "mid": "#a855f7", "glow": "#c084fc", "rim": "#581c87"},
    "cyan":     {"name": "Cyan",     "base": "#0891b2", "mid": "#06b6d4", "glow": "#22d3ee", "rim": "#164e63"}
}

THEME_STYLES = {
    "dark": {
        "bg": "#0d0f12",
        "header_bg": "#15181d",
        "card_bg": "#181b20",
        "card_border": "#2b3038",
        "text_main": "#f3f0e8",
        "text_sub": "#a7a49c",
        "btn_bg": "#24282e",
        "btn_fg": "#ece9e1",
        "line_color": "#242930",
        "hole_fill": "#0a0c0f",
        "hole_outline": "#30353d",
        "top_camp_fill": "#2b2331",
        "bottom_camp_fill": "#30251e",
        "bg_accent": "#24282e",
        "bg_star": "#4a4d52",
        "menu_particle": "#c8a96b",
        "modal_dim": "gray50"
    },
    "light": {
        "bg": "#f2efe8",
        "header_bg": "#fbfaf7",
        "card_bg": "#fbfaf7",
        "card_border": "#d5d0c6",
        "text_main": "#202124",
        "text_sub": "#6d6a64",
        "btn_bg": "#e8e3da",
        "btn_fg": "#262522",
        "line_color": "#d9d4ca",
        "hole_fill": "#e5e0d7",
        "hole_outline": "#b9b3a8",
        "top_camp_fill": "#eee5ef",
        "bottom_camp_fill": "#f1e5dc",
        "bg_accent": "#e2ddd3",
        "bg_star": "#aaa49a",
        "menu_particle": "#9a7a3d",
        "modal_dim": "gray75"
    }
}

DIFFICULTIES = {
    "Beginner": {"depth": 1, "randomness": 0.35},
    "Easy":     {"depth": 2, "randomness": 0.15},
    "Medium":   {"depth": 3, "randomness": 0.0},
    "Hard":     {"depth": 4, "randomness": 0.0}
}

# ---------------- MOVE LOGIC & SEARCH ----------------
def get_steps(pos, state):
    r, c = pos
    steps = []
    for dr, dc in NEIGHBORS:
        nr, nc = r + dr, c + dc
        if (nr, nc) in BOARD_POINTS and state.get((nr, nc), EMPTY) == EMPTY:
            steps.append((nr, nc))
    return steps

def get_jumps(pos, state, visited=None):
    if visited is None:
        visited = set()
    jumps = []
    r, c = pos
    for dr, dc in NEIGHBORS:
        mid = (r + dr, c + dc)
        land = (r + 2 * dr, c + 2 * dc)
        if mid in BOARD_POINTS and land in BOARD_POINTS:
            if state.get(mid, EMPTY) != EMPTY and state.get(land, EMPTY) == EMPTY:
                if land not in visited:
                    visited.add(land)
                    jumps.append(land)
                    jumps.extend(get_jumps(land, state, visited))
    return jumps

def get_moves_for_piece(pos, state):
    return list(set(get_steps(pos, state) + get_jumps(pos, state)))

def get_all_moves(state, player):
    moves = []
    for pos, occ in state.items():
        if occ == player:
            for dest in get_moves_for_piece(pos, state):
                moves.append((pos, dest))

    if player == AI:
        moves.sort(key=lambda m: (m[0][0] - m[1][0]), reverse=True)
    else:
        moves.sort(key=lambda m: (m[1][0] - m[0][0]), reverse=True)
    return moves

def check_win(state, player):
    camp = BOTTOM_CAMP if player == HUMAN else TOP_CAMP
    return all(state.get(p, EMPTY) == player for p in camp)

def evaluate(state):
    if check_win(state, AI):
        return 100000
    if check_win(state, HUMAN):
        return -100000

    ai_score, human_score = 0, 0
    for (r, c), occ in state.items():
        if occ == AI:
            dist = r + 0.25 * abs(c)
            ai_score += (14 - dist) * 12
            if (r, c) in TOP_CAMP:
                ai_score += 60
        elif occ == HUMAN:
            dist = (12 - r) + 0.25 * abs(c)
            human_score += (14 - dist) * 12
            if (r, c) in BOTTOM_CAMP:
                human_score += 60

    return ai_score - human_score

def minimax(state, depth, alpha, beta, maximizing):
    if depth == 0 or check_win(state, AI) or check_win(state, HUMAN):
        return evaluate(state), None

    moves = get_all_moves(state, AI if maximizing else HUMAN)
    if not moves:
        return evaluate(state), None

    best = moves[0]
    if maximizing:
        v = -math.inf
        for start, end in moves:
            state[start], state[end] = EMPTY, AI
            score, _ = minimax(state, depth - 1, alpha, beta, False)
            state[start], state[end] = AI, EMPTY
            if score > v:
                v, best = score, (start, end)
            alpha = max(alpha, v)
            if alpha >= beta:
                break
        return v, best
    else:
        v = math.inf
        for start, end in moves:
            state[start], state[end] = EMPTY, HUMAN
            score, _ = minimax(state, depth - 1, alpha, beta, True)
            state[start], state[end] = HUMAN, EMPTY
            if score < v:
                v, best = score, (start, end)
            beta = min(beta, v)
            if alpha >= beta:
                break
        return v, best


# ---------------- PARTICLES ----------------
class FireworkParticle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2.5, 9.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.decay = random.uniform(0.015, 0.035)
        self.alpha = 1.0
        self.gravity = 0.16
        self.radius = random.randint(2, 4)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.97
        self.alpha -= self.decay
        return self.alpha > 0


class MenuDriftingParticle:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.vx = random.uniform(-0.4, 0.4)
        self.vy = random.uniform(-0.5, -0.1)
        self.r = random.uniform(1.2, 3.2)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.y < -10:
            self.y = self.h + 10
            self.x = random.uniform(0, self.w)
        if self.x < -10:
            self.x = self.w + 10
        elif self.x > self.w + 10:
            self.x = -10



# ---------------- MASTER APPLICATION ----------------
class ChineseCheckersMaster:
    def __init__(self, root):
        self.root = root
        select_game_fonts(self.root)
        self.root.title("Chinese Checkers")
        self.root.geometry("1000x900")
        self.root.minsize(800, 850)
        self.root.resizable(True, True)

        try:
            self.root.attributes("-zoomed", False)
        except Exception:
            pass

        self.mode = "dark"
        self.human_theme = "ruby"
        self.ai_theme = "sapphire"
        self.difficulty = "Medium"

        # Responsive board metrics. These are recalculated from the actual
        # canvas size; no gameplay coordinate is hard-coded to a window size.
        self.w = 800
        self.h = 700
        self.spacing_y = 44
        self.spacing_x = 26
        self.ox = self.w / 2
        self.oy = self.h / 2 - 250
        self.hole_radius = 8
        self.marble_radius = 13

        self.ambient_stars = [
            (random.random(), random.random(), random.choice([1.0, 1.4, 1.8, 2.2]))
            for _ in range(42)
        ]
        self.menu_particles = []
        self.menu_anim_job = None
        self.menu_pulse_tick = 0

        # State
        self.state = {}
        self.turn = HUMAN
        self.selected = None
        self.valid_destinations = []
        self.animating = False
        self.anim_piece = None
        self.game_over = False
        self.is_paused = False
        self.move_count = 0
        self.winner = None

        # Timing
        self.start_time = 0
        self.elapsed_time = 0
        self.pause_start = 0

        # Visual animation state
        self.pulse_tick = 0
        self.hover_pos = None
        self.turn_banner_text = ""
        self.turn_banner_color = "#c8a96b"
        self.turn_banner_until = 0
        self.pulse_job = None
        self.timer_job = None
        self.ai_job = None
        self.animation_job = None
        self.firework_job = None
        self.configure_job = None
        self._jobs = set()

        # Fireworks
        self.particles = []

        # Sliding rules
        self.rules_offset_x = 0
        self.rules_target_x = 0
        self.rules_max_scroll = 190

        self.in_game = False

        self.container = tk.Frame(root, bg=self.theme["bg"])
        self.container.pack(fill=tk.BOTH, expand=True)
        self.root.bind("<Configure>", self.on_window_configure)

        self.apply_window_theme()
        self.show_rules_modal()

    @property
    def theme(self):
        return THEME_STYLES[self.mode]

    def apply_window_theme(self):
        self.root.configure(bg=self.theme["bg"])
        self.container.configure(bg=self.theme["bg"])

    def _after(self, delay, callback):
        """Schedule an after() job that removes itself from the cancellation set."""
        job_id = None

        def wrapped():
            if job_id in self._jobs:
                self._jobs.discard(job_id)
            try:
                callback()
            except tk.TclError:
                pass

        job_id = self.root.after(delay, wrapped)
        self._jobs.add(job_id)
        return job_id

    def _cancel_job(self, job_id):
        if job_id:
            try:
                self.root.after_cancel(job_id)
            except (tk.TclError, ValueError):
                pass
            self._jobs.discard(job_id)

    def cancel_animations(self):
        """Cancel every scheduled visual/game callback before changing screens."""
        for job_id in list(self._jobs):
            try:
                self.root.after_cancel(job_id)
            except (tk.TclError, ValueError):
                pass
        self._jobs.clear()
        self.menu_anim_job = None
        self.pulse_job = None
        self.timer_job = None
        self.ai_job = None
        self.animation_job = None
        self.firework_job = None
        self.configure_job = None

        # If a hop is interrupted by a state transition, put the marble back.
        if self.anim_piece:
            start = self.anim_piece.get("start")
            end = self.anim_piece.get("end")
            player = self.anim_piece.get("player")
            if start is not None and player is not None:
                self.state[start] = player
            if end is not None and end in self.state:
                self.state[end] = EMPTY
        self.anim_piece = None
        self.animating = False

    def toggle_dark_light(self):
        self.mode = "light" if self.mode == "dark" else "dark"
        self.apply_window_theme()
        if self.in_game:
            self.build_game_screen()
        else:
            self.show_rules_modal()

    def on_window_configure(self, event=None):
        """Keep every full-window surface centered and recompute board scale."""
        if self.configure_job:
            self._cancel_job(self.configure_job)

        def apply():
            self.configure_job = None
            try:
                cw = max(800, self.container.winfo_width())
                ch = max(850, self.container.winfo_height())
            except tk.TclError:
                return

            if hasattr(self, "menu_canvas") and self.menu_canvas.winfo_exists():
                self.menu_canvas.configure(width=cw, height=ch)
                if self.menu_particles:
                    for p in self.menu_particles:
                        p.w, p.h = cw, ch
                else:
                    self.menu_particles = [MenuDriftingParticle(cw, ch) for _ in range(50)]

            if hasattr(self, "card") and self.card.winfo_exists():
                card_w = min(720, max(680, cw - 40))
                self.card.place_configure(width=card_w)

            if hasattr(self, "rules_slider_canvas") and self.rules_slider_canvas.winfo_exists():
                self.rules_slider_canvas.configure(width=max(620, min(670, cw - 120)))
                self.rules_max_scroll = max(120, self.rules_slider_canvas.winfo_width() * 0.34)

            if hasattr(self, "canvas") and self.canvas.winfo_exists():
                self.canvas.configure(width=max(1, self.canvas.winfo_width()),
                                      height=max(1, self.canvas.winfo_height()))
                self.recompute_board_metrics()
                self.draw_board()

        self.configure_job = self._after(15, apply)

    # ---------------- START MENU & CURSOR-SLIDING RULES ----------------
    def show_rules_modal(self):
        self.in_game = False
        self.cancel_animations()
        self.particles.clear()
        self.hover_pos = None

        for w in self.container.winfo_children():
            w.destroy()

        cw = max(800, self.container.winfo_width() or 1000)
        ch = max(850, self.container.winfo_height() or 900)

        self.menu_canvas = tk.Canvas(
            self.container, width=cw, height=ch, bg=self.theme["bg"],
            highlightthickness=0
        )
        self.menu_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.menu_particles = [MenuDriftingParticle(cw, ch) for _ in range(55)]

        self.card = tk.Frame(
            self.container, bg=self.theme["card_bg"], padx=34, pady=22,
            highlightbackground=self.theme["card_border"], highlightthickness=1
        )
        self.card.place(relx=0.5, rely=0.5, anchor=tk.CENTER,
                        width=min(720, max(680, cw - 40)))

        top_bar = tk.Frame(self.card, bg=self.theme["card_bg"])
        top_bar.pack(fill=tk.X)
        mode_btn_text = "☀ Light" if self.mode == "dark" else "🌙 Dark"
        tk.Button(
            top_bar, text=mode_btn_text, command=self.toggle_dark_light,
            bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], relief=tk.FLAT,
            padx=12, pady=3, font=(FONT_TEXT, 9, "bold"), cursor="hand2"
        ).pack(side=tk.RIGHT)

        self.title_lbl = tk.Label(
            self.card, text="CHINESE CHECKERS",
            font=(FONT_NAME, 21, "bold"),
            fg=self.theme["text_main"], bg=self.theme["card_bg"]
        )
        self.title_lbl.pack()

        tk.Label(
            self.card, text="TACTICAL STAR-BOARD DUEL",
            font=(FONT_TEXT, 9, "bold"), fg="#c8a96b",
            bg=self.theme["card_bg"]
        ).pack(pady=(2, 10))

        self.rules_slider_canvas = tk.Canvas(
            self.card, width=620, height=105, bg=self.theme["btn_bg"],
            highlightthickness=1, highlightbackground=self.theme["card_border"],
            cursor="sb_h_double_arrow"
        )
        self.rules_slider_canvas.pack(fill=tk.X, pady=(0, 14))
        self.rules_slider_canvas.bind("<Motion>", self.on_rules_hover)
        self.rules_slider_canvas.bind("<Leave>", self.on_rules_leave)

        self.rules_offset_x = 0
        self.rules_target_x = 0
        self.render_sliding_rules()

        tk.Label(
            self.card, text="CHOOSE YOUR MARBLE COLOR",
            font=(FONT_TEXT, 9, "bold"),
            fg=self.theme["text_main"], bg=self.theme["card_bg"]
        ).pack(anchor="w")

        cf = tk.Frame(self.card, bg=self.theme["card_bg"])
        cf.pack(fill=tk.X, pady=(6, 14))

        self.color_var = tk.StringVar(value=self.human_theme)
        for key in ["ruby", "sapphire", "yellow", "emerald", "amethyst", "cyan"]:
            data = PALETTES[key]
            tk.Radiobutton(
                cf, text=f" {data['name']}", value=key, variable=self.color_var,
                bg=self.theme["card_bg"], fg=data["mid"],
                selectcolor=self.theme["btn_bg"],
                font=(FONT_TEXT, 9, "bold"),
                activebackground=self.theme["card_bg"],
                activeforeground=data["mid"], highlightthickness=0
            ).pack(side=tk.LEFT, padx=7)

        tk.Label(
            self.card, text="SELECT DIFFICULTY",
            font=(FONT_TEXT, 9, "bold"),
            fg=self.theme["text_main"], bg=self.theme["card_bg"]
        ).pack(anchor="w")

        df = tk.Frame(self.card, bg=self.theme["card_bg"])
        df.pack(fill=tk.X, pady=(6, 18))

        self.diff_var = tk.StringVar(value=self.difficulty)
        for d in ["Beginner", "Easy", "Medium", "Hard"]:
            tk.Radiobutton(
                df, text=f"  {d}", value=d, variable=self.diff_var,
                bg=self.theme["card_bg"], fg=self.theme["text_main"],
                selectcolor=self.theme["btn_bg"],
                font=(FONT_TEXT, 10),
                activebackground=self.theme["card_bg"],
                activeforeground=self.theme["text_main"],
                highlightthickness=0
            ).pack(side=tk.LEFT, padx=10)

        btn_frame = tk.Frame(self.card, bg=self.theme["card_bg"])
        btn_frame.pack(fill=tk.X, pady=(4, 0))

        tk.Button(
            btn_frame, text="💡 TIPS & STRATEGY",
            font=(FONT_TEXT, 10, "bold"),
            bg=self.theme["btn_bg"], fg=self.theme["btn_fg"],
            relief=tk.FLAT, padx=18, pady=9, cursor="hand2",
            command=lambda: self.show_tips_modal(from_game=False)
        ).pack(side=tk.LEFT, padx=(6, 0))

        self.start_btn = tk.Button(
            btn_frame, text="START MATCH ▶",
            font=(FONT_NAME, 10, "bold"),
            bg="#c8a96b", fg="#040813",
            activebackground="#9a7a3d", activeforeground="#ffffff",
            relief=tk.FLAT, padx=26, pady=9,
            cursor="hand2", command=self.start_game
        )
        self.start_btn.pack(side=tk.RIGHT, padx=(0, 6))

        self.animate_menu_loop()

    def on_rules_hover(self, event):
        canvas_width = max(1, self.rules_slider_canvas.winfo_width())
        ratio = max(0.0, min(1.0, event.x / canvas_width))
        self.rules_target_x = -ratio * self.rules_max_scroll

    def on_rules_leave(self, event):
        self.rules_target_x = 0

    def render_sliding_rules(self):
        if not hasattr(self, "rules_slider_canvas") or not self.rules_slider_canvas.winfo_exists():
            return

        self.rules_offset_x += (self.rules_target_x - self.rules_offset_x) * 0.22
        cv = self.rules_slider_canvas
        cv.delete("all")
        cw = max(1, cv.winfo_width())

        cv.create_text(
            16, 14, text="3 SIMPLE RULES TO PLAY   ◄ Move mouse here to slide ►",
            font=(FONT_TEXT, 8, "bold"), fill="#c8a96b", anchor="w"
        )

        base_x = 16 + self.rules_offset_x
        rules = [
            ("• 1. Goal: ", "Move all 6 of your marbles across the board into the opposite star point.", 38),
            ("• 2. Step: ", "Move 1 step in any direction into an empty connected hole.", 60),
            ("• 3. Jump: ", "Hop over any marble into an empty hole behind it. Chain multiple hops in 1 turn!", 82),
        ]

        for prefix, body, y in rules:
            text_id = cv.create_text(
                base_x, y, text=prefix, font=(FONT_TEXT, 9, "bold"),
                fill=self.theme["text_main"], anchor="w"
            )
            bbox = cv.bbox(text_id)
            prefix_w = (bbox[2] - bbox[0]) if bbox else 65
            cv.create_text(
                base_x + prefix_w, y, text=body,
                font=(FONT_TEXT, 9), fill=self.theme["text_sub"], anchor="w"
            )

        scroll_pct = abs(self.rules_offset_x) / max(1, self.rules_max_scroll)
        dot_cx = cw * 0.44 + scroll_pct * min(50, cw * 0.08)
        cv.create_oval(dot_cx - 3, 98, dot_cx + 3, 104, fill="#c8a96b", outline="")

    def animate_menu_loop(self):
        if not hasattr(self, "menu_canvas") or not self.menu_canvas.winfo_exists():
            return

        self.menu_canvas.delete("all")
        self.menu_pulse_tick += 1
        cw = max(1, self.menu_canvas.winfo_width())
        ch = max(1, self.menu_canvas.winfo_height())
        cx, cy = cw / 2, ch / 2

        for i, r_offset in enumerate([180, 270, 360, 460]):
            rad = r_offset + 5 * math.sin(self.menu_pulse_tick * 0.05 + i)
            self.menu_canvas.create_oval(
                cx - rad, cy - rad, cx + rad, cy + rad,
                outline=self.theme["bg_accent"], width=1, dash=(3, 9)
            )

        p_col = self.theme["menu_particle"]
        for p in self.menu_particles:
            p.update()
            self.menu_canvas.create_oval(
                p.x - p.r, p.y - p.r, p.x + p.r, p.y + p.r,
                fill=p_col, outline=""
            )

        title_colors = [
            "#f8fafc", "#e0f2fe", "#bae6fd", "#7dd3fc",
            "#c8a96b", "#7dd3fc", "#bae6fd", "#e0f2fe"
        ]
        if self.mode == "dark" and hasattr(self, "title_lbl"):
            self.title_lbl.config(fg=title_colors[(self.menu_pulse_tick // 4) % len(title_colors)])

        self.render_sliding_rules()
        self.menu_anim_job = self._after(30, self.animate_menu_loop)

    # ---------------- TIPS MODAL ----------------
    def show_tips_modal(self, from_game=False):
        if from_game and not self.is_paused and not self.game_over:
            self.toggle_pause()

        overlay = tk.Frame(self.container, bg=self.theme["bg"])
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        card = tk.Frame(
            overlay, bg=self.theme["card_bg"], padx=34, pady=26,
            highlightbackground=self.theme["card_border"], highlightthickness=1
        )
        card.place(relx=0.5, rely=0.5, anchor=tk.CENTER,
                   width=min(720, max(680, self.container.winfo_width() - 40)))

        tk.Label(
            card, text="STRATEGY GUIDE",
            font=(FONT_NAME, 19, "bold"),
            fg=self.theme["text_main"], bg=self.theme["card_bg"]
        ).pack()
        tk.Label(
            card, text="HOW TO WIN FASTER",
            font=(FONT_TEXT, 8, "bold"), fg="#c8a96b",
            bg=self.theme["card_bg"]
        ).pack(pady=(2, 14))

        tips = [
            ("1. Build 'Hop Highways'",
             "Keep your marbles spaced with 1 empty hole between them. This creates giant jumping tracks to leap across the board in 1 turn."),
            ("2. No Marble Left Behind",
             "Keep your pieces moving together. A marble left stranded at home has no teammates to jump over and will crawl very slowly."),
            ("3. Fill the Back Rows First",
             "When reaching the enemy camp, land in the deepest corner spots first so your remaining pieces have room to jump in."),
            ("4. Block the AI",
             "Step into spaces right ahead of the AI's marbles to ruin their jump tracks and force them into single steps.")
        ]

        for title, desc in tips:
            tf = tk.Frame(card, bg=self.theme["card_bg"])
            tf.pack(fill=tk.X, pady=(0, 10))
            tk.Label(
                tf, text=title, font=(FONT_TEXT, 10, "bold"),
                fg="#c8a96b", bg=self.theme["card_bg"]
            ).pack(anchor="w")
            tk.Label(
                tf, text=desc, font=(FONT_TEXT, 9),
                fg=self.theme["text_sub"], bg=self.theme["card_bg"],
                wraplength=620, justify=tk.LEFT
            ).pack(anchor="w")

        def close_tips():
            overlay.destroy()
            if from_game and self.is_paused and not self.game_over:
                self.toggle_pause()

        btn_text = "← RESUME MATCH" if from_game else "← BACK TO MENU"
        tk.Button(
            card, text=btn_text, font=(FONT_TEXT, 10, "bold"),
            bg=self.theme["btn_bg"], fg=self.theme["btn_fg"],
            relief=tk.FLAT, padx=20, pady=8, cursor="hand2",
            command=close_tips
        ).pack(pady=(10, 0))

    def start_game(self):
        self.cancel_animations()
        self.human_theme = self.color_var.get()
        self.difficulty = self.diff_var.get()

        contrasts = {
            "ruby": "sapphire", "sapphire": "ruby", "yellow": "sapphire",
            "emerald": "ruby", "amethyst": "yellow", "cyan": "ruby"
        }
        self.ai_theme = contrasts.get(self.human_theme, "sapphire")

        self.reset_state()
        self.build_game_screen()

    # ---------------- MAIN BOARD SCREEN ----------------
    def build_game_screen(self):
        self.in_game = True
        self.cancel_animations()

        for w in self.container.winfo_children():
            w.destroy()

        header = tk.Frame(
            self.container, bg=self.theme["header_bg"],
            pady=10, padx=20
        )
        header.pack(fill=tk.X, padx=20, pady=(12, 0))

        tb = tk.Frame(header, bg=self.theme["header_bg"])
        tb.pack(side=tk.LEFT)

        col = PALETTES[self.human_theme]["glow"]
        self.status_lbl = tk.Label(
            tb, text=f"● Your Turn ({PALETTES[self.human_theme]['name']})",
            fg=col, bg=self.theme["header_bg"],
            font=(FONT_NAME, 11, "bold")
        )
        self.status_lbl.pack(anchor="w")

        self.sub_lbl = tk.Label(
            tb, text="Level: " + self.difficulty + "  |  Time: 00:00",
            fg=self.theme["text_sub"], bg=self.theme["header_bg"],
            font=(FONT_TEXT, 9)
        )
        self.sub_lbl.pack(anchor="w")

        cb = tk.Frame(header, bg=self.theme["header_bg"])
        cb.pack(side=tk.RIGHT)

        mode_text = "☀ Light" if self.mode == "dark" else "🌙 Dark"
        self.theme_btn = tk.Button(
            cb, text=mode_text, command=self.toggle_dark_light,
            bg=self.theme["btn_bg"], fg=self.theme["btn_fg"],
            relief=tk.FLAT, padx=10, pady=5,
            font=(FONT_TEXT, 9, "bold"), cursor="hand2"
        )
        self.theme_btn.pack(side=tk.LEFT, padx=4)

        tk.Button(
            cb, text="💡 Tips",
            command=lambda: self.show_tips_modal(from_game=True),
            bg=self.theme["btn_bg"], fg=self.theme["btn_fg"],
            relief=tk.FLAT, padx=10, pady=5,
            font=(FONT_TEXT, 9, "bold"), cursor="hand2"
        ).pack(side=tk.LEFT, padx=4)

        self.pause_btn = tk.Button(
            cb, text="❚❚ Pause", command=self.toggle_pause,
            bg=self.theme["btn_bg"], fg=self.theme["btn_fg"],
            relief=tk.FLAT, padx=12, pady=5,
            font=(FONT_TEXT, 9, "bold"), cursor="hand2"
        )
        self.pause_btn.pack(side=tk.LEFT, padx=4)

        tk.Button(
            cb, text="↺ Reset", command=self.show_rules_modal,
            bg="#ef4444", fg="#ffffff", relief=tk.FLAT,
            padx=12, pady=5, font=(FONT_TEXT, 9, "bold"),
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=4)

        self.canvas = tk.Canvas(
            self.container, bg=self.theme["bg"],
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<Leave>", self.on_canvas_leave)
        self.canvas.bind("<Configure>", self.on_board_configure)

        self.root.update_idletasks()
        self.recompute_board_metrics()
        self.update_timer()
        self.start_visual_loop()
        self.show_turn_banner(
            f"YOUR TURN • {PALETTES[self.human_theme]['name'].upper()}",
            PALETTES[self.human_theme]["glow"]
        )
        self.draw_board()

    def reset_state(self):
        self.state = {p: EMPTY for p in BOARD_POINTS}
        for p in TOP_CAMP:
            self.state[p] = HUMAN
        for p in BOTTOM_CAMP:
            self.state[p] = AI

        self.turn = HUMAN
        self.selected = None
        self.valid_destinations = []
        self.animating = False
        self.anim_piece = None
        self.game_over = False
        self.is_paused = False
        self.move_count = 0
        self.winner = None
        self.start_time = time.time()
        self.elapsed_time = 0
        self.hover_pos = None
        self.pulse_tick = 0

    def update_timer(self):
        if not self.game_over and self.in_game:
            if not self.is_paused:
                self.elapsed_time = int(time.time() - self.start_time)
                mins = self.elapsed_time // 60
                secs = self.elapsed_time % 60
                if hasattr(self, "sub_lbl") and self.sub_lbl.winfo_exists():
                    self.sub_lbl.config(
                        text=f"Level: {self.difficulty}  |  Time: {mins:02d}:{secs:02d}"
                    )
            self.timer_job = self._after(1000, self.update_timer)

    def toggle_pause(self):
        if self.game_over or self.animating:
            return

        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_start = time.time()
            self.pause_btn.config(
                text="▶ Resume", bg="#059669", fg="#ffffff"
            )
            self.status_lbl.config(text="Game Paused", fg="#fbbf24")
        else:
            self.start_time += time.time() - self.pause_start
            self.pause_btn.config(
                text="❚❚ Pause",
                bg=self.theme["btn_bg"], fg=self.theme["btn_fg"]
            )
            col = (
                PALETTES[self.human_theme]["glow"]
                if self.turn == HUMAN
                else PALETTES[self.ai_theme]["glow"]
            )
            label = (
                f"● Your Turn ({PALETTES[self.human_theme]['name']})"
                if self.turn == HUMAN else "● AI Turn"
            )
            self.status_lbl.config(text=label, fg=col)
            if self.turn == AI:
                self.ai_job = self._after(100, self.ai_turn)
        self.draw_board()

    # ---------------- RESPONSIVE GEOMETRY ----------------
    def on_board_configure(self, event=None):
        self.recompute_board_metrics()
        self.draw_board()

    def recompute_board_metrics(self):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return

        self.w = max(1, self.canvas.winfo_width())
        self.h = max(1, self.canvas.winfo_height())

        # The topology spans 16 horizontal column units and 12 vertical rows.
        # Hex-star geometry uses a 0.59 horizontal/vertical unit ratio.
        unit = min((self.w - 90) / 16.0, (self.h - 90) / 12.0)
        unit = max(20.0, unit)

        self.spacing_y = unit
        self.spacing_x = unit * 0.59

        board_width = 16 * self.spacing_x
        board_height = 12 * self.spacing_y

        self.ox = self.w / 2.0
        self.oy = (self.h - board_height) / 2.0

        self.hole_radius = max(6.0, min(12.5, unit * 0.19))
        self.marble_radius = max(10.0, min(19.0, unit * 0.31))

    def grid_to_px(self, r, c):
        return self.ox + c * self.spacing_x, self.oy + r * self.spacing_y

    def px_to_grid(self, px, py):
        best = None
        min_dist = max(18.0, self.hole_radius * 2.2)
        for p in BOARD_POINTS:
            x, y = self.grid_to_px(*p)
            d = math.hypot(px - x, py - y)
            if d < min_dist:
                min_dist, best = d, p
        return best

    # ---------------- HIGH-FIDELITY BOARD RENDERING ----------------
    def _mix_hex(self, a, b, t):
        """Small standard-library color mixer used for procedural layers."""
        t = max(0.0, min(1.0, t))
        a = a.lstrip("#")
        b = b.lstrip("#")
        vals = [
            int(int(a[i:i+2], 16) * (1 - t) + int(b[i:i+2], 16) * t)
            for i in (0, 2, 4)
        ]
        return "#" + "".join(f"{v:02x}" for v in vals)

    def draw_background_pattern(self):
        cx, cy = self.w / 2.0, self.h / 2.0
        accent = self.theme["bg_accent"]
        star_color = self.theme["bg_star"]

        # Layered "brushed slate" rings.
        max_rad = max(self.w, self.h) * 0.72
        ring_step = max(38, min(92, max_rad / 8))
        ring_count = int(max_rad / ring_step)

        for i in range(ring_count, 0, -1):
            rad = i * ring_step
            wobble = 4 * math.sin(self.pulse_tick * 0.012 + i * 0.7)
            col = accent if i % 2 else self._mix_hex(accent, self.theme["bg"], 0.35)
            self.canvas.create_oval(
                cx - rad + wobble, cy - rad,
                cx + rad + wobble, cy + rad,
                outline=col, width=1, dash=(2 + i % 3, 12)
            )

        # Radar spokes and constellation-like nodes.
        for angle_deg in range(0, 360, 15):
            angle = math.radians(angle_deg)
            inner = min(self.w, self.h) * 0.10
            outer = max(self.w, self.h) * 0.55
            x1 = cx + math.cos(angle) * inner
            y1 = cy + math.sin(angle) * inner
            x2 = cx + math.cos(angle) * outer
            y2 = cy + math.sin(angle) * outer
            self.canvas.create_line(
                x1, y1, x2, y2, fill=accent, width=1, dash=(1, 13)
            )

        for i in range(24):
            angle = i * (math.tau / 24.0) + 0.15 * math.sin(i)
            rad = min(self.w, self.h) * (0.20 + (i % 5) * 0.065)
            x = cx + math.cos(angle) * rad
            y = cy + math.sin(angle) * rad
            nr = 1.5 + (i % 3) * 0.7
            self.canvas.create_oval(
                x - nr, y - nr, x + nr, y + nr,
                fill=star_color, outline=""
            )
            if i % 2 == 0:
                prev_angle = angle - 0.23
                px = cx + math.cos(prev_angle) * rad
                py = cy + math.sin(prev_angle) * rad
                self.canvas.create_line(
                    px, py, x, y, fill=accent, width=1
                )

        # Deterministic pseudo wood/slate grain: no external image dependency.
        for i in range(90):
            phase = i * 1.731
            x = (cx + math.sin(phase * 2.17) * self.w * 0.48)
            y = (cy + math.cos(phase * 1.31) * self.h * 0.48)
            length = 6 + (i % 7) * 2
            self.canvas.create_line(
                x, y, x + length, y + math.sin(phase) * 2,
                fill=accent, width=1
            )

    def draw_board_base(self):
        # Broad shadow under the star board.
        min_x = self.ox - 8 * self.spacing_x
        max_x = self.ox + 8 * self.spacing_x
        min_y = self.oy
        max_y = self.oy + 12 * self.spacing_y
        for i in range(10, 0, -1):
            grow = i * 2.2
            self.canvas.create_polygon(
                min_x - grow, min_y + grow,
                self.ox, min_y - grow,
                max_x + grow, min_y + grow,
                self.ox, max_y + grow,
                fill=self._mix_hex(self.theme["bg"], "#000000", 0.25),
                outline=""
            )

        # Layered star silhouette, built from the same board topology bounds.
        pts = [
            (self.ox, min_y - 18),
            (self.ox + 4 * self.spacing_x, min_y + 4 * self.spacing_y),
            (self.ox + 8 * self.spacing_x, min_y + 4 * self.spacing_y),
            (self.ox + 4 * self.spacing_x, self.oy + 6 * self.spacing_y),
            (self.ox + 8 * self.spacing_x, max_y),
            (self.ox, self.oy + 9 * self.spacing_y),
            (self.ox - 8 * self.spacing_x, max_y),
            (self.ox - 4 * self.spacing_x, self.oy + 6 * self.spacing_y),
            (self.ox - 8 * self.spacing_x, min_y + 4 * self.spacing_y),
            (self.ox - 4 * self.spacing_x, min_y + 4 * self.spacing_y),
        ]
        self.canvas.create_polygon(
            pts, fill=self._mix_hex(self.theme["hole_fill"], self.theme["bg"], 0.25),
            outline=self.theme["card_border"], width=2
        )

        # Inner border creates depth without requiring image filters.
        inset = max(5, self.spacing_y * 0.12)
        pts2 = [
            (x + (inset if x < self.ox else -inset), y + inset)
            for x, y in pts
        ]
        self.canvas.create_line(
            pts2 + [pts2[0]], fill=self.theme["bg_accent"], width=2
        )

    def _draw_hole(self, cx, cy, pos):
        r = self.hole_radius
        hole = self.theme["hole_fill"]
        outline = self.theme["hole_outline"]

        # Recess shadow, top-left bevel, dark inner well, and bottom-right specular.
        self.canvas.create_oval(
            cx - r - 2, cy - r + 2, cx + r + 3, cy + r + 4,
            fill=self._mix_hex(self.theme["bg"], "#000000", 0.38), outline=""
        )
        self.canvas.create_oval(
            cx - r - 1.5, cy - r - 1.5, cx + r + 1.5, cy + r + 1.5,
            fill=self._mix_hex(outline, "#000000", 0.22),
            outline=""
        )
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=hole, outline=outline, width=1.2
        )
        self.canvas.create_arc(
            cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1,
            start=110, extent=150, style=tk.ARC,
            outline=self._mix_hex(outline, "#ffffff", 0.18), width=1.1
        )
        self.canvas.create_arc(
            cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1,
            start=285, extent=115, style=tk.ARC,
            outline=self._mix_hex(outline, "#ffffff", 0.42), width=1.0
        )

        if pos in TOP_CAMP:
            camp = self.theme["top_camp_fill"]
            self.canvas.create_oval(
                cx - r * 0.62, cy - r * 0.62,
                cx + r * 0.62, cy + r * 0.62,
                fill=camp, outline=""
            )
        elif pos in BOTTOM_CAMP:
            camp = self.theme["bottom_camp_fill"]
            self.canvas.create_oval(
                cx - r * 0.62, cy - r * 0.62,
                cx + r * 0.62, cy + r * 0.62,
                fill=camp, outline=""
            )

    def draw_board(self):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return

        self.canvas.delete("all")
        self.draw_background_pattern()
        self.draw_board_base()

        # Network lines beneath the wells.
        for r, c in BOARD_POINTS:
            x1, y1 = self.grid_to_px(r, c)
            for dr, dc in [(-1, 1), (0, 2), (1, 1)]:
                neighbor = (r + dr, c + dc)
                if neighbor in BOARD_POINTS:
                    x2, y2 = self.grid_to_px(*neighbor)
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=self.theme["line_color"],
                        width=max(1.0, self.spacing_y * 0.055)
                    )

        # Selection-to-destination guidance.
        if self.selected and self.valid_destinations and not self.is_paused and not self.game_over:
            sx, sy = self.grid_to_px(*self.selected)
            glow = PALETTES[self.human_theme]["glow"]
            for dest in self.valid_destinations:
                dx, dy = self.grid_to_px(*dest)
                self.canvas.create_line(
                    sx, sy, dx, dy, fill=glow, width=1.4, dash=(4, 5)
                )

        # Holes and destinations.
        for pos in BOARD_POINTS:
            cx, cy = self.grid_to_px(*pos)
            self._draw_hole(cx, cy, pos)

            interactive = not self.is_paused and not self.game_over
            pulse = 0.5 + 0.5 * math.sin(self.pulse_tick * 0.14)

            if pos in self.valid_destinations and interactive:
                glow = PALETTES[self.human_theme]["glow"]
                rr = self.hole_radius + 7 + pulse * 3
                self.canvas.create_oval(
                    cx - rr, cy - rr, cx + rr, cy + rr,
                    outline=glow, width=1.5
                )
                self.canvas.create_oval(
                    cx - 3, cy - 3, cx + 3, cy + 3,
                    fill=glow, outline=""
                )

            if pos == self.hover_pos and interactive:
                hover_color = (
                    PALETTES[self.human_theme]["glow"]
                    if self.state.get(pos) == HUMAN or pos in self.valid_destinations
                    else "#94a3b8"
                )
                rr = self.hole_radius + 4
                self.canvas.create_oval(
                    cx - rr, cy - rr, cx + rr, cy + rr,
                    outline=hover_color, width=1.2
                )

        # Marbles.
        for pos in BOARD_POINTS:
            occ = self.state[pos]
            if occ == EMPTY:
                continue
            if self.anim_piece and self.anim_piece["pos"] == pos:
                continue

            cx, cy = self.grid_to_px(*pos)
            is_sel = (
                pos == self.selected
                and not self.is_paused
                and not self.game_over
            )
            is_hover = (
                pos == self.hover_pos
                and occ == HUMAN
                and self.turn == HUMAN
                and not self.is_paused
                and not self.game_over
            )
            theme = self.human_theme if occ == HUMAN else self.ai_theme
            self.render_marble(cx, cy, theme, is_sel, is_hover)

        if self.anim_piece:
            self.render_marble(
                self.anim_piece["x"], self.anim_piece["y"],
                self.anim_piece["theme"], False, False,
                scale=self.anim_piece.get("scale", 1.0),
                airborne=True,
                shadow_scale=self.anim_piece.get("shadow_scale", 1.0)
            )

        if self.is_paused:
            self._draw_overlay(self.theme["modal_dim"])
            self.canvas.create_text(
                self.w / 2, self.h / 2 - 15,
                text="GAME PAUSED",
                font=(FONT_NAME, 24, "bold"),
                fill=self.theme["text_main"]
            )
            self.canvas.create_text(
                self.w / 2, self.h / 2 + 24,
                text="Click Resume to continue",
                font=(FONT_TEXT, 11),
                fill=self.theme["text_sub"]
            )

        if self.game_over:
            self.draw_fireworks()
            self.draw_victory_card()
        elif self.turn_banner_until > time.time() and self.turn_banner_text:
            self.draw_turn_banner()

    def _draw_overlay(self, fill):
        self.canvas.create_rectangle(
            0, 0, self.w, self.h, fill=fill, stipple="gray50", outline=""
        )

    def render_marble(
        self, cx, cy, theme_key, selected=False, hovered=False,
        scale=1.0, airborne=False, shadow_scale=1.0
    ):
        theme = PALETTES[theme_key]
        r = self.marble_radius * scale
        shadow_scale = max(0.25, shadow_scale)

        # Elevated cast shadow.
        shadow_y = cy + r * (0.32 + (1.0 - shadow_scale) * 0.8)
        sr_x = r * (1.10 + shadow_scale * 0.18)
        sr_y = r * 0.40 * shadow_scale
        shadow = "#02050a" if self.mode == "dark" else "#64748b"
        self.canvas.create_oval(
            cx - sr_x, shadow_y - sr_y,
            cx + sr_x, shadow_y + sr_y,
            fill=shadow, outline=""
        )

        if selected:
            pulse = 0.5 + 0.5 * math.sin(self.pulse_tick * 0.16)
            rr = r + 7 + pulse * 3
            self.canvas.create_oval(
                cx - rr, cy - rr, cx + rr, cy + rr,
                outline=theme["glow"], width=1.7
            )

        if hovered and not selected:
            self.canvas.create_oval(
                cx - r - 4, cy - r - 4,
                cx + r + 4, cy + r + 4,
                outline=theme["glow"], width=1.0
            )

        # Main gem body.
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=theme["base"], outline=theme["rim"], width=1.5
        )
        self.canvas.create_oval(
            cx - r * 0.86, cy - r * 0.86,
            cx + r * 0.86, cy + r * 0.86,
            fill=theme["mid"], outline=""
        )
        self.canvas.create_oval(
            cx - r * 0.67, cy - r * 0.67,
            cx + r * 0.67, cy + r * 0.67,
            fill=self._mix_hex(theme["mid"], "#ffffff", 0.10),
            outline=""
        )

        # Inner refraction halo.
        self.canvas.create_arc(
            cx - r * 0.76, cy - r * 0.76,
            cx + r * 0.76, cy + r * 0.76,
            start=35, extent=105, style=tk.ARC,
            outline=self._mix_hex(theme["glow"], "#ffffff", 0.28), width=max(1, r * 0.08)
        )

        # Multi-layer specular highlight.
        hx, hy = cx - r * 0.34, cy - r * 0.38
        self.canvas.create_oval(
            hx - r * 0.20, hy - r * 0.14,
            hx + r * 0.20, hy + r * 0.14,
            fill="#ffffff", outline=""
        )
        self.canvas.create_oval(
            cx - r * 0.10, cy - r * 0.67,
            cx + r * 0.08, cy - r * 0.49,
            fill=self._mix_hex(theme["glow"], "#ffffff", 0.65),
            outline=""
        )

        # Tiny bottom refraction glint.
        self.canvas.create_arc(
            cx - r * 0.72, cy - r * 0.72,
            cx + r * 0.72, cy + r * 0.72,
            start=210, extent=65, style=tk.ARC,
            outline=self._mix_hex(theme["base"], "#ffffff", 0.30), width=1
        )

    # ---------------- SMOOTH HOP ANIMATION ----------------
    def animate_move(self, start_pos, end_pos, player, on_complete):
        self.animating = True
        sx, sy = self.grid_to_px(*start_pos)
        ex, ey = self.grid_to_px(*end_pos)
        theme = self.human_theme if player == HUMAN else self.ai_theme

        self.state[start_pos] = EMPTY
        self.anim_piece = {
            "x": sx, "y": sy, "pos": start_pos,
            "start": start_pos, "end": end_pos, "player": player,
            "theme": theme, "scale": 1.0, "shadow_scale": 1.0
        }

        total_frames = max(22, int(170 / 8))
        hop_height = max(18.0, self.spacing_y * 0.62)

        def step(frame=0):
            if not self.animating or not self.anim_piece:
                return

            if frame >= total_frames:
                self.anim_piece = None
                self.state[end_pos] = player
                self.animating = False
                self.draw_board()
                on_complete()
                return

            t = frame / float(total_frames)
            # Smoothstep gives a soft launch/landing while the requested
            # parabolic component supplies the characteristic hop.
            ease = t * t * (3.0 - 2.0 * t)
            x = sx + (ex - sx) * ease
            y_linear = sy + (ey - sy) * ease
            y = y_linear - 4.0 * hop_height * t * (1.0 - t)

            # Squeeze/stretch: elongate slightly during flight and squash at landing.
            flight = math.sin(math.pi * t)
            stretch = 1.0 + 0.075 * flight
            landing = max(0.0, (t - 0.88) / 0.12)
            squash = 1.0 + 0.12 * math.sin(math.pi * landing)
            scale = stretch * squash

            shadow_scale = 1.0 - 0.58 * flight

            self.anim_piece.update({
                "x": x, "y": y, "pos": start_pos,
                "scale": scale, "shadow_scale": shadow_scale
            })
            self.draw_board()
            self.animation_job = self._after(14, lambda: step(frame + 1))

        step()

    # ---------------- FIREWORKS ----------------
    def spawn_firework(self):
        cx = random.randint(80, max(80, int(self.w - 80)))
        cy = random.randint(80, max(80, int(self.h * 0.60)))
        palette = [
            "#f43f5e", "#c8a96b", "#34d399",
            "#facc15", "#a855f7", "#fb923c", "#ffffff"
        ]
        burst_color = random.choice(palette)
        for _ in range(random.randint(32, 46)):
            self.particles.append(FireworkParticle(cx, cy, burst_color))

    def update_fireworks_loop(self):
        if not self.game_over:
            return

        if random.random() < 0.18:
            self.spawn_firework()

        alive = []
        for p in self.particles:
            if p.update():
                # Keep a short motion trail for each spark.
                if not hasattr(p, "trail"):
                    p.trail = []
                p.trail.append((p.x, p.y))
                if len(p.trail) > 5:
                    p.trail.pop(0)
                alive.append(p)
        self.particles = alive
        self.draw_board()
        self.firework_job = self._after(28, self.update_fireworks_loop)

    def draw_fireworks(self):
        for p in self.particles:
            trail = getattr(p, "trail", [])
            for i, (tx, ty) in enumerate(trail):
                radius = max(0.7, p.radius * (i + 1) / max(1, len(trail)) * 0.55)
                self.canvas.create_oval(
                    tx - radius, ty - radius, tx + radius, ty + radius,
                    fill=p.color, outline=""
                )
            r = p.radius * max(0.35, p.alpha)
            self.canvas.create_oval(
                p.x - r, p.y - r, p.x + r, p.y + r,
                fill=p.color, outline=""
            )

    def draw_victory_card(self):
        self._draw_overlay(self.theme["modal_dim"])

        cw = min(520, self.w - 60)
        ch = min(290, self.h - 60)
        x1 = (self.w - cw) / 2
        y1 = (self.h - ch) / 2
        x2 = x1 + cw
        y2 = y1 + ch

        self.canvas.create_rectangle(
            x1 + 8, y1 + 8, x2 + 8, y2 + 8,
            fill="#010307" if self.mode == "dark" else "#cbd5e1",
            outline=""
        )
        edge = "#34d399" if self.winner == HUMAN else "#f43f5e"
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=self.theme["card_bg"], outline=edge, width=2.5
        )

        mins = self.elapsed_time // 60
        secs = self.elapsed_time % 60
        time_str = f"{mins:02d}m {secs:02d}s"

        if self.winner == HUMAN:
            title_text = "★ VICTORY! ★"
            title_color = "#34d399"
            sub_text = "You conquered the opposing camp!"
        else:
            title_text = "DEFEAT"
            title_color = "#f43f5e"
            sub_text = "AI reached your camp first!"

        self.canvas.create_text(
            (x1 + x2) / 2, y1 + 48,
            text=title_text, font=(FONT_NAME, 26, "bold"),
            fill=title_color
        )
        self.canvas.create_text(
            (x1 + x2) / 2, y1 + 88,
            text=sub_text, font=(FONT_TEXT, 11),
            fill=self.theme["text_sub"]
        )

        stat_y = y1 + 140
        box_w = min(185, cw * 0.36)
        self.canvas.create_rectangle(
            x1 + 40, stat_y - 12, x1 + 40 + box_w, stat_y + 38,
            fill=self.theme["btn_bg"], outline=self.theme["card_border"]
        )
        self.canvas.create_text(
            x1 + 40 + box_w / 2, stat_y,
            text="TIME PLAYED", font=(FONT_TEXT, 8, "bold"),
            fill=self.theme["text_sub"]
        )
        self.canvas.create_text(
            x1 + 40 + box_w / 2, stat_y + 19,
            text=time_str, font=(FONT_NAME, 12, "bold"),
            fill=self.theme["text_main"]
        )

        self.canvas.create_rectangle(
            x2 - 40 - box_w, stat_y - 12, x2 - 40, stat_y + 38,
            fill=self.theme["btn_bg"], outline=self.theme["card_border"]
        )
        self.canvas.create_text(
            x2 - 40 - box_w / 2, stat_y,
            text="TURNS TAKEN", font=(FONT_TEXT, 8, "bold"),
            fill=self.theme["text_sub"]
        )
        self.canvas.create_text(
            x2 - 40 - box_w / 2, stat_y + 19,
            text=f"{self.move_count} moves",
            font=(FONT_NAME, 12, "bold"),
            fill=self.theme["text_main"]
        )

        btn_y = y2 - 48
        self.canvas.create_rectangle(
            x1 + cw * 0.30, btn_y - 19,
            x2 - cw * 0.30, btn_y + 19,
            fill="#2563eb", outline="#60a5fa", width=1.5
        )
        self.canvas.create_text(
            (x1 + x2) / 2, btn_y,
            text="PLAY AGAIN ↺",
            font=(FONT_TEXT, 11, "bold"), fill="#ffffff"
        )

    # ---------------- HOVER / TURN POLISH ----------------
    def on_canvas_motion(self, event):
        if not hasattr(self, "canvas") or self.animating:
            return
        pos = self.px_to_grid(event.x, event.y)
        if pos != self.hover_pos:
            self.hover_pos = pos
            interactive = (
                self.turn == HUMAN and
                not self.is_paused and
                not self.game_over
            )
            self.canvas.configure(
                cursor="hand2" if interactive and (
                    (pos and self.state.get(pos) == HUMAN) or
                    (pos in self.valid_destinations if pos else False)
                ) else "arrow"
            )
            self.draw_board()

    def on_canvas_leave(self, event):
        if self.hover_pos is not None:
            self.hover_pos = None
            self.canvas.configure(cursor="arrow")
            self.draw_board()

    def start_visual_loop(self):
        if self.pulse_job:
            self._cancel_job(self.pulse_job)

        def tick():
            if not self.in_game:
                return
            self.pulse_tick += 1
            if self.turn_banner_until <= time.time():
                self.turn_banner_text = ""
            self.draw_board()
            self.pulse_job = self._after(35, tick)

        self.pulse_job = self._after(35, tick)

    def show_turn_banner(self, text, color):
        self.turn_banner_text = text
        self.turn_banner_color = color
        self.turn_banner_until = time.time() + 0.95
        self.draw_board()

    def draw_turn_banner(self):
        progress = max(0.0, min(1.0, self.turn_banner_until - time.time()))
        alpha_like = 0.65 + 0.35 * min(1.0, progress * 3)
        y = max(48, self.h * 0.08)
        bw = min(440, self.w * 0.58)
        bh = 42
        x1 = self.w / 2 - bw / 2
        x2 = self.w / 2 + bw / 2

        self.canvas.create_rectangle(
            x1, y - bh / 2, x2, y + bh / 2,
            fill=self._mix_hex(self.theme["card_bg"], self.turn_banner_color, 0.08),
            outline=self.turn_banner_color, width=1.5
        )
        self.canvas.create_text(
            self.w / 2, y,
            text=self.turn_banner_text,
            font=(FONT_TEXT, 10, "bold"),
            fill=self.turn_banner_color
        )

    # ---------------- TURNS & ACTIONS ----------------
    def on_click(self, event):
        if self.game_over:
            cw = min(520, self.w - 60)
            ch = min(290, self.h - 60)
            x1 = (self.w - cw) / 2
            y1 = (self.h - ch) / 2
            x2 = x1 + cw
            btn_y = y1 + ch - 48
            if (x1 + cw * 0.30) <= event.x <= (x2 - cw * 0.30) and \
               (btn_y - 19) <= event.y <= (btn_y + 19):
                self.show_rules_modal()
            return

        if self.turn != HUMAN or self.animating or self.is_paused:
            return

        clicked = self.px_to_grid(event.x, event.y)
        if not clicked:
            return

        if self.state[clicked] == HUMAN:
            self.selected = clicked
            self.valid_destinations = get_moves_for_piece(clicked, self.state)
            self.draw_board()
            return

        if self.selected and clicked in self.valid_destinations:
            start = self.selected
            dest = clicked
            self.selected = None
            self.valid_destinations = []
            self.move_count += 1
            self.animate_move(start, dest, HUMAN, self.after_human_move)

    def after_human_move(self):
        if check_win(self.state, HUMAN):
            self.game_over = True
            self.winner = HUMAN
            self.status_lbl.config(text="★ VICTORY! ★", fg="#34d399")
            self.show_turn_banner("VICTORY", "#34d399")
            self.particles.clear()
            self.update_fireworks_loop()
            return

        self.turn = AI
        col = PALETTES[self.ai_theme]["glow"]
        self.status_lbl.config(text="● AI is searching jumps...", fg=col)
        self.show_turn_banner("AI THINKING", col)
        self.ai_job = self._after(180, self.ai_turn)

    def ai_turn(self):
        if self.is_paused or self.game_over:
            return

        diff = DIFFICULTIES[self.difficulty]
        depth = diff["depth"]
        randomness = diff["randomness"]

        all_ai_moves = get_all_moves(self.state, AI)
        if not all_ai_moves:
            return

        if randomness > 0 and random.random() < randomness:
            best_move = random.choice(
                all_ai_moves[:max(2, len(all_ai_moves) // 2)]
            )
        else:
            _, best_move = minimax(
                self.state, depth, -math.inf, math.inf, True
            )

        if not best_move:
            best_move = all_ai_moves[0]

        start, end = best_move
        self.animate_move(start, end, AI, self.after_ai_move)

    def after_ai_move(self):
        if check_win(self.state, AI):
            self.game_over = True
            self.winner = AI
            self.status_lbl.config(text="✖ DEFEAT", fg="#f43f5e")
            self.show_turn_banner("AI REACHED YOUR CAMP", "#f43f5e")
            self.draw_board()
            return

        self.turn = HUMAN
        col = PALETTES[self.human_theme]["glow"]
        self.status_lbl.config(
            text=f"● Your Turn ({PALETTES[self.human_theme]['name']})",
            fg=col
        )
        self.show_turn_banner(
            f"YOUR TURN • {PALETTES[self.human_theme]['name'].upper()}",
            col
        )


if __name__ == "__main__":
    app_root = tk.Tk()
    game = ChineseCheckersMaster(app_root)
    app_root.mainloop()
