
# File 1: ScrollRenderer
class ScrollRenderer:
    def __init__(self, width, height, linesScrolled, text):
        self.width = width
        self.height = height
        self.linesScrolled = linesScrolled
        self.text = text

    def formatTextForWidth(self, text):
        formattedText = []
        for line in text.splitlines():
            if len(line) > self.width:
                formattedText.append(line[:self.width])
            else:
                formattedText.append(line)
        return formattedText

    def render(self):
        formattedText = self.formatTextForWidth(self.text.splitlines())

        if self.linesScrolled > len(formattedText) - self.height:
            raise RenderException("Cannot scroll past end of file")
        if self.linesScrolled < 0:
            raise RenderException("Cannot scroll past beginning of file")

        for line in formattedText[self.linesScrolled:self.linesScrolled + self.height]:
            print(line)

    def renderLines(self):
        formattedText = self.formatTextForWidth(self.text)

        if self.linesScrolled > len(formattedText) - self.height:
            raise RenderException("Cannot scroll past end of file")
        if self.linesScrolled < 0:
            raise RenderException("Cannot scroll past beginning of file")

        output = []
        for line in formattedText[self.linesScrolled:self.linesScrolled + self.height]:
            output.append(line + "\n")
        
        # convert list to string with newlines
        return "".join(output)

# custom render exception
class RenderException(Exception):
    pass

# File 2: TUI.py

import sys
import os
from abc import ABC, abstractmethod
import asyncio
from asyncio.subprocess import PIPE, STDOUT
import ctypes
from ctypes import wintypes

class BaseTUI(ABC):
    def __init__(self):
        self.cursor_x = 0
        self.cursor_y = 0
        self.width = 0
        self.height = 0
        self.pos = [0, 0] # [char x, line y]

    @abstractmethod
    def enable_raw_mode(self):
        pass

    @abstractmethod
    def restore_terminal(self):
        pass

    @abstractmethod
    async def read_key(self):
        pass

    @abstractmethod
    def clear_screen(self):
        pass

    @abstractmethod
    def move_cursor(self, x, y):
        pass

    @abstractmethod
    def show_cursor(self):
        pass

    @abstractmethod
    def hide_cursor(self):
        pass

    @abstractmethod
    def render(self, text, status):
        pass


class UnixTUI(BaseTUI):
    def __init__(self):
        super().__init__()
        self.old_settings = None

        self.width, self.height = os.get_terminal_size()

    def enable_raw_mode(self):
        import termios
        import tty

        fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(fd)
        tty.setraw(sys.stdin.fileno())

    def restore_terminal(self):
        import termios

        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, self.old_settings)

    async def read_key(self):
        import select

        while True:
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                return sys.stdin.read(1)
            await asyncio.sleep(0.01)  # Add a small delay to reduce CPU usage

    def clear_screen(self):
        sys.stdout.write("\033[2J")
        sys.stdout.flush()

    def move_cursor(self, x, y):
        sys.stdout.write(f"\033[{y};{x}H")
        sys.stdout.flush()

    def show_cursor(self):
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    def hide_cursor(self):
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    def render(self, text, status, overlay=None):
        self.clear_screen()

        if overlay is not None:
            for line in overlay.splitlines():
                # write right-aligned
                sys.stdout.write(" " * (self.width - len(line)))

        self.width, self.height = os.get_terminal_size()

        linenum = 2
        for line in text.splitlines():
            sys.stdout.write(f"\033[{linenum};0H")
            sys.stdout.write(line)
            linenum += 1

        sys.stdout.write(f"\033[0;0H")
        # white background, black text
        sys.stdout.write("\033[47m\033[30m")
        sys.stdout.write(status)
        # add whitespace to clear the rest of the line
        sys.stdout.write(" " * (self.width - len(status)))
        sys.stdout.write("\n")
        # reset colors
        sys.stdout.write("\033[0m")
        self.move_cursor(self.cursor_x, self.cursor_y)
        sys.stdout.flush()

class WindowsTUI(BaseTUI):
    def __init__(self):
        super().__init__()
        self.kernel32 = ctypes.windll.kernel32
        self.GetStdHandle = self.kernel32.GetStdHandle
        self.SetConsoleCursorPosition = self.kernel32.SetConsoleCursorPosition
        self.SetConsoleMode = self.kernel32.SetConsoleMode
        self.GetConsoleScreenBufferInfo = self.kernel32.GetConsoleScreenBufferInfo
        self.GetConsoleMode = self.kernel32.GetConsoleMode
        self.STD_OUTPUT_HANDLE = -11
        self.STD_INPUT_HANDLE = -10
        self.hstdout = self.GetStdHandle(self.STD_OUTPUT_HANDLE)
        self.hstdin = self.GetStdHandle(self.STD_INPUT_HANDLE)
        self.original_mode = wintypes.DWORD()
        self.enable_raw_mode()

    def enable_raw_mode(self):
        self.GetConsoleMode(self.hstdin, ctypes.byref(self.original_mode))
        new_mode = self.original_mode.value & ~(0x0001 | 0x0004)  # Clear ENABLE_PROCESSED_INPUT and ENABLE_LINE_INPUT flags
        self.SetConsoleMode(self.hstdin, new_mode)

    def restore_terminal(self):
        self.SetConsoleMode(self.hstdin, self.original_mode)

    async def read_key(self):
        while True:
            import msvcrt
            if msvcrt.kbhit():
                return msvcrt.getwch()
            await asyncio.sleep(0.01)

    def clear_screen(self):
        os.system("cls")

    def move_cursor(self, x, y):
        coord = wintypes._COORD(x, y)
        self.SetConsoleCursorPosition(self.hstdout, coord)

    def show_cursor(self):
        console_info = self._get_console_info()
        console_info.bVisible = True
        self._set_console_info(console_info)

    def hide_cursor(self):
        console_info = self._get_console_info()
        console_info.bVisible = False
        self._set_console_info(console_info)

    def _get_console_info(self):
        class CONSOLE_CURSOR_INFO(ctypes.Structure):
            _fields_ = [("dwSize", wintypes.DWORD),
                        ("bVisible", wintypes.BOOL)]

        console_info = CONSOLE_CURSOR_INFO()
        self.kernel32.GetConsoleCursorInfo(self.hstdout, ctypes.byref(console_info))
        return console_info

    def _set_console_info(self, console_info):
        self.kernel32.SetConsoleCursorInfo(self.hstdout, ctypes.byref(console_info))

    def render(self, text, status, overlay=None):
        self.clear_screen()
        sys.stdout.write("\033[0;0H")  # Move to the top-left corner
        sys.stdout.write(status + "\n")
        sys.stdout.write(text)
        self.move_cursor(self.cursor_x, self.cursor_y)  # Move the cursor to its current position
        sys.stdout.flush()

# File 3: pyEdit.py

import asyncio
import os
import sys

class pyEdit:
    def __init__(self):
        self.text = ""
        self.linesScrolled = 0
        self.pos = [0, 0] # [char x, line y]
        self.numChar = 0
        self.numLine = 0
        self.wantChar = 0
        self.debug = ""
        self.filename = ""

    #returns the path to one text file
    def getFilePath(self):
        # search current directory for a file
        dir = os.listdir() # get a list of files

        print("Choose a file to open: ")

        # Create a empty list to store text files
        textFiles = []

        # Search for text files in the directory
        for file in dir:
            if file.endswith(".txt"):
                # Add the file to the list
                textFiles.append(file)

        # Print the list of text files to the user
        for i in range(len(textFiles)):
            print(f"{i+1}: {textFiles[i]}")

        # Listen for user input of a number
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
                self.filename = self.getFilePath()
                file = open(self.filename, "r")
                self.text = file.read()

                file.close()

            self.tui = TUI()
            self.tui.enable_raw_mode()
            self.tui.hide_cursor()
            self.tui.clear_screen()
            self.tui.cursor_y = 2

            self.setWidthHeight()
            self.Scrollrenderer = ScrollRenderer(self.width, self.height, self.linesScrolled, self.text)

            loop = asyncio.get_event_loop()
            self.render()
            loop.run_until_complete(self.main())
        finally:
            self.tui.move_cursor(0, 0)
            self.tui.show_cursor()
            self.tui.clear_screen()
            self.tui.restore_terminal()

    def Down(self):
        if self.linesScrolled + 5 < len(self.text) - self.height and self.tui.cursor_y == self.height - 1:
            self.linesScrolled += 5
            self.tui.cursor_y -= 5
            self.placeCursor(self.wantChar, self.tui.cursor_y)
            self.render()
        elif self.linesScrolled == len(self.text) - self.height and self.tui.cursor_y == self.height - 1:
            self.linesScrolled = len(self.text) - self.height
            self.tui.cursor_y += 1
            self.placeCursor(self.wantChar, self.tui.cursor_y)
            self.render()
        else:
            self.tui.cursor_y += 1
            self.placeCursor(self.wantChar, self.tui.cursor_y)  # Update the cursor position
            self.render()



    def Up(self):
        if self.linesScrolled - 5 > 0 and self.tui.cursor_y == 2:
            self.linesScrolled -= 5
            self.tui.cursor_y += 5
            self.placeCursor(self.wantChar, self.tui.cursor_y)
            self.render()
        elif self.linesScrolled > 0 and self.tui.cursor_y == 2:
            self.linesScrolled = 0
            self.tui.cursor_y -= 1
            self.placeCursor(self.wantChar, self.tui.cursor_y)
            self.render()
        else:
            self.tui.cursor_y -= 1
            self.placeCursor(self.wantChar, self.tui.cursor_y)
            self.render()

    async def main(self):
        while True:
            # listen for down arrow key
            key = await self.getKey()
            # Bugged beyond belief right now
            if key == "DOWN":
                self.Down()
            
            elif key == "UP":
                self.Up()
            
            elif key == "LEFT":
                if self.tui.cursor_x > 0:
                    self.tui.cursor_x -= 1
                    self.wantChar = self.tui.cursor_x
                    self.placeCursor(self.tui.cursor_x, self.tui.cursor_y)
                    self.render()
            
            elif key == "RIGHT":
                if self.tui.cursor_x < self.width - 1:
                    self.tui.cursor_x += 1
                    self.wantChar = self.tui.cursor_x
                    self.placeCursor(self.tui.cursor_x, self.tui.cursor_y)
                    self.render()
            # if key == control c
            elif key == "\x03":
                # throw exception
                raise KeyboardInterrupt
            # if key == backspace
            elif key == "\x7f":
                self.deleteChar()
            # if key == enter
            elif key == "SAVE":
                self.Save()
                break
            elif key == "\r":
                self.insertChar("\n")
            else:
                self.insertChar(key)

    def Save(self):
        file = open(self.filename, "w")
        file.write(self.text)
        file.close()

    def insertChar(self, char):
        # self.text = self.text[:self.pos[0]] + char + self.text[self.pos[0]:]

        # split text into lines
        text = self.text.splitlines()

        # get the line the cursor is on
        line = text[self.pos[1]]

        # if char == "\n":
        #     # move the cursor to the start of the next line
        #     self.tui.cursor_y += 1
        #     self.tui.cursor_x = 0

        #     self.pos = [0, self.pos[1] + 1]
        # get the char the cursor is on and add the new char
        line = line[:self.pos[0]] + char + line[self.pos[0]:]

        # replace the line with the new line
        text[self.pos[1]] = line

        # join the lines back together
        self.text = "\n".join(text)

        if char == "\n":
            # move the cursor to the start of the next line
            self.tui.cursor_y += 1 + self.linesScrolled
            self.tui.cursor_x = 1

            self.pos = [0, self.pos[1] + 1]
        else:
            self.pos[0] += 1
            self.numChar += 1
            self.tui.cursor_x += 1

        # move the cursor
        # self.tui.cursor_x += 1
        self.wantChar = self.tui.cursor_x
        self.placeCursor(self.tui.cursor_x, self.tui.cursor_y)

        self.render()

    def deleteChar(self):
        # split text into lines
        text = self.text.splitlines()

        # if the cursor is at the start of the line
        if self.pos[0] == 0:
            # add the current line to the previous line
            text[self.pos[1] - 1] += text[self.pos[1]]
            # remove the current line
            text.pop(self.pos[1])
            self.pos[1] -= 1
            self.pos[0] = len(text[self.pos[1]])
        else:
            # get the line the cursor is on
            line = text[self.pos[1]]

            # get the char the cursor is on and add the new char
            line = line[:self.pos[0] - 1] + line[self.pos[0]:]

            # replace the line with the new line
            text[self.pos[1]] = line
            self.pos[0] -= 1
            self.numChar -= 1

        # join the lines back together
        self.text = "\n".join(text)


        # move the cursor
        self.tui.cursor_x = self.pos[0] + 1
        self.tui.cursor_y = self.pos[1] + 2 + self.linesScrolled
        self.wantChar = self.tui.cursor_x
        self.placeCursor(self.tui.cursor_x, self.tui.cursor_y)

        self.render()

    async def getKey(self):

        # Created using help from StackOverflow 

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
                            decoded_key = key_stroke.decode("utf-8")
                            if decoded_key == chr(19):  # Control + S
                                return "SAVE"
                            return decoded_key

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
                if ch == chr(19):  # Control + S
                    return "SAVE"
                return ch


    def render(self):
        self.setWidthHeight()

        self.Scrollrenderer.width = self.width
        self.Scrollrenderer.height = self.height - 1
        self.Scrollrenderer.linesScrolled = self.linesScrolled
        self.Scrollrenderer.text = self.text

        # clear screen
        print("\033c", end="")

        scrollRenderedLines = self.Scrollrenderer.renderLines()   

        # set cursor position
        self.tui.show_cursor()
        self.tui.move_cursor(self.tui.cursor_x, self.tui.cursor_y)
        self.tui.render(scrollRenderedLines, "Hello World! This is my text editor. Press q to quit. Ctrl-S to Save. " + self.debug, overlay="Hello guys! = none \n Testing again! \n")

    def placeCursor(self, char, relLine):
        line = self.linesScrolled + relLine - 2 # -2 because of the header and index
        if line < len(self.text.splitlines()):
            self.numLine = line
            if char <= len(self.text.splitlines()[line]):
                self.numChar = char
            else:
                self.numChar = len(self.text.splitlines()[line]) + 1
            
            self.tui.cursor_x = self.numChar
            self.tui.cursor_y = self.numLine - self.linesScrolled + 2
            self.tui.move_cursor(self.tui.cursor_x, self.tui.cursor_y)

            # Text index
            self.pos[0] = self.numChar - 1
            self.pos[1] = self.numLine

            self.debug = f"Line: {self.pos[1]} Char: {self.pos[0]} Cursor: {self.tui.cursor_x}, {self.tui.cursor_y}"
        else:
            raise ScrollRenderer.RenderException("Line number out of range of cursor placement")

# File 4: main.py

import os

def main():
    
    Program = pyEdit()

    Program.run()

if __name__ == "__main__":
    main()

    # wait for user to press enter
    print("Press enter to exit")
    input()