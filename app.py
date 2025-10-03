
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
from pathlib import Path

DB_PATH = Path(__file__).with_name("worklog.db")

# ---------------- Password Gate (via Secrets) ----------------
def _check_password():
    def _pw_entered():
        if st.session_state.get("pw", "") == st.secrets.get("APP_PASSWORD"):
            st.session_state["auth_ok"] = True
            st.session_state.pop("pw", None)
        else:
            st.session_state["auth_ok"] = False

    if st.session_state.get("auth_ok"):
        return True

    st.title("업무 정리 앱 🔐")
    st.caption("접속에는 비밀번호가 필요합니다.")
    st.text_input("비밀번호", type="password", key="pw", on_change=_pw_entered)
    if "auth_ok" in st.session_state and not st.session_state["auth_ok"]:
        st.error("비밀번호가 틀렸습니다.")
    st.stop()

# Call password gate BEFORE any content renders
_check_password()

# ---------------- DB ----------------
def init_db():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            customer TEXT NOT NULL,
            contact TEXT,
            summary TEXT NOT NULL,
            actions TEXT,
            next_steps TEXT,
            tags TEXT,
            created_at TEXT NOT NULL
        )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_date ON entries(date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_customer ON entries(customer)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tags ON entries(tags)")
        con.commit()

def insert_entry(e):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO entries (date, customer, contact, summary, actions, next_steps, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            e["date"], e["customer"], e.get("contact",""), e["summary"], e.get("actions",""),
            e.get("next_steps",""), e.get("tags",""),
            datetime.now().isoformat(timespec="seconds")
        ))
        con.commit()

def fetch_df(query="SELECT * FROM entries ORDER BY date DESC, id DESC", params=()):
    with sqlite3.connect(DB_PATH) as con:
        import pandas as pd
        df = pd.read_sql_query(query, con, params=params)
    return df

def search_entries(q):
    like = f"%{q}%"
    sql = """
    SELECT * FROM entries
    WHERE date LIKE ? OR customer LIKE ? OR contact LIKE ?
       OR summary LIKE ? OR actions LIKE ? OR next_steps LIKE ?
       OR tags LIKE ?
    ORDER BY date DESC, id DESC
    """
    return fetch_df(sql, (like, like, like, like, like, like, like))

def get_customers():
    df = fetch_df("SELECT DISTINCT customer FROM entries ORDER BY customer ASC")
    return sorted(df["customer"].dropna().tolist())

# -------------- UI Helpers --------------
def entry_form():
    st.subheader("새 업무 기록 추가")
    col1, col2 = st.columns(2)
    with col1:
        d = st.date_input("날짜", value=date.today(), format="YYYY-MM-DD")
        customer = st.text_input("고객사 *", placeholder="예: 현대차 / NEXVEL / LS오토모티브")
        contact = st.text_input("담당자/직책", placeholder="예: 김대리 / 구매팀")
    with col2:
        tags = st.text_input("태그(쉼표 구분)", placeholder="예: EV,샘플,윤활유")

    summary = st.text_area("오늘 진행 요약 *", height=120, placeholder="무엇을, 왜, 어떻게 진행했는지 한 문단으로")
    actions = st.text_area("오늘 한 일", height=120, placeholder="- 자료 송부\n- 샘플 의뢰\n- 전화 미팅")
    next_steps = st.text_area("다음 액션", height=100, placeholder="- 다음 주 테스트 동행\n- 단가/납기 회신 요청")

    if st.button("저장", type="primary", use_container_width=True):
        if not customer.strip():
            st.error("고객사는 필수입니다.")
            return
        if not summary.strip():
            st.error("진행 요약은 필수입니다.")
            return
        insert_entry({
            "date": d.strftime("%Y-%m-%d"),
            "customer": customer.strip(),
            "contact": contact.strip(),
            "summary": summary.strip(),
            "actions": actions.strip(),
            "next_steps": next_steps.strip(),
            "tags": tags.strip()
        })
        st.success("저장되었습니다 ✅")

def page_daily():
    st.subheader("Daily Log (날짜별)")
    d = st.date_input("날짜 선택", value=date.today(), format="YYYY-MM-DD")
    df = fetch_df("SELECT * FROM entries WHERE date=? ORDER BY id DESC", (d.strftime("%Y-%m-%d"),))
    if df.empty:
        st.info("이 날짜의 기록이 없습니다.")
        return
    st.dataframe(df, use_container_width=True)

def page_customer():
    st.subheader("Browse by Customer (고객별 보기)")
    customers = get_customers()
    if not customers:
        st.info("아직 고객 데이터가 없습니다. 먼저 Add Entry에서 기록을 추가하세요.")
        return
    col1, col2 = st.columns([2,1])
    with col1:
        cust = st.selectbox("고객 선택", customers, index=0)
    df = fetch_df("SELECT * FROM entries WHERE customer=? ORDER BY date DESC, id DESC", (cust,))
    st.caption(f"총 {len(df)}건")
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.write("**요약 리포트**")
    if not df.empty:
        tmp = df.copy()
        tmp["month"] = pd.to_datetime(tmp["date"]).dt.to_period("M").astype(str)
        pivot = tmp.groupby("month")["id"].count().reset_index().rename(columns={"id":"entries"})
        st.dataframe(pivot, use_container_width=True)

def page_search_export():
    st.subheader("Search & Export (검색/내보내기)")
    q = st.text_input("검색어", placeholder="고객, 담당자, 요약/액션/다음액션, 태그에서 검색")
    if q:
        df = search_entries(q)
    else:
        df = fetch_df()
    st.caption(f"검색 결과: {len(df)}건")
    st.dataframe(df, use_container_width=True, height=400)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("CSV로 내보내기", use_container_width=True):
            df.to_csv("export.csv", index=False, encoding="utf-8-sig")
            st.success("export.csv 로 저장 완료.")
    with col2:
        if st.button("Excel(xlsx)로 내보내기", use_container_width=True):
            df.to_excel("export.xlsx", index=False)
            st.success("export.xlsx 로 저장 완료.")

# -------------- Main --------------
def main():
    st.set_page_config(page_title="업무 리스트 정리", layout="wide")
    init_db()
    st.sidebar.title("업무 정리 도우미")
    page = st.sidebar.radio("메뉴", ["Add Entry", "Browse by Customer", "Daily Log", "Search & Export"])
    if page == "Add Entry":
        entry_form()
    elif page == "Browse by Customer":
        page_customer()
    elif page == "Daily Log":
        page_daily()
    else:
        page_search_export()

    st.sidebar.markdown("---")
    st.sidebar.caption("Made with ❤️ by GPT + You")

if __name__ == "__main__":
    main()
