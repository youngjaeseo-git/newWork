#!/usr/bin/env bash
#
# sync-standards.sh — 작업방식 기준을 '템플릿 repo'에서 이 프로젝트로 가져온다(일방향 pull).
# ─────────────────────────────────────────────────────────────────────────
# - 가져오는 것: CLAUDE.md, templates/  (공통 작업방식)
# - 건드리지 않는 것: run.sh 등 '이 프로젝트 고유' 파일 (덮어쓰기 방지)
# - 이 프로젝트(gameLadder)는 '받아 쓰는 쪽'이며, 템플릿으로 내보내지 않는다.
#
# 사용:  ./scripts/sync-standards.sh         (main 브랜치에서 가져오기)
#        TEMPLATE_RAW=<raw 베이스URL> ./scripts/sync-standards.sh   (다른 위치 지정)
#
# raw URL은 맥/클라우드 컨테이너 양쪽에서 접근됩니다(GitHub raw 허용).
# ─────────────────────────────────────────────────────────────────────────
set -euo pipefail

TEMPLATE_RAW="${TEMPLATE_RAW:-https://raw.githubusercontent.com/youngjaeseo-git/newWork/refs/heads/main}"

echo "▶ 템플릿에서 작업방식 가져오기: $TEMPLATE_RAW"

# 1) 작업방식 기준
curl -fsSL "$TEMPLATE_RAW/CLAUDE.md" -o CLAUDE.md
echo "  ✅ CLAUDE.md"

# 2) 양식(templates) — 있으면 갱신
mkdir -p templates
if curl -fsSL "$TEMPLATE_RAW/templates/troubleshooting.md" -o templates/troubleshooting.md; then
  echo "  ✅ templates/troubleshooting.md"
fi

# 3) 공용 헬퍼 스크립트 (프로젝트 무관) — 템플릿에 있으면 가져옴
mkdir -p scripts
if curl -fsSL "$TEMPLATE_RAW/scripts/shot.sh" -o scripts/shot.sh; then
  chmod +x scripts/shot.sh
  echo "  ✅ scripts/shot.sh (폰 화면 캡처+업로드)"
fi

echo "✅ 동기화 완료. 'git diff' 로 변경 확인 후 커밋하세요."
echo "   (run.sh 등 프로젝트 고유 파일은 건드리지 않았습니다)"
