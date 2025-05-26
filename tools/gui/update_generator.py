#!/usr/bin/env python3
"""
OTA Update Package Generator GUI
A Tkinter-based tool for creating test update packages and manifests.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import sys
import hashlib
import zipfile
from datetime import datetime
import requests
from pathlib import Path

class UpdateGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OTA Update Package Generator")
        self.root.geometry("800x600")
        
        # Variables
        self.product_type = tk.StringVar(value="robot-ai-standard")
        self.version = tk.StringVar(value="1.0.0")
        self.download_url = tk.StringVar()
        self.release_notes = tk.StringVar()
        self.selected_files = []
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Package Creation Tab
        package_frame = ttk.Frame(notebook)
        notebook.add(package_frame, text="Create Package")
        self.setup_package_tab(package_frame)
        
        # Manifest Generator Tab
        manifest_frame = ttk.Frame(notebook)
        notebook.add(manifest_frame, text="Generate Manifest")
        self.setup_manifest_tab(manifest_frame)
        
    def setup_package_tab(self, parent):
        # Product Type Selection
        product_frame = ttk.LabelFrame(parent, text="Product Configuration")
        product_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(product_frame, text="Product Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        product_combo = ttk.Combobox(product_frame, textvariable=self.product_type, 
                                   values=["robot-ai-standard", "robot-ai-advanced", "robot-ai-lite"])
        product_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(product_frame, text="Version:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        version_entry = ttk.Entry(product_frame, textvariable=self.version)
        version_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        product_frame.columnconfigure(1, weight=1)
        
        # File Selection
        files_frame = ttk.LabelFrame(parent, text="Package Contents")
        files_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # File list
        self.files_listbox = tk.Listbox(files_frame, height=8)
        self.files_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # File buttons
        file_buttons_frame = ttk.Frame(files_frame)
        file_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(file_buttons_frame, text="Add Files", command=self.add_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_buttons_frame, text="Add Directory", command=self.add_directory).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_buttons_frame, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_buttons_frame, text="Clear All", command=self.clear_files).pack(side=tk.LEFT, padx=2)
        
        # Package Creation
        create_frame = ttk.LabelFrame(parent, text="Create Package")
        create_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(create_frame, text="Create Update Package", 
                  command=self.create_package).pack(pady=10)
        
    def setup_manifest_tab(self, parent):
        # Manifest Configuration
        config_frame = ttk.LabelFrame(parent, text="Manifest Configuration")
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Basic info
        ttk.Label(config_frame, text="Product Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(config_frame, textvariable=self.product_type).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(config_frame, text="Version:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(config_frame, textvariable=self.version).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(config_frame, text="Download URL:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(config_frame, textvariable=self.download_url).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        
        config_frame.columnconfigure(1, weight=1)
        
        # Release Notes
        notes_frame = ttk.LabelFrame(parent, text="Release Notes")
        notes_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.release_notes_text = scrolledtext.ScrolledText(notes_frame, height=10)
        self.release_notes_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Generate Manifest
        generate_frame = ttk.LabelFrame(parent, text="Generate Manifest")
        generate_frame.pack(fill=tk.X, padx=5, pady=5)
        
        buttons_frame = ttk.Frame(generate_frame)
        buttons_frame.pack(pady=10)
        
        ttk.Button(buttons_frame, text="Generate Manifest", 
                  command=self.generate_manifest).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Save Manifest", 
                  command=self.save_manifest).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Upload to Test Server", 
                  command=self.upload_manifest).pack(side=tk.LEFT, padx=5)
        
    def add_files(self):
        files = filedialog.askopenfilenames(title="Select files to include in update package")
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
                self.files_listbox.insert(tk.END, os.path.basename(file))
                
    def add_directory(self):
        directory = filedialog.askdirectory(title="Select directory to include in update package")
        if directory:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file_path not in self.selected_files:
                        self.selected_files.append(file_path)
                        relative_path = os.path.relpath(file_path, directory)
                        self.files_listbox.insert(tk.END, f"{os.path.basename(directory)}/{relative_path}")
                        
    def remove_selected(self):
        selection = self.files_listbox.curselection()
        if selection:
            index = selection[0]
            self.files_listbox.delete(index)
            del self.selected_files[index]
            
    def clear_files(self):
        self.files_listbox.delete(0, tk.END)
        self.selected_files.clear()
        
    def create_package(self):
        if not self.selected_files:
            messagebox.showwarning("Warning", "Please select files to include in the package")
            return
            
        if not self.version.get():
            messagebox.showwarning("Warning", "Please specify a version")
            return
            
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            title="Save update package as",
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        
        if not filename:
            return
            
        try:
            # Create ZIP package
            with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in self.selected_files:
                    if os.path.isfile(file_path):
                        # Add file to ZIP with relative path
                        arcname = os.path.basename(file_path)
                        zipf.write(file_path, arcname)
                        
            # Calculate checksum
            checksum = self.calculate_checksum(filename)
            
            messagebox.showinfo("Success", 
                              f"Package created successfully!\n\n"
                              f"Location: {filename}\n"
                              f"Checksum: {checksum}")
                              
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create package: {str(e)}")
            
    def calculate_checksum(self, filename):
        hash_sha256 = hashlib.sha256()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
        
    def generate_manifest(self):
        if not self.version.get():
            messagebox.showwarning("Warning", "Please specify a version")
            return
            
        manifest = {
            "version": self.version.get(),
            "product_type": self.product_type.get(),
            "release_date": datetime.now().isoformat(),
            "release_notes": self.release_notes_text.get(1.0, tk.END).strip(),
            "download_url": self.download_url.get(),
            "checksum": "to_be_calculated",
            "size": 0,
            "critical_update": False,
            "rollback_supported": True,
            "dependencies": [],
            "post_install_actions": [
                {
                    "type": "restart_service",
                    "service": "robot-ai"
                }
            ]
        }
        
        # Show generated manifest in a new window
        self.show_manifest(manifest)
        
    def show_manifest(self, manifest):
        manifest_window = tk.Toplevel(self.root)
        manifest_window.title("Generated Manifest")
        manifest_window.geometry("600x500")
        
        text_widget = scrolledtext.ScrolledText(manifest_window)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget.insert(1.0, json.dumps(manifest, indent=2))
        text_widget.config(state=tk.DISABLED)
        
        # Store manifest for saving
        self.current_manifest = manifest
        
    def save_manifest(self):
        if not hasattr(self, 'current_manifest'):
            messagebox.showwarning("Warning", "Please generate a manifest first")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Save manifest as",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.current_manifest, f, indent=2)
                messagebox.showinfo("Success", f"Manifest saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save manifest: {str(e)}")
                
    def upload_manifest(self):
        if not hasattr(self, 'current_manifest'):
            messagebox.showwarning("Warning", "Please generate a manifest first")
            return
            
        # For testing, save to the OTA cache directory
        cache_dir = "/var/lib/ota/cache"
        manifest_path = os.path.join(cache_dir, "latest_manifest.json")
        
        try:
            # Ensure directory exists
            os.makedirs(cache_dir, exist_ok=True)
            
            with open(manifest_path, 'w') as f:
                json.dump(self.current_manifest, f, indent=2)
                
            messagebox.showinfo("Success", 
                              f"Manifest uploaded to test server!\n\n"
                              f"Location: {manifest_path}\n"
                              f"The OTA daemon will detect this on next update check.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload manifest: {str(e)}")


def main():
    # Check if running in X11 environment
    if not os.environ.get('DISPLAY'):
        print("Error: No X11 display available. Please run in a graphical environment.")
        sys.exit(1)
        
    root = tk.Tk()
    app = UpdateGeneratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 