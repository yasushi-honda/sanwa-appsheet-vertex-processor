FROM python:3.11-slim

WORKDIR /app

# 必要な依存関係のみインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードをコピー
COPY src/ ./src/

# 環境変数
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# 非rootユーザーで実行
RUN useradd -m -u 1000 appuser
USER appuser

# Flaskアプリケーション起動
CMD ["python", "src/main.py"]
