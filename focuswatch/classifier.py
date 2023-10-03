from focuswatch.database import DatabaseManager


class Classifier():
  def __init__(self):
    self._database = DatabaseManager()

  def classify_entry(self, window_class=None, window_name=None):
    """ Simple classification based on keywords """

    """ Returns category with max depth from keywords in window name and class or Uncategorized """

    entry = window_class + ' ' + window_name
    keywords = self._database.get_all_keywords()

    keyword_depths = {}

    for keyword in keywords:
      id, name, category_id = keyword
      if name in entry:
        keyword_depths[category_id] = self._database.get_category_depth(
          category_id)

    if len(keyword_depths) > 0:
      max_depth = max(keyword_depths, key=keyword_depths.get)
      return max_depth
    else:
      uncategorized_id = self._database.get_category_id_from_name(
        "Uncategorized")
      return uncategorized_id if uncategorized_id else None


if __name__ == '__main__':
  classifier = Classifier()
  category = classifier.classify_entry(
    window_class="code", window_name="classifier.py - FocusWatch - Visual Studio Code")
  print(category)

  # category = classifier.classify_entry(
  # window_class="test", window_name="nothing at all")
  print(category)
