# 桌面宠物 Desktop Pet

Windows 桌面宠物小工具，功能：

1. **贴边隐藏**：窗口贴屏幕右边缘，鼠标移开自动隐藏（只露一条边），移过去展开
2. **北京时间**：实时显示北京时间（解决电脑是洛杉矶时区的问题）
3. **文字翻译**：选中文字后按 Ctrl+C 复制，自动翻译成中文显示
4. **截图翻译**：点"截图翻译"按钮，截取屏幕识别文字并翻译（兜底，用于不能选中的地方）

## 依赖安装

```bash
pip install pyperclip requests mss
```

## 运行

```bash
python desktop_pet.py
```

## 文件说明

- `desktop_pet.py`：主程序（Tkinter + pyperclip + requests + mss）
- `ocr.ps1`：Windows 自带 OCR 兜底脚本（无需安装额外软件）

## 使用提示

- 翻译接口使用 Google 免费翻译接口，无需 API Key
- 截图翻译依赖 Windows 自带 OCR（Win10/11 自带）
