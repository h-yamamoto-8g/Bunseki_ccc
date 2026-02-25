# 機能要件・画面仕様

**バージョン**: 1.0  
**最終更新**: 2026-02-26

---

## 1. アプリ全体の仕様

### 起動・終了
- 実行ファイルでPython環境なしで運用
- 起動時に `{app_data}/bunseki/config/settings.json` を読み込む（なければデフォルト値で生成する）
- デフォルトで全画面表示

### ウィンドウ構成
- メインウィンドウ1枚（タブ切り替え方式）
- ウィンドウ最小サイズ: 1280 × 800px
- タイトルバー: 「Bunseki ver.{バージョン}」

---

## 2. 画面一覧

| 画面ID                      | kind   | 名前     | 概要                                          | 優先度 |
| ------------------------- | ------ | ------ | ------------------------------------------- | --- |
| home                      | page   | ホーム    | 当月の予定表と本日のタスク概要を表示するダッシュボード                 | 必須  |
| tasks                     | page   | タスク    | 新規タスクの起票と全体のタスクリストの表示                       | 必須  |
| data                      | page   | データ    | 過去データ一覧の確認                                  | 必須  |
| news                      | page   | ニュース   | 業務に関連する連絡事項を投稿・閲覧                           | 必須  |
| library                   | page   | ライブラリ  | 回覧した時の添付資料を一覧で                              | 必須  |
| log                       | page   | ログ     | 分析装置や試薬のログ                                  | 必須  |
| job                       | page   | ジョブ    | 分析に必要なJOB番号を設定                              | 必須  |
| settings                  | page   | 設定     | setting.jsonやusers.json等の編集                 | 必須  |
| logon                     | dialog | ログオン   | ユーザーとしてログオン                                 | 必須  |
| setup                     | dialog | セットアップ | ユーザー特有のデータパスを設定                             | 必須  |
| tasks.task_setup          | state  | 起票     | タスクの起票条件の入力                                 | 必須  |
| tasks.analysis_targets    | state  | 分析対象   | そのタスクで分析する対象のサンプルを表示                        | 必須  |
| tasks.analysis            | state  | 分析準備   | 分析に必要な情報を提供し、ユーザーの分析終了を待つ                   | 必須  |
| tasks.result_entry        | state  | データ入力  | データを入力する画面                                  | 必須  |
| tasks.result_verification | state  | データ確認  | データの確認と自動異常検知を行う                            | 必須  |
| tasks.submission          | state  | 回覧     | 分析結果を添付して確認者へ回覧<br>また、確認者は次の確認者へ回覧もしくは終了させる | 必須  |
| tasks.completed           | state  | 終了     | 終了                                          | 必須  |

### 画面種別（kind）定義 | kind | 意味 | サイドバー表示
---

| kind   | 意味                   | サイドバー表示 |
| ------ | -------------------- | ------- |
| page   | サイドバーから遷移するメイン画面     | する      |
| state  | page内部の表示切り替え(URLなし) | しない     |
| dialog | モーダルダイアログ(他画面に重なる)   | しない     |


## [page] home

**目的**: 今日やるべきことと当月全体の状況をひと目で把握するダッシュボード。

**表示内容**:
- 当月の予定表（web view）
    - 当月の予定表Excelをwebで表示
- 現在、進行中のタスクを一覧表示(自分のと他人ので分別)
    - ステータス内訳（`tasks.{state}`の名前）
- 新規タスクの起票(tasks.task_setupへの遷移)

**操作**:
- 新規タスク作成ボタンをクリックすることで`tasks.task_setup`に遷移
- タスク一覧のレコードをダブルクリックすることで進行中の`tasks.{state}`に遷移

**エラー・例外**:
-  再開したい進行中のタスクが見つからなかった場合は、その旨を赤い警告バナーで表示して、再起票ボタンを設置する
	- 再起票ボタンが押された時は、新規タスクボタンと同じく`tasks.task_setup`遷移
---

### [page] tasks

**目的**: タスクと分析業務の一連の流れ（起票 → 分析対象 → 分析準備 → データ入力 → 確認 → 回覧 → 完了）を管理する中心ページ。
業務フローを始める前の初期ページでは、タスク一覧と新規タスク起票ボタンを表示する。
タスク一覧は一覧表示で最新100件を取表示する。

表示内容**:
- タスク一覧テーブル（列：タスク名 / ホルダグループ名 / JOB番号 / ステータス / 担当者 / 最終更新日 / Action）
- ステータスフィルタ（全件 / 進行中 / 回覧中 / 終了/ `{user_name}` / 担当者）
- 最新100件を表示

**操作**:
- 「新規起票」ボタン → `tasks.analysis_targets` へ遷移
- 一覧の行をダブルクリック or Actionボタンクリック→ そのタスクの現在のstateに遷移（中断していた続きから再開）
- ステータスフィルタの切り替え → 一覧を絞り込む
- さらに表示ボタンをクリックして追加の100件を表示

#### state遷移フロー

```
[tasks.task_setup]: 新規起票
      ↓
[tasks.analysis_targets]: 分析対象サンプルの確認
      ↓
[tasks.analysis]: 分析準備情報の提供・分析終了待ち
      ↓
[tasks.result_entry]: データ入力
      ↓
[tasks.result_verification]: データ確認・自動異常検知
      ↓
[tasks.submission]: 回覧・承認
      ↓
[tasks.completed]: 終了
```

**前stateへの戻りルール**:
- すべてのstateからの他のstateへ行き来することができる
- 戻った先のstateは`tasks.task_setup`を除いて編集可能である。
- `task_setup`とを変更したい場合は「編集」ボタンを押して **編集モード** に切り替える
- `tasks.task_setup`と`tasks.analysis_targets`に戻って編集を保存した場合は、ダイアログで警告を出し、OKならそれ以降のstateを初期化する。
- 回覧後の確認者は`tasks.result_verification`と`tasks.submission`以外の編集無効(読み取り専用)とする。差し戻しをして分析者に変更をしてもらう。

---

#### [state] tasks.task_setup

**目的**: 新規起票

**表示内容**:
- ホルダグループ選択(ドロップダウンリスト)
- JOB番号選択(JOB番号入力欄と追加ボタン)

**データソース:**
- ファイル: `holder_groups.json`
- ホルダグループ
	- `holder_groups.json > items[].holder_group_name`の全て

**モード**:
- 起表示は編集可能
- 別ステータスを進行中は読み取り専用で「編集」ボタンで編集可能になるが、保存すると以降のstateを初期化
- 確認者へ回覧後は編集も無効

**操作**:
- 「起票」ボタン → 新しいタスクを作成し `tasks.analysis_targets` へ遷移
- JOB番号追加ボタン「+」をクリックでJOB番号入力欄に記載されているJOB番号をタグのように追加(初期値で管理者が設定したものが入っている)

**補足:**
- タスクIDは`{起票日時}_{ホルダグループコード}`
- タスク名は`{起票日時}_{ホルダグループ名}`
- 選択したホルダグループの`holder_groups.json::holder_group_code`を保持する

**前のstate**: なし（tasksページのデフォルト表示）  
**次のstate**: `tasks.analysis_targets`

---

#### [state] tasks.analysis_targets

**目的**: このタスクで分析するサンプルの一覧を確認する。

**モード**:
- **表示モード**（デフォルト）: 読み取り専用
- **編集モード**: 「編集」ボタンで切り替え。サンプルの追加・削除が可能 (編集した場合には編集済み表示をする)追加・削除したサンプルは記録する。
	- 別ステータスを進行中に編集した場合は、以降のstateを初期化
	- 確認者へ回覧後は編集無効

**表示内容**:
- タスク名（ヘッダー部）
- 分析対象サンプル一覧（列：JOB番号 / サンプリング日時 / サンプル名 / 中央値 / 最大値 / 最小値）
  
**操作**:
- 「追加」ボタン -> サンプル名をドロップダウンリストで追加か自由記入で追加
	- 自由記入の場合はタスク内限定で一時的に独自IDを内部で作成する。
	- 自由記入の場合は計算をしない。
- 「削除」ボタン -> サンプルのレコードを削除
- 「印刷」ボタン -> 横向きで1ページに列が入り切るように印刷(縦はページを跨いでも良い)
- 「次へ」ボタン -> tasks.analysis へ遷移
- 「戻る」ボタン -> `tasks.task_setup` へ遷移（表示モードで開く）

**データソース:**
- サンプル一覧テーブル
	- ファイル: `bunseki.csv`
	- サンプル取得の条件:
	    - `bunseki.csv::holder_group_code` = `tasks.task_setup` で選択した `holder_group_code`
	    - `job_number` が選択したJOB番号リストのいずれかに一致（OR検索）
	    - 重複なし
	- データの集計データの条件(AND検索)
		- サンプル条件で取得した`valid_sample_set_code`に該当
		- `trend_enabled`がtrue
		- `sample_sampling_date`が直近5年分
- サンプル追加
	- ファイル: `valid_samples.json`
	- 条件
		- `items[].is_active`がtrueの`items[].display_name`を`items[].sort_order`の順番で表示

**補足:**
ここで表示したサンプルの`bunseki.csv::valid_sample_set_code`を保持する。
`
**前のstate**: `tasks.task_setup  
**次のstate**: `tasks.analysis`

---

#### [state] tasks.analysis

**目的**: 分析に必要な情報（マニュアルやツールのリンクや分析前後に必要な確認項目）をユーザーに提供し、ユーザーが実際の分析を終えるまで待機する。

**表示内容**:
- 分析基準書のリンク
- 関連マニュアルのリンク
- 業務ツールのリンク
- 分析前確認リスト
- 分析後確認リスト

**操作**:
- リンク全般 -> Webリンクとファイルパスがある。
	- 必要に応じて開く方を切り替える
- 分析前後の確認リスト -> チェックボックスにチェックをいれる
	- 全てにチェックが入っていないと「分析終了」ボタンを押せない
	- 一括チェックボタンを配置
	- 確認者へ回覧後は編集不可
- 「分析終了」ボタン -> `tasks.result_entry` へ遷移
- 「戻る」ボタン -> `tasks.analysis_targets` へ遷移（表示モードで開く）

**前のstate**: `tasks.analysis_targets`  
**次のstate**: `tasks.result_entry`

---

#### [state] tasks.result_entry

**目的**: 分析が終わったデータを入力する。(開発は後回しで今回は下記の薄い実装で終了)

**表示内容**:
- 「通常のデータ入力を行なってください。」というメッセージ

**操作**:
- 「Lab-Aidの起動」ボタン -> Lab-Aidの起動
- 「入力完了」ボタン -> `tasks.result_verification`に遷移

**前のstate**: `tasks.analysis`  
**次のstate**: `tasks.result_verification`

---

#### [state] tasks.result_verification

**目的**: 入力されたデータを確認し、自動異常検知の結果を提示する。

**表示内容**:
- valid_holder_display_nameごとタブを作り下記を表示
	- 入力データの一覧表示（読み取り専用）

| 列名                        | 表示名    | 備考                                                      |
| ------------------------- | ------ | ------------------------------------------------------- |
| valid_sample_display_name | サンプル名  | valid_sample_set_codeを保持                                |
| valid_test_display_name   | 試験項目名  | valid_test_display_nameを保持                              |
| test_raw_data             | データ    |                                                         |
| test_unit_name            | 単位     |                                                         |
| -                         | 最上限基準値 | test_upper_limit_spec_1~4で一番値が小さいもの                     |
| -                         | 最下限基準値 | test_lower_limit_spec_1~4で一番値が大きいもの                     |
| test_judgment             | 異常フラグ  | NN以外ならそのまま表示、NNなら計算結果を表示(`trend_enabled` = trueのものだけ計算) |
| -                         | トレンド   | トレンド表示ボタン                                               |

	- 自動異常検知の結果（business-logic.md の判定ロジックに基づく色分け表示）
	- 異常フラグが立った項目のハイライト
- チェックボックスの確認項目

**データソース**
- ファイル: `bunseki.csv`
- 分析結果として使用するデータの取得条件( OR )
	- `bunseki.csv::holder_group_code` = `[state]tasks.task_setup` で選択した `holder_group_code`
	- `job_number` で選択したJOB番号リストのいずれかに一致（OR検索）
	- 重複なし
- 計算に使用するデータの取得条件( AND )
	- `[state]tasks.task_setup`で保持した `holder_group_code` = `bunseki.csv::holder_group_code`
	- `trend_enabled` = true
	- `[state]tasks.analysis_targets`で保持した `valid_sample_set_code` = `bunseki.csv::valid_sample_set_code`
	- `sample_sampling_date`が分析対象のデータから過去5年分
	- `test_raw_data`の文字列を削除して数字のみ残したものを使用する
- グラフに使用するデータの取得条件(AND)
	- `[state]tasks.task_setup`で保持した `holder_group_code` = `bunseki.csv::holder_group_code`
	- `[state]tasks.analysis_targets`で保持した `valid_sample_set_code` = `bunseki.csv::valid_sample_set_code`
	- `sample_sampling_date`が分析対象のデータから過去5年分
	- `test_raw_data`の文字列を削除して数字のみ残したものを使用する

**操作**:
- トレンドグラフボタン -> ポップアップダイアログで表示
- 「回覧へ」ボタン → 確認項目にチェックがついているか確認し、`tasks.submission` へ遷移

**前のstate**: `tasks.result_entry`  
**次のstate**: `tasks.submission`（確認完了時）/ `tasks.result_entry`（修正時）

---

#### [state] tasks.submission

**目的**: 分析結果を添付ファイルとともに確認者へ回覧する。確認者は次の確認者へ回覧するか、タスクを終了させる。

**表示内容**:
- 添付ファイルフィールド
- 回覧フロー(分析者 -> 確認者は確定で、確認者の人数は可変)
- コメント記入欄

**操作**:

ロール：起票者
- 「回覧送信」ボタン → 確認者に通知し、自分の操作は完了

ロール：確認者
- 「次へ回覧」ボタン → 次の確認者を選択して回覧
- 「終了」ボタン → `tasks.completed` へ遷移

**補足:**
- SMTPなどの直接送信は前提にしない（Outlook起動/メール作成）

**前のstate**: `tasks.result_verification`  
**次のstate**: `tasks.completed`（終了時）

---

#### [state] tasks.completed

**目的**: タスクが正式に完了したことを表示する。

**表示内容**:
- 完了メッセージ
- タスクのサマリー情報（完了日時・担当者・分析項目数など）

**操作**:
- 「タスク一覧に戻る」ボタン → tasks へ遷移

**前のstate**: `tasks.submission`  
**次のstate**: なし

---

### [page] data

**目的**: 過去の分析データを一覧で確認・検索する。

**表示内容**:
- ※ [TODO] 表示する列・検索条件・ソート条件を記載する

**操作**:
- ※ [TODO]

---

### [page] news

**目的**: 業務に関連する連絡事項を投稿・閲覧する。

**表示内容**:
- ※ [TODO] 投稿一覧の表示形式・投稿フォームの項目を記載する

**操作**:
- ※ [TODO]

---

### [page] library

**目的**: 回覧時に添付された資料を一覧で管理・閲覧する。

**表示内容**:
- ※ [TODO]

**操作**:
- ※ [TODO]

---

### [page] log

**目的**: 分析装置や試薬の使用ログを記録・確認する。

**表示内容**:
- ※ [TODO] ログの種類（装置ログ / 試薬ログ）と表示項目を記載する

**操作**:
- ※ [TODO]

---

### [page] job

**目的**: 分析に必要なJOB番号を設定・管理する。

**表示内容**:
- ※ [TODO]

**操作**:
- ※ [TODO]

---

### [page] settings

**目的**: アプリの動作設定を編集・保存する。

**表示内容**:
- settings.json の編集フォーム（項目は data-spec.md 参照）
- users.json の編集テーブル（ユーザー追加・削除・編集）

**操作**:
- 各項目を編集して「保存」ボタン → ファイルに書き込む
- 「キャンセル」ボタン → 変更を破棄して元の値に戻す

---

### [dialog] logon

**目的**: アプリ起動時にユーザーを識別してログオンする。

**表示内容**:
- ユーザー選択（users.json から読み込んだユーザー一覧）
- パスワード入力欄 ※[TODO] 認証方式を確認（パスワード / PIN / 選択のみ）

**操作**:
- 「ログオン」ボタン → 認証成功時にメインウィンドウを表示する
- 認証失敗時 → エラーメッセージを表示して再入力を促す
- キャンセル / 閉じる → アプリを終了する

---

### [dialog] setup

**目的**: ユーザー固有のデータパス（SharePointフォルダのローカル同期先）を設定する。

**表示内容**:
- SharePointルートパスの入力欄（フォルダ選択ダイアログ付き）
- 出力先フォルダの入力欄（フォルダ選択ダイアログ付き）

**操作**:
- フォルダ選択ボタン → OS標準のフォルダ選択ダイアログを開く
- 「保存」ボタン → settings.json に書き込み、ダイアログを閉じる
- 「キャンセル」ボタン → 変更を破棄してダイアログを閉じる（初回時はアプリ終了）

---

## 4. 共通UI仕様

### サイドバー
- kind=page の画面のみ表示する（state・dialog は表示しない）
- 現在表示中の page をハイライト表示する
- アイコン + テキストで各ページを表示する

### ステータスバー（メインウィンドウ下部）
- 現在の処理状態を表示する（例：「読み込み中...」「準備完了」）
- 右端にログオン中のユーザー名を表示する

### エラーダイアログ
- 予期しないエラーは `QMessageBox.critical` でスタックトレース付きで表示する
- エラーログは `{app_data}/bunseki/logs/app.log` に記録する
#### エラー・例外
- SharePointフォルダが見つからない場合：赤いバナーで警告を表示する
	- 警告の中にデータルートをセットアップするボタンを設置し、クリックしたら`setup`ダイアログに遷移して、セットアップが終了したらデータの再読み込みをする。
- エラー: 赤いバナーで警告を表示する
	- エラー内容と管理者へ連絡することを記載し、エラーログのダウンロードボタンを表示