# 点検チェックリスト（カテゴリ別）

小規模 Streamlit / LLM 個人・社内アプリ向け。各カテゴリは「見る場所」「grep の当たり」
「危険な形 / 安全な形」「修正パターン」で構成する。**該当しない項目は無理に埋めない。**

## 目次

1. 秘密情報・認証情報（最優先）
2. 出力レンダリングと XSS
3. 入力とインジェクション
4. ファイル・データの取り扱い
5. 依存パッケージの脆弱性
6. Streamlit のデプロイ・設定
7. エラー処理と情報漏洩

---

## 1. 秘密情報・認証情報（APIキー）

この種のアプリで最も事故が多い領域。**キーが git に入る / ログに出る / 履歴に混ざる**の3経路を潰す。

**見る場所**: `.env`, `.env.example`, `.gitignore`, `st.secrets` / `secrets.toml`,
`os.getenv`・`session_state` を触る箇所、キーを文字列連結・print・log する箇所。

**grep の当たり**:
```bash
# ハードコードされたキーらしき文字列（Google旧AIza/新AQ. ・OpenAI・Anthropic ほか）
grep -rnE 'AIza[0-9A-Za-z_-]{20,}|AQ\.[0-9A-Za-z._-]{20,}|sk-[0-9A-Za-z]{20,}|sk-ant-[0-9A-Za-z-]{20,}' --include='*.py' .
grep -rniE '(api[_-]?key|secret|token|password)\s*=\s*["'"'"'][^"'"'"']{8,}' --include='*.py' .
# キーがログ・出力に出ていないか
grep -rnE 'print\(|logging\.(info|debug|warning|error)|st\.(write|text|code)' --include='*.py' . | grep -iE 'key|secret|token'
```

**必ず確認すること**:
- `.gitignore` に `.env`, `*.env`, `.streamlit/secrets.toml`, 履歴・データ用ディレクトリ（例 `data/`）,
  `__pycache__/` が入っているか。**入っていなければ High**（キー・機微データがコミットされうる）。
- `.env.example` に**実キーが書かれていないか**（プレースホルダのみが正）。
- ソースにキーがハードコードされていないか。あれば **Critical**。
- git 管理下のアプリなら、**すでにコミット済みでないか**を確認:
  ```bash
  git ls-files | grep -E '\.env$|secrets\.toml$'          # 追跡されていたら Critical
  git log --all -p -- .env .streamlit/secrets.toml 2>/dev/null | grep -iE 'AIza|sk-|key' | head
  ```
  履歴に残っていたら「削除しても履歴に残る。キーを失効させ再発行せよ」と明記（High〜Critical）。
- キーが `session_state` にパスワード入力（`type="password"`）で入るのは適切。ただし
  **キーがエラーメッセージや履歴 output に混入しないか**を確認（3, 7章と連動）。

**安全な形の例**: 解決順が `session_state → 環境変数 → st.secrets` で、`st.secrets` が無い環境でも
try で握られている（アクセス自体が例外を投げるため）。この形なら問題なし＝「良かった点」に回す。

---

## 2. 出力レンダリングと XSS

LLM の出力やユーザー入力を **HTML として描画**すると、`<script>` や `onerror` が実行されうる。
Streamlit は既定でエスケープするので、危険なのは**明示的に生 HTML を許可した箇所**。

**grep の当たり**:
```bash
grep -rnE 'unsafe_allow_html\s*=\s*True|st\.html\(|st\.components\.v1\.html|components\.html' --include='*.py' .
grep -rnE 'st\.markdown\(|st\.write\(' --include='*.py' .
```

**判断基準**:
- `unsafe_allow_html=True` に **LLM出力 / ユーザー入力が流れ込む** → **High**（反射型XSS）。
  再現例まで書く: モデル出力に `<img src=x onerror=alert(document.cookie)>` が含まれ描画されると発火。
- `unsafe_allow_html=True` でも**渡すのが固定文字列・自前のラベルだけ**なら問題なし。
- `st.markdown(生成結果)` は既定で HTML 無効なので基本安全。ただし Markdown リンク
  `[x](javascript:...)` は Streamlit 側で無害化される想定——バージョン依存なので、生成結果を
  そのまま `st.markdown` するなら「HTMLは無効＝安全」と確認したことを記録する。
- `st.code(...)` はコードブロック表示でエスケープされる＝安全。

**修正パターン**: 生 HTML が不要なら `unsafe_allow_html` を外す。どうしても必要なら
`html.escape()` してから埋め込む、もしくは許可タグだけの sanitizer（bleach 等）を通す。

---

## 3. 入力とインジェクション

**3-1. パストラバーサル / ファイル名**
`download_button` の `file_name`、保存パスにユーザー入力・タイトルが混ざる箇所を見る。

```bash
grep -rnE 'file_name\s*=|open\(|Path\(|\.write_text|\.write\(' --include='*.py' .
```
- ファイル名生成にサニタイズ関数があるか（英数と一部記号だけ残す等）。`../` や絶対パスが
  そのまま `file_name` や `open()` に渡ると **High**。
- ただし `download_button` の `file_name` はブラウザのダウンロード名であり、サーバ側で `open()`
  するのとは危険度が違う。**どちらなのかを見極めて**深刻度をつける。
- サニタイズ関数がある場合、**日本語・絵文字・長さ・空文字**の扱いに穴がないか一度目を通す
  （壊れても RCE ではないので Low〜Info が多い）。

**3-2. eval / exec / コマンド実行**
```bash
grep -rnE '\beval\(|\bexec\(|os\.system\(|subprocess\.|__import__\(|pickle\.load' --include='*.py' .
```
- ユーザー入力やLLM出力が上記に渡る → **Critical**（RCE）。この種のアプリでは通常無いはずで、
  あったら最優先。無ければ「危険な動的実行なし＝確認済み」。

**3-3. プロンプトインジェクション**
ユーザー入力・貼り付けたメール本文などが system 指示ごとLLMに渡る。個人ツールでは
「自分の入力で自分のモデルが乱れるだけ」なので**通常は Low〜Info**。ただし:
- LLM出力を**そのまま実行・HTML描画・ファイル書き込み**する経路があると、注入が実害に化ける
  （2章・3-1・3-2と連動）。その連鎖があるなら深刻度を引き上げる。
- 他人の入力を処理する設計（共有・API化）なら Medium 以上で扱う。

---

## 4. ファイル・データの取り扱い

**見る場所**: 履歴・キャッシュ・一時ファイルの保存先、書き込み先ディレクトリの決め方。

- 生成結果や入力を**平文で保存**していないか。していても、保存先が `.gitignore` 済みで
  ローカルのみなら個人利用では許容（Info）。**機微情報（メール全文・個人情報）が含まれうる**なら、
  「リポジトリや共有ディレクトリに出さないこと」を注記。
- 書き込み先が**固定パス**か（`Path(__file__).parent / "data"` 等）。ユーザー入力でディレクトリが
  変わるなら 3-1 と同じ扱い。
- 保存失敗を握りつぶす設計自体は可用性の判断でありセキュリティ問題ではない——**ただし
  握りつぶす際にキーや個人情報をログに吐いていないか**だけ確認。
- 一時ファイルを `/tmp` に予測可能な名前で作っていないか（共有マシンなら Low）。

---

## 5. 依存パッケージの脆弱性

```bash
# バージョン固定の状況を見る
cat requirements.txt requirements*.txt pyproject.toml 2>/dev/null
# 監査ツールがあれば使う（無ければスキップし、レポートに「未実施」と書く）
pip-audit -r requirements.txt 2>/dev/null || echo "pip-audit 未導入"
```
- `>=` のみで上限なしは、再現性・供給網の観点で **Low**（「固定 or ロックファイル推奨」）。
- `pip-audit` / `safety` が使えるなら実行し、既知CVEのあるパッケージを **Medium 以上**で拾う。
  ツールが無い環境では「監査未実施」と正直に書く（勝手に脆弱性を捏造しない）。
- 見慣れない/タイポっぽいパッケージ名がないか（typosquatting）を一応眺める。

---

## 6. Streamlit のデプロイ・設定

ローカルで `streamlit run` する分には安全でも、**公開・共有すると前提が変わる**。

- 起動方法・スクリプト・README に `--server.address 0.0.0.0` や `--server.enableCORS false`,
  `--server.enableXsrfProtection false` が無いか。あれば、**外部公開時に** 認証なしで誰でも
  叩ける／XSRF無効になる旨を Medium〜High で。
  ```bash
  grep -rnE 'server\.address|enableCORS|enableXsrfProtection|0\.0\.0\.0|--server' . --include='*.py' --include='*.sh' --include='*.md' --include='*.toml'
  ```
- `.streamlit/secrets.toml` が `.gitignore` 済みか（1章と連動）。
- 認証が無いアプリを公開URLに載せる計画があれば、「Streamlit 単体に認証はない。
  リバースプロキシ/Basic認証/アクセス制限を前に置くこと」を助言。
- **このアプリが個人ローカル利用のみ**なら、これらは「現状該当なし・共有時に要対応」の Info で良い。

---

## 7. エラー処理と情報漏洩

```bash
grep -rnE 'except.*:\s*$|st\.(error|exception|write)\(.*exc|traceback|str\(e\)|\{exc\}|\{e\}' --include='*.py' .
```
- 例外の**生メッセージ・スタックトレースをそのままUIに出す**と、内部パスやキーの一部が
  漏れうる。個人ツールなら Low、共有アプリなら Medium。
- 例外メッセージに**APIキーやプロンプト全文が含まれて表示**されないか（SDKの例外を包んで
  UIに渡す設計なら、包んだ文字列に何を入れているか確認）。
- `st.exception()` はスタックトレースを丸ごと出すので、本番想定なら避ける助言を。

---

## 深刻度をつけるときの早見表

- **キーが git/公開に出ている・出る** → Critical/High
- **信用できない文字列が HTML描画/実行/任意パス書き込みに届く** → High（届かないなら格下げ）
- **機微データ平文・既知CVE・トレース漏れ** → Medium
- **バージョン未固定・親切すぎるエラー・軽微なサニタイズ穴** → Low
- **今は無害だが共有したら危険** → 条件を明記して1段上げる

---

## 認証・DBを持つ場合の追加観点（該当する構成のときだけ）

ログイン・データベース・外部公開を持つアプリでは、上記7カテゴリに加えて以下も見る。
**個人ローカルツールには無縁なので、これらの機能が実在するときだけ点検する**（無い機能の
不在を「脆弱性」として書かない）。

**A. 認証・セッション**
- パスワードが平文/弱いハッシュ（md5, sha1 単体）で保存されていないか → High。`bcrypt`/`argon2` が正。
- セッションIDやトークンが推測可能・失効しない・URLに載っていないか。
- `st.session_state` に**認証状態だけ**を置いて、権限チェックを各ページで実際に行っているか
  （Streamlit はページを直接URLで開けるため、ページ側でガードしないと認証を素通りできる）→ High。
- ログイン試行のレート制限・ロックアウトの有無（無ければ Low〜Medium）。

**B. SQL / NoSQL インジェクション**
```bash
grep -rnE 'execute\(|executemany\(|cursor\.|f".*(SELECT|INSERT|UPDATE|DELETE).*\{|\.format\(.*(SELECT|INSERT)' --include='*.py' .
```
- クエリを**文字列連結・f-string でユーザー入力から組み立てて**いないか → High/Critical。
  パラメータ化クエリ（`execute(sql, (params,))`）や ORM が正。
- ORM 使用時も `raw()` / `text()` に生入力が渡っていないか確認。

**C. アクセス制御・IDOR**
- ユーザーIDやレコードIDを入力から受け取り、**本人のものか検証せず**に読み書きしていないか
  （他人のID指定で他人のデータが見える）→ High。
- 管理者機能がロールチェックなしに叩けないか。

**D. CSRF / 外部連携**
- 外部への副作用（メール送信・課金・書き込み）を持つエンドポイントに XSRF 保護があるか
  （Streamlit は既定で XSRF 有効。6章で無効化されていないか確認）。
- Webhook や外部APIコールで、受信データを検証せず信用していないか。
