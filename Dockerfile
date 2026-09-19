# ベースとなる環境（軽めのPython 3.11）
FROM python:3.11-slim

# OSのパッケージを更新し、日本語LaTeX環境をインストール
# ※この処理はクラウド上で数分かかります
RUN apt-get update && apt-get install -y \
    texlive-lang-japanese \
    texlive-latex-extra \
    texlive-fonts-recommended \
    fonts-ipaexfont \
    && kanji-config-updmap-sys ipaex \
    && kanji-config-updmap-sys status \
    && rm -rf /var/lib/apt/lists/*

# サーバー内での作業場所を /app に設定
WORKDIR /app

# Pythonのパッケージリストをコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 自分のパソコンの src フォルダ（Pythonのコード）をサーバーにコピー
COPY src/ ./src/
COPY latex_templates/ ./latex_templates/

# クラウドサービス（Render）が使うポート番号を許可
EXPOSE 8000

# サーバー起動時のコマンド（ホストを 0.0.0.0 にして外部アクセスを許可）
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]