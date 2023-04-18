import sys
import os
from abc import ABC, abstractmethod
import asyncio
from asyncio.subprocess import PIPE, STDOUT
from ScrollRenderer import ScrollRenderer

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

    def enable_raw_mode(self):
        import msvcrt

        self.old_settings = msvcrt.getch()

    def restore_terminal(self):
        import msvcrt

        msvcrt.putch(self.old_settings)

    async def read_key(self):
        import msvcrt

        while True:
            if msvcrt.kbhit():
                return msvcrt.getch().decode('utf-8')
            await asyncio.sleep(0.01)  # Add a small delay to reduce CPU usage


    def clear_screen(self):
        os.system("cls")

    def move_cursor(self, x, y):
        os.system(f"echo off && set /p= < nul && echo {chr(27)}[{y};{x}H")

    def show_cursor(self):
        pass  # Not implemented

    def hide_cursor(self):
        pass  # Not implemented

    def render(self, text, status):
        self.clear_screen()
        # sys.stdout.write(text)
        sys.stdout.write("\033[0;0H")  # Move to the top-left corner
        sys.stdout.write(status + "\n")
        sys.stdout.write(text)
        self.move_cursor(self.cursor_x, self.cursor_y)  # Move the cursor to its current position
        sys.stdout.flush()


if os.name == "posix":
    TUI = UnixTUI
elif os.name == "nt":
    TUI = WindowsTUI
else:
    raise NotImplementedError("Unsupported operating system")

def list_to_string(list):
    string = ""
    for i in list:
        string += i
    return string

async def main():
    # Example usage
    tui = TUI()
    tui.enable_raw_mode()
    tui.hide_cursor()
    tui.clear_screen()

    text = "Hello to you too!"
    status = "Press q to quit"

    rendering = ScrollRenderer(os.get_terminal_size().columns, os.get_terminal_size().lines - 1, 0, "Hello World! \n new day \n new time \n excited for the day again \n woa that's a lot of text \n I wonder how long this will go on \n maybe I should just stop typing \n nah I'm having too much fun \n I wonder if this will work \n I hope it does \n I really hope it does \n I really really hope it does \n I really really really hope it does \n I really really really really hope it does \n I really really really really really hope it does \n I really really really really really really hope it does \n I really really really really really really really hope it does \n I really really really really really really really really hope it does \n I really really really really really really really really really hope it does \n I really really really really really really really really really really hope it does")

    tui.render(rendering.renderLines(), status)

    try:
        tui.show_cursor()
        while True:
            tui.render(rendering.renderLines(), status)

            key = await tui.read_key()
            if key == "q":
                break
            elif key == "\x03":
                raise KeyboardInterrupt
                break
            elif key == "\033":  # Escape sequence for UnixTUI
                key += sys.stdin.read(2)  # Read 2 more characters

                if key == "\033[A": # Up arrow
                    tui.cursor_y = max(0, tui.cursor_y - 1)
                elif key == "\033[B": # Down arrow
                    tui.cursor_y += 1
                elif key == "\033[C": # Right arrow
                    tui.cursor_x += 1
                elif key == "\033[D": # Left arrow
                    tui.cursor_x = max(0, tui.cursor_x - 1)
            tui.move_cursor(tui.cursor_x, tui.cursor_y)

    finally:
        tui.move_cursor(0,0)
        tui.show_cursor()
        tui.restore_terminal()

