import unittest
from datetime import datetime, timedelta
from focuswatch.models.activity import Activity


class TestActivity(unittest.TestCase):
  """ Test the Activity model. """

  def setUp(self):
    self.time_start = datetime(2024, 8, 26, 14, 0, 0)
    self.time_stop = self.time_start + timedelta(hours=2)
    self.activity = Activity(id=1, time_start=self.time_start, time_stop=self.time_stop,
                             window_class="TestClass", window_name="TestWindow", category_id=1, project_id=1)

  def test_activity_initialization(self):
    """ Test that the Activity is initialized correctly. """
    self.assertEqual(self.activity.id, 1)
    self.assertEqual(self.activity.time_start, self.time_start)
    self.assertEqual(self.activity.time_stop, self.time_stop)
    self.assertEqual(self.activity.window_class, "TestClass")
    self.assertEqual(self.activity.window_name, "TestWindow")
    self.assertEqual(self.activity.category_id, 1)
    self.assertEqual(self.activity.project_id, 1)

  def test_activity_duration(self):
    """Test the duration calculation of the Activity."""
    expected_duration = 2 * 60 * 60
    self.assertEqual(self.activity.duration, expected_duration)

  def test_invalid_time_initialization(self):
    """ Test that initializing with an invalid time raises a ValueError. """
    with self.assertRaises(ValueError):
      Activity(time_start=self.time_stop, time_stop=self.time_start)

  def test_activity_without_stop_time(self):
    """ Test the behavior when the Activity has no stop time. """
    activity_no_stop = Activity(
      time_start=self.time_start, window_class="TestClass", window_name="TestWindow")
    self.assertIsNone(activity_no_stop.time_stop)
    with self.assertRaises(TypeError):
      _ = activity_no_stop.duration

  def test_activity_across_midnight(self):
    """ Test the duration calculation for an activity spanning midnight. """
    time_start = datetime(2024, 8, 26, 23, 30, 0)
    time_stop = datetime(2024, 8, 27, 0, 30, 0)
    activity = Activity(time_start=time_start, time_stop=time_stop)
    self.assertEqual(activity.duration, 3600)


if __name__ == "__main__":
  unittest.main()
