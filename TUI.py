import sys
import os
from abc import ABC, abstractmethod
import asyncio
from asyncio.subprocess import PIPE, STDOUT
from ScrollRenderer import ScrollRenderer
import ctypes
from ctypes import wintypes
import msvcrt


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
