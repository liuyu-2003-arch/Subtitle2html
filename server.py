#!/usr/bin/env python3
"""
本地字幕上传服务：接收上传的字幕文件，生成 HTML 到 subtitle/，可在线访问。

启动: python server.py
访问: http://localhost:5000/upload.html 上传
"""

import os
import sys
from pathlib import Path

# 确保从项目根目录运行
PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, request, jsonify, send_from_directory

from scripts.build_subtitle import (
    parse_content,
    build_html,
    derive_output_name_upload,
    derive_title,
    rebuild_index_from_subtitle_dir,
    add_translation,
    OUTPUT_DIR,
    SUPPORTED_EXT,
)

app = Flask(__name__, static_folder=str(PROJECT_ROOT))
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # 4MB


@app.route("/")
def index():
    return send_from_directory(PROJECT_ROOT, "index.html")


@app.route("/<path:path>")
def static_file(path):
    return send_from_directory(PROJECT_ROOT, path)


@app.route("/api/upload", methods=["POST"])
def upload_subtitle():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "未选择文件"}), 400

    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "未选择文件"}), 400

    ext = Path(f.filename).suffix.lower()
    if ext not in SUPPORTED_EXT:
        return jsonify({
            "ok": False,
            "error": f"不支持格式 {ext}，支持: .srt .vtt .ass .ssa .txt"
        }), 400

    try:
        content = f.read().decode("utf-8", errors="replace")
    except Exception as e:
        return jsonify({"ok": False, "error": f"读取文件失败: {e}"}), 400

    try:
        subs = parse_content(content, ext)
    except Exception as e:
        return jsonify({"ok": False, "error": f"解析字幕失败: {e}"}), 400

    if not subs:
        return jsonify({"ok": False, "error": "未解析到字幕内容"}), 400

    stem = Path(f.filename).stem
    title = derive_title(stem)
    OUTPUT_DIR.mkdir(exist_ok=True)
    out_name = derive_output_name_upload(stem, OUTPUT_DIR)
    out_path = OUTPUT_DIR / out_name

    try:
        # 尝试添加翻译
        subs, title = add_translation(subs, title)
        html = build_html(subs, title)
        out_path.write_text(html, encoding="utf-8")
    except Exception as e:
        return jsonify({"ok": False, "error": f"生成 HTML 失败: {e}"}), 500

    try:
        rebuild_index_from_subtitle_dir()
    except Exception as e:
        return jsonify({
            "ok": True,
            "filename": out_name,
            "url": f"/subtitle/{out_name}",
            "warning": f"首页更新失败: {e}",
        }), 200

    return jsonify({
        "ok": True,
        "filename": out_name,
        "url": f"/subtitle/{out_name}",
        "title": title,
        "count": len(subs),
    })


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("字幕上传服务: http://localhost:5000")
    print("上传页面:     http://localhost:5000/upload.html")
    app.run(host="0.0.0.0", port=5000, debug=True)
