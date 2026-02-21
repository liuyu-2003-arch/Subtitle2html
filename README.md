# Subtitle2HTML

把字幕变成在线网页 🎬

## 功能特性

✨ **简单易用** - 上传字幕文件，一键生成美观的在线网页
🎨 **现代设计** - 响应式设计，完美支持各种设备
📱 **移动友好** - 手机、平板、桌面完美适配
🔍 **搜索功能** - 内置字幕搜索功能，快速查找内容
📋 **多格式支持** - 支持 SRT、VTT、ASS/SSA 多种字幕格式
⚡ **零依赖** - 纯HTML/CSS/JavaScript，无需服务器

## 支持的字幕格式

- **SRT** (.srt) - SubRip 字幕格式
- **VTT** (.vtt) - WebVTT 字幕格式
- **ASS/SSA** (.ass, .ssa) - Advanced SubStation Alpha 格式

## 使用方法

### 在线使用

1. 打开网站 [Subtitle2HTML](https://liuyu-2003-arch.github.io/Subtitle2html/)
2. 点击上传区域或拖入字幕文件
3. 点击"转换为HTML"按钮
4. 等待转换完成，下载生成的HTML文件
5. 打开HTML文件在浏览器中查看字幕

### 本地运行

1. 克隆本仓库：
```bash
git clone https://github.com/liuyu-2003-arch/Subtitle2html.git
cd Subtitle2html
```

2. 用浏览器打开 `index.html` 文件即可使用

## 项目结构

```
Subtitle2html/
├── index.html           # 主页面
├── js/
│   ├── parser.js        # 字幕解析器
│   └── script.js        # 主应用逻辑
└── subtitle/            # 生成的网页保存目录
```

## 文件说明

- **index.html** - 上传和转换界面
- **js/parser.js** - 多格式字幕解析器，支持 SRT、VTT、ASS/SSA 格式
- **js/script.js** - 主应用程序，处理文件上传、解析和HTML生成
- **subtitle/** - 存放生成的HTML网页文件

## 生成的网页特性

转换生成的HTML网页包含以下功能：

📖 **整洁展示** - 清晰显示所有字幕及时间码
🔍 **搜索功能** - 支持关键词搜索字幕
📋 **复制功能** - 点击字幕项即可复制内容
📱 **响应式设计** - 自适应各种屏幕尺寸
🌐 **独立文件** - 生成的网页可以离线查看

## 技术栈

- HTML5
- CSS3
- Vanilla JavaScript (无框架依赖)

## 浏览器兼容性

支持所有现代浏览器：
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## 常见问题

**Q: 文件大小有限制吗？**
A: 文件大小限制为10MB，足以处理大多数字幕文件。

**Q: 能否保留原字幕文件的样式（如颜色、字体）？**
A: 当前版本以简洁易读为设计理念，不保留原样式，但生成的网页具有现代美观的设计。

**Q: 网页能否在线访问？**
A: 可以！将生成的HTML文件上传到服务器或GitHub Pages等平台即可在线访问。

## 开源协议

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**Made with ❤️ by liuyu-2003-arch**
