from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTextEdit, QScrollArea, QFrame
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt
import threading
import keyboard
from tasks.task_manager import change_visibility, handle_return_pressed

def create_window():
    window = QWidget()
    layout = QVBoxLayout()
    width = 720

    # Create a horizontal layout to hold the search bar and image button
    search_layout = QHBoxLayout()

    search_bar = QLineEdit()
    search_bar.setPlaceholderText("Type here...")

    # Set a maximum width for the search bar
    search_bar.setMaximumWidth(680)  # Adjust the maximum width as needed

    image_button = QPushButton()
    image_button.setIcon(QIcon("image.png"))  # Set the icon for the button
    image_button.setIconSize(QSize(20, 20))  # Set the size of the icon
    image_button.setFixedSize(30, 30)  # Set a fixed size for the button

    search_layout.addWidget(search_bar)
    search_layout.addWidget(image_button)

    response_label = QTextEdit()
    response_label.setFixedWidth(width)
    response_label.setWordWrapMode(True)
    response_label.setFrameStyle(QFrame.NoFrame)
    response_label.setReadOnly(True)
    response_label.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    response_label.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    scroll_area = QScrollArea()
    scroll_area.setWidget(response_label)
    scroll_area.setWidgetResizable(True)
    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll_area.setStyleSheet("border: none; QTextEdit { scrollbar: no; }")

    layout.addLayout(search_layout)  # Add the search layout instead of just the search bar
    layout.addWidget(scroll_area)

    response_label.setVisible(False)
    scroll_area.setVisible(False)

    window.setLayout(layout)

    # Connect the returnPressed signal to the handler function
    search_bar.returnPressed.connect(lambda: handle_return_pressed(search_bar, response_label, scroll_area, window))

    return window

def hotkey_thread_o(window):
    keyboard.add_hotkey('ctrl+space', lambda: change_visibility(window))
    keyboard.wait('esc')
