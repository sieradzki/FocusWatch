import os
import unittest
from unittest import mock
import tempfile

from focuswatch.config import Config


class TestConfig(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    # Create temp directory and set as working dir to prevent overriding current config
    cls.temp_dir = tempfile.TemporaryDirectory()
    os.chdir(cls.temp_dir.name)
    cls.config_path = os.path.join(os.getcwd(), 'config.ini')

  @classmethod
  def tearDownClass(cls):
    # Clean up temp directory
    cls.temp_dir.cleanup()

  def test_initialize_config_file_created(self):
    with mock.patch('builtins.print') as mock_print:
      config = Config(self.config_path)

      self.assertTrue(os.path.exists(self.config_path))
      mock_print.assert_called_with(
        "Configuration file written successfully.")

  def test_initialize_config_exception_handling(self):
    with mock.patch('builtins.print') as mock_print:
      with mock.patch('configparser.ConfigParser.write', side_effect=Exception("Mocked exception")):
        config = Config(self.config_path)

        mock_print.assert_called_with(
          "An error occured while writing the configuration file. Mocked exception.")

  def test_initialize_config_file_content(self):
    with mock.patch('builtins.print'):
      config = Config(self.config_path)
      config_contents = config.get_all_config()

      self.assertIn('General', config_contents)
      self.assertIn('Database', config_contents)

      self.assertIn('watch_interval', config_contents['General'])
      self.assertIn('verbose', config_contents['General'])

      self.assertIn('location', config_contents['Database'])


if __name__ == '__main__':
  unittest.main()
