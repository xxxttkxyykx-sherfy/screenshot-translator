#!/usr/bin/env python3
"""
Persistent worker daemon.
Swift menubar touches /tmp/translate_trigger to start a session.
"""
import os, sys, time, tempfile, threading

TRIGGER   = "/tmp/translate_trigger"
ALIVE     = "/tmp/translator_alive"

# ── hide from Dock ────────────────────────────────────────────────────────────
try:
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
    NSApplication.sharedApplication().setActivationPolicy_(
        NSApplicationActivationPolicyAccessory
    )
except Exception:
    pass

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from selector import RegionSelector
from ocr import extract_text
from translator import translate
from overlay import TranslationOverlay

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not API_KEY:
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from config import DEEPSEEK_API_KEY
        API_KEY = DEEPSEEK_API_KEY
    except ImportError:
        pass


class Daemon(QObject):
    _sig_ok  = pyqtSignal(str, str)
    _sig_err = pyqtSignal(str)

    def __init__(self, app: QApplication):
        super().__init__()
        self._app     = app
        self._overlay = None
        self._busy    = False

        self._sig_ok.connect(self._on_ok)
        self._sig_err.connect(self._on_err)

        timer = QTimer(self)
        timer.timeout.connect(self._check)
        timer.start(80)

    def _check(self):
        if self._busy or not os.path.exists(TRIGGER):
            return
        try:
            os.unlink(TRIGGER)
        except OSError:
            return
        self._busy = True
        self._run()

    def _run(self):
        self._busy = True
        # 1. Region selection
        selector = RegionSelector()
        region   = selector.run()
        if not region or region[2] < 10 or region[3] < 10:
            self._busy = False
            return
        x, y, w, h = region

        # 2. Close old overlay — clear the reference BEFORE closing so that
        #    any in-flight _on_ok / _on_err triggered during close() sees None
        #    and doesn't crash on an already-deleted C++ object.
        old = self._overlay
        self._overlay = None
        if old:
            try: old.close()
            except Exception: pass

        # 3. New loading overlay
        self._overlay = TranslationOverlay(x, y, w, h, api_key=API_KEY)
        self._overlay.retranslate.connect(self._run)
        self._overlay.show_loading()

        # 4. Capture + OCR + translate in background
        threading.Thread(
            target=self._process, args=(x, y, w, h), daemon=True
        ).start()

    def _process(self, x, y, w, h):
        import mss, mss.tools
        tmp = tempfile.mktemp(suffix=".png")
        try:
            time.sleep(0.15)   # let selector fully close
            with mss.MSS() as sct:
                img = sct.grab({"top": y, "left": x, "width": w, "height": h})
                mss.tools.to_png(img.rgb, img.size, output=tmp)

            text = extract_text(tmp)
            if not text.strip():
                self._sig_err.emit("未识别到文字")
                return
            result = translate(text, API_KEY)
            self._sig_ok.emit(text, result)
        except Exception as e:
            self._sig_err.emit(str(e))
        finally:
            try: os.unlink(tmp)
            except: pass

    def _on_ok(self, original: str, translated: str):
        if self._overlay:
            try:
                self._overlay.show_result(original, translated)
            except RuntimeError:
                # C++ overlay was auto-dismissed or double-closed; discard
                self._overlay = None
        self._busy = False

    def _on_err(self, msg: str):
        if self._overlay:
            try:
                self._overlay.show_error(msg)
            except RuntimeError:
                self._overlay = None
        self._busy = False


def main():
    # Write alive marker
    with open(ALIVE, "w") as f:
        f.write(str(os.getpid()))

    import atexit
    atexit.register(lambda: (
        os.unlink(ALIVE) if os.path.exists(ALIVE) else None
    ))

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    daemon = Daemon(app)  # noqa: F841
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
