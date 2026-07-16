"""文章要約ページ。"""

from __future__ import annotations

import streamlit as st

from core.prompts import SUMMARY_FORMATS, SUMMARY_SYSTEM, summary_prompt
from core.ui import Settings, generate_and_render, render_sidebar, require_input, setup_page

setup_page("文章要約", "📝")
settings: Settings = render_sidebar()

st.caption("長文・議事録・記事を、目的に合った形式に圧縮します。")

with st.form("summary"):
    source = st.text_area(
        "要約したい文章 **必須**",
        height=300,
        placeholder="記事、議事録、メールスレッド、資料の文字起こしなどを貼り付けてください。",
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        fmt = st.radio("出力形式", list(SUMMARY_FORMATS.keys()), horizontal=False)
    with col2:
        st.markdown("**この形式の中身**")
        st.info(SUMMARY_FORMATS[fmt], icon="ℹ️")

    extra = st.text_area(
        "補足指示（任意）",
        placeholder="例: 数値と固有名詞は必ず残して / 決定事項だけに絞って",
        height=80,
    )

    submitted = st.form_submit_button("要約する", type="primary", use_container_width=True)

if source.strip():
    st.caption(f"入力: {len(source)} 文字")

if submitted and not require_input(source, "要約したい文章"):
    submitted = False

generate_and_render(
    tool="文章要約",
    title=f"{fmt}_{source[:20]}",
    system_instruction=SUMMARY_SYSTEM,
    prompt=summary_prompt(source, fmt=fmt, extra=extra) if submitted else "",
    settings=settings,
    submitted=submitted,
)
