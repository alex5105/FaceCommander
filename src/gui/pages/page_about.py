# Standard library imports, in alphabetic order.
#
# Logging module.
# https://docs.python.org/3/library/logging.html
import logging
#
# Tcl/Tk user interface module.  
# https://docs.python.org/3/library/tkinter.html
# https://tkdocs.com/tutorial/text.html
#
# TOTH  
# -   https://www.pythontutorial.net/tkinter/tkinter-event-binding/
# -   https://www.pythontutorial.net/tkinter/tkinter-place/
from tkinter.ttk import Label
from tkinter.scrolledtext import ScrolledText
from tkinter.font import Font #, families as font_families
#
# Browser launcher module.
# https://docs.python.org/3/library/webbrowser.html
import webbrowser
#
# PIP modules would go here.
#
#
# Local imports.
#
from src.app import App
from src.gui.frames.safe_disposable_frame import SafeDisposableFrame
from src.update_manager import UpdateManager

logger = logging.getLogger("PageAbout")
def log_path(description, path): logger.info(" ".join((
    description, "".join(('"', str(path), '"'))
    , "Exists." if path.exists() else "Doesn't exist."
)))

# Jim initially was using Python lambda expressions for the event handlers. That
# seemed to result in all tag_bind() calls being overridden to whichever was the
# last one called. So now the tags are set up here, outside the class, and
# lambda expressions aren't used.
addressTags = {}
def add_address_tag(pageAbout, address):
    def _enter(event): pageAbout.hover_enter(address, event)
    def _leave(event): pageAbout.hover_leave(address, event)
    def _click(event): pageAbout.open_in_browser(address, event)

    addressTag = {
        'tag': f'address{len(addressTags)}',
        'enter': _enter,
        'leave': _leave,
        'click': _click
    }
    tagText = addressTag['tag']

    pageAbout.text.tag_configure(tagText)

    # TOTH using tag_bind. https://stackoverflow.com/a/65733556/7657675  
    # TOTH list of events that makes clear they have to be in angle brackets.
    # https://stackoverflow.com/a/32289245/7657675
    #
    # -   <Enter> is triggered when the pointer hovers here.
    # -   <Leave> is triggered when the pointer stops hovering here.
    # -   <1> is triggered when this is clicked. It seems to be a shorthand for
    #     button-1.
    pageAbout.text.tag_bind(tagText, "<Enter>", addressTag['enter'])
    pageAbout.text.tag_bind(tagText, "<Leave>", addressTag['leave'])
    pageAbout.text.tag_bind(tagText, "<1>", addressTag['click'])

    addressTags[address] = addressTag
    return addressTag

def add_address_tags(pageAbout, addresses):
    # TOTH Underlining https://stackoverflow.com/a/44890599/7657675
    pageAbout.text.tag_configure("link", underline=True, foreground="#0000EE")

    for address in addresses:
        add_address_tag(pageAbout, address)

    return addressTags

def tags_for(address):
    try:
        return ("link", addressTags[address]['tag'])
    except KeyError as keyError:
        raise ValueError(
            "Address hasn't been registered."
            f' Add add_address_tag(pageAbout,"{address}")'
        ) from keyError

class PageAbout(SafeDisposableFrame):
    hoverCursor = "hand2"

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.is_active = False

        # Create font objects for the fonts used on this page.
        font24 = Font(family="Google Sans", size=24)
        font18 = Font(family="Google Sans", size=18)
        font12 = Font(family="Google Sans", size=12)

        # Handy code to log all font families.
        # logger.info(font_families())

        # Create the about page content as a ScrolledText widget. The text won't
        # be editable but that can't be set here because the widget will ignore
        # the text.insert() method. Instead editing is disabled after the
        # insert().
        #
        # If the height were set here in the constructor, or in the `configure`
        # method, then the value is interpreted as a number of lines.  
        # TOTH
        # https://stackoverflow.com/questions/14887610/specify-the-dimensions-of-a-tkinter-text-box-in-pixels#comment125318354_52055199
        # Setting it in the `place` method instead will interpret it as a number
        # of pixels, which is what's required here.
        self.text = ScrolledText(
            self, wrap="word", borderwidth=0, font=font12, spacing1=15) 

        # Create tags for styling the page content.
        self.text.tag_configure("h1", font=font24)
        self.text.tag_configure("h2", font=font18)

        # Create a tag for every address in the about page. That seems to be the
        # only way that event handlers can be bound.
        add_address_tags(self, (
            "https://acecentre.org.uk",
            App().repositoryURL,
            "https://www.flaticon.com/free-icons/eye",
            "https://github.com/acidcoke/Grimassist/",
            "https://github.com/google/project-gameface"
        ) )
        logger.info(f'addressTags{addressTags}')

        # Fix the widget to the top of the frame. The height is set later, in
        # the configuration change handler. That handler will be invoked once
        # when the page is rendered, as well as being invoked every time the
        # page changes size.
        self.text.place(x=0, y=0, relwidth=1, anchor='nw')

        # The argument tail is an alternating sequence of texts and tag lists.
        # If the text is to be set in the default style then an empty tag list
        # () is given.
        self.text.insert("1.0"
        , f"About {App().name}\n", "h1"
        , "Control and move the pointer using head movements and facial"
        " gestures.\nDisclaimer: This software isn't intended for medical"
        f" use.\n{App().name} is an ", (),
        "Open Source project", tags_for(App().repositoryURL),
        " developed by the Ace Centre. Visit ", (),
        "our website", tags_for("https://acecentre.org.uk"),
        " to find out more about how we provide support for people with"
        " complex communications difficulties.\n", ()
        , "Releases\n", "h2"
        , f"Version {App().version}\n", ()
        , f"Last check for updates {self.last_fetch()}.\n", ()
        , "Attribution\n", "h2"
        , "Blink graphics in the user interface are based on ", ()
        , "Eye icons created by Kiranshastry - Flaticon", tags_for(
            "https://www.flaticon.com/free-icons/eye")
        , ".\nThis software was based on ", ()
        , "Grimassist", tags_for(
            "https://github.com/acidcoke/Grimassist/")
        , ", itself based on ", ()
        , "Google GameFace", tags_for(
            "https://github.com/google/project-gameface")
        , ".", ()
        )
        self.text.configure(state='disabled')

        # When the pointer hovers over a link, change it to a hand. It might
        # seem like that could be done by adding a configuration to the tag,
        # which is how links are underlined. However, it seems like that doesn't
        # work and the cursor cannot be configured at the tag level. The
        # solution is to configure and reconfigure it dynamically, at the widget
        # level, in the hover handlers.
        #
        # Discover the default cursor configuration here and store it. The value
        # is used in the hover handlers.
        self.initialCursor = self.text['cursor']

        # Label to display the address of a link when it's hovered over.
        #
        # It takes the background colour of the text control, above. It starts
        # out hidden.
        self.hoverLabel = Label(
            self, text="", font=font12, background=self.text['background'])
        self.hoverLabel.place_forget()

        # Register a listener for changes to the size of the frame.
        self.bind("<Configure>", self.handle_configure)

    def handle_configure(self, event):
        self.text.place(
            height=self.winfo_height()
            # This subtraction would reserve space for the label, and the scroll
            # bar would end a little higher too.  
            # - self.hoverLabel.winfo_height()
        )
    
    def last_fetch(self):
        lastFetch = UpdateManager().lastFetch
        return "never" if lastFetch is None else lastFetch.strftime("%c")

    def hover_enter(self, address, event):
        logger.info(f'hover({address}, {event}) {event.type}')
        self.text.configure(cursor=self.hoverCursor)
        # TOTH how to set the text of a label.
        # https://stackoverflow.com/a/17126015/7657675
        self.hoverLabel.configure(text=address)
        # Put the hover label in the bottom left corner of the page.
        self.hoverLabel.place(x=0, rely=1, anchor='sw')

    def hover_leave(self, address, event):
        logger.info(f'hover({address}, {event}) {event.type}')
        self.text.configure(cursor=self.initialCursor)
        # TOTH how to set the text of a label.
        # https://stackoverflow.com/a/17126015/7657675
        self.hoverLabel.configure(text="")
        # Make the hover label disappear.
        self.hoverLabel.place_forget()

    def open_in_browser(self, address, event):
        logger.info(f'open_in_browser({address}, {event})')
        webbrowser.open(address)

    def enter(self):
        super().enter()
        def written(*args):
            logger.info(
                f'written({args}) {UpdateManager().lastFetchMessage.get()}')
        UpdateManager().lastFetchMessage.trace('w', written)
        logger.info(
            f'releases_retrieval() {UpdateManager().releases_retrieval(True)}')




        # Next line would opens the About file in the browser.
        # open_in_browser(aboutHTML.as_uri(), None)

    def refresh_profile(self):
        pass