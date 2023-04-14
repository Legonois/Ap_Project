import sys
import os
import select
import termios
import tty

def enable_raw_mode():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setraw(sys.stdin.fileno())
    return old_settings

def restore_terminal(old_settings):
    fd = sys.stdin.fileno()
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def main():
    old_settings = enable_raw_mode()
    cursor_x, cursor_y = 0, 0

    try:
        # Hide cursor and clear screen
        sys.stdout.write("\033[?25l\033[2J")
        sys.stdout.flush()

        while True:
            # Wait for input
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                key = sys.stdin.read(1)

                if key == "q":
                    break
                elif key == "\033":  # Escape sequence
                    key += sys.stdin.read(2)  # Read 2 more characters

                    if key == "\033[A":
                        cursor_y = max(0, cursor_y - 1)
                    elif key == "\033[B":
                        cursor_y += 1
                    elif key == "\033[C":
                        cursor_x += 1
                    elif key == "\033[D":
                        cursor_x = max(0, cursor_x - 1)

            # Move cursor to the new position
            sys.stdout.write(f"\033[{cursor_y};{cursor_x}H")
            sys.stdout.flush()

    finally:
        # Show cursor and restore terminal settings
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        restore_terminal(old_settings)

if __name__ == "__main__":
    main()
