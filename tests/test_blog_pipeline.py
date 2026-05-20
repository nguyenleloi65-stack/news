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
                "topics": ["人工智能"],
                "word_count": {"min": 500, "max": 700},
                "style": "headline",
                "schedule": {"enabled": True},
                "image_pool": ["https://images.pexels.com/photo.jpg"],
            }
        }

        notion_blog = _load_notion_blog_config(config_data)
        self.assertTrue(notion_blog["ENABLED"])
        self.assertEqual(notion_blog["TOKEN"], "token_123")
        self.assertEqual(notion_blog["DATABASE_ID"], "db_456")
        self.assertEqual(notion_blog["TOPICS"], ["人工智能"])
        self.assertEqual(notion_blog["WORD_COUNT"], {"min": 500, "max": 700})
        self.assertEqual(notion_blog["STYLE"], "headline")
        self.assertEqual(notion_blog["SCHEDULE"], {"enabled": True})
        self.assertEqual(notion_blog["IMAGE_POOL"], ["https://images.pexels.com/photo.jpg"])


if __name__ == "__main__":
    unittest.main()
