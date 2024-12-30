# Focuswatch 

### Description:
PySide6 desktop time tracking app for Linux systems with xorg and Windows.

---

## Table of Contents:
- [Focuswatch](#focuswatch)
    - [Description:](#description)
  - [Table of Contents:](#table-of-contents)
  - [1. Introduction](#1-introduction)
  - [2. Features](#2-features)
  - [3. Showcase # todo](#3-showcase--todo)
  - [4. Installation and Setup](#4-installation-and-setup)
    - [4.1 Development Setup](#41-development-setup)
    - [4.2 Using the Latest Release](#42-using-the-latest-release)

---

## 1. Introduction

Activity monitoring and logging with categorization and data visualization.

---

## 2. Features
- User-friendly interface for data visualization and categorization.
- Track time spent on each activity.
- Customizable categories for time tracking.
- Focused / distracted activity tagging.
- Categorization helper
- Retroactive categorization based on current ruleset

---

## 3. Showcase # todo
images/screenshots of the application # todo


Main dashboard

---

## 4. Installation and Setup

### 4.1 Development Setup
Follow these steps to set up the project for development:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/sieradzki/FocusWatch.git
   cd FocusWatch
   ```

2. **Create a Virtual Environment (Optional):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. (For Linux) **Install xorg Dependencies:**
   ```bash
   sudo pacman -S install xdotool xprintidle # Arch Linux
   sudo apt-get install xdotool xprintidle # Debian/Ubuntu
   ```

5. **Run the Application:**
   ```bash
   python -m focuswatch
   ```
   By default the app will run in the background and will be accessible from the system tray.

---

### 4.2 Using the Latest Release
1. **Download the Executable:**
   - Visit the [Releases](https://github.com/sieradzki/FocusWatch/releases) section of the GitHub repository.
   - Download the latest executable file for your operating system.

2. **Run the Application:**
   - Windows: Double-click the `.exe` file.
   - Linux: Ensure the file has executable permissions, then run:
     ```bash
     ./focuswatch-linux
     ```

3. **No Installation Required:**
   The application runs standalone; dependencies are bundled with the executable.

---