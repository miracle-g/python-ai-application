"""アプリ全体の設定値。

モデル名は Gemini API の更新に追従して変わることがあるため、
ここだけを書き換えれば全ページに反映されるようにしている。
"""

from __future__ import annotations

from pathlib import Path

APP_NAME = "AI ライティングスタジオ"
APP_ICON = "🖋️"

# 選択肢としてUIに出すモデル。実際に利用可能なIDは
# https://ai.google.dev/gemini-api/docs/models で確認できる。
# 2.5系は新規ユーザーには提供終了しており、404になるため載せない。
AVAILABLE_MODELS: list[str] = [
    "gemini-3.5-flash",
    "gemini-3.1-pro-preview",
    "gemini-3.1-flash-lite",
]
DEFAULT_MODEL = "gemini-3.5-flash"

DEFAULT_TEMPERATURE = 0.7

# 履歴の保存先（ローカルのJSONL。個人利用前提でDBは使わない）
DATA_DIR = Path(__file__).parent / "data"
HISTORY_FILE = DATA_DIR / "history.jsonl"
HISTORY_LIMIT = 200
