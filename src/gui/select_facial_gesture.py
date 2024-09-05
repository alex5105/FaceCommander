import customtkinter
from PIL import Image, ImageDraw

ICON_SIZE = (40, 40)  # Adjust icon size as needed
ITEM_HEIGHT = 50  # Adjust item height as needed
LIGHT_BLUE = "#ADD8E6"  # Adjust color as needed
BUTTON_SPACING = 10  # Spacing between buttons
CONFIRM_BUTTON_COLOR = "#008CBA"  # Button color for modern look
CANCEL_BUTTON_COLOR = "#FF6347"  # Cancel button color
CONFIRM_ICON_PATH = "assets/images/confirm_icon.png"  # Path to the confirmation icon


def mouse_in_widget(mouse_x, mouse_y, widget, expand_x=(0, 0), expand_y=(0, 0)):
    widget_x1 = widget.winfo_rootx() - expand_x[0]
    widget_y1 = widget.winfo_rooty() - expand_y[0]
    widget_x2 = widget_x1 + widget.winfo_width() + expand_x[0] + expand_x[1]
    widget_y2 = widget_y1 + widget.winfo_height() + expand_y[0] + expand_y[1]
    return widget_x1 <= mouse_x <= widget_x2 and widget_y1 <= mouse_y <= widget_y2


class Select_Facial_Gesture:
    def __init__(self, master, dropdown_items: dict, width, callback: callable):
        self.master = master
        self.dropdown_items = dropdown_items
        self.callback = callback
        self.width = width
        self.selected_gesture = None  # No gesture is selected initially
        self.divs = {}
        self.max_columns = 4
        self.min_columns = 2
        self.div_name = ""
        self.selected_gesture

        # Load confirmation icon image
        self.confirm_icon = Image.open(CONFIRM_ICON_PATH).resize((20, 20))

    def open(self, div_name):
        """Open the custom dialog as a modal popup using customtkinter."""
        self.dialog_window = customtkinter.CTkToplevel(self.master)
        self.dialog_window.title("Select an Option")
        self.dialog_window.resizable(True, True)

        # Center the dialog on the parent window
        self.center_window(self.dialog_window, self.width, 400)

        # Set dialog as modal
        self.dialog_window.grab_set()  # Block interaction with other windows
        self.dialog_window.focus_set()
        self.dialog_window.transient(self.master)

        # Create a label
        label = customtkinter.CTkLabel(self.dialog_window, text="Select a Gesture", font=("Arial", 14))
        label.pack(pady=20)

        # Create a scrollable frame for items
        self.scrollable_frame = customtkinter.CTkScrollableFrame(self.dialog_window, width=self.width + 20)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create buttons for each item in dropdown_items using customtkinter
        for gesture, image_path in self.dropdown_items.items():
            image = customtkinter.CTkImage(Image.open(image_path).resize(ICON_SIZE), size=ICON_SIZE)
            btn = customtkinter.CTkButton(
                master=self.scrollable_frame,
                text=gesture,
                image=image,
                width=self.width // self.max_columns - BUTTON_SPACING,
                height=ITEM_HEIGHT,
                border_width=0,
                corner_radius=0,
                fg_color=LIGHT_BLUE,
                hover_color="gray90",
                text_color_disabled="gray80",
                compound="left",
                anchor="w",
                command=lambda i=gesture: self.on_select(div_name, i)
            )
            self.divs[gesture] = {"button": btn, "image": image, "original_image": image_path}
            btn.grid(row=len(self.divs.items()) // self.max_columns, column=len(self.divs.items()) % self.max_columns, padx=5, pady=5, sticky="ew")

        # Create a frame for Confirm and Cancel buttons
        button_frame = customtkinter.CTkFrame(self.dialog_window)
        button_frame.pack(pady=20)

        # Confirm button (initially disabled)
        self.confirm_button = customtkinter.CTkButton(
            button_frame, 
            text="Confirm", 
            command=self.confirm_selection, 
            state="disabled",  # Disabled until a gesture is selected
            fg_color=CONFIRM_BUTTON_COLOR
        )
        self.confirm_button.grid(row=0, column=0, padx=10)

        # Cancel button
        cancel_button = customtkinter.CTkButton(
            button_frame, 
            text="Cancel", 
            command=self.dialog_window.destroy, 
            fg_color=CANCEL_BUTTON_COLOR
        )
        cancel_button.grid(row=0, column=1, padx=10)

        # Bind resize event to handle dialog size changes
        self.dialog_window.bind("<Configure>", self.on_resize)

        # Wait for the dialog to be closed
        self.dialog_window.wait_window()

    def center_window(self, window, width, height):
        """Center the window on the parent window."""
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        x = parent_x + (parent_width // 4) - (width // 2)
        y = parent_y + (parent_height // 4) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def on_resize(self, event):
        """Handle window resize event."""
        dialog_width = self.dialog_window.winfo_width()
        if dialog_width > 1100:
            num_columns = self.max_columns
        elif dialog_width > 800:
            num_columns = self.max_columns - 1
        elif dialog_width > 500:
            num_columns = self.max_columns - 2
        else:
            num_columns = 1
        self.update_grid(num_columns)

    def update_grid(self, num_columns):
        """Update the grid configuration and reposition buttons."""
        for i in range(self.max_columns):
            self.scrollable_frame.grid_columnconfigure(i, weight=0)
        for i in range(num_columns):
            self.scrollable_frame.grid_columnconfigure(i, weight=1)
        for index, gesture in enumerate(self.divs):
            row = index // num_columns
            col = index % num_columns
            button = self.divs[gesture]['button']
            button.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

    def on_select(self, div_name, selected_item):
        """Handle item selection, enable the Confirm button, and overlay confirmation icon."""
        self.selected_gesture = selected_item
        self.div_name = div_name
        # Overlay confirmation icon on selected image
        self.overlay_confirmation_icon(selected_item)

        self.confirm_button.configure(state="normal")  # Enable the Confirm button

    def overlay_confirmation_icon(self, selected_item):
        """Overlay a small confirmation icon on the selected item's image."""
        # Reset previously selected item (remove confirmation icon from previous selection)
        for gesture, data in self.divs.items():
            original_image_path = data['original_image']
            original_image = Image.open(original_image_path).resize(ICON_SIZE)
            self.divs[gesture]['image'] = customtkinter.CTkImage(original_image, size=ICON_SIZE)
            self.divs[gesture]['button'].configure(image=self.divs[gesture]['image'])

        # Add confirmation icon to the selected item's image
        selected_image_path = self.divs[selected_item]['original_image']
        selected_image = Image.open(selected_image_path).resize(ICON_SIZE)

        # Create a new image with the confirmation icon overlaid
        combined_image = selected_image.copy()
        combined_image.paste(self.confirm_icon, (ICON_SIZE[0] - 20, ICON_SIZE[1] - 20), self.confirm_icon)

        # Update the button with the new image
        self.divs[selected_item]['image'] = customtkinter.CTkImage(combined_image, size=ICON_SIZE)
        self.divs[selected_item]['button'].configure(image=self.divs[selected_item]['image'])

    def confirm_selection(self):
        """Handle confirmation and close the dialog."""
        if self.selected_gesture:
            print(f"Confirmed gesture: {self.selected_gesture}")
            self.callback(self.div_name, self.selected_gesture)            
            self.dialog_window.destroy()
