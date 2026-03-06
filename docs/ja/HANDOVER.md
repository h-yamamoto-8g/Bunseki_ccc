# 引き継ぎ書 — 類似アプリ開発に向けて（日本語版）

> このファイルは参照用です。Claude Code CLI が読み込むのは `docs/HANDOVER.md`（英語版）です。

> 本ドキュメントは Bunseki_ccc の開発で得た知見をまとめたものです。
> 類似アプリを Claude Code CLI / claude.ai で新規開発する際の参考資料として使用してください。

---

## 1. プロジェクト概要

- **目的**: 製造所排水の環境分析業務を補助する PySide6 製デスクトップアプリ
- **配布方法**: PyInstaller で **ワンファイル exe** にビルドし、**SharePoint** 経由で配布
- **データ共有**: `app_data/` フォルダを SharePoint 同期フォルダに配置し、複数ユーザーで共有
- **開発環境**: macOS / **本番環境**: Windows 10/11

---

## 2. app_data の仕組み（最重要）

### 2.1 DATA_PATH の解決チェーン

`app/config.py` の `_resolve_data_path()` で起動時に決まる。優先順位:

1. **ユーザー設定ファイル** `~/.bunseki/settings.json` の `app_data_path` キー
2. **Windows SharePoint 規定パス**（チームのSharePoint同期パス）
3. **非 Windows フォールバック** `~/app_data`（存在しないことを想定→設定ダイアログ表示）

> 重要: settings.json はユーザーのホームに保存される（SharePoint 上ではない）。各マシンごとに異なるパスを持てる設計。

### 2.2 app_data ディレクトリ構成

```
DATA_PATH/
├── _common/                          ← 全ユーザー共有（読み取り専用的に使う）
│   ├── master_data/source/
│   │   ├── holder_groups.json        ← HG マスタ
│   │   ├── valid_samples.json        ← 試料マスタ
│   │   ├── valid_holders.json        ← HG バリデーション
│   │   └── valid_tests.json          ← 検査項目マスタ
│   ├── data/lab_aid/
│   │   ├── raw/                      ← Extractor 出力（生データ CSV）
│   │   └── normalized/bunseki.csv    ← ETL 出力（正規化済み）
│   └── tools/
│       ├── lab_aid_extractor/dist/   ← 外部 exe ツール
│       └── lab_aid_etl/dist/         ← 外部 exe ツール
└── bunseki/                          ← アプリ固有データ
    ├── config/
    │   ├── users.json                ← ユーザーアカウント（SHA-256 ハッシュ）
    │   └── hg_config.json            ← HG チェックリスト設定
    ├── tasks/tasks.json              ← タスク（業務案件）データ
    ├── data/anomalies.json
    ├── news/news.json
    ├── jobs/jobs.json
    ├── manuals/
    └── logs/
```

### 2.3 致命的だったバグ: DATA_PATH がインポート時に固定される問題

全 store モジュールが `from app.config import DATA_PATH` でモジュールレベル定数としてキャッシュしていた。`reload_paths()` で config を更新しても、各 store の変数は古い値のまま。

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

**新規アプリでもこのパターンを必ず踏襲すること。**

### 2.4 添付ファイルパスは相対パスで保存

SharePoint 経由で共有するため、各ユーザーのローカルパスは異なる。

```python
# 保存時: DATA_PATH からの相対パスに変換
rel = str(dest.relative_to(_cfg.DATA_PATH))

# 読み込み時: 相対パスなら DATA_PATH を付加
if not p.is_absolute():
    p = _cfg.DATA_PATH / p
```

---

## 3. 開発環境 (macOS) と本番環境 (Windows) の違い

### 3.1 フォント

| 環境 | Qt フォント | matplotlib フォント |
|------|-----------|-------------------|
| macOS | Hiragino Sans 12pt | Hiragino Sans |
| Windows | Yu Gothic UI 10pt | Yu Gothic |

```python
if platform.system() == "Darwin":
    qapp.setFont(QFont("Hiragino Sans", 12))
    matplotlib.rcParams["font.family"] = "Hiragino Sans"
else:
    qapp.setFont(QFont("Yu Gothic UI", 10))
    matplotlib.rcParams["font.family"] = "Yu Gothic"
```

### 3.2 DATA_PATH デフォルト
- **Windows**: チームのSharePoint同期パス
- **macOS / Linux**: `~/app_data`（存在しない前提→設定ダイアログ強制表示）

### 3.3 ファイルオープン

```python
if platform.system() == "Darwin":
    subprocess.Popen(["open", str(path)])
elif platform.system() == "Windows":
    os.startfile(str(path))
else:
    subprocess.Popen(["xdg-open", str(path)])
```

### 3.4 外部ツール
`lab_aid_extract.exe` / `lab_aid_etl.exe` は Windows 専用。macOS 開発時は `data_update_service.py` の `ENABLED = False` で無効化する。

### 3.5 開発時の注意
- mac で動作確認 → Windows で exe ビルド → SharePoint で配布のフロー
- macOS で問題なくても Windows で崩れるケースが多い（フォントサイズ、パス区切り文字）
- `Path` オブジェクトを使えばパス区切りは自動処理されるが、文字列結合は NG

---

## 4. ワンファイル exe (PyInstaller) のポイント

### 4.1 ビルドコマンド

```bash
pip install pyinstaller
pyinstaller bunseki.spec
# → dist/Bunseki.exe（単体で動作するワンファイル）
```

### 4.2 spec ファイルの要点

```python
a = Analysis(
    ["main.py"],
    datas=[("resources/assets/splash.png", "resources/assets")],
    hiddenimports=[
        "matplotlib.backends.backend_qtagg",  # matplotlib が動的にロードする
        "PySide6.QtSvg",                       # SVG アイコン表示に必要
        "PySide6.QtSvgWidgets",
        "openpyxl",                            # 帳票出力
    ],
    excludes=[
        "matplotlib.backends.backend_tk",      # Tcl/Tk は不要（サイズ削減）
        "matplotlib.backends.backend_tkagg",
        "PyQt5", "PyQt6",                      # PySide6 と競合防止
    ],
)
```

### 4.3 app_data は exe に含めない

`app_data/` は SharePoint 同期フォルダに別途配置する。exe に同梱すると:
- ユーザーごとのデータ更新ができない
- exe サイズが膨大になる
- SharePoint 共有の意味がなくなる

### 4.4 リソース（SVG アイコン等）は Qt Resource にコンパイル

```
resources/assets/*.svg → resources.qrc → app/ui/generated/resources_rc.py
```

`resources_rc.py` は Python ファイルなので exe に自動同梱される。外部ファイルとして配置する必要がない。

---

## 5. バグ修正で得た教訓（重要度順）

### 5.1 [致命的] PySide6 + six + shibokensupport の import 競合

**症状**: PyInstaller ビルドで `AttributeError` が発生しアプリが起動しない
**原因**: PySide6 が `builtins.__import__` をパッチし、`six` ライブラリの `_SixMetaPathImporter` と競合

**解決策（2段階の防御が必要）**:
```python
# 第1段階: __import__ の復元
import builtins
_original_import = builtins.__import__
# ... PySide6 の import ...
builtins.__import__ = _original_import

# 第2段階: PyInstaller frozen 環境専用
if getattr(sys, "frozen", False):
    try:
        import shibokensupport.feature as _sbk_feature
        _sbk_feature._mod_uses_pyside = lambda *_a, **_kw: False
    except Exception:
        pass
```

### 5.2 [致命的] スプラッシュスクリーンの起動順序問題

**最終解決策**: PyInstaller Splash（exe 展開中）+ QSplashScreen（Python 起動後）の2段構え

**必須の順序**:
```
1. QApplication 生成（最小限の import のみ）
2. QSplashScreen 表示
3. heavy import（matplotlib, app.* モジュール）
4. processEvents() を挟んでスプラッシュを描画し続ける
5. 最低表示時間 (1500ms) 経過後にスプラッシュを閉じる
```

### 5.3 [重要] ブロッキング処理でアニメーションが止まる

**症状**: ローディングスピナーが表示されるが回転しない
**原因**: `subprocess.run()` がメインスレッドをブロックし、`QTimer` イベントが処理されない
**解決策**: `QThread` で別スレッドに逃がし、メインスレッドでイベントループを回す

### 5.4 [重要] 変数名 `app` と パッケージ名 `app` の衝突

**解決策**: QApplication の変数名は `qapp` にする。パッケージ名と同名の変数を絶対に使わない。

### 5.5 [重要] 回覧の差戻し時にデータが消える

**原因**: 2段階の `update` で中間状態が不整合
**解決策**: 1回の `update_task_field()` で全フィールドをアトミックに書き込む

### 5.6 [中] ログインダイアログが背面に隠れる

**解決策**: `WindowStaysOnTopHint` + `raise_()` + `activateWindow()` の3点セット

### 5.7 [中] 未設定ユーザーにパス設定ダイアログが出ない

**解決策**: 「パスが存在するか」ではなく `~/.bunseki/settings.json` の存在・内容で判定する

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

依存方向は **一方通行**。下位レイヤーが上位レイヤーを import してはいけない。

### 6.2 ステートマシン（業務フロー）

タスクは 7 つのステートを順に遷移する:
```
起票 → 分析対象 → 分析準備 → データ入力 → データ確認 → 回覧 → 終了
```

各ステートは `app/ui/states/{state_name}/` に `state.py`（UI）+ `wrapper.py`（ロジック橋渡し）を持つ。

### 6.3 設定管理

- グローバル設定: `app/config.py` のモジュールレベル変数
- ユーザーローカル設定: `~/.bunseki/settings.json`
- アプリデータ: `DATA_PATH/` 配下の各種 JSON

---

## 7. 新規アプリ開発時の推奨手順

### 7.1 初期セットアップ
1. 本リポジトリをテンプレートとしてコピー
2. `docs/requirements.md` を新業務に合わせて書き換える
3. `docs/CLAUDE.md` のプロジェクト概要を更新
4. `app/config.py` のパス定義を新アプリ名に変更
5. ステート定義を新業務フローに合わせて再設計

### 7.2 Claude Code に最初に渡すべき情報
```
1. CLAUDE.md（コーディング規約・アーキテクチャルール）
2. requirements.md（機能要件）
3. HANDOVER.md（過去のバグと教訓）
4. app/config.py（パス設計の実例）
5. main.py の起動シーケンス（スプラッシュ〜ログイン〜メイン画面）
```

### 7.3 最初から入れておくべき防御コード
```python
# 1. builtins.__import__ 復元（PySide6 + six 競合防止）
# 2. shibokensupport monkey-patch（PyInstaller frozen 環境）
# 3. DATA_PATH は関数経由の遅延評価
# 4. QApplication 変数名は qapp（パッケージ名 app との衝突防止）
# 5. スプラッシュ → heavy import → ログインの起動順序
# 6. 外部プロセス実行は QThread
# 7. ファイルパスは Path オブジェクト + 相対パスで保存
```

---

## 8. 技術スタック

| 項目 | ライブラリ | 備考 |
|------|-----------|------|
| UI | PySide6 >= 6.7 | PyQt ではない。ライセンスの違いに注意 |
| データ処理 | pandas >= 2.0 | CSV 読み込み・集計 |
| グラフ | matplotlib >= 3.7 | バックエンドは `qtagg`（hiddenimports に追加必須）|
| 帳票 | openpyxl >= 3.1 | Excel 出力 |
| ビルド | PyInstaller | ワンファイルモード (`--onefile`) |
| アイコン生成 | cairosvg + Pillow | `tools/gen_icon.py`, `tools/gen_splash.py` |

---

## 9. 開発期間の振り返り

- **2/26**: 初期コミット
- **3/2**: UI 作成・機能追加
- **3/3 午前**: 本番パス切り替え、SharePoint 対応、添付ファイル相対パス化
- **3/3 午後**: PyInstaller 対応開始 → DATA_PATH 遅延評価バグ修正
- **3/4 深夜〜朝**: PySide6+six 競合、スプラッシュ、起動順序、変数名衝突 — **最も苦労した期間**
- **3/4 午前**: ローディング UI、ワンファイル化完了

**最大の教訓**: PyInstaller 化は最後に回さず、**早い段階で exe ビルドを試す**こと。import 順序、パス解決、ライブラリ競合など、開発環境では見つからないバグが大量に出る。
