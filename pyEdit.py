import ScrollRenderer
import asyncio
import os
import sys
from TUI import UnixTUI
from TUI import WindowsTUI
from TUI import BaseTUI

class pyEdit:
    def __init__(self):
        self.text = ""
        self.linesScrolled = 0

    def getFilePath(self):
        # search current directory for a file
        dir = os.listdir()

        print("Choose a file to open: ")

        textFiles = []

        for file in dir:
            if file.endswith(".txt"):
                textFiles.append(file)

        for i in range(len(textFiles)):
            print(f"{i+1}: {textFiles[i]}")

        # listen for user input of a number
        while True:
            try:
                choice = int(input())
                if choice > len(textFiles) or choice < 1:
                    print("Invalid choice")
                else:
                    break
            except:
                print("Invalid choice")

        return textFiles[choice-1]
                
    def setWidthHeight(self):
        size = os.get_terminal_size()
        self.width = size.columns
        self.height = size.lines


    def run(self):
        # start async loop

        try:
                
            if os.name == "posix":
                TUI = UnixTUI
            elif os.name == "nt":
                TUI = WindowsTUI
            else:
                raise NotImplementedError("Unsupported operating system")

            if self.text == "":
                file = open(self.getFilePath(), "r")
                self.text = file.read()

                file.close()

            self.tui = TUI()
            self.tui.enable_raw_mode()
            self.tui.hide_cursor()
            self.tui.clear_screen()
            self.tui.cursor_y = 2

            self.setWidthHeight()
            self.Scrollrenderer = ScrollRenderer.ScrollRenderer(self.width, self.height, self.linesScrolled, self.text)

            loop = asyncio.get_event_loop()
            self.render()
            loop.run_until_complete(self.main())
        finally:
            self.tui.move_cursor(0, 0)
            self.tui.show_cursor()
            self.tui.clear_screen()
            self.tui.restore_terminal()

    async def main(self):
        while True:
            # listen for down arrow key
            key = await self.getKey()
            if key == "DOWN":
                if self.linesScrolled < len(self.text) - self.height and self.tui.cursor_y == self.height - 1:
                    self.linesScrolled += 5
                    self.tui.cursor_y -= 5
                    self.render()
                else:
                    self.tui.cursor_y += 1
                    self.render()
            if key == "UP":
                if self.linesScrolled > 0 and self.tui.cursor_y == 2:
                    self.linesScrolled -= 5
                    self.tui.cursor_y += 5
                    self.render()
                elif self.tui.cursor_y > 2:
                    self.tui.cursor_y -= 1
                    self.render()
                else:
                    self.tui.cursor_y = 2
                    self.render()
            if key == "LEFT":
                if self.tui.cursor_x > 0:
                    self.tui.cursor_x -= 1
                    self.render()
            if key == "RIGHT":
                if self.tui.cursor_x < self.width - 1:
                    self.tui.cursor_x += 1
                    self.render()
            # if key == control c
            if key == "\x03":
                # throw exception
                raise KeyboardInterrupt
            # if control c is pressed
            if key == "\x03":
                # throw exception
                raise KeyboardInterrupt

    async def getKey(self):
        if os.name == 'nt':
            # Windows
            import msvcrt

            def getKey():
                while True:
                    if msvcrt.kbhit():
                        key_stroke = msvcrt.getch()
                        if key_stroke == b'\x00' or key_stroke == b'\xe0':
                            key_stroke = msvcrt.getch()
                            if key_stroke == b'H':
                                return "UP"
                            if key_stroke == b'P':
                                return "DOWN"
                            if key_stroke == b'M':
                                return "RIGHT"
                            if key_stroke == b'K':
                                return "LEFT"
                        else:
                            return key_stroke.decode("utf-8")

            return getKey()
        else:
            # macOS and Linux
            import termios
            import tty

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)

            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

            if ch == '\x1b':
                ch = ch + sys.stdin.read(2)
                if ch == '\x1b[A':
                    return "UP"
                if ch == '\x1b[B':
                    return "DOWN"
                if ch == '\x1b[C':
                    return "RIGHT"
                if ch == '\x1b[D':
                    return "LEFT"
                else:
                    return ch
            else:
                return ch

    def render(self):
        self.setWidthHeight()

        self.Scrollrenderer.width = self.width
        self.Scrollrenderer.height = self.height
        self.Scrollrenderer.linesScrolled = self.linesScrolled
        self.Scrollrenderer.text = self.text

        # clear screen
        print("\033c", end="")

        scrollRenderedLines = self.Scrollrenderer.renderLines()   

        # set cursor position
        self.tui.show_cursor()
        self.tui.move_cursor(self.tui.cursor_x, self.tui.cursor_y)  
        self.tui.render(scrollRenderedLines, "Hello World! This is my text editor. Press q to quit.")
