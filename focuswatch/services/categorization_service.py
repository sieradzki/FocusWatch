from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class CategorizationService:
  def __init__(self, activity_service, classifier):
    self._activity_service = activity_service
    self._classifier = classifier

  def retroactive_categorization(self, progress_callback=None):
    """ Perform retroactive categorization of activities.

    Args:
        progress_callback (callable, optional): Function to call with progress updates.
    """
    # Fetch all activities
    activities = self._activity_service.get_all_activities()
    total_activities = len(activities)

    if progress_callback:
      progress_callback(0, total_activities)

    # Group activities by (window_class, window_name)
    activity_groups = defaultdict(list)
    for activity in activities:
      key = (activity.window_class, activity.window_name)
      activity_groups[key].append(activity)

    # Process each group
    processed_activities = 0
    for group_activities in activity_groups.values():
      window_class = group_activities[0].window_class
      window_name = group_activities[0].window_name

      # Classify once per group
      category_id = self._classifier.classify_entry(
          window_class, window_name)

      # Find activities that need updating
      activities_to_update = [
          activity for activity in group_activities if activity.category_id != category_id
      ]

      if activities_to_update:
        # Update all activities in one query
        activity_ids = [
            activity.id for activity in activities_to_update]
        self._activity_service.bulk_update_category(
            activity_ids, category_id)

      processed_activities += len(group_activities)

      # Emit progress signal
      if progress_callback:
        progress_callback(processed_activities, total_activities)

    # Final progress update
    if progress_callback:
      progress_callback(total_activities, total_activities)

    logger.info("Retroactive categorization completed.")
    return True
