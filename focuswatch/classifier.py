from typing import List, Optional

from focuswatch.database.category_manager import CategoryManager
from focuswatch.database.keyword_manager import KeywordManager


class Classifier():
  def __init__(self):
    self._category_manager = CategoryManager()
    self._keyword_manager = KeywordManager()

  def classify_entry(self, window_class: str, window_name=str) -> int:
    """ Classify an entry based on the window class and name. 

    Args:
      window_class: The class of the window.
      window_name: The name of the window.

    Returns:
      Category id with max depth from keywords in window name and class or id of 'Uncategorized' category
    """

    entry = window_class + ' ' + window_name
    keywords = self._keyword_manager.get_all_keywords()

    keyword_depths = {}

    for keyword in keywords:
      id, name, category_id = keyword
      # TODO tolower check
      if name in entry:
        keyword_depths[category_id] = self._category_manager.get_category_depth(
          category_id)

    if len(keyword_depths) > 0:
      max_depth = max(keyword_depths, key=keyword_depths.get)
      return max_depth
    else:
      uncategorized_id = self._category_manager.get_category_id_from_name(
        "Uncategorized")
      return uncategorized_id if uncategorized_id else None


if __name__ == '__main__':
  classifier = Classifier()
  category = classifier.classify_entry(
    window_class="code", window_name="classifier.py - FocusWatch - Visual Studio Code")
  print(category)

  # category = classifier.classify_entry(
  # window_class="test", window_name="nothing at all")
  # print(category)
