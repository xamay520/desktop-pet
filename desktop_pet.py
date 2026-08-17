# -*- coding: utf-8 -*-
"""
马维斯桌宠 v2 - 贴边隐藏(召唤条) + 北京时间 + 文字翻译
Windows 版
功能：
  1. 卡通宠物形象（马维斯：蓝色小猫），会眨眼、呼吸、摇尾巴
  2. 贴屏幕右边缘，鼠标移开自动隐藏；隐藏后右侧留一条彩色"召唤条"
  3. 鼠标移到屏幕最右边（召唤条）即可展开桌宠
  4. 实时显示北京时间（解决电脑是洛杉矶时区的问题）
  5. 选中文字后按 Ctrl+C 复制，自动翻译成中文，气泡显示
  6. 右键宠物可退出

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
import random
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
EDGE = 20                               # 隐藏时露出的召唤条宽度(px)
WIDTH, HEIGHT = 300, 330                # 窗口尺寸

# 马维斯配色
BODY = "#4fc3f7"        # 马维斯蓝
BODY_DARK = "#29a3e0"
FACE = "#e8f4fd"
OUTLINE = "#1b6e9e"
BLUSH = "#ffb3c1"
WHITE = "#ffffff"
TRANSPARENT = "#010101"  # 透明背景色


class DesktopPet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("马维斯桌宠")
        self.root.overrideredirect(True)          # 无边框
        self.root.attributes("-topmost", True)    # 置顶
        self.root.attributes("-transparentcolor", TRANSPARENT)  # 背景透明
        self.root.configure(bg=TRANSPARENT)

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.x = self.screen_w - WIDTH
        self.y = self.screen_h - HEIGHT - 40
        self.root.geometry(f"{WIDTH}x{HEIGHT}+{self.x}+{self.y}")

        self.hidden = False
        self.last_clip = ""
        self.blinking = False
        self.bubble_visible = False

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT,
                                bg=TRANSPARENT, highlightthickness=0)
        self.canvas.pack()

        self._draw_pet()
        self._bind_events()
        self._start_clock()
        self._start_animations()
        self._start_clipboard_watch()

    # ---------- 绘制马维斯 ----------
    def _draw_pet(self):
        c = self.canvas
        cx = 130  # 宠物中心偏左，右侧留召唤条
        # 尾巴（画在身体后面）
        self.tail = c.create_arc(cx + 60, 200, cx + 115, 255, start=0, extent=130,
                                 style="arc", outline=BODY_DARK, width=5)
        # 身体
        c.create_oval(cx - 72, 120, cx + 72, 265, fill=BODY, outline=OUTLINE, width=3, tags="body")
        # 肚皮
        c.create_oval(cx - 42, 155, cx + 42, 245, fill=WHITE, outline="", tags="body")
        # 耳朵
        c.create_polygon(cx - 62, 132, cx - 46, 78, cx - 24, 122, fill=BODY, outline=OUTLINE, width=3, tags="body")
        c.create_polygon(cx + 62, 132, cx + 46, 78, cx + 24, 122, fill=BODY, outline=OUTLINE, width=3, tags="body")
        c.create_polygon(cx - 57, 128, cx - 48, 90, cx - 31, 120, fill=BLUSH, outline="", tags="body")
        c.create_polygon(cx + 57, 128, cx + 48, 90, cx + 31, 120, fill=BLUSH, outline="", tags="body")
        # 脸
        c.create_oval(cx - 56, 88, cx + 56, 195, fill=FACE, outline=OUTLINE, width=3, tags="body")
        # 眼睛（大眼 + 高光）
        self.eye_l = c.create_oval(cx - 33, 118, cx - 12, 146, fill="#2b2b2b", outline="", tags="body")
        self.eye_r = c.create_oval(cx + 12, 118, cx + 33, 146, fill="#2b2b2b", outline="", tags="body")
        c.create_oval(cx - 29, 121, cx - 25, 125, fill=WHITE, outline="", tags="body")
        c.create_oval(cx + 16, 121, cx + 20, 125, fill=WHITE, outline="", tags="body")
        # 腮红
        c.create_oval(cx - 54, 152, cx - 37, 165, fill=BLUSH, outline="", tags="body")
        c.create_oval(cx + 37, 152, cx + 54, 165, fill=BLUSH, outline="", tags="body")
        # 嘴（微笑：上半弧）
        c.create_arc(cx - 12, 148, cx + 12, 170, start=180, extent=180,
                     style="arc", outline=OUTLINE, width=2, tags="body")
        # 天线（马维斯标志）
        c.create_line(cx, 88, cx, 66, fill=OUTLINE, width=3, tags="body")
        c.create_oval(cx - 7, 58, cx + 7, 72, fill="#ffd54f", outline=OUTLINE, width=2, tags="body")
        # 气泡
        self.bubble = c.create_oval(cx - 135, 4, cx + 135, 78, fill=WHITE,
                                    outline=OUTLINE, width=2, state="hidden")
        self.bubble_txt = c.create_text(cx, 41, text="", width=250, fill="#2b2b2b",
                                        font=("Microsoft YaHei", 9), state="hidden")
        # 时钟
        self.clock_id = c.create_text(cx, 292, text="", fill="#2b2b2b",
                                      font=("Consolas", 11, "bold"))
        # 召唤条（右侧，隐藏时可见）
        c.create_rectangle(WIDTH - EDGE, 90, WIDTH, 220, fill=BODY, outline=OUTLINE, width=2, tags="tab")
        c.create_text(WIDTH - EDGE // 2, 155, text="<", fill=WHITE, font=("Arial", 16, "bold"), tags="tab")
        # 退出按钮
        self.exit_btn = c.create_oval(cx + 92, 4, cx + 114, 26, fill="#e57373", outline="", state="hidden")
        self.exit_txt = c.create_text(cx + 103, 15, text="×", fill=WHITE,
                                      font=("Arial", 13, "bold"), state="hidden")

    # ---------- 事件绑定 ----------
    def _bind_events(self):
        self.canvas.bind("<Button-1>", self._start_move)
        self.canvas.bind("<B1-Motion>", self._on_move)
        self.canvas.bind("<Button-3>", lambda e: self.root.destroy())  # 右键退出
        self.canvas.tag_bind(self.exit_btn, "<Button-1>", lambda e: self.root.destroy())
        self.canvas.tag_bind(self.exit_txt, "<Button-1>", lambda e: self.root.destroy())
        self._start_hide_watch()

    def _start_move(self, e):
        self._drag_x, self._drag_y = e.x, e.y

    def _on_move(self, e):
        x = self.root.winfo_x() + e.x - self._drag_x
        y = self.root.winfo_y() + e.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    # ---------- 贴边隐藏 / 召唤 ----------
    def _start_hide_watch(self):
        def watch():
            while True:
                time.sleep(0.3)
                px, py = self.root.winfo_pointerx(), self.root.winfo_pointery()
                wx, wy = self.root.winfo_x(), self.root.winfo_y()
                if self.hidden:
                    # 鼠标移到屏幕右边缘召唤条区域 → 展开
                    if px >= self.screen_w - EDGE - 2 and wy <= py <= wy + HEIGHT:
                        self._expand()
                else:
                    # 鼠标不在窗口内 → 隐藏
                    if not (wx <= px <= wx + WIDTH and wy <= py <= wy + HEIGHT):
                        self._hide()
        threading.Thread(target=watch, daemon=True).start()

    def _hide(self):
        self.hidden = True
        self.canvas.itemconfig("tab", state="normal")   # 显示召唤条
        self.root.geometry(f"{WIDTH}x{HEIGHT}+{self.screen_w - EDGE}+{self.root.winfo_y()}")

    def _expand(self):
        self.hidden = False
        self.canvas.itemconfig("tab", state="hidden")   # 隐藏召唤条
        self.root.geometry(f"{WIDTH}x{HEIGHT}+{self.screen_w - WIDTH}+{self.root.winfo_y()}")

    # ---------- 动画：呼吸 / 眨眼 / 尾巴 ----------
    def _start_animations(self):
        def breathe():
            dy = 1
            while True:
                time.sleep(0.4)
                self.canvas.move("body", 0, dy)
                dy = -dy
        threading.Thread(target=breathe, daemon=True).start()

        def blink_loop():
            while True:
                time.sleep(random.uniform(2.5, 5.5))
                self._blink()
        threading.Thread(target=blink_loop, daemon=True).start()

        def tail_loop():
            while True:
                for _ in range(6):
                    self.canvas.move(self.tail, 0, -2)
                    time.sleep(0.1)
                for _ in range(6):
                    self.canvas.move(self.tail, 0, 2)
                    time.sleep(0.1)
                time.sleep(1.5)
        threading.Thread(target=tail_loop, daemon=True).start()

    def _blink(self):
        if self.blinking:
            return
        self.blinking = True
        c = self.canvas
        for eye in (self.eye_l, self.eye_r):
            x1, y1, x2, y2 = c.coords(eye)
            midy = (y1 + y2) / 2
            c.coords(eye, x1, midy, x2, midy)   # 压成一条线
        time.sleep(0.12)
        for eye in (self.eye_l, self.eye_r):
            x1, y1, x2, y2 = c.coords(eye)
            midy = (y1 + y2) / 2
            c.coords(eye, x1, midy - 14, x2, midy + 14)  # 恢复
        self.blinking = False

    # ---------- 北京时间 ----------
    def _start_clock(self):
        def update():
            while True:
                now = datetime.now(BJ_TZ)
                self.canvas.itemconfig(self.clock_id, text=now.strftime("%Y-%m-%d %H:%M:%S"))
                time.sleep(1)
        threading.Thread(target=update, daemon=True).start()

    # ---------- 气泡 ----------
    def _show_bubble(self, text):
        c = self.canvas
        c.itemconfig(self.bubble_txt, text=text[:120])
        c.itemconfig(self.bubble, state="normal")
        c.itemconfig(self.bubble_txt, state="normal")
        self.bubble_visible = True

        def hide():
            time.sleep(6)
            if self.bubble_visible:
                c.itemconfig(self.bubble, state="hidden")
                c.itemconfig(self.bubble_txt, state="hidden")
                self.bubble_visible = False
        threading.Thread(target=hide, daemon=True).start()

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

    def _translate_and_show(self, text):
        def do():
            result = self.translate(text)
            self.root.after(0, lambda: self._show_bubble(result))
        threading.Thread(target=do, daemon=True).start()

    def translate(self, text):
        if requests is None:
            return "未安装 requests，请先 pip install requests"
        # 判断语言方向：含较多中文则译成英文，否则译成中文
        cn_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        if cn_count > 0:
            src, dst = "zh-CN", "en"
        else:
            src, dst = "en", "zh-CN"

        # 1. MyMemory（整句翻译效果好，免费无需 key）
        try:
            url = "https://api.mymemory.translated.net/get"
            params = {"q": text, "langpair": f"{src}|{dst}"}
            r = requests.get(url, params=params, timeout=8)
            r.raise_for_status()
            data = r.json()
            if data.get("responseStatus") == 200:
                result = data["responseData"]["translatedText"]
                if result:
                    return result
        except Exception:
            pass

        # 2. 有道词典（国内必达，单词/短语）
        try:
            url = "https://dict.youdao.com/jsonapi"
            r = requests.post(url, data={"q": text}, headers={
                "Referer": "https://dict.youdao.com/",
                "User-Agent": "Mozilla/5.0"}, timeout=8)
            j = r.json()
            if "translate" in j and j["translate"]:
                return j["translate"][0].get("tgt", "")
            if "ec" in j:
                word = j["ec"]["word"][0]
                trs = word.get("trs", [])
                if trs:
                    items = trs[0].get("tr", [{}])[0].get("l", {}).get("i", [])
                    if items:
                        return "; ".join(items[:3])
        except Exception:
            pass

        # 3. 百度联想（单词兜底）
        try:
            url = "https://fanyi.baidu.com/sug"
            r = requests.post(url, data={"kw": text}, headers={
                "Referer": "https://fanyi.baidu.com/"}, timeout=8)
            j = r.json()
            if j.get("data"):
                return j["data"][0]["v"]
        except Exception:
            pass

        return "翻译失败：所有接口不可用"

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
                self._show_bubble(text if text else "未识别到文字")
        except Exception as e:
            self._show_bubble(f"截图失败: {e}")
        finally:
            self.root.deiconify()

    def _ocr(self, image_path):
        # 调用同目录 ocr.ps1（Windows 自带 OCR），隐藏 PowerShell 窗口
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr.ps1")
        try:
            flags = 0
            if os.name == "nt":
                flags = subprocess.CREATE_NO_WINDOW
            r = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", script, image_path],
                capture_output=True, text=True, timeout=90, creationflags=flags
            )
            return r.stdout.strip()
        except Exception as e:
            return f"OCR失败: {e}"

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    DesktopPet().run()
