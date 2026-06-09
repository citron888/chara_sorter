# CharaSorter

A desktop app for sorting character illustrations and videos into folders.  
Features AI-powered automatic character recognition and order-learning to organize large collections quickly.

> 他の言語: [日本語](README.md)

---

## Requirements

- Windows 10 / 11 (64-bit)
- No installation needed. Just double-click `CharaSorter.exe`.
- **On first AI analysis only**, the AI model (~500 MB) is downloaded automatically from the internet.

---

## How to Use

1. Select the **destination** folder (where sorted files go)
2. Select the **source** folder (where unsorted files are)
3. Type a character name for the displayed image → **Move (Ctrl+Enter)**

### Keyboard Shortcuts

| Key | Action |
|---|---|
| `Ctrl + Enter` | Move file to folder |
| `Ctrl + →` | Skip (next file) |
| `Ctrl + ←` | Go back to previous file |
| `Ctrl + D` | Send to trash |
| `Ctrl + Z` | Undo last move |
| `Ctrl + Q` | Auto-recognize character with AI |
| `Ctrl + P` | Open in external player |

### AI Recognition

- Enter a **work/series name** (e.g. `series_a`) in the options bar to narrow candidates to that series only.
- Leave it blank to search all character tags.
- The **📋 button** shows a tag list for the current series filter — click any tag to insert it.
- Enable **Auto AI** to analyze every file automatically when it opens.
- Video files are analyzed by sampling multiple frames.

### Danbooru Auto-Lookup

When opening an image, if it exists on Danbooru, the character name and artist are fetched automatically.  
The artist name is shown in the status bar.

**Getting an API key (optional — works without one too)**

1. Log in at [https://danbooru.donmai.us](https://danbooru.donmai.us)
2. Username (top-right) → **My Account** → **API Keys** → **New API Key**
3. Enter any **Name** (e.g. `CharaSorter`)
4. Select `posts:index` under **Permissions** (or leave blank for full access)
5. **Create** → copy the key
6. In CharaSorter: ⚙ Settings → enter **Danbooru Login** and **Danbooru API Key**

Without an API key the app works anonymously but with stricter rate limits.

### Auto-sorting of Character Candidates

The app records the order in which you enter character names and re-sorts AI recognition candidates to match your past input order.  
The AI model itself is not retrained (can be disabled in settings).

### File Naming

| Pattern | Output filename |
|---|---|
| Single character, folder mode ON | `dest/charname/charname_001.jpg` |
| Multiple characters or folder mode OFF | `dest/char1_char2_001.jpg` |
| Video prefix ON | `dest/charname/_m_charname_001.mp4` |

---

## Notes

### Automatic Duplicate Deletion
If a file with an **identical MD5 hash** already exists in the destination folder, the source file is automatically sent to the **Recycle Bin**.  
This typically happens when you try to move the same image twice. The file can be restored from the Recycle Bin.  
This behavior can be disabled by turning off **Duplicate Check** in settings.

---

## Settings File

Settings are saved to `sort_ui_config.json` in the same folder as the exe.  
Delete it to reset all settings.

---

## License & Credits

### AI Model
The AI recognition feature downloads and uses the following model at runtime.

> **WD-SwinV2-Tagger-v3** by SmilingWolf  
> <https://huggingface.co/SmilingWolf/wd-swinv2-tagger-v3>  
> License: **Apache 2.0**

The model is not bundled with the app — it is downloaded automatically on first use.

### Application Code
This app was created with the assistance of **Claude (Anthropic)**.

> Portions of this application were generated with the assistance of  
> **Claude** by **Anthropic** (<https://www.anthropic.com/>).

The source code may be freely modified and redistributed, including AI-assisted derivatives.  
Please keep this credit notice when distributing modified versions.

### Libraries Used

| Library | License |
|---|---|
| Python | PSF License |
| Pillow | HPND (PIL License) |
| OpenCV (cv2) | Apache 2.0 |
| onnxruntime-directml | MIT |
| huggingface_hub | Apache 2.0 |
| pandas | BSD 3-Clause |
| send2trash | BSD 3-Clause |
| PyInstaller | GPL-2.0 + Bootloader Exception |

---

## Building from Source

```bash
# Regenerate icon
python make_icon.py

# Build exe
python -m PyInstaller --onefile --windowed --name CharaSorter --icon sort_ui.ico \
  --hidden-import cv2 --hidden-import pandas --hidden-import onnxruntime \
  --hidden-import huggingface_hub --hidden-import send2trash sort_ui.py
```
