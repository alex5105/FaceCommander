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
# -   https://www.askpython.com/python-modules/tkinter/tkinter-intvar  
#     Includes an example of the trace() method.
from tkinter import END, StringVar
from tkinter.ttk import Label
from tkinter.scrolledtext import ScrolledText
from tkinter.font import Font #, families as font_families
#
# Type hints module.
# https://docs.python.org/3/library/typing.html#typing.NamedTuple
from typing import NamedTuple, Callable, Any
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
# def log_path(description, path): logger.info(" ".join((
#     description, "".join(('"', str(path), '"'))
#     , "Exists." if path.exists() else "Doesn't exist."
# )))

class Para():
    def __init__(self, stringVar):
        self._stringVar = stringVar
    
    def get(self):
        value = self._stringVar.get()
        # logger.info(f'{value=}')
        if (value is not None and value != "" and not value.endswith("\n")):
            return value + "\n"
        return value
    
    def trace(self, *args):
        return self._stringVar.trace(*args)

class PageAbout(SafeDisposableFrame):
    hoverCursor = "hand2"

    def __init__(self, tkRoot, updateHost, **kwargs):
        super().__init__(tkRoot, **kwargs)
        self.is_active = False
        self._updateHost = updateHost

        # Create font objects for the fonts used on this page.
        font24 = Font(family="Google Sans", size=24)
        font18 = Font(family="Google Sans", size=18)
        font12 = Font(family="Google Sans", size=12)
        #
        # This is the nearest you can get to making a character invisible.
        font1Pixel = Font(size=-1)

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
        #
        # Headings.
        self.text.tag_configure("h1", font=font24)
        self.text.tag_configure("h2", font=font18)
        #
        # Spacers, which must be inserted in between adjacent dynamic texts.
        self.text.tag_configure("spacer", font=font1Pixel)
        #
        # Links.
        # TOTH Underlining https://stackoverflow.com/a/44890599/7657675
        self.text.tag_configure(
            "link", underline=True, foreground="#0000EE")

        # Fix the widget to the top of the frame. The height is set later, in
        # the configuration change handler. That handler will be invoked once
        # when the page is rendered, as well as being invoked every time the
        # page changes size.
        self.text.place(x=0, y=0, relwidth=1, anchor='nw')

        self._spanned = SpannedText(self
        ).paragraph(f"About {App().name}", "h1"
        ).span(f"""\
Control and move the pointer using head movements and facial gestures.
Disclaimer: This software isn't intended for medical use.
{App().name} is an """
        ).link("Open Source project", App().repositoryURL, "link"
        ).span(" developed by the Ace Centre. Visit "
        ).link("our website", "https://acecentre.org.uk", "link"
        ).paragraph(
            " to find out more about how we provide support for people with"
            " complex communications difficulties."
        ).paragraph("Updates", "h2"
        ).span("This software can "
        ).clickable(
            "check for updates", self.check_updates, []
            , "Download releases information now."
            , "link"
        ).span(" on its "
        ).link("releases website",  App().releasesWebsite, "link"
        ).paragraph("."
        ).paragraph(f"Version {App().version}"
        ).span(Para(self._updateHost.releasesSummary)
        ).span(" ", "spacer"
        ).span(Para(self._updateHost.installerSummary)
        ).span(" ", "spacer"
        ).clickable(
            Para(self._updateHost.installerPrompt), self.install_update, []
            , "Launch installer"
            , "link"
        ).paragraph("Attribution", "h2"
        ).span("Blink graphics in the user interface are based on "
        ).link(
            "Eye icons created by Kiranshastry - Flaticon"
            , "https://www.flaticon.com/free-icons/eye"
            , "link"
        ).span(".\nThis software was based on "
        ).link("Grimassist", "https://github.com/acidcoke/Grimassist/", "link"
        ).span(", itself based on "
        ).link(
            "Google GameFace"
            , "https://github.com/google/project-gameface"
            , "link"
        ).span(".")

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
        lastFetch = None # UpdateManager().lastFetch
        return "never" if lastFetch is None else lastFetch.strftime("%c")

    def hover_enter(self, event, anchor, tip):
        logger.info(f'hover_enter(,{event.type=},{anchor=},{tip=})')
        self.text.configure(cursor=self.hoverCursor)
        # TOTH how to set the text of a label.
        # https://stackoverflow.com/a/17126015/7657675
        self.hoverLabel.configure(text=tip)
        # Put the hover label in the bottom left corner of the page.
        self.hoverLabel.place(x=0, rely=1, anchor='sw')

    def hover_leave(self, event, anchor, tip):
        logger.info(f'hover_leave(,{event.type=},{anchor=},{tip=})')
        self.text.configure(cursor=self.initialCursor)
        # TOTH how to set the text of a label.
        # https://stackoverflow.com/a/17126015/7657675
        self.hoverLabel.configure(text="")
        # Make the hover label disappear.
        self.hoverLabel.place_forget()

    def check_updates(self, event, anchor):
        logger.info(f'check_updates(,{event.type=},{anchor=})')
        UpdateManager().manage(checkNow=True)
    
    def install_update(self, event, anchor):
        logger.info(f'install_update(,{event.type=},{anchor=})')
        UpdateManager().launch_installer()

    def enter(self):
        super().enter()

        # Next line would opens the About file in the browser.
        # open_in_browser(aboutHTML.as_uri(), None)

    def refresh_profile(self):
        pass

class Clickable(NamedTuple):
    identifier:str
    callback:Callable
    parameters:list[Any]
    hoverTip:str
    page:PageAbout

    # Jim initially was using Python lambda expressions for the event handlers.
    # That seemed to result in all tag_bind() calls being overridden to
    # whichever was the last one called. So now lambda expressions aren't used.
    def enter(self, event):
        self.page.hover_enter(event, self.identifier, self.hoverTip)
    def leave(self, event):
        self.page.hover_leave(event, self.identifier, self.hoverTip)
    def click(self, event):
        parameters = [event, self.identifier] + self.parameters
        self.callback(*parameters)
    
    def configure(self):
        self.page.text.tag_configure(self.identifier)

        # TOTH using tag_bind. https://stackoverflow.com/a/65733556/7657675  
        # TOTH list of events that makes clear they have to be in angle
        # brackets. https://stackoverflow.com/a/32289245/7657675
        #
        # -   <Enter> is triggered when the pointer hovers here.
        # -   <Leave> is triggered when the pointer stops hovering here.
        # -   <1> is triggered when this is clicked. It seems to be a shorthand
        #     for button-1.
        self.page.text.tag_bind(self.identifier, "<Enter>", self.enter)
        self.page.text.tag_bind(self.identifier, "<Leave>", self.leave)
        self.page.text.tag_bind(self.identifier, "<1>", self.click)
        return self

    @classmethod
    def link(cls, identifier:str, address:str, page:PageAbout):
        def open_in_browser(event, anchor, url):
            webbrowser.open(url)

        return cls(identifier, open_in_browser, [address], address, page)

class Dynamic(NamedTuple):
    identifier:str
    start:str
    finish:str
    eol:str
    observable:StringVar | Para
    styleTags:list[str]
    page:PageAbout

    @classmethod
    def stubbed(cls, identifier, observable, page, *tags):
        return cls(
            identifier
            , "-".join((identifier, "start"))
            , "-".join((identifier, "finish"))
            , "".join((identifier, "eol"))
            , observable
            #
            # Filter out the identifier tag which will be added by the setter.
            , tuple(tag for tag in tags if tag != identifier)
            , page
        )

    def configure(self):
        self.page.text.tag_configure(self.identifier)
        self.page.text.tag_configure(self.eol)

        # Marks are set to a position just before the "newline that Tk always
        # adds at the end of the text."  
        # See https://tkdocs.com/tutorial/text.html#modifying
        #
        # They have left gravity so that subsequent text inserted at END gets
        # appended after the marks.  
        # See https://tkdocs.com/tutorial/text.html#marks
        self.page.text.mark_set(self.start, 'end - 1 chars')
        self.page.text.mark_gravity(self.start, 'left')
        self.page.text.mark_set(self.finish, self.start)
        self.page.text.mark_gravity(self.finish, 'left')
        return self

    def setter(self):
        newText = self.observable.get()
        tkText = self.page.text
        logger.info(
            f'{self.identifier=} {newText=} {tkText.index(self.start)}'
            f' {tkText.index(self.finish)}')
        startIndex = tkText.index(self.start)
        finishIndex = tkText.index(self.finish)

        # The Text object must be editable while the update is applied. When the
        # update is finished it will be reverted to whatever state it was in
        # before.
        initialState = tkText['state']
        tkText.configure(state='normal')

        # Delete the old text and remove the tags.
        if startIndex != finishIndex:
            logger.info(self._tag_ranges())
            for tagName in (self.identifier, self.eol):
                tkText.tag_remove(tagName, self.start, self.finish)
            logger.info(self._tag_ranges())
            tkText.delete(self.start, self.finish)

        # If the newText ends with a newline then the newline mustn't be inside
        # the identifier tag. However, there must be a tag so that the finish
        # mark can be positioned.
        insertions = []
        splits = newText.split("\n")
        for splitIndex, split in enumerate(splits):
            if splitIndex > 0:
                insertions.extend(("\n", (self.eol, *self.styleTags)))
            if split != "":
                insertions.extend((split, (self.identifier, *self.styleTags)))

        if len(insertions) == 0:
            finishPosition = self.start
        else:
            tkText.insert(self.start, *insertions)
            finishPosition = ".".join((insertions[-1][0], "last"))
        logger.info(
            f'{splits=} {insertions=} {finishPosition=} {self._tag_ranges()}')

        tkText.mark_set(self.finish, finishPosition)
        tkText.configure(state=initialState)
    
    def _tag_ranges(self):
        return (
            f' {self.identifier=}'
            f' {self.page.text.tag_ranges(self.identifier)}'
            f' {self.eol=}'
            f' {self.page.text.tag_ranges(self.eol)}'
        )

    def tracer(self, *args):
        logger.info(f'tracer{args}')
        self.setter()

class SpannedText:
    def __init__(self, pageAbout):
        self._page = pageAbout
        self._anchors = {}

    def _new_anchor_identifier(self):
        identifier = f'anchor{len(self._anchors)}'
        self._anchors[identifier] = []
        return identifier

    def _span(self, text, tags, identifier=None):
        if type(text) in (StringVar, Para):
            if identifier is None:
                identifier = self._new_anchor_identifier()
            anchor = Dynamic.stubbed(
                identifier, text, self._page, *tags).configure()
            self._anchors[anchor.identifier].append(anchor)
            # Invoke the setter to insert the text.
            anchor.setter()
            text.trace('w', anchor.tracer)
        else:
            self._page.text.insert(END, text, tags)
        return self

    def span(self, text, *tags):
        return self._span(text, tags)

    def paragraph(self, text, *tags):
        return self._span(text + "\n", tags)
    
    def link(self, text, address, *tags):
        identifier = self._new_anchor_identifier()
        anchor = Clickable.link(identifier, address, self._page).configure()
        self._anchors[identifier].append(anchor)
        return self._span(text, (anchor.identifier, *tags), identifier)

    def clickable(self, text, callback, parameters, hoverTip, *tags):
        identifier = self._new_anchor_identifier()
        anchor = Clickable(
            identifier, callback, parameters, hoverTip, self._page).configure()
        self._anchors[identifier].append(anchor)
        return self._span(text, (identifier, *tags), identifier)
