# 同時アクセス時に別人のPDFが届く / PDFが壊れる（競合状態）

- 記録日: 2026-08-31
- 対象: `src/main.py` の `GET /api/generate`
- 状態: **修正済み（2026-08-31 検証完了）**

---

## 症状

複数のリクエストが同時に処理されると、次のいずれかが起きる。

- 頼んだのと違う問題数の PDF が届く（他人のプリントが届く）
- 開けない壊れた PDF が届く
- どちらの場合も HTTP ステータスは `200 OK`（成功扱い）

---

## 原因

`src/main.py` は PDF 生成時、毎回同じファイル名を使っている。

```python
tex_filename = "output.tex"
pdf_filename = "output.pdf"
```

FastAPI は `async def` ではなく `def` で定義されたエンドポイントを
スレッドプールで並行実行するため、サーバーが1台・ワーカーが1つでも
複数のリクエストが同時に走る。その全員が同じ5つのファイルを奪い合う。

```
output.tex   ← 自分で書く
output.aux   ← platex が作る
output.log   ← platex が作る
output.dvi   ← platex が作る
output.pdf   ← dvipdfmx が作る
```

```
Aさん: output.tex を書く ─▶ platex 実行 ─────▶ output.pdf を返す
Bさん:      output.tex を上書き ─▶ platex 実行 ─▶
                 ↑ Aの内容が壊れる        Aに B の PDF が届く
```

---

## 再現手順

TeX Live がインストールされた Windows 環境で実行。

```powershell
# サーバー起動
.venv\Scripts\activate
uvicorn src.main:app --reload

# 別ターミナルから、問題数を変えて同時に3件投げる
Start-Job { curl.exe "http://localhost:8000/api/generate?num_problems=10&num_prints=1" -o "$env:TEMP\a.pdf" }
Start-Job { curl.exe "http://localhost:8000/api/generate?num_problems=30&num_prints=1" -o "$env:TEMP\b.pdf" }
Start-Job { curl.exe "http://localhost:8000/api/generate?num_problems=50&num_prints=1" -o "$env:TEMP\c.pdf" }
Get-Job | Wait-Job | Out-Null

# 確認
Get-FileHash "$env:TEMP\a.pdf","$env:TEMP\b.pdf","$env:TEMP\c.pdf"
```

---

## 実測結果（2026-08-31）

| リクエスト | 期待 | 実際 |
|---|---|---|
| a.pdf | 10問 | **30問**（別リクエストの内容） |
| b.pdf | 30問 | **開けない**（PDFビューアが 0/0 ページと表示） |
| c.pdf | 50問 | 50問（正常） |

3件中2件が失敗。いずれも HTTP 200 で返っていた。

---

## ログに残った決定的な証拠

### 1. 複数プロセスの出力が1文字単位で混ざっている

```
(c]:[5/texlive/2024/texmf-][6dist/tex/latex/geomet]ry/geometry.sty
```

platex がファイルを読んでいる最中に、別プロセスの dvipdfmx が出力する
`[5]` `[6]` が割り込んでいる。同時実行されている証拠。

### 2. ソースに存在しない文字が出現した

```
! LaTeX Error: Unicode character ^^e7^^81^^a8 (U+7068)
               not set up for use with LaTeX.
l.169   ^^e7^^81^^a8
                    おくと \\
```

U+7068（灨）はソースのどこにも存在しない。
続きが `おくと` であることから、本来は `main.py` の

```python
step1 = f"${latex(expr)}=0$ とおくと"
```

の `と` である。バイト列を比較すると先頭1バイトだけが差し替わっている。

| 文字 | UTF-8 |
|---|---|
| と（本来） | `E3 81 A8` |
| 灨（実際） | `E7 81 A8` |
| 点（他箇所に存在） | `E7 82 B9` |

問題数が違えば同じバイト位置に別の文字が来るため、
**書き込み途中のファイルが読まれ、1文字の途中で2つの内容が接合された**。
ファイルが引き裂かれた瞬間がそのままログに残っている。

### 3. LaTeX エラーが出ても 200 OK が返っている

```
! LaTeX Error: ...
INFO: "GET /api/generate?num_problems=30&num_prints=1 HTTP/1.1" 200 OK
```

`-interaction=nonstopmode` により platex は止まらず最後まで走り、
壊れたページを含む DVI を作って正常終了する。
そのため `subprocess.run(..., check=True)` も例外を投げない。
→ 改善リスト④「エラーが成功として返る」の実物。

---

## 対策案（検討中）

| 案 | 内容 | 評価 |
|---|---|---|
| A. ファイル名を UUID に | 毎回違う名前にする | ゴミが溜まり続ける。削除処理を自前で書く必要 |
| B. 一時ディレクトリ | リクエストごとに使い捨てフォルダ | 削除も自動。有力 |
| C. ロックで直列化 | 1件ずつ順番に処理 | 競合は直るが待ち時間が人数分積み上がる。ワーカーを増やすと破綻 |
| D. ジョブキュー | Redis 等で順番に捌く | 同時実行数を設定で決められるが、Redis 等の導入が必要 |

A・B は直列化しないので待ち時間が増えないが、アクセス集中でサーバーがパンクしうる。
C・D は直列化するので負荷に上限がかかるが、待ち時間が人数分積み上がる。

実測：1リクエスト約0.8秒（10問1枚）、約0.97秒（10問20枚＝40ページ）。
コストの大半は platex の起動という固定費で、ページ数の影響は小さい。
ただしこれは手元の Windows での値であり、Render 無料枠では数倍遅くなりうる。

### 採用：案B（一時ディレクトリ）

理由：
- 想定利用者は塾講師で、同時に何十人も殺到する性質のアプリではない
- 待ち時間を増やさずに済む
- 案A と同じことを標準ライブラリ（`tempfile.TemporaryDirectory`）が保証してくれる。
  自前で削除処理を書くと `try/finally` の書き漏れで「失敗時だけゴミが残る」リスクがある

許容した代償：
- 同時実行数に上限がないため、アクセスが集中すると platex が同時多数起動しサーバーが落ちうる。
  必要になれば `Semaphore` で上限だけ別途かけられる（案Bと案Cの中間）

※ どの案でも、`FileResponse` はレスポンス送信時にファイルを読むため、
　 生成した PDF をメモリに読み込んでから返す必要がある。

---

## 実装した内容

`src/main.py` の PDF 生成部分を以下のように変更した。

1. `tempfile.TemporaryDirectory()` を `with` で使い、リクエストごとに使い捨てフォルダを作る
2. `subprocess.run(..., cwd=tmp)` で、platex / dvipdfmx をそのフォルダの中で実行する
   → `.tex .aux .log .dvi .pdf` の5ファイルが全部そのフォルダに閉じ込められる
3. `check=True` を外し、`capture_output=True, text=True, errors="replace"` を付けて
   `returncode` を自分で判定。失敗時は `raise HTTPException(status_code=500, detail=ログ末尾2000文字)`
4. `FileResponse` を廃止。`with` の中で `read_bytes()` してメモリに読み込み、
   `with` の外で `Response(content=pdf_bytes, media_type="application/pdf", ...)` を返す

`FileResponse` が使えないのは、`with` を抜けた時点でフォルダが消えるのに対し、
`FileResponse` はレスポンス送信時に初めてファイルを読むため。

---

## 検証結果（2026-08-31）

### 単発リクエスト

| 確認項目 | 結果 |
|---|---|
| PDF が正常に生成される | OK（23,269 バイト、10問のプリント） |
| HTTP ステータス | 200 OK |
| プロジェクトルートに `output.*` が残らない | OK（1つも生成されない） |

### 同時アクセス（再現時と同一条件・複数回）

| 確認項目 | 結果 |
|---|---|
| 3件のハッシュが全て異なる | OK |
| 3件とも正常に開ける | OK |
| 頼んだ問題数と一致する | OK（10 / 30 / 50） |
| ルートに `output.*` が残らない | OK |
| `! LaTeX Error` が出ない | OK |

### 本番環境（Render / Debian コンテナ）

ローカルは Windows + TeX Live 2024、本番は Debian + texlive-lang-japanese と
環境が異なるため、デプロイ後に同一の検証を本番に対しても実施した。

新しいコードが動いていることの確認方法：
レスポンスヘッダーに `etag` と `last-modified` が**無い**こと。
Starlette の `FileResponse` はこの2つを必ず付与するが、`Response` は付与しない。

| 確認項目 | 結果 |
|---|---|
| 単発リクエスト | 200 OK / Content-Type: application/pdf / 9,814 バイト |
| PDF の見た目 | ローカル版と同一（日本語・数式・2ページ構成） |
| 同時3件のハッシュ | 全て異なる |
| 頼んだ問題数と一致 | OK |

備考：本番の PDF は 9,814 バイトで、ローカルの 23,269 バイトより小さい。
日本語フォントの埋め込み方が環境で異なるためと思われる。
表示は同一だが、フォントが埋め込まれているかは未確認（優先度低）。

### エラー経路

`dvipdfmx` の引数を存在しないファイルに変えて意図的に失敗させた結果：

```
HTTP/1.1 500 Internal Server Error
{"detail":"dvipdfmxに失敗しました:\n..."}
```

修正前は同じ状況で `200 OK` が返っていた。

---

## 検証中に見つかった別の問題（未対応）

`-interaction=nonstopmode` を `nonstopmpde` とタイプミスしても、
TeX は未知の値を警告して無視し、**既定の `errorstopmode` で続行する**。

`errorstopmode` は LaTeX エラー時に人間の入力を待つモードであり、
`capture_output=True` は stdout / stderr しか横取りしないため **stdin は素通り**する。
つまりエラーが起きると platex がターミナルからの入力を待ち、**リクエストが終わらない**。

さらに厄介なのは、本番（Render）にはターミナルが無いため即座に失敗し、
**手元ではハングし本番では失敗する**という環境依存の挙動になること。

対策：

```python
subprocess.run(..., capture_output=True, stdin=subprocess.DEVNULL, timeout=60)
```

- `stdin=subprocess.DEVNULL` … 何を聞かれても即 EOF。待たない
- `timeout=60` … 万一止まっても強制終了

サーバーから外部コマンドを呼ぶときの定石。改善リストに追加済み。

---

## 関連

- `docs/改善リスト.md` の ① と ④
