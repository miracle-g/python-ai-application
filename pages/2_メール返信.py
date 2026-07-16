"""メール返信ページ。"""

from __future__ import annotations

import streamlit as st

from core.prompts import MAIL_SYSTEM, mail_prompt
from core.ui import Settings, generate_and_render, render_sidebar, require_input, setup_page

setup_page("メール返信", "📧")
settings: Settings = render_sidebar()

st.caption("受信メールを貼り付けて返信の方針を書くだけ。関係性に合った敬語で返信文を組み立てます。")

RELATIONSHIPS = [
    "社外の取引先（初めてのやり取り）",
    "社外の取引先（継続的な関係）",
    "顧客・お客様",
    "社内の上司",
    "社内の同僚・部下",
    "採用担当者 / 応募者",
    "友人・知人（カジュアル）",
]

MAIL_TONES = [
    "丁寧・標準的なビジネス文体",
    "かしこまった・格式高い",
    "簡潔・用件のみ",
    "柔らかく親しみのある",
    "毅然と・きっぱり断る",
]

INTENT_PRESETS = {
    "自由入力": "",
    "承諾する": "依頼を承諾する。日程や条件に合意し、次のアクションを明確にする。",
    "丁重に断る": "依頼を断る。理由を簡潔に述べ、相手の気分を害さないよう配慮し、代替案があれば添える。",
    "日程を調整する": "日程調整に応じる。こちらの候補日を複数提示し、相手に選んでもらう。",
    "お礼を伝える": "感謝を伝える。何に対する感謝かを具体的に書く。",
    "質問・確認する": "不明点を質問する。何が分からないかを箇条書きで明確にする。",
    "お詫びする": "こちらの非をお詫びする。言い訳をせず、原因と再発防止策を簡潔に述べる。",
    "検討中と伝える": "即答を避け、社内で検討する旨と回答予定時期を伝える。",
}

with st.form("mail"):
    received = st.text_area(
        "受信したメール **必須**",
        height=220,
        placeholder="返信したいメールの本文をそのまま貼り付けてください。",
    )

    preset = st.selectbox("返信の方針（プリセット）", list(INTENT_PRESETS.keys()))
    intent = st.text_area(
        "返信で伝えたいこと **必須**",
        value=INTENT_PRESETS[preset],
        height=100,
        placeholder="例: 提案は魅力的だが、今期は予算がないので見送りたい。来期の再提案は歓迎したい。",
        help="プリセットを選ぶと下書きが入ります。自分の状況に合わせて書き換えてください。",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        relationship = st.selectbox("相手との関係", RELATIONSHIPS)
    with col2:
        tone = st.selectbox("トーン", MAIL_TONES)
    with col3:
        my_name = st.text_input("自分の名前・所属", placeholder="例: 株式会社〇〇 山田太郎")

    extra = st.text_area(
        "補足情報（任意）",
        placeholder="例: 添付資料のURLを載せたい / 来週は出張で不在",
        height=80,
    )

    submitted = st.form_submit_button("返信文を作成する", type="primary", use_container_width=True)

if submitted:
    if not require_input(received, "受信したメール") or not require_input(intent, "返信で伝えたいこと"):
        submitted = False

generate_and_render(
    tool="メール返信",
    title=intent[:40] if intent else "メール返信",
    system_instruction=MAIL_SYSTEM,
    prompt=mail_prompt(
        received,
        intent=intent,
        relationship=relationship,
        tone=tone,
        my_name=my_name,
        extra=extra,
    )
    if submitted
    else "",
    settings=settings,
    submitted=submitted,
    file_ext="txt",
)
