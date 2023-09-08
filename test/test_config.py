import os
import unittest
from unittest import mock
import tempfile

from focuswatch.config import initialize_config, load_config


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
      initialize_config(self.config_path)

      self.assertTrue(os.path.exists(self.config_path))
      mock_print.assert_called_with(
        "Configuration file initialized successfully.")

  def test_initialize_config_exception_handling(self):
    with mock.patch('builtins.print') as mock_print:
      with mock.patch('configparser.ConfigParser.write', side_effect=Exception("Mocked exception")):
        initialize_config()

        mock_print.assert_called_with(
          "An error occured while initializing the configuration file. Mocked exception.")

  def test_initialize_config_file_content(self):
    with mock.patch('builtins.print'):
      initialize_config(self.config_path)
      config = load_config(self.config_path)

      self.assertIn('General', config)
      self.assertIn('Database', config)

      self.assertIn('watch_interval', config['General'])

      self.assertIn('location', config['Database'])
      self.assertIn('name', config['Database'])


if __name__ == '__main__':
  unittest.main()
