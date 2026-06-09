# CharaSorter

キャラクターイラスト・動画に特化した、画像仕分けデスクトップアプリです。  
AIによるキャラクター自動認識・学習機能を搭載し、大量のファイルを素早くキャラ名フォルダへ整理できます。

---

## 動作環境

- Windows 10 / 11 (64bit)
- インストール不要。`CharaSorter.exe` をダブルクリックで起動します。
- **初回のAI分析時のみ**、AIモデル（約 500 MB）をインターネット経由で自動ダウンロードします。

---

## 使い方

1. **振り分け先** フォルダ（整理先）を選択
2. **仕分け元** フォルダ（未整理画像の置き場所）を選択
3. 表示された画像のキャラクター名などを入力 → **移動 (Ctrl+Enter)**

### キーボードショートカット

| キー | 動作 |
|---|---|
| `Ctrl + Enter` | ファイルを移動 |
| `Ctrl + →` | スキップ（次へ） |
| `Ctrl + ←` | 前の画像に戻る |
| `Ctrl + D` | ゴミ箱に削除 |
| `Ctrl + Z` | 直前の移動を元に戻す |
| `Ctrl + Q` | AI でキャラクターを自動認識 |
| `Ctrl + P` | 外部プレーヤーで再生 |

### AI 自動認識

- オプション行の **作品名** 欄に作品名（例: `series_a`）を入力すると、その作品のキャラクターだけを候補に絞り込みます。
- 空欄のままにすると全キャラクタータグが対象になります。
- **📋 ボタン**で現在の作品名フィルタに対応するタグ一覧を確認できます（クリックでキャラ欄に挿入）。
- **自動AI** をONにすると、ファイルを開くたびに自動で解析します。
- 動画ファイルは複数フレームをサンプリングしてAI解析します。

### Danbooru 自動検索

画像を開いたとき、Danbooru に同一画像が登録されていればキャラクター名・作者名を自動取得します。  
エントリが空の場合は自動入力、作者名はステータスバーに表示されます。

**APIキーの取得手順（任意・無料アカウントでも動作します）**

1. [https://danbooru.donmai.us](https://danbooru.donmai.us) にログイン
2. 右上のユーザー名 → **My Account** → **API Keys** → **New API Key**
3. **Name** に任意の名前（例: `CharaSorter`）を入力
4. **Permissions** で `posts:index` を選択（空白のままにすると全権限）
5. **Create** → 表示されたキーをコピー
6. CharaSorter の ⚙ 設定 → **Danbooruログイン名** と **Danbooru APIキー** に入力

APIキーなしでも匿名で動作しますが、レート制限が厳しめになります。

### キャラ順序の学習

移動操作をくり返すうちに、入力したキャラの並び順を自動で学習します。  
次回のAI認識結果は、過去の登録順に合わせて自動ソートされます（設定でOFF可能）。

### ファイル命名規則

| パターン | 出力ファイル名 |
|---|---|
| キャラ1人・フォルダ分けON | `振り分け先/charname/charname_001.jpg` |
| キャラ複数・またはフォルダ分けOFF | `振り分け先/char1_char2_001.jpg` |
| 動画prefix オン | `振り分け先/charname/_m_charname_001.mp4` |

---

## 設定ファイル

`sort_ui_config.json`（exe と同じフォルダ）に設定が保存されます。  
手動で削除するとリセットされます。

---

## ライセンス・クレジット

### AI モデル
本アプリの AI 自動認識機能は以下のモデルを実行時にダウンロードして使用します。

> **WD-SwinV2-Tagger-v3** by SmilingWolf  
> <https://huggingface.co/SmilingWolf/wd-swinv2-tagger-v3>  
> License: **Apache 2.0**

モデルのファイル自体はアプリに同梱されていません。  
利用規約の詳細は上記リンクのモデルカードをご確認ください。

### アプリケーションコード
本アプリのコードは **Claude (Anthropic)** との対話によって生成・改良されました。

> Portions of this application were generated with the assistance of  
> **Claude** by **Anthropic** (<https://www.anthropic.com/>).

本アプリのソースコードは自由に改変・再配布できます。  
**Claude などの AI を利用しての改造・派生物の作成も明示的に許可します。**  
改変時はこのクレジット表記を残していただけると幸いです。

### 使用ライブラリ（主要）

| ライブラリ | ライセンス |
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

## ビルド方法（開発者向け）

```bash
# アイコン再生成
python make_icon.py

# exe ビルド
python -m PyInstaller --onefile --windowed --name CharaSorter --icon sort_ui.ico \
  --hidden-import cv2 --hidden-import pandas --hidden-import onnxruntime \
  --hidden-import huggingface_hub --hidden-import send2trash sort_ui.py
```
