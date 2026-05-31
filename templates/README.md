# templates/ — 추적 파일 빈 양식

CLAUDE.md 3번 "프로젝트 진행 관리" 규칙에서 쓰는 추적 파일들의 빈 양식입니다.

| 양식 | 역할 |
|---|---|
| `brainstorming.md` | 초기 아이디어·요구사항 원본 덤프 (수정하지 않음) |
| `plan.md` | 전체 계획 + 주간 세부 계획 + 현재 상태 요약 |
| `todo.md` | 진행 상태 대시보드 (거시 관점) |
| `work.md` | 할 일 / 한 일 체크리스트 (미시 관점) |
| `history.md` | 주간 아카이브 |

## 새 프로젝트에서 사용

```bash
./scripts/init-project.sh          # 양식을 루트로 복사 (+ docs/ 생성)
./scripts/init-project.sh --force  # 이미 있어도 덮어쓰기
```

스크립트는 양식 안의 `YYYY-MM-DD` 자리표시자를 실행 당일 날짜로 바꿔 복사합니다.
복사 후 **brainstorming.md 부터** 채우세요.
