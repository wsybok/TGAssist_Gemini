FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
COPY *.py .
COPY utils/ ./utils/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建非root用户
RUN useradd -m -u 1000 botuser
USER botuser

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV USE_WEBHOOK=true

# 启动命令
CMD ["python", "main.py"] 