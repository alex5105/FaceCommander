from functools import partial

import customtkinter
from PIL import Image

from src.config_manager import ConfigManager
from src.gui.pages import (
    PageSelectCamera, PageKeyboard, PageAbout)
from src.gui.frames.safe_disposable_frame import SafeDisposableFrame
from src.gui.frames.frame_cam_preview import FrameCamPreview
from src.controllers import Keybinder
LIGHT_BLUE = "#F9FBFE"
BTN_SIZE = 225, 48
PROF_DROP_SIZE = 220, 40
EXPANDED_WIDTH = 260
COLLAPSED_WIDTH = 60

class FrameMenu(SafeDisposableFrame):

    def __init__(self, master, master_callback: callable, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(6, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_propagate(False)
        self.configure(fg_color=LIGHT_BLUE)
        self.grid_columnconfigure(0, minsize=400)  # Set minsize to desired width
        self.expanding = True

        self.master_callback = master_callback

        self.menu_btn_images = {
            PageSelectCamera.__name__: [
                customtkinter.CTkImage(
                    Image.open("assets/images/menu_btn_camera.png"),
                    size=BTN_SIZE),
                customtkinter.CTkImage(
                    Image.open("assets/images/menu_btn_camera_selected.png"),
                    size=BTN_SIZE)
            ],
            PageKeyboard.__name__: [
                customtkinter.CTkImage(
                    Image.open("assets/images/menu_btn_keyboard.png"),
                    size=BTN_SIZE),
                customtkinter.CTkImage(
                    Image.open("assets/images/menu_btn_keyboard_selected.png"),
                    size=BTN_SIZE)
            ],
            PageAbout.__name__: [
                customtkinter.CTkImage(
                    Image.open("assets/images/menu_btn_about.png"),
                    size=BTN_SIZE),
                customtkinter.CTkImage(
                    Image.open("assets/images/menu_btn_about_selected.png"),
                    size=BTN_SIZE)
            ]
        }
        # Toggle button
        # self.toggle_button = customtkinter.CTkButton(self, text="◀", width=20, command=self.toggle_sidebar)
        self.toggle_button = customtkinter.CTkButton(master=self, anchor="nw", border_spacing=20, border_width=0,
                                hover=False, corner_radius=0, text="Hide   ◀",
                                command=self.toggle_sidebar)
        # self.toggle_button.grid(row=0, column=1, padx=20, pady=10, sticky="ew")
        self.toggle_button.grid(row=0,
                    column=0,
                    padx=(0, 0),
                    pady=0,
                    ipadx=0,
                    ipady=0,
                    sticky="nw")
        self.toggle_button.configure(fg_color=LIGHT_BLUE, hover=False)
        # Profile button
        prof_drop = customtkinter.CTkImage(
            Image.open("assets/images/prof_drop_head.png"), size=PROF_DROP_SIZE)
        self.profile_btn = customtkinter.CTkLabel(
            master=self,
            textvariable=ConfigManager().current_profile_name,
            image=prof_drop,
            height=42,
            compound="center",
            anchor="w",
            cursor="hand2",
        )
        self.profile_btn.bind("<Button-1>",
                         partial(self.master_callback, "show_profile_switcher"))

        self.profile_btn.grid(row=1,
                         column=0,
                         padx=10,
                         pady=10,
                         ipadx=0,
                         ipady=0,
                         sticky="nw",
                         columnspan=1,
                         rowspan=1)

        self.buttons = {}
        self.buttons = self.create_tab_btn(self.menu_btn_images, offset=2)
        self.set_tab_active(PageSelectCamera.__name__)
        # Place Preview frame at the bottom of the window
        self.grid_rowconfigure(len(self.buttons) + 5, weight=1)  # Make the last row (for frame_preview) expand
        self.frame_preview = FrameCamPreview(self,
                                             self.cam_preview_callback,
                                             logger_name="frame_preview")
        self.frame_preview.grid(row=len(self.buttons) + 5, column=0, padx=0, pady=0, sticky="sew", columnspan=1)
        self.frame_preview.enter()        
    def toggle_sidebar(self):
        if self.expanding:
            self.configure(width=COLLAPSED_WIDTH)
            self.toggle_button.configure(text="▶")
            self.profile_btn.grid_forget()
            self.frame_preview.grid_forget()
            for k, btn in self.buttons.items():
                btn.grid_forget()
        else:
            self.configure(width=EXPANDED_WIDTH)
            self.toggle_button.configure(text="Hide   ◀")
            self.profile_btn.grid(row=1, column=0, padx=10, pady=10, sticky="nw")
            for idx, (k, btn) in enumerate(self.buttons.items()):
                btn.grid(row=idx + 2,
                        column=0,
                        padx=(0, 0),
                        pady=0,
                        ipadx=0,
                        ipady=0,
                        sticky="nw")                
            self.frame_preview.grid(row=len(self.buttons) + 5, column=0, padx=0, pady=0, sticky="sew", columnspan=1)

        self.expanding = not self.expanding

    def create_tab_btn(self, btns: dict, offset):

        out_dict = {}
        for idx, (k, im_paths) in enumerate(btns.items()):
            btn = customtkinter.CTkButton(master=self,
                                          image=im_paths[0],
                                          anchor="nw",
                                          border_spacing=0,
                                          border_width=0,
                                          hover=False,
                                          corner_radius=0,
                                          text="",
                                          command=partial(
                                              self.master_callback,
                                              function_name="change_page",
                                              args={"target": k}))

            btn.grid(row=idx + offset,
                     column=0,
                     padx=(0, 0),
                     pady=0,
                     ipadx=0,
                     ipady=0,
                     sticky="nw")
            btn.configure(fg_color=LIGHT_BLUE, hover=False)
            out_dict[k] = btn
        return out_dict

    def set_tab_active(self, tab_name: str):
        for k, btn in self.buttons.items():
            im_normal, im_active = self.menu_btn_images[k]
            if k == tab_name:
                btn.configure(image=im_active)

            else:
                btn.configure(image=im_normal)
    def cam_preview_callback(self, function_name, args: dict, **kwargs):
        if function_name == "toggle_switch":
            self.set_mediapipe_mouse_enable(new_state=args["switch_status"])

    def set_mediapipe_mouse_enable(self, new_state: bool):
        Keybinder().set_active(new_state)