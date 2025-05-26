#!/usr/bin/env python3
"""
OTA Daemon Manager GUI
A Tkinter-based tool for monitoring and controlling the OTA daemon.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
import threading
import time
import os
import sys
import socketio
from datetime import datetime

class DaemonManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OTA Daemon Manager")
        self.root.geometry("900x700")
        
        # Configuration
        self.api_base_url = "http://localhost:5000/api/v1"
        self.api_key = "admin-key-example"  # Default API key
        self.websocket_url = "http://localhost:5000"
        
        # Status variables
        self.connection_status = tk.StringVar(value="Disconnected")
        self.daemon_status = tk.StringVar(value="Unknown")
        self.current_version = tk.StringVar(value="Unknown")
        self.update_available = tk.StringVar(value="No")
        self.available_version = tk.StringVar(value="N/A")
        
        # WebSocket client
        self.sio = None
        self.websocket_connected = False
        
        self.setup_ui()
        self.start_status_monitoring()
        self.connect_websocket()
        
    def setup_ui(self):
        # Create main notebook
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status Tab
        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text="Status")
        self.setup_status_tab(status_frame)
        
        # Update Tab
        update_frame = ttk.Frame(notebook)
        notebook.add(update_frame, text="Updates")
        self.setup_update_tab(update_frame)
        
        # Logs Tab
        logs_frame = ttk.Frame(notebook)
        notebook.add(logs_frame, text="Logs")
        self.setup_logs_tab(logs_frame)
        
        # Settings Tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        self.setup_settings_tab(settings_frame)
        
    def setup_status_tab(self, parent):
        # Connection Status
        conn_frame = ttk.LabelFrame(parent, text="Connection Status")
        conn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Status indicators
        status_grid = ttk.Frame(conn_frame)
        status_grid.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(status_grid, text="API Connection:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.connection_label = ttk.Label(status_grid, textvariable=self.connection_status, foreground="red")
        self.connection_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(status_grid, text="Daemon Status:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.daemon_label = ttk.Label(status_grid, textvariable=self.daemon_status)
        self.daemon_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(status_grid, text="Current Version:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(status_grid, textvariable=self.current_version).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(status_grid, text="Update Available:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.update_label = ttk.Label(status_grid, textvariable=self.update_available)
        self.update_label.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(status_grid, text="Available Version:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(status_grid, textvariable=self.available_version).grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Control buttons
        control_frame = ttk.LabelFrame(parent, text="Daemon Control")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(pady=10)
        
        ttk.Button(buttons_frame, text="Refresh Status", 
                  command=self.refresh_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Reconnect WebSocket", 
                  command=self.connect_websocket).pack(side=tk.LEFT, padx=5)
        
        # System Information
        info_frame = ttk.LabelFrame(parent, text="System Information")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.info_text = scrolledtext.ScrolledText(info_frame, height=10, state=tk.DISABLED)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_update_tab(self, parent):
        # Update Control
        control_frame = ttk.LabelFrame(parent, text="Update Control")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(pady=10)
        
        ttk.Button(buttons_frame, text="Check for Updates", 
                  command=self.check_updates).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Install Update", 
                  command=self.install_update).pack(side=tk.LEFT, padx=5)
        
        # Update Progress
        progress_frame = ttk.LabelFrame(parent, text="Update Progress")
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.pack(pady=10)
        
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.pack(pady=5)
        
        # Update History
        history_frame = ttk.LabelFrame(parent, text="Update History")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # History tree
        columns = ("Date", "Type", "Version", "Status")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=150)
            
        self.history_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Refresh history button
        ttk.Button(history_frame, text="Refresh History", 
                  command=self.refresh_history).pack(pady=5)
        
    def setup_logs_tab(self, parent):
        # Log Control
        control_frame = ttk.LabelFrame(parent, text="Log Control")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(pady=5)
        
        ttk.Button(buttons_frame, text="Refresh Logs", 
                  command=self.refresh_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Clear Display", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        
        # Log display
        logs_frame = ttk.LabelFrame(parent, text="System Logs")
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=20, font=("Courier", 9))
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_settings_tab(self, parent):
        # API Configuration
        api_frame = ttk.LabelFrame(parent, text="API Configuration")
        api_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(api_frame, text="API Base URL:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.api_url_var = tk.StringVar(value=self.api_base_url)
        ttk.Entry(api_frame, textvariable=self.api_url_var, width=50).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(api_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.api_key_var = tk.StringVar(value=self.api_key)
        ttk.Entry(api_frame, textvariable=self.api_key_var, width=50, show="*").grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        api_frame.columnconfigure(1, weight=1)
        
        ttk.Button(api_frame, text="Save Settings", 
                  command=self.save_settings).grid(row=2, column=1, sticky=tk.E, padx=5, pady=10)
        
        # WebSocket Events
        events_frame = ttk.LabelFrame(parent, text="WebSocket Events")
        events_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.events_text = scrolledtext.ScrolledText(events_frame, height=15, font=("Courier", 9))
        self.events_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(events_frame, text="Clear Events", 
                  command=self.clear_events).pack(pady=5)
        
    def start_status_monitoring(self):
        """Start background thread for status monitoring"""
        def monitor():
            while True:
                self.refresh_status_background()
                time.sleep(10)  # Update every 10 seconds
                
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        
    def refresh_status_background(self):
        """Background status refresh"""
        try:
            response = requests.get(f"{self.api_base_url}/status", 
                                  headers={"X-API-Key": self.api_key}, 
                                  timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # Update UI in main thread
                self.root.after(0, self.update_status_display, data, True)
            else:
                self.root.after(0, self.update_status_display, None, False)
        except Exception:
            self.root.after(0, self.update_status_display, None, False)
            
    def update_status_display(self, data, connected):
        """Update status display in main thread"""
        if connected and data:
            self.connection_status.set("Connected")
            self.connection_label.config(foreground="green")
            
            self.daemon_status.set(data.get("status", "Unknown"))
            self.current_version.set(data.get("current_version", "Unknown"))
            
            # Check for updates
            last_check = data.get("last_check", {})
            if last_check and last_check.get("update_available"):
                self.update_available.set("Yes")
                self.update_label.config(foreground="orange")
                self.available_version.set(last_check.get("version", "Unknown"))
            else:
                self.update_available.set("No")
                self.update_label.config(foreground="green")
                self.available_version.set("N/A")
                
            # Update info display
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, json.dumps(data, indent=2))
            self.info_text.config(state=tk.DISABLED)
        else:
            self.connection_status.set("Disconnected")
            self.connection_label.config(foreground="red")
            self.daemon_status.set("Unknown")
            
    def refresh_status(self):
        """Manual status refresh"""
        self.refresh_status_background()
        
    def check_updates(self):
        """Trigger update check"""
        try:
            self.progress_label.config(text="Checking for updates...")
            self.progress_var.set(50)
            
            response = requests.post(f"{self.api_base_url}/check", 
                                   headers={"X-API-Key": self.api_key}, 
                                   timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.progress_var.set(100)
                
                if data.get("update_available"):
                    self.progress_label.config(text=f"Update available: {data.get('version')}")
                    messagebox.showinfo("Update Available", 
                                      f"Update {data.get('version')} is available!")
                else:
                    self.progress_label.config(text="No updates available")
                    messagebox.showinfo("No Updates", "No updates are currently available.")
            else:
                self.progress_label.config(text="Check failed")
                messagebox.showerror("Error", f"Failed to check for updates: {response.status_code}")
                
        except Exception as e:
            self.progress_label.config(text="Check failed")
            messagebox.showerror("Error", f"Failed to check for updates: {str(e)}")
        finally:
            self.progress_var.set(0)
            
    def install_update(self):
        """Install available update"""
        result = messagebox.askyesno("Confirm Installation", 
                                   "Are you sure you want to install the available update?")
        if not result:
            return
            
        try:
            self.progress_label.config(text="Installing update...")
            self.progress_var.set(25)
            
            response = requests.post(f"{self.api_base_url}/apply", 
                                   headers={"X-API-Key": self.api_key}, 
                                   timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.progress_var.set(100)
                
                if data.get("success"):
                    self.progress_label.config(text=f"Update {data.get('version')} installed successfully")
                    messagebox.showinfo("Success", "Update installed successfully!")
                else:
                    self.progress_label.config(text="Installation failed")
                    messagebox.showerror("Error", f"Installation failed: {data.get('error')}")
            else:
                self.progress_label.config(text="Installation failed")
                messagebox.showerror("Error", f"Failed to install update: {response.status_code}")
                
        except Exception as e:
            self.progress_label.config(text="Installation failed")
            messagebox.showerror("Error", f"Failed to install update: {str(e)}")
        finally:
            self.progress_var.set(0)
            
    def refresh_history(self):
        """Refresh update history"""
        try:
            response = requests.get(f"{self.api_base_url}/history", 
                                  headers={"X-API-Key": self.api_key}, 
                                  timeout=10)
            
            if response.status_code == 200:
                history = response.json()
                
                # Clear existing items
                for item in self.history_tree.get_children():
                    self.history_tree.delete(item)
                    
                # Add history items
                for item in history:
                    timestamp = item.get("timestamp", "Unknown")
                    check_type = item.get("check_type", "Unknown")
                    version = item.get("version", "N/A")
                    status = "Success" if item.get("success") else "Failed"
                    
                    self.history_tree.insert("", 0, values=(timestamp, check_type, version, status))
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh history: {str(e)}")
            
    def refresh_logs(self):
        """Refresh system logs"""
        try:
            # Use journalctl to get recent OTA logs
            import subprocess
            result = subprocess.run(["sudo", "journalctl", "-u", "ota", "-n", "100", "--no-pager"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.logs_text.delete(1.0, tk.END)
                self.logs_text.insert(1.0, result.stdout)
                self.logs_text.see(tk.END)
            else:
                messagebox.showerror("Error", "Failed to retrieve logs")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh logs: {str(e)}")
            
    def clear_logs(self):
        """Clear log display"""
        self.logs_text.delete(1.0, tk.END)
        
    def clear_events(self):
        """Clear events display"""
        self.events_text.delete(1.0, tk.END)
        
    def save_settings(self):
        """Save API settings"""
        self.api_base_url = self.api_url_var.get()
        self.api_key = self.api_key_var.get()
        messagebox.showinfo("Settings", "Settings saved successfully!")
        
    def connect_websocket(self):
        """Connect to WebSocket server"""
        try:
            if self.sio:
                self.sio.disconnect()
                
            self.sio = socketio.Client()
            
            @self.sio.event
            def connect():
                self.websocket_connected = True
                self.log_event("WebSocket connected")
                
            @self.sio.event
            def disconnect():
                self.websocket_connected = False
                self.log_event("WebSocket disconnected")
                
            @self.sio.on("update_check_complete")
            def on_update_check(data):
                self.log_event(f"Update check complete: {data}")
                
            @self.sio.on("update_applied")
            def on_update_applied(data):
                self.log_event(f"Update applied: {data}")
                
            self.sio.connect(self.websocket_url)
            
        except Exception as e:
            self.log_event(f"WebSocket connection failed: {str(e)}")
            
    def log_event(self, message):
        """Log WebSocket event"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.events_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.events_text.see(tk.END)


def main():
    # Check if running in X11 environment
    if not os.environ.get('DISPLAY'):
        print("Error: No X11 display available. Please run in a graphical environment.")
        sys.exit(1)
        
    root = tk.Tk()
    app = DaemonManagerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 