"""
Translation overlay — full-screen transparent window.
Click INSIDE the card  → emit retranslate signal (start new selection)
Click OUTSIDE the card → dismiss
"""
import os
import threading
from datetime import date as _date

from PyQt6.QtWidgets import (QWidget, QFrame, QVBoxLayout, QLabel,
                              QApplication, QHBoxLayout, QLineEdit)
from PyQt6.QtCore import Qt, QTimer, QRect, pyqtSignal
from PyQt6.QtGui import (QPainter, QColor, QFont, QPainterPath,
                          QLinearGradient, QPen)

# ── palette ────────────────────────────────────────────────────────────────────
BG_TOP  = QColor(255, 240, 245, 238)
BG_BOT  = QColor(255, 220, 232, 238)
BORDER  = QColor(255, 182, 193, 180)
ACCENT  = QColor(236, 100, 140)
DIM     = QColor(180, 120, 140)
MAIN    = QColor(70,  25,  50)
ERR     = QColor(200, 60,  80)
HINT_IN = QColor(236, 100, 140)
BTN_BG  = QColor(255, 200, 215, 200)

MIN_W           = 360
AUTO_DISMISS_MS = 40_000

def _resolve_vocab_file() -> str:
    """Return the vocab file path: config.py > env var > ~/Documents default."""
    try:
        from config import VOCAB_FILE as _cf
        if _cf and _cf.strip():
            return _cf.strip()
    except ImportError:
        pass
    env = os.environ.get("VOCAB_FILE", "").strip()
    if env:
        return env
    return os.path.expanduser("~/Documents/生词本.md")

VOCAB_FILE = _resolve_vocab_file()

_BTN_RETRY = (
    "color: rgba(236,100,140,255);"
    "background: rgba(255,200,215,180); border-radius: 8px;"
    "padding: 3px 10px; font-size: 11px; font-weight: 600;"
    "font-family: 'PingFang SC', sans-serif;"
)
_BTN_COPY = (
    "color: rgba(90,150,200,255);"
    "background: rgba(210,230,255,180); border-radius: 8px;"
    "padding: 3px 10px; font-size: 11px; font-weight: 600;"
    "font-family: 'PingFang SC', sans-serif;"
)
_BTN_COPIED = (
    "color: rgba(60,160,90,255);"
    "background: rgba(210,245,220,180); border-radius: 8px;"
    "padding: 3px 10px; font-size: 11px; font-weight: 600;"
    "font-family: 'PingFang SC', sans-serif;"
)
_BTN_VOCAB = (
    "color: rgba(150,100,200,255);"
    "background: rgba(230,215,255,180); border-radius: 8px;"
    "padding: 3px 10px; font-size: 11px; font-weight: 600;"
    "font-family: 'PingFang SC', sans-serif;"
)
_BTN_VOCAB_ON = (
    "color: rgba(255,255,255,255);"
    "background: rgba(150,100,200,220); border-radius: 8px;"
    "padding: 3px 10px; font-size: 11px; font-weight: 600;"
    "font-family: 'PingFang SC', sans-serif;"
)


# ── pink card (child widget) ───────────────────────────────────────────────────

class _Card(QFrame):
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)

        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, BG_TOP)
        g.setColorAt(1, BG_BOT)
        p.fillPath(path, g)

        p.setPen(QPen(BORDER, 1))
        p.drawPath(path)

        # top accent stripe
        stripe = QPainterPath()
        stripe.addRoundedRect(1, 1, self.width() - 2, 3, 2, 2)
        p.fillPath(stripe, ACCENT)


# ── clickable label ────────────────────────────────────────────────────────────

class _ClickLabel(QLabel):
    """QLabel that emits `clicked` and stops event propagation to the overlay."""
    clicked = pyqtSignal()

    def mousePressEvent(self, e):
        self.clicked.emit()
        e.accept()   # don't bubble up to TranslationOverlay.mousePressEvent


# ── main overlay ───────────────────────────────────────────────────────────────

class TranslationOverlay(QWidget):
    retranslate    = pyqtSignal()        # user wants a new selection
    _vocab_sig     = pyqtSignal(str, str)  # (word, definition) — from bg thread
    _vocab_err_sig = pyqtSignal(str)       # error message — from bg thread

    def __init__(self, x: int, y: int, w: int, h: int, api_key: str = ""):
        super().__init__()
        self._sx, self._sy, self._sw, self._sh = x, y, w, h
        self._api_key = api_key
        self._can_retranslate = False
        self._vocab_row   = None   # set in show_result
        self._vocab_input = None
        self._vocab_btn   = None
        self._vocab_status = None

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # Card container
        self._card = _Card(self)
        lay = QVBoxLayout(self._card)
        lay.setContentsMargins(16, 16, 16, 10)
        lay.setSpacing(7)
        self._lay = lay

        self._vocab_sig.connect(self._on_vocab_done)
        self._vocab_err_sig.connect(self._on_vocab_err)

        self._place(80)

    # ── positioning ────────────────────────────────────────────────────────────

    def _place(self, h: int):
        sw  = self.width()
        sh  = self.height()
        ow  = min(max(self._sw, MIN_W), sw - 20)

        ox = max(10, min(self._sx, sw - ow - 10))

        SAFE_TOP = 38
        SAFE_BOT = 12

        below = self._sy + self._sh + 10
        above = self._sy - h - 10

        if below + h <= sh - SAFE_BOT:
            oy = below
        elif above >= SAFE_TOP:
            oy = above
        else:
            if (sh - below) > (self._sy - SAFE_TOP):
                oy = below
            else:
                oy = above

        oy = max(SAFE_TOP, min(oy, sh - h - SAFE_BOT))
        self._card.setGeometry(ox, oy, ow, h)

    def _resize(self):
        sw = self.width()
        ow = min(max(self._sw, MIN_W), sw - 20)
        self._card.resize(ow, self._card.height() or 80)
        self._lay.activate()
        QApplication.instance().processEvents()
        QApplication.instance().processEvents()
        self._card.adjustSize()
        h = max(self._card.height() + 8, 80)
        self._place(h)
        self._card.update()

    # ── helpers ────────────────────────────────────────────────────────────────

    def _clear(self):
        self._vocab_row   = None
        self._vocab_input = None
        self._vocab_btn   = None
        self._vocab_status = None
        while self._lay.count():
            item = self._lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _lbl(self, text, size, color: QColor,
             bold=False, wrap=True, align=Qt.AlignmentFlag.AlignLeft) -> QLabel:
        lb = QLabel(text)
        w  = "600" if bold else "400"
        lb.setStyleSheet(
            f"color: rgba({color.red()},{color.green()},{color.blue()},{color.alpha()});"
            f"background: transparent; font-size: {size}px; font-weight: {w};"
            f"font-family: 'PingFang SC', 'Helvetica Neue', sans-serif;"
        )
        lb.setWordWrap(wrap)
        lb.setAlignment(align)
        return lb

    def _div(self):
        d = QFrame()
        d.setFrameShape(QFrame.Shape.HLine)
        d.setFixedHeight(1)
        d.setStyleSheet("background: rgba(255,182,193,160); border: none;")
        return d

    # ── button actions ─────────────────────────────────────────────────────────

    def _on_retranslate_click(self):
        self.hide()
        self.retranslate.emit()
        self.close()

    def _copy_feedback(self, btn: _ClickLabel, text: str):
        QApplication.clipboard().setText(text)
        btn.setText("✓  已复制")
        btn.setStyleSheet(_BTN_COPIED)

        def _reset():
            try:
                btn.setText("📋  复制")
                btn.setStyleSheet(_BTN_COPY)
            except RuntimeError:
                pass

        QTimer.singleShot(1500, _reset)

    # ── vocab input ────────────────────────────────────────────────────────────

    def _toggle_vocab(self):
        if self._vocab_row is None:
            return
        if self._vocab_row.isHidden():
            self._vocab_row.show()
            self._vocab_btn.setStyleSheet(_BTN_VOCAB_ON)
            self._resize()
            self._vocab_input.setFocus()
        else:
            self._vocab_row.hide()
            self._vocab_btn.setStyleSheet(_BTN_VOCAB)
            self._resize()

    def _submit_vocab(self):
        if self._vocab_input is None:
            return
        word = self._vocab_input.text().strip()
        if not word:
            return
        self._vocab_status.setText("查询中…")
        self._vocab_input.setEnabled(False)
        threading.Thread(
            target=self._vocab_worker, args=(word,), daemon=True
        ).start()

    def _vocab_worker(self, word: str):
        try:
            from translator import lookup_word
            definition = lookup_word(word, self._api_key)
            self._vocab_sig.emit(word, definition)
        except Exception as e:
            self._vocab_err_sig.emit(str(e))

    def _on_vocab_done(self, word: str, definition: str):
        try:
            self._write_vocab(word, definition)
            if self._vocab_input:
                self._vocab_input.clear()
                self._vocab_input.setEnabled(True)
            if self._vocab_status:
                self._vocab_status.setText("✓ 已记录")
                QTimer.singleShot(2000, lambda: self._safe_set_status(""))
        except RuntimeError:
            pass

    def _on_vocab_err(self, msg: str):
        try:
            if self._vocab_input:
                self._vocab_input.setEnabled(True)
            if self._vocab_status:
                self._vocab_status.setText("⚠️ 查询失败")
                QTimer.singleShot(2500, lambda: self._safe_set_status(""))
        except RuntimeError:
            pass

    def _safe_set_status(self, text: str):
        try:
            if self._vocab_status:
                self._vocab_status.setText(text)
        except RuntimeError:
            pass

    def _write_vocab(self, word: str, definition: str):
        today = _date.today().isoformat()
        os.makedirs(os.path.dirname(VOCAB_FILE), exist_ok=True)

        if not os.path.exists(VOCAB_FILE):
            with open(VOCAB_FILE, "w", encoding="utf-8") as f:
                f.write(
                    "# 📖 生词本\n\n"
                    "> 用截屏翻译器遇到的生词，持续更新 🌱\n\n"
                    "---\n\n"
                )

        with open(VOCAB_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n### {word}\n{definition}\n📅 {today}\n\n---\n")

    # ── click handling ─────────────────────────────────────────────────────────

    def mousePressEvent(self, e):
        if self._card.geometry().contains(e.pos()):
            # _ClickLabel and QLineEdit consume their own events;
            # this fires only for clicks on the card background.
            should_retranslate = self._can_retranslate
            self.hide()
            if should_retranslate:
                self.retranslate.emit()
            self.close()
        else:
            self.close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.close()

    # ── public API ─────────────────────────────────────────────────────────────

    def show_loading(self):
        self._can_retranslate = False
        self._clear()
        self._place(64)
        lb = self._lbl("🌸  识别与翻译中…", 13, DIM)
        lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lay.addWidget(lb, 0, Qt.AlignmentFlag.AlignCenter)
        self.show()
        self.activateWindow()

    def show_result(self, original: str, translated: str):
        self._can_retranslate = True
        self._clear()

        # Original text (dimmed, one line)
        preview = original.replace("\n", " ")
        if len(preview) > 160:
            preview = preview[:160] + "…"
        self._lay.addWidget(self._lbl(preview, 11, DIM))
        self._lay.addWidget(self._div())

        # Translation
        self._lay.addWidget(self._lbl(translated, 15, MAIN, bold=True))
        self._lay.addWidget(self._div())

        # ── action row ────────────────────────────────────────────────────────
        action_row = QFrame()
        action_row.setStyleSheet("background: transparent;")
        al = QHBoxLayout(action_row)
        al.setContentsMargins(0, 0, 0, 0)
        al.setSpacing(6)

        retry_btn = _ClickLabel("🔄  继续翻译")
        retry_btn.setStyleSheet(_BTN_RETRY)
        retry_btn.clicked.connect(self._on_retranslate_click)

        copy_btn = _ClickLabel("📋  复制")
        copy_btn.setStyleSheet(_BTN_COPY)
        copy_btn.clicked.connect(lambda: self._copy_feedback(copy_btn, translated))

        self._vocab_btn = _ClickLabel("📚  记词")
        self._vocab_btn.setStyleSheet(_BTN_VOCAB)
        self._vocab_btn.clicked.connect(self._toggle_vocab)

        out = self._lbl("点击外部关闭", 10, DIM, wrap=False)

        al.addWidget(retry_btn)
        al.addWidget(copy_btn)
        al.addWidget(self._vocab_btn)
        al.addStretch()
        al.addWidget(out)
        self._lay.addWidget(action_row)

        # ── vocab input row (hidden until 📚 is clicked) ──────────────────────
        self._vocab_row = QFrame()
        self._vocab_row.setStyleSheet("background: transparent;")
        vl = QHBoxLayout(self._vocab_row)
        vl.setContentsMargins(0, 2, 0, 0)
        vl.setSpacing(6)

        self._vocab_input = QLineEdit()
        self._vocab_input.setPlaceholderText("输入不认识的单词，按 Enter 保存…")
        self._vocab_input.setStyleSheet(
            "background: rgba(255,255,255,150);"
            "border: 1px solid rgba(200,160,220,180);"
            "border-radius: 6px; padding: 4px 8px;"
            "font-size: 12px; color: rgba(70,25,50,255);"
            "font-family: 'PingFang SC', sans-serif;"
        )
        self._vocab_input.returnPressed.connect(self._submit_vocab)

        self._vocab_status = QLabel("")
        self._vocab_status.setStyleSheet(
            "color: rgba(150,100,200,255); font-size: 10px; background: transparent;"
            "font-family: 'PingFang SC', sans-serif;"
        )
        self._vocab_status.setFixedWidth(60)

        vl.addWidget(self._vocab_input)
        vl.addWidget(self._vocab_status)

        self._vocab_row.hide()
        self._lay.addWidget(self._vocab_row)

        self._resize()
        self.show()
        self.activateWindow()
        QTimer.singleShot(AUTO_DISMISS_MS, self.close)

    def show_error(self, message: str):
        self._can_retranslate = False
        self._clear()
        self._place(80)
        lb = self._lbl(f"⚠️  {message}", 13, ERR)
        lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lay.addWidget(lb, 0, Qt.AlignmentFlag.AlignCenter)
        self.show()
        QTimer.singleShot(6000, self.close)
