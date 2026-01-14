import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

def open_data_entry_popup():
    """Opens a modal Toplevel window for data entry."""
    popup = tk.Toplevel(root)
    popup.wm_title("Data Entry Form")
    # Make the popup modal (prevents interaction with the main window while open)
    popup.grab_set() 
    
    # Use a frame for better organization
    frame = ttk.Frame(popup, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # --- Input Fields ---
    
    # First Name
    ttk.Label(frame, text="First Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
    first_name_entry = ttk.Entry(frame, width=25)
    first_name_entry.grid(row=0, column=1, pady=5)

    # Last Name
    ttk.Label(frame, text="Last Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
    last_name_entry = ttk.Entry(frame, width=25)
    last_name_entry.grid(row=1, column=1, pady=5)

    # Age
    ttk.Label(frame, text="Age:").grid(row=2, column=0, sticky=tk.W, pady=5)
    age_spinbox = tk.Spinbox(frame, from_=0, to=120, width=5)
    age_spinbox.grid(row=2, column=1, sticky=tk.W, pady=5)

    # --- Submission Logic ---
    def on_submit():
        first_name = first_name_entry.get()
        last_name = last_name_entry.get()
        age = age_spinbox.get()
        
        if not first_name or not last_name:
            messagebox.showerror("Error", "First and last name are required.")
            return

        print(f"Data submitted: Name: {first_name} {last_name}, Age: {age}")
        popup.destroy() # Close the popup window

    # --- Buttons ---
    submit_button = ttk.Button(frame, text="Submit", command=on_submit)
    submit_button.grid(row=3, column=1, sticky=tk.E, pady=10)
    
    cancel_button = ttk.Button(frame, text="Cancel", command=popup.destroy)
    cancel_button.grid(row=3, column=0, sticky=tk.W, pady=10)

# Main window setup
root = tk.Tk()
root.title("Main Application")
root.geometry("300x150")

main_label = tk.Label(root, text="Click below to open data entry form.")
main_label.pack(pady=20)

# Button to open the popup from the main window
open_button = ttk.Button(root, text="Open Form", command=open_data_entry_popup)
open_button.pack(pady=10)

root.mainloop()

