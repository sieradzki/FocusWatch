import unittest
from focuswatch.models.keyword import Keyword


class TestKeyword(unittest.TestCase):

  def setUp(self):
    self.keyword = Keyword(id=1, name="Test", category_id=1, match_case=False)
    self.case_sensitive_keyword = Keyword(name="Test", match_case=True)

  def test_keyword_initialization(self):
    """ Test that the Keyword is initialized correctly. """
    self.assertEqual(self.keyword.id, 1)
    self.assertEqual(self.keyword.name, "Test")
    self.assertEqual(self.keyword.category_id, 1)
    self.assertFalse(self.keyword.match_case)

  def test_repr(self):
    """ Test the __repr__ method for proper string representation. """
    expected_repr = "Keyword(name='Test', category_id=1, id=1, match_case=False)"
    self.assertEqual(repr(self.keyword), expected_repr)

  def test_case_insensitive_match(self):
    """ Test the matches method for case-insensitive matching. """
    self.assertTrue(self.keyword.matches("this is a test"))
    self.assertTrue(self.keyword.matches("TEST case"))
    self.assertFalse(self.keyword.matches("this is not a match"))

  def test_case_sensitive_match(self):
    """ Test the matches method for case-sensitive matching. """
    self.assertTrue(self.case_sensitive_keyword.matches("This is a Test"))
    self.assertFalse(self.case_sensitive_keyword.matches("this is a test"))
    self.assertFalse(self.case_sensitive_keyword.matches("Another TEST"))

  def test_empty_text(self):
    """ Test matching with an empty text string. """
    self.assertFalse(self.keyword.matches(""))
    self.assertFalse(self.case_sensitive_keyword.matches(""))

  def test_keyword_empty_name(self):
    """ Test matching when the keyword name is empty. 
    Technically I'm not sure if this is allowed but it could be used as a wildcard. 
    """
    empty_keyword = Keyword(name="")
    self.assertTrue(empty_keyword.matches("anything matches"))
    self.assertTrue(empty_keyword.matches(""))

  def test_partial_match(self):
    """ Test partial matches where the keyword is a substring. """
    partial_keyword = Keyword(name="est")
    self.assertTrue(partial_keyword.matches("Test"))
    self.assertTrue(partial_keyword.matches("Best case scenario"))
    self.assertFalse(partial_keyword.matches("Worst case"))


if __name__ == '__main__':
  unittest.main()
