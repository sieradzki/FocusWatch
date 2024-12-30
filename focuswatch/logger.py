""" Logger module for FocusWatch.
https://github.com/mCodingLLC/VideosSampleCode/blob/master/videos/135_modern_logging/mylogger.py """
import datetime as dt
import json
import logging
import atexit
import sys
import os
from typing import override

from focuswatch.config import Config


LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class MyJSONFormatter(logging.Formatter):
  """ Custom JSON formatter for logging. """

  def __init__(self, *, fmt_keys: dict[str, str] | None = None,):
    super().__init__()
    self.fmt_keys = fmt_keys if fmt_keys is not None else {}

  @override
  def format(self, record: logging.LogRecord) -> str:
    message = self._prepare_log_dict(record)
    return json.dumps(message, default=str)

  def _prepare_log_dict(self, record: logging.LogRecord):
    always_fields = {
      "message": record.getMessage(),
      "timestamp": dt.datetime.fromtimestamp(
        record.created, tz=dt.timezone.utc
      ).isoformat(),
    }
    if record.exc_info is not None:
      always_fields["exc_info"] = self.formatException(record.exc_info)

    if record.stack_info is not None:
      always_fields["stack_info"] = self.formatStack(record.stack_info)

    message = {
      key: msg_val
      if (msg_val := always_fields.pop(val, None)) is not None
      else getattr(record, val)
      for key, val in self.fmt_keys.items()
    }
    message.update(always_fields)

    for key, val in record.__dict__.items():
      if key not in LOG_RECORD_BUILTIN_ATTRS:
        message[key] = val

    return message


class NonErrorFilter(logging.Filter):
  @override
  def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
    return record.levelno <= logging.INFO


class ColoredFormatter(logging.Formatter):
  """ Formatter that adds color to log output based on level. """
  BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

  RESET_SEQ = "\033[0m"
  COLOR_SEQ = "\033[1;%dm"
  BOLD_SEQ = "\033[1m"

  COLORS = {
    "WARNING": YELLOW,
    "INFO": WHITE,
    "DEBUG": BLUE,
    "CRITICAL": YELLOW,
    "ERROR": RED
  }

  def format(self, record):
    levelname = record.levelname
    if levelname in self.COLORS:
      levelname_color = self.COLOR_SEQ % (
        30 + self.COLORS[levelname]) + levelname + self.RESET_SEQ
      record.levelname = levelname_color
    return logging.Formatter.format(self, record)


def setup_logging():
  # Get logging file path from config
  config = Config()

  if getattr(sys, "frozen", False):
    # If the application is frozen (packaged)
    config_file = config.default_logger_config_path
    log_level = os.environ.get("FOCUSWATCH_LOG_LEVEL", "INFO").upper()
  else:
    # If running in development mode
    config_file = config["logging"]["logger_config"]
    log_level = os.environ.get("FOCUSWATCH_LOG_LEVEL", "DEBUG").upper()

  if not os.path.exists(config_file):
    raise FileNotFoundError(
      f"Logging configuration file not found: {config_file}")

  with open(config_file, encoding="utf-8") as f_in:
    log_config = json.load(f_in)

  # Replace the placeholder with the actual log file path
  log_file_path = config.default_log_path
  log_config["handlers"]["file_json"]["filename"] = log_file_path

  # Set log levels based on environment variable
  log_config["handlers"]["stdout"]["level"] = log_level
  log_config["handlers"]["file_json"]["level"] = log_level
  log_config["loggers"]["root"]["level"] = log_level

  # Add color formatter to stdout handler
  stdout_handler_config = log_config["handlers"]["stdout"]
  stdout_handler_config["formatter"] = "colored"

  logging.config.dictConfig(log_config)
  queue_handler = logging.getHandlerByName("queue_handler")
  if queue_handler is not None:
    queue_handler.listener.start()
    atexit.register(queue_handler.listener.stop)
