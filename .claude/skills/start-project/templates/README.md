# templates/ — 추적 파일 빈 양식

CLAUDE.md 3번 "프로젝트 진행 관리" 규칙에서 쓰는 추적 파일들의 빈 양식입니다.

| 양식 | 역할 |
|---|---|
| `brainstorming.md` | 초기 아이디어·요구사항 원본 덤프 (수정하지 않음) |
| `plan.md` | 전체 계획 + 주간 세부 계획 + 현재 상태 요약 |
| `todo.md` | 진행 상태 대시보드 (거시 관점) |
| `work.md` | 할 일 / 한 일 체크리스트 (미시 관점) |
| `history.md` | 주간 아카이브 |
| `troubleshooting.md` | 트러블슈팅 로그 (필요할 때만, `docs/` 에 복사해 사용) |

## 새 프로젝트에서 사용

```bash
./scripts/init-project.sh          # 양식을 루트로 복사 (+ docs/ 생성)
./scripts/init-project.sh --force  # 이미 있어도 덮어쓰기
```

스크립트는 `brainstorming` · `plan` · `todo` · `work` · `history` 양식의
`YYYY-MM-DD` 자리표시자를 실행 당일 날짜로 바꿔 루트로 복사하고 `docs/` 를 만듭니다.
복사 후 **brainstorming.md 부터** 채우세요.

`troubleshooting.md` 는 상시 추적 파일이 아니라 **필요할 때** 꺼내 쓰는 양식입니다.
시간을 많이 쓴 문제가 생기면 `docs/YYYY-MM-DD_트러블슈팅-제목.md` 로 복사해 기록하세요.
