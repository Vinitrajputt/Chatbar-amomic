
import sys
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QConicalGradient

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

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = QWidget()
    window.setFixedSize(400, 200)
    
    edge_widget = EdgeLightingWidget(window)
    edge_widget.setGeometry(window.rect())
    
    window.setStyleSheet("background-color: #1A1A1A;")
    
    window.show()
    edge_widget.start_animation()
    
    sys.exit(app.exec_())
