"""タイトル・アイデア出しページ。"""

from __future__ import annotations

import streamlit as st

from core.prompts import IDEA_KINDS, IDEA_SYSTEM, idea_prompt
from core.ui import Settings, generate_and_render, render_sidebar, require_input, setup_page

setup_page("タイトル・アイデア出し", "💡")
settings: Settings = render_sidebar()

st.caption("タイトル案、キャッチコピー、構成案。切り口を変えてまとめて出します。")

with st.form("idea"):
    topic = st.text_input(
        "テーマ **必須**",
        placeholder="例: 副業でWebライターを始める方法",
    )

    col1, col2 = st.columns(2)
    with col1:
        kind = st.selectbox("出したいもの", list(IDEA_KINDS.keys()))
    with col2:
        audience = st.text_input("想定読者", placeholder="例: 本業のある20〜30代")

    st.caption(IDEA_KINDS[kind])

    extra = st.text_area(
        "補足指示（任意）",
        placeholder="例: 数字を入れたタイトルを多めに / 煽り表現は禁止",
        height=80,
    )

    submitted = st.form_submit_button("アイデアを出す", type="primary", use_container_width=True)

if submitted and not require_input(topic, "テーマ"):
    submitted = False

# アイデア出しは発散させたいので、温度の下限を上げる
idea_settings = Settings(model=settings.model, temperature=max(settings.temperature, 1.0))
st.caption(f"※ 発散させるため temperature を {idea_settings.temperature} で実行します。")

generate_and_render(
    tool="アイデア出し",
    title=f"{kind}_{topic}",
    system_instruction=IDEA_SYSTEM,
    prompt=idea_prompt(topic, kind=kind, audience=audience, extra=extra) if submitted else "",
    settings=idea_settings,
    submitted=submitted,
)
