""" Unit tests for the Config class in focuswatch.config """
import os
import unittest
from unittest import mock
import tempfile

from focuswatch.config import Config


class TestConfig(unittest.TestCase):
  """ Unit tests for the Config class """

  @classmethod
  def setUpClass(cls):
    # Create temp directory and set as working dir to prevent overriding current config
    cls.temp_dir = tempfile.TemporaryDirectory()
    os.chdir(cls.temp_dir.name)
    cls.config_path = os.path.join(os.getcwd(), "config.ini")

  @classmethod
  def tearDownClass(cls):
    # Clean up temp directory
    cls.temp_dir.cleanup()

  def test_initialize_config_file_created(self):
    with mock.patch("builtins.print") as mock_print:
      config = Config(self.config_path)
      config.initialize_config()

      self.assertTrue(os.path.exists(self.config_path))
      mock_print.assert_called_with(
          "Configuration file written successfully.")

  def test_write_config_to_file_filenotfounderror(self):
    with mock.patch("builtins.open", side_effect=FileNotFoundError("Mocked FileNotFoundError")), \
            mock.patch("builtins.print") as mock_print:
      config = Config(self.config_path)
      config.write_config_to_file()
      mock_print.assert_called_with(
        "The configuration file was not found. Mocked FileNotFoundError.")

  def test_write_config_to_file_ioerror(self):
    with mock.patch("builtins.open", side_effect=IOError("Mocked IOError")), \
            mock.patch("builtins.print") as mock_print:
      config = Config(self.config_path)
      config.write_config_to_file()
      mock_print.assert_called_with(
        "An error occurred while writing the configuration file. Mocked IOError.")

  def test_initialize_config_file_content(self):
    config = Config(self.config_path)
    config.initialize_config()
    config_contents = config.get_config()

    self.assertIn("General", config_contents)
    self.assertIn("Database", config_contents)

    self.assertIn("watch_interval", config_contents["General"])
    self.assertIn("verbose", config_contents["General"])

    self.assertIn("location", config_contents["Database"])


if __name__ == "__main__":
  unittest.main()
