#!/usr/bin/env bash
set -euo pipefail

# ── 프로젝트 루트 기준으로 실행 ──────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── 환경 변수 로드 (.env 파일이 있으면 불러옴) ────────────────────────────────
if [ -f ".env" ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# ── 필수 환경 변수 체크 ────────────────────────────────────────────────────────
# 필요한 변수가 있으면 아래에 추가:
# : "${MY_VAR:?MY_VAR is required. .env.example 을 참고하세요}"

# ── 의존성 설치 (필요한 섹션만 주석 해제) ────────────────────────────────────
# Node.js
# if [ -f "package.json" ]; then
#   echo "[setup] npm install..."
#   npm install --silent
# fi

# Python
# if [ -f "requirements.txt" ]; then
#   echo "[setup] pip install..."
#   pip install -r requirements.txt -q
# fi

# ── 실행 ──────────────────────────────────────────────────────────────────────
# 아래에 실제 실행 명령을 넣으세요:
# 예) node src/index.js
# 예) python main.py
# 예) go run ./cmd/server

echo "run.sh: 실행 명령을 아래에 채워주세요."
echo "  예) node src/index.js"
echo "  예) python main.py"
