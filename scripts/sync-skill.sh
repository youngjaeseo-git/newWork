#!/usr/bin/env bash
set -euo pipefail

# ── 스킬 패키지 동기화 ───────────────────────────────────────────────────────
# 루트의 CLAUDE.md / templates/ / scripts/init-project.sh 를
# start-project 스킬 폴더로 복사해 자기완결형(self-contained) 으로 만든다.
#
# 루트 파일이 "원본"이고, 스킬 폴더는 이 스크립트로 생성되는 패키지다.
# CLAUDE.md 나 양식을 수정했으면 이 스크립트를 다시 돌려 동기화한다.
#
# 사용법: ./scripts/sync-skill.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_DIR="$ROOT_DIR/.claude/skills/start-project"

mkdir -p "$SKILL_DIR/scripts" "$SKILL_DIR/templates"

cp "$ROOT_DIR/CLAUDE.md"                 "$SKILL_DIR/CLAUDE.md"
cp "$ROOT_DIR/scripts/init-project.sh"   "$SKILL_DIR/scripts/init-project.sh"
chmod +x "$SKILL_DIR/scripts/init-project.sh"
cp "$ROOT_DIR/templates/"*.md            "$SKILL_DIR/templates/"

echo "[sync] 스킬 패키지 동기화 완료 → $SKILL_DIR"
echo "[sync] 포함: CLAUDE.md, scripts/init-project.sh, templates/*.md"
