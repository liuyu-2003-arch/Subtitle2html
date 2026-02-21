# 快速开始指南

## 🚀 本地运行

### 方式1：直接打开HTML文件
1. 用浏览器打开 `index.html` 文件
2. 选择字幕文件上传
3. 点击"转换为HTML"按钮
4. 自动下载生成的HTML网页

### 方式2：使用本地服务器（推荐）
如果你有 Python 安装：
```bash
# Python 3.x
python -m http.server 8000

# Python 2.x
python -m SimpleHTTPServer 8000
```

然后打开浏览器访问 `http://localhost:8000`

如果你有 Node.js 安装：
```bash
npx http-server
```

## 📤 部署到 GitHub Pages

1. 确保你的仓库是公开的
2. 进入 Settings > Pages
3. 在 "Build and deployment" 中选择 "Deploy from a branch"
4. 选择 main 分支和 / (root) 文件夹
5. 点击 Save
6. 等待部署完成，访问 `https://你的用户名.github.io/Subtitle2html/`

## 📝 使用示例

### 示例1：转换SRT格式字幕
1. 在 `examples/` 文件夹中有 `demo.srt` 示例文件
2. 上传任何 `.srt` 格式的字幕文件
3. 选择转换，生成的网页会自动下载到本地

### 示例2：转换VTT格式字幕
```
WEBVTT

00:00:01.000 --> 00:00:03.000
第一条字幕

00:00:04.000 --> 00:00:06.000
第二条字幕
```

### 示例3：转换ASS格式字幕
```
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,第一条字幕
```

## 🎯 功能介绍

### 上传界面
- 点击上传区域选择文件
- 或直接拖入字幕文件
- 支持文件大小最大 10MB

### 转换功能
- 自动识别字幕格式
- 解析所有字幕行
- 保留时间码信息

### 生成的网页功能
- 📖 美观的字幕展示
- 🔍 内置搜索功能
- 📋 点击复制字幕内容
- 📱 完全响应式设计
- 🌐 可离线访问

## ⚙️ 技术细节

### 支持的格式

**SRT (SubRip)**
```
1
00:00:01,000 --> 00:00:03,000
字幕内容
```

**VTT (WebVTT)**
```
WEBVTT

00:00:01.000 --> 00:00:03.000
字幕内容
```

**ASS/SSA (Advanced SubStation Alpha)**
```
[Events]
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,字幕内容
```

### 文件夹说明

```
/
├── index.html          # 主页面
├── js/
│   ├── parser.js       # 字幕格式解析器
│   └── script.js       # 应用程序逻辑
├── subtitle/           # 生成的网页存放目录
├── examples/           # 示例字幕文件
│   └── demo.srt        # SRT格式示例
├── README.md           # 项目说明
└── QUICKSTART.md       # 本文件
```

## 🐛 常见问题排查

### Q: 上传文件后无反应？
A: 检查浏览器控制台（F12）是否有错误信息

### Q: 转换超时？
A: 文件可能过大，减小文件体积后重试

### Q: 生成的CSV打不开？
A: 您需要先将生成的HTML文件上传到web服务器，然后通过web访问

### Q: 支持其他字幕格式吗？
A: 当前支持 SRT、VTT、ASS/SSA，如需其他格式可提交 Issue

## 📞 获取帮助

- 查看 README.md 获取详细说明
- 提交 GitHub Issue 报告问题
- 提交 Pull Request 贡献代码

## 🔧 开发者信息

- 项目语言：HTML5, CSS3, JavaScript (ES6)
- 无需外部依赖，完全纯前端实现
- 开源协议：MIT

---

祝你使用愉快！ 🎉
