#!/usr/bin/env python3
# ════════════════════════════════════════════════════════════
#  fetch.py —— 抓取资讯 → 存入 SQLite → 导出 JSON 给网页
#  一般不用改这个文件;要改源去 sources.py
# ════════════════════════════════════════════════════════════
import sqlite3, json, hashlib, html, re, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from sources import KEYWORDS, RSS_SOURCES, HTML_SOURCES

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "news.db"
JSON_OUT = ROOT / "site" / "news.json"
CN_TZ = timezone(timedelta(hours=8))

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}


# ───────────── 数据库 ─────────────
def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id        TEXT PRIMARY KEY,   -- 链接的哈希,用于去重
            date      TEXT,               -- YYYY.MM.DD
            cat       TEXT,
            title     TEXT,
            body      TEXT,
            src       TEXT,
            url       TEXT,
            is_new    INTEGER DEFAULT 1,
            fetched_at TEXT
        )
    """)
    # 全文搜索表(让你能 SQL 检索标题+正文)
    # 用 trigram 分词器:能正确处理中文(默认分词器不切中文,搜不到)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS news_fts
        USING fts5(title, body, content='news', content_rowid='rowid',
                   tokenize='trigram')
    """)
    conn.commit()


def hit_keywords(text):
    return any(k in text for k in KEYWORDS)


def clean(text):
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", "", text)        # 去 HTML 标签
    text = re.sub(r"\s+", " ", text).strip()
    return text


def to_date(struct_or_str):
    """把各种时间格式统一成 YYYY.MM.DD"""
    try:
        if hasattr(struct_or_str, "tm_year"):
            dt = datetime(*struct_or_str[:6], tzinfo=timezone.utc).astimezone(CN_TZ)
            return dt.strftime("%Y.%m.%d")
    except Exception:
        pass
    return datetime.now(CN_TZ).strftime("%Y.%m.%d")


def upsert(conn, item):
    """插入一条;已存在(同链接)就跳过。返回是否为新增。"""
    uid = hashlib.sha1(item["url"].encode("utf-8")).hexdigest()[:16]
    cur = conn.execute("SELECT 1 FROM news WHERE id=?", (uid,))
    if cur.fetchone():
        return False
    conn.execute(
        "INSERT INTO news (id,date,cat,title,body,src,url,is_new,fetched_at) "
        "VALUES (?,?,?,?,?,?,?,1,?)",
        (uid, item["date"], item["cat"], item["title"], item["body"],
         item["src"], item["url"], datetime.now(CN_TZ).isoformat()),
    )
    rowid = conn.execute("SELECT rowid FROM news WHERE id=?", (uid,)).fetchone()[0]
    conn.execute("INSERT INTO news_fts(rowid,title,body) VALUES (?,?,?)",
                 (rowid, item["title"], item["body"]))
    return True


# ───────────── 抓取 ─────────────
def fetch_rss(src):
    out = []
    feed = feedparser.parse(src["url"])
    for e in feed.entries[:30]:
        title = clean(e.get("title", ""))
        body = clean(e.get("summary", ""))[:280]
        if not hit_keywords(title + body):
            continue
        out.append({
            "date": to_date(e.get("published_parsed")),
            "cat": src["cat"],
            "title": title,
            "body": body or "(点链接查看原文)",
            "src": src["name"],
            "url": e.get("link", ""),
        })
    return out


def fetch_html(src):
    out = []
    try:
        r = requests.get(src["url"], headers=HEADERS, timeout=20)
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as ex:
        print(f"  ! HTML 抓取失败 {src['name']}: {ex}")
        return out

    for node in soup.select(src["selector_item"])[:30]:
        t_el = node.select_one(src["selector_title"])
        l_el = node.select_one(src["selector_link"])
        if not t_el or not l_el:
            continue
        title = clean(t_el.get_text())
        link = l_el.get("href", "")
        if link and not link.startswith("http"):
            link = src.get("base_url", "").rstrip("/") + "/" + link.lstrip("/")
        date = datetime.now(CN_TZ).strftime("%Y.%m.%d")
        if src.get("selector_date"):
            d_el = node.select_one(src["selector_date"])
            if d_el:
                raw = clean(d_el.get_text())
                m = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", raw)
                if m:
                    date = f"{m[1]}.{int(m[2]):02d}.{int(m[3]):02d}"
        if not hit_keywords(title):
            continue
        out.append({
            "date": date, "cat": src["cat"], "title": title,
            "body": "(点链接查看原文)", "src": src["name"], "url": link,
        })
    return out


# ───────────── 导出给网页 ─────────────
def export_json(conn):
    rows = conn.execute(
        "SELECT date,cat,title,body,src,url,is_new FROM news "
        "ORDER BY date DESC, fetched_at DESC LIMIT 200"
    ).fetchall()
    data = [{
        "date": r[0], "cat": r[1], "title": r[2], "body": r[3],
        "src": r[4], "url": r[5], "isNew": bool(r[6]),
        "major": False,
    } for r in rows]
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  → 导出 {len(data)} 条到 {JSON_OUT.name}")


def main():
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    # 每次抓取前,把超过7天的 is_new 清掉(去掉 NEW 角标)
    week_ago = (datetime.now(CN_TZ) - timedelta(days=7)).isoformat()
    conn.execute("UPDATE news SET is_new=0 WHERE fetched_at < ?", (week_ago,))

    total_new = 0
    for src in RSS_SOURCES:
        print(f"· RSS  {src['name']}")
        for item in fetch_rss(src):
            if upsert(conn, item):
                total_new += 1
        time.sleep(1)

    for src in HTML_SOURCES:
        print(f"· HTML {src['name']}")
        for item in fetch_html(src):
            if upsert(conn, item):
                total_new += 1
        time.sleep(1)

    conn.commit()
    export_json(conn)
    conn.close()
    print(f"✓ 本次新增 {total_new} 条")


if __name__ == "__main__":
    main()
