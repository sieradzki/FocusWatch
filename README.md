# FocusWatch
 Activity monitoring and logging with categorization

Currently supports Linux systems with xorg.
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

The program by default runs in the system tray, to open the dashboard right click on the icon and choose the option from the menu.