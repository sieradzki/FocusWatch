# FocusWatch
 Activity monitoring and logging with categorization

Currently supports Linux systems with xorg.
Windows support is currently broken, it will be fixed on the next release.
When running on Windows, it has to be launched with administrator privileges.
# Setup

1. Install python 3.12
2. Install required libraries
```
pip install -r requirements.txt
```

## Additional steps for Linux
(Example commands for Arch-based systems)

3. Install xdotool
```console
sudo pacman -S xdotool
```

4. Install xprintidle
```console
sudo pacman -S xprintidle
```

# Usage
```console
cd focuswatch
python -m focuswatch
```

Or you can download the latest release from the releases page and run the executable.

The program by default runs in the system tray, to open the dashboard right click on the icon and choose the option from the menu.