class SubtitleApp {
    constructor() {
        this.currentFile = null;
        this.currentSubtitles = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const convertBtn = document.getElementById('convertBtn');
        const resetBtn = document.getElementById('resetBtn');
        const copyBtn = document.getElementById('copyBtn');

        // 点击上传区域
        uploadArea.addEventListener('click', () => fileInput.click());

        // 拖拽上传
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });

        // 文件输入变化
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0]);
            }
        });

        // 转换按钮
        convertBtn.addEventListener('click', () => this.convertToHTML());

        // 重置按钮
        resetBtn.addEventListener('click', () => this.reset());

        // 复制链接
        copyBtn.addEventListener('click', () => this.copyLink());
    }

    handleFileSelect(file) {
        this.currentFile = file;
        const selectedFileDiv = document.getElementById('selectedFile');
        const convertBtn = document.getElementById('convertBtn');

        // 验证文件类型
        const allowedExtensions = ['srt', 'vtt', 'ass', 'ssa'];
        const extension = file.name.split('.').pop().toLowerCase();

        if (!allowedExtensions.includes(extension)) {
            this.showMessage('仅支持 .srt, .vtt, .ass, .ssa 格式', 'error');
            this.currentFile = null;
            convertBtn.disabled = true;
            return;
        }

        // 验证文件大小（限制为 10MB）
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showMessage('文件大小不能超过 10MB', 'error');
            this.currentFile = null;
            convertBtn.disabled = true;
            return;
        }

        selectedFileDiv.textContent = `已选择: ${file.name}`;
        selectedFileDiv.style.display = 'block';
        convertBtn.disabled = false;
        this.hideMessage();
        this.hideResult();
    }

    convertToHTML() {
        if (!this.currentFile) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const content = e.target.result;
                const subtitles = SubtitleParser.parse(content, this.currentFile.name);

                if (subtitles.length === 0) {
                    this.showMessage('无法解析字幕文件，请检查文件格式', 'error');
                    return;
                }

                this.currentSubtitles = subtitles;
                this.generateAndUploadHTML(subtitles);
            } catch (error) {
                this.showMessage('处理文件时出错: ' + error.message, 'error');
            }
        };

        reader.onerror = () => {
            this.showMessage('读取文件失败', 'error');
        };

        this.showLoading(true);
        reader.readAsText(this.currentFile);
    }

    generateAndUploadHTML(subtitles) {
        // 生成文件名（去掉扩展名）
        const baseFileName = this.currentFile.name.substring(0, this.currentFile.name.lastIndexOf('.'));
        const htmlFileName = baseFileName + '.html';

        // 生成 HTML 内容
        const htmlContent = this.generateHTMLContent(subtitles, baseFileName);

        // 创建 Blob
        const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });

        // 构建文件路径
        const subtitlePath = `subtitle/${htmlFileName}`;

        // 在本地存储并显示链接
        this.displayResult(subtitlePath, htmlFileName, blob);
    }

    generateHTMLContent(subtitles, title) {
        const subtitleHTML = subtitles.map((sub, index) => `
            <div class="subtitle-item" data-start="${sub.startTime}" data-end="${sub.endTime}">
                <div class="subtitle-time">
                    <span class="time-start">${sub.startTimeStr}</span>
                    <span class="time-separator">→</span>
                    <span class="time-end">${sub.endTimeStr}</span>
                </div>
                <div class="subtitle-text">${this.escapeHtml(sub.text)}</div>
            </div>
        `).join('');

        return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${this.escapeHtml(title)}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 40px;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 20px;
        }

        .header h1 {
            color: #333;
            font-size: 32px;
            margin-bottom: 10px;
            word-break: break-word;
        }

        .subtitle-count {
            color: #999;
            font-size: 14px;
        }

        .search-box {
            margin-bottom: 30px;
            display: flex;
            gap: 10px;
        }

        #searchInput {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.3s;
        }

        #searchInput:focus {
            outline: none;
            border-color: #667eea;
        }

        .search-hint {
            color: #999;
            font-size: 12px;
            margin-top: 8px;
        }

        .subtitles-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .subtitle-item {
            padding: 20px;
            border-left: 4px solid #667eea;
            background: #f8f9fa;
            border-radius: 6px;
            transition: all 0.3s ease;
        }

        .subtitle-item:hover {
            background: #f0f2ff;
            transform: translateX(4px);
        }

        .subtitle-item.highlight {
            background: #fff3cd;
            border-left-color: #ffc107;
        }

        .subtitle-time {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
            font-size: 12px;
            color: #999;
            font-weight: 600;
        }

        .time-separator {
            color: #ccc;
        }

        .subtitle-text {
            color: #333;
            font-size: 16px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
        }

        .empty-state svg {
            width: 64px;
            height: 64px;
            margin-bottom: 20px;
            opacity: 0.5;
        }

        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: #667eea;
            text-decoration: none;
            font-size: 14px;
            transition: color 0.3s;
        }

        .back-link:hover {
            color: #764ba2;
        }

        @media (max-width: 600px) {
            .container {
                padding: 20px;
            }

            .header h1 {
                font-size: 24px;
            }

            .subtitle-item {
                padding: 15px;
            }

            .subtitle-text {
                font-size: 14px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="../../index.html" class="back-link">← 返回上传</a>
        
        <div class="header">
            <h1>📺 ${this.escapeHtml(title)}</h1>
            <div class="subtitle-count">共 ${subtitles.length} 条字幕</div>
        </div>

        <div class="search-box">
            <input 
                type="text" 
                id="searchInput" 
                placeholder="搜索字幕内容..."
                autocomplete="off"
            >
        </div>
        <div class="search-hint">💡 输入关键词来搜索字幕，支持多个关键词用空格分隔</div>

        <div class="subtitles-container" id="subtitlesContainer">
            ${subtitleHTML}
        </div>
    </div>

    <script>
        // 搜索功能
        const searchInput = document.getElementById('searchInput');
        const subtitlesContainer = document.getElementById('subtitlesContainer');
        const subtitleItems = subtitlesContainer.querySelectorAll('.subtitle-item');

        searchInput.addEventListener('input', (e) => {
            const keywords = e.target.value.toLowerCase().trim().split(/\\s+/).filter(k => k);
            let hasResults = false;

            subtitleItems.forEach(item => {
                const text = item.textContent.toLowerCase();
                const matches = keywords.every(keyword => text.includes(keyword));

                if (matches) {
                    item.style.display = '';
                    item.classList.add('highlight');
                    hasResults = true;
                } else {
                    item.style.display = 'none';
                    item.classList.remove('highlight');
                }
            });

            // 显示/隐藏空状态
            if (!hasResults && keywords.length > 0) {
                if (!document.getElementById('emptyState')) {
                    const emptyState = document.createElement('div');
                    emptyState.id = 'emptyState';
                    emptyState.className = 'empty-state';
                    emptyState.innerHTML = '<p>未找到匹配的字幕</p>';
                    subtitlesContainer.appendChild(emptyState);
                }
            } else {
                const emptyState = document.getElementById('emptyState');
                if (emptyState) {
                    emptyState.remove();
                }
            }
        });

        // 点击字幕项复制内容
        subtitleItems.forEach(item => {
            item.addEventListener('click', () => {
                const text = item.querySelector('.subtitle-text').textContent;
                navigator.clipboard.writeText(text).then(() => {
                    const originalBg = item.style.background;
                    item.style.background = '#d4edda';
                    setTimeout(() => {
                        item.style.background = originalBg;
                    }, 500);
                }).catch(err => {
                    console.error('复制失败:', err);
                });
            });
            item.style.cursor = 'copy';
        });
    </script>
</body>
</html>`;
    }

    displayResult(subtitlePath, htmlFileName, blob) {
        this.showLoading(false);

        // 使用下载链接
        const url = URL.createObjectURL(blob);
        
        // 显示结果
        const resultLink = document.getElementById('resultLink');
        resultLink.href = url;
        resultLink.textContent = `📖 ${htmlFileName}`;
        
        // 保存下载链接和文件名供复制使用
        resultLink.dataset.downloadUrl = url;
        resultLink.dataset.fileName = htmlFileName;
        
        document.getElementById('resultSection').classList.add('show');
        
        this.showMessage(`✅ 字幕已转换成功！已为你生成 ${htmlFileName}`, 'success');

        // 自动触发下载
        setTimeout(() => {
            this.downloadFile(blob, htmlFileName);
        }, 500);
    }

    downloadFile(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    copyLink() {
        const resultLink = document.getElementById('resultLink');
        const url = resultLink.href;
        const text = resultLink.textContent;

        navigator.clipboard.writeText(text + '\n' + url).then(() => {
            const copyBtn = document.getElementById('copyBtn');
            const originalText = copyBtn.textContent;
            copyBtn.textContent = '已复制！';
            copyBtn.classList.add('copied');

            setTimeout(() => {
                copyBtn.textContent = originalText;
                copyBtn.classList.remove('copied');
            }, 2000);
        }).catch(err => {
            this.showMessage('复制失败: ' + err.message, 'error');
        });
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        if (show) {
            loading.classList.add('show');
        } else {
            loading.classList.remove('show');
        }
    }

    showMessage(text, type) {
        const message = document.getElementById('message');
        message.textContent = text;
        message.className = 'message show ' + type;
    }

    hideMessage() {
        const message = document.getElementById('message');
        message.classList.remove('show');
    }

    hideResult() {
        document.getElementById('resultSection').classList.remove('show');
    }

    reset() {
        document.getElementById('fileInput').value = '';
        document.getElementById('selectedFile').style.display = 'none';
        document.getElementById('convertBtn').disabled = true;
        this.currentFile = null;
        this.currentSubtitles = null;
        this.hideMessage();
        this.hideResult();
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new SubtitleApp();
});
