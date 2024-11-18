import unittest
from src.scraper import fetch_page

class TestScraper(unittest.TestCase):
    def test_fetch_page(self):
        url = "https://www1.salary.com/"
        html = fetch_page(url)
        self.assertIsNotNone(html)
        self.assertIn("<!DOCTYPE html>", html)

if __name__ == "__main__":
    unittest.main()