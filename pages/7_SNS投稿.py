"""SNS投稿ページ。"""

from __future__ import annotations

import streamlit as st

from core.prompts import SNS_PLATFORMS, SNS_SYSTEM, sns_prompt
from core.ui import TONES, Settings, generate_and_render, render_sidebar, require_input, setup_page

setup_page("SNS投稿", "📱")
settings: Settings = render_sidebar()

st.caption("ブログ記事や伝えたい内容から、各SNSの作法に合わせた投稿文に変換します。")

with st.form("sns"):
    source = st.text_area(
        "元にする内容 **必須**",
        height=240,
        placeholder="ブログ記事の本文、告知したいこと、伝えたいメッセージなどを貼り付けてください。",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        platform = st.selectbox("プラットフォーム", list(SNS_PLATFORMS.keys()))
    with col2:
        tone = st.selectbox("トーン", TONES)
    with col3:
        count = st.number_input("案の数", min_value=1, max_value=5, value=3)

    st.caption(SNS_PLATFORMS[platform])

    extra = st.text_area(
        "補足指示（任意）",
        placeholder="例: 記事URLを末尾に置く前提で / 絵文字は使わない",
        height=80,
    )

    submitted = st.form_submit_button("投稿文を作る", type="primary", use_container_width=True)

if submitted and not require_input(source, "元にする内容"):
    submitted = False

generate_and_render(
    tool="SNS投稿",
    title=f"{platform}_{source[:20]}",
    system_instruction=SNS_SYSTEM,
    prompt=sns_prompt(source, platform=platform, tone=tone, count=int(count), extra=extra)
    if submitted
    else "",
    settings=settings,
    submitted=submitted,
)
