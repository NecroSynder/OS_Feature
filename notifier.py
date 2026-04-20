import json
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
            
        # Track active alerts so we don't spam the user with 50 notifications for the same app
        self.active_alerts = set() 

    def send_deadlock_alert(self, app_name, pid):
        if not self.settings.get("show_alerts"):
            return
        
        # Create a unique ID for this specific crash
        alert_id = f"{app_name}_{pid}"
        if alert_id in self.active_alerts:
            return # We already warned the user about this one
        
        self.active_alerts.add(alert_id)

        toast = Notification(
            app_id="Deadlock Resolver",
            title="Application Hung!",
            msg=f"{app_name} is deadlocked and not responding.",
            duration="long"
        )

        if self.settings.get("play_sound"):
            # Native Windows alert sound
            toast.set_audio(audio.Mail, loop=False)

        # THE MAGIC BUTTON: Silently executes 'taskkill' to force quit the specific PID
        kill_command = f"cmd.exe /c taskkill /F /PID {pid}"
        toast.add_actions(label=f"Force Quit {app_name}", launch=kill_command)

        toast.show()

    def remove_from_history(self, app_name, pid):
        """Called if the app recovers on its own, allowing future alerts."""
        alert_id = f"{app_name}_{pid}"
        if alert_id in self.active_alerts:
            self.active_alerts.remove(alert_id)