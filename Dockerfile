# 第一阶段：安装GCC和编译依赖
FROM python:3.12-alpine as builder

# 安装编译工具和依赖
RUN set -ex && \
    apk add --no-cache \
        gcc \
        musl-dev \
        jpeg-dev \
        zlib-dev \
        libjpeg

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 并安装 Python 依赖
COPY backend/requirements.txt .
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    sed -i '/bcrypt/d' requirements.txt && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# 第二阶段：运行环境
FROM python:3.12-alpine

# 设置环境变量
ENV LANG="C.UTF-8" \
    TZ=Asia/Shanghai \
    PUID=1000 \
    PGID=1000 \
    UMASK=022 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安装运行时依赖
RUN set -ex && \
    apk add --no-cache \
        bash \
        busybox-suid \
        su-exec \
        shadow \
        tini \
        openssl \
        tzdata && \
    # 添加用户
    addgroup -S ab -g 911 && \
    adduser -S ab -G ab -h /home/ab -s /sbin/nologin -u 911 && \
    # 清理
    rm -rf /var/cache/apk/* /root/.cache /tmp/*

# 设置工作目录
WORKDIR /app

# 复制编译阶段安装的 Python 依赖
COPY --from=builder /install /usr/local

# 复制项目代码
COPY --chmod=755 webui/dist ./dist
COPY --chmod=755 backend/src/module ./module
COPY --chmod=755 backend/src/main.py .
COPY --chmod=755 entrypoint.sh /entrypoint.sh


# 设置入口点和暴露端口
ENTRYPOINT ["tini", "-g", "--", "/entrypoint.sh"]
EXPOSE 7892

# 声明数据卷
VOLUME [ "/app/config" , "/app/data" ]
