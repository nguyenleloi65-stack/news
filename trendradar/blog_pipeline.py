# coding=utf-8
"""每日博客生成与 Notion 发布流水线。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from typing import Any, Dict, List

import feedparser
import requests

from trendradar.ai.client import AIClient
from trendradar.core.loader import ConfigLoader

TOPICS = ["人工智能", "科技趋势", "网赚与数字副业"]
DEFAULT_IMAGE_POOL = [
    "https://images.pexels.com/photos/3861969/pexels-photo-3861969.jpeg",
    "https://images.pexels.com/photos/546819/pexels-photo-546819.jpeg",
    "https://images.pexels.com/photos/3183150/pexels-photo-3183150.jpeg",
]


def fetch_rss_briefs(feeds: List[Dict[str, str]], per_feed: int = 3) -> str:
    lines = []
    for feed in feeds:
        parsed = feedparser.parse(feed["url"])
        for entry in parsed.entries[:per_feed]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")[:120]
            link = entry.get("link", "")
            lines.append(f"- [{feed['name']}] {title} | {summary} | {link}")
    return "\n".join(lines[:120])


def generate_blog(ai_client: AIClient, topic: str, briefs: str) -> Dict[str, str]:
    prompt = f"""
你是一位头条风格中文科技博主。请围绕“{topic}”写一篇 500-700 字文章，要求：
1) 标题要抓人眼球，适合中国读者；
2) 有观点、有信息差，口语化但不低俗；
3) 结构清晰，使用二级小标题；
4) 输出 JSON：{{"title":"...","content":"..."}}

可参考素材：
{briefs}
"""
    raw = ai_client.chat([
        {"role": "system", "content": "你是中文爆款科技专栏作者。"},
        {"role": "user", "content": prompt},
    ], temperature=0.8, max_tokens=1800)
    cleaned = raw.strip().replace("```json", "").replace("```", "")
    return json.loads(cleaned)


def render_parchment_html(title: str, content: str, image_url: str) -> str:
    css = """
    <style>
      body { background:#f4ecd8; font-family: 'STKaiti','KaiTi',serif; color:#3a2f1f; }
      .paper { max-width: 820px; margin: 30px auto; padding: 36px; background:#f8f1df; border:1px solid #dcc9a3; box-shadow: 0 6px 20px rgba(0,0,0,.12); line-height: 1.9; }
      h1,h2 { color:#5a3e1f; }
      img { width:100%; border-radius:10px; margin:18px 0; }
    </style>
    """
    return f"{css}<div class='paper'><h1>{title}</h1><img src='{image_url}' alt='cover'/><div>{content.replace(chr(10), '<br/>')}</div></div>"


def create_notion_page(token: str, database_id: str, title: str, html_content: str) -> None:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
            "Date": {"date": {"start": datetime.utcnow().date().isoformat()}},
        },
        "children": [
            {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "以下为羊皮纸风格 HTML，可粘贴到支持 HTML 的前端展示。"}}]}},
            {"object": "block", "type": "code", "code": {"rich_text": [{"type": "text", "text": {"content": html_content[:1900]}}], "language": "html"}},
        ],
    }
    resp = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload, timeout=30)
    resp.raise_for_status()


def run(limit: int = 30) -> None:
    cfg = ConfigLoader().load()
    feeds = [f for f in cfg.get("RSS", {}).get("FEEDS", []) if f.get("ENABLED", True)][:limit]
    briefs = fetch_rss_briefs(feeds)
    ai_client = AIClient(cfg.get("AI", {}))

    notion_cfg = cfg.get("NOTION_BLOG", {})
    token = notion_cfg.get("TOKEN", "")
    database_id = notion_cfg.get("DATABASE_ID", "")

    for idx, topic in enumerate(TOPICS):
        blog = generate_blog(ai_client, topic, briefs)
        image_url = DEFAULT_IMAGE_POOL[idx % len(DEFAULT_IMAGE_POOL)]
        html = render_parchment_html(blog["title"], blog["content"], image_url)
        if token and database_id:
            create_notion_page(token, database_id, blog["title"], html)
        print(f"[OK] {topic}: {blog['title']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate 3 CN blogs and publish to Notion")
    parser.add_argument("--limit", type=int, default=30, help="使用的RSS新闻源数量")
    args = parser.parse_args()
    run(limit=args.limit)
