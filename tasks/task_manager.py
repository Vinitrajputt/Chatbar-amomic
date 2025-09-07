from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import QTimer

def change_visibility(window):
    if window.isVisible():
        window.hide()
    else:
        window.show()
        window.activateWindow()
        window.raise_()
        window.setFocus()
        search_bar = window.findChild(QLineEdit)
        search_bar.setFocus()

def handle_return_pressed(search_bar, response_label, scroll_area, window):
    # Get the text from the search bar
        text = search_bar.text()
        # Clear the text from the search bar
        search_bar.clear()
        # Set the text for the response label
        response_label.setText(text)
        # Show the response label and scroll area
        response_label.setVisible(True)
        scroll_area.setVisible(True)
        # Set focus on the response label
        response_label.setFocus()
        # Set the cursor position to the end of the response label
        response_label.moveCursor(response_label.textCursor().End)
        # Hide the window after 5 seconds
        QTimer.singleShot(5000, lambda: change_visibility(window))
