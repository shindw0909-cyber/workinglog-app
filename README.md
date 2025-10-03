# 업무 리스트 정리 프로그램 (Worklog → 고객별 정리)

비전공자도 바로 쓸 수 있는 **하루 업무 기록 → 고객별 자동 분류** 앱입니다.

## 두 가지 사용 방법
1) **브라우저 앱 (추천)** — Streamlit 실행  
2) **명령행 빠른 기록** — CLI 스크립트

---

## 1) 브라우저 앱 (Streamlit)

### 설치
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

### 실행
```bash
streamlit run app.py
```

브라우저에서 열리면 왼쪽 사이드바로 이동합니다:
- **Add Entry**: 오늘 만난 고객/업무를 기록
- **Browse by Customer**: 고객별 누적 기록 보기 (필터/정렬 가능)
- **Daily Log**: 날짜별로 오늘 한 일 확인
- **Search & Export**: 키워드 검색 + CSV/Excel 내보내기

> DB 파일: `worklog.db` (같은 폴더에 생성). 깃/백업 시 포함하세요.

---

## 2) 명령행 기록 (CLI)

### 빠른 추가
```bash
python cli.py add --customer "현대차" --contact "김대리" \
  --summary "전동액슬 윤활유 BlueV 제안" \
  --actions "TDS/권장점도 송부" \
  --next "다음 주 샘플 테스트 일정 확인" \
  --tags "EV,윤활유"
```

### 날짜 지정
```bash
python cli.py add --date 2025-10-02 --customer "NEXVEL" --summary "BLDC 샤프트 anti-creep"
```

### 검색/내보내기
```bash
python cli.py search --q "BlueV"
python cli.py export --format xlsx --out export.xlsx
```

---

## 데이터 항목(필드)
- **date**: YYYY-MM-DD (기본값: 오늘)
- **customer**: 고객사명(필수)
- **contact**: 상대 담당자명/직책
- **summary**: 오늘 진행 요약 (필수)
- **actions**: 오늘 한 일 (불릿/문장 자유)
- **next_steps**: 다음 액션/To‑Do
- **tags**: 쉼표로 구분 (예: EV,샘플,품질이슈)

---

## 팁
- 고객사 표기를 일관되게(예: '현대차' vs '현대자동차') 하면 검색/집계가 깔끔해집니다.
- **Search & Export** 페이지에서 Excel로 내보내 팀 공유 리포트를 바로 만들 수 있어요.
- 나중에 필요한 필드를 추가하려면 `init_db()` 의 스키마와 관련 쿼리만 업데이트하면 됩니다.

행복한 자동화 🙌
