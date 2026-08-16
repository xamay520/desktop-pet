# -*- coding: utf-8 -*-
"""
桌面宠物 - 贴边隐藏 + 北京时间 + 文字翻译
Windows 版
功能：
  1. 桌宠窗口贴屏幕右边缘，鼠标移开自动隐藏（只露一条边），移过去展开
  2. 实时显示北京时间（解决电脑是洛杉矶时区的问题）
  3. 选中文字后按 Ctrl+C 复制，自动翻译成中文显示
  4. 点"截图翻译"按钮，截取屏幕识别文字并翻译（兜底，用于不能选中的地方）

依赖安装：
  pip install pyperclip requests mss

运行：
  python desktop_pet.py
"""
import tkinter as tk
import threading
import time
import subprocess
import os
import tempfile
from datetime import datetime, timezone, timedelta

try:
    import pyperclip
except ImportError:
    pyperclip = None
try:
    import requests
except ImportError:
    requests = None

BJ_TZ = timezone(timedelta(hours=8))   # 北京时间 UTC+8
EDGE = 4                                # 贴边时露出的宽度(px)
WIDTH, HEIGHT = 280, 220                # 窗口尺寸


class DesktopPet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("桌宠")
        self.root.overrideredirect(True)          # 无边框
        self.root.attributes("-topmost", True)    # 置顶
        self.root.attributes("-alpha", 0.95)

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.x = self.screen_w - WIDTH
        self.y = self.screen_h - HEIGHT - 60
        self.root.geometry(f"{WIDTH}x{HEIGHT}+{self.x}+{self.y}")

        self.hidden = False
        self.last_clip = ""

        self._build_ui()
        self._bind_events()
        self._start_clock()
        self._start_clipboard_watch()

    # ---------- UI ----------
    def _build_ui(self):
        self.root.configure(bg="#2b2b2b")
        tk.Label(self.root, text="[ 桌宠 ]", bg="#2b2b2b", fg="#ffffff",
                 font=("Microsoft YaHei", 12, "bold")).pack(pady=(8, 2))

        tk.Label(self.root, text="北京时间", bg="#2b2b2b", fg="#888888",
                 font=("Microsoft YaHei", 9)).pack()
        self.clock_label = tk.Label(self.root, text="", bg="#2b2b2b", fg="#4fc3f7",
                                    font=("Consolas", 15, "bold"))
        self.clock_label.pack(pady=2)

        self.result_label = tk.Label(self.root, text="复制文字后自动翻译，或点下方按钮",
                                     bg="#2b2b2b", fg="#cccccc",
                                     font=("Microsoft YaHei", 10),
                                     wraplength=250, justify="left")
        self.result_label.pack(pady=6, padx=8)

        btn_frame = tk.Frame(self.root, bg="#2b2b2b")
        btn_frame.pack(pady=4)
        tk.Button(btn_frame, text="翻译剪贴板", command=self.translate_clipboard,
                  bg="#3a3a3a", fg="white", relief="flat",
                  font=("Microsoft YaHei", 9)).pack(side="left", padx=3)
        tk.Button(btn_frame, text="截图翻译", command=self.screenshot_translate,
                  bg="#3a3a3a", fg="white", relief="flat",
                  font=("Microsoft YaHei", 9)).pack(side="left", padx=3)
        tk.Button(btn_frame, text="退出", command=self.root.destroy,
                  bg="#5a2a2a", fg="white", relief="flat",
                  font=("Microsoft YaHei", 9)).pack(side="left", padx=3)

    # ---------- 贴边隐藏 ----------
    def _bind_events(self):
        self.root.bind("<Enter>", self._on_enter)
        self.root.bind("<Leave>", self._on_leave)
        self.root.bind("<Button-1>", self._start_move)
        self.root.bind("<B1-Motion>", self._on_move)

    def _start_move(self, e):
        self._drag_x, self._drag_y = e.x, e.y

    def _on_move(self, e):
        x = self.root.winfo_x() + e.x - self._drag_x
        y = self.root.winfo_y() + e.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _on_enter(self, e):
        if self.hidden:
            self._expand()

    def _on_leave(self, e):
        self.root.after(800, self._check_hide)

    def _check_hide(self):
        px, py = self.root.winfo_pointerx(), self.root.winfo_pointery()
        wx, wy = self.root.winfo_x(), self.root.winfo_y()
        if not (wx <= px <= wx + WIDTH and wy <= py <= wy + HEIGHT):
            self._hide()

    def _hide(self):
        self.hidden = True
        self.root.geometry(f"{WIDTH}x{HEIGHT}+{self.screen_w - EDGE}+{self.root.winfo_y()}")

    def _expand(self):
        self.hidden = False
        self.root.geometry(f"{WIDTH}x{HEIGHT}+{self.screen_w - WIDTH}+{self.root.winfo_y()}")

    # ---------- 北京时间 ----------
    def _start_clock(self):
        def update():
            while True:
                now = datetime.now(BJ_TZ)
                self.clock_label.config(text=now.strftime("%Y-%m-%d %H:%M:%S"))
                time.sleep(1)
        threading.Thread(target=update, daemon=True).start()

    # ---------- 剪贴板监听翻译 ----------
    def _start_clipboard_watch(self):
        def watch():
            if pyperclip is None:
                return
            while True:
                try:
                    text = pyperclip.paste()
                    if text and text != self.last_clip and len(text) < 2000:
                        self.last_clip = text
                        if self._needs_translate(text):
                            self._translate_and_show(text)
                except Exception:
                    pass
                time.sleep(1.5)
        threading.Thread(target=watch, daemon=True).start()

    @staticmethod
    def _needs_translate(text):
        # 含较多非中文字符才翻译，避免中文内容反复触发
        non_cn = sum(1 for c in text if ord(c) > 127 and not ('\u4e00' <= c <= '\u9fff'))
        return non_cn > 0

    def translate_clipboard(self):
        if pyperclip is None:
            self.result_label.config(text="未安装 pyperclip，请先 pip install pyperclip")
            return
        text = pyperclip.paste()
        if text:
            self._translate_and_show(text)
        else:
            self.result_label.config(text="剪贴板为空")

    def _translate_and_show(self, text):
        def do():
            result = self.translate(text)
            self.root.after(0, lambda: self.result_label.config(text=result[:300]))
        threading.Thread(target=do, daemon=True).start()

    def translate(self, text):
        if requests is None:
            return "未安装 requests，请先 pip install requests"
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {"client": "gtx", "sl": "auto", "tl": "zh-CN", "dt": "t", "q": text}
            r = requests.get(url, params=params, timeout=8)
            r.raise_for_status()
            data = r.json()
            return "".join(part[0] for part in data[0] if part[0])
        except Exception as e:
            return f"翻译失败: {e}"

    # ---------- 截图翻译 ----------
    def screenshot_translate(self):
        self.root.withdraw()
        self.root.after(400, self._do_screenshot)

    def _do_screenshot(self):
        try:
            import mss
            shot_path = os.path.join(tempfile.gettempdir(), "pet_shot.png")
            with mss.mss() as sct:
                sct.shot(output=shot_path)
            text = self._ocr(shot_path)
            if text and "OCR" not in text:
                self._translate_and_show(text)
            else:
                self.result_label.config(text=text if text else "未识别到文字")
        except Exception as e:
            self.result_label.config(text=f"截图失败: {e}")
        finally:
            self.root.deiconify()

    def _ocr(self, image_path):
        # 调用同目录 ocr.ps1（Windows 自带 OCR）
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr.ps1")
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", script, image_path],
                capture_output=True, text=True, timeout=90
            )
            return r.stdout.strip()
        except Exception as e:
            return f"OCR失败: {e}"

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    DesktopPet().run()
