""" Classifier module for FocusWatch. 

This module provides the Classifier class, which is responsible for classifying 
user activity entries based on window class and name.
"""
from typing import Optional

from focuswatch.database.category_manager import CategoryManager
from focuswatch.database.keyword_manager import KeywordManager


class Classifier():
  """ Classifier class for FocusWatch application. """

  def __init__(self):
    """ Initialize the classifier. """
    self._category_manager = CategoryManager()
    self._keyword_manager = KeywordManager()

  def classify_entry(self, window_class: str, window_name: str) -> Optional[int]:
    """ Classify an entry based on the window class and name. 

    Args:
      window_class: The class of the window.
      window_name: The name of the window.

    Returns:
      Category id with max depth from keywords in window name and class or id of 'Uncategorized' category
    """

    entry = window_class + " " + window_name
    keywords = self._keyword_manager.get_all_keywords()

    keyword_depths = {}

    entry_lower = entry.lower()

    for keyword in keywords:
      _, name, category_id, match_case = keyword
      if match_case:
        if name in entry:
          keyword_depths[category_id] = self._category_manager.get_category_depth(
            category_id)
      else:
        if name.lower() in entry_lower:
          keyword_depths[category_id] = self._category_manager.get_category_depth(
            category_id)

    if keyword_depths:
      max_depth = max(keyword_depths, key=keyword_depths.get)
      return max_depth
    else:
      uncategorized_id = self._category_manager.get_category_id_from_name(
        "Uncategorized")
      return uncategorized_id if uncategorized_id else None


if __name__ == "__main__":
  classifier = Classifier()
  category = classifier.classify_entry(
    window_class="code", window_name="classifier.py - FocusWatch - Visual Studio Code")
  print(category)
