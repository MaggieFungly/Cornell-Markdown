from PyQt5.QtWidgets import QApplication, QTextEdit, QMainWindow, QTextBrowser, QWidget, QVBoxLayout
from PyQt5.QtGui import QTextCursor, QColor, QTextBlockFormat, QFont, QTextCharFormat, QSyntaxHighlighter
from PyQt5.QtCore import Qt, QRegExp, QRegularExpression
import mistune
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import html
from mistune import HTMLRenderer, escape
import sys

class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(MarkdownHighlighter, self).__init__(parent)

        headingFormat = QTextCharFormat()
        headingFormat.setForeground(QColor(45, 130, 189))
        headingFormat.setFontWeight(QFont.Bold)

        highlightFormat = QTextCharFormat()
        highlightFormat.setBackground(QColor(230, 195, 99, 90))

        boldItalicFormat = QTextCharFormat()
        boldItalicFormat.setFontWeight(QFont.Bold)
        boldItalicFormat.setFontItalic(True)

        boldFormat = QTextCharFormat()
        boldFormat.setFontWeight(QFont.Bold)

        italicFormat = QTextCharFormat()
        italicFormat.setFontItalic(True)

        inlineCodeFormat = QTextCharFormat()
        inlineCodeFormat.setFontFamily("Consolas")
        inlineCodeFormat.setForeground(QColor(109, 163, 148))
        inlineCodeFormat.setBackground(QColor(180, 214, 197, 70))

        inlineMathFormat = QTextCharFormat()
        inlineMathFormat.setFontFamily("CMU Serif")
        inlineMathFormat.setFontItalic(True)

        codeBlockFormat = QTextCharFormat()
        codeBlockFormat.setFontFamily("Consolas")
        codeBlockFormat.setForeground(QColor(109, 163, 148))

        linkFormat = QTextCharFormat()
        linkFormat.setForeground(QColor(131, 178, 196))

        self.highlightingRules = [
            (QRegularExpression(r'^#+\s.*'), headingFormat),  # Headings
            (QRegularExpression(r'\=\=(.*?)\=\='),
             highlightFormat),  # highlight text
            (QRegularExpression(r'\*(.*?)\*'), italicFormat),  # Italic text
            (QRegularExpression(r'\*\*(.*?)\*\*'), boldFormat),  # Bold text
            (QRegularExpression(r'\*\*\*(.*?)\*\*\*'),
             boldItalicFormat),  # Bold and italic text
            (QRegularExpression(r'`([^`]+)`'), inlineCodeFormat),  # Code
            (QRegularExpression(r'\$(.*?)\$'), inlineMathFormat),  # Inline equations
            (QRegularExpression(r'\[([^\]]+)\]\(([^)]+)\)'),
             linkFormat),  # Links
            (QRegularExpression(r'```(.*?)```',
             QRegularExpression.DotMatchesEverythingOption |
             QRegularExpression.MultilineOption), codeBlockFormat)
            # Add more highlighting rules for other Markdown elements.
        ]

    def highlightBlock(self, text):
        for pattern, char_format in self.highlightingRules:
            expression = QRegularExpression(pattern)
            match = expression.match(text)
            while match.hasMatch():
                self.setFormat(match.capturedStart(),
                               match.capturedLength(), char_format)
                match = expression.match(text, match.capturedEnd())


class MarkdownTextEdit(QTextEdit):

    auto_pairing_symbols = {
        "(": ")",
        "{": "}",
        "[": "]",
        "'": "'",
        "*": "*",
        "$": "$",
        "<": ">",
        "`": "`", }

    def __init__(self, *args, **kwargs):
        super(MarkdownTextEdit, self).__init__(*args, **kwargs)

        self.highlighter = MarkdownHighlighter(self.document())

    def keyPressEvent(self, event):

        symbol = event.text()

        cursor = self.textCursor()

        if symbol in self.auto_pairing_symbols.keys():

            selected_text = cursor.selectedText()

            if selected_text:
                original_position = cursor.selectionStart(), cursor.selectionEnd()

                cursor.insertText(symbol + selected_text +
                                  self.get_closing_bracket(symbol))

                cursor.setPosition(original_position[0] + 1)
                cursor.setPosition(
                    original_position[1] + 1, QTextCursor.KeepAnchor)
                self.setTextCursor(cursor)

            else:
                cursor.insertText(symbol)
                cursor.insertText(self.get_closing_bracket(symbol))
                cursor.movePosition(QTextCursor.PreviousCharacter)
                self.setTextCursor(cursor)

        else:
            super(MarkdownTextEdit, self).keyPressEvent(event)

        format = QTextCharFormat()
        format.setFontWeight(QFont.Normal)

        if cursor.block().text().startswith("# "):
            format.setFontWeight(QFont.Bold)

        cursor.select(QTextCursor.LineUnderCursor)
        cursor.mergeCharFormat(format)


    @staticmethod
    def get_closing_bracket(opening_bracket):
        return MarkdownTextEdit.auto_pairing_symbols[opening_bracket]


class Example(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        vbox = QVBoxLayout(self)
        vbox.addWidget(MarkdownTextEdit())

        self.show()


def main():

    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
