# 手术机器人资讯台 · 自动更新版

每天自动抓取手术机器人 / 精锋医疗相关资讯,存进数据库(可检索),并发布成一个网页。
**全程免费,跑在 GitHub 上,不用买服务器,配置一次后零维护。**

---

## 它怎么运作

GitHub 每天定时运行一个 Python 脚本 → 抓取你配置的资讯源 → 命中关键词的存进 `news.db`(SQLite 数据库)→ 导出 `news.json` → 网页读取并展示。

---

## 部署步骤(照着做,约 15 分钟)

### 第 1 步:建一个 GitHub 仓库
1. 注册 / 登录 [github.com](https://github.com)(免费)。
2. 点右上角 **+ → New repository**,起个名字(如 `surgrobot-news`),选 **Public**,创建。

### 第 2 步:上传这些文件
把本文件夹里的所有内容,保持目录结构上传到仓库。最简单的办法:
- 仓库页面点 **Add file → Upload files**,把整个文件夹拖进去。

目录结构应该长这样:
```
你的仓库/
├── .github/workflows/fetch.yml   ← 定时任务
├── scripts/
│   ├── fetch.py                  ← 抓取主脚本
│   ├── sources.py                ← 资讯源配置(你主要改这个)
│   ├── search.py                 ← 命令行检索
│   └── requirements.txt
├── site/
│   ├── index.html                ← 网页
│   └── news.json                 ← 自动生成,初始为空
├── news.db                       ← 数据库,初始为空
└── README.md
```

### 第 3 步:打开网页托管(GitHub Pages)
1. 仓库 **Settings → Pages**。
2. **Source** 选 `Deploy from a branch`,Branch 选 `main` + `/site` 文件夹(若没有 /site 选项,选 `main /root` 也行,见下方备注),保存。
3. 等一两分钟,页面顶部会出现你的网址,形如
   `https://你的用户名.github.io/surgrobot-news/`
   这就是你随时能打开看的资讯台。

> 备注:若 Pages 只让选 `/root` 不让选 `/site`,把 `site/` 里的 `index.html` 和 `news.json` 移到仓库根目录即可。

### 第 4 步:让定时任务能提交
1. 仓库 **Settings → Actions → General**。
2. 拉到最下 **Workflow permissions**,选 **Read and write permissions**,保存。
   (这样机器人才能把抓到的新资讯提交回仓库。)

### 第 5 步:先手动跑一次试试
1. 仓库 **Actions** 标签 → 左侧选 **抓取资讯并更新** → 右侧 **Run workflow**。
2. 跑完(绿勾)后,刷新你的网页,应该能看到抓取到的资讯了。
3. 之后它每天北京时间早上 9 点自动跑,你什么都不用做。

---

## 怎么加 / 改资讯源

只改 `scripts/sources.py` 一个文件:

**加关键词监控(最简单,推荐)** —— 用谷歌新闻 RSS:
浏览器打开 `news.google.com`,搜你想监控的词,在结果页找到 RSS 链接复制,
照着 `sources.py` 里 `RSS_SOURCES` 的格式加一条即可。等于帮你全网监控这个词。

**改抓取频率** —— 改 `.github/workflows/fetch.yml` 里的 `cron`:
- `"0 1 * * *"` = 每天一次(UTC 1点 = 北京 9点)
- `"0 1,9 * * *"` = 每天两次(北京 9点 和 17点)

**改过滤关键词** —— `sources.py` 顶部的 `KEYWORDS` 列表,只有命中的才入库。

---

## 怎么检索数据库

数据库是标准 SQLite,支持中文全文搜索。本地装好 Python 后:

```bash
python scripts/search.py 远程手术
python scripts/search.py 医保
python scripts/search.py CE认证
```

或者用任何 SQLite 工具(如免费的 [DB Browser for SQLite](https://sqlitebrowser.org/))打开 `news.db`,
直接写 SQL 查,例如:
```sql
SELECT date, title, src, url FROM news
WHERE title LIKE '%精锋%' ORDER BY date DESC;
```

---

## 常见问题

**Q:抓取跑了但网页没更新?**
A:GitHub Pages 有缓存,等几分钟或强制刷新(Ctrl+F5)。

**Q:谷歌新闻 RSS 在国内打不开会影响吗?**
A:不影响。抓取是在 GitHub 的服务器(海外)上跑的,不受你本地网络限制。你只是用浏览器看最终网页。

**Q:想抓某个没有 RSS 的网站(如医保局)?**
A:用 `sources.py` 里 `HTML_SOURCES` 的格式,填 CSS 选择器。不太会写选择器的话,把目标网址发我,我帮你配。

**Q:免费额度够用吗?**
A:GitHub Actions 公开仓库完全免费、无限分钟数;Pages 也免费。每天跑一次绰绰有余。

---

## 想升级?

- **推送到微信/邮箱**:在 `fetch.py` 末尾加一段,有新增时调用 Server酱(微信)或 SMTP(邮件)。
- **更强的中文分词检索**:把 SQLite 换成带中文分词的方案,或接入 Postgres 全文检索。
- **多人协作 / 真数据库**:升级到 B 档(Supabase + Vercel)。

