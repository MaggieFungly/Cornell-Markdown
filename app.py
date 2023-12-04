import sys
import os
import json
from PyQt5 import QtCore
from PyQt5.QtCore import QEventLoop, Qt
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QDialog, QMenu, QSplitter, QToolButton, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QScrollArea, QFormLayout, QWidgetItem, QTextBrowser, QSpacerItem, QSizePolicy, QFileDialog, QMessageBox, QListWidget, QListWidgetItem, QListView, QAbstractItemView, QShortcut, QRadioButton, QComboBox
)
from PyQt5.QtGui import QFontMetrics, QKeySequence, QTextCursor, QIcon, QColor
from PyQt5.QtCore import QSize, pyqtSignal, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from MarkdownEditor import MarkdownTextEdit
import mistune

class Block:
    def __init__(self, title='', notes='', cues='', hierarchy=0, highlighted=0):
        self.title = title
        self.notes = notes
        self.cues = cues
        self.hierarchy = hierarchy
        self.highlighted = highlighted

    def to_dict(self):
        return {
            'title': self.title,
            'notes': self.notes,
            'cues': self.cues,
            'hierarchy': self.hierarchy,
            'highlighted': self.highlighted
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class ListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Adjust the scroll bar properties for smoother scrolling
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.setMouseTracking(True)

    def dragMoveEvent(self, event):
        if ((target := self.row(self.itemAt(event.pos()))) ==
            (current := self.currentRow()) or
                (current == self.count() - 1 and target == -1)):
            event.ignore()
        else:
            super().dragMoveEvent(event)


class BlockNotesCuesWidget(QWidget):
    def __init__(self, parent=None):
        super(BlockNotesCuesWidget, self).__init__(parent)

        # cues
        self.cues_render_edit_button = QPushButton("Render")

        self.cues_edit = MarkdownTextEdit()
        self.cues_edit.setObjectName("CuesEdit")
        self.cues_edit.textChanged.connect(self.auto_resize)

        self.cues_browser = QWebEngineView()
        # set attribute for the browser so it can be deleted when exiting the application
        self.cues_browser.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # notes
        self.notes_render_edit_button = QPushButton("Render")

        self.notes_edit = MarkdownTextEdit()
        self.notes_edit.setObjectName("NotesEdit")
        self.notes_edit.textChanged.connect(self.auto_resize)

        self.notes_browser = QWebEngineView()
        # set attribute for the browser so it can be deleted when exiting the application
        self.notes_browser.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # set widget height
        # edits
        self.notes_edit.setFixedHeight(100)
        self.cues_edit.setFixedHeight(100)

        # browsers
        self.notes_browser.setFixedHeight(100)
        self.cues_browser.setFixedHeight(100)

        self.cues_browser.setMaximumHeight(600)
        self.notes_browser.setMaximumHeight(600)

        # buttons
        self.notes_render_edit_button.setFixedHeight(30)
        self.cues_render_edit_button.setFixedHeight(30)

        # current mode
        self.cues_current_mode = "edit"
        self.notes_current_mode = "edit"

        self.cues_current_widget = self.cues_edit
        self.notes_current_widget = self.notes_edit

        self.cues_edit_to_browser_shortcut = QShortcut(
            QKeySequence("Ctrl+Return"), self)
        self.notes_edit_to_browser_shortcut = QShortcut(
            QKeySequence("Ctrl + Return"), self)

        # arrange layout
        notes_cues_layout = QGridLayout()
        notes_cues_layout.addWidget(self.cues_render_edit_button, 0, 0)
        notes_cues_layout.addWidget(self.cues_edit, 1, 0)
        notes_cues_layout.addWidget(self.notes_render_edit_button, 0, 1)
        notes_cues_layout.addWidget(self.notes_edit, 1, 1)

        # set sizes
        # column width ratio
        notes_cues_layout.setColumnStretch(0, 1)
        notes_cues_layout.setColumnStretch(1, 3)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.setLayout(notes_cues_layout)

        # set html contents
        with open('./head.html', 'r') as f:
            self.head_html = f.read()
            f.close()
        
        # set baseurl
        self.baseurl = QUrl.fromLocalFile(
            os.path.dirname(os.path.abspath(__file__)) + '/')

    def calculate_html_height(self, view):
        # JavaScript code to calculate the height of the content
        js_code = """
                    function documentHeight() {
                        var body = document.body;
                        var html = document.documentElement;
                        return Math.max(
                            body.scrollHeight, body.offsetHeight,
                            html.clientHeight, html.scrollHeight, html.offsetHeight
                        );
                    }
                    documentHeight();
                """
        result_list = []
        loop = QEventLoop()
        # Run the JavaScript code and get the result
        view.page().runJavaScript(js_code, lambda result: (
            result_list.append(result), loop.quit()))
        loop.exec_()
        return result_list

    def get_current_widget_height(self, widget, widget_mode):

        if widget_mode == "edit":
            font = widget.document().defaultFont()
            fontMetrics = QFontMetrics(font)
            # Measure the size of the text
            edit_size = fontMetrics.size(
                0, widget.toPlainText())
            edit_height = edit_size.height()
            return int(edit_height) + 25

        elif widget_mode == "browser":
            # Usage:
            result_list = self.calculate_html_height(widget)
            return int(result_list[0]) + 10

    def auto_resize(self):

        notes_height = self.get_current_widget_height(
            self.notes_current_widget, self.notes_current_mode)
        cues_height = self.get_current_widget_height(
            self.cues_current_widget, self.cues_current_mode)

        self.widget_height = max(notes_height, cues_height)

        # Set the size of the QTextEdit
        if self.widget_height < 100:
            self.widget_height = 100
        if self.widget_height >= 600:
            self.widget_height = 600

        if self.notes_current_mode == "edit":
            self.notes_edit.setFixedHeight(self.widget_height)
        else:
            self.notes_browser.setMaximumHeight(self.widget_height)
        if self.cues_current_mode == "edit":
            self.cues_edit.setFixedHeight(self.widget_height)
        else:
            self.cues_browser.setMaximumHeight(self.widget_height)

        self.setFixedHeight(
            self.widget_height +
            self.cues_render_edit_button.height() + 30)

    def markdown_to_html(self, markdown_text):
        markdown = mistune.create_markdown(
            renderer=mistune.HTMLRenderer(),
            plugins=['strikethrough', 'table', 'url', 'task_lists', 'math', 'ruby', 'spoiler'])
        html_content = self.head_html + markdown(markdown_text)
        return html_content

    def replace_widget(self, notes_cues, current_mode, text):
        if notes_cues == "cues":
            if current_mode == "edit":
                from_widget = self.cues_edit
                to_widget = self.cues_browser
                to_widget.setHtml(self.markdown_to_html(
                    text), baseUrl=self.baseurl)
                self.cues_current_mode = "browser"
                self.cues_current_widget = self.cues_browser
                self.cues_render_edit_button.setText("Edit")
            if current_mode == "browser":
                from_widget = self.cues_browser
                to_widget = self.cues_edit
                to_widget.setText(text)
                self.cues_current_mode = "edit"
                self.cues_current_widget = self.cues_edit
                self.cues_render_edit_button.setText("Render")
        if notes_cues == "notes":
            if current_mode == "edit":
                from_widget = self.notes_edit
                to_widget = self.notes_browser
                to_widget.setHtml(self.markdown_to_html(
                    text), baseUrl=self.baseurl)
                self.notes_current_mode = "browser"
                self.notes_current_widget = self.notes_browser
                self.notes_render_edit_button.setText("Edit")
            if current_mode == "browser":
                from_widget = self.notes_browser
                to_widget = self.notes_edit
                to_widget.setText(text)
                self.notes_current_mode = "edit"
                self.notes_current_widget = self.notes_edit
                self.notes_render_edit_button.setText("Render")

        layout = self.layout()
        layout.replaceWidget(from_widget, to_widget)

        from_widget.hide()
        to_widget.show()


class BlockTitleWidget(QWidget):
    def __init__(self, parent=None):
        super(BlockTitleWidget, self).__init__(parent)

        # set fixed width
        self.setFixedWidth(140)
        self.setStyleSheet("""padding: 1px""")

        # Create QLineEdit
        self.block_title_lineedit = QLineEdit()

        # Create QPushButtons
        insert_icon = QIcon('./icons/add_icon.png')
        self.insert_button = QPushButton(icon=insert_icon)
        self.insert_button.setFixedSize(30, 30)

        remove_icon = QIcon('./icons/remove_icon.png')
        self.remove_button = QPushButton(icon=remove_icon)
        self.remove_button.setFixedSize(30, 30)

        highlight_icon = QIcon('./icons/highlight_icon.png')
        self.highlight_button = QPushButton(icon=highlight_icon)
        self.highlight_button.setFixedSize(30, 30)

        # Create QVBoxLayout
        block_title_layout = QVBoxLayout()
        title_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        # Add widgets to the layouts
        title_layout.addWidget(self.block_title_lineedit)

        button_layout.addWidget(self.insert_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.highlight_button)
        button_layout.setSpacing(3)

        block_title_layout.addLayout(title_layout)
        block_title_layout.addLayout(button_layout)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Set the layout on the application's window
        self.setLayout(block_title_layout)

    def dropEvent(self, event):
        # Get the source item
        source_item = self.itemAt(event.source().pos())

        # Get the destination item
        destination_item = self.itemAt(event.pos())

        # Get the drop index
        drop_index = self.indexAt(event.pos()).row()

        # Check if source item is the same as destination item
        if (source_item is destination_item) or (destination_item is None) or (drop_index > self.count()):
            event.ignore()
        else:
            # Handle the case when source and destination are not the same
            # For example, add source item to destination widget
            destination_item.addWidget(source_item)
            super(BlockTitleWidget, self).dropEvent(event)


class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.blocks = []

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Cornell in Markdown')
        self.setWindowIcon(QIcon("./icons/app_icon.png"))
        self.setGeometry(100, 100, 800, 600)

        self.layout = QGridLayout()

        # toolbar layout
        self.file_name_edit = QLineEdit()
        self.file_name_edit.setText('Untitled')

        create_file_button = QPushButton("Create File")
        create_file_button.clicked.connect(self.create_file)

        open_file_button = QPushButton("Open File")
        open_file_button.clicked.connect(self.open_file)

        export_button = QPushButton("Export File")
        export_button.clicked.connect(self.export_file)

        toolbar_layout = QGridLayout()
        toolbar_layout.addWidget(
            self.file_name_edit, 0, 0)
        toolbar_layout.addWidget(
            create_file_button, 0, 1)
        toolbar_layout.addWidget(
            open_file_button, 0, 2)
        toolbar_layout.addWidget(
            export_button, 0, 3)        

        # outlines visibility
        self.toggle_outlines_checkbox = QRadioButton("Show Outlines")
        self.toggle_outlines_checkbox.setChecked(True)
        self.toggle_outlines_checkbox.clicked.connect(
            self.toggle_outlines)

        # Notes and Cues
        self.notes_cues_list_widget = ListWidget()
        self.notes_cues_list_widget.setFlow(QListView.TopToBottom)

        # Outlines list widget
        self.outlines_list_widget = ListWidget()
        self.outlines_list_widget.setFixedWidth(180)

        # set actions for the outlines
        self.outlines_list_widget.setDragDropMode(
            QAbstractItemView.InternalMove)
        self.outlines_list_widget.setFlow(QListView.TopToBottom)
        self.outlines_list_widget.setWrapping(False)
        self.outlines_list_widget.setResizeMode(QListView.Fixed)
        self.outlines_list_widget.setMovement(QListView.Snap)
        self.outlines_list_widget.setSpacing(10)
        self.outlines_list_widget.setAcceptDrops(True)

        self.outlines_list_widget.dropEvent = self.handle_item_dropped

        # set sync selection
        self.outlines_list_widget.currentRowChanged.connect(
            self.sync_list_item_selection)
        self.notes_cues_list_widget.currentRowChanged.connect(
            self.sync_list_item_selection)

        self.layout.addLayout(
            toolbar_layout, 0, 0)
        self.layout.addWidget(
            self.toggle_outlines_checkbox, 0, 1)
        self.layout.addWidget(
            self.notes_cues_list_widget, 1, 0)
        self.layout.addWidget(
            self.outlines_list_widget, 1, 1)

        # set layout for the whole widget
        self.setLayout(self.layout)
        self.show()

    def insert_block_notes_cues(self, index, new_block):
        # initialize a block_notes_cues_widget
        block_notes_cues_widget = BlockNotesCuesWidget()
        # edit
        # cues_edit
        cues_edit = block_notes_cues_widget.cues_edit
        cues_edit.setPlainText(new_block.cues)

        # notes_edit
        notes_edit = block_notes_cues_widget.notes_edit
        notes_edit.setPlainText(new_block.notes)

        block_notes_cues_widget.auto_resize()

        # browser
        # notes_browser
        notes_browser = block_notes_cues_widget.notes_browser
        notes_browser.setHtml(
            BlockNotesCuesWidget.markdown_to_html(
                block_notes_cues_widget, new_block.notes),
            baseUrl=block_notes_cues_widget.baseurl)
        # cues_browser
        cues_browser = block_notes_cues_widget.cues_browser
        cues_browser.setHtml(
            BlockNotesCuesWidget.markdown_to_html(
                block_notes_cues_widget, new_block.cues),
            baseUrl=block_notes_cues_widget.baseurl)

        # insert item to the listwidget
        item = QListWidgetItem()
        item.setSizeHint(block_notes_cues_widget.sizeHint())

        self.notes_cues_list_widget.insertItem(index, item)
        self.notes_cues_list_widget.setItemWidget(
            item, block_notes_cues_widget)

        # connect
        # cues_edit connect
        cues_edit.textChanged.connect(
            lambda: self.update_block_cues(new_block, cues_edit.toPlainText()))
        cues_edit.textChanged.connect(
            lambda i=item, w=block_notes_cues_widget: self.set_size_hint(i, w))

        # notes_edit connect
        notes_edit.textChanged.connect(
            lambda: self.update_block_notes(new_block, notes_edit.toPlainText()))
        notes_edit.textChanged.connect(
            lambda i=item, w=block_notes_cues_widget: self.set_size_hint(i, w))

        # connect edit/render button
        block_notes_cues_widget.cues_render_edit_button.clicked.connect(
            lambda checked, i=item, w=block_notes_cues_widget:
            (
                w.replace_widget(
                    notes_cues="cues", current_mode=w.cues_current_mode, text=new_block.cues),
                w.auto_resize(),
                self.set_size_hint(i, w)
            )
        )
        block_notes_cues_widget.notes_render_edit_button.clicked.connect(
            lambda checked, i=item, w=block_notes_cues_widget:
            (
                w.replace_widget(
                    notes_cues="notes", current_mode=w.notes_current_mode, text=new_block.notes),
                w.auto_resize(),
                self.set_size_hint(i, w)
            )
        )

    def set_size_hint(self, item, widget):
        item.setSizeHint(
            QSize(widget.width(), widget.height() + 10))

    def insert_block_title(self, index, new_block):
        # title_block
        # initial item
        block_title_widget = BlockTitleWidget()

        # insert item to the listwidget
        item = QListWidgetItem()

        self.outlines_list_widget.insertItem(index, item)
        self.outlines_list_widget.setItemWidget(item, block_title_widget)

        # set initial sizehint for the item
        # item.setSizeHint(block_title_widget.sizeHint())
        item.setSizeHint(QSize(130, 90))

        # set block_title_widget actions
        # title_edit
        title_edit = block_title_widget.block_title_lineedit
        title_edit.textChanged.connect(
            lambda text=title_edit, b=new_block: self.update_block_title(b, text))
        title_edit.setText(new_block.title)

        # insert_button
        insert_button = block_title_widget.insert_button
        insert_button.clicked.connect(
            lambda checked, b=new_block: self.insert_block(
                self.blocks.index(b) + 1, Block())
        )

        # remove_button
        remove_button = block_title_widget.remove_button
        remove_button.clicked.connect(
            lambda checked, b=new_block: self.remove_block(self.blocks.index(b)))

        # highlight_button
        highlight_button = block_title_widget.highlight_button
        highlight_button.clicked.connect(
            lambda checked, b=new_block: self.highlight_block(
                self.blocks.index(b), change_highlight_status=True)
        )

        block_title_widget.show()

    def insert_block(self, index, new_block=Block()):

        self.blocks.insert(index, new_block)
        self.insert_block_notes_cues(index, new_block)
        self.insert_block_title(index, new_block)
        self.update_blocks()

        if new_block.highlighted == 1:
            self.highlight_block(index, change_highlight_status=False)

    def remove_block(self, index):

        if len(self.blocks) > 1:

            # remove from notes
            block_note_cues_item = self.notes_cues_list_widget.takeItem(
                index)
            if block_note_cues_item is not None:
                del block_note_cues_item

            # remove from the outlines
            block_title_item = self.outlines_list_widget.takeItem(index)
            if block_title_item is not None:
                del block_title_item

            self.blocks.pop(index)

            self.update_blocks()

    def handle_item_dropped(self, event):
        # Get the source widget
        source_widget = event.source()
        # Get the original index of the dragged item
        original_index = source_widget.currentRow()
        # Get the drop index
        drop_index = self.outlines_list_widget.indexAt(event.pos()).row()

        # move the blocks
        block = self.blocks[original_index]
        # remove at original place
        self.remove_block(original_index)
        self.insert_block(drop_index, block)

    def highlight_block(self, index, change_highlight_status):
        # Find the index of the block
        block = self.blocks[index]

        if change_highlight_status == True:
            block.highlighted = abs(block.highlighted - 1)
            self.update_blocks()

        notes_cues_item = self.notes_cues_list_widget.item(index)
        title_item = self.outlines_list_widget.item(index)

        if block.highlighted == 1:
            notes_cues_item.setBackground(QColor(223, 199, 75, 76))
            title_item.setBackground(QColor(223, 199, 75, 76))
        else:
            notes_cues_item.setBackground(QColor(255, 255, 255, 75))
            title_item.setBackground(QColor(255, 255, 255, 75))

    def sync_list_item_selection(self, index):

        if self.sender() == self.notes_cues_list_widget:
            self.outlines_list_widget.setCurrentRow(index)
        else:
            self.notes_cues_list_widget.setCurrentRow(index)

    def update_block_title(self, block, new_title):
        block.title = new_title
        self.update_blocks()

    def update_block_cues(self, block, cues_text):
        block.cues = cues_text
        self.update_blocks()

    def update_block_notes(self, block, notes_text):
        block.notes = notes_text
        self.update_blocks()

    def update_block_highlight(self, block, highlighted):
        block.highlighted = highlighted
        self.update_blocks()

    def update_blocks(self):
        blocks_data = [block.to_dict() for block in self.blocks]
        with open(self.full_path, 'w') as file:
            json.dump(blocks_data, file, indent=2)

    def open_folder_dialog(self):
        options = QFileDialog.Options()
        folder_path = QFileDialog.getExistingDirectory(
            self, "QFileDialog.getExistingDirectory()", "", options=options)

        if folder_path:
            return folder_path
        else:
            return None

    def create_file(self):

        # Get the text from the QLineEdit
        filename = self.file_name_edit.text()

        # Open a file dialog to choose the destination folder
        options = QFileDialog.Options()
        folder_path = QFileDialog.getExistingDirectory(
            self, "Choose Destination Folder", "", options=options)

        if folder_path:

            self.close()
            self.__init__()

            self.file_name_edit.setText(filename)
            self.file_name_edit.setReadOnly(True)

            # Append ".json" to the filename to create the full filename with extension
            full_path = os.path.join(folder_path, f"{filename}.json")
            # Perform the file-saving operation (e.g., create an empty JSON file)
            if os.path.exists(full_path):
                QMessageBox.warning(
                    self, "File Exists", f"A file with the name '{filename}' already exists.")
            else:
                with open(full_path, 'w') as file:
                    json.dump({}, file)

                self.full_path = full_path
                self.insert_block(0)

    def open_file(self):
        options = QFileDialog.Options()

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)", options=options)

        if file_path:

            self.close()
            self.__init__()

            file_name, _ = os.path.splitext(os.path.basename(file_path))

            self.full_path = file_path
            self.file_name_edit.setText(file_name)
            self.file_name_edit.setReadOnly(True)

            # Process the selected file
            self.process_json_file(file_path)

    def process_json_file(self, file_path):
        try:
            with open(file_path, 'r') as file:
                notebook = json.load(file)

                self.blocks.clear()
                if notebook is None:
                    notebook.insert(Block().to_dict())

                for i in range(len(notebook)):
                    new_block = Block.from_dict(notebook[i])
                    self.insert_block(i, new_block)

        except Exception as e:
            print(f"Error loading JSON file: {file_path}\nError: {str(e)}")

    def export_file(self):

        file_name = self.file_name_edit.text()

        notes = ""
        cues = ""

        for block in self.blocks:
            notes = notes + block.notes
            cues = cues + block.cues

        try:
            with open(f"{file_name}_notes.md", 'w') as notes_file:
                notes_file.write(notes)
            notes_file.close()

            with open(f"{file_name}_cues.md", 'w') as cues_file:
                cues_file.write(cues)
            cues_file.close()

            file_exported_message_box = QMessageBox()
            file_exported_message_box.setWindowTitle("File Exported")
            file_exported_message_box.setText(
                f"{file_name}_notes.md and {file_name}_cues.md files are successfully exported.")
            file_exported_message_box.setObjectName(
                "file_exported_message_box")
            file_exported_message_box.exec_()

        except:
            QMessageBox.warning(self, "File Export Error",
                                "The Markdown files can not be exported.")

    def toggle_outlines(self):
        
        visible = not self.outlines_list_widget.isVisible()
        self.outlines_list_widget.setVisible(visible)

        if visible == False:
            self.layout.removeWidget(self.notes_cues_list_widget)
            self.layout.addWidget(self.notes_cues_list_widget, 1, 0, 1, 2)
        
        else: 
            self.layout.removeWidget(self.notes_cues_list_widget)
            self.layout.addWidget(self.notes_cues_list_widget, 1, 0, 1, 1)


if __name__ == '__main__':

    with open("AppStyling.css", "r") as f:
        _style = f.read()

    app = QApplication(sys.argv)
    app.setStyleSheet(_style)
    ex = MyApp()
    sys.exit(app.exec_())
