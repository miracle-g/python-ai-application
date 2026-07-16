"""Gemini API の薄いラッパー。

APIキーの解決とストリーミング生成だけを担当し、UIのことは知らない。
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


class GeminiError(RuntimeError):
    """APIキー未設定や生成失敗をUIに見せるための例外。"""


def resolve_api_key() -> str | None:
    """セッション入力 → 環境変数 → secrets.toml の順にAPIキーを探す。"""
    key = st.session_state.get("api_key")
    if key:
        return key.strip()

    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if key:
        return key.strip()

    try:
        return str(st.secrets["GEMINI_API_KEY"]).strip()
    except Exception:
        # secrets.toml が無い場合、st.secrets へのアクセス自体が例外になる
        return None


@st.cache_resource(show_spinner=False)
def _get_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def _build_config(
    system_instruction: str | None,
    temperature: float,
) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
    )


def generate_stream(
    prompt: str,
    *,
    system_instruction: str | None = None,
    model: str,
    temperature: float,
) -> Iterator[str]:
    """生成結果をチャンク単位で返す。st.write_stream にそのまま渡せる。"""
    api_key = resolve_api_key()
    if not api_key:
        raise GeminiError(
            "APIキーが設定されていません。サイドバーから入力するか、"
            "`.env` に GEMINI_API_KEY を設定してください。"
        )

    client = _get_client(api_key)
    try:
        stream = client.models.generate_content_stream(
            model=model,
            contents=prompt,
            config=_build_config(system_instruction, temperature),
        )
        for chunk in stream:
            if chunk.text:
                yield chunk.text
    except GeminiError:
        raise
    except Exception as exc:  # SDK の例外階層に依存せずUIへ橋渡しする
        raise GeminiError(f"生成に失敗しました: {exc}") from exc


def generate(
    prompt: str,
    *,
    system_instruction: str | None = None,
    model: str,
    temperature: float,
) -> str:
    """ストリーミングせずに全文をまとめて取得する。"""
    return "".join(
        generate_stream(
            prompt,
            system_instruction=system_instruction,
            model=model,
            temperature=temperature,
        )
    )
