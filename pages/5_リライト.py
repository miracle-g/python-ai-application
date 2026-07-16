"""リライト・トーン変換ページ。"""

from __future__ import annotations

import streamlit as st

from core.prompts import REWRITE_GOALS, REWRITE_SYSTEM, rewrite_prompt
from core.ui import TONES, Settings, generate_and_render, render_sidebar, require_input, setup_page

setup_page("リライト・トーン変換", "🔄")
settings: Settings = render_sidebar()

st.caption("元の情報を保ったまま、短く・詳しく・やさしく・説得力高く、狙いを指定して書き換えます。")

with st.form("rewrite"):
    source = st.text_area(
        "リライトしたい文章 **必須**",
        height=280,
        placeholder="書き換えたい文章を貼り付けてください。",
    )

    col1, col2 = st.columns(2)
    with col1:
        goal = st.selectbox("狙い", list(REWRITE_GOALS.keys()))
        st.caption(REWRITE_GOALS[goal])
    with col2:
        tone = st.selectbox("トーン", TONES)

    extra = st.text_area(
        "補足指示（任意）",
        placeholder="例: 一文は40字以内に / 「〜させていただく」は使わない",
        height=80,
    )

    submitted = st.form_submit_button("リライトする", type="primary", use_container_width=True)

if source.strip():
    st.caption(f"入力: {len(source)} 文字")

if submitted and not require_input(source, "リライトしたい文章"):
    submitted = False

generate_and_render(
    tool="リライト",
    title=f"{goal}_{source[:20]}",
    system_instruction=REWRITE_SYSTEM,
    prompt=rewrite_prompt(source, goal=goal, tone=tone, extra=extra) if submitted else "",
    settings=settings,
    submitted=submitted,
)
