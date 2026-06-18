#!/usr/bin/env python3
# ════════════════════════════════════════════════════════════
#  search.py —— 命令行检索数据库里的资讯
#  用法:  python scripts/search.py 远程手术
#         python scripts/search.py "医保 OR 立项"
# ════════════════════════════════════════════════════════════
import sqlite3, sys
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "news.db"

def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/search.py 关键词")
        return
    query = " ".join(sys.argv[1:])
    conn = sqlite3.connect(DB)
    # trigram 分词器需要查询词≥3字符;更短的词回退到 LIKE 模糊匹配
    if len(query.replace(" ", "")) >= 3 and " " not in query:
        rows = conn.execute("""
            SELECT n.date, n.cat, n.title, n.src, n.url
            FROM news_fts f JOIN news n ON n.rowid = f.rowid
            WHERE news_fts MATCH ? ORDER BY rank LIMIT 30
        """, (query,)).fetchall()
    else:
        like = f"%{query}%"
        rows = conn.execute("""
            SELECT date, cat, title, src, url FROM news
            WHERE title LIKE ? OR body LIKE ?
            ORDER BY date DESC LIMIT 30
        """, (like, like)).fetchall()
    if not rows:
        print(f"没找到含「{query}」的资讯")
        return
    print(f"\n找到 {len(rows)} 条含「{query}」的资讯:\n" + "─" * 50)
    for d, cat, title, src, url in rows:
        print(f"[{d}] ({cat}) {title}\n   {src} · {url}\n")
    conn.close()

if __name__ == "__main__":
    main()
