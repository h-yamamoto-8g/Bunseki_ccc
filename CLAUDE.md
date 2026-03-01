# CLAUDE.md — Bunseki プロジェクト指示書

## プロジェクト概要

**Bunseki** は分析業務管理デスクトップアプリ。
分析担当者がタスク（起票→サンプル確認→分析→データ入力→データ確認→回覧→終了）を一元管理する。

---

## 環境・実行制約

| 項目 | 内容 |
|------|------|
| OS | Windows 11（社内PC） |
| ネットワーク | 社内LAN・インターネットあり |
| 配布形式 | PyInstaller で単一実行ファイル（Python環境不要） |
| DB | **禁止**（JSONとCSVのみ使用） |
| SMTP | **禁止**（メール送信はOutlook起動 / pywin32でメール作成・表示のみ） |
| 外部API | **禁止**（社内PCからの外部アクセス不可） |

---

## 使用技術スタック

```
GUI:         PySide6
集計・処理:   pandas, numpy
グラフ:       matplotlib (QtAgg backend) ※文字化けに注意（日本語フォント設定必須）
Excel操作:   openpyxl
メール作成:   pywin32（win32com.client でOutlook操作）
ビルド:       PyInstaller
Python:      3.11+
```

依存ライブラリを追加する場合は **メジャーで実績のあるライブラリ** を選択すること。

---

## ディレクトリ構成（目標）

```
/
├── CLAUDE.md
├── requirements.md          # 機能要件・画面仕様（正）
├── main.py                  # エントリポイント
├── assets/                  # SVGアイコン等
├── app/
│   ├── config.py            # 定数・パス定義
│   ├── data/
│   │   ├── loader.py        # DataLoader（CSV/JSON読み込み・集計）
│   │   └── task_store.py    # タスクCRUD（JSON永続化）
│   ├── widgets/             # 共通ウィジェット（サイドバー等）
│   ├── pages/               # page 種別の画面
│   ├── states/              # tasks.{state} 種別の画面
│   └── dialogs/             # dialog 種別の画面
└── app_data/                # データルート（SharePoint同期フォルダ）
    ├── _common/
    │   ├── data/lab_aid/normalized/bunseki.csv
    │   └── master_data/source/
    │       ├── holder_groups.json
    │       └── valid_samples.json
    └── bunseki/
        ├── config/settings.json
        ├── tasks/tasks.json
        ├── logs/app.log
        └── attachments/     # 回覧添付ファイル
```

---

## データソース仕様

### bunseki.csv
- 行数：約24万行（低速フィルタに注意、必要に応じてキャッシュ）
- `holder_group_code`: HG_001〜HG_014
- `sample_sampling_date`: YYYYMMDDHHMMSS形式の数値
- `test_raw_data`: 数値に `<`, `>` 等の記号が混在 → 計算時は記号を除去して数値のみ使用
- `trend_enabled`: true/false（文字列）→ bool変換して使用
- `test_judgment`: NN = 正常扱い、NN以外 = そのまま異常フラグとして表示

### 異常検知ロジック（mean ± 2σ）
- 対象: `trend_enabled = true` かつ同一 `holder_group_code` + `valid_sample_set_code` + `valid_test_set_code`
- 計算に使う期間: **過去5年分**（分析対象データの日付を基準）
- データ件数が3件未満の場合は判定不可（None扱い）
- stdが0の場合は正常扱い

### tasks.json
- タスクID: `{起票日時}_{ホルダーグループコード}` 例: `20250107152900_HG_003`
- タスク名: `{起票日時}_{ホルダーグループ名}`
- 各stateの進捗は `state_data.{state_name}` に保存

---

## 画面・state 一覧

| 画面ID | kind | 名前 | 実装状況 |
|--------|------|------|----------|
| home | page | ホーム | 要実装 |
| tasks | page | タスク | 要実装 |
| data | page | データ | 要実装 |
| news | page | ニュース | 要実装 |
| library | page | ライブラリ | 要実装 |
| log | page | ログ | 要実装 |
| job | page | ジョブ | 要実装 |
| settings | page | 設定 | 要実装 |
| logon | dialog | ログオン | 要実装 |
| setup | dialog | セットアップ | 要実装 |
| tasks.task_ticket | state | 起票 | 要実装 |
| tasks.analysis_targets | state | 分析対象 | 要実装 |
| tasks.analysis | state | 分析準備 | 要実装 |
| tasks.result_entry | state | データ入力 | 要実装 |
| tasks.result_verification | state | データ確認 | 要実装 |
| tasks.submission | state | 回覧 | 要実装 |
| tasks.completed | state | 終了 | 要実装 |

詳細仕様は `requirements.md` を参照すること。

---

## アーキテクチャ方針

### ウィンドウ構成
- メインウィンドウ1枚（タブ切り替え）
- 最小サイズ: 1280 × 800px
- 起動時フルスクリーン
- タイトル: `Bunseki ver.{バージョン}`

### サイドバー
- `kind=page` の画面のみ表示（state・dialog は非表示）
- 現在のページをハイライト
- SVGアイコンで各ページを表示

### tasks.{state} 共通UI
- 画面上部中央にステータスアイコン群（ブレッドクラム）
- アクティブ状態は名前も表示、非アクティブはグレーアウト
- ステータスアイコンはリンクで直接遷移可能
- 左端にタスク名、右端にユーザー名
- 下部に「戻る」「次へ」ボタン

### state 遷移フロー
```
task_ticket → analysis_targets → analysis → result_entry → result_verification → submission → completed
```

### 戻りルール
- 全stateから他stateへ移動可能
- `task_ticket` と `analysis_targets` は読み取り専用がデフォルト、「編集」ボタンで編集モード
- 編集モードで保存 → 警告ダイアログ → 以降のstateをリセット
- 回覧後の確認者は `result_verification` と `submission` 以外は読み取り専用

### ロール管理
- **起票者**: 全stateを操作可能（回覧後は制限あり）
- **確認者**: `result_verification`, `submission` のみ操作可能
- **代理回覧**: 他人の進行中タスクを代理で操作可能（記録に残す）

---

## コーディング規約

### 全般
- Python 3.11+の型ヒントを使用（`X | Y`, `list[X]`形式）
- クラス名: PascalCase / 変数・関数: snake_case
- ファイルは機能単位で小さく保つ（1ファイル = 1クラスが目安）
- コメントは日本語でOK（ロジックが自明でない箇所のみ）

### PySide6
- シグナル/スロットパターンを徹底する
- UIの構築は `_setup_ui()` メソッドにまとめる
- データのロードは `load_task()` / `load_data()` 等の公開メソッドで行う
- 重い処理（CSV読み込み等）は `QThread` または `QRunnable` で非同期化

### matplotlib（グラフ）
- 日本語フォントを明示的に設定（`rcParams['font.family']`）
- Windows向け: `'Yu Gothic'` または `'Meiryo'` を優先
- backend は `QtAgg` を使用
- グラフは `FigureCanvasQTAgg` で埋め込む

### データ処理
- `test_raw_data` の数値抽出は必ず `DataLoader.extract_numeric()` を使用
- 日付は `_fmt_date()` を通して表示用文字列に変換
- 集計に使う歴史データは **過去5年分** にフィルタすること

### エラーハンドリング
- 予期しないエラーは `QMessageBox.critical` でスタックトレース付き表示
- エラーログは `{app_data}/bunseki/logs/app.log` に記録
- SharePointフォルダが見つからない場合は赤バナーで警告 + セットアップボタン表示

---

## デザイン原則

- 軽い角丸（`border-radius: 6~8px`）
- 適度な余白（`padding: 16~32px`）
- 横いっぱいに広げすぎない（コンテンツは中央寄せ）
- 原色禁止（落ち着いたトーン）
- 文字色: 白 または `#333333`（暗色背景なら白、明色背景なら `#1e293b` 〜 `#374151`）
- ロード中はスピナー等でフィードバック
- グラフの文字化けに注意（日本語フォント設定必須）

---

## 起動・開発

```bash
# 開発実行
cd /Users/yamamotohikaru/Desktop/Bunseki
python main.py

# ビルド（Windows上で実行）
pyinstaller --onefile --windowed --name Bunseki main.py
```

---

## 重要メモ

- `app_data` のパスは `settings.json` で設定（初回起動時は `setup` ダイアログ）
- `bunseki.csv` は読み取り専用（書き込み不可）
- タスクデータの永続化は `tasks.json` のみ
- メール送信は pywin32 + Outlook を使用（SMTPは禁止）
- 回覧時の2σ超過データは別途JSONに記録し、`data` ページで参照可能にする
