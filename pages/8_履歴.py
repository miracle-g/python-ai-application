"""生成履歴ページ。"""

from __future__ import annotations

import streamlit as st

from config import HISTORY_FILE
from core import history
from core.ui import render_sidebar, setup_page

setup_page("履歴", "🕘")
render_sidebar()

st.caption(f"過去の生成結果を新しい順に表示します。保存先: `{HISTORY_FILE}`")

entries = history.load_all()

if not entries:
    st.info("まだ履歴がありません。各ツールで文章を生成すると、ここに自動保存されます。", icon="📭")
    st.stop()

tools = sorted({e.tool for e in entries})
col1, col2 = st.columns([2, 1])
with col1:
    selected = st.multiselect("ツールで絞り込む", tools, default=tools)
with col2:
    query = st.text_input("キーワード検索", placeholder="本文・タイトルから探す")

filtered = [
    e
    for e in entries
    if e.tool in selected and (not query or query.lower() in (e.title + e.output).lower())
]

st.write(f"**{len(filtered)}** 件 / 全 {len(entries)} 件")

for i, entry in enumerate(filtered):
    with st.expander(f"**{entry.tool}** — {entry.title}　　`{entry.created_at}`"):
        st.markdown(entry.output)
        st.divider()
        st.caption(f"モデル: {entry.model} / {len(entry.output)} 文字")
        st.download_button(
            "⬇️ ダウンロード",
            data=entry.output,
            file_name=f"{entry.created_at}_{entry.tool}.md",
            mime="text/markdown",
            key=f"dl_{i}",
        )

st.divider()
with st.expander("⚠️ 履歴の削除"):
    st.write("履歴ファイルを完全に削除します。この操作は取り消せません。")
    if st.checkbox("削除することを理解しました"):
        if st.button("すべての履歴を削除する", type="primary"):
            history.clear()
            st.success("履歴を削除しました。")
            st.rerun()
