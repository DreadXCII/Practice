"""
Battle Map - a DnD map tool in Python (tkinter)
-------------------------------------------------
Upload a map image, place monster/player/ally tokens on it, drag them
around, zoom and pan, rename tokens, and remove them.

Requires:
    pip install Pillow

On Linux, tkinter itself sometimes needs a separate system package:
    sudo apt install python3-tk

Controls:
    Upload map          - choose an image file to use as the map
    Move / select       - drag tokens to move them, drag empty space to pan
    Place monster/player/ally - click the map to drop a token of that type
    Double-click a token - rename it
    Right-click a token  - delete it
    Select a token, then press Delete/Backspace - also deletes it
    Scroll wheel         - zoom in/out, centered on the cursor
    Clear tokens         - remove every token
    Reset view            - re-fit and re-center the map
"""

import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk

TOKEN_COLORS = {
    "monster": "#b0473d",
    "player": "#3f7d8c",
    "ally": "#5c8c4a",
}

TOKEN_TEXT_COLORS = {
    "monster": "#2a0f0c",
    "player": "#0c2226",
    "ally": "#14210d",
}

TYPE_LABELS = {"monster": "Monster", "player": "Player", "ally": "Ally"}

MODE_COLORS = {
    "select": "#d3902f",
    "monster": "#b0473d",
    "player": "#3f7d8c",
    "ally": "#5c8c4a",
}


class BattleMapApp:
    def __init__(self, root):
        self.root = root
        root.title("Battle Map")
        root.geometry("1150x780")
        root.configure(bg="#16130e")

        self.mode = tk.StringVar(value="select")
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0

        self.original_image = None
        self.photo_image = None
        self.map_item = None
        self.map_loaded = False
        self.img_w = 0
        self.img_h = 0

        self.tokens = []
        self.next_id = 1
        self.counters = {"monster": 0, "player": 0, "ally": 0}
        self.selected_id = None

        self.drag_token_id = None
        self.drag_offset = (0, 0)
        self._drag_moved = False
        self._press_pos = (0, 0)

        self.panning = False
        self.pan_start = (0, 0)
        self.pan_start_offset = (0, 0)
        self._pan_moved = False

        self._build_ui()
        self._bind_events()

    # ---------- UI construction ----------
    def _build_ui(self):
        toolbar = tk.Frame(self.root, bg="#211c15", pady=8, padx=10)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(
            toolbar, text="Upload map", command=self.upload_map,
            bg="#7a5720", fg="#eadfc4", relief=tk.FLAT, padx=10, pady=4,
            activebackground="#d3902f", activeforeground="#1a1509",
        ).pack(side=tk.LEFT, padx=(0, 10))

        mode_frame = tk.Frame(toolbar, bg="#211c15")
        mode_frame.pack(side=tk.LEFT, padx=(0, 10))
        self.mode_buttons = {}
        for label, key in [
            ("Move / select", "select"),
            ("Place monster", "monster"),
            ("Place player", "player"),
            ("Place ally", "ally"),
        ]:
            b = tk.Button(
                mode_frame, text=label, relief=tk.FLAT, padx=8, pady=4,
                command=lambda k=key: self.set_mode(k),
            )
            b.pack(side=tk.LEFT, padx=2)
            self.mode_buttons[key] = b
        self._refresh_mode_buttons()

        tk.Button(
            toolbar, text="Clear tokens", command=self.clear_tokens,
            relief=tk.FLAT, padx=8, pady=4, bg="#211c15", fg="#eadfc4",
        ).pack(side=tk.LEFT, padx=4)
        tk.Button(
            toolbar, text="Reset view", command=self.fit_to_view,
            relief=tk.FLAT, padx=8, pady=4, bg="#211c15", fg="#eadfc4",
        ).pack(side=tk.LEFT, padx=4)

        zoom_frame = tk.Frame(toolbar, bg="#211c15")
        zoom_frame.pack(side=tk.LEFT, padx=10)
        tk.Button(
            zoom_frame, text="-", relief=tk.FLAT, width=2, bg="#211c15", fg="#eadfc4",
            command=lambda: self.zoom_by(1 / 1.25),
        ).pack(side=tk.LEFT)
        self.zoom_label = tk.Label(
            zoom_frame, text="100%", bg="#211c15", fg="#a89a7c", width=5
        )
        self.zoom_label.pack(side=tk.LEFT, padx=4)
        tk.Button(
            zoom_frame, text="+", relief=tk.FLAT, width=2, bg="#211c15", fg="#eadfc4",
            command=lambda: self.zoom_by(1.25),
        ).pack(side=tk.LEFT)

        self.canvas = tk.Canvas(self.root, bg="#1c1810", highlightthickness=0)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.status = tk.Label(
            self.root,
            text="No map loaded. Upload a map image to begin.",
            bg="#211c15", fg="#a89a7c", anchor="w", padx=10, pady=4,
        )
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        self.empty_text = self.canvas.create_text(
            0, 0,
            text=(
                "Upload a battle map image to get started.\n"
                "Then pick a token type and click the map to place tokens.\n"
                "Drag tokens to move them; scroll to zoom."
            ),
            fill="#a89a7c", font=("Georgia", 13), justify="center",
            tags=("empty",),
        )

    def _refresh_mode_buttons(self):
        for key, btn in self.mode_buttons.items():
            if key == self.mode.get():
                btn.configure(bg="#2a241b", fg=MODE_COLORS[key])
            else:
                btn.configure(bg="#211c15", fg="#eadfc4")

    def set_mode(self, key):
        self.mode.set(key)
        self._refresh_mode_buttons()
        self.canvas.configure(cursor="crosshair" if key != "select" else "fleur")
        self.deselect()

    def _bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<MouseWheel>", self.on_wheel)
        self.canvas.bind("<Button-4>", lambda e: self.on_wheel_linux(e, 1))
        self.canvas.bind("<Button-5>", lambda e: self.on_wheel_linux(e, -1))
        self.canvas.bind("<Configure>", self.on_resize)
        self.root.bind("<Delete>", self.on_delete_key)
        self.root.bind("<BackSpace>", self.on_delete_key)

    # ---------- Map loading ----------
    def upload_map(self):
        path = filedialog.askopenfilename(
            title="Choose a map image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        try:
            img = Image.open(path)
            img.load()
        except Exception as e:
            messagebox.showerror("Could not open image", str(e))
            return

        self.original_image = img.convert("RGBA")
        self.img_w, self.img_h = self.original_image.size
        self.map_loaded = True
        self.canvas.delete("empty")
        self.fit_to_view()
        self.set_status(
            f"Map loaded ({self.img_w} x {self.img_h}px). {self.token_count_text()}"
        )

    def on_resize(self, event):
        if not self.map_loaded:
            self.canvas.coords(self.empty_text, event.width / 2, event.height / 2)

    # ---------- Zoom / pan / rendering ----------
    def fit_to_view(self):
        if not self.map_loaded:
            return
        vp_w = self.canvas.winfo_width()
        vp_h = self.canvas.winfo_height()
        if vp_w < 10 or vp_h < 10:
            self.root.after(50, self.fit_to_view)
            return
        scale = min(vp_w / self.img_w, vp_h / self.img_h, 1.0) * 0.95
        self.zoom = max(0.1, scale)
        self.pan_x = (vp_w - self.img_w * self.zoom) / 2
        self.pan_y = (vp_h - self.img_h * self.zoom) / 2
        self.redraw_map()
        self.redraw_all_tokens()

    def redraw_map(self):
        if not self.map_loaded:
            return
        new_w = max(1, int(self.img_w * self.zoom))
        new_h = max(1, int(self.img_h * self.zoom))
        resized = self.original_image.resize((new_w, new_h), Image.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(resized)
        if self.map_item is None:
            self.map_item = self.canvas.create_image(
                self.pan_x, self.pan_y, anchor="nw",
                image=self.photo_image, tags=("map",),
            )
        else:
            self.canvas.itemconfigure(self.map_item, image=self.photo_image)
            self.canvas.coords(self.map_item, self.pan_x, self.pan_y)
        self.canvas.tag_lower(self.map_item)
        self.zoom_label.configure(text=f"{round(self.zoom * 100)}%")

    def zoom_at(self, cx, cy, new_zoom_raw):
        new_zoom = max(0.1, min(5.0, new_zoom_raw))
        world_x = (cx - self.pan_x) / self.zoom
        world_y = (cy - self.pan_y) / self.zoom
        self.pan_x = cx - world_x * new_zoom
        self.pan_y = cy - world_y * new_zoom
        self.zoom = new_zoom
        self.redraw_map()
        self.redraw_all_tokens()

    def zoom_by(self, factor):
        if not self.map_loaded:
            return
        cx = self.canvas.winfo_width() / 2
        cy = self.canvas.winfo_height() / 2
        self.zoom_at(cx, cy, self.zoom * factor)

    def on_wheel(self, event):
        if not self.map_loaded:
            return
        factor = 1.1 if event.delta > 0 else 1 / 1.1
        self.zoom_at(event.x, event.y, self.zoom * factor)

    def on_wheel_linux(self, event, direction):
        if not self.map_loaded:
            return
        factor = 1.1 if direction > 0 else 1 / 1.1
        self.zoom_at(event.x, event.y, self.zoom * factor)

    def to_canvas_coords(self, img_x, img_y):
        return self.pan_x + img_x * self.zoom, self.pan_y + img_y * self.zoom

    def to_image_coords(self, cx, cy):
        return (cx - self.pan_x) / self.zoom, (cy - self.pan_y) / self.zoom

    # ---------- Tokens ----------
    def token_count_text(self):
        m = sum(1 for t in self.tokens if t["type"] == "monster")
        p = sum(1 for t in self.tokens if t["type"] == "player")
        a = sum(1 for t in self.tokens if t["type"] == "ally")
        return (
            f"{m} monster{'s' if m != 1 else ''}, "
            f"{p} player{'s' if p != 1 else ''}, "
            f"{a} all{'ies' if a != 1 else 'y'} on the map."
        )

    def add_token(self, ttype, img_x, img_y):
        self.counters[ttype] += 1
        token = {
            "id": self.next_id,
            "type": ttype,
            "label": f"{TYPE_LABELS[ttype]} {self.counters[ttype]}",
            "x": img_x,
            "y": img_y,
            "canvas_ids": {},
        }
        self.next_id += 1
        self.tokens.append(token)
        self.draw_token(token)
        self.set_status(f"Placed {token['label']}. {self.token_count_text()}")

    def remove_token(self, token_id):
        token = next((t for t in self.tokens if t["id"] == token_id), None)
        if not token:
            return
        for cid in token["canvas_ids"].values():
            self.canvas.delete(cid)
        self.tokens.remove(token)
        if self.selected_id == token_id:
            self.selected_id = None
        self.set_status(f"Token removed. {self.token_count_text()}")

    def initials(self, label):
        parts = label.split()
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    def draw_token(self, token):
        cx, cy = self.to_canvas_coords(token["x"], token["y"])
        r = 20
        fill = TOKEN_COLORS[token["type"]]
        outline_color = "#d3902f" if self.selected_id == token["id"] else "#1a1509"
        outline_width = 4 if self.selected_id == token["id"] else 3

        oval = self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r, fill=fill,
            outline=outline_color, width=outline_width,
            tags=(f"token_{token['id']}", "token"),
        )
        text = self.canvas.create_text(
            cx, cy, text=self.initials(token["label"]),
            fill=TOKEN_TEXT_COLORS[token["type"]],
            font=("Georgia", 11, "bold"),
            tags=(f"token_{token['id']}", "token"),
        )
        label = self.canvas.create_text(
            cx, cy + r + 12, text=token["label"],
            fill="#eadfc4", font=("Georgia", 9),
            tags=(f"token_{token['id']}", "token"),
        )
        token["canvas_ids"] = {"oval": oval, "text": text, "label": label}

    def redraw_token(self, token):
        for cid in token["canvas_ids"].values():
            self.canvas.delete(cid)
        self.draw_token(token)

    def redraw_all_tokens(self):
        for t in self.tokens:
            self.redraw_token(t)

    def deselect(self):
        if self.selected_id is not None:
            self.selected_id = None
            self.redraw_all_tokens()

    def select_token(self, token_id):
        self.selected_id = token_id
        self.redraw_all_tokens()

    def find_token_at(self, cx, cy):
        items = self.canvas.find_overlapping(cx - 3, cy - 3, cx + 3, cy + 3)
        for item in reversed(items):
            for tag in self.canvas.gettags(item):
                if tag.startswith("token_"):
                    return int(tag.split("_")[1])
        return None

    def rename_token(self, token_id):
        token = next((t for t in self.tokens if t["id"] == token_id), None)
        if not token:
            return
        new_label = simpledialog.askstring(
            "Rename token", "New label:",
            initialvalue=token["label"], parent=self.root,
        )
        if new_label:
            token["label"] = new_label.strip()
            self.redraw_token(token)

    def clear_tokens(self):
        if not self.tokens:
            return
        if messagebox.askyesno("Clear tokens", "Remove all tokens from the map?"):
            for t in self.tokens:
                for cid in t["canvas_ids"].values():
                    self.canvas.delete(cid)
            self.tokens = []
            self.counters = {"monster": 0, "player": 0, "ally": 0}
            self.selected_id = None
            self.set_status("All tokens cleared.")

    # ---------- Mouse handlers ----------
    def on_press(self, event):
        if not self.map_loaded:
            return

        tid = self.find_token_at(event.x, event.y)
        if tid is not None:
            token = next(t for t in self.tokens if t["id"] == tid)
            tcx, tcy = self.to_canvas_coords(token["x"], token["y"])
            self.drag_token_id = tid
            self.drag_offset = (event.x - tcx, event.y - tcy)
            self._drag_moved = False
            self._press_pos = (event.x, event.y)
            return

        if self.mode.get() == "select":
            self.panning = True
            self._pan_moved = False
            self.pan_start = (event.x, event.y)
            self.pan_start_offset = (self.pan_x, self.pan_y)
        else:
            img_x, img_y = self.to_image_coords(event.x, event.y)
            self.add_token(self.mode.get(), img_x, img_y)

    def on_motion(self, event):
        if self.drag_token_id is not None:
            dx = event.x - self._press_pos[0]
            dy = event.y - self._press_pos[1]
            if abs(dx) > 2 or abs(dy) > 2:
                self._drag_moved = True
            if self._drag_moved:
                token = next(t for t in self.tokens if t["id"] == self.drag_token_id)
                new_cx = event.x - self.drag_offset[0]
                new_cy = event.y - self.drag_offset[1]
                img_x, img_y = self.to_image_coords(new_cx, new_cy)
                token["x"], token["y"] = img_x, img_y
                self.redraw_token(token)
            return

        if self.panning:
            dx = event.x - self.pan_start[0]
            dy = event.y - self.pan_start[1]
            if abs(dx) > 2 or abs(dy) > 2:
                self._pan_moved = True
            self.pan_x = self.pan_start_offset[0] + dx
            self.pan_y = self.pan_start_offset[1] + dy
            self.redraw_map()
            self.redraw_all_tokens()

    def on_release(self, event):
        if self.drag_token_id is not None:
            if not self._drag_moved:
                self.select_token(self.drag_token_id)
            self.drag_token_id = None
            return
        if self.panning:
            self.panning = False
            if not self._pan_moved:
                self.deselect()

    def on_double_click(self, event):
        tid = self.find_token_at(event.x, event.y)
        if tid is not None:
            self.rename_token(tid)

    def on_right_click(self, event):
        tid = self.find_token_at(event.x, event.y)
        if tid is not None:
            self.remove_token(tid)

    def on_delete_key(self, event):
        if self.selected_id is not None:
            self.remove_token(self.selected_id)

    def set_status(self, text):
        self.status.configure(text=text)


if __name__ == "__main__":
    root = tk.Tk()
    app = BattleMapApp(root)
    root.mainloop()

    app.run(debug=True)
    