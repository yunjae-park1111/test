# 멀티스테이지 빌드를 위한 베이스 이미지
ARG PYTHON_VERSION=3.11-slim
ARG NODE_VERSION=18-alpine

# ================================================================
# Stage 1: Python Dependencies Builder
# ================================================================
FROM python:${PYTHON_VERSION} as python-builder

# 보안을 위한 비루트 사용자 생성
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Python 의존성 설치를 위한 별도 스테이지
WORKDIR /app

# requirements.txt 복사 (레이어 캐싱 최적화)
COPY ai-platform-backend/requirements.txt /app/backend-requirements.txt
COPY vllm-benchmark/requirements.txt /app/benchmark-requirements.txt

# Python 가상환경 생성 및 의존성 설치
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# pip 업그레이드 및 보안 패키지 설치
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
        -r /app/backend-requirements.txt \
        -r /app/benchmark-requirements.txt

# ================================================================
# Stage 2: Node.js Frontend Builder  
# ================================================================
FROM node:${NODE_VERSION} as node-builder

# 보안을 위한 비루트 사용자
USER node
WORKDIR /app

# package.json과 lock 파일 복사 (캐싱 최적화)
COPY --chown=node:node frontend/package*.json ./

# 의존성 설치 (프로덕션 전용)
RUN npm ci --only=production && \
    npm cache clean --force

# 소스 코드 복사 및 빌드
COPY --chown=node:node frontend/ ./
RUN npm run build

# ================================================================
# Stage 3: Production Runtime
# ================================================================
FROM python:${PYTHON_VERSION} as production

# 보안 강화를 위한 시스템 설정
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        # 런타임 필수 패키지만 설치
        curl \
        ca-certificates \
        dumb-init \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    # 불필요한 패키지 제거
    && apt-get autoremove -y \
    # 보안 업데이트
    && apt-get upgrade -y

# 비루트 사용자 생성 (보안 모범 사례)
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# 애플리케이션 디렉토리 설정
WORKDIR /app

# Python 가상환경 복사
COPY --from=python-builder --chown=appuser:appuser /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 빌드된 프론트엔드 정적 파일 복사
COPY --from=node-builder --chown=appuser:appuser /app/dist /app/static

# 백엔드 소스 코드 복사
COPY --chown=appuser:appuser ai-platform-backend/ /app/backend/
COPY --chown=appuser:appuser vllm-benchmark/ /app/benchmark/

# 설정 파일 복사
COPY --chown=appuser:appuser k8s/configmaps/ /app/config/

# 필요한 디렉토리 생성 및 권한 설정
RUN mkdir -p /app/logs /app/cache /app/tmp && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app && \
    # 로그 및 캐시 디렉토리는 쓰기 권한 필요
    chmod 777 /app/logs /app/cache /app/tmp

# 보안을 위한 비루트 사용자로 전환
USER appuser

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 환경 변수 설정
ENV PYTHONPATH="/app/backend:/app/benchmark:$PYTHONPATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 포트 노출
EXPOSE 8080 9090

# 볼륨 마운트 포인트
VOLUME ["/app/logs", "/app/cache"]

# 신호 처리를 위한 dumb-init 사용 (보안 모범 사례)
ENTRYPOINT ["dumb-init", "--"]

# 애플리케이션 시작 명령
CMD ["python", "-m", "uvicorn", "backend.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--workers", "4", \
     "--log-level", "info", \
     "--access-log"]

# ================================================================
# 빌드 메타데이터 (보안 및 추적을 위한 라벨)
# ================================================================
LABEL maintainer="AI Platform Team <team@aiplatform.com>" \
      version="1.0.0" \
      description="AI Platform Backend with vLLM Benchmark" \
      org.opencontainers.image.title="ai-platform-backend" \
      org.opencontainers.image.description="FastAPI backend with Kubernetes integration" \
      org.opencontainers.image.vendor="AI Platform Team" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
      org.opencontainers.image.licenses="MIT" \
      security.scan="enabled" \
      security.nonroot="true"
