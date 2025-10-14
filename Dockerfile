# 사용할 Python 기본 이미지 (Python 3.11 버전을 가정)
FROM python:3.11-slim

# 작업 디렉토리 설정 (컨테이너 내부)
WORKDIR /app

# 시스템 의존성 설치 (필요한 경우)
# MySQL 클라이언트 등을 설치해야 할 수 있지만, 일단 최소한으로 진행합니다.
# RUN apt-get update && apt-get install -y --no-install-recommends \
#    default-libmysqlclient-dev \
#    && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 코드 모두 복사
COPY . .

# Uvicorn 서버를 실행할 포트 노출 (FastAPI 기본 포트 8000)
EXPOSE 8000

# 서버 실행 명령어 정의
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# 컨테이너 환경에서는 보통 --reload를 빼고 실행합니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]