import ScrollRenderer
import asyncio
import os
import sys

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

        if self.text == "":
            file = open(self.getFilePath(), "r")
            self.text = file.read().split("\n")

            file.close()

        self.setWidthHeight()
        self.Scrollrenderer = ScrollRenderer.ScrollRenderer(self.width, self.height, self.linesScrolled, self.text)

        loop = asyncio.get_event_loop()
        self.render()
        loop.run_until_complete(self.main())

    async def main(self):
        while True:
            # listen for down arrow key
            key = await self.getKey()
            if key == "DOWN":
                if self.linesScrolled < len(self.text) - self.height:
                    self.linesScrolled += 1
                    self.render()
            if key == "UP":
                if self.linesScrolled > 0:
                    self.linesScrolled -= 1
                    self.render()
            if key == "q":
                break
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
        # print text
        # self.Scrollrenderer.render()
        scrollRenderedLines = self.Scrollrenderer.renderLines()

        for i in scrollRenderedLines:

            # if last element in list, no newline
            if i == scrollRenderedLines[-1]:
                # remove newline character
                if i[-1] == "\n":
                    print(i[:-1], end="")
                else:
                    print(i, end="")
            else:
                print(i, end="")