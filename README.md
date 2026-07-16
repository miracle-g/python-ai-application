# 🖋️ AI ライティングスタジオ

ブログ執筆・メール返信・要約などのライティング作業を1つにまとめた、個人用のAIツールです。
Python + Streamlit + Gemini API で動きます。データベースも認証もありません。

## 機能

| ページ | できること |
|---|---|
| ✍️ ブログ記事執筆 | テーマ・読者・文字数・SEOキーワードから、見出し構成つきの記事をMarkdownで生成 |
| 📧 メール返信 | 受信メールと返信方針から、相手との関係性に合った敬語で返信文を作成 |
| 📝 文章要約 | 3行 / 箇条書き / エグゼクティブサマリー / 議事録 / 一文 の5形式で要約 |
| 🔍 校正・推敲 | 誤字脱字・表記ゆれ・冗長表現を指摘し、修正後の全文と指摘一覧を返す |
| 🔄 リライト | 短く / 詳しく / やさしく / 説得力高く、狙いとトーンを指定して書き換え |
| 💡 アイデア出し | タイトル案・キャッチコピー・構成案・ネタ出しを切り口を変えて量産 |
| 📱 SNS投稿 | 元ネタを X / LinkedIn / Instagram / note などの作法に合わせて変換 |
| 🕘 履歴 | 過去の生成結果を検索・再利用・ダウンロード |

## セットアップ

### 1. APIキーを取得

[Google AI Studio](https://aistudio.google.com/apikey) で無料のAPIキーを発行します。

### 2. 依存関係をインストール

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. APIキーを設定

```bash
cp .env.example .env
# .env を開いて GEMINI_API_KEY=... を自分のキーに書き換える
```

`.env` を使わずに、アプリ起動後サイドバーから直接入力することもできます
（その場合キーはセッション内のみ保持され、保存されません）。

### 4. 起動

```bash
streamlit run app.py
```

ブラウザで http://localhost:8501 が開きます。

## 設定

`config.py` を編集すると全ページに反映されます。

- `AVAILABLE_MODELS` — サイドバーのモデル選択肢
- `DEFAULT_MODEL` — 初期選択のモデル
- `DEFAULT_TEMPERATURE` — 創造性の初期値
- `HISTORY_LIMIT` — 履歴ページに表示する最大件数

> **モデル名について**
> Gemini のモデルIDは随時追加・廃止されます。選択肢のモデルでエラーが出る場合は、
> [公式のモデル一覧](https://ai.google.dev/gemini-api/docs/models) で現行のIDを確認し、
> `config.py` の `AVAILABLE_MODELS` を書き換えてください。
> サイドバーの「その他（手入力）」から一時的に別のIDを試すこともできます。

## プロンプトの調整

生成される文章の質を変えたいときは `core/prompts.py` を編集します。
各ツールの「システム指示」と「プロンプト組み立て」がすべてこのファイルに集約されています。
全ツール共通のルール（前置きを書かない、事実を捏造しない等）は `BASE_RULE` にあります。

## 構成

```
app.py                  ホーム画面
config.py               設定値（モデル名・既定値・保存先）
core/
  gemini_client.py      Gemini APIラッパー（キー解決 + ストリーミング生成）
  prompts.py            全ツールのプロンプト定義
  ui.py                 共通UI（サイドバー・生成実行・結果表示・DL）
  history.py            履歴のJSONL保存
pages/                  各機能のページ（入力フォームの定義に専念）
data/history.jsonl      生成履歴（自動生成 / gitignore済み）
```

新しいツールを追加したい場合は、`core/prompts.py` にプロンプトを足し、
`pages/` にフォームだけのページを1枚作れば済みます。生成・表示・履歴保存は
`core/ui.py` の `generate_and_render()` が引き受けます。

## メモ

- 生成結果に `[要確認]` が出たら、AIが事実を知らない箇所です。自分で埋めてください。
- 履歴は `data/history.jsonl` にローカル保存されます。`.gitignore` 済みです。
- 校正ページは temperature を 0.3 以下に、アイデア出しは 1.0 以上に自動調整します
  （用途に対して極端な設定を防ぐため）。
