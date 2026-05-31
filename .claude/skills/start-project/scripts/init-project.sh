#!/usr/bin/env bash
set -euo pipefail

# ── 새 프로젝트 추적 파일 세팅 ───────────────────────────────────────────────
# CLAUDE.md 3번 "프로젝트 진행 관리" 규칙에 따라
# templates/ 의 빈 양식을 대상 폴더로 복사하고 docs/ 를 만든다.
#
# 양식(source)은 이 스크립트와 같은 패키지의 templates/ 에서 읽고,
# 생성(destination)은 기본적으로 "현재 작업 폴더"에 한다.
# → 그래서 ~/.claude/skills/ 로 옮겨 스킬로 호출해도 현재 프로젝트에 생성된다.
#
# 사용법:
#   ./scripts/init-project.sh                 # 현재 폴더에 추적 파일 생성
#   ./scripts/init-project.sh /path/to/proj   # 지정 폴더에 생성
#   ./scripts/init-project.sh --force         # 이미 있어도 덮어쓰기

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATES_DIR="$PKG_DIR/templates"

FORCE=0
DEST_DIR="$(pwd)"
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    -*) echo "[init] 알 수 없는 옵션: $arg" >&2; exit 1 ;;
    *)  DEST_DIR="$(cd "$arg" && pwd)" ;;
  esac
done

if [[ ! -d "$TEMPLATES_DIR" ]]; then
  echo "[init] templates/ 디렉터리를 찾을 수 없습니다: $TEMPLATES_DIR" >&2
  exit 1
fi

TODAY="$(date +%F)"

copy_template() {
  local name="$1"
  local src="$TEMPLATES_DIR/$name"
  local dst="$DEST_DIR/$name"

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

# 상시 추적 파일만 복사한다. troubleshooting.md 는 필요할 때만 쓰는 양식이라 제외.
for f in brainstorming.md plan.md todo.md work.md history.md; do
  copy_template "$f"
done

# 산출물 보관용 docs/ 디렉터리
if [[ ! -d "$DEST_DIR/docs" ]]; then
  mkdir -p "$DEST_DIR/docs"
  echo "[init] 생성: docs/"
else
  echo "[init] 이미 있음, 건너뜀: docs/"
fi

echo
echo "[init] 완료 → $DEST_DIR"
echo "[init] 먼저 brainstorming.md 부터 채우세요."
echo "[init] 안내: \"어떤 걸 만들고 싶으세요? 떠오르는 것 아무거나, 정리 안 해도 됩니다.\""
