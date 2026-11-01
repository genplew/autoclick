import json
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import keyboard
from pynput import mouse
from pynput.mouse import Button
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "mouse_track.json")

events = []
start_time = None
mouse_pressed = False
last_move_time = 0
recording = False
playing = False
stop_flag = threading.Event()
play_thread = None
play_start = 0.0
skip_target = 0.0

WIDTH, HEIGHT = 3840, 2160
MIN_MOVE_INTERVAL = 0.01
RECORDING_DELAY = 3
SPEED_FACTOR = 1.0
MIN_DELAY = 0.001
DRAG_PREDICTION = True
STOP_KEY = "scroll lock"


def convert_button(button_str):
    if "Button.left" in button_str:
        return "left"
    if "Button.right" in button_str:
        return "right"
    if "Button.middle" in button_str:
        return "middle"
    return "left"


def check_stop_key():
    try:
        key = HOTKEY.get().strip().lower()
    except Exception:
        key = "scroll lock"
    if "+" in key:
        keys = [k.strip() for k in key.split("+")]
        return all(keyboard.is_pressed(k) for k in keys)
    return keyboard.is_pressed(key)


def on_move(x, y):
    global last_move_time
    if start_time is None or stop_flag.is_set():
        return
    current_time = time.time()
    if current_time - last_move_time < MIN_MOVE_INTERVAL and mouse_pressed:
        return
    last_move_time = current_time
    events.append({
        "type": "move",
        "x": x,
        "y": y,
        "time": current_time - start_time,
        "pressed": mouse_pressed,
    })


def on_click(x, y, button, pressed):
    global mouse_pressed
    if start_time is None or stop_flag.is_set():
        return
    mouse_pressed = pressed
    events.append({
        "type": "click",
        "x": x,
        "y": y,
        "button": str(button),
        "state": "pressed" if pressed else "released",
        "time": time.time() - start_time,
    })


def on_scroll(x, y, dx, dy):
    if start_time is None or stop_flag.is_set():
        return
    events.append({
        "type": "scroll",
        "x": x,
        "y": y,
        "dx": dx,
        "dy": dy,
        "time": time.time() - start_time,
    })


def record_worker(status_cb):
    global start_time, mouse_pressed, last_move_time, events, recording
    events = []
    mouse_pressed = False
    last_move_time = 0
    start_time = None
    stop_flag.clear()
    # Clear old recording file
    try:
        with open(INPUT_FILE, "w") as f:
            f.write("[]")
    except Exception:
        pass
    status_cb("Grabando en 3s...")
    time.sleep(RECORDING_DELAY)
    if stop_flag.is_set():
        status_cb("Cancelado")
        recording = False
        return
    start_time = time.time()
    listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    listener.start()
    status_cb("Grabando... (todo el mouse)")
    while not stop_flag.is_set():
        if check_stop_key():
            break
        time.sleep(0.1)
    listener.stop()
    with open(INPUT_FILE, "w") as f:
        json.dump(events, f, indent=2)
    status_cb(f"Guardado {len(events)} eventos")
    recording = False


def play_worker(status_cb):
    global playing, play_start, skip_target
    stop_flag.clear()
    skip_target = 0.0
    try:
        with open(INPUT_FILE, "r") as f:
            evs = json.load(f)
    except FileNotFoundError:
        status_cb("No hay archivo")
        playing = False
        return
    if not evs:
        status_cb("Sin eventos")
        playing = False
        return
    total_time = evs[-1]["time"] / SPEED_FACTOR if evs else 0
    status_cb("Reproduciendo en 3s...")
    time.sleep(3)
    if stop_flag.is_set():
        status_cb("Cancelado")
        playing = False
        return
    start = time.time()
    play_start = start
    current_button = None
    for i, event in enumerate(evs):
        if stop_flag.is_set() or check_stop_key():
            status_cb("Detenido")
            playing = False
            return
        elapsed_now = time.time() - start
        remaining_total = max(0, total_time - elapsed_now)
        status_cb(f"Reproduciendo: {elapsed_now:.1f}s / {total_time:.1f}s (restante {remaining_total:.1f}s)")
        target_time = event["time"] / SPEED_FACTOR
        elapsed = time.time() - start
        remaining = target_time - elapsed
        if remaining > 0:
            sleep_interval = 0.05
            while remaining > 0 and not stop_flag.is_set():
                if check_stop_key():
                    status_cb("Detenido")
                    playing = False
                    return
                sl = min(sleep_interval, remaining)
                time.sleep(sl)
                remaining -= sl
                elapsed_now = time.time() - start
                remaining_total = max(0, total_time - elapsed_now)
                status_cb(f"Reproduciendo: {elapsed_now:.1f}s / {total_time:.1f}s (restante {remaining_total:.1f}s)")
        try:
            if event["type"] == "move":
                x, y = event["x"], event["y"]
                if DRAG_PREDICTION and current_button and i < len(evs) - 1:
                    nxt = evs[i + 1]
                    if nxt["type"] == "move":
                        pyautogui.dragTo(x, y, button=current_button, duration=0.0001, _pause=False)
                    else:
                        pyautogui.dragTo(x, y, button=current_button, _pause=False)
                elif event.get("pressed", False) and current_button:
                    pyautogui.dragTo(x, y, button=current_button, _pause=False)
                else:
                    pyautogui.moveTo(x, y, _pause=False)
            elif event["type"] == "click":
                button = convert_button(event["button"])
                if event["state"] == "pressed":
                    pyautogui.mouseDown(x=event["x"], y=event["y"], button=button, _pause=False)
                    current_button = button
                else:
                    pyautogui.mouseUp(x=event["x"], y=event["y"], button=button, _pause=False)
                    current_button = None
            elif event["type"] == "scroll":
                pyautogui.scroll(int(event["dy"] * 10), x=event["x"], y=event["y"], _pause=False)
        except Exception as e:
            pass
    if (LOOP_ENABLED.get() if "LOOP_ENABLED" in globals() else False) and not stop_flag.is_set():
        play_worker(status_cb)
        return
    status_cb("Reproducción completa")
    playing = False


POS_FILE = os.path.join(BASE_DIR, "window_pos.json")

def load_pos():
    try:
        with open(POS_FILE) as f:
            d = json.load(f)
        return d.get("x", 100), d.get("y", 100)
    except Exception:
        return 100, 100

def save_pos(root):
    try:
        geo = root.geometry()
        parts = geo.split("+")
        x = int(parts[1]) if len(parts) > 1 else 100
        y = int(parts[2]) if len(parts) > 2 else 100
        with open(POS_FILE, "w") as f:
            json.dump({"x": x, "y": y}, f)
    except Exception:
        pass


class App:
    def __init__(self, root):
        self.root = root
        root.title("Mouse Recorder / Player")
        root.resizable(False, False)
        root.attributes("-topmost", True)
        self.status = tk.StringVar(value="Listo")
        frm = ttk.Frame(root, padding=12)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, textvariable=self.status).pack(pady=6)
        btns = ttk.Frame(frm)
        btns.pack(pady=6)
        self.img_record = tk.PhotoImage(file=os.path.join(BASE_DIR, "record.png"))
        self.img_play = tk.PhotoImage(file=os.path.join(BASE_DIR, "play.png"))
        self.img_stop = tk.PhotoImage(file=os.path.join(BASE_DIR, "stop.png"))
        self.rec_btn = ttk.Button(btns, image=self.img_record, command=self.start_record)
        self.rec_btn.grid(row=0, column=0, padx=4)
        self.play_btn = ttk.Button(btns, image=self.img_play, command=self.start_play)
        self.play_btn.grid(row=0, column=1, padx=4)
        self.stop_btn = ttk.Button(btns, image=self.img_stop, command=self.stop)
        self.stop_btn.grid(row=0, column=2, padx=4)
        hk = ttk.Frame(frm)
        hk.pack(pady=4)
        ttk.Label(hk, text="Tecla de parada:").grid(row=0, column=0, padx=2)
        ttk.Entry(hk, textvariable=HOTKEY, width=16).grid(row=0, column=1, padx=2)
        ttk.Checkbutton(frm, text="Loop", variable=LOOP_ENABLED).pack(pady=4)

    def set_status(self, msg):
        self.root.after(0, lambda: self.status.set(msg))

    def start_record(self):
        global recording
        if recording or playing:
            return
        if not messagebox.askyesno("Confirmar", "¿Deseas borrar la grabación anterior?"):
            return
        recording = True
        threading.Thread(target=record_worker, args=(self.set_status,), daemon=True).start()

    def start_play(self):
        global playing
        if recording or playing:
            return
        playing = True
        threading.Thread(target=play_worker, args=(self.set_status,), daemon=True).start()
        self.rec_btn.config(state="disabled")

    def stop(self):
        stop_flag.set()


if __name__ == "__main__":
    global HOTKEY
    root = tk.Tk()
    x, y = load_pos()
    root.geometry(f"300x210+{x}+{y}")
    root.resizable(False, False)
    HOTKEY = tk.StringVar(value="`")
    LOOP_ENABLED = tk.BooleanVar(value=False)
    App(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (save_pos(root), root.destroy()))
    root.mainloop()
