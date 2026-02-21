// 字幕解析器
class SubtitleParser {
    // 解析 SRT 格式
    static parseSRT(content) {
        const subtitles = [];
        const blocks = content.trim().split(/\n\s*\n+/);

        for (const block of blocks) {
            const lines = block.trim().split('\n');
            if (lines.length < 3) continue;

            const timeMatch = lines[1].match(/(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})/);
            if (!timeMatch) continue;

            const startTime = this.srtTimeToSeconds(timeMatch[1]);
            const endTime = this.srtTimeToSeconds(timeMatch[2]);
            const text = lines.slice(2).join('\n').trim();

            subtitles.push({
                startTime,
                endTime,
                text,
                startTimeStr: this.secondsToTimeStr(startTime),
                endTimeStr: this.secondsToTimeStr(endTime)
            });
        }

        return subtitles;
    }

    // 解析 VTT 格式
    static parseVTT(content) {
        const subtitles = [];
        const lines = content.trim().split('\n');
        
        let i = 0;
        // 跳过 VTT 头
        while (i < lines.length && !lines[i].includes('-->')) {
            i++;
        }

        while (i < lines.length) {
            const line = lines[i].trim();
            
            if (line.includes('-->')) {
                const timeMatch = line.match(/(\d{2}:\d{2}:\d{2})[.,](\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2})[.,](\d{3})/);
                if (timeMatch) {
                    const startTime = this.vttTimeToSeconds(timeMatch[1], timeMatch[2]);
                    const endTime = this.vttTimeToSeconds(timeMatch[3], timeMatch[4]);
                    
                    const textLines = [];
                    i++;
                    while (i < lines.length && lines[i].trim() !== '') {
                        textLines.push(lines[i].trim());
                        i++;
                    }

                    if (textLines.length > 0) {
                        const text = textLines.join('\n');
                        subtitles.push({
                            startTime,
                            endTime,
                            text,
                            startTimeStr: this.secondsToTimeStr(startTime),
                            endTimeStr: this.secondsToTimeStr(endTime)
                        });
                    }
                }
            }
            i++;
        }

        return subtitles;
    }

    // 解析 ASS/SSA 格式
    static parseASS(content) {
        const subtitles = [];
        const lines = content.split('\n');
        
        let eventsStarted = false;
        let formatLine = '';

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];

            if (line.startsWith('[Events]')) {
                eventsStarted = true;
                continue;
            }

            if (eventsStarted) {
                if (line.startsWith('Format:')) {
                    formatLine = line;
                    continue;
                }

                if (line.startsWith('Dialogue:')) {
                    const format = formatLine.replace('Format: ', '').split(',').map(s => s.trim());
                    const values = line.replace('Dialogue: ', '').split(',');
                    
                    if (values.length >= 10) {
                        const startIndex = format.indexOf('Start');
                        const endIndex = format.indexOf('End');
                        const textIndex = format.indexOf('Text');

                        const startTime = this.assTimeToSeconds(values[startIndex].trim());
                        const endTime = this.assTimeToSeconds(values[endIndex].trim());
                        const text = values.slice(textIndex).join(',').trim();

                        subtitles.push({
                            startTime,
                            endTime,
                            text,
                            startTimeStr: this.secondsToTimeStr(startTime),
                            endTimeStr: this.secondsToTimeStr(endTime)
                        });
                    }
                }
            }
        }

        return subtitles;
    }

    // 时间转换函数
    static srtTimeToSeconds(timeStr) {
        const [time, ms] = timeStr.split(',');
        const [h, m, s] = time.split(':').map(Number);
        return h * 3600 + m * 60 + s + parseInt(ms) / 1000;
    }

    static vttTimeToSeconds(timeStr, msStr) {
        const [h, m, s] = timeStr.split(':').map(Number);
        return h * 3600 + m * 60 + s + parseInt(msStr) / 1000;
    }

    static assTimeToSeconds(timeStr) {
        // ASS 格式: h:mm:ss.cc
        const [time, centiseconds] = timeStr.split('.');
        const [h, m, s] = time.split(':').map(Number);
        return h * 3600 + m * 60 + s + parseInt(centiseconds || 0) / 100;
    }

    static secondsToTimeStr(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 1000);
        
        return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
    }

    // 自动检测格式并解析
    static parse(content, filename) {
        const ext = filename.toLowerCase().split('.').pop();

        switch (ext) {
            case 'srt':
                return this.parseSRT(content);
            case 'vtt':
                return this.parseVTT(content);
            case 'ass':
            case 'ssa':
                return this.parseASS(content);
            default:
                // 尝试自动检测
                if (content.includes('WEBVTT')) {
                    return this.parseVTT(content);
                } else if (content.includes('[Events]')) {
                    return this.parseASS(content);
                } else {
                    return this.parseSRT(content);
                }
        }
    }
}
