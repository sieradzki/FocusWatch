import configparser
import os


class Config:
  """ Configuration class for FocusWatch """

  def __init__(self, config_file_path='config.ini'):
    self.config_file_path = config_file_path
    self.config = configparser.ConfigParser()
    self.load_config()
    # self.config.read(self.config_file_path)

  def initialize_config(self):
    """ Initialize the configuration file with default values """
    self.config['General'] = {
      'watch_interval': 1.0,
      'verbose': 0,
      'watch_afk': True,
      'afk_timeout': 10
    }
    self.config['Database'] = {
      'location': './focuswatch.sqlite',
    }

    self.write_config_to_file()

  def write_config_to_file(self):
    """ Write the configuration to the configuration file """
    try:
      with open(self.config_file_path, 'w') as config_file:
        self.config.write(config_file)
      print("Configuration file written successfully.")  # TODO  logging
    except Exception as e:
      print(
        f"An error occured while writing the configuration file. {e}.")

  def load_config(self):
    """ Load config from the configuration file """
    if not os.path.exists(self.config_file_path):
      # TODO logging module
      print(
        f"Configuration file {self.config_file_path} not found. Creating default configuration")
      self.initialize_config()
    else:
      self.config.read(self.config_file_path)

  def update_config(self, section, option, value):  # TODO change name to set_config_value
    """ Update the configuration with a new value """
    if section in self.config and option in self.config[section]:
      self.config[section][option] = str(value)
      self.write_config_to_file()
    else:
      return ValueError(f"Section '{section}' or option '{option}' does not exist.")

  def get_config(self, section, option):  # TODO change name to get_config_value
    """ Get a configuration value """
    if section in self.config and option in self.config[section]:
      return self.config[section][option]
    else:
      return ValueError(f"Section '{section}' or option '{option}' does not exist.")

  def get_all_config(self):  # TODO change name to get_config
    """ Get all configuration values """
    all_config = {}
    for section in self.config.sections():
      all_config[section] = dict(self.config[section])
    return all_config


if __name__ == '__main__':
  config = Config()
  print(config.get_all_config())
  config.update_config('General', 'verbose', '1')
  print(config.get_all_config())
