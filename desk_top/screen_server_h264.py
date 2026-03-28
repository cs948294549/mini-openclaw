import socket
import threading
import mss
import numpy as np
import cv2
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key

HOST = '0.0.0.0'
PORT = 25901

with mss.mss() as sct:
    mon = sct.monitors[1]
    SCR_W = mon['width']
    SCR_H = mon['height']

CLIENT_W = 1280
CLIENT_H = 720

mouse_controller = MouseController()
keyboard_controller = KeyboardController()

SPECIAL_KEYS = {
    'enter': Key.enter,
    'backspace': Key.backspace,
    'esc': Key.esc,
    'tab': Key.tab,
    'space': Key.space,
    'shift': Key.shift,
    'ctrl': Key.ctrl,
    'alt': Key.alt,
    'up': Key.up, 'down': Key.down, 'left': Key.left, 'right': Key.right,
    'delete': Key.delete, 'home': Key.home, 'end': Key.end,
    'f1': Key.f1,'f2': Key.f2,'f3': Key.f3,'f4': Key.f4,'f5': Key.f5,'f6': Key.f6,
    'f7': Key.f7,'f8': Key.f8,'f9': Key.f9,'f10': Key.f10,'f11': Key.f11,'f12': Key.f12
}

def capture_screen():
    with mss.mss() as sct:
        img = sct.grab(sct.monitors[1])
        frame = np.array(img)
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

def encode_jpg(frame):
    _, enc = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
    return enc.tobytes()

def send_frame(conn, data):
    conn.sendall(len(data).to_bytes(4, 'big') + data)

def video_stream(conn):
    print("[视频] 已启动")
    while True:
        try:
            frame = capture_screen()
            jpg = encode_jpg(frame)
            send_frame(conn, jpg)
        except:
            break

def input_server(conn):
    print("[键鼠] 已启动")
    buffer = ""
    while True:
        try:
            data = conn.recv(1024)
            if not data: break
            recv_str = data.decode('utf-8', errors='replace')
            buffer += recv_str

            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                cmd = line.strip()
                if not cmd:
                    continue  # 空指令直接跳过，不报错

                print(f"[指令] {cmd}")

                # ---------------------- 鼠标移动 ----------------------
                if cmd.startswith('MOVE'):
                    parts = cmd.split()
                    if len(parts) >=3:
                        _, x, y = parts
                        x, y = int(x), int(y)
                        rx = int(x * SCR_W / CLIENT_W)
                        ry = int(y * SCR_H / CLIENT_H)
                        mouse_controller.position = (rx, ry)

                # ---------------------- 鼠标点击 ----------------------
                elif cmd == 'LD': mouse_controller.press(Button.left)
                elif cmd == 'LU': mouse_controller.release(Button.left)
                elif cmd == 'RD': mouse_controller.press(Button.right)
                elif cmd == 'RU': mouse_controller.release(Button.right)

                # ---------------------- 功能键 ----------------------
                elif cmd.startswith('KEY'):
                    parts = cmd.split(maxsplit=1)
                    if len(parts) >=2:
                        key_name = parts[1]
                        print(f"→ 功能键: {key_name}")
                        key = SPECIAL_KEYS.get(key_name, key_name)
                        try:
                            keyboard_controller.press(key)
                            keyboard_controller.release(key)
                        except:
                            pass

                # ---------------------- 文字打字（核心修复） ----------------------
                elif cmd.startswith('TEXT'):
                    parts = cmd.split(maxsplit=1)
                    if len(parts) >= 2:
                        text = parts[1]
                        print(f"→ 打字: {repr(text)}")
                        try:
                            keyboard_controller.type(text)
                        except:
                            pass
                    # 空TEXT直接跳过，不报错

        except Exception as e:
            print(f"[异常] {e}")
            continue

def main():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print("✅ 服务端已启动（稳定版）")
    while True:
        conn, addr = s.accept()
        print("\n客户端连接:", addr)
        threading.Thread(target=video_stream, args=(conn,), daemon=True).start()
        threading.Thread(target=input_server, args=(conn,), daemon=True).start()

if __name__ == '__main__':
    main()