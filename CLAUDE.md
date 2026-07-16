# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

Gemini API を使った個人用AIライティングツール（Streamlit マルチページアプリ）。
ブログ執筆・メール返信・要約・校正・リライト・アイデア出し・SNS投稿の7ツール＋履歴ページ。
**DBも認証もない**（個人利用前提）。永続化はローカルのJSONL1本のみ。

## コマンド

```bash
# セットアップ（.venv は作成済み）
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 起動
.venv/bin/streamlit run app.py            # http://localhost:8501

# 起動確認だけしたい場合（ブラウザを開かない）
.venv/bin/streamlit run app.py --server.headless true --server.port 8599
curl -s http://localhost:8599/_stcore/health   # "ok" が返れば起動成功（/healthz はHTMLを返すので使わない）
```

APIキーは `.env` の `GEMINI_API_KEY`（`.env.example` をコピー）、
または起動後にサイドバーから入力。**リポジトリにキーは無いので、実APIを叩く検証はできない前提で作業すること。**

## テスト

コミットされたテストスイートは無い。検証には Streamlit の `AppTest` を使う（`streamlit.testing.v1.AppTest`）。
実APIを叩かずに全フローを通せるので、変更時はこれで確認する。

```python
import sys; sys.path.insert(0, str(ROOT))   # pages/ 配下を直接テストする場合に必要
from unittest.mock import patch
import core.ui as ui
from streamlit.testing.v1 import AppTest

# 生成をモックするなら core.ui の名前を差し替える
# （ui.py は `from core.gemini_client import generate_stream` で取り込んでいるため、
#   core.gemini_client 側を patch しても効かない）
with patch.object(ui, "generate_stream", fake_stream):
    at = AppTest.from_file(str(ROOT / "pages/1_ブログ記事執筆.py"), default_timeout=30).run()
    at.text_input[0].set_value("テーマ")
    at.button[0].click().run()
    assert not at.exception
```

ハマりどころ:
- **ウィジェットのインデックスは「本文が先、サイドバーが後」**。`at.text_input[0]` はページ本文の最初の入力で、サイドバーのAPIキー欄は末尾になる。
- `st.form_submit_button` は `at.button` から取る（`at.form_submit_button` は存在しない）。
- テストを走らせると `data/history.jsonl` に実データが書かれる。後片付けすること。

## アーキテクチャ

### ページは「フォームだけ」を書く

各 `pages/*.py` は**入力フォームの定義に専念する**。生成・ストリーミング表示・履歴保存・
ダウンロード・文字数表示はすべて `core/ui.py` の `generate_and_render()` が引き受ける。
ページ側に生成ロジックを書かないこと。

### 新しいツールを追加する手順

1. `core/prompts.py` にシステム指示（`BASE_RULE` を埋め込む）とプロンプト組み立て関数を追加。
2. `pages/N_名前.py` を作る。`setup_page()` → `render_sidebar()` → フォーム → `generate_and_render()` の順。
3. **`app.py` の `TOOLS` 配列に追記する**（下記の理由で必須）。

`pages/` に置いたファイルは Streamlit が自動でサイドバーに出すが、**ホーム画面のカード一覧は
`app.py` の `TOOLS` 配列にハードコードされていて自動同期しない**。壊れ方が2通りあるので注意:

- **ページを追加して `TOOLS` に足し忘れる** → サイドバーには出るがホームに出ない（**エラーにならず気づけない**）
- **ページをリネームして `TOOLS` を直し忘れる** → `st.page_link` が `StreamlitPageNotFoundError` を投げて**ホーム画面全体が落ちる**

ファイル名の規約: 先頭の数字がサイドバーの並び順、数字とアンダースコアを除いた部分がサイドバーの
表示名になる。**ファイル名に絵文字は入れない**（アイコンは `setup_page("名前", "🔍")` の第2引数で渡す）。

### `generate_and_render()` の呼び出し規約（重要）

ページは毎回この関数を呼び、実行するかどうかは `submitted` フラグで制御する。
未送信時にプロンプトを組み立てないよう、呼び出し側は慣習的にこう書く:

```python
prompt=blog_prompt(topic, ...) if submitted else ""
```

`submitted=False` のときは、`st.session_state["output::{tool}"]` に前回の結果があれば再表示する。
これは **`st.download_button` を押すと Streamlit が再実行され、結果が消えてしまうため**の仕組み。
新しいページでもこの `output::{tool}` のキー規約に乗ること。

必須入力のチェックも同じ `submitted` フラグを倒す形で書く（`require_input()` はエラー表示までやる）:

```python
if submitted and not require_input(topic, "テーマ"):
    submitted = False
```

`generate_and_render()` の `tool` 引数は **`output::` のキーと履歴の分類名を兼ねる**ので、
ページ間で重複させないこと。

### レイヤーの責務

- `config.py` — モデル名・既定値・保存先の**唯一の定義場所**。モデルIDを変えるならここだけ。
- `core/gemini_client.py` — APIキー解決とストリーミング生成のみ。**Streamlit UIのことを知らない**（`st.session_state` の読みと `@st.cache_resource` は例外）。SDKの例外はすべて `GeminiError` に包んでUIへ渡す。
- `core/prompts.py` — 全ツールのシステム指示とプロンプト組み立て。**出力品質の調整はこのファイルだけで完結させる**。共通ルール（前置きを書かない／事実を捏造せず `[要確認]` と書く）は `BASE_RULE` にあり、各システム指示がこれを埋め込む。
- `core/ui.py` — サイドバー、生成実行、結果表示、DL。`Settings`（frozen dataclass）でモデルと温度を運ぶ。
- `core/history.py` — JSONL追記。**保存失敗は握りつぶす**（結果は画面に出ているため、履歴のために生成を失敗させない）。壊れた行は読み込み時にスキップ。

### `HistoryEntry` のスキーマ変更は既存履歴を黙って捨てる

`load_all()` は `HistoryEntry(**json.loads(line))` で復元し、`TypeError` を握りつぶしてスキップする。
そのため**フィールドを増減させると、噛み合わない既存行がエラーも警告もなく消える**（検証済み: 未知フィールドを
1つ足した行を混ぜると 2件中1件しか読めない）。フィールドを足すときは:

- 新フィールドには**必ずデフォルト値を付ける**（古い行に無くても復元できるように）
- 未知フィールドを許容したいなら `load_all()` 側で既知キーだけ拾うようにする
- どちらもやらないなら、`data/history.jsonl` が消えても構わないことを確認してから変更する

### APIキーの解決順

`resolve_api_key()`: `st.session_state["api_key"]` → 環境変数 `GEMINI_API_KEY` / `GOOGLE_API_KEY` → `st.secrets`。
`st.secrets` は secrets.toml が無いとアクセス自体が例外を投げるので、必ず try で囲む。

### ページ単位の temperature 上書き

`render_sidebar()` が返す `Settings` をそのまま使わず、用途に合わせて作り直しているページがある。
用途に対して極端な設定になるのを防ぐ意図なので、消さないこと。

- `pages/4_校正・推敲.py` — `min(temperature, 0.3)`（校正は創作ではない）
- `pages/6_アイデア出し.py` — `max(temperature, 1.0)`（発散させたい）

## コーディング規約

- **UIテキスト・プロンプト・コメント・docstring はすべて日本語**。個人用の日本語ライティングツールなので、英語で書かない。コード識別子は英語。
- 全モジュール先頭に `from __future__ import annotations`。型注釈は `str | None` 形式で書く（Python 3.13）。
- プロンプト内の任意項目は `core/prompts.py` の `_section()` を使う。値が空ならセクションごと消えるので、`if` で分岐して文字列連結しない。
- トーンの選択肢は `core/ui.py` の `TONES` を共有する。ページごとに定義し直さない（メールだけは敬語の都合で専用リストを持つ）。

## 注意

- **モデルIDは未検証**。`config.py` の `AVAILABLE_MODELS` は 2026年1月時点の知識で書かれており、実APIで確認が取れていない。エラーが出たら https://ai.google.dev/gemini-api/docs/models で現行IDを確認して `config.py` を直す。サイドバーの「その他（手入力）」で任意IDも試せる。
- SDK は `google-genai` 2.x（`from google import genai` / `client.models.generate_content_stream`）。旧 `google-generativeai` パッケージのAPIとは別物なので混同しないこと。
- `data/` は gitignore 済み。履歴の実データをコミットしない。
