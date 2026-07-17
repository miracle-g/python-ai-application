"""簡易パスワード認証。

認証もDBも持たない個人用アプリを Streamlit Community Cloud のような公開環境に
出すと、URLを知る第三者に API キーを使われてしまう。それを防ぐための最小限のゲート。

パスワードが設定されているときだけ有効になる:
`st.secrets["app_password"]` → 環境変数 `APP_PASSWORD` の順に探し、
どちらも無ければ素通しする（.env でローカル利用する手元では認証を求めない）。
"""

from __future__ import annotations

import hmac
import os

import streamlit as st


def _configured_password() -> str | None:
    """設定されたログインパスワードを返す。未設定なら None。"""
    try:
        secret = st.secrets.get("app_password")
    except Exception:
        # secrets.toml が無いと st.secrets へのアクセス自体が例外を投げる
        secret = None
    if secret:
        return str(secret)
    return os.environ.get("APP_PASSWORD") or None


def require_auth() -> None:
    """パスワードが設定されていれば認証ゲートを表示し、未認証なら以降を止める。

    全ページの先頭（`set_page_config` の直後）で呼ぶこと。
    パスワード未設定のローカル環境では何もしない。
    """
    password = _configured_password()
    if not password:
        return

    if st.session_state.get("authenticated"):
        return

    st.title("🔒 ログイン")
    st.caption("このアプリはパスワードで保護されています。")
    entered = st.text_input("パスワード", type="password", key="_auth_input")
    if entered:
        if hmac.compare_digest(entered, password):
            st.session_state["authenticated"] = True
            st.session_state.pop("_auth_input", None)
            st.rerun()
        else:
            st.error("パスワードが違います。", icon="🚫")
    st.stop()
