import unittest
from ann_url import FAISSContentSearch

class TestFAISSContentSearch(unittest.TestCase):
    def setUp(self):
        self.search_engine = FAISSContentSearch()

    def test_get_combined_text_with_empty_title_and_description(self):
        title = ""
        description = ""
        expected_combined_text = ""
        actual_combined_text = self.search_engine._get_combined_text(title, description)
        self.assertEqual(actual_combined_text, expected_combined_text)

if __name__ == "__main__":
    unittest.main()