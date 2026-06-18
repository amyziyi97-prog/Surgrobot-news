# ════════════════════════════════════════════════════════════
#  资讯源配置 —— 想加/删源,只改这个文件就够了
# ════════════════════════════════════════════════════════════
#
#  两种源:
#  - rss:  有 RSS 订阅地址的(最省心,推荐优先用)
#  - html: 没有 RSS、需要从网页里抓的(要填 CSS 选择器)
#
#  关键词过滤:只有标题/摘要里命中 KEYWORDS 里任意一个词的,才会入库,
#  避免抓进一堆无关新闻。
# ════════════════════════════════════════════════════════════

# 只保留命中这些关键词的资讯(命中任意一个即可)
KEYWORDS = [
    "手术机器人", "精锋", "腔镜机器人", "达芬奇", "微创机器人",
    "单孔", "多孔", "内窥镜", "远程手术", "医保局", "立项指南",
    "Intuitive", "Edge Medical", "康诺思腾", "术锐",
]

# ── RSS 源:填 名称 + RSS地址 + 默认分类 ──
# 分类可选:company公司 / policy政策 / market市场 / tech技术 / global出海
RSS_SOURCES = [
    # 谷歌新闻按关键词生成的 RSS(最实用,等于帮你全网监控关键词)
    {
        "name": "谷歌新闻·手术机器人",
        "url": "https://news.google.com/rss/search?q=%E6%89%8B%E6%9C%AF%E6%9C%BA%E5%99%A8%E4%BA%BA&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "cat": "market",
    },
    {
        "name": "谷歌新闻·精锋医疗",
        "url": "https://news.google.com/rss/search?q=%E7%B2%BE%E9%94%8B%E5%8C%BB%E7%96%97&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "cat": "company",
    },
    # 想加别的关键词,把上面 q= 后面那串换成你的词的 URL 编码即可。
    # 偷懒办法:浏览器打开 news.google.com 搜你的词,点 RSS,复制地址。
]

# ── HTML 源:没有 RSS 的网站,从列表页直接抓 ──
# selector_item: 每条新闻的容器; selector_title/_link/_date: 容器内取标题/链接/日期
HTML_SOURCES = [
    # 示例(国家医保局政策动态页,结构可能变,以实际为准):
    # {
    #     "name": "国家医保局·医保动态",
    #     "url": "https://www.nhsa.gov.cn/col/col14/index.html",
    #     "cat": "policy",
    #     "selector_item": "ul.list li",
    #     "selector_title": "a",
    #     "selector_link": "a",
    #     "selector_date": "span.date",
    #     "base_url": "https://www.nhsa.gov.cn",   # 相对链接补全用
    # },
]
