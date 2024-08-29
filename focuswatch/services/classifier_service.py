""" Classifier service for FocusWatch. 

This module provides the Classifier class, which is responsible for classifying 
user activity entries based on window class and name.
"""

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
  from focuswatch.services.category_service import CategoryService
  from focuswatch.services.keyword_service import KeywordService

logger = logging.getLogger(__name__)


class ClassifierService:
  """Service class for classifying activities in the FocusWatch application."""

  def __init__(self, category_service: 'CategoryService', keyword_service: 'KeywordService'):
    self._category_service = category_service
    self._keyword_service = keyword_service

  def classify_entry(self, window_class: str, window_name: str) -> Optional[int]:
    """Classify an entry based on the window class and name.

    Args:
      window_class: The class of the window.
      window_name: The name of the window.

    Returns:
      Optional[int]: Category id with max depth from keywords in window name and class,
                     or id of 'Uncategorized' category if no match is found.
    """
    entry = f"{window_class} {window_name}"
    keywords = self._keyword_service.get_all_keywords()

    keyword_depths = {}
    entry_lower = entry.lower()

    for keyword in keywords:
      if keyword.match_case:
        if keyword.name in entry:
          keyword_depths[keyword.category_id] = self._category_service.get_category_depth(
            keyword.category_id)
      else:
        if keyword.name.lower() in entry_lower:
          keyword_depths[keyword.category_id] = self._category_service.get_category_depth(
            keyword.category_id)

    if keyword_depths:
      return max(keyword_depths, key=keyword_depths.get)
    else:
      return self._category_service.get_category_id_from_name("Uncategorized") or None
