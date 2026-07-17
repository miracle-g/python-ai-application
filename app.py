"""AI ライティングスタジオ — ホーム画面。

起動:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from config import APP_ICON, APP_NAME
from core.auth import require_auth
from core.gemini_client import resolve_api_key
from core.ui import render_sidebar

st.set_page_config(page_title=APP_NAME, page_icon=APP_ICON, layout="wide")
require_auth()  # パスワードが設定されていれば未認証者をここで止める
render_sidebar()

st.title(f"{APP_ICON} {APP_NAME}")
st.caption("書く・返す・まとめる・磨く。ライティングまわりをまとめた個人用ツールです。")

if not resolve_api_key():
    st.warning(
        "**まずはAPIキーを設定してください。** サイドバーに入力するか、"
        "`.env` ファイルに `GEMINI_API_KEY=...` を書いてください。"
        "キーは [Google AI Studio](https://aistudio.google.com/apikey) で無料で取得できます。",
        icon="🔑",
    )

st.divider()

TOOLS = [
    ("pages/1_ブログ記事執筆.py", "✍️", "ブログ記事執筆", "テーマから見出し構成つきの記事をMarkdownで書き起こします。"),
    ("pages/2_メール返信.py", "📧", "メール返信", "受信メールと方針を渡すと、関係性に合った返信文を作ります。"),
    ("pages/3_文章要約.py", "📝", "文章要約", "3行・議事録・エグゼクティブサマリーなど形式を選んで要約します。"),
    ("pages/4_校正・推敲.py", "🔍", "校正・推敲", "誤字脱字や冗長表現を指摘し、修正後の全文を返します。"),
    ("pages/5_リライト.py", "🔄", "リライト・トーン変換", "短く・詳しく・やさしく。狙いを指定して書き換えます。"),
    ("pages/6_アイデア出し.py", "💡", "タイトル・アイデア出し", "タイトル案、キャッチコピー、構成案を切り口を変えて量産します。"),
    ("pages/7_SNS投稿.py", "📱", "SNS投稿", "元ネタからX・LinkedIn・Instagram向けの投稿文に変換します。"),
    ("pages/8_履歴.py", "🕘", "履歴", "過去の生成結果を見返して再利用します。"),
]

cols = st.columns(2)
for i, (path, icon, name, desc) in enumerate(TOOLS):
    with cols[i % 2]:
        with st.container(border=True):
            st.subheader(f"{icon} {name}")
            st.write(desc)
            st.page_link(path, label=f"{name}を開く", icon="➡️")

st.divider()
with st.expander("💡 使いこなしのヒント"):
    st.markdown(
        """
- **サイドバーの「創造性」** は、堅い文章なら `0.2〜0.5`、アイデア出しなら `1.0〜1.5` が目安です。
- **モデル選択** は Flash が速くて安価、Pro は複雑な構成や長文で品質が出ます。
- 生成結果に `[要確認]` と出たら、AIが事実を知らない箇所です。自分で埋めてください。
- 生成した文章はすべて **履歴** に自動保存されます（ローカルの `data/history.jsonl`）。
        """
    )
