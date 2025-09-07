import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QThread, pyqtSlot, QTimer
from PyQt5.QtGui import QWindow
from pynput import keyboard

# Windows-specific imports for focus handling
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    
    # Windows API constants
    SW_RESTORE = 9
    HWND_TOPMOST = -1
    HWND_NOTOPMOST = -2
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_SHOWWINDOW = 0x0040

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
    toggle_visibility_signal = pyqtSignal()

    def __init__(self, sys_argv):
        super(ChatApp, self).__init__(sys_argv)

        self.chat_window = ChatBarWindow()
        
        # Store reference to app in chat window for focus callbacks
        self.chat_window.app_reference = self

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
        self.toggle_visibility_signal.connect(self.toggle_visibility)

        self.worker_thread.start()

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

    def force_window_focus_windows(self):
        """Force window focus on Windows using Win32 API."""
        if sys.platform != "win32":
            return

        try:
            # Get window handle
            hwnd = int(self.chat_window.winId())
            
            # Get current foreground window
            foreground_hwnd = ctypes.windll.user32.GetForegroundWindow()
            
            # Get thread IDs
            current_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
            foreground_thread_id = ctypes.windll.user32.GetWindowThreadProcessId(foreground_hwnd, None)
            
            # Attach input to foreground thread if different
            if foreground_thread_id != current_thread_id:
                ctypes.windll.user32.AttachThreadInput(foreground_thread_id, current_thread_id, True)
            
            # Show and restore window
            ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
            
            # Set window position to topmost temporarily, then remove topmost
            ctypes.windll.user32.SetWindowPos(
                hwnd, HWND_TOPMOST, 0, 0, 0, 0, 
                SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
            )
            ctypes.windll.user32.SetWindowPos(
                hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
            )
            
            # Set foreground window
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            
            # Detach thread input if we attached it
            if foreground_thread_id != current_thread_id:
                ctypes.windll.user32.AttachThreadInput(foreground_thread_id, current_thread_id, False)
                
        except Exception as e:
            print(f"Failed to force focus: {e}")

    def toggle_visibility(self):
        """Toggles the visibility of the chat window with proper focus handling."""
        if self.chat_window.isVisible():
            self.chat_window.hide()
            self.chat_window.hide_response()
        else:
            # Show window first
            self.chat_window.show()
            
            # Use platform-specific focus methods
            if sys.platform == "win32":
                # Windows: Use Win32 API for reliable focus
                self.force_window_focus_windows()
            else:
                # Other platforms: Use Qt methods
                self.chat_window.activateWindow()
                self.chat_window.raise_()
            
            # Set focus to input bar with multiple attempts
            self.focus_input_bar()

    def focus_input_bar(self):
        """Ensure input bar gets focus with multiple attempts."""
        def set_focus_attempt():
            if self.chat_window.isVisible():
                self.chat_window.input_bar.setFocus()
                self.chat_window.input_bar.activateWindow()
                
                # Force cursor to end of text (in case there's existing text)
                self.chat_window.input_bar.setCursorPosition(
                    len(self.chat_window.input_bar.text())
                )
        
        # Multiple focus attempts with increasing delays
        QTimer.singleShot(0, set_focus_attempt)
        QTimer.singleShot(50, set_focus_attempt)
        QTimer.singleShot(100, set_focus_attempt)
        QTimer.singleShot(200, set_focus_attempt)

def main():
    """Initializes and runs the application."""
    app = ChatApp(sys.argv)

    # --- Global Hotkey Setup using pynput ---
    def on_activate():
        app.toggle_visibility_signal.emit()

    def for_canonical(f):
        return lambda k: f(listener.canonical(k))

    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse('<ctrl>+<space>'),
        on_activate)

    listener = keyboard.Listener(
        on_press=for_canonical(hotkey.press),
        on_release=for_canonical(hotkey.release))
    listener.start()
    # --- End of Hotkey Setup ---

    # Show window initially to "warm up" the focus system, then hide it
    app.chat_window.show()
    QTimer.singleShot(100, app.chat_window.hide)  # Hide after 100ms
    
    # Reset first_activation flag after warmup
    QTimer.singleShot(200, lambda: setattr(app, 'first_activation', True))
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

