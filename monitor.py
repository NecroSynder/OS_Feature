import json
import time
import psutil
import ctypes
import ctypes.wintypes

class ProcessMonitor:
    def __init__(self):
        self.config = self.load_config()
        # Convert ignore list to lowercase for safe comparisons
        self.ignore_list = [name.lower() for name in self.config.get("ignore_list", [])]
        self.hung_timeout = self.config.get("hung_timeout_seconds", 15)
        
        # Dictionary to track how long a process has been hung: {pid: first_seen_time}
        self.hung_history = {} 

    def load_config(self):
        """Loads the settings from config.json."""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: config.json not found. Using default settings.")
            return {}

    def scan_for_deadlocks(self):
        """
        Scans Windows for visible windows that have stopped responding.
        Returns a list of applications that have been hung longer than the timeout.
        """
        current_time = time.time()
        current_hung_pids = set()
        confirmed_deadlocks = []
        
        user32 = ctypes.windll.user32
        
        # This is a callback function that Windows will run for every open window
        def enum_windows_proc(hwnd, lParam):
            # 1. Check if the window is visible and if Windows flags it as "Hung"
            if user32.IsWindowVisible(hwnd) and user32.IsHungAppWindow(hwnd):
                
                # 2. Get the Process ID (PID) from the Window Handle (HWND)
                pid = ctypes.wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                
                try:
                    proc = psutil.Process(pid.value)
                    proc_name = proc.name()
                    
                    # 3. Check if the app is safe to kill (not in ignore_list)
                    if proc_name.lower() not in self.ignore_list:
                        current_hung_pids.add(pid.value)
                        
                        # 4. Start the timer if this is a newly hung app
                        if pid.value not in self.hung_history:
                            self.hung_history[pid.value] = current_time
                        
                        # 5. Check if it has been hung longer than our config allows
                        time_hung = current_time - self.hung_history[pid.value]
                        if time_hung >= self.hung_timeout:
                            # Avoid adding duplicates if one app has multiple hung windows
                            if not any(d['pid'] == pid.value for d in confirmed_deadlocks):
                                confirmed_deadlocks.append({
                                    "pid": pid.value,
                                    "name": proc_name,
                                    "time_hung": round(time_hung)
                                })
                                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process might have closed on its own or we lack permissions
                    pass
            
            return True # Continue scanning

        # Define the C-type function signature required by the Windows API
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        
        # Trigger the Windows API scan
        user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)
        
        # Clean up history: remove PIDs that are no longer hung (they recovered or crashed)
        pids_to_remove = [p for p in self.hung_history if p not in current_hung_pids]
        for p in pids_to_remove:
            del self.hung_history[p]
            
        return confirmed_deadlocks

# --- Testing Block ---
if __name__ == "__main__":
    monitor = ProcessMonitor()
    print("Testing monitor.py independently...")
    print(f"Tracking apps hung longer than {monitor.hung_timeout} seconds.")
    print("Scanning... (Press Ctrl+C to stop)")
    
    try:
        while True:
            deadlocks = monitor.scan_for_deadlocks()
            if deadlocks:
                for app in deadlocks:
                    print(f"[!] DEADLOCK FOUND: {app['name']} (PID: {app['pid']}) - Hung for {app['time_hung']}s")
            time.sleep(2) # Scan every 2 seconds for the test
    except KeyboardInterrupt:
        print("\nTest stopped.")