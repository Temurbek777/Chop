import sys
import time
import cups
import os
import getpass
import customtkinter as ctk
from tkinter import ttk, messagebox
from threading import Thread
import pyudev
import psutil

class USBMonitor(Thread):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.daemon = True  # Thread terminates when app closes

    def run(self):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='block')
        for device in iter(monitor.poll, None):
            if (device.get('DEVTYPE') == 'partition' and
                'ID_BUS' in device.parent.properties and
                device.parent.properties['ID_BUS'] == 'usb' and
                device.get('ID_FS_USAGE') == 'filesystem'):
                if device.action == 'add':
                    for _ in range(50):  # check for ~5 seconds
                        for partition in psutil.disk_partitions():
                            if partition.device == device.device_node:
                                print(f"Mount point found: {partition.mountpoint}")
                                self.app.show_files(partition.mountpoint)
                                return
                        time.sleep(0.1)  # small wait instead of fixed 5 sec
                    print(f"USB detected: {device.device_node}")
                    for partition in psutil.disk_partitions():
                        if partition.device == device.device_node:
                            print(f"Mount point found: {partition.mountpoint}")
                            self.app.show_files(partition.mountpoint)
                            break
                    else:
                        username = getpass.getuser()
                        media_path = f"/media/{username}"
                        if os.path.exists(media_path):
                            for folder in os.listdir(media_path):
                                full_path = os.path.join(media_path, folder)
                                if os.path.ismount(full_path):
                                    print(f"Fallback mount point: {full_path}")
                                    self.app.show_files(full_path)
                                    break
                        else:
                            print("No mount point found")
                elif device.action == 'remove':
                    print(f"USB removed: {device.device_node}")
                    for partition in psutil.disk_partitions(all=True):
                        if partition.device == device.device_node:
                            print(f"Removed mount point: {partition.mountpoint}")
                            self.app.handle_usb_removal(partition.mountpoint)
                            break

class PrintSettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Print Settings")
        self.geometry("400x500")
        self.transient(parent)  # Make dialog modal
        self.after(100, self.grab_set)  # Delay grab_set to ensure window is viewable
        self.result = None

        # Printer selection
        self.printer_label = ctk.CTkLabel(self, text="Printer:")
        self.printer_label.pack(pady=5)
        self.printer_combo = ctk.CTkComboBox(self, values=["Select a printer"])
        try:
            conn = cups.Connection()
            printers = list(conn.getPrinters().keys())
            self.printer_combo.configure(values=["Select a printer"] + printers)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load printers: {e}", parent=self)
        self.printer_combo.pack(pady=5)

        # Copies
        self.copies_label = ctk.CTkLabel(self, text="Copies:")
        self.copies_label.pack(pady=5)
        self.copies_spin = ctk.CTkEntry(self, placeholder_text="1")
        self.copies_spin.insert(0, "1")
        self.copies_spin.pack(pady=5)

        # Duplex
        self.duplex_label = ctk.CTkLabel(self, text="Duplex:")
        self.duplex_label.pack(pady=5)
        self.duplex_combo = ctk.CTkComboBox(self, values=["One-Sided", "Two-Sided (Long Edge)", "Two-Sided (Short Edge)"])
        self.duplex_combo.pack(pady=5)

        # Orientation
        self.orientation_label = ctk.CTkLabel(self, text="Orientation:")
        self.orientation_label.pack(pady=5)
        self.orientation_combo = ctk.CTkComboBox(self, values=["Portrait", "Landscape"])
        self.orientation_combo.pack(pady=5)

        # Page size
        self.page_size_label = ctk.CTkLabel(self, text="Page Size:")
        self.page_size_label.pack(pady=5)
        self.page_size_combo = ctk.CTkComboBox(self, values=["A4", "Letter", "Legal"])
        self.page_size_combo.pack(pady=5)

        # Page range
        self.page_range_label = ctk.CTkLabel(self, text="Page Range (e.g., 1-4):")
        self.page_range_label.pack(pady=5)
        self.page_range_entry = ctk.CTkEntry(self, placeholder_text="e.g., 1-4, 7, 9-12")
        self.page_range_entry.pack(pady=5)

        # Color mode
        self.color_mode_label = ctk.CTkLabel(self, text="Color Mode:")
        self.color_mode_label.pack(pady=5)
        self.color_mode_combo = ctk.CTkComboBox(self, values=["Monochrome"])
        self.color_mode_combo.pack(pady=5)

        # Collate
        self.collate_check = ctk.CTkCheckBox(self, text="Collate")
        self.collate_check.select()
        self.collate_check.pack(pady=5)

        # Buttons
        self.ok_button = ctk.CTkButton(self, text="OK", command=self.on_ok)
        self.ok_button.pack(pady=10)
        self.cancel_button = ctk.CTkButton(self, text="Cancel", command=self.on_cancel)
        self.cancel_button.pack(pady=5)

    def on_ok(self):
        try:
            copies = int(self.copies_spin.get())
            if copies < 1 or copies > 99:
                raise ValueError("Copies must be between 1 and 99")
            printer_name = self.printer_combo.get()
            if printer_name == "Select a printer":
                raise ValueError("Please select a printer")
            options = {
                'copies': str(copies),
                'sides': {
                    "One-Sided": "one-sided",
                    "Two-Sided (Long Edge)": "two-sided-long-edge",
                    "Two-Sided (Short Edge)": "two-sided-short-edge"
                }[self.duplex_combo.get()],
                'orientation-requested': '3' if self.orientation_combo.get() == "Portrait" else '4',
                'media': self.page_size_combo.get().lower(),
                'print-color-mode': 'monochrome' if self.color_mode_combo.get() == "Monochrome" else 'color',
                'collate': 'true' if self.collate_check.get() else 'false'
            }
            page_range = self.page_range_entry.get().strip()
            if page_range:
                options['page-ranges'] = page_range
            self.result = (printer_name, options)
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self)

    def on_cancel(self):
        self.result = None
        self.destroy()

class PrintApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Flash Drive Printer")

        # Use fullscreen but keep window manager buttons
        self.attributes("-fullscreen", True)
        self.resizable(True, True)

        # Press ESC or Alt+F4 to quit
        self.bind("<Escape>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # Initial label
        self.label = ctk.CTkLabel(self, text="Insert the Flash drive and print", font=("Arial", 30))
        self.label.pack(expand=True)

        # File tree and button (initialized later)
        self.tree = None
        self.print_btn = None
        self.current_mount_path = None

        # Start USB monitoring
        self.monitor = USBMonitor(self)
        self.monitor.start()

        # Keyboard shortcut to exit
        self.bind('<q>', lambda event: self.destroy())

    def show_files(self, mount_path):
        if not os.path.exists(mount_path) or not os.access(mount_path, os.R_OK):
            print(f"Cannot access mount path: {mount_path}")
            return
        self.current_mount_path = mount_path

        # Clear initial label
        self.label.pack_forget()

        # Create tree view
        if self.tree:
            self.tree.destroy()
        self.tree = ttk.Treeview(self, columns=("Name", "Size"), show="tree headings")
        self.tree.heading("Name", text="File Name")
        self.tree.heading("Size", text="Size (KB)")
        self.tree.column("Name", width=400)
        self.tree.column("Size", width=100)
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

        # Populate tree with files
        allowed_extensions = ('.pdf', '.txt', '.jpg', '.jpeg', '.png')
        for root, dirs, files in os.walk(mount_path):
            rel_path = os.path.relpath(root, mount_path)
            parent = "" if rel_path == "." else rel_path.replace(os.sep, "/")
            for file in files:
                if file.lower().endswith(allowed_extensions):
                    file_path = os.path.join(root, file)
                    size = os.path.getsize(file_path) / 1024  # Size in KB
                    self.tree.insert(parent, "end", text=file, values=(file, f"{size:.2f}"))

        # Print button
        if self.print_btn:
            self.print_btn.destroy()
        self.print_btn = ctk.CTkButton(self, text="Print Settings", command=self.open_print_settings, state="disabled")
        self.print_btn.pack(pady=10)

        # Enable button on file selection
        self.tree.bind('<<TreeviewSelect>>', self.check_selection)

    def handle_usb_removal(self, mount_path):
        if mount_path == self.current_mount_path:
            if self.tree:
                self.tree.destroy()
                self.tree = None
            if self.print_btn:
                self.print_btn.destroy()
                self.print_btn = None
            self.label.pack(expand=True)
            self.current_mount_path = None

    def check_selection(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            path = os.path.join(self.current_mount_path, item['text'])
            if os.path.isfile(path):
                self.print_btn.configure(state="normal")
            else:
                self.print_btn.configure(state="disabled")
        else:
            self.print_btn.configure(state="disabled")

    def open_print_settings(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        file_path = os.path.join(self.current_mount_path, item['text'])

        if not os.path.isfile(file_path) or not os.access(file_path, os.R_OK):
            messagebox.showerror("Error", f"Cannot access file: {file_path}", parent=self)
            return

        dialog = PrintSettingsDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            printer_name, options = dialog.result
            try:
                conn = cups.Connection()
                if printer_name not in conn.getPrinters():
                    raise ValueError(f"Printer '{printer_name}' not found in CUPS.")
                job_id = conn.printFile(printer_name, file_path, "Flash Drive Print Job", options=options)
                messagebox.showinfo("Success", f"File sent to printer! Job ID: {job_id}. Check status with 'lpstat -p {printer_name} -o'.", parent=self)
            except cups.IPPError as e:
                messagebox.showerror("Error", f"CUPS IPP Error: {e}", parent=self)
            except ValueError as e:
                messagebox.showerror("Error", str(e), parent=self)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to print: {e}", parent=self)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")  # Optional: dark theme
    app = PrintApp()
    app.mainloop()