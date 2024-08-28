import unittest
from PySide6.QtCore import QObject
from focuswatch.viewmodels.base_viewmodel import BaseViewModel


class TestBaseViewModel(unittest.TestCase):

  def setUp(self):
    self.viewmodel = BaseViewModel()

  def test_initialization(self):
    """ Test that the BaseViewModel initializes correctly. """
    self.assertIsInstance(self.viewmodel, QObject)
    self.assertEqual(self.viewmodel._property_observers, {})

  def test_set_property(self):
    """ Test that setting a property emits the property_changed signal. """
    self.viewmodel.property_changed.connect(self.on_property_changed)
    self.property_changed_triggered = False

    # Define a test property in the viewmodel
    self.viewmodel.test_property = "initial_value"
    self.viewmodel._set_property("test_property", "new_value")

    self.assertEqual(self.viewmodel.test_property, "new_value")
    self.assertTrue(self.property_changed_triggered)

  def on_property_changed(self, property_name):
    """ Helper method to capture property changed signal. """
    if property_name == "test_property":
      self.property_changed_triggered = True

  def test_add_property_observer(self):
    """ Test that property observers are added correctly. """
    def dummy_callback():
      pass

    self.viewmodel.add_property_observer("test_property", dummy_callback)
    self.assertIn("test_property", self.viewmodel._property_observers)
    self.assertEqual(
      self.viewmodel._property_observers["test_property"], [dummy_callback])

  def test_notify_observers(self):
    """ Test that observers are notified when a property changes. """
    self.observer_notified = False

    def dummy_callback():
      self.observer_notified = True

    self.viewmodel.add_property_observer("test_property", dummy_callback)
    self.viewmodel._notify_observers("test_property")

    self.assertTrue(self.observer_notified)


if __name__ == "__main__":
  unittest.main()
