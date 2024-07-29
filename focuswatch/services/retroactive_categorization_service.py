from focuswatch.classifier import Classifier
from focuswatch.services.activity_service import ActivityService
from focuswatch.services.category_service import CategoryService
from focuswatch.services.keyword_service import KeywordService


class RetroactiveCategorizationService:
  def __init__(self, activity_service: ActivityService, category_service: CategoryService, keyword_service: KeywordService):
    self._activity_service = activity_service
    self._category_service = category_service
    self._keyword_service = keyword_service
    self._classifier = Classifier(category_service, keyword_service)

  def categorize_all_activities(self, progress_callback=None):
    activities = self._activity_service.get_all_activities()
    total_activities = len(activities)

    for i, activity in enumerate(activities):
      window_class, window_name = activity.window_class, activity.window_name
      category_id = self._classifier.classify_entry(
          window_class, window_name)
      self._activity_service.update_category(activity.id, category_id)

      if progress_callback:
        progress_callback(i + 1, total_activities)

    return True
