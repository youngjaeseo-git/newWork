#!/usr/bin/env bash
#
# shot.sh — 실행 중인 안드로이드 폰의 '현재 화면'을 캡처해 docs/shots/에 저장하고
#           깃에 자동 커밋·푸시한다. (수동 캡처·크롭·업로드 대체)
# ─────────────────────────────────────────────────────────────────────────
# 프로젝트 무관(Flutter/언어 상관없음). 필요한 건 adb + git 뿐이라
# 안드로이드 앱을 띄우는 '어느 프로젝트에서나' 그대로 동작한다.
#
# 사용: ./scripts/shot.sh    (게임/앱이 폰에서 실행 중일 때)
# 그 다음 클로드에게 "방금 캡처 봐줘" 라고 하면 됨.
# ─────────────────────────────────────────────────────────────────────────
set -euo pipefail

command -v adb >/dev/null 2>&1 || { echo "❌ adb 필요 (Android platform-tools 설치)"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "❌ git 필요"; exit 1; }

mkdir -p docs/shots
TS="$(date +%Y%m%d_%H%M%S)"
OUT="docs/shots/shot_$TS.png"

echo "▶ 폰 화면 캡처 → $OUT"
adb exec-out screencap -p > "$OUT" 2>/dev/null \
  || { echo "❌ 캡처 실패 — 폰 연결/USB 디버깅 확인 (adb devices)"; rm -f "$OUT"; exit 1; }
[ -s "$OUT" ] || { echo "❌ 캡처 결과가 비어 있음 (폰 화면이 켜져 있는지 확인)"; rm -f "$OUT"; exit 1; }

git add "$OUT"
git commit -m "chore(shot): 폰 화면 캡처 $TS" >/dev/null 2>&1 || true
git pull --rebase --autostash >/dev/null 2>&1 || true
if git push >/dev/null 2>&1; then
  echo "✅ 업로드 완료: $OUT — 클로드에게 '방금 캡처 봐줘' 라고 하세요."
else
  echo "⚠️ 푸시 실패(네트워크?). 'git push' 후 클로드에게 알려주세요. 파일: $OUT"
fi
