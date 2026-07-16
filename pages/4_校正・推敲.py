"""校正・推敲ページ。"""

from __future__ import annotations

import streamlit as st

from core.prompts import PROOFREAD_SYSTEM, proofread_prompt
from core.ui import Settings, generate_and_render, render_sidebar, require_input, setup_page

setup_page("校正・推敲", "🔍")
settings: Settings = render_sidebar()

st.caption("誤字脱字・表記ゆれ・冗長表現を指摘し、修正後の全文とあわせて返します。")

LEVELS = {
    "誤字脱字のみ": "明らかな誤字・脱字・変換ミス・句読点の誤りだけを直す。表現には手を入れない。",
    "標準（誤字＋文法＋表記ゆれ）": "誤字脱字に加え、文法の誤り、送り仮名や表記のゆれ、係り受けの乱れを直す。",
    "しっかり（＋冗長表現・読みやすさ）": "標準の範囲に加えて、冗長な言い回し、重複表現、二重敬語、回りくどい構文を整理し、読みやすさを上げる。",
}

with st.form("proofread"):
    source = st.text_area(
        "校正したい文章 **必須**",
        height=300,
        placeholder="ブログ記事、メール、資料など、チェックしたい文章を貼り付けてください。",
    )

    level = st.radio("校正レベル", list(LEVELS.keys()), horizontal=True)
    st.caption(LEVELS[level])

    extra = st.text_area(
        "補足指示（任意）",
        placeholder="例: 「ユーザ」ではなく「ユーザー」に統一して / 社名は正式名称で",
        height=80,
    )

    submitted = st.form_submit_button("校正する", type="primary", use_container_width=True)

if source.strip():
    st.caption(f"入力: {len(source)} 文字")

if submitted and not require_input(source, "校正したい文章"):
    submitted = False

# 校正は創作ではないので、ページ内で温度を下げて安定させる
proof_settings = Settings(model=settings.model, temperature=min(settings.temperature, 0.3))

generate_and_render(
    tool="校正・推敲",
    title=source[:30],
    system_instruction=PROOFREAD_SYSTEM,
    prompt=proofread_prompt(source, level=LEVELS[level], extra=extra) if submitted else "",
    settings=proof_settings,
    submitted=submitted,
)
