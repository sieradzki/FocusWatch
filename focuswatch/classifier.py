from focuswatch.database import DatabaseManager


class Classifier():
  def __init__(self):
    self._database = DatabaseManager()

  def classify_entry(self, window_class=None, window_name=None):
    """ Simple temporary classification based on keywords """
    # TODO smarter classification

    """ For now the method returns most common class from keywords in window name and class - this can cause issues for example when count is the same for multiple categories """

    categories = []
    categories.extend(self._database.get_categories_from_keyword(window_class))
    for word in window_name.split():
      categories.extend(self._database.get_categories_from_keyword(word))

    if categories:
      return max(set(categories), key=categories.count)
    else:
      return None


if __name__ == '__main__':
  classifier = Classifier()
  category = classifier.classify_entry(
    window_class="code", window_name="code in python - tutorial - Mozilla Firefox")
  print(category)
