import ctypes
import logging
import os
import sys
import subprocess
import textwrap

from focuswatch.utils import is_frozen, is_linux, is_windows

if is_windows():
  import winreg as reg

logger = logging.getLogger(__name__)
APP_NAME = "focuswatch"
SERVICE_FILE = f"/etc/systemd/system/{APP_NAME}.service"


def create_service_file():
  """ Create a systemd service file for the application. 
  note: the service should wait for the graphical session to start before running to ensure that the application can access the display and system tray. """
  service_content = textwrap.dedent(f"""
  [Unit]
  Description={APP_NAME} service
  After=graphical-session.target

  [Service]
  Environment=DISPLAY=:0
  ExecStart={sys.executable}
  Restart=always
  User={os.getenv("USER")}

  [Install]
  WantedBy=default.target
  """).strip()
  return service_content


def run_pkexec_script(script_content):
  """ Run a script with elevated privileges using pkexec (PolicyKit). """
  try:
    command = ['pkexec', 'bash', '-c', script_content]
    subprocess.run(command, check=True)
    logger.info(f"pkexec script executed successfully.")
  except subprocess.CalledProcessError as e:
    logger.error(f"Failed to execute pkexec script: {e}")
    raise


def write_service_file(service_content):
  """ Write the service file to the systemd directory. """
  script_content = textwrap.dedent(f"""
  echo '{service_content}' > {SERVICE_FILE}
  chmod 644 {SERVICE_FILE}
  """)
  run_pkexec_script(script_content)


def enable_service():
  """ Enable and start the service. """
  script_content = textwrap.dedent(f"""
  systemctl daemon-reload
  systemctl enable {APP_NAME}
  systemctl start {APP_NAME}
  """)
  run_pkexec_script(script_content)


def add_to_autostart_linux():
  """ Add the application to Linux autostart using systemd. """
  service_content = create_service_file()
  try:
    write_service_file(service_content)
    enable_service()
    return True
  except Exception as e:
    logger.error(f"Failed to add {APP_NAME} to Linux autostart: {e}")
    return False


def remove_service_file():
  """ Remove the service file from the systemd directory. """
  script_content = textwrap.dedent(f"""
  systemctl stop {APP_NAME}
  systemctl disable {APP_NAME}
  rm {SERVICE_FILE}
  systemctl daemon-reload
  """)
  try:
    run_pkexec_script(script_content)
    return True
  except (OSError, subprocess.CalledProcessError) as e:
    logger.error(f"Failed to remove service file: {e}")
    return False


def is_admin():
  """ Check if the application is running with administrator privileges - Windows only."""
  try:
    return ctypes.windll.shell32.IsUserAnAdmin()
  except Exception as e:
    logger.error(f"Failed to check admin status: {e}")
    return False


def run_as_admin(func):
  """ Run a function with elevated privileges - Windows only. """
  if is_admin():
    return func()
  else:
    try:
      ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    except Exception as e:
      logger.error(f"Failed to elevate privileges: {e}")
      return False


def add_to_autostart_windows():
  """ Add the application to Windows autostart. """
  key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
  try:
    key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_ALL_ACCESS)
    reg.SetValueEx(key, APP_NAME, 0, reg.REG_SZ, sys.executable)
    reg.CloseKey(key)
    logger.info(f"{APP_NAME} added to Windows autostart.")
    return True
  except OSError as e:
    logger.error(f"Failed to add {APP_NAME} to Windows autostart: {e}")
    return False


def add_to_autostart():
  """ Add the application to autostart. """
  if not is_frozen():
    logger.warning("Autostart can only be set for the packaged application.")
    return False

  if is_in_autostart():
    logger.info(f"{APP_NAME} is already in autostart.")
    return True

  if is_windows():
    return run_as_admin(add_to_autostart_windows)
  elif is_linux():
    init_system = detect_init_system()
    if init_system == "systemd":
      return add_to_autostart_linux()
    else:
      logger.warning(f"Unsupported init system: {
                     init_system}. Please refer to your distribution's documentation for enabling services.")
      service_content = create_service_file()
      write_service_file(service_content)
      return False
  else:
    raise OSError("Unsupported operating system")


def remove_from_autostart():
  """ Remove the application from autostart. """
  if not is_frozen():
    logger.warning("Autostart can only be set for the packaged application.")
    return False

  if not is_in_autostart():
    logger.info(f"{APP_NAME} is not in autostart.")
    return True

  if is_windows():
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
      key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_ALL_ACCESS)
      reg.DeleteValue(key, APP_NAME)
      reg.CloseKey(key)
      logger.info(f"{APP_NAME} removed from Windows autostart.")
      return True
    except OSError as e:
      logger.error(f"Failed to remove {APP_NAME} from Windows autostart: {e}")
      return False
  elif is_linux():
    init_system = detect_init_system()
    if init_system == "systemd":
      return remove_service_file()
    else:
      logger.warning(f"Unsupported init system: {
                     init_system}. Please refer to your distribution's documentation for disabling services.")
      return False
  else:
    raise OSError("Unsupported operating system")


def is_in_autostart():
  """ Check if the application is in autostart. """
  if is_windows():
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
      key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_READ)
      reg.QueryValueEx(key, APP_NAME)
      reg.CloseKey(key)
      return True
    except OSError:
      return False
  elif is_linux():
    return os.path.exists(SERVICE_FILE)
  else:
    raise OSError("Unsupported operating system")


def detect_init_system():
  """ Detect the init system used by the Linux distribution - currently only supports systemd. """
  if os.path.exists("/bin/systemctl"):
    return "systemd"
  return "unknown"
