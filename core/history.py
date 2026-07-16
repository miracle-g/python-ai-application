"""生成履歴のローカル保存（JSONL）。

個人利用前提なのでDBは使わず、追記のみのJSONLで扱う。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime

from config import HISTORY_FILE, HISTORY_LIMIT


@dataclass
class HistoryEntry:
    created_at: str
    tool: str
    title: str
    model: str
    output: str


def save(tool: str, title: str, model: str, output: str) -> None:
    """1件追記する。失敗しても生成結果は画面に出ているので握りつぶす。"""
    entry = HistoryEntry(
        created_at=datetime.now().isoformat(timespec="seconds"),
        tool=tool,
        title=title.strip()[:80] or "(無題)",
        model=model,
        output=output,
    )
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with HISTORY_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
    except OSError:
        pass


def load_all() -> list[HistoryEntry]:
    """新しい順に返す。"""
    if not HISTORY_FILE.exists():
        return []

    entries: list[HistoryEntry] = []
    with HISTORY_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(HistoryEntry(**json.loads(line)))
            except (json.JSONDecodeError, TypeError):
                continue  # 壊れた行は無視する
    return list(reversed(entries))[:HISTORY_LIMIT]


def clear() -> None:
    HISTORY_FILE.unlink(missing_ok=True)
