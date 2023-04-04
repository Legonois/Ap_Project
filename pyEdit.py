import ScrollRenderer
import asyncio
import os

class pyEdit:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.text = ""
        self.linesScrolled = 0

    def getFilePath(self):
        # search current directory for a file
        dir = os.listdir()

        textFiles = []

        for file in dir:
            if file.endswith(".txt"):
                textFiles.append(file)

        if len(textFiles) == 0:
            return None

        return textFiles[0]
                
    def setWidthHeight(self):
        size = os.get_terminal_size()
        self.width = size.columns
        self.height = size.lines


    def run(self):
        # start async loop

        if self.text == "":
            self.text = open(self.getFilePath(), "r")

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.main())

    async def main(self):
        # listen for down arrow key
        key = await self.getKey()
        if key == "DOWN":
            self.linesScrolled += 1
            self.render()
        if key == "UP":
            self.linesScrolled -= 1
            self.render()

    async def getKey(self):
        return input()

    def render(self):
        ScrollRenderer(self.width, self.height, self.linesScrolled, self.text).render()
