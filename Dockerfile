FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建必要的目录并设置权限
RUN mkdir -p /app/data /app/certs /app/utils /app/i18n && \
    chown -R 1000:1000 /app && \
    chmod 777 /app/data && \
    chmod 755 /app/certs

# 复制项目文件
COPY requirements.txt .
COPY *.py .
COPY utils/ ./utils/
COPY i18n/ ./i18n/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建非root用户
RUN useradd -m -u 1000 botuser
RUN chown -R botuser:botuser /app
USER botuser

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 启动命令
CMD ["python", "main.py"] 