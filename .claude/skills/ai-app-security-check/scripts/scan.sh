#!/usr/bin/env bash
# AI アプリ セキュリティチェック — 機械的な下調べ用スキャナ。
#
# これは grep ベースの「当たり取り」であり、判断はしない。
# ヒット0でも安全の証明にはならず、ヒットありでも脆弱とは限らない。
# 出力を「次に自分の目で見るべき場所のリスト」として使うこと。
#
# 使い方:  bash scan.sh <対象アプリのルート>   （省略時はカレント）

set -uo pipefail
ROOT="${1:-.}"
cd "$ROOT" || { echo "対象ディレクトリが見つかりません: $ROOT" >&2; exit 1; }

# 検索から除外する重い/無関係なディレクトリ
EXCL=(--exclude-dir='.venv' --exclude-dir='.git' --exclude-dir='__pycache__' --exclude-dir='node_modules' --exclude-dir='.agents' --exclude-dir='.claude')
PY=(--include='*.py')

section() { printf '\n========== %s ==========\n' "$1"; }
note()    { printf '  %s\n' "$1"; }

echo "対象: $(pwd)"

section "1. ハードコードされた秘密情報らしき文字列"
# Google(旧AIza / 新AQ.), OpenAI(sk-), Anthropic(sk-ant-), GitHub(ghp_/gho_ 等), Slack(xox...) を対象
grep -rnoE 'AIza[0-9A-Za-z_-]{20,}|AQ\.[0-9A-Za-z._-]{20,}|sk-ant-[0-9A-Za-z-]{20,}|sk-[0-9A-Za-z]{20,}|gh[posru]_[0-9A-Za-z]{20,}|xox[baprs]-[0-9A-Za-z-]{10,}' "${EXCL[@]}" "${PY[@]}" . \
  || note "（キーらしきパターンのヒットなし）"
grep -rniE '(api[_-]?key|secret|token|passwd|password)[[:space:]]*=[[:space:]]*["'"'"'][^"'"'"']{8,}' "${EXCL[@]}" "${PY[@]}" . \
  || note "（代入形の秘密情報リテラルのヒットなし）"

section "2. 生HTML描画（XSSの起点になりうる）"
grep -rnE 'unsafe_allow_html[[:space:]]*=[[:space:]]*True|st\.html\(|components\.html' "${EXCL[@]}" "${PY[@]}" . \
  || note "（unsafe_allow_html / st.html のヒットなし）"

section "3. 危険な動的実行・コマンド実行"
grep -rnE '\beval\(|\bexec\(|os\.system\(|subprocess\.|__import__\(|pickle\.load' "${EXCL[@]}" "${PY[@]}" . \
  || note "（eval/exec/subprocess 等のヒットなし）"

section "4. ファイル書き込み・ダウンロード名（パストラバーサル確認用）"
grep -rnE 'file_name[[:space:]]*=|open\([^)]*["'"'"']?[war]|\.write_text|\.write_bytes' "${EXCL[@]}" "${PY[@]}" . \
  || note "（ファイル書き込み系のヒットなし）"

section "5. 例外・トレースのUI露出"
grep -rnE 'st\.exception\(|traceback\.|st\.(error|write)\([^)]*(exc|str\(e\)|\{e\}|\{exc\})' "${EXCL[@]}" "${PY[@]}" . \
  || note "（例外の直接露出らしきヒットなし）"

section "6. .gitignore の状態"
if [ -f .gitignore ]; then
  for pat in '.env' 'secrets.toml' '__pycache__' 'data/'; do
    if grep -qE "(^|/)${pat//./\\.}" .gitignore; then
      note "OK   : '$pat' は .gitignore にある"
    else
      note "要確認: '$pat' が .gitignore に見当たらない"
    fi
  done
else
  note "要確認: .gitignore が存在しない"
fi
# サンプル用 env ファイルに実キーが残っていないか。
# 特定のキー形式に頼らず「プレースホルダに見えない長い値」を疑う
# （AQ. のような新形式キーもパターン非依存で拾える）。
found_env_example=0
for envf in .env.example .env.sample .env.template env.example .env.dist; do
  [ -f "$envf" ] || continue
  found_env_example=1
  flagged=0
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in \#*|'') continue;; esac
    [ "${line#*=}" = "$line" ] && continue   # KEY=VALUE 形式でない行は無視
    key="${line%%=*}"
    val="${line#*=}"
    # 前後の空白と引用符を除去
    val="$(printf '%s' "$val" | sed -E 's/^[[:space:]]*["'"'"']?//; s/["'"'"']?[[:space:]]*$//')"
    [ -z "$val" ] && continue
    # プレースホルダらしき語を含むなら安全とみなす
    printf '%s' "$val" | grep -qiE 'your|xxx+|change[_-]?me|placeholder|dummy|sample|example|here|\.\.\.|^<.*>$' && continue
    # 引用符・空白・パスを含まない16文字以上の英数字トークン = 実キーの疑い
    if printf '%s' "$val" | grep -qE '^[A-Za-z0-9._-]{16,}$'; then
      note "要確認(重大): $envf の $key に実キーらしき値（${#val}文字）。プレースホルダに置換し失効させること"
      flagged=1
    fi
  done < "$envf"
  [ "$flagged" -eq 0 ] && note "OK   : $envf に実キーらしき値は見当たらない"
  # サンプルファイル自身が .gitignore で無視されていないか（無視されると見本にならない）。
  # git があれば否定パターン(!...)込みで正確に判定する。単純 grep だと "!$envf" を
  # 「無視されている」と誤判定するため使わない。
  if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git check-ignore -q "$envf" 2>/dev/null \
      && note "要確認: $envf が .gitignore で無視されている（見本として機能しない）"
  elif [ -f .gitignore ] \
       && grep -qxF "$envf" .gitignore \
       && ! grep -qxF "!$envf" .gitignore; then
    note "要確認: $envf が .gitignore に載っている（見本として機能しない可能性）"
  fi
done
[ "$found_env_example" -eq 0 ] && note "（.env.example 等のサンプル env ファイルなし）"

section "7. git に秘密情報が追跡・コミットされていないか"
if [ -d .git ] && command -v git >/dev/null 2>&1; then
  tracked=$(git ls-files 2>/dev/null | grep -E '(^|/)\.env$|secrets\.toml$' || true)
  [ -n "$tracked" ] && note "要確認(重大): 追跡されている秘密ファイル -> $tracked" \
                     || note "OK   : .env / secrets.toml は追跡されていない"
else
  note "（git リポジトリではない、または git 未導入 — スキップ）"
fi

section "8. Streamlit の公開・CORS・XSRF 設定"
grep -rnE 'server\.address|enableCORS|enableXsrfProtection|0\.0\.0\.0|--server\.' "${EXCL[@]}" \
  --include='*.py' --include='*.sh' --include='*.md' --include='*.toml' --include='*.cfg' . \
  || note "（公開バインド/CORS/XSRF 関連の記述なし）"

section "9. 依存パッケージ"
for f in requirements.txt pyproject.toml Pipfile; do
  [ -f "$f" ] && { note "--- $f ---"; sed 's/^/    /' "$f"; }
done
if command -v pip-audit >/dev/null 2>&1; then
  note "--- pip-audit ---"
  pip-audit -r requirements.txt 2>&1 | sed 's/^/    /' || true
else
  note "pip-audit 未導入（既知CVEの自動確認はスキップ。レポートには『未実施』と記す）"
fi

printf '\n下調べ完了。ヒット箇所を checklist.md の基準で一件ずつ判断すること。\n'
