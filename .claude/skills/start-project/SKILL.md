---
name: start-project
description: 새 프로젝트를 내 작업방식 기준으로 킥오프한다. 작업방식 기준(CLAUDE.md)을 프로젝트 루트에 배치하고, 추적 파일(brainstorming/plan/todo/work/history)과 docs/ 를 생성한 뒤, 브레인스토밍부터 시작한다. Use when the user starts a new project or asks to set up / kick off / 프로젝트 시작 / 킥오프 / 새 프로젝트 세팅.
---

# start-project — 새 프로젝트 킥오프

새 프로젝트를 항상 같은 작업방식 기준으로 시작하기 위한 스킬이다.
이 스킬 폴더에는 작업방식 기준 `CLAUDE.md`, 추적 파일 양식 `templates/`,
세팅 스크립트 `scripts/init-project.sh` 가 함께 들어 있다.

## 절차

아래에서 `{skill_dir}` 는 이 SKILL.md 가 있는 폴더를 가리킨다.

1. **작업방식 기준 배치**
   - 현재 프로젝트 루트에 `CLAUDE.md` 가 없으면, `{skill_dir}/CLAUDE.md` 를 루트로 복사한다.
   - 이미 있으면 덮어쓰지 말고, 차이를 사용자에게 알린 뒤 어떻게 할지 묻는다.

2. **추적 파일 생성**
   - 현재 프로젝트 폴더에서 다음을 실행한다:
     `bash {skill_dir}/scripts/init-project.sh`
   - 이 명령은 `brainstorming/plan/todo/work/history.md` 와 `docs/` 를 현재 폴더에 만든다.

3. **브레인스토밍 시작 (가장 먼저)**
   - 사용자에게 묻는다: "어떤 걸 만들고 싶으세요? 지금 떠오르는 것 아무거나 말씀해 주세요. 정리 안 해도 됩니다."
   - 답변을 **가공 없이** `brainstorming.md` 에 기록한다. 정리·판단하지 않는다.

4. **경쟁 제품 피드백 리서치 (해당되면)**
   - 비슷한 제품·서비스가 있으면 `/deep-research` 로 `개선 요청 Top 5` / `불편·불만 Top 5` 를 모아
     `docs/YYYY-MM-DD_경쟁제품-피드백.md` 로 저장하고, 각 항목 적용 여부를 사용자에게 체크받는다.

5. **지난 교훈 참고**
   - 배치한 `CLAUDE.md` 의 13번 "지난 프로젝트 교훈" 을 먼저 훑어보고, 이번 계획에 반영한다.

6. **계획 수립**
   - `brainstorming.md` · 리서치 결과 · 지난 교훈을 바탕으로 `plan.md` (전체 목표 → 마일스톤 → 주간 계획)를 작성한다.

7. **도구 추천**
   - brainstorming 내용을 보고 이 프로젝트에 유용한 스킬/MCP 도구를 추천한다.
   - 이후 1달·2달·3달 시점에 맞는 도구를 다시 상기시킨다.

이후의 모든 세부 규칙(일하는 방식, 커밋/PR, 배포·수익 모델 등)은
프로젝트 루트에 배치된 `CLAUDE.md` 를 따른다.

## 마무리 (프로젝트 종료 시)

프로젝트(또는 큰 마일스톤)를 마치면 **회고**를 남긴다. (`CLAUDE.md` 3번 "프로젝트 회고 루틴")
- `templates/retrospective.md` 로 총평을 작성해 `docs/YYYY-MM-DD_회고.md` 로 저장한다.
- 재사용 가능한 교훈은 사용자 동의를 받아 `CLAUDE.md` 13번에 추가한다 → 다음 프로젝트가 참고.

## 설치 (개인 스킬로 쓰려면)

이 폴더(`start-project/`)를 통째로 `~/.claude/skills/` 아래로 복사하면
어느 프로젝트에서든 `/start-project` 로 호출할 수 있다.
