"""全ページで共有するUI部品。

各ページは「入力フォームを作る」ことに集中し、
モデル設定・生成・結果表示・履歴保存はここに任せる。
"""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from config import APP_ICON, APP_NAME, AVAILABLE_MODELS, DEFAULT_MODEL, DEFAULT_TEMPERATURE
from core import history
from core.auth import require_auth
from core.gemini_client import GeminiError, generate_stream, resolve_api_key

CUSTOM_MODEL_LABEL = "その他（手入力）"

TONES = [
    "です・ます調（丁寧）",
    "だ・である調（硬め）",
    "カジュアル・親しみやすい",
    "フォーマル・ビジネス",
    "熱量高め・エモーショナル",
    "客観的・ニュートラル",
]


@dataclass(frozen=True)
class Settings:
    model: str
    temperature: float


def setup_page(title: str, icon: str) -> None:
    st.set_page_config(page_title=f"{title} | {APP_NAME}", page_icon=icon, layout="wide")
    require_auth()  # パスワードが設定されていれば未認証者をここで止める
    st.title(f"{icon} {title}")


def render_sidebar() -> Settings:
    """APIキー・モデル・温度の設定UI。全ページのサイドバーに出す。"""
    with st.sidebar:
        st.header("⚙️ 設定")

        if resolve_api_key():
            st.success("APIキー: 設定済み", icon="✅")
        else:
            st.warning("APIキーが未設定です", icon="⚠️")
        st.text_input(
            "Gemini API キー",
            type="password",
            key="api_key",
            help="`.env` に GEMINI_API_KEY を設定していれば入力不要です。"
            "ここでの入力はこのセッション内のみ保持されます。",
            placeholder="AIza...",
        )

        choice = st.selectbox(
            "モデル",
            [*AVAILABLE_MODELS, CUSTOM_MODEL_LABEL],
            index=AVAILABLE_MODELS.index(DEFAULT_MODEL) if DEFAULT_MODEL in AVAILABLE_MODELS else 0,
            help="Flash は速く安価、Pro は高品質。",
        )
        if choice == CUSTOM_MODEL_LABEL:
            model = st.text_input(
                "モデルID",
                value=DEFAULT_MODEL,
                help="新しいモデルが出た場合はここに直接IDを入力できます。",
            ).strip() or DEFAULT_MODEL
        else:
            model = choice

        temperature = st.slider(
            "創造性（temperature）",
            min_value=0.0,
            max_value=2.0,
            value=DEFAULT_TEMPERATURE,
            step=0.1,
            help="低いほど堅実で再現性が高く、高いほど多様な表現になります。",
        )

        st.divider()
        st.caption(f"{APP_ICON} {APP_NAME}")

    return Settings(model=model, temperature=temperature)


def _output_key(tool: str) -> str:
    return f"output::{tool}"


def generate_and_render(
    *,
    tool: str,
    title: str,
    system_instruction: str,
    prompt: str,
    settings: Settings,
    submitted: bool,
    file_ext: str = "md",
) -> None:
    """生成の実行・ストリーミング表示・履歴保存・ダウンロードまでを一括で行う。

    submitted が False の場合は、直前の生成結果があればそれを再表示する。
    """
    key = _output_key(tool)

    if submitted:
        st.subheader("生成結果")
        try:
            stream = generate_stream(
                prompt,
                system_instruction=system_instruction,
                model=settings.model,
                temperature=settings.temperature,
            )
            with st.spinner("生成中...", show_time=True):
                output = st.write_stream(stream)
        except GeminiError as exc:
            st.error(str(exc), icon="🚫")
            return

        if not output:
            st.warning("結果が空でした。入力内容を変えて再試行してください。", icon="⚠️")
            return

        st.session_state[key] = output
        history.save(tool=tool, title=title, model=settings.model, output=output)

    elif key in st.session_state:
        st.subheader("生成結果")
        st.markdown(st.session_state[key])

    output = st.session_state.get(key)
    if not output:
        return

    st.divider()
    left, right = st.columns([1, 3])
    with left:
        st.download_button(
            "⬇️ ダウンロード",
            data=output,
            file_name=f"{_safe_filename(title) or tool}.{file_ext}",
            mime="text/markdown" if file_ext == "md" else "text/plain",
            use_container_width=True,
        )
    with right:
        st.caption(f"{len(output)} 文字 / モデル: {settings.model}")

    with st.expander("📋 コピー用のプレーンテキスト"):
        st.code(output, language=None)


def _safe_filename(title: str) -> str:
    keep = [c for c in title.strip()[:40] if c.isalnum() or c in " -_ぁ-んァ-ン一-龥"]
    return "".join(keep).strip().replace(" ", "_")


def require_input(value: str, label: str) -> bool:
    """必須入力のチェック。空ならエラーを出して False を返す。"""
    if not value.strip():
        st.error(f"「{label}」を入力してください。", icon="✍️")
        return False
    return True
