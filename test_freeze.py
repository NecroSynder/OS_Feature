import tkinter as tk
import time

def intentionally_deadlock():
    print("Deadlock triggered! The app will now freeze.")
    print("Try clicking on this window or dragging it...")
    # This blocks the main GUI event loop, instantly causing a "Hung" state
    time.sleep(260) 

# Create a basic Windows GUI
root = tk.Tk()
root.title("Test Dummy")
root.geometry("300x200")

# Add a big button to trigger the freeze
btn = tk.Button(root, text="Click to CAUSE DEADLOCK", command=intentionally_deadlock, bg="red", fg="white", font=("Arial", 12, "bold"))
btn.pack(expand=True, fill="both", padx=20, pady=20)

root.mainloop()