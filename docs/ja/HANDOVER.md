# 引き継ぎ書 — 類似アプリ開発に向けて（日本語版）

> このファイルは参照用です。Claude Code CLI が読み込むのは `docs/HANDOVER.md`（英語版）です。

> 本ドキュメントは Bunseki_ccc の開発で得た知見をまとめたものです。

---

## 1. プロジェクト概要

- **目的**: 製造所排水の環境分析業務を補助する PySide6 製デスクトップアプリ
- **配布方法**: PyInstaller で **ワンファイル exe** にビルドし、**SharePoint** 経由で配布
- **データ共有**: `app_data/` フォルダを SharePoint 同期フォルダに配置し、複数ユーザーで共有
- **開発環境**: macOS / **本番環境**: Windows 10/11

---

## 2. USERPROFILE ベースのパス管理（最重要）

### 2.1 パス解決の仕組み

起動時に USERPROFILE（ユーザーのホームフォルダ）を基準に全パスを自動導出する。

**設定ファイル**: `~/.bunseki/settings.json`

```json
{
  "user_profile_path": "C:\\Users\\12414"
}
```

**導出ルール**:
| 変数 | 導出先 |
|------|--------|
| `USERPROFILE` | `C:\Users\12414` |
| `SYNC_ROOT` | `{USERPROFILE}\トクヤマグループ` |
| `DATA_PATH` | `{USERPROFILE}\トクヤマグループ\環境分析課 - ドキュメント\app_data` |

**解決優先順位**:
1. `~/.bunseki/settings.json` の `user_profile_path`
2. フォールバック: `Path.home()`（未設定時はダイアログで設定を促す）

**後方互換**: 旧設定（`app_data_path`, `sync_root_path`）が存在する場合はフォールバックとして使用。

### 2.2 ツール設定のパス変数

ツール設定のパス入力欄で以下の変数が使える:

| 変数 | 展開先の例 |
|------|-----------|
| `%USERPROFILE%` | `C:\Users\12414` |
| `%SYNC_ROOT%` | `C:\Users\12414\トクヤマグループ` |
| `%DATA_PATH%` | `C:\Users\12414\トクヤマグループ\環境分析課 - ドキュメント\app_data` |

展開処理は `_expand_path()` 関数で統一的に行われる:
1. アプリ独自変数（`%SYNC_ROOT%`, `%DATA_PATH%`）を置換
2. OS 環境変数（`%USERPROFILE%` 等）を `os.path.expandvars()` で展開

### 2.3 app_data ディレクトリ構成

```
DATA_PATH/
├── _common/                          ← 全ユーザー共有
│   ├── master_data/source/
│   │   ├── holder_groups.json        ← HG マスタ
│   │   ├── valid_samples.json        ← 試料マスタ
│   │   ├── valid_holders.json        ← HG バリデーション
│   │   └── valid_tests.json          ← 検査項目マスタ
│   ├── data/lab_aid/
│   │   ├── raw/                      ← Extractor 出力（生データ CSV）
│   │   └── normalized/bunseki.csv    ← ETL 出力（正規化済み）
│   └── tools/
└── bunseki/                          ← アプリ固有データ
    ├── config/
    │   ├── users.json                ← ユーザーアカウント
    │   ├── hg_config.json            ← HG チェックリスト設定
    │   └── data_config.json          ← 列設定・ツールパス設定
    ├── tasks/tasks.json              ← タスクデータ
    ├── data/anomalies.json
    ├── news/news.json
    ├── jobs/jobs.json
    └── logs/
```

### 2.4 致命的だったバグ: DATA_PATH がインポート時に固定される問題

全 store モジュールが `from app.config import DATA_PATH` でモジュールレベル定数としてキャッシュしていた。

**解決策**: 全 store で関数経由の遅延評価に変更:

```python
# NG: モジュールレベルで固定される
from app.config import DATA_PATH
TASKS_FILE = DATA_PATH / "bunseki" / "tasks" / "tasks.json"

# OK: 呼び出し時に最新の DATA_PATH を参照
import app.config as _cfg
def _tasks_file():
    return _cfg.DATA_PATH / "bunseki" / "tasks" / "tasks.json"
```

### 2.5 添付ファイルパスは相対パスで保存

SharePoint 経由で共有するため、各ユーザーのローカルパスは異なる。

---

## 3. 開発環境 (macOS) と本番環境 (Windows) の違い

### 3.1 フォント

| 環境 | Qt フォント | matplotlib フォント |
|------|-----------|-------------------|
| macOS | Hiragino Sans 12pt | Hiragino Sans |
| Windows | Yu Gothic UI 10pt | Yu Gothic |

### 3.2 ファイルオープン

`_open_file()` で OS に応じて分岐:
- Windows: `os.startfile()` — `.appref-ms` 等のシェル関連付けにも対応
- macOS: `subprocess.Popen(["open", ...])`
- Linux: `subprocess.Popen(["xdg-open", ...])`

### 3.3 外部ツール
`lab_aid_extract.exe` / `lab_aid_etl.exe` は Windows 専用。macOS 開発時は無効化。

---

## 4. ワンファイル exe (PyInstaller)

### 4.1 ビルドコマンド

```bash
pip install pyinstaller
pyinstaller bunseki.spec
# → dist/Bunseki.exe
```

### 4.2 スプラッシュ画面

- `WindowStaysOnTopHint` は使用しない（他のアプリの背面に回れるようにする）
- PyInstaller Splash（exe 展開中）+ QSplashScreen（Python 起動後）の2段構え

### 4.3 app_data は exe に含めない

`app_data/` は SharePoint 同期フォルダに別途配置。

---

## 5. バグ修正で得た教訓（重要度順）

### 5.1 [致命的] PySide6 + six + shibokensupport の import 競合

**解決策**: `builtins.__import__` 復元 + `shibokensupport.feature` パッチの2段階防御。

### 5.2 [致命的] スプラッシュスクリーンの起動順序

```
1. QApplication 生成（最小限の import のみ）
2. QSplashScreen 表示（WindowStaysOnTopHint なし）
3. heavy import（matplotlib, app.* モジュール）
4. processEvents() を挟んでスプラッシュを描画し続ける
5. 最低表示時間経過後にスプラッシュを閉じる
```

### 5.3 [重要] openpyxl で .xlsm ファイルを開くとマクロが消える

**症状**: Excel でファイルを開くと「ファイル形式が正しくありません」エラー
**原因**: `load_workbook()` のデフォルトでは VBA マクロが破棄される
**解決策**: `load_workbook(path, keep_vba=True)` を使用

### 5.4 [重要] openpyxl.utils のインポートパス

**症状**: `cannot import name 'coordinate_from_string' from 'openpyxl.utils'`
**解決策**: `openpyxl.utils.cell` からインポートする

```python
# NG
from openpyxl.utils import coordinate_from_string
# OK
from openpyxl.utils.cell import coordinate_from_string, column_index_from_string
```

### 5.5 [重要] pandas が整数を float に変換する

**症状**: CSV の整数値が `0.0` と表示される
**解決策**: 表示時に float が整数値なら int にキャスト

```python
def _to_display(val) -> str:
    if val is None:
        return ""
    if isinstance(val, float):
        if val != val:  # NaN
            return ""
        if val.is_integer():
            return str(int(val))
        return str(val)
    s = str(val)
    return "" if s in ("nan", "None") else s
```

### 5.6 [重要] 回覧の差戻し時にデータが消える

**解決策**: 1回の `update_task_field()` で全フィールドをアトミックに書き込む。

### 5.7 [中] ブロッキング処理でアニメーションが止まる

**解決策**: `QThread` で別スレッドに逃がす。

---

## 6. アーキテクチャの要点

### 6.1 レイヤー構成（厳守）

```
UI (pages/, states/, dialogs/)
  ↓
UI ラッパー (wrapper.py) — UI イベントとサービスの橋渡し
  ↓
Service (services/) — ビジネスロジック
  ↓
Core (core/) — データ永続化 (JSON/CSV 読み書き)
```

### 6.2 ステートマシン（業務フロー）

```
起票 → 分析対象 → 分析準備 → データ入力 → データ確認 → 回覧 → 終了
```

各ステートは `app/ui/states/{state_name}/` に `state.py`（UI）+ `wrapper.py`（ロジック橋渡し）を持つ。

### 6.3 設定管理

| 設定 | 保存先 | 用途 |
|------|--------|------|
| USERPROFILE | `~/.bunseki/settings.json` | パスの基準 |
| 列設定・ツールパス | `{DATA_PATH}/bunseki/config/data_config.json` | 表示列・CSV出力列・ツール設定 |
| ユーザー | `{DATA_PATH}/bunseki/config/users.json` | ログイン認証 |
| HG 設定 | `{DATA_PATH}/bunseki/config/hg_config.json` | チェックリスト等 |

---

## 7. 技術スタック

| 項目 | ライブラリ | 備考 |
|------|-----------|------|
| UI | PySide6 >= 6.7 | PyQt ではない |
| データ処理 | pandas >= 2.0 | CSV 読み込み・集計 |
| グラフ | matplotlib >= 3.7 | バックエンドは `qtagg` |
| Excel 読み書き | openpyxl >= 3.1 | `.xlsm` は `keep_vba=True` 必須 |
| ビルド | PyInstaller | ワンファイルモード |
