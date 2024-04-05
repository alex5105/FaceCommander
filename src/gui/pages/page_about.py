# Standard library imports.
#
# https://docs.python.org/3/library/datetime.html#datetime.datetime.now
from datetime import datetime
#
# Logging module.
# https://docs.python.org/3.8/library/logging.html
import logging
#
# Object oriented path handling.
# https://docs.python.org/3/library/pathlib.html
from pathlib import Path
#
# Tcl/Tk user interface module.  
# https://docs.python.org/3/library/tkinter.html
# https://docs.python.org/3/library/tkinter.font.html#module-tkinter.font
from tkinter import Tk
from tkinter.font import Font, families as font_families
from tkinter.ttk import Style, Frame, Label
#
# Browser launcher module.
# https://docs.python.org/3/library/webbrowser.html
import webbrowser
#
# PIP modules.
#
# HTML frame around the TKhtml3 widget.
# 
# https://github.com/Andereoo/TkinterWeb/blob/main/tkinterweb/docs/HTMLFRAME.md
from tkinterweb import HtmlFrame
#
# Local imports.
#
from src.gui.frames.safe_disposable_frame import SafeDisposableFrame
from src.config_manager import ConfigManager

logger = logging.getLogger("PageAbout")
def log_html_frame_message(message): logger.info(message)
def log_path(description, path): logger.info(" ".join((
    description, "".join(('"', str(path), '"'))
    , "Exists." if path.exists() else "Doesn't exist."
)))

def open_in_browser(clicked): webbrowser.open(clicked)


import webview
def create_window():
    webViewWindow = webview.create_window(
        'About FaceCommander'
            # , url=fontsHTML.as_uri()
        , html='''
<button id="clicker">Open in browser</button><script>
document.getElementById("clicker").onclick = (event => {
    console.log("clickerty");
    console.log(window.pywebview);
    console.log(window.pywebview.api);
    window.pywebview.api.navigate('https://example.com');
});
</script>
'''
        , js_api=API(None)
    )
    webview.start(debug=True)



    # window = webview.create_window(
    #     'Simple browser', 'https://pywebview.flowrl.com/hello')
    # webview.start()



class API:
    def __init__(self, pageAbout):
        self.pageAbout = pageAbout
    
    def navigate(self, url):
        print(f'navigate(,{url})')
        webbrowser.open(url)
        return {}

class PageAbout(SafeDisposableFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.webViewWindow = None
        self.jsAPI = API(self)

        fontGoogleSans = Font(family="Google Sans", size=24)
        fontTimes = Font(family="Times New Roman", size=36)
        logger.info(fontGoogleSans, font_families())

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.is_active = False
        self.grid_propagate(False)

        # style = Style()
        # style.configure("About", background)

        # Create style used by default for all Frames
        Style().configure('TFrame', background='#080', font=fontGoogleSans)

        # https://tkdocs.com/shipman/colors.html
        Style().configure('TLabel', background='#999', font=fontGoogleSans)
        Style().configure('times.TLabel', background='#bbb', font=fontTimes)
        Style().configure('Html', background='#8bb', font=fontTimes)

        self.innerFrame = Frame(self)
        # https://tkinter-docs.readthedocs.io/en/latest/widgets/common.html#Widget.winfo_class
        logger.info(
            'self.innerFrame.winfo_class()'
            f' "{self.innerFrame.winfo_class()}".')
        logger.info(
            'self.innerFrame.configure()'
            f' "{self.innerFrame.configure()}".')

        self.htmlFrame = HtmlFrame(self)
        self.htmlFrame.set_message_func(log_html_frame_message)
        self.htmlFrame.on_link_click(open_in_browser)
        logger.info(
            'self.htmlFrame.winfo_class()'
            f' "{self.htmlFrame.winfo_class()}".')
        logger.info(
            'self.htmlFrame.configure()'
            f' "{self.htmlFrame.configure()}".')
        logger.info(
            'self.htmlFrame.html.winfo_class()'
            f' "{self.htmlFrame.html.winfo_class()}".')
        logger.info(
            'self.htmlFrame.html.configure()'
            f' "{self.htmlFrame.html.configure()}".')
        self.htmlFrame.grid(column=0, row=2)

        labelTimes = Label(
            self.innerFrame, text="This is thymes lable", style='times.TLabel')
        labelTimes.grid(column=0, row=0)
        logger.info(
            'labelTimes.winfo_class()'
            f' "{labelTimes.winfo_class()}".')
        logger.info(
            'labelTimes.configure()'
            f' "{labelTimes.configure()}".')
        labelDefault = Label(
            self.innerFrame, text="This is de fault lable")
        labelDefault.grid(column=1, row=0)

        labelEmpty = Label(self.innerFrame, text="")
        labelEmpty.grid(column=0, row=1)

        self.innerFrame.grid(row=0, column=0, padx=5, pady=5, sticky="nswe")

    def enter(self):
        super().enter()
        self.load_content()

    def load_content(self):
        rootPath = Path().resolve()
        log_path("Run-time rootPath", rootPath)
        aboutHTML = rootPath.joinpath("assets", "web", "about.html")
        log_path("About HTML path", aboutHTML)
        self._versionUpdated = False
        self.htmlFrame.on_done_loading(self.update_version)
        self.htmlFrame.load_file(aboutHTML.as_uri())

        # https://pywebview.flowrl.com/guide/api.html#webview-create-window
        # https://github.com/r0x0r/pywebview/blob/2cff89a76fd70a621900e5e806355affc24f787d/docs/examples/no_block.md
        import multiprocessing
        import sys

        if getattr(sys, 'frozen', False):
            multiprocessing.freeze_support()

        multiprocessing.set_start_method('spawn')
        p = multiprocessing.Process(target=create_window)
        p.start()

        print('Main thread is not blocked. You can execute your code after pywebview window is created')

#     # main thread must be blocked using join or any other user defined method to prevent app from quitting
        # Adding a join() here stops the app from doing anything, until the
        # webview gets closed.
        p.join()
#     print('App exists now')

#         # fontsHTML = rootPath.joinpath("assets", "web", "about.html")
#         self.webViewWindow = webview.create_window(
#             'About FaceCommander'
#             # , url=fontsHTML.as_uri()
#             , html='''
#             <button id="clicker">Open in browser</button
# ><script>
# document.getElementById("clicker").onclick = (event => {
#     console.log("clickerty");
#     console.log(window.pywebview);
#     console.log(window.pywebview.api);
# });
# // onclick="window.pywebview.api.navigate('https://example.com')
# </script>
#             '''
#             , js_api=self.jsAPI)
#             # If you use frameless the window doesn't have a built-in close mechanism, frameless=True)
#         webview.start(debug=True)

        # Next line opens the About file in the browser.
        # open_in_browser(aboutHTML.as_uri())
    
    def update_version(self, appVersionID="app-version"):
        if self._versionUpdated: return
        self._versionUpdated = True
        appVersion = ConfigManager().version
        logger.info(f'ConfigManager().version"{appVersion}"')
        html = self.htmlFrame.html
        # Find the <span id="version"> node.
        parent = html.search(f"#{appVersionID}")[0]
        tag = html.get_node_tag(parent)
        logger.info(f"Found app version parent <{tag}>.")
        # The text of the node will be in its first child.
        oldChilds = html.get_node_children(parent)

        # To add the new text, add a new parent node. The text will be in the
        # first child. Then insert the new child into the old parent, which
        # implicitly moves it out of the new parent. Then delete the new parent,
        # and the old text node.
        #
        # Assume there isn't already a node with id="newVersion"
        newID = appVersionID + "-new"
        self.htmlFrame.add_html(f'<{tag} id="{newID}">{appVersion}</{tag}>')
        newParent = html.search(f"#{newID}")[0]
        child = html.get_node_children(newParent)[0]
        html.insert_node(parent, child)
        for oldChild in oldChilds: html.delete_node(oldChild)
        html.delete_node(newParent)

    def leave(self):
        super().leave()
        # if self.webViewWindow is not None:
        #     self.webViewWindow.destroy()
        #     self.webViewWindow = None
