import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLineEdit, 
                             QTextEdit, QPushButton, QGraphicsDropShadowEffect,
                             QGraphicsOpacityEffect)
from PyQt5.QtCore import (Qt, QPropertyAnimation, QEasingCurve, QTimer, 
                          QSequentialAnimationGroup, pyqtProperty, QRect)
from PyQt5.QtGui import QFont, QColor, QIcon, QPainter, QLinearGradient, QTextDocument

# from .edge_lighting_widget import EdgeLightingWidget

class EdgeLightingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_angle)
        self.is_animating = False

    def start_animation(self):
        if not self.is_animating:
            self.is_animating = True
            self.timer.start(16)  # ~60 FPS
            self.update()

    def stop_animation(self):
        if self.is_animating:
            self.is_animating = False
            self.timer.stop()
            self.update()

    def update_angle(self):
        self.angle = (self.angle + 2) % 360
        self.update()

    def paintEvent(self, event):
        if not self.is_animating:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        from PyQt5.QtGui import QConicalGradient
        gradient = QConicalGradient(rect.center(), self.angle)
        gradient.setColorAt(0, QColor(255, 255, 255, 255))
        gradient.setColorAt(0.25, QColor(255, 255, 255, 0))
        gradient.setColorAt(0.5, QColor(255, 255, 255, 0))
        gradient.setColorAt(0.75, QColor(255, 255, 255, 0))
        gradient.setColorAt(1.0, QColor(255, 255, 255, 255))

        from PyQt5.QtGui import QPen, QBrush, QPainterPath
        from PyQt5.QtCore import QRectF

        pen = QPen()
        pen.setBrush(QBrush(gradient))
        pen.setWidth(2) # Controls the line thickness
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # Create a path with rounded corners, slightly inset
        path_rect = QRectF(rect).adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(path_rect, 11, 11) # Adjust radius to match inset
        
        painter.drawPath(path)

class ShimmerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._shimmer_pos = 0
        self.animation = QPropertyAnimation(self, b"shimmer_pos")
        self.animation.setDuration(1500)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setLoopCount(-1)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)

    @pyqtProperty(float)
    def shimmer_pos(self):
        return self._shimmer_pos

    @shimmer_pos.setter
    def shimmer_pos(self, value):
        self._shimmer_pos = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient = QLinearGradient(self.rect().topLeft(), self.rect().bottomRight())
        gradient.setColorAt(max(0, self._shimmer_pos - 0.2), QColor(255, 255, 255, 0))
        gradient.setColorAt(self._shimmer_pos, QColor(255, 255, 255, 60))
        gradient.setColorAt(min(1, self._shimmer_pos + 0.2), QColor(255, 255, 255, 0))

        from PyQt5.QtGui import QPainterPath
        from PyQt5.QtCore import QRectF
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12, 12)
        painter.fillPath(path, gradient)

    def start(self):
        self.animation.start()

    def stop(self):
        self.animation.stop()
        self.hide()

class ChatBarWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # Constants for better sizing control - must be defined before setup_ui()
        self.BASE_HEIGHT = 100
        self.MIN_RESPONSE_HEIGHT = 30
        self.MAX_RESPONSE_HEIGHT = 400
        self.WINDOW_WIDTH = 800
        self.MARGIN_ADJUSTMENT = 20
        
        # Initialize other attributes
        self.animation = None
        self.thinking_animation_timer = QTimer(self)
        self.thinking_animation_timer.timeout.connect(self.update_thinking_animation)
        self.thinking_dots = 0
        
        # Setup UI after all attributes are initialized
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("ChatBar")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Container
        self.container = QWidget()
        self.container.setObjectName("container")
        self.main_layout.addWidget(self.container)
        
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(15, 15, 15, 15)
        self.container_layout.setSpacing(10)  # Set consistent spacing

        # Shadow effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(25)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(5)
        self.shadow.setColor(QColor(0, 0, 0, 160))
        self.container.setGraphicsEffect(self.shadow)

        # Edge lighting
        self.edge_lighting = EdgeLightingWidget(self.container)
        self.edge_lighting.hide()

        # Shimmer effect
        self.shimmer = ShimmerWidget(self.container)
        self.shimmer.hide()

        # Input bar
        self.input_bar = QLineEdit(self)
        self.input_bar.setPlaceholderText("Ask me anything...")
        self.input_bar.textChanged.connect(self.handle_text_changed)
        self.input_bar.setFixedHeight(50)  # Fixed height for consistency
        
        # Response view with proper text wrapping
        self.response_view = QTextEdit(self)
        self.response_view.setReadOnly(True)
        self.response_view.setVisible(False)
        self.response_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.response_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.response_view.setWordWrapMode(True)  # Enable word wrapping
        self.response_view.setLineWrapMode(QTextEdit.WidgetWidth)  # Wrap at widget width
        self.response_view.textChanged.connect(self.on_text_changed)
        
        # Set initial minimum size
        self.response_view.setMinimumHeight(self.MIN_RESPONSE_HEIGHT)

        # Copy button
        self.copy_button = QPushButton(self)
        # self.copy_button.setIcon(QIcon("copy_icon.svg"))
        self.copy_button.setText("Copy")  # Fallback text
        self.copy_button.setVisible(False)
        self.copy_button.setCursor(Qt.PointingHandCursor)
        self.copy_button.setFixedSize(60, 30)

        self.container_layout.addWidget(self.input_bar)
        self.container_layout.addWidget(self.response_view)
        self.container_layout.addWidget(self.copy_button, 0, Qt.AlignRight)

        self.load_stylesheet()
        self.setFixedWidth(self.WINDOW_WIDTH)
        self.setFixedHeight(self.BASE_HEIGHT)

    @pyqtProperty(int)
    def windowHeight(self):
        return self.height()

    @windowHeight.setter
    def windowHeight(self, height):
        self.setFixedHeight(height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.edge_lighting.setGeometry(self.container.rect())
        self.shimmer.setGeometry(self.container.rect())
        # Trigger height adjustment when window is resized
        if self.response_view.isVisible():
            QTimer.singleShot(0, self.adjust_height)

    def handle_text_changed(self, text):
        if text:
            self.edge_lighting.start_animation()
            self.edge_lighting.show()
        else:
            self.edge_lighting.stop_animation()
            self.edge_lighting.hide()

    def animate_height(self, new_height):
        if self.animation and self.animation.state() == QPropertyAnimation.Running:
            self.animation.stop()
        
        current_height = self.height()
        if current_height == new_height:
            return
            
        self.animation = QPropertyAnimation(self, b"windowHeight")
        self.animation.setDuration(50)
        self.animation.setStartValue(current_height)
        self.animation.setEndValue(new_height)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.start()

    def calculate_text_height(self, text=""):
        """Calculate the exact height needed for the text"""
        if not text and not self.response_view.toPlainText():
            return self.MIN_RESPONSE_HEIGHT
            
        # Create a temporary document to measure text height
        doc = QTextDocument()
        if text:
            doc.setPlainText(text)
        else:
            doc.setHtml(self.response_view.toHtml())
        
        # Set the same width as the response view (accounting for margins)
        content_width = (self.response_view.width() - 
                        self.response_view.contentsMargins().left() - 
                        self.response_view.contentsMargins().right() - 20)  # Extra margin for safety
        
        if content_width > 0:
            doc.setTextWidth(content_width)
        
        # Get the height and add some padding
        text_height = doc.size().height()
        margins = (self.response_view.contentsMargins().top() + 
                  self.response_view.contentsMargins().bottom())
        
        total_height = text_height + margins  # Extra padding
        
        # Ensure minimum and maximum constraints
        return max(self.MIN_RESPONSE_HEIGHT, min(total_height, self.MAX_RESPONSE_HEIGHT))

    def show_response(self, text):
        self.edge_lighting.stop_animation()
        self.edge_lighting.hide()

        if text == "Thinking...":
            self.response_view.setText("Thinking")
            self.thinking_animation_timer.start(400)
            self.copy_button.setDisabled(True)
            self.shimmer.start()
            self.shimmer.show()
        else:
            self.thinking_animation_timer.stop()
            self.response_view.setMarkdown(text)
            self.copy_button.setDisabled(False)
            self.shimmer.stop()
        
        self.response_view.setVisible(True)
        self.copy_button.setVisible(text != "Thinking...")
        
        # Delay height adjustment to ensure proper rendering
        QTimer.singleShot(10, self.adjust_height)

    def append_chunk(self, chunk):
        if self.thinking_animation_timer.isActive():
            self.thinking_animation_timer.stop()
            self.response_view.clear()
            self.shimmer.stop()
        
        # Use insertPlainText to maintain cursor position
        cursor = self.response_view.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(chunk)
        self.response_view.setTextCursor(cursor)
        
        # Adjust height after adding content
        QTimer.singleShot(10, self.adjust_height)

    def stream_finished(self):
        self.copy_button.setDisabled(False)
        # Convert to markdown after streaming is complete
        plain_text = self.response_view.toPlainText()
        self.response_view.setMarkdown(plain_text)
        # Final height adjustment after markdown conversion
        QTimer.singleShot(50, self.adjust_height)

    def hide_response(self):
        self.response_view.setVisible(False)
        self.copy_button.setVisible(False)
        self.input_bar.clear()
        self.response_view.clear()
        self.adjust_height()

    def on_text_changed(self):
        """Handle text changes in response view"""
        QTimer.singleShot(10, self.adjust_height)

    def adjust_height_immediate(self):
        """Immediate height adjustment without animation for fast text streaming"""
        target_height = self.BASE_HEIGHT
        
        if self.response_view.isVisible():
            # Calculate required height for the text content
            required_height = self.calculate_text_height()
            self.response_view.setFixedHeight(int(required_height))
            
            # Calculate total window height
            input_height = self.input_bar.height()
            button_height = self.copy_button.height() if self.copy_button.isVisible() else 0
            
            container_margins = (self.container_layout.contentsMargins().top() + 
                               self.container_layout.contentsMargins().bottom())
            main_margins = (self.main_layout.contentsMargins().top() + 
                          self.main_layout.contentsMargins().bottom())
            
            # Account for spacing between elements
            spacing = self.container_layout.spacing() * 2  # Two spaces (input-response, response-button)
            if not self.copy_button.isVisible():
                spacing = self.container_layout.spacing()
            
            total_content_height = (input_height + required_height + button_height + 
                                  container_margins + main_margins + spacing)
            
            target_height = int(total_content_height) + self.MARGIN_ADJUSTMENT
        else:
            # Reset response view height when hidden
            self.response_view.setFixedHeight(1)

        # Set height immediately without animation
        if abs(self.height() - target_height) > 1:
            self.setFixedHeight(target_height)

    def adjust_height(self):
        """Refined height adjustment with proper text measurement"""
        target_height = self.BASE_HEIGHT
        
        if self.response_view.isVisible():
            # Calculate required height for the text content
            required_height = self.calculate_text_height()
            self.response_view.setFixedHeight(int(required_height))
            
            # Calculate total window height
            input_height = self.input_bar.height()
            button_height = self.copy_button.height() if self.copy_button.isVisible() else 0
            
            container_margins = (self.container_layout.contentsMargins().top() + 
                               self.container_layout.contentsMargins().bottom())
            main_margins = (self.main_layout.contentsMargins().top() + 
                          self.main_layout.contentsMargins().bottom())
            
            # Account for spacing between elements
            spacing = self.container_layout.spacing() * 2  # Two spaces (input-response, response-button)
            if not self.copy_button.isVisible():
                spacing = self.container_layout.spacing()
            
            total_content_height = (input_height + required_height + button_height + 
                                  container_margins + main_margins + spacing)
            
            target_height = int(total_content_height) + self.MARGIN_ADJUSTMENT
        else:
            # Reset response view height when hidden
            self.response_view.setFixedHeight(1)

        # Only animate if height actually needs to change
        if abs(self.height() - target_height) > 1:  # Small threshold to avoid unnecessary animations
            self.animate_height(target_height)

    def update_thinking_animation(self):
        self.thinking_dots = (self.thinking_dots + 1) % 4
        self.response_view.setText("Thinking" + "." * self.thinking_dots)

    def event(self, event):
        if event.type() == event.WindowDeactivate:
            self.hide()
            self.hide_response()
        return super().event(event)

    def showEvent(self, event):
        """Handle show event to ensure proper sizing"""
        super().showEvent(event)
        if self.response_view.isVisible():
            QTimer.singleShot(50, self.adjust_height)

    def load_stylesheet(self):
        try:
            with open("ui/styles.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Stylesheet not found, using default styling.")
            # Basic fallback styling
            self.setStyleSheet("""
                QWidget#container {
                    background-color: rgba(45, 45, 45, 240);
                    border-radius: 12px;
                }
                QLineEdit {
                    background-color: rgba(60, 60, 60, 200);
                    border: 2px solid rgba(100, 100, 100, 100);
                    border-radius: 8px;
                    padding: 8px;
                    font-size: 14px;
                    color: white;
                }
                QTextEdit {
                    background-color: rgba(50, 50, 50, 200);
                    border: 1px solid rgba(100, 100, 100, 100);
                    border-radius: 8px;
                    padding: 8px;
                    font-size: 14px;
                    color: white;
                }
                QPushButton {
                    background-color: rgba(70, 130, 180, 200);
                    border: none;
                    border-radius: 6px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(70, 130, 180, 255);
                }
            """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatBarWindow()
    window.show()
    
    # Example usage:
    QTimer.singleShot(1000, lambda: window.show_response("Thinking..."))
    QTimer.singleShot(3000, lambda: window.show_response("This is a **markdown** example with `code`. Here's a longer text that should wrap properly within the widget bounds and demonstrate the improved sizing behavior. Let's see how it handles multiple lines of content with proper text wrapping."))
    
    sys.exit(app.exec_())