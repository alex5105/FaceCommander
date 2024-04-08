# Standard library imports.
#
# https://docs.python.org/3/library/datetime.html#datetime.datetime.now
from datetime import datetime
#
# Logging module.
# https://docs.python.org/3.8/library/logging.html
import logging
#
# Multiprocessing module, required for embedded web view.
# https://docs.python.org/3/library/multiprocessing.html
import multiprocessing

# from threading import Thread

#
# Object oriented path handling.
# https://docs.python.org/3/library/pathlib.html
from pathlib import Path

from signal import signal, SIGTERM, getsignal

#
# System parameters module, only used to check the multiprocessing capability.
# https://docs.python.org/3/library/sys.html
import sys
#
# Tcl/Tk user interface module.  
# https://docs.python.org/3/library/tkinter.html
from tkinter import Text, END
from tkinter.ttk import Frame
from tkinter.font import Font, families as font_families
#
# Browser launcher module.
# https://docs.python.org/3/library/webbrowser.html
import webbrowser
#
# PIP modules.
#
# Web view module.  
# https://pywebview.flowrl.com/guide/api.html
import webview

#
# Local imports.
#
from src.gui.frames.safe_disposable_frame import SafeDisposableFrame
from src.config_manager import ConfigManager

logger = logging.getLogger("PageAbout")
def log_path(description, path): logger.info(" ".join((
    description, "".join(('"', str(path), '"'))
    , "Exists." if path.exists() else "Doesn't exist."
)))

def open_in_browser(clicked): webbrowser.open(clicked)


def await_window_close(lock, webViewWindow):
    # self.webViewWindow = webViewWindow
    logger.info(
        f'await_window_close({lock}, {webViewWindow}) {getsignal(SIGTERM)}')
    lock.acquire()
    webViewWindow.destroy()

def create_window(url, lock, x=0, y=0, width=200, height=200):
    # https://pywebview.flowrl.com/guide/api.html#webview-create-window
    logger.info(f'create_window(,x={x})')
    webViewWindow = webview.create_window(
        'About FaceCommander', url=url, js_api=API(None)
        , x=x, y=y, width=width, height=height
#         , html='''
# <button id="clicker">Open in browser</button><script>
# document.getElementById("clicker").onclick = (event => {
#     console.log("clickerty");
#     console.log(window.pywebview);
#     console.log(window.pywebview.api);
#     window.pywebview.api.navigate('https://example.com');
# });
# </script>
# '''
    )
    logger.info(f'Created web view window.')
    # https://pywebview.flowrl.com/guide/api.html#webview-start
    webview.start(
        func=await_window_close, args=(lock, webViewWindow), debug=True)
    logger.info(f'After web view start.')
    



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

        signalReturn = signal(SIGTERM, self.handle_termination)

        self.webViewProcess = None
        self.webViewLock = None
        self.jsAPI = API(self)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.is_active = False
        self.grid_propagate(False)


        # self.innerFrame = Frame(self)
        # # https://tkinter-docs.readthedocs.io/en/latest/widgets/common.html#Widget.winfo_class
        # logger.info(
        #     'self.innerFrame.winfo_class()'
        #     f' "{self.innerFrame.winfo_class()}".')
        # logger.info(
        #     'self.innerFrame.configure()'
        #     f' "{self.innerFrame.configure()}".')

        # self.innerFrame.grid(row=0, column=0, padx=5, pady=5, sticky="nswe")


        fontGoogleSans24 = Font(family="Google Sans", size=24)
        fontGoogleSans12 = Font(family="Google Sans", size=12)
        # fontTimes = Font(family="Times New Roman", size=36)
        logger.info(font_families())

        text = Text(self, wrap="word", borderwidth=0)
        text.tag_configure("h1", font=fontGoogleSans24)
        text.tag_configure("p", font=fontGoogleSans12)
        # TOTH Underlining https://stackoverflow.com/a/44890599/7657675
        text.tag_configure("link", underline=True)

        text.insert("1.0"
        , "About FaceCommander\n", "h1"
        , f"Version {ConfigManager().version}\n", "p"
        , "Control and move the pointer using head movements and facial"
        " gestures.\nDisclaimer: This software isn't intended for medical"
        " use.\n", "p"
        , "FaceCommander is a project of the ", "p"
        , "Ace Centre", ("p", "link")
        , " charity.", "p"
#     <a href="https://acecentre.org.uk/">Ace Centre</a> charity.</p>
# <h2>Attribution</h2
# ><p
#     >Blink graphics in the user interface are based on
#     <a href="https://www.flaticon.com/free-icons/eye" target="_blank"
#         >Eye icons created by Kiranshastry - Flaticon</a>.</p
# ><p
#     >This software was based on <a
#         href="https://github.com/acidcoke/Grimassist/">Grimassist</a
#     >, itself based on <a
#         href="https://github.com/google/project-gameface" >Google GameFace</a

        )
        text['state'] = 'disabled'
        text.grid(row=0, column=0, padx=0, pady=5, sticky="nsew")

    def handle_termination(self, signalNumber, stackFrame):
        logger.info(f'handle_termination({signalNumber}, {stackFrame})')

    def enter(self):
        super().enter()
        self.load_content()

    def load_content(self):
        return




        rootPath = Path().resolve()
        log_path("Run-time rootPath", rootPath)
        aboutHTML = rootPath.joinpath("assets", "web", "about.html")
        log_path("About HTML path", aboutHTML)

        # TOTH the need for update().
        # https://stackoverflow.com/a/13327708/7657675
        self.innerFrame.update()
        logger.info(
            f'innerFrame geometry:{self.innerFrame.winfo_geometry()}'
            f' innerFrame x:{self.innerFrame.winfo_x()}'
            f' innerFrame rootx:{self.innerFrame.winfo_rootx()}'
            f' innerFrame vrootx:{self.innerFrame.winfo_vrootx()}'
            f' innerFrame width:{self.innerFrame.winfo_width()}'
            f' innerFrame reqwidth:{self.innerFrame.winfo_reqwidth()}'
            f' innerFrame screenmmwidth:{self.innerFrame.winfo_screenmmwidth()}'
            f' innerFrame screenwidth:{self.innerFrame.winfo_screenwidth()}'
            f' innerFrame vrootwidth:{self.innerFrame.winfo_vrootwidth()}'
        )


        self._versionUpdated = False



        # One-time multiprocessing set-up.
        # See
        # https://github.com/r0x0r/pywebview/blob/2cff89a76fd70a621900e5e806355affc24f787d/docs/examples/no_block.md
        #
        if getattr(sys, 'frozen', False): multiprocessing.freeze_support()
        startMethod = multiprocessing.get_start_method(True)
        if startMethod is None:
            logger.info("Setting multiprocessing start method:spawn.")
            multiprocessing.set_start_method('spawn')
        else:
            logger.info(f"Multiprocessing start method:{startMethod}.")

        self.webViewLock = multiprocessing.Lock()
        self.webViewLock.acquire()

        # The geometry accessors are listed here, without explanation though.
        # https://tkinter-docs.readthedocs.io/en/latest/widgets/common.html#Widget.winfo_rootx
        self.webViewProcess = multiprocessing.Process(
            target=create_window, args=(
                aboutHTML.as_uri(), self.webViewLock,
                self.innerFrame.winfo_rootx(),
                self.innerFrame.winfo_rooty(),
                self.innerFrame.winfo_width()
            )
        )
        self.webViewProcess.start()
        logger.info(
            f'Web view process "{self.webViewProcess.name}"'
            f' pid:{self.webViewProcess.pid}'
            f' lock:{self.webViewLock}.')
        
        # ToDo https://tkinterexamples.com/events/window/
        # Move the web view when the app window moves. Same for resize.
        # self.close_web_view when the app exits.

        # pywebview must be run on a main thread.
        # t = Thread(target=create_window, args=(
        #     aboutHTML.as_uri(),
        #     self.innerFrame.winfo_rootx(),
        #     self.innerFrame.winfo_rooty(),
        #     self.innerFrame.winfo_width()
        # ))
        # t.start()


#     # main thread must be blocked using join or any other user defined method to prevent app from quitting
        # Adding a join() here stops the app from doing anything, until the
        # webview gets closed.



        # self.webViewProcess.join()


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

    def close_web_view(self):
        if self.webViewLock is None:
            logger.info("No web view lock.")
        else:
            logger.info("Releasing web view lock.")
            self.webViewLock.release()
            self.webViewLock = None
        if self.webViewProcess is None:
            logger.info("No web view process.")
        else:
            logger.info("Joining web view process.")
            self.webViewProcess.join()
            self.webViewProcess.close()
            self.webViewProcess = None

    def leave(self):
        self.close_web_view()
        super().leave()
    
    def destroy(self):
        self.close_web_view()
        super().destroy()
