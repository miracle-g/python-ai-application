"""ブログ記事執筆ページ。"""

from __future__ import annotations

import streamlit as st

from core.prompts import BLOG_SYSTEM, blog_prompt
from core.ui import TONES, Settings, generate_and_render, render_sidebar, require_input, setup_page

setup_page("ブログ記事執筆", "✍️")
settings: Settings = render_sidebar()

st.caption("テーマと条件を渡すと、見出し構成の整った記事をMarkdownで書き起こします。")

with st.form("blog"):
    topic = st.text_input(
        "テーマ / 記事で伝えたいこと **必須**",
        placeholder="例: 在宅ワークで集中力を保つための時間管理術",
    )

    col1, col2 = st.columns(2)
    with col1:
        audience = st.text_input("想定読者", placeholder="例: リモートワーク歴1年未満の会社員")
        tone = st.selectbox("文体・トーン", TONES)
    with col2:
        length = st.select_slider(
            "目安の文字数",
            options=[800, 1200, 1600, 2000, 3000, 4000, 5000],
            value=2000,
        )
        keywords = st.text_input("SEOキーワード（カンマ区切り）", placeholder="例: 在宅ワーク, 集中力, ポモドーロ")

    with st.expander("さらに細かく指定する"):
        outline = st.text_area(
            "希望する構成・見出し案",
            placeholder="例:\n- 導入: 在宅ワークの落とし穴\n- 本論: 時間管理の3つの型\n- まとめ",
            height=120,
        )
        extra = st.text_area(
            "補足情報・追加指示",
            placeholder="例: 自分の体験談を交えて、専門用語は使わずに書いてほしい",
            height=100,
        )

    submitted = st.form_submit_button("記事を執筆する", type="primary", use_container_width=True)

if submitted and not require_input(topic, "テーマ"):
    submitted = False

generate_and_render(
    tool="ブログ記事執筆",
    title=topic,
    system_instruction=BLOG_SYSTEM,
    prompt=blog_prompt(
        topic,
        audience=audience,
        tone=tone,
        length=length,
        keywords=keywords,
        outline=outline,
        extra=extra,
    )
    if submitted
    else "",
    settings=settings,
    submitted=submitted,
)
