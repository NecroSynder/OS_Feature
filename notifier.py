import json
import os
import tempfile
from winotify import Notification, audio

class AlertSystem:
    def __init__(self):
        # Load config to check if notifications are enabled
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.settings = config.get("notifications", {"show_alerts": True, "play_sound": True})
        except FileNotFoundError:
            self.settings = {"show_alerts": True, "play_sound": True}
            
        self.active_alerts = set() 

    def send_deadlock_alert(self, app_name, pid):
        if not self.settings.get("show_alerts"):
            return
        
        # Create a unique ID for this specific crash
        alert_id = f"{app_name}_{pid}"
        if alert_id in self.active_alerts:
            return 
        
        self.active_alerts.add(alert_id)

        toast = Notification(
            app_id="Deadlock Resolver",
            title="Application Hung!",
            msg=f"{app_name} is deadlocked and not responding.",
            duration="long"
        )

        if self.settings.get("play_sound"):
            toast.set_audio(audio.Mail, loop=False)

        # THE FIX: Create a temporary batch file in your Windows Temp folder
        temp_dir = tempfile.gettempdir()
        bat_path = os.path.join(temp_dir, f"kill_deadlock_{pid}.bat")
        
        # Write the taskkill command into the batch file
        with open(bat_path, 'w') as bat_file:
            # The second line kills the app. 
            # The third line tells the batch file to delete itself!
            bat_file.write(f"@echo off\n"
                        f"taskkill /F /T /PID {pid}\n"
                        f"del \"%~f0\"")

        # Tell Windows to just open the file we just created
        toast.add_actions(label=f"Force Quit {app_name}", launch=bat_path)

        toast.show()

    def remove_from_history(self, app_name, pid):
        """Called if the app recovers on its own, allowing future alerts."""
        alert_id = f"{app_name}_{pid}"
        if alert_id in self.active_alerts:
            self.active_alerts.remove(alert_id)