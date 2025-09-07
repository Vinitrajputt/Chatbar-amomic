
import sys
import ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QThread, pyqtSlot, QTimer

from ui.ui_manager_chat import ChatBarWindow
from api.client import LocalAIClient


class ChatWorker(QObject):
    """Handles API requests in a separate thread."""

    new_chunk = pyqtSignal(str)
    stream_finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.client = LocalAIClient()

    @pyqtSlot(str)
    def process_text(self, text):
        """Sends text to the server and emits the response chunks."""
        try:
            for chunk in self.client.get_streaming_response(text):
                self.new_chunk.emit(chunk)
            self.stream_finished.emit()
        except Exception as e:
            self.error.emit(f"An unexpected error occurred: {e}")


class ChatApp(QApplication):
    """Main application class."""

    send_request = pyqtSignal(str)

    def __init__(self, sys_argv):
        super(ChatApp, self).__init__(sys_argv)

        self.chat_window = ChatBarWindow()

        # Set up worker thread for network requests
        self.worker_thread = QThread()
        self.chat_worker = ChatWorker()
        self.chat_worker.moveToThread(self.worker_thread)

        # Connect signals and slots
        self.chat_window.input_bar.returnPressed.connect(self.send_message)
        self.chat_window.copy_button.clicked.connect(self.copy_to_clipboard)
        self.send_request.connect(self.chat_worker.process_text)
        self.chat_worker.new_chunk.connect(self.chat_window.append_chunk)
        self.chat_worker.stream_finished.connect(self.handle_stream_finished)
        self.chat_worker.error.connect(self.handle_error)

        self.worker_thread.start()

        # Hotkey setup
        self.hotkey_timer = QTimer(self)
        self.hotkey_timer.timeout.connect(self.check_hotkey)
        self.hotkey_timer.start(100)  # Check every 100ms
        self.hotkey_pressed = False

    def check_hotkey(self):
        """Checks if the hotkey (Ctrl+Space) is pressed."""
        ctrl_pressed = ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000
        space_pressed = ctypes.windll.user32.GetAsyncKeyState(0x20) & 0x8000

        if ctrl_pressed and space_pressed:
            if not self.hotkey_pressed:
                self.toggle_visibility()
                self.hotkey_pressed = True
        else:
            self.hotkey_pressed = False

    def send_message(self):
        """Handles sending a message from the input bar."""
        message = self.chat_window.input_bar.text()
        if message:
            self.chat_window.input_bar.setDisabled(True)
            self.chat_window.show_response("Thinking...")
            self.send_request.emit(message)

    def handle_stream_finished(self):
        """Handles the end of a response stream."""
        self.chat_window.stream_finished()
        self.chat_window.input_bar.setDisabled(False)
        self.chat_window.input_bar.clear()
        self.chat_window.input_bar.setFocus()

    def handle_error(self, error_message):
        """Handles an error from the worker."""
        self.chat_window.show_response(error_message)
        self.chat_window.input_bar.setDisabled(False)

    def copy_to_clipboard(self):
        """Copies the response text to the clipboard."""
        self.clipboard().setText(self.chat_window.response_view.toPlainText())

    def toggle_visibility(self):
        """Toggles the visibility of the chat window."""
        if self.chat_window.isVisible():
            self.chat_window.hide()
            self.chat_window.hide_response()
        else:
            self.chat_window.show()
            self.chat_window.activateWindow()
            self.chat_window.raise_()
            QTimer.singleShot(0, self.chat_window.input_bar.setFocus)


def main():
    """Initializes and runs the application."""
    app = ChatApp(sys.argv) 
    app.chat_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
