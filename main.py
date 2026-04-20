import time
import threading
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
from monitor import ProcessMonitor
from notifier import AlertSystem

class DeadlockApp:
    def __init__(self):
        self.monitor = ProcessMonitor()
        self.notifier = AlertSystem()
        self.is_running = True
        
        # Determine scan interval from config (default 5 seconds)
        self.scan_interval = self.monitor.config.get("scan_interval_seconds", 5)

        # Build the System Tray menu
        self.menu = pystray.Menu(
            item('Status: Running', lambda: None), # Just an info text, does nothing
            pystray.Menu.SEPARATOR,
            item('Quit', self.quit_app)
        )

        # Initialize the tray icon (Start with Green)
        self.icon = pystray.Icon("DeadlockResolver", self.create_icon('green'), "Deadlock Resolver", self.menu)

    def create_icon(self, color):
        """Generates the colored circle for the taskbar."""
        image = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
        dc = ImageDraw.Draw(image)
        dc.ellipse((0, 0, 64, 64), fill=color)
        return image

    def background_scanner(self):
        """Runs continuously in the background to check for deadlocks."""
        while self.is_running:
            # 1. Scan the OS for frozen apps
            deadlocks = self.monitor.scan_for_deadlocks()
            
            if deadlocks:
                # 2. Change Taskbar Icon to RED
                self.icon.icon = self.create_icon('red')
                self.icon.title = f"Warning: {len(deadlocks)} app(s) hung!"
                
                # 3. Fire notifications for each hung app
                for app in deadlocks:
                    self.notifier.send_deadlock_alert(app['name'], app['pid'])
                    
                    # Optional: If auto-kill is enabled in config, kill it automatically
                    if self.monitor.config.get("auto_kill_enabled"):
                        import os
                        os.system(f"taskkill /F /PID {app['pid']}")
            else:
                # 4. If system is healthy, ensure icon is GREEN
                self.icon.icon = self.create_icon('green')
                self.icon.title = "System Healthy"
            
            # 5. Sleep until the next scan cycle
            time.sleep(self.scan_interval)

    def quit_app(self, icon, item):
        """Cleanly shuts down the threads and the icon."""
        self.is_running = False
        icon.stop()

    def run(self):
        """Starts the background thread and the tray icon loop."""
        # Spin up the background monitor as a daemon thread
        # (Daemon means it will automatically die when the main program closes)
        monitor_thread = threading.Thread(target=self.background_scanner, daemon=True)
        monitor_thread.start()

        # Start the blocking system tray loop
        print("Starting Deadlock Resolver. Check your System Tray!")
        self.icon.run()

if __name__ == "__main__":
    app = DeadlockApp()
    app.run()