"""
OCR via a pre-compiled Swift binary that calls macOS Vision framework.
Run setup.sh once to compile the binary into bin/ocr_helper.
"""
import os
import subprocess

_DIR = os.path.dirname(os.path.abspath(__file__))
OCR_BINARY = os.path.join(_DIR, "bin", "ocr_helper")

# Swift source embedded here so setup.sh can write & compile it
SWIFT_SOURCE = r'''
import Vision
import Foundation

let args = CommandLine.arguments
guard args.count > 1 else {
    fputs("Usage: ocr_helper <image_path>\n", stderr)
    exit(1)
}

let url = URL(fileURLWithPath: args[1])
do {
    let handler = try VNImageRequestHandler(url: url, options: [:])
    let request = VNRecognizeTextRequest()
    request.recognitionLanguages = ["en-US", "zh-Hans", "zh-Hant"]
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    try handler.perform([request])

    let lines = (request.results ?? [])
        .compactMap { $0.topCandidates(1).first?.string }
    print(lines.joined(separator: "\n"))
} catch {
    fputs("OCR error: \(error)\n", stderr)
    exit(1)
}
'''


def extract_text(image_path: str) -> str:
    if not os.path.exists(OCR_BINARY):
        raise FileNotFoundError(
            "OCR 工具未编译，请先运行: bash setup.sh"
        )
    result = subprocess.run(
        [OCR_BINARY, image_path],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"OCR 失败: {result.stderr.strip()}")
    return result.stdout.strip()
