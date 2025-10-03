
import argparse
import sqlite3
from datetime import date, datetime
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).with_name("worklog.db")

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
        con.commit()

def add_entry(args):
    init_db()
    d = args.date or date.today().strftime("%Y-%m-%d")
    created_at = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO entries (date, customer, contact, summary, actions, next_steps, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            d, args.customer, args.contact or "", args.summary or "",
            args.actions or "", args.next or "", args.tags or "", created_at
        ))
        con.commit()
    print("✅ Saved:", d, args.customer)

def search(args):
    init_db()
    like = f"%{args.q}%"
    sql = """
    SELECT * FROM entries
    WHERE date LIKE ? OR customer LIKE ? OR contact LIKE ?
       OR summary LIKE ? OR actions LIKE ? OR next_steps LIKE ?
       OR tags LIKE ?
    ORDER BY date DESC, id DESC
    """
    with sqlite3.connect(DB_PATH) as con:
        df = pd.read_sql_query(sql, con, params=(like,)*7)
    print(df.to_string(index=False))

def export(args):
    init_db()
    with sqlite3.connect(DB_PATH) as con:
        df = pd.read_sql_query("SELECT * FROM entries ORDER BY date DESC, id DESC", con)
    out = args.out or ("export.xlsx" if args.format=="xlsx" else "export.csv")
    if args.format == "xlsx":
        df.to_excel(out, index=False)
    else:
        df.to_csv(out, index=False, encoding="utf-8-sig")
    print("📦 Exported ->", out)

def main():
    parser = argparse.ArgumentParser(description="Worklog → Customer organizer CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="기록 추가")
    p_add.add_argument("--date", help="YYYY-MM-DD (기본: 오늘)")
    p_add.add_argument("--customer", required=True)
    p_add.add_argument("--contact")
    p_add.add_argument("--summary")
    p_add.add_argument("--actions")
    p_add.add_argument("--next", help="next_steps")
    p_add.add_argument("--tags")
    p_add.set_defaults(func=add_entry)

    p_search = sub.add_parser("search", help="검색")
    p_search.add_argument("--q", required=True)
    p_search.set_defaults(func=search)

    p_export = sub.add_parser("export", help="CSV/Excel 내보내기")
    p_export.add_argument("--format", choices=["csv","xlsx"], default="xlsx")
    p_export.add_argument("--out")
    p_export.set_defaults(func=export)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
