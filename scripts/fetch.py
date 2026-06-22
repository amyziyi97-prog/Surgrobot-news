#!/usr/bin/env python3
# ════════════════════════════════════════════════════════════
#  fetch.py —— 抓取资讯 → 存入 SQLite → 导出 JSON 给网页
#  一般不用改这个文件;要改源去 sources.py
# ════════════════════════════════════════════════════════════
import sqlite3, json, hashlib, html, re, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import re
from difflib import SequenceMatcher

import feedparser
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from sources import KEYWORDS, RSS_SOURCES, HTML_SOURCES

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "news.db"
JSON_OUT = ROOT / "news.json"
CN_TZ = timezone(timedelta(hours=8))

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}

# ───────────── Email Sending ─────────────
import os, smtplib, ssl
from email.mime.text import MIMEText
from email.header import Header

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
MAIL_TO   = os.environ.get("MAIL_TO", "")

def filter_for_push(items, days=1):
    """推送前处理:① 按链接去重 ② 只保留最近 days 天内发布的。
    注意:只影响推送,数据库和网页仍保存全部抓到的内容。"""
    today = datetime.now(CN_TZ).date()
    seen, out = set(), []
    for it in items:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        try:
            d = datetime.strptime(it["date"], "%Y.%m.%d").date()
            if (today - d).days >= days:   # 超过 days 天的旧闻不推
                continue
        except Exception:
            pass   # 日期格式异常的,保守保留
        out.append(it)
    return out

CAT_CN = {"company":"公司","policy":"政策","market":"市场",
          "tech":"技术","global":"海外","auto":"自动抓取"}
    
def push_email(new_items):
    """有新资讯时,发邮件提醒"""
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and MAIL_TO) or not new_items:
        return
    subject = f"手术机器人资讯 · 新增 {len(new_items)} 条"
    # 拼 HTML 正文:每条一行,可点链接
    rows = []
    for it in new_items[:20]:
        cat_label = CAT_CN.get(it.get("cat", ""), it.get("cat", ""))
        rows.append(
            f'<p style="margin:6px 0"><b>[{it["date"]}]</b> '
            f'<span style="background:#eef;color:#447;padding:1px 6px;'
            f'border-radius:4px;font-size:12px">{cat_label}</span> '
            f'<a href="{it["url"]}">{it["title"]}</a> '
            f'<span style="color:#888">（{it["src"]}）</span></p>'
        )
    body = "<h3>本次新增资讯</h3>" + "".join(rows)
    msg = MIMEText(body, "html", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, 465, context=ctx, timeout=20) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, [MAIL_TO], msg.as_string())
        print(f"  → 已发邮件 ({len(new_items)} 条)")
    except Exception as ex:
        print(f"  ! 邮件推送失败: {ex}")
        
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

def guess_category(title, default_cat):
    """按标题内容判断分类。优先级:出海 > 政策 > 公司/市场 > 技术。
    规则:'公司'只留给精锋自己;同行(微创、真健康等)的商业动态归'市场'。"""
    t = title
    global_kw = ["CE认证","CE标志","获CE","FDA","欧盟","出口","海外","国际化",
                 "走出去","进入美国","进入欧洲","巴西","卢旺达","沙特","意大利",
                 "东南亚","一带一路","NHS","逆向输出","海外订单","海外市场","海外获批"]
    domestic = ["国内首例","省人民医院","市人民医院","中国首例","完成手术","成功实施","临床手术"]
    if any(k in t for k in global_kw) and not any(k in t for k in domestic):
        return "global"

    policy_kw = ["医保","立项指南","集采","国家药监","NMPA","获批上市","纳入",
                 "政策","监管","收费标准","审批","注册证","挂网"]
    if any(k in t for k in policy_kw):
        return "policy"

    # 商业类信号(融资、IPO、营收、股价、订单等)
    biz_kw = ["融资","IPO","上市","递交","招股","营收","财报","亿元","万元",
              "轮融资","订单","中标","战略合作","签约","估值","股份","冲刺","递表",
              "涨超","跌超","回购","业绩"]
    if any(k in t for k in biz_kw):
        return "company" if "精锋" in t else "market"   # ← 只有精锋算公司

    tech_kw = ["专利","研发","技术突破","新一代","力反馈","导航","单孔","柔性","算法"]
    if any(k in t for k in tech_kw):
        return "tech"

    # 兜底:含"精锋"的统一归公司,否则用源默认分类
    if "精锋" in t:
        return "company"
    return default_cat

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
            "cat": guess_category(title, src["cat"]),
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
            "date": date, "cat": guess_category(title, src["cat"]), "title": title,
            "body": "(点链接查看原文)", "src": src["name"], "url": link,
        })
    return out
# ───────────── 去重 ─────────────
def _normalize_title(title):
    """去掉媒体后缀、股票代码、标点,提取核心内容用于相似度比对"""
    t = re.sub(r"\s*[-–—]\s*[^-–—]+$", "", title)   # 去末尾 "- 媒体名"
    t = re.sub(r"\(?\d{5,6}\.?(HK|SH|SZ)?\)?", "", t)  # 去股票代码
    t = re.sub(r"-?[ABH]股?", "", t)                  # 去 -B/-A/H股
    t = re.sub(r"[（）()，,。！!？?：:\u201c\u201d\u2018\u2019\"'\s、]", "", t)
    return t

def dedup_by_content(rows, threshold=0.62):
    """按标题内容相似度去重(同一事件多家媒体只留一条)。
    rows 是 (date,cat,title,body,src,url,is_new) 元组列表。"""
    kept, kept_norm = [], []
    for r in rows:
        norm = _normalize_title(r[2])   # r[2] 是 title
        if any(SequenceMatcher(None, norm, kn).ratio() >= threshold for kn in kept_norm):
            continue
        kept.append(r)
        kept_norm.append(norm)
    return kept
# ───────────── 导出给网页 ─────────────
def export_json(conn):
    rows = conn.execute(
        "SELECT date,cat,title,body,src,url,is_new FROM news "
        "ORDER BY date DESC, fetched_at DESC LIMIT 200"
    ).fetchall()
    rows = dedup_by_content(rows)   # ← 新增:导出前按内容去重
    
    today = datetime.now(CN_TZ).date()
    def _is_new(date_str, days=3):
        parts = date_str.split(".")
        if len(parts) < 3:
            return False          # 只到月份的旧闻不算新
        try:
            d = datetime(int(parts[0]), int(parts[1]), int(parts[2])).date()
            return 0 <= (today - d).days <= days
        except Exception:
            return False

    data = [{
        "date": r[0], "cat": r[1], "title": r[2], "body": r[3],
        "src": r[4], "url": r[5], "isNew": _is_new(r[0]),
        "major": False,
    } for r in rows]
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  → 导出 {len(data)} 条到 {JSON_OUT.name}")


def main():
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    # 每次抓取前,把超过7天的 is_new 清掉(去掉 NEW 角标)
    # week_ago = (datetime.now(CN_TZ) - timedelta(days=7)).isoformat()
   # conn.execute("UPDATE news SET is_new=0 WHERE fetched_at < ?", (week_ago,))

    new_items = []
    for src in RSS_SOURCES:
        print(f"· RSS  {src['name']}")
        for item in fetch_rss(src):
            if upsert(conn, item):
                new_items.append(item)
        time.sleep(1)

    for src in HTML_SOURCES:
        print(f"· HTML {src['name']}")
        for item in fetch_html(src):
            if upsert(conn, item):
                new_items.append(item)
        time.sleep(1)
    total_new = len(new_items)

    conn.commit()
    export_json(conn)
    conn.close()
    push_items = filter_for_push(new_items, days=1)
    push_email(push_items)    
    print(f"✓ 本次新增 {total_new} 条")


if __name__ == "__main__":
    main()
