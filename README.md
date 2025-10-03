
# 업무 정리 앱 v2 — 고객사/프로젝트 히스토리 트래커 (보안)

## 새 기능
- `project` 필드 추가 (선택적) — 기존 목록에서 선택하거나 새 프로젝트명 입력
- **Customer Overview**: 고객사 내 프로젝트별 활동 집계(마지막 활동일, 건수)
- **Project Overview**: 프로젝트별 타임라인/마지막 활동/다음 액션 요약
- 기존 페이지: Add Entry, Daily Log, Search & Export

## 비밀번호 게이트
Streamlit **Secrets**에 아래를 저장하고 Redeploy:
```
APP_PASSWORD = "Alfnwlakfwk1!"
```

## 업그레이드/마이그레이션
- 앱이 자동으로 `project` 컬럼 존재 여부를 확인 후 없으면 `ALTER TABLE`로 추가합니다.
- DB 파일은 `.gitignore`에 의해 GitHub에 업로드되지 않습니다.
