import socket
import tkinter as tk
from PIL import Image, ImageTk
import io
import cv2
import numpy as np
import threading

# ===================== 【改成服务端IP】 =====================
HOST = '192.168.130.186'
PORT = 25901
# ============================================================

root = tk.Tk()
root.title("远程桌面")
root.geometry("1280x720")

lbl = tk.Label(root)
lbl.pack(expand=True, fill="both")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

# ===================== 【新增】组合键状态记录 =====================
key_state = {
    "ctrl": False,
    "shift": False,
    "alt": False
}

def recv_fixed(sock, size):
    buf = b''
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def recv_loop():
    print("✅ 画面接收中")
    while True:
        try:
            len_data = recv_fixed(s, 4)
            if not len_data: break
            data_len = int.from_bytes(len_data, 'big')
            jpg_data = recv_fixed(s, data_len)
            if not jpg_data: break

            nparr = np.frombuffer(jpg_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            ww = lbl.winfo_width()
            hh = lbl.winfo_height()
            if ww > 50 and hh > 50:
                img = cv2.resize(img, (ww, hh))

            im = Image.fromarray(img)
            imtk = ImageTk.PhotoImage(im)
            root.after(0, lambda: lbl.config(image=imtk))
            root.after(0, lambda: setattr(lbl, 'image', imtk))
        except:
            continue


# =============== 鼠标 ===============
def on_mouse(event):
    try:
        s.sendall(f"MOVE {event.x} {event.y}\n".encode())
    except:
        pass


def on_click(event):
    cmd = "LD" if event.num == 1 else "RD" if event.num == 3 else "MD"
    try:
        s.sendall(f"{cmd}\n".encode())
    except:
        pass


def on_release(event):
    cmd = "LU" if event.num == 1 else "RU" if event.num == 3 else "MU"
    try:
        s.sendall(f"{cmd}\n".encode())
    except:
        pass


# =============== 键盘：支持组合键（兼容原有逻辑）===============
KEY_MAP = {
    "BackSpace": "backspace",
    "Return": "enter",
    "Escape": "esc",
    "Space": "space",
    "space": "space",
    "Tab": "tab",
    "Up": "up", "Down": "down", "Left": "left", "Right": "right",
    "Delete": "delete", "Home": "home", "End": "end",
    "F1": "f1", "F2": "f2", "F3": "f3", "F4": "f4", "F5": "f5", "F6": "f6",
    "F7": "f7", "F8": "f8", "F9": "f9", "F10": "f10", "F11": "f11", "F12": "f12"
}


def on_key_press(event):
    try:
        sym = event.keysym

        # ===================== 【新增】组合键状态标记 =====================
        if sym in ["Control_L", "Control_R"]:
            key_state["ctrl"] = True
            return
        if sym in ["Shift_L", "Shift_R"]:
            key_state["shift"] = True
            return
        if sym in ["Alt_L", "Alt_R"]:
            key_state["alt"] = True
            return

        # ===================== 【新增】组合键发送 =====================
        if key_state["ctrl"]:
            s.sendall(f"KEY ctrl+{sym.lower()}\n".encode())
            return
        if key_state["shift"]:
            s.sendall(f"KEY shift+{sym.lower()}\n".encode())
            return
        if key_state["alt"]:
            s.sendall(f"KEY alt+{sym.lower()}\n".encode())
            return

        # 原有功能键逻辑（不变）
        if sym in KEY_MAP:
            key = KEY_MAP[sym]
            s.sendall(f"KEY {key}\n".encode())
            return

        # 原有普通字符逻辑（不变）
        if len(sym) == 1 and sym.isprintable():
            s.sendall(f"KEY {sym}\n".encode())

    except:
        pass


# ===================== 【新增】松开时重置组合键状态 =====================
def on_key_release(event):
    try:
        if event.keysym in ["Control_L", "Control_R"]:
            key_state["ctrl"] = False
        if event.keysym in ["Shift_L", "Shift_R"]:
            key_state["shift"] = False
        if event.keysym in ["Alt_L", "Alt_R"]:
            key_state["alt"] = False
    except:
        pass


# 绑定（不变）
lbl.bind('<Motion>', on_mouse)
lbl.bind('<ButtonPress>', on_click)
lbl.bind('<ButtonRelease>', on_release)
lbl.bind('<KeyPress>', on_key_press)
lbl.bind('<KeyRelease>', on_key_release)
lbl.focus_set()

# 连接
try:
    s.connect((HOST, PORT))
    print("✅ 连接成功")
except:
    root.destroy()

threading.Thread(target=recv_loop, daemon=True).start()
root.mainloop()