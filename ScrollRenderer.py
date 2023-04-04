
class ScrollRenderer:
    def __init__(self, width, height, linesScrolled, text):
        self.width = width
        self.height = height
        self.linesScrolled = linesScrolled
        self.text = text

    def formatTextForWidth(self, text):
        formattedText = []
        for line in text:
            if len(line) > self.width:
                formattedText.append(line[:self.width])
            else:
                formattedText.append(line)
        return formattedText

    def render(self):
        formattedText = self.formatTextForWidth(self.text)
        for line in formattedText[self.linesScrolled:self.linesScrolled + self.height]:
            print(line)