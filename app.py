#!/usr/bin/env python3
"""
Screenshot Translation Tool — macOS menu bar app
Click "译" in the menu bar to start region selection.
"""
import os, sys, time, tempfile, threading, subprocess

import rumps

API_KEY = ""


def _load_api_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        try:
            from config import DEEPSEEK_API_KEY
            key = DEEPSEEK_API_KEY
        except ImportError:
            pass
    return key


def _run_selection_and_translate():
    """Runs the PyQt6 selector + overlay in a subprocess to avoid NSApp conflict."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()
    env["DEEPSEEK_API_KEY"] = API_KEY
    subprocess.Popen(
        [sys.executable, os.path.join(script_dir, "worker.py")],
        env=env,
        cwd=script_dir,
    )


class TranslatorApp(rumps.App):
    def __init__(self):
        super().__init__("译", quit_button=None)
        self.menu = [
            rumps.MenuItem("📷  截图翻译", callback=self.translate),
            None,  # separator
            rumps.MenuItem("退出", callback=rumps.quit_application),
        ]

    @rumps.clicked("📷  截图翻译")
    def translate(self, _):
        threading.Thread(target=_run_selection_and_translate, daemon=True).start()


def main():
    global API_KEY
    API_KEY = _load_api_key()
    if not API_KEY:
        print("❌  请在 config.py 里填写 DEEPSEEK_API_KEY")
        sys.exit(1)

    print("✅  截屏翻译已启动 — 点击菜单栏「译」图标开始翻译")
    TranslatorApp().run()


if __name__ == "__main__":
    main()
