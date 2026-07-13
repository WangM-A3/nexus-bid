FROM python:3.11-slim

# 安装中文字体（PDF报告需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先装依赖（利用Docker缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# 复制代码
COPY . .

# 创建必要目录
RUN mkdir -p upload output

# 暴露端口
EXPOSE 7860

# 环境变量
ENV PORT=7860
ENV SILICONFLOW_API_KEY=sk-toiqhdxjmwxtlgzxxbbrsimrnebyfmvedsrpwesqdeyppviq

# 启动
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:7860", "app:app", "--timeout", "120"]
