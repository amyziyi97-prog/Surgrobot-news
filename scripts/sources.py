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

# 放宽了一些,让更多相关资讯能进来
KEYWORDS = [
    "手术机器人", "精锋", "腔镜", "达芬奇", "微创机器人",
    "单孔", "多孔", "内窥镜", "内镜", "远程手术", "医保",
    "立项指南", "支气管镜", "骨科机器人", "Intuitive",
    "Edge Medical", "思哲睿", "术锐", "微创医疗", "机器人手术"
]

# ── RSS 源:谷歌新闻按关键词监控,等于帮你全网盯这些词 ──
# 分类:company公司 / policy政策 / market市场 / tech技术 / global出海
RSS_SOURCES = [
    {"name":"谷歌·手术机器人","cat":"market",
     "url":"https://news.google.com/rss/search?q=%E6%89%8B%E6%9C%AF%E6%9C%BA%E5%99%A8%E4%BA%BA&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"},
    {"name":"谷歌·精锋医疗","cat":"company",
     "url":"https://news.google.com/rss/search?q=%E7%B2%BE%E9%94%8B%E5%8C%BB%E7%96%97&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"},
    {"name":"谷歌·腔镜机器人","cat":"tech",
     "url":"https://news.google.com/rss/search?q=%E8%85%94%E9%95%9C%E6%9C%BA%E5%99%A8%E4%BA%BA&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"},
    {"name":"谷歌·达芬奇手术","cat":"global",
     "url":"https://news.google.com/rss/search?q=%E8%BE%BE%E8%8A%AC%E5%A5%87%E6%89%8B%E6%9C%AF&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"},
    {"name":"谷歌·微创机器人","cat":"company",
     "url":"https://news.google.com/rss/search?q=%E5%BE%AE%E5%88%9B%E6%9C%BA%E5%99%A8%E4%BA%BA&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"},
    {"name":"谷歌·单孔机器人","cat":"tech",
     "url":"https://news.google.com/rss/search?q=%E5%8D%95%E5%AD%94%E6%9C%BA%E5%99%A8%E4%BA%BA&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"},
    {"name":"谷歌·远程手术","cat":"policy",
     "url":"https://news.google.com/rss/search?q=%E8%BF%9C%E7%A8%8B%E6%89%8B%E6%9C%AF&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"},
    {"name":"谷歌·支气管镜机器人","cat":"tech",
     "url":"https://news.google.com/rss/search?q=%E6%94%AF%E6%B0%94%E7%AE%A1%E9%95%9C%E6%9C%BA%E5%99%A8%E4%BA%BA&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"},
    {"name":"谷歌·手术机器人+医保","cat":"policy",
     "url":"https://news.google.com/rss/search?q=%E6%89%8B%E6%9C%AF%E6%9C%BA%E5%99%A8%E4%BA%BA%20%E5%8C%BB%E4%BF%9D&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"},
]

# ── HTML 源:没有 RSS 的网站,需填 CSS 选择器(暂时空着) ──
HTML_SOURCES = []
