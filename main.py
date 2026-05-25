import time
import threading
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
from monitor import ProcessMonitor
from notifier import AlertSystem
import subprocess

class DeadlockApp:
    def __init__(self):
        self.monitor = ProcessMonitor()
        self.notifier = AlertSystem()
        self.is_running = True
        self.current_deadlocks = []
        self.scan_interval = self.monitor.config.get("scan_interval_seconds", 5)

        # Start with the default healthy menu
        self.icon = pystray.Icon("DeadlockResolver", self.create_icon('green'), "System : Healthy", menu=pystray.Menu(self.get_menu()))

    def create_icon(self, color):
        """Generates the colored circle for the taskbar."""
        image = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
        dc = ImageDraw.Draw(image)
        dc.ellipse((0, 0, 64, 64), fill=color)
        return image

    def get_menu(self):
        """Builds a fresh menu object based on the CURRENT deadlocks list."""
        if not self.current_deadlocks:
            return pystray.Menu(
                item('System : Healthy', lambda: None),
                pystray.Menu.SEPARATOR,
                item('Quit', self.quit_app)
            )
        else:
            menu_items = [
                item('Status : Deadlocks Detected!', lambda: None),
                pystray.Menu.SEPARATOR
            ]
            
            # --- FIX: Create a factory function to bind the PID safely ---
            def make_action(target_pid):
                return lambda icon, item: self.force_close_app(target_pid)
            
            # Add a clickable force-close option for EACH frozen app
            for app in self.current_deadlocks:
                # Use the factory function to generate a valid 2-argument lambda
                action = make_action(app['pid'])
                menu_items.append(item(f"Force Kill {app['name']} (PID: {app['pid']})", action))
                
            menu_items.append(pystray.Menu.SEPARATOR)
            menu_items.append(item('Quit', self.quit_app))
            
            return pystray.Menu(*menu_items)

    def force_close_app(self, pid):
        """Runs the taskkill command when a menu item is clicked."""
        # We pass the command and arguments as a list of strings
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)], 
                check=True, 
                capture_output=True, 
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW # Hides the brief command prompt flash
            )
            print(f"Successfully killed process {pid}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to kill process {pid}. Error: {e.stderr}")

    def background_scanner(self):
        """Runs continuously in the background to check for deadlocks."""
        while self.is_running:
            # 1. Update our main list of frozen apps
            self.current_deadlocks = self.monitor.scan_for_deadlocks()
            
            self.icon.menu = self.get_menu()
            
            if self.current_deadlocks:
                # 2. Change Taskbar Icon to RED
                self.icon.icon = self.create_icon('red')
                
                # 3. Format the HOVER text
                status_lines = [f"{app['name']} : Hung" for app in self.current_deadlocks]
                hover_text = "\n".join(status_lines)
                
                if len(hover_text) > 120:
                    hover_text = hover_text[:117] + "..."
                self.icon.title = hover_text
                
                # 4. Fire notifications
                for app in self.current_deadlocks:
                    self.notifier.send_deadlock_alert(app['name'], app['pid'])
                    
            else:
                # 5. If system is healthy, ensure icon is GREEN
                self.icon.icon = self.create_icon('green')
                self.icon.title = "System : Healthy"
            
            time.sleep(self.scan_interval)

    def quit_app(self, icon, item):
        """Cleanly shuts down the threads and the icon."""
        self.is_running = False
        icon.stop()

    def run(self):
        """Starts the background thread and the tray icon loop."""
        monitor_thread = threading.Thread(target=self.background_scanner, daemon=True)
        monitor_thread.start()
        print("Starting Deadlock Resolver. Check your System Tray!")
        self.icon.run()

if __name__ == "__main__":
    app = DeadlockApp()
    app.run()