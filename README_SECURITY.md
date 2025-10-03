
# 보안 설정 가이드

## 1) 비밀번호 게이트 (Secrets)
Streamlit Cloud 앱의 **Settings → Secrets** 에 아래 항목을 추가하고 저장하세요:

```
APP_PASSWORD = "Alfnwlakfwk1!"
```

저장 후 **Redeploy** 하면, 접속 시 비밀번호 창이 표시됩니다.

## 2) DB 비공개
`.gitignore`에 `worklog.db`가 포함되어 있어 GitHub에 업로드되지 않습니다.
이미 올렸다면 GitHub에서 해당 파일을 삭제한 뒤 커밋하세요.

## 3) 저장소 공개/비공개
민감한 코드/설정이 있다면 GitHub 저장소를 **Private**으로 전환하세요.
