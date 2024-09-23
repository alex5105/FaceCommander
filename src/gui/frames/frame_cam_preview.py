import tkinter

import customtkinter
from PIL import Image, ImageTk

from src.camera_manager import CameraManager
from src.config_manager import ConfigManager
from src.controllers import Keybinder
from src.gui.frames.safe_disposable_frame import SafeDisposableFrame
from playsound import playsound
from tkinter import messagebox
from pathlib import Path
import plistlib
import threading
import os
import sys
import winreg
import platform

CANVAS_WIDTH = 320
CANVAS_HEIGHT = 240
LIGHT_BLUE = "#F9FBFE"
TOGGLE_ICON_SIZE = (32, 20)
APP_NAME = 'FaceCommander'


class FrameCamPreview(SafeDisposableFrame):

    def __init__(self, master, master_callback: callable, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.configure(fg_color=LIGHT_BLUE)
        self.os_type = platform.system()
        # Auto-Start Variable
        self.autostart_var = customtkinter.BooleanVar(value=self.check_autostart())
        # Canvas.
        self.placeholder_im = Image.open("assets/images/placeholder.png")
        self.placeholder_im = ImageTk.PhotoImage(
            image=self.placeholder_im.resize((CANVAS_WIDTH, CANVAS_HEIGHT)))

        self.canvas = tkinter.Canvas(master=self,
                                     width=CANVAS_WIDTH,
                                     height=CANVAS_HEIGHT,
                                     bg=LIGHT_BLUE,
                                     bd=0,
                                     relief='ridge',
                                     highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=10, pady=10, sticky="sw")

        # Toggle label
        self.toggle_label = customtkinter.CTkLabel(master=self,
                                                   compound='right',
                                                   text="Face control",
                                                   text_color="black",
                                                   justify=tkinter.LEFT)
        self.toggle_label.cget("font").configure(size=14)
        self.toggle_label.grid(row=1,
                               column=0,
                               padx=(10, 0),
                               pady=5,
                               sticky="nw")

        # Toggle switch
        self.toggle_switch = customtkinter.CTkSwitch(
            master=self,
            text="",
            width=200,
            border_color="transparent",
            switch_height=18,
            switch_width=32,
            variable=Keybinder().is_active,
            command=lambda: [
                master_callback("toggle_switch", {"switch_status": self.toggle_switch.get()}),
                self.play_sound()
            ],
            onvalue=1,
            offvalue=0,
        )
        if ConfigManager().config["auto_play"]:
            self.toggle_switch.select()

        self.toggle_switch.grid(row=1,
                                column=0,
                                padx=(100, 0),
                                pady=5,
                                sticky="nw")

        # Toggle label
        self.auto_label = customtkinter.CTkLabel(master=self,
                                                   compound='right',
                                                   text="Auto Start",
                                                   text_color="black",
                                                   justify=tkinter.LEFT)
        self.auto_label.cget("font").configure(size=14)
        self.auto_label.grid(row=1,
                               column=0,
                               padx=(10, 0),
                               pady=30,
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

        self.auto_switch.grid(row=1,
                                column=0,
                                padx=(100, 0),
                                pady=30,
                                sticky="nw")
        # Toggle description label
        self.toggle_label = customtkinter.CTkLabel(
            master=self,
            compound='right',
            text="Allow facial gestures to control\nyour actions. ",
            text_color="#444746",
            justify=tkinter.LEFT)
        self.toggle_label.cget("font").configure(size=12)
        self.toggle_label.grid(row=2,
                               column=0,
                               padx=(10, 0),
                               pady=5,
                               sticky="nw")

        # Set first image.
        self.canvas_image = self.canvas.create_image(0,
                                                     0,
                                                     image=self.placeholder_im,
                                                     anchor=tkinter.NW)
        self.new_photo = None
        self.after(1, self.camera_loop)

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
        self.play_sound()
        if self.autostart_var.get():
            success = self.enable_autostart()
            if success:
                messagebox.showinfo("Auto-Start", "Application will start automatically!")
            else:
                messagebox.showerror("Error", "Failed to enable auto-start.")
        else:
            success = self.disable_autostart()
            if success:
                messagebox.showinfo("Auto-Start", "Application will not start automatically!")
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
                    
    def play_sound(self):
        sound_path = 'assets/sounds/notif.mp3'
        threading.Thread(target=playsound, args=(sound_path,), daemon=True).start()

    def switch_toggled(self):
        # Play sound when the switch is toggled
        sound_path = 'assets/sounds/notif.mp3'  # Path to your sound file

        # Check if the sound file exists
        if os.path.exists(sound_path):
            playsound(sound_path)  # Play the sound if the file exists
        else:
            print(f"Sound file not found: {sound_path}")
        # Existing functionality
        self.root_function_callback(
            "toggle_switch", {"switch_status": self.toggle_switch.get()}
        )

    def camera_loop(self):
        if self.is_destroyed:
            return
        if self.is_active:
            if CameraManager().is_destroyed:
                return
            frame_rgb = CameraManager().get_debug_frame()
            # Assign ref to avoid garbage collected
            self.new_photo = ImageTk.PhotoImage(
                image=Image.fromarray(frame_rgb).resize((CANVAS_WIDTH,
                                                         CANVAS_HEIGHT)))
            self.canvas.itemconfig(self.canvas_image, image=self.new_photo)
            self.canvas.update()

            self.after(ConfigManager().config["tick_interval_ms"],
                       self.camera_loop)

    def enter(self):
        super().enter()
        self.after(1, self.camera_loop)

    def destroy(self):
        super().destroy()
