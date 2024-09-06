import tkinter as tk  # stick to one logic either using tk or tkinter!
from tkinter import ttk


class GUI(tk.Tk):
    def __init__(self):
        super().__init__()  # this basically replaces window as self
        self.title("Example")
        self.minsize(width=600, height=400)  # do not allow resizing smaller than your initial canvas size
        max_height = 1000  # use this to determine length of scroll heigth and if desired max window heigth
        # self.maxsize(width=650, height=max_height)  # → specify if needed

        main_frame = tk.Frame(self)  # name it more descriptive
        main_frame.pack(expand=True, fill="both")  # let the canvas parent frame stretch out when resizing

        # let the canvas expand to fill main_frame both in width and height
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # scrollregion is also essential when using scrollbars → but you only need y in your case!
        self.canvas = tk.Canvas(main_frame, scrollregion=f"0 0 0 {max_height}", width=600, height=400)
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW)

        self.scroll = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.canvas.yview, cursor="arrow")
        self.scroll.grid(row=0, column=1, sticky=tk.NS)
        self.canvas.config(yscrollcommand=self.scroll.set)

        ###############################

        self.container_frame = tk.LabelFrame(self.canvas)

        # Saving User Info
        user_info_frame = tk.LabelFrame(self.container_frame,
                                        text="User Information")  # unnecessary to manage with .grid

        first_name_label = tk.Label(user_info_frame, text="First Name")
        first_name_label.grid(row=0, column=0)
        last_name_label = tk.Label(user_info_frame, text="Last Name")
        last_name_label.grid(row=0, column=1)

        first_name_entry = tk.Entry(user_info_frame)
        last_name_entry = tk.Entry(user_info_frame)
        first_name_entry.grid(row=1, column=0)
        last_name_entry.grid(row=1, column=1)

        title_label = tk.Label(user_info_frame, text="Title")
        title_combobox = ttk.Combobox(user_info_frame, values=["", "Mr.", "Ms.", "Dr."])
        title_label.grid(row=0, column=2)
        title_combobox.grid(row=1, column=2)

        age_label = tk.Label(user_info_frame, text="Age")
        age_spinbox = tk.Spinbox(user_info_frame, from_=18, to=110)
        age_label.grid(row=2, column=0)
        age_spinbox.grid(row=3, column=0)

        nationality_label = tk.Label(user_info_frame, text="Nationality")
        nationality_combobox = ttk.Combobox(user_info_frame,
                                            values=["Africa", "Antarctica", "Asia", "Europe", "North America",
                                                    "Oceania",
                                                    "South America"])
        nationality_label.grid(row=2, column=1)
        nationality_combobox.grid(row=3, column=1)

        for widget in user_info_frame.winfo_children():
            widget.grid_configure(padx=10, pady=5, sticky="nsew")  # add sticky to stretch widget to fill grid cell

        # Saving Course Info
        courses_frame = tk.LabelFrame(self.container_frame)  # unnecessary to manage with .grid

        registered_label = tk.Label(courses_frame, text="Registration Status")

        reg_status_var = tk.StringVar(value="Not Registered")
        registered_check = tk.Checkbutton(courses_frame, text="Currently Registered",
                                          variable=reg_status_var, onvalue="Registered", offvalue="Not registered")

        registered_label.grid(row=0, column=0)
        registered_check.grid(row=1, column=0)

        numcourses_label = tk.Label(courses_frame, text="# Completed Courses")
        numcourses_spinbox = tk.Spinbox(courses_frame, from_=0, to='infinity')
        numcourses_label.grid(row=0, column=1)
        numcourses_spinbox.grid(row=1, column=1)

        numsemesters_label = tk.Label(courses_frame, text="# Semesters")
        numsemesters_spinbox = tk.Spinbox(courses_frame, from_=0, to="infinity")
        numsemesters_label.grid(row=0, column=2)
        numsemesters_spinbox.grid(row=1, column=2)

        for widget in courses_frame.winfo_children():
            widget.grid_configure(padx=10, pady=5, sticky="nsew")

        # rowconfigure seems to make no sense except you want to stretch in height as well (but why then a scrollbar?)
        # but giving all cols the same weight will let them stretch evenly
        user_info_frame.columnconfigure(0, weight=1)
        user_info_frame.columnconfigure(1, weight=1)
        user_info_frame.columnconfigure(2, weight=1)

        courses_frame.columnconfigure(0, weight=1)
        courses_frame.columnconfigure(1, weight=1)
        courses_frame.columnconfigure(2, weight=1)

        self.print_button = tk.Button(self.container_frame, text="Submit", bg='green', fg='white', font=12)

        user_info_frame.grid(row=0, column=0, sticky="ew")
        courses_frame.grid(row=1, column=0, sticky="ew")
        self.print_button.grid(row=2, column=0)
        self.container_frame.columnconfigure(0, weight=1)

        # add the pady and padx in the position tuple & specify width for the frames by callback
        self.padx = 20
        # self.canvas.create_window((self.padx, 10), anchor=tk.NW, window=user_info_frame, tags='frame')
        # self.canvas.create_window((self.padx, 160), anchor=tk.NW, window=courses_frame, tags='frame')
        # self.canvas.create_window((500, 350), anchor=tk.NW, window=self.print_button, tags="button")
        self.container_frame_id = self.canvas.create_window((self.padx, 10), anchor=tk.NW, window=self.container_frame,
                                                            tags="container_frame")

        self.canvas.bind("<Configure>", self.onCanvasConfigure)

    def onCanvasConfigure(self, e):
        """stretch canvas frames to match canvas width on resize (respecting the scrollbar and the padding)"""
        # self.canvas.itemconfig('frame', width=self.canvas.winfo_width() - self.padx - self.scroll.winfo_width())
        canvas_width = e.width
        self.canvas.itemconfig(self.container_frame_id, width=canvas_width * 0.9)


if __name__ == '__main__':
    app = GUI()
    app.mainloop()
