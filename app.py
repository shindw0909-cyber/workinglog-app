
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta
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

_check_password()

# ---------------- DB ----------------
def init_db():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        # base table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            customer TEXT NOT NULL,
            project TEXT,
            contact TEXT,
            summary TEXT NOT NULL,
            actions TEXT,
            next_steps TEXT,
            tags TEXT,
            created_at TEXT NOT NULL
        )
        """)
        con.commit()
        # add missing columns for upgrades
        cur.execute("PRAGMA table_info(entries)")
        cols = {row[1] for row in cur.fetchall()}
        if "project" not in cols:
            cur.execute("ALTER TABLE entries ADD COLUMN project TEXT")
        con.commit()
        # helpful indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_date ON entries(date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_customer ON entries(customer)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_project ON entries(project)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tags ON entries(tags)")
        con.commit()

def insert_entry(e):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO entries (date, customer, project, contact, summary, actions, next_steps, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            e["date"], e["customer"], e.get("project",""), e.get("contact",""), e["summary"],
            e.get("actions",""), e.get("next_steps",""), e.get("tags",""),
            datetime.now().isoformat(timespec="seconds")
        ))
        con.commit()

def fetch_df(query="SELECT * FROM entries ORDER BY date DESC, id DESC", params=()):
    with sqlite3.connect(DB_PATH) as con:
        df = pd.read_sql_query(query, con, params=params)
    return df

def search_entries(q):
    like = f"%{q}%"
    sql = """
    SELECT * FROM entries
    WHERE date LIKE ? OR customer LIKE ? OR project LIKE ? OR contact LIKE ?
       OR summary LIKE ? OR actions LIKE ? OR next_steps LIKE ? OR tags LIKE ?
    ORDER BY date DESC, id DESC
    """
    return fetch_df(sql, (like, like, like, like, like, like, like, like))

def get_distinct(field):
    df = fetch_df(f"SELECT DISTINCT {field} FROM entries WHERE IFNULL({field},'')<>'' ORDER BY {field} ASC")
    return sorted(df[field].dropna().tolist())

# -------------- UI Helpers --------------
def entry_form():
    st.subheader("새 업무 기록 추가")
    col1, col2 = st.columns(2)
    with col1:
        d = st.date_input("날짜", value=date.today(), format="YYYY-MM-DD")
        customer = st.text_input("고객사 *", placeholder="예: 현대차 / NEXVEL / LS오토모티브")
        # project quick-pick or free text
        existing = [""] + get_distinct("project")
        project = st.selectbox("프로젝트(선택)", existing, index=0, help="기존 목록에서 선택하거나 아래에 새 프로젝트명을 입력하세요.")
        new_project = st.text_input("새 프로젝트명(없으면 비워두기)", placeholder="예: BlueV 전동액슬 적용 / BLDC 샤프트 코팅")
        project = new_project.strip() if new_project.strip() else project.strip()
    with col2:
        contact = st.text_input("담당자/직책", placeholder="예: 김대리 / 구매팀")
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
            "project": project,
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
    st.subheader("Customer Overview (고객사별 히스토리)")
    customers = get_distinct("customer")
    if not customers:
        st.info("먼저 기록을 추가하세요.")
        return
    cust = st.selectbox("고객 선택", customers, index=0)
    df = fetch_df("SELECT * FROM entries WHERE customer=? ORDER BY date DESC, id DESC", (cust,))
    st.caption(f"총 {len(df)}건")
    st.dataframe(df, use_container_width=True)

    st.markdown("### 고객사 내 프로젝트 요약")
    if not df.empty:
        tmp = df.copy()
        tmp["last_activity"] = pd.to_datetime(tmp["date"])
        agg = tmp.groupby(tmp["project"].fillna("").replace("", "(프로젝트 미지정)")).agg(
            entries=("id","count"),
            last_date=("last_activity","max"),
        ).reset_index().rename(columns={"project":"project"})
        # days since
        agg["days_since"] = (pd.Timestamp.today().normalize() - agg["last_date"]).dt.days
        st.dataframe(agg.sort_values(["days_since","project"]), use_container_width=True)

def page_project():
    st.subheader("Project Overview (프로젝트별 진행상황)")
    projects = get_distinct("project")
    if not projects:
        st.info("프로젝트가 아직 없습니다. 기록 추가 시 프로젝트명을 입력해보세요.")
        return
    proj = st.selectbox("프로젝트 선택", projects, index=0)
    df = fetch_df("SELECT * FROM entries WHERE project=? ORDER BY date DESC, id DESC", (proj,))
    st.caption(f"총 {len(df)}건")
    st.dataframe(df, use_container_width=True)

    # Timeline / last activity / upcoming
    st.markdown("### 프로젝트 스냅샷")
    if not df.empty:
        last_date = pd.to_datetime(df["date"]).max()
        last_summary = df.loc[pd.to_datetime(df["date"]).idxmax(), "summary"]
        open_next = df[df["next_steps"].str.len()>0]["next_steps"].head(5).tolist()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("마지막 활동일", str(last_date.date()))
            st.write("**마지막 활동 요약**")
            st.write(last_summary)
        with col2:
            st.write("**다음 액션(상위 5)**")
            if open_next:
                for i, n in enumerate(open_next, 1):
                    st.write(f"- {n}")
            else:
                st.write("등록된 다음 액션이 없습니다.")

def page_search_export():
    st.subheader("Search & Export (검색/내보내기)")
    q = st.text_input("검색어", placeholder="고객, 프로젝트, 담당자, 요약/액션/다음액션, 태그에서 검색")
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
    st.set_page_config(page_title="업무 리스트 정리 (프로젝트 트래커)", layout="wide")
    init_db()
    st.sidebar.title("업무 정리 도우미")
    page = st.sidebar.radio("메뉴", ["Add Entry", "Customer Overview", "Project Overview", "Daily Log", "Search & Export"])
    if page == "Add Entry":
        entry_form()
    elif page == "Customer Overview":
        page_customer()
    elif page == "Project Overview":
        page_project()
    elif page == "Daily Log":
        page_daily()
    else:
        page_search_export()

    st.sidebar.markdown("---")
    st.sidebar.caption("Made with ❤️ by GPT + You")

if __name__ == "__main__":
    main()
