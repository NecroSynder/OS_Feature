# Deadlock Resolver Documentation

## Overview

Deadlock Resolver is a lightweight, background Windows utility designed to monitor the system for unresponsive ("Hung") graphical applications. It sits quietly in the system tray and proactively alerts the user via Windows Toast notifications when an application has frozen. Users can cleanly force-quit the offending application directly from the system tray menu or the notification itself.

## System Requirements

- Operating System: Windows (Relies on `ctypes.windll.user32` Windows APIs)
- Python: Python 3.14
- Required Packages: `pystray`, `Pillow` (icon generation), `psutil`, `winotify`

---

## Core Components

1. `main.py` (Application Entry Point) manages the application's lifecycle and user interface.
   - **System Tray Integration:** Uses `pystray` to create an interactive taskbar icon.
   - **Dynamic Status:** The tray icon is a green circle when the system is healthy, and turns red when deadlocks are detected. Hovering over the red icon reveals the names of the hung applications.
   - **Actionable Menu:** Clicking the tray icon dynamically generates a menu listing all frozen apps with a clickable option to execute a `taskkill` command to force close them.
2. `monitor.py` (The Detection Engine) does the heavy lifting of scanning the OS for unresponsive windows.
   - **Windows API Hooking:** It utilizes a C-type callback function (`EnumWindowsProc`) via `ctypes` to iterate through every open window on the system.
   - **Deadlock Validation:** It checks if a window is visible and flagged as "Hung" by the OS using `user32.IsHungAppWindow`.
   - **Grace Period:** Before declaring an app deadlocked, it ensures the application has been hung longer than the configured timeout period, preventing false positives from momentary lag spikes.
3. `notifier.py` (Alert System) handles user-facing warnings via native Windows Toast notifications.
   - **Winotify Integration:** Generates persistent notifications containing the name of the frozen app.
   - **One-Click Resolution:** It employs a clever workaround by generating a temporary `.bat` file (which deletes itself after execution) in the Windows Temp folder. This allows the application to embed a native "Force Quit" button directly inside the Windows notification.
4. `test_freeze.py` (Testing Utility) a small, built-in dummy application used to verify the software works.
   - **Simulated Hang:** It opens a Tkinter GUI with a "Click to CAUSE DEADLOCK" button.
   - **Mechanism:** Clicking the button triggers a `time.sleep(260)` command on the main thread, instantly blocking the event loop and forcing Windows to flag the application as "Not Responding".

---

## Configuration (config.json)

The application's behavior is driven by the `config.json` file.

| Setting                     | Type             | Description                                                                                                                                 |
| --------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `scan_interval_seconds`     | Integer          | How often the background thread checks for deadlocks. Default in the provided config is `1` second.                                         |
| `hung_timeout_seconds`      | Integer          | The grace period an app must remain unresponsive before being flagged. Currently set to `0` for immediate flagging.                         |
| `auto_kill_enabled`         | Boolean          | Reserved for future use (currently `false`). Likely intended to automatically terminate apps without user input.                            |
| `ignore_list`               | Array of Strings | "Core system applications that the monitor is explicitly forbidden from tracking or killing (e.g. `explorer.exe`, `System`, `SearchUI.exe`) |
| `notifications.show_alerts` | Boolean          | Toggles visual Toast notifications on or off (`true` by default).                                                                           |
| `notifications.play_sound`  | Boolean          | Toggles the audio chime for Toast notifications (`true` by default).                                                                        |

---

## Usage Guide

1. **Start the Application:**
Run python main.py in your terminal. You will see "Starting Deadlock Resolver. Check your System Tray!" printed in the console, and a green circle icon will appear in your taskbar.

2. **Test the Detection:**
Leave the background app running and execute `python test_freeze.py`. Click the red "CAUSE DEADLOCK" button.

3. **Resolve the Deadlock:**
   - Wait for the configured timeout (0 seconds in your current config).
   - A Toast notification will appear, and the system tray icon will turn red.
   - Either click "Force Quit Test Dummy" on the notification OR right-click the red tray icon and select the force kill option.
   - The dummy app will be terminated (`taskkill`), and the icon will revert to green.