"""
Region selector: semi-transparent overlay, no background screenshot.
Underlying screen (including video) stays live and visible.
"""
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, QPoint, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QCursor, QFont


class RegionSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.result: tuple | None = None
        self._g_start = QPoint()
        self._g_end   = QPoint()
        self._dragging = False

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

    # ── painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._dragging:
            p.fillRect(self.rect(), QColor(255, 180, 200, 45))
        else:
            lp1 = self._g_start - self.mapToGlobal(QPoint(0, 0))
            lp2 = self._g_end   - self.mapToGlobal(QPoint(0, 0))
            sel = QRect(lp1, lp2).normalized()

            # Pink-tinted outside, clear inside
            p.fillRect(self.rect(), QColor(240, 100, 140, 80))
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            p.fillRect(sel, QColor(0, 0, 0, 0))
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            # Rose border
            p.setPen(QPen(QColor(236, 100, 140), 2))
            p.drawRect(sel)

            # Corner dots
            dot_c = QColor(236, 100, 140)
            for cx, cy in [(sel.left(), sel.top()), (sel.right(), sel.top()),
                           (sel.left(), sel.bottom()), (sel.right(), sel.bottom())]:
                p.setBrush(dot_c)
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(cx - 4, cy - 4, 8, 8)

            # Size label
            gsel = QRect(self._g_start, self._g_end).normalized()
            p.setPen(QColor(255, 255, 255))
            p.setFont(QFont("PingFang SC", 11))
            ly = sel.top() - 8 if sel.top() > 24 else sel.bottom() + 18
            p.drawText(sel.left() + 4, ly,
                       f" {gsel.width()} × {gsel.height()} ")

        # Instruction
        p.setPen(QColor(255, 220, 230))
        p.setFont(QFont("PingFang SC", 15))
        p.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            "\n🌸  拖动选择翻译区域    ·    ESC 取消",
        )

    # ── mouse events ──────────────────────────────────────────────────────────

    def mousePressEvent(self, e):
        self._g_start = e.globalPosition().toPoint()
        self._g_end   = self._g_start
        self._dragging = True

    def mouseMoveEvent(self, e):
        self._g_end = e.globalPosition().toPoint()
        self.update()

    def mouseReleaseEvent(self, e):
        self._g_end = e.globalPosition().toPoint()
        sel = QRect(self._g_start, self._g_end).normalized()
        self.result = (sel.x(), sel.y(), sel.width(), sel.height())
        self.close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.result = None
            self.close()

    # ── public ────────────────────────────────────────────────────────────────

    def run(self) -> tuple | None:
        self.show()
        self.raise_()
        self.activateWindow()
        app = QApplication.instance()
        from PyQt6.QtCore import QThread
        while self.isVisible():
            app.processEvents()
            QThread.msleep(10)
        return self.result
