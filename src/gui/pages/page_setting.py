import logging
import tkinter
import customtkinter
import plistlib
import os
import sys
import winreg
import platform
import subprocess
from src.app import App
from pathlib import Path
from tkinter import messagebox
from src.config_manager import ConfigManager
from src.controllers import MouseController
from functools import partial
import tkinter as tk

APP_NAME = 'FaceCommander'
logger = logging.getLogger("PageSetting")

class PageSetting(customtkinter.CTkFrame):

    def __init__(self, master, master_callback:callable, **kwargs):
        super().__init__(master, **kwargs)

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.os_type = platform.system()
        self.master_callback = master_callback
        # Top label
        top_label = customtkinter.CTkLabel(master=self, text="Setting")
        top_label.cget("font").configure(size=24)
        top_label.grid(row=0, column=0, padx=20, pady=20, sticky="nw")
        
        self.log_status = customtkinter.BooleanVar(value=True)
        self.cursor_status = customtkinter.BooleanVar(value=True)
        self.autostart_var = customtkinter.BooleanVar(value=self.check_autostart())
        # Toggle label
        self.auto_label = customtkinter.CTkLabel(master=self,
                                                   compound='right',
                                                   text="Auto Start",
                                                   text_color="black",
                                                   justify=tkinter.LEFT)
        self.auto_label.cget("font").configure(size=14)
        self.auto_label.grid(row=0,
                               column=0,
                               padx=(10, 0),
                               pady=60,
                               sticky="nw")

        # Toggle switch
        self.auto_switch = customtkinter.CTkSwitch(
            master=self,
            text="",
            width=200,
            border_color="transparent",
            switch_height=18,
            switch_width=32,
            variable=self.autostart_var,
            command=self.toggle_autostart,
            onvalue=1,
            offvalue=0,
        )
    
        self.auto_switch.grid(row=0,
                                column=0,
                                padx=(150, 0),
                                pady=60,
                                sticky="nw")
        
        self.log_label = customtkinter.CTkLabel(master=self,
                                                   compound='right',
                                                   text="Logging",
                                                   text_color="black",
                                                   justify=tkinter.LEFT)
        self.log_label.cget("font").configure(size=14)
        self.log_label.grid(row=0,
                               column=0,
                               padx=(10, 0),
                               pady=90,
                               sticky="nw")

        # Toggle switch
        self.log_switch = customtkinter.CTkSwitch(
            master=self,
            text="",
            width=200,
            border_color="transparent",
            switch_height=18,
            switch_width=32,
            variable=self.log_status,
            command=self.change_log_status,
            onvalue=1,
            offvalue=0,
        )
    
        self.log_switch.grid(row=0,
                                column=0,
                                padx=(150, 0),
                                pady=90,
                                sticky="nw")
        
        self.log_button = customtkinter.CTkButton(
                    master=self,
                    text="Open Log Directory",
                    command=self.open_log_directory,
                    width=180,
                    fg_color='lightblue'
                )
        
        self.log_button.grid(row=0,
                                column=0,
                                padx=(200, 0),
                                pady=90,
                                sticky="nw")
        
        self.cursor_control = customtkinter.CTkLabel(master=self,
                                                   compound='right',
                                                   text="Hide Cursor Control",
                                                   text_color="black",
                                                   justify=tkinter.LEFT)
        self.cursor_control.cget("font").configure(size=14)
        self.cursor_control.grid(row=0,
                               column=0,
                               padx=(10, 0),
                               pady=120,
                               sticky="nw")

        # Toggle switch
        self.cursor_switch = customtkinter.CTkSwitch(
            master=self,
            text="",
            width=200,
            border_color="transparent",
            switch_height=18,
            switch_width=32,
            variable=self.cursor_status,
            command=self.switch_cursor,
            onvalue=1,
            offvalue=0,
        )
    
        self.cursor_switch.grid(row=0,
                                column=0,
                                padx=(150, 0),
                                pady=120,
                                sticky="nw")
        
        self.slider = customtkinter.CTkSlider(master=self,
                                             from_=1,
                                             to=300,
                                             width=250,
                                             number_of_steps=300,
                                             command=partial(self.slider_drag_callback))
        self.slider.bind("<Button-1>",
                    partial(self.slider_mouse_down_callback))
        self.slider.bind("<ButtonRelease-1>",
                    partial(self.slider_mouse_up_callback))
        self.slider.grid(row=0,
                    column=0,
                    padx=(5, 0),
                    pady=(160, 10),
                    sticky="nw")
        
        self.slider_label = customtkinter.CTkLabel(master=self,
                                            text="0\t            Throttle time\t\t 3s",
                                            text_color="#868686",
                                            justify=tk.LEFT)
        self.slider_label.cget("font").configure(size=11)
        self.slider_label.grid(row=0,
                        column=0,
                        padx=(10, 0),
                        pady=(182, 10),
                        sticky="nw")
        
    def slider_drag_callback(self, slider_value: str):
        self.slider_dragging = True

    def slider_mouse_down_callback(self, event):
        self.slider_dragging = True

    def slider_mouse_up_callback(self, event):
        self.slider_dragging = False
        ConfigManager().set_throttle_time(self.slider.get()/100)

    def open_log_directory(self):
        log_file_path = App().logPath
        
        log_directory = os.path.dirname(log_file_path)
    
        # Check if the directory exists
        if not os.path.exists(log_directory):
            messagebox.showerror("Error", "Log directory not found!")
            return
        
        # Open the directory in the system's file explorer
        try:
            if sys.platform == "win32":
                subprocess.Popen(f'explorer /select,"{log_file_path}"')  # Windows
            elif sys.platform == "darwin":
                subprocess.call(["open", log_directory])  # macOS
            else:
                subprocess.call(["xdg-open", log_directory])  # Linux
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open log directory: {e}")

    def change_log_status(self):
        self.log_status = not self.log_status
        logger.info(f'Logging Status: {self.log_status}')
        self.update_logging_status()
    
    def update_logging_status(self):
        """
        Dynamically updates the logging level at runtime.
        """
        if self.log_status:
            logging_level = logging.INFO
        else:
            logging_level = logging.CRITICAL
        
        # Update the level for all loggers
        logging.getLogger().setLevel(logging_level)
    
    def add_to_registry(self):
        try:
            exe_path = os.path.abspath(sys.argv[0])
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Run",
                                0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"Failed to add to registry: {e}")
            return False

    def remove_from_registry(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Run",
                                0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Failed to remove from registry: {e}")
            return False
        
    def add_to_launch_agents(self):
        plist = {
            'Label': 'com.yourapp.autostart',
            'ProgramArguments': [sys.executable, os.path.abspath(sys.argv[0])],
            'RunAtLoad': True,
            'KeepAlive': False,
        }
        launch_agents_dir = Path.home() / 'Library' / 'LaunchAgents'
        launch_agents_dir.mkdir(parents=True, exist_ok=True)
        plist_path = launch_agents_dir / 'com.yourapp.autostart.plist'
        with open(plist_path, 'wb') as f:
            plistlib.dump(plist, f)
        return True

    def remove_from_launch_agents(self):
        plist_path = Path.home() / 'Library' / 'LaunchAgents' / 'com.yourapp.autostart.plist'
        if plist_path.exists():
            plist_path.unlink()
            return True
        return False

    def add_to_autostart(self):
        desktop_entry = f"""[Desktop Entry]
    Type=Application
    Exec={sys.executable} {os.path.abspath(sys.argv[0])}
    Hidden=false
    NoDisplay=false
    X-GNOME-Autostart-enabled=true
    Name=YourAppName
    Comment=Start YourAppName at login
    """
        autostart_dir = Path.home() / '.config' / 'autostart'
        autostart_dir.mkdir(parents=True, exist_ok=True)
        desktop_file = autostart_dir / 'yourappname.desktop'
        with open(desktop_file, 'w') as f:
            f.write(desktop_entry)
        return True

    def remove_from_autostart(self):
        desktop_file = Path.home() / '.config' / 'autostart' / 'yourappname.desktop'
        if desktop_file.exists():
            desktop_file.unlink()
            return True
        return False

    def check_autostart(self):
        if self.os_type == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r"Software\Microsoft\Windows\CurrentVersion\Run",
                                     0, winreg.KEY_READ)
                value, _ = winreg.QueryValueEx(key, APP_NAME)
                winreg.CloseKey(key)
                return True if value else False
            except FileNotFoundError:
                return False
            except ImportError:
                return False
        elif self.os_type == "Darwin":
            plist_path = Path.home() / 'Library' / 'LaunchAgents' / 'com.yourapp.autostart.plist'
            return plist_path.exists()
        elif self.os_type == "Linux":
            desktop_file = Path.home() / '.config' / 'autostart' / 'yourappname.desktop'
            return desktop_file.exists()
        else:
            return False

    def toggle_autostart(self):
        if self.autostart_var.get():
            success = self.enable_autostart()
            if success:
                messagebox.showinfo("Auto-Start", "Application will start automatically on restart")
            else:
                messagebox.showerror("Error", "Failed to enable auto-start.")
        else:
            success = self.disable_autostart()
            if success:
                messagebox.showinfo("Auto-Start", "Application will not start automatically")
            else:
                messagebox.showerror("Error", "Failed to disable auto-start.")

    def enable_autostart(self):
        try:
            if self.os_type == "Windows":
                return self.add_to_registry()  # Or add_to_startup()
            elif self.os_type == "Darwin":
                return self.add_to_launch_agents()
            elif self.os_type == "Linux":
                return self.add_to_autostart()
            else:
                return False
        except Exception as e:
            print(f"Enable autostart failed: {e}")
            return False

    def disable_autostart(self):
        try:
            if self.os_type == "Windows":
                return self.remove_from_registry()  # Or remove_from_startup()
            elif self.os_type == "Darwin":
                return self.remove_from_launch_agents()
            elif self.os_type == "Linux":
                return self.remove_from_autostart()
            else:
                return False
        except Exception as e:
            print(f"Disable autostart failed: {e}")
            return False
        
    def switch_cursor(self):
        self.cursor_status = not self.cursor_status
        ConfigManager().set_cursor_control(self.cursor_status)
        self.master_callback()
        if self.cursor_status:
            ConfigManager().set_temp_config(field="enable", value=0)
            ConfigManager().apply_config()
            MouseController().set_enabled(False)

    def leave(self):
        logger.info('<Leave>')
    
    def enter(self):
        logger.info('<Enter>')

if __name__ == "__main__":
    # Example usage:
    root = customtkinter.CTk()  # Create a window
    app = PageSetting(root)  # Create an instance of PageSetting
    app.pack(fill="both", expand=True)  # Add it to the window
    root.mainloop()  # Start the Tkinter event loop
