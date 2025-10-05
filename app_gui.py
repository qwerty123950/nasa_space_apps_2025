# app_gui.py

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import datetime
import threading

# --- Configuration ---
API_URL = "http://127.0.0.1:8000/analyze"

AVAILABLE_VARIABLES = [
    "max_temp_c",
    "min_temp_c",
    "precipitation_mm",
    "wind_speed_kph",
    "dust_ug_m3",
]

# --- Main Application Class ---
class TerraClimeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TerraClime Planner")
        self.root.geometry("550x600")
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', font=('Helvetica', 12), padding=10)
        self.style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'))
        self.style.configure('Results.TLabel', font=('Helvetica', 11))
        self.style.configure('TCheckbutton', font=('Helvetica', 11))
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        input_frame = ttk.LabelFrame(main_frame, text="Query Parameters", padding="15")
        input_frame.pack(fill='x')
        ttk.Label(input_frame, text="Latitude:", font=('Helvetica', 11)).grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.lat_var = tk.StringVar(value="37.74")
        ttk.Entry(input_frame, textvariable=self.lat_var, width=15).grid(row=0, column=1, sticky='w', padx=5, pady=5)
        ttk.Label(input_frame, text="Longitude:", font=('Helvetica', 11)).grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.lon_var = tk.StringVar(value="-119.59")
        ttk.Entry(input_frame, textvariable=self.lon_var, width=15).grid(row=1, column=1, sticky='w', padx=5, pady=5)
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        ttk.Label(input_frame, text="Date:", font=('Helvetica', 11)).grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.month_var = tk.StringVar(value="July")
        self.day_var = tk.StringVar(value="15")
        ttk.Combobox(input_frame, textvariable=self.month_var, values=months, width=12).grid(row=2, column=1, sticky='w', padx=5)
        ttk.Entry(input_frame, textvariable=self.day_var, width=4).grid(row=2, column=2, sticky='w', padx=5)
        ttk.Label(input_frame, text="Variables:", font=('Helvetica', 11)).grid(row=3, column=0, sticky='nw', padx=5, pady=10)
        vars_frame = ttk.Frame(input_frame)
        vars_frame.grid(row=3, column=1, columnspan=2, sticky='w')
        self.check_vars = {}
        for i, var_name in enumerate(AVAILABLE_VARIABLES):
            self.check_vars[var_name] = tk.BooleanVar()
            ttk.Checkbutton(vars_frame, text=var_name, variable=self.check_vars[var_name], style='TCheckbutton').pack(anchor='w')
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(pady=20)
        self.analyze_button = ttk.Button(action_frame, text="Analyze Climate", command=self.start_analysis_thread)
        self.analyze_button.pack(side=tk.LEFT)
        self.status_label = ttk.Label(action_frame, text="", font=('Helvetica', 10, 'italic'))
        self.status_label.pack(side=tk.LEFT, padx=10)
        results_container = ttk.LabelFrame(main_frame, text="Analysis Results", padding="15")
        results_container.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(results_container)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(results_container, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.results_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.results_frame, anchor="nw")
        self.results_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.placeholder_label = ttk.Label(self.results_frame, text="Results will be displayed here.", style='Results.TLabel', foreground='gray')
        self.placeholder_label.pack()

    def start_analysis_thread(self):
        self.analyze_button.config(state="disabled")
        self.status_label.config(text="Fetching NASA data... please wait.")
        analysis_thread = threading.Thread(target=self.run_analysis)
        analysis_thread.start()

    def run_analysis(self):
        try:
            latitude = float(self.lat_var.get())
            longitude = float(self.lon_var.get())
            month_str = self.month_var.get()
            months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            month = months_list.index(month_str) + 1
            day = int(self.day_var.get())
        except (ValueError, IndexError):
            messagebox.showerror("Invalid Input", "Please check your location and date inputs.")
            self.reset_ui_state()
            return

        selected_variables = [var for var, is_selected in self.check_vars.items() if is_selected.get()]
        if not selected_variables:
            messagebox.showwarning("No Selection", "Please select at least one variable to analyze.")
            self.reset_ui_state()
            return

        # THIS IS THE CRITICAL PART FOR THE GUI
        payload = {
            "latitude": latitude,
            "longitude": longitude,
            "month": month,
            "day": day,
            "variables": selected_variables
        }

        try:
            response = requests.post(API_URL, json=payload, timeout=90)
            response.raise_for_status()
            data = response.json()
            self.display_results(data)
        except requests.exceptions.RequestException as e:
            messagebox.showerror("API Error", f"Could not get data from the backend.\n\nError: {e}")
        finally:
            self.reset_ui_state()

    def reset_ui_state(self):
        self.analyze_button.config(state="normal")
        self.status_label.config(text="")

    def display_results(self, data):
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        results = data.get('results', [])
        if not results:
            ttk.Label(self.results_frame, text="No results returned for the selected variables.", style='Results.TLabel').pack()
            return
        for result in results:
            var_frame = ttk.Frame(self.results_frame, padding=5)
            var_frame.pack(fill='x', expand=True, pady=5)
            var_name = result.get('variable', 'N/A').replace("_", " ").title()
            unit = result.get('unit', '')
            mean = result.get('mean', 0)
            data_points = result.get('raw_data_points', 'N/A')
            ttk.Label(var_frame, text=f"{var_name}:", font=('Helvetica', 12, 'bold')).pack(anchor='w')
            ttk.Label(var_frame, text=f"  • Average: {mean:.1f} {unit} (from {data_points} years)", style='Results.TLabel').pack(anchor='w')
            likelihood = result.get('likelihood', {})
            prob_event = likelihood.get('probability_of_event')
            prob_exceed = likelihood.get('probability_exceeding')
            if prob_event is not None:
                ttk.Label(var_frame, text=f"  • Chance of Event (>1mm): {prob_event:.0%}", style='Results.TLabel').pack(anchor='w')
            elif prob_exceed is not None:
                ttk.Label(var_frame, text=f"  • Chance of Extreme Conditions: {prob_exceed:.0%}", style='Results.TLabel').pack(anchor='w')

if __name__ == "__main__":
    root = tk.Tk()
    app = TerraClimeApp(root)
    root.mainloop()