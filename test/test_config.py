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
    cls.original_cwd = os.getcwd()
    os.chdir(cls.temp_dir.name)
    cls.config_path = os.path.join(os.getcwd(), "config.yml")

  @classmethod
  def tearDownClass(cls):
    # Clean up temp directory and restore original working directory
    os.chdir(cls.original_cwd)
    cls.temp_dir.cleanup()

  def test_initialize_config_file_created(self):
    with mock.patch("logging.Logger.info") as _:
      config = Config(self.config_path)
      config.initialize_config()

      self.assertTrue(os.path.exists(self.config_path))
      # mock_info.assert_any_call(
      # "Configuration file written successfully.")

  def test_write_config_to_file_filenotfounderror(self):
    # Ensure the Config object is initialized before mocking
    config = Config(self.config_path)
    with mock.patch("focuswatch.config.open", side_effect=FileNotFoundError("Mocked FileNotFoundError")), \
            mock.patch("logging.Logger.error") as mock_error:
      config.write_config_to_file()
      mock_error.assert_called_with(
          "The configuration file was not found. Mocked FileNotFoundError")

  def test_write_config_to_file_ioerror(self):
    # Ensure the Config object is initialized before mocking
    config = Config(self.config_path)
    with mock.patch("focuswatch.config.open", side_effect=IOError("Mocked IOError")), \
            mock.patch("logging.Logger.error") as mock_error:
      config.write_config_to_file()
      mock_error.assert_called_with(
          "An error occurred while writing the configuration file. Mocked IOError")

  def test_initialize_config_file_content(self):
    config = Config(self.config_path)
    config.initialize_config()
    config_contents = config

    self.assertIn("general", config_contents)
    self.assertIn("database", config_contents)

    self.assertIn("watch_interval", config_contents["general"])
    self.assertIn("verbose", config_contents["general"])

    self.assertIn("location", config_contents["database"])


if __name__ == "__main__":
  unittest.main()
