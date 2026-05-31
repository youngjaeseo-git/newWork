# 작업방식 기준 (Working Standards)

새 프로젝트를 항상 **같은 기준·같은 세팅**으로 시작하기 위한 템플릿 모음입니다.
매번 규칙을 다시 만들지 않고, 이 저장소의 내용을 가져다 적용하면 됩니다.

## 구성

| 경로 | 역할 |
|---|---|
| `CLAUDE.md` | 작업방식 기준 본체 (Claude가 자동으로 읽음) |
| `run.sh` | 실행 진입점 템플릿 (`./run.sh` 하나로 실행) |
| `templates/` | 추적 파일 빈 양식 (brainstorming · plan · todo · work · history · troubleshooting) |
| `scripts/init-project.sh` | 추적 파일 + `docs/` 를 현재 프로젝트에 생성 |
| `scripts/sync-skill.sh` | 위 내용을 `start-project` 스킬 패키지로 동기화 |
| `.claude/skills/start-project/` | 호출형 스킬 — `/start-project` 로 킥오프 자동화 |

---

## 새 프로젝트에 적용하는 3가지 방법

### ① 글로벌 규칙 — 모든 프로젝트에 자동 적용
`CLAUDE.md` 를 개인 글로벌 메모리로 복사해 두면, 어느 프로젝트에서든 Claude가 자동으로 읽습니다.

```bash
cp CLAUDE.md ~/.claude/CLAUDE.md
```

- 장점: 한 번 해두면 끝. 호출 불필요.
- 한계: 추적 파일·`run.sh` 스캐폴딩은 따로 만들어야 함 (→ ② 또는 ③).

### ② 나만의 스킬 — `/start-project` 로 킥오프 자동화 (추천)
`start-project` 스킬을 개인 스킬 폴더로 복사하면, 어느 프로젝트에서든 호출 한 번으로
CLAUDE.md 배치 + 추적 파일 생성 + 브레인스토밍 시작까지 진행됩니다.

```bash
# 1) 스킬 패키지를 최신 상태로 동기화 (CLAUDE.md/templates 수정했을 때)
./scripts/sync-skill.sh

# 2) 개인 스킬 폴더로 복사
cp -r .claude/skills/start-project ~/.claude/skills/

# 3) 이후 아무 프로젝트에서나
/start-project
```

- 장점: "불러오기" 한 번으로 전체 세팅. 스크립트·양식이 스킬에 동봉됨.
- 참고: 클라우드(웹) 세션은 임시 환경이라 `~/.claude/` 가 유지되지 않습니다. 로컬(데스크톱/CLI)에서 쓰세요.

### ③ 템플릿 저장소 — 이 repo에서 새로 시작
이 저장소 자체를 새 프로젝트의 출발점으로 씁니다.

```bash
# 추적 파일만 현재 폴더에 만들고 싶을 때
./scripts/init-project.sh

# 또는 GitHub에서 이 repo를 "Template repository" 로 설정해 두고
# "Use this template" 버튼으로 새 저장소 생성
```

- 장점: 처음부터 모든 파일을 갖고 출발.
- 한계: 깃 기반 프로젝트에 자연스러움.

---

## 추천 조합

- **로컬에서 여러 프로젝트를 한다면**: ① (글로벌 규칙) + ② (스킬) 조합이 가장 편합니다.
- **새 프로젝트를 깃 저장소로 시작한다면**: ③ 템플릿 저장소.

## 수정했을 때

`CLAUDE.md` 나 `templates/` 를 고쳤다면, 스킬 패키지를 다시 동기화하세요.

```bash
./scripts/sync-skill.sh
```
