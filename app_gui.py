# app_gui.py

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import calendar
from datetime import date

# --- Configuration ---
API_URL = "http://127.0.0.1:8000/analyze"

AVAILABLE_VARIABLES = [
    "max_temp_c",
    "min_temp_c",
    "precipitation_mm",
    "wind_speed_kph",
    "dust_ug_m3",
]

FRIENDLY_VAR_INFO = {
    "max_temp_c": ("Max Temperature", "°C"),
    "min_temp_c": ("Min Temperature", "°C"),
    "precipitation_mm": ("Precipitation", "mm/day"),
    "wind_speed_kph": ("Wind Speed", "km/h"),
    "dust_ug_m3": ("Dust", "µg/m³"),
}

EXAMPLE_LOCATIONS = [
    ("Yosemite Valley, USA", 37.74, -119.59),
    ("New Delhi, India", 28.61, 77.21),
    ("Nairobi, Kenya", -1.29, 36.82),
    ("Sydney, Australia", -33.87, 151.21),
    ("London, UK", 51.51, -0.13),
]

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


class TerraClimeApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("TerraClime Planner")
        self.root.minsize(720, 560)

        # Styling
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self.style.configure("TButton", font=("Segoe UI", 10), padding=6)
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 10, "italic"))
        self.style.configure("Results.TLabel", font=("Segoe UI", 10))

        self._build_layout()

    # ---------- UI Construction ----------
    def _build_layout(self):
        container = ttk.Frame(self.root, padding=14)
        container.pack(fill=tk.BOTH, expand=True)

        # Header
        header = ttk.Frame(container)
        header.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(header, text="TerraClime Planner", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Estimate the likelihood of weather conditions for a location and date using NASA MERRA‑2",
            style="SubHeader.TLabel",
        ).pack(anchor="w")

        # Inputs
        inputs = ttk.LabelFrame(container, text="Query Parameters", padding=12)
        inputs.pack(fill=tk.X)

        # Location row
        ttk.Label(inputs, text="Latitude").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.lat_var = tk.StringVar(value="37.74")
        self.lat_entry = ttk.Entry(inputs, textvariable=self.lat_var, width=12)
        self.lat_entry.grid(row=0, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(inputs, text="Longitude").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        self.lon_var = tk.StringVar(value="-119.59")
        self.lon_entry = ttk.Entry(inputs, textvariable=self.lon_var, width=12)
        self.lon_entry.grid(row=0, column=3, sticky="w", padx=4, pady=4)

        ttk.Label(inputs, text="Examples").grid(row=0, column=4, sticky="w", padx=4, pady=4)
        self.example_var = tk.StringVar(value=EXAMPLE_LOCATIONS[0][0])
        self.example_combo = ttk.Combobox(
            inputs, textvariable=self.example_var, values=[n for n, _, _ in EXAMPLE_LOCATIONS], width=26, state="readonly"
        )
        self.example_combo.grid(row=0, column=5, sticky="w", padx=4, pady=4)
        self.example_combo.bind("<<ComboboxSelected>>", self._on_example_change)

        # Date row
        ttk.Label(inputs, text="Month").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.month_var = tk.StringVar(value="July")
        self.month_combo = ttk.Combobox(inputs, textvariable=self.month_var, values=MONTHS, width=12, state="readonly")
        self.month_combo.grid(row=1, column=1, sticky="w", padx=4, pady=4)
        self.month_combo.bind("<<ComboboxSelected>>", self._on_month_change)

        ttk.Label(inputs, text="Day").grid(row=1, column=2, sticky="w", padx=4, pady=4)
        self.day_var = tk.StringVar(value="15")
        self.day_spin = ttk.Spinbox(inputs, from_=1, to=31, textvariable=self.day_var, width=6)
        self.day_spin.grid(row=1, column=3, sticky="w", padx=4, pady=4)

        # Variables row
        vars_frame = ttk.LabelFrame(inputs, text="Variables", padding=8)
        vars_frame.grid(row=2, column=0, columnspan=6, sticky="we", padx=2, pady=(10, 0))
        vars_frame.grid_columnconfigure(0, weight=1)
        self.check_vars = {}
        for i, var in enumerate(AVAILABLE_VARIABLES):
            self.check_vars[var] = tk.BooleanVar(value=(var in ("max_temp_c", "precipitation_mm")))
            label = FRIENDLY_VAR_INFO.get(var, (var, ""))[0]
            ttk.Checkbutton(vars_frame, text=label, variable=self.check_vars[var]).grid(row=i // 3, column=i % 3, sticky="w", padx=6, pady=4)

        vars_actions = ttk.Frame(vars_frame)
        vars_actions.grid(row=(len(AVAILABLE_VARIABLES) // 3) + 1, column=0, columnspan=3, sticky="w", pady=(6, 0))
        ttk.Button(vars_actions, text="Select All", command=self._select_all_vars).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(vars_actions, text="Clear", command=self._clear_vars).pack(side=tk.LEFT)

        # Actions
        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=10)

        self.analyze_button = ttk.Button(actions, text="Analyze Climate", command=self._start_analysis_thread)
        self.analyze_button.pack(side=tk.LEFT)
        ttk.Button(actions, text="Clear Results", command=self._clear_results).pack(side=tk.LEFT, padx=8)

        # Progress + Status
        self.progress = ttk.Progressbar(actions, mode="indeterminate", length=180)
        self.progress.pack(side=tk.LEFT, padx=10)
        self.status_label = ttk.Label(actions, text="")
        self.status_label.pack(side=tk.LEFT, padx=6)

        # Results area: Treeview inside a scrollable frame
        results_container = ttk.LabelFrame(container, text="Analysis Results", padding=10)
        results_container.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(results_container, columns=("var", "mean", "std", "like", "n"), show="headings", height=12)
        self.tree.heading("var", text="Variable")
        self.tree.heading("mean", text="Average")
        self.tree.heading("std", text="Std Dev")
        self.tree.heading("like", text="Likelihood")
        self.tree.heading("n", text="Data Points")

        self.tree.column("var", width=160, anchor="w")
        self.tree.column("mean", width=130, anchor="center")
        self.tree.column("std", width=100, anchor="center")
        self.tree.column("like", width=160, anchor="center")
        self.tree.column("n", width=100, anchor="center")

        y_scroll = ttk.Scrollbar(results_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=y_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.placeholder = ttk.Label(results_container, text="Results will appear here after analysis.", style="Results.TLabel", foreground="gray")
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")

    # ---------- Helpers ----------
    def _select_all_vars(self):
        for v in self.check_vars.values():
            v.set(True)

    def _clear_vars(self):
        for v in self.check_vars.values():
            v.set(False)

    def _clear_results(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")

    def _on_example_change(self, _event=None):
        name = self.example_var.get()
        for n, la, lo in EXAMPLE_LOCATIONS:
            if n == name:
                self.lat_var.set(f"{la}")
                self.lon_var.set(f"{lo}")
                break

    def _on_month_change(self, _event=None):
        month = MONTHS.index(self.month_var.get()) + 1
        # Use leap year to allow Feb 29 if desired in historical analysis
        _, last_day = calendar.monthrange(2020, month)
        try:
            current = int(self.day_var.get())
        except ValueError:
            current = 1
        new_day = min(max(1, current), last_day)
        self.day_var.set(str(new_day))
        self.day_spin.configure(from_=1, to=last_day)

    def _set_inputs_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for w in [self.lat_entry, self.lon_entry, self.month_combo, self.day_spin, self.example_combo, self.analyze_button]:
            try:
                w.configure(state=state)
            except Exception:
                pass
        # Checkbuttons
        for var in self.check_vars:
            cb_state = state
            # Access associated checkbutton via variable tracing not stored; instead disable parent frame children
        # Disable variable checkbuttons by traversing from parent
        # Simple approach: disable inputs frame entirely is too broad; skip for simplicity.

    # ---------- Analysis ----------
    def _start_analysis_thread(self):
        # Validate inputs before starting thread
        try:
            lat = float(self.lat_var.get())
            lon = float(self.lon_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Latitude and Longitude must be numeric.")
            return

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            messagebox.showerror("Invalid Input", "Latitude must be between -90 and 90, longitude between -180 and 180.")
            return

        month = MONTHS.index(self.month_var.get()) + 1
        try:
            day = int(self.day_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Day must be an integer.")
            return

        _, last_day = calendar.monthrange(2020, month)
        if day < 1 or day > last_day:
            messagebox.showerror("Invalid Input", f"Day must be between 1 and {last_day} for {self.month_var.get()}.")
            return

        selected = [v for v, s in self.check_vars.items() if s.get()]
        if not selected:
            messagebox.showwarning("No Selection", "Select at least one variable to analyze.")
            return

        self._set_inputs_enabled(False)
        self.progress.start(12)
        self.status_label.config(text="Fetching NASA data…")

        payload = {
            "latitude": lat,
            "longitude": lon,
            "month": month,
            "day": day,
            "variables": selected,
        }

        thread = threading.Thread(target=self._run_analysis, args=(payload,))
        thread.daemon = True
        thread.start()

    def _run_analysis(self, payload: dict):
        try:
            resp = requests.post(API_URL, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            self.root.after(0, lambda: messagebox.showerror("API Error", f"Could not get data from the backend.\n\nError: {e}"))
            self.root.after(0, self._reset_ui_state)
            return

        self.root.after(0, lambda d=data: self._display_results(d))
        self.root.after(0, self._reset_ui_state)

    def _reset_ui_state(self):
        self.progress.stop()
        self.status_label.config(text="")
        self._set_inputs_enabled(True)

    # ---------- Results Rendering ----------
    def _display_results(self, data: dict):
        # Clear table
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.placeholder.place_forget()

        results = data.get("results", [])
        if not results:
            self.placeholder.config(text="No results returned for the selected parameters.")
            self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
            return

        for res in results:
            var_key = res.get("variable", "N/A")
            title, unit = FRIENDLY_VAR_INFO.get(var_key, (var_key, res.get("unit", "")))
            mean = res.get("mean", 0.0)
            stdv = res.get("std_dev", 0.0)
            n = res.get("raw_data_points", 0)
            like = res.get("likelihood", {})
            if like.get("probability_of_event") is not None:
                like_text = f"Event: {like['probability_of_event']:.0%}"
            elif like.get("probability_exceeding") is not None:
                like_text = f"Exceedance: {like['probability_exceeding']:.0%}"
            else:
                like_text = "—"

            mean_text = f"{mean:.2f} {unit}" if unit else f"{mean:.2f}"
            std_text = f"{stdv:.2f}"

            self.tree.insert("", tk.END, values=(title, mean_text, std_text, like_text, n))


if __name__ == "__main__":
    root = tk.Tk()
    app = TerraClimeApp(root)
    root.mainloop()
