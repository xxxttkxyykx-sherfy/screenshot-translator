import Cocoa
import Foundation

let selfPath = URL(fileURLWithPath: CommandLine.arguments[0])
let dir = selfPath.deletingLastPathComponent().deletingLastPathComponent().path

let TRIGGER = "/tmp/translate_trigger"
let ALIVE   = "/tmp/translator_alive"

func isWorkerAlive() -> Bool {
    FileManager.default.fileExists(atPath: ALIVE)
}

func startWorker() {
    let task = Process()
    task.executableURL = URL(fileURLWithPath: "/bin/bash")
    task.arguments = ["\(dir)/run_worker.sh"]
    task.currentDirectoryURL = URL(fileURLWithPath: dir)
    try? task.run()
    // Wait up to 2s for worker to be ready
    for _ in 0..<20 {
        Thread.sleep(forTimeInterval: 0.1)
        if isWorkerAlive() { break }
    }
}

func sendTrigger() {
    FileManager.default.createFile(atPath: TRIGGER, contents: nil, attributes: nil)
}

class AppDelegate: NSObject, NSApplicationDelegate {
    var statusItem: NSStatusItem!
    var quitMenu: NSMenu!

    func applicationDidFinishLaunching(_ n: Notification) {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let btn = statusItem.button {
            btn.title  = "译"
            btn.font   = NSFont.systemFont(ofSize: 14, weight: .medium)
            btn.action = #selector(handleClick)
            btn.target = self
            btn.sendAction(on: [.leftMouseUp, .rightMouseUp])
        }
        // Right-click menu (quit only)
        quitMenu = NSMenu()
        quitMenu.addItem(NSMenuItem(title: "退出翻译工具",
                                    action: #selector(NSApplication.terminate(_:)),
                                    keyEquivalent: "q"))
    }

    @objc func handleClick() {
        guard let event = NSApp.currentEvent else { return }
        if event.type == .rightMouseUp {
            // Right-click → show quit menu
            statusItem.menu = quitMenu
            statusItem.button?.performClick(nil)
            statusItem.menu = nil
        } else {
            // Left-click → translate immediately
            DispatchQueue.global().async {
                if !isWorkerAlive() { startWorker() }
                sendTrigger()
            }
        }
    }
}

NSApplication.shared.setActivationPolicy(.accessory)
let delegate = AppDelegate()
NSApplication.shared.delegate = delegate
NSApplication.shared.run()
