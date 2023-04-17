
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