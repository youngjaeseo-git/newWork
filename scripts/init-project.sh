#!/usr/bin/env bash
set -euo pipefail

# ── 새 프로젝트 추적 파일 세팅 ───────────────────────────────────────────────
# CLAUDE.md 3번 "프로젝트 진행 관리" 규칙에 따라
# templates/ 의 빈 양식을 프로젝트 루트로 복사하고 docs/ 를 만든다.
#
# 사용법:
#   ./scripts/init-project.sh          # 현재 루트에 추적 파일 생성
#   ./scripts/init-project.sh --force  # 이미 있어도 덮어쓰기

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATES_DIR="$ROOT_DIR/templates"

FORCE=0
if [[ "${1:-}" == "--force" ]]; then
  FORCE=1
fi

if [[ ! -d "$TEMPLATES_DIR" ]]; then
  echo "[init] templates/ 디렉터리를 찾을 수 없습니다: $TEMPLATES_DIR" >&2
  exit 1
fi

TODAY="$(date +%F)"

copy_template() {
  local name="$1"
  local src="$TEMPLATES_DIR/$name"
  local dst="$ROOT_DIR/$name"

  if [[ ! -f "$src" ]]; then
    echo "[init] 건너뜀 (양식 없음): $name" >&2
    return
  fi

  if [[ -f "$dst" && "$FORCE" -ne 1 ]]; then
    echo "[init] 이미 있음, 건너뜀: $name  (덮어쓰려면 --force)"
    return
  fi

  # YYYY-MM-DD 자리표시자를 오늘 날짜로 치환하며 복사
  sed "s/YYYY-MM-DD/$TODAY/g" "$src" > "$dst"
  echo "[init] 생성: $name"
}

for f in brainstorming.md plan.md todo.md work.md history.md; do
  copy_template "$f"
done

# 산출물 보관용 docs/ 디렉터리
if [[ ! -d "$ROOT_DIR/docs" ]]; then
  mkdir -p "$ROOT_DIR/docs"
  echo "[init] 생성: docs/"
else
  echo "[init] 이미 있음, 건너뜀: docs/"
fi

echo
echo "[init] 완료. 먼저 brainstorming.md 부터 채우세요."
echo "[init] 안내: \"어떤 걸 만들고 싶으세요? 떠오르는 것 아무거나, 정리 안 해도 됩니다.\""
