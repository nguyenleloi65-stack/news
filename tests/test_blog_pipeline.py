import unittest

from trendradar.blog_pipeline import render_parchment_html
from trendradar.core.loader import _load_notion_blog_config


class BlogPipelineSecurityTests(unittest.TestCase):
    def test_render_parchment_html_escapes_untrusted_fields(self) -> None:
        html_text = render_parchment_html(
            title="<script>alert(1)</script>",
            content="<img src=x onerror=alert(2)>",
            image_url="https://example.com/x.jpg\" onerror=\"alert(3)",
        )

        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html_text)
        self.assertIn("&lt;img src=x onerror=alert(2)&gt;", html_text)
        self.assertIn("https://example.com/x.jpg&quot; onerror=&quot;alert(3)", html_text)
        self.assertNotIn("<script>alert(1)</script>", html_text)


class LoaderNotionBlogTests(unittest.TestCase):
    def test_load_notion_blog_config_maps_expected_keys(self) -> None:
        config_data = {
            "notion_blog": {
                "enabled": True,
                "token": "token_123",
                "database_id": "db_456",
                "blog_count": 2,
                "source_limit": 10,
                "word_count_min": 500,
                "word_count_max": 700,
                "cron": "0 8 * * *",
                "topics": ["人工智能"],
                "style": {"format": "parchment", "tone": "headline_cn"},
                "image": {"license": "royalty_free", "provider": "pexels"},
                "image_pool": ["https://images.pexels.com/photo.jpg"],
            }
        }

        notion_blog = _load_notion_blog_config(config_data)
        self.assertTrue(notion_blog["ENABLED"])
        self.assertEqual(notion_blog["TOKEN"], "token_123")
        self.assertEqual(notion_blog["DATABASE_ID"], "db_456")
        self.assertEqual(notion_blog["BLOG_COUNT"], 2)
        self.assertEqual(notion_blog["SOURCE_LIMIT"], 10)
        self.assertEqual(notion_blog["WORD_COUNT_MIN"], 500)
        self.assertEqual(notion_blog["WORD_COUNT_MAX"], 700)
        self.assertEqual(notion_blog["CRON"], "0 8 * * *")
        self.assertEqual(notion_blog["TOPICS"], ["人工智能"])
        self.assertEqual(notion_blog["STYLE_FORMAT"], "parchment")
        self.assertEqual(notion_blog["STYLE_TONE"], "headline_cn")
        self.assertEqual(notion_blog["IMAGE_LICENSE"], "royalty_free")
        self.assertEqual(notion_blog["IMAGE_PROVIDER"], "pexels")
        self.assertEqual(notion_blog["IMAGE_POOL"], ["https://images.pexels.com/photo.jpg"])


if __name__ == "__main__":
    unittest.main()
