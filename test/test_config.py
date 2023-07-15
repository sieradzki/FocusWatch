import configparser
import os
import unittest

from focuswatch.config import CONFIG_FILE_PATH, initialize_config


class  TestConfig(unittest.TestCase):
  def test_initialize_config_file_exists(self):
    initialize_config()
    self.assertTrue(os.path.exists(CONFIG_FILE_PATH))

  def test_initialize_config_file_content(self):
    initialize_config()
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_PATH)

    self.assertIn('General', config)
    self.assertIn('Database', config)

    self.assertIn('watch_interval', config['General'])

    self.assertIn('location', config['Database'])
    self.assertIn('name', config['Database'])


if __name__ == '__main__':
  unittest.main()
    
  