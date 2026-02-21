# Subtitle2html

字幕转 HTML 网页，支持在线访问。

## 方式一：上传生成（推荐）

1. 安装依赖并启动服务：
   ```bash
   pip install flask
   python server.py
   ```
2. 浏览器打开：<http://localhost:5000/upload.html>
3. 拖入或选择字幕文件（支持 .srt .ass .ssa .vtt .txt）
4. 点击「生成并保存到 subtitle/」— 网页会保存到 `subtitle/` 文件夹，并以**文件名的英文部分**命名
5. 生成的页面可通过 <http://localhost:5000/subtitle/xxx.html> 直接访问

## 方式二：批量生成（GitHub Actions）

将字幕文件放入 `subtitles/` 文件夹，推送后 GitHub Actions 会自动为每个字幕生成 HTML 到 `subtitle/`，并更新首页 `index.html`。

## 方式三：本地生成器

打开 `subtitle-generator.html`，上传字幕、生成 HTML 并下载，再将下载的文件放入 `subtitle/` 文件夹。

## 在线部署

将项目推送到 GitHub 并启用 GitHub Pages，即可通过在线地址访问所有字幕页面。
