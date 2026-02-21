#!/usr/bin/env python3
"""
scripts/build_subtitle.py

1. 扫描 subtitles/ 文件夹，为每个字幕文件在 subtitle/ 生成 HTML 页面
2. 扫描 subtitle/ 文件夹，生成根目录 index.html 首页

支持格式：.srt  .vtt  .ass  .ssa  .txt
"""

import re
import json
import hashlib
from pathlib import Path
from datetime import datetime

# ── 路径配置 ──────────────────────────────────────────────
SUBTITLES_DIR = Path("subtitles")
OUTPUT_DIR    = Path("subtitle")
INDEX_PATH    = Path("index.html")
SUPPORTED_EXT = {".srt", ".vtt", ".ass", ".ssa", ".txt"}

# ── 时间转换 ──────────────────────────────────────────────
def time_to_sec(t: str) -> float:
    t = t.replace(",", ".")
    parts = t.split(":")
    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])

def ass_time_to_sec(t: str) -> float:
    parts = t.split(":")
    if len(parts) < 3:
        return 0.0
    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])

def fmt_time_full(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def fmt_duration(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    if h > 0:
        return f"{h}小时{m}分{s}秒"
    return f"{m}分{s}秒"

# ── 解析器 ────────────────────────────────────────────────
def parse_srt(text: str) -> list:
    subs = []
    blocks = re.split(r"\n\n+", text.strip())
    for block in blocks:
        lines = block.strip().splitlines()
        time_line = next((l for l in lines if "-->" in l), None)
        if not time_line:
            continue
        m = re.match(
            r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})",
            time_line,
        )
        if not m:
            continue
        idx = lines.index(time_line) + 1
        text_part = " ".join(lines[idx:]).strip()
        text_part = re.sub(r"<[^>]+>", "", text_part).strip()
        if text_part:
            subs.append({
                "s": round(time_to_sec(m.group(1)), 2),
                "e": round(time_to_sec(m.group(2)), 2),
                "t": text_part,
            })
    return subs

def parse_vtt(text: str) -> list:
    subs = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if "-->" in lines[i]:
            m = re.match(
                r"(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})",
                lines[i],
            )
            if m:
                i += 1
                text_lines = []
                while i < len(lines) and lines[i].strip():
                    text_lines.append(lines[i].strip())
                    i += 1
                text_part = " ".join(text_lines)
                text_part = re.sub(r"<[^>]+>", "", text_part).strip()
                if text_part:
                    subs.append({
                        "s": round(time_to_sec(m.group(1)), 2),
                        "e": round(time_to_sec(m.group(2)), 2),
                        "t": text_part,
                    })
        i += 1
    return subs

def parse_ass(text: str) -> list:
    subs = []
    in_events = False
    fmt = []
    for line in text.splitlines():
        if line.startswith("[Events]"):
            in_events = True
            continue
        if in_events and line.startswith("Format:"):
            fmt = [f.strip() for f in line.replace("Format:", "").split(",")]
        if in_events and line.startswith("Dialogue:"):
            parts = line.replace("Dialogue:", "").split(",")
            obj = {fmt[i]: (parts[i] if i < len(parts) else "").strip()
                   for i in range(len(fmt))}
            ti = fmt.index("Text") if "Text" in fmt else -1
            if ti < 0:
                continue
            raw = ",".join(parts[ti:])
            raw = re.sub(r"\{[^}]+\}", "", raw).replace("\\N", " ").strip()
            start = ass_time_to_sec(obj.get("Start", "0:00:00.00"))
            end   = ass_time_to_sec(obj.get("End",   "0:00:00.00"))
            if raw:
                subs.append({"s": round(start, 2), "e": round(end, 2), "t": raw})
    return subs

def parse_txt(text: str) -> list:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return [{"s": round(i * 3, 2), "e": round(i * 3 + 2.5, 2), "t": l}
            for i, l in enumerate(lines)]

def parse_file(path: Path) -> list:
    text = path.read_text(encoding="utf-8", errors="replace")
    ext  = path.suffix.lower()
    return parse_content(text, ext)


def parse_content(text: str, ext: str) -> list:
    """从文本内容解析字幕，ext 如 .srt .vtt .ass .ssa .txt"""
    ext = ext.lower() if ext.startswith(".") else "." + ext.lower()
    if ext == ".srt":               return parse_srt(text)
    if ext == ".vtt":               return parse_vtt(text)
    if ext in (".ass", ".ssa"):     return parse_ass(text)
    return parse_txt(text)

# ── 文件名处理 ────────────────────────────────────────────
def derive_output_name(stem: str) -> str:
    ascii_part = re.sub(r"[^\x00-\x7F]", "-", stem)
    ascii_part = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_part)
    ascii_part = ascii_part.strip("-").lower()
    
    # Generate a short hash of the full stem to ensure uniqueness
    hash_suffix = hashlib.md5(stem.encode("utf-8")).hexdigest()[:6]
    
    if not ascii_part:
        return f"sub-{hash_suffix}.html"
        
    return f"{ascii_part}-{hash_suffix}.html"


def derive_output_name_upload(stem: str, output_dir: Path) -> str:
    """上传时使用：仅取文件名英文部分，不加固有 hash，遇冲突追加数字"""
    ascii_part = re.sub(r"[^\x00-\x7F]", "-", stem)
    ascii_part = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_part)
    ascii_part = ascii_part.strip("-").lower()
    if not ascii_part or len(ascii_part) < 2:
        ascii_part = "subtitle-" + hashlib.md5(stem.encode("utf-8")).hexdigest()[:8]
    base = ascii_part + ".html"
    if not (output_dir / base).exists():
        return base
    for i in range(2, 999):
        cand = f"{ascii_part}-{i}.html"
        if not (output_dir / cand).exists():
            return cand
    return f"{ascii_part}-{int(datetime.now().timestamp())}.html"

def derive_title(stem: str) -> str:
    return stem.replace("_", " ").strip()

# ── 转义 ──────────────────────────────────────────────────
def esc(s: str) -> str:
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))

# ── 字幕页 HTML ───────────────────────────────────────────
def build_html(subs: list, title: str) -> str:
    if not subs:
        raise ValueError("字幕列表为空")
    total   = subs[-1]["e"]
    mins    = int(total // 60)
    secs    = int(total % 60)
    count   = len(subs)
    subs_js = json.dumps(subs, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;500&family=Crimson+Pro:ital,wght@0,300;0,400;1,300&display=swap');
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#0a0a0c;--bg2:#111116;--border:rgba(255,255,255,.06);--gold:#c9a84c;--gold2:#e8c97a;--text:#d4cfc8;--text-dim:#6b6760;--text-mute:#38383a;--abg:rgba(201,168,76,.08)}}
html{{scroll-behavior:smooth}}
body{{background:var(--bg);color:var(--text);font-family:'Noto Serif SC','Songti SC',serif;min-height:100vh;overflow-x:hidden}}
body::before{{content:'';position:fixed;inset:0;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.04'/%3E%3C/svg%3E");pointer-events:none;z-index:9999;opacity:.35}}
.hd{{position:fixed;top:0;left:0;right:0;z-index:100;background:linear-gradient(to bottom,rgba(10,10,12,.97) 55%,transparent);padding:22px 40px 44px}}
.back{{display:inline-flex;align-items:center;gap:6px;font-family:'Crimson Pro',serif;font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:var(--text-mute);text-decoration:none;margin-bottom:10px;transition:color .2s}}
.back:hover{{color:var(--gold)}}
h1{{font-size:clamp(15px,2.2vw,21px);font-weight:300;letter-spacing:.08em;color:#f0ece4;line-height:1.4}}
.meta{{margin-top:5px;font-family:'Crimson Pro',serif;font-size:12px;color:var(--text-mute);letter-spacing:.04em}}
.ctrls{{position:fixed;top:22px;right:40px;z-index:101;display:flex;gap:8px}}
.btn{{background:none;border:1px solid var(--border);color:var(--text-mute);padding:5px 13px;font-family:'Noto Serif SC',serif;font-size:11px;letter-spacing:.08em;cursor:pointer;transition:all .2s;border-radius:2px}}
.btn:hover{{border-color:var(--gold);color:var(--gold)}}
.btn.on{{border-color:var(--gold);color:var(--gold);background:var(--abg)}}
.srch{{position:fixed;top:22px;right:200px;z-index:100}}
.srch input{{background:rgba(20,20,26,.92);border:1px solid var(--border);color:var(--text);padding:6px 14px;font-family:'Noto Serif SC',serif;font-size:12px;width:180px;outline:none;border-radius:2px;transition:border-color .2s;backdrop-filter:blur(10px)}}
.srch input::placeholder{{color:var(--text-mute)}}
.srch input:focus{{border-color:rgba(201,168,76,.4)}}
.main{{display:grid;grid-template-columns:1fr 290px;padding-top:100px;padding-bottom:68px;min-height:100vh}}
.sl{{padding:28px 44px 28px 38px;overflow-y:auto;height:calc(100vh - 168px);position:sticky;top:100px;scrollbar-width:thin;scrollbar-color:#222228 transparent}}
.sl::-webkit-scrollbar{{width:3px}}
.sl::-webkit-scrollbar-thumb{{background:#222228;border-radius:2px}}
.si{{display:flex;align-items:baseline;gap:16px;padding:8px 14px;border-left:2px solid transparent;cursor:pointer;transition:all .2s;border-radius:0 3px 3px 0;margin-bottom:1px}}
.si:hover{{background:rgba(255,255,255,.025);border-left-color:var(--text-mute)}}
.si.act{{background:var(--abg);border-left-color:var(--gold)}}
.si.sm{{background:rgba(201,168,76,.05)}}
.st{{font-family:'Crimson Pro',serif;font-size:11px;color:var(--text-mute);flex-shrink:0;width:48px;letter-spacing:.04em;transition:color .2s}}
.si.act .st{{color:var(--gold);opacity:.65}}
.sx{{font-size:14.5px;font-weight:300;line-height:1.75;letter-spacing:.05em;color:var(--text-dim);transition:color .2s;flex:1}}
.si.act .sx{{color:#f0ece4;font-weight:400}}
.sx mark{{background:rgba(201,168,76,.14);color:var(--gold2);padding:0 2px;border-radius:2px}}
.sp{{border-left:1px solid var(--border);background:var(--bg2);position:sticky;top:100px;height:calc(100vh - 168px);overflow-y:auto;display:flex;flex-direction:column}}
.np{{padding:32px 22px;flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;border-bottom:1px solid var(--border)}}
.np-lb{{font-family:'Crimson Pro',serif;font-size:10px;font-style:italic;letter-spacing:.28em;text-transform:uppercase;color:var(--text-mute);margin-bottom:20px}}
.np-dc{{display:flex;align-items:center;gap:10px;margin-bottom:14px}}
.np-dl{{width:26px;height:1px;background:linear-gradient(to right,transparent,var(--gold));opacity:.35}}
.np-dl:last-child{{background:linear-gradient(to left,transparent,var(--gold))}}
.np-dd{{width:4px;height:4px;border-radius:50%;background:var(--gold);opacity:.45}}
.np-tx{{font-size:clamp(15px,2.2vw,21px);font-weight:300;letter-spacing:.07em;line-height:1.85;color:#f0ece4;min-height:72px;display:flex;align-items:center;justify-content:center;transition:all .3s}}
.np-ix{{margin-top:18px;font-family:'Crimson Pro',serif;font-size:11px;color:var(--text-mute);letter-spacing:.1em}}
.stats{{padding:18px 22px}}
.sr{{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border);font-size:11px;letter-spacing:.04em}}
.sr-l{{color:var(--text-mute);font-family:'Crimson Pro',serif}}
.sr-v{{color:var(--text-dim)}}
.pw{{position:fixed;bottom:0;left:0;right:0;z-index:100;padding:14px 40px 18px;background:linear-gradient(to top,rgba(10,10,12,.97) 55%,transparent)}}
.td{{display:flex;justify-content:space-between;font-family:'Crimson Pro',serif;font-size:11px;color:var(--text-dim);letter-spacing:.08em;margin-bottom:6px}}
.pb{{width:100%;height:2px;background:var(--text-mute);cursor:pointer;border-radius:1px}}
.pf{{height:100%;background:linear-gradient(to right,var(--gold),var(--gold2));border-radius:1px;width:0%;pointer-events:none}}
.curtain{{position:fixed;inset:0;background:#000;z-index:9998;animation:cr 1.2s ease forwards .1s}}
@keyframes cr{{to{{opacity:0;pointer-events:none}}}}
@media(max-width:700px){{.main{{grid-template-columns:1fr}}.sp{{display:none}}.hd{{padding:14px 18px 44px}}.sl{{padding:16px}}.pw{{padding:10px 18px 14px}}.ctrls{{top:14px;right:18px}}.srch{{display:none}}}}
</style>
</head>
<body>
<div class="curtain"></div>
<header class="hd">
  <a class="back" href="../index.html">← 返回首页</a>
  <h1>{esc(title)}</h1>
  <div class="meta">{count:,} 句字幕 · {mins}分{secs}秒</div>
</header>
<div class="ctrls">
  <button class="btn on" id="btnA" onclick="tA()">自动跟随</button>
  <button class="btn" id="btnC" onclick="tC()">紧凑</button>
</div>
<div class="srch"><input type="text" placeholder="搜索字幕…" id="q" oninput="doQ()"></div>
<div class="main">
  <div class="sl" id="sl"></div>
  <aside class="sp">
    <div class="np">
      <div class="np-lb">Now Playing</div>
      <div class="np-dc"><div class="np-dl"></div><div class="np-dd"></div><div class="np-dl"></div></div>
      <div class="np-tx" id="npTx">——</div>
      <div class="np-ix" id="npIx">— / {count}</div>
    </div>
    <div class="stats">
      <div class="sr"><span class="sr-l">总时长</span><span class="sr-v">{mins}分{secs}秒</span></div>
      <div class="sr"><span class="sr-l">字幕总数</span><span class="sr-v">{count:,}</span></div>
      <div class="sr"><span class="sr-l">当前进度</span><span class="sr-v" id="sPct">0%</span></div>
      <div class="sr"><span class="sr-l">当前时间</span><span class="sr-v" id="sTm">00:00:00</span></div>
      <div class="sr" id="sqR" style="display:none"><span class="sr-l">搜索结果</span><span class="sr-v" id="sqC">0</span></div>
    </div>
  </aside>
</div>
<div class="pw">
  <div class="td"><span id="tL">00:00:00</span><span id="tR">{fmt_time_full(total)}</span></div>
  <div class="pb" id="pb" onclick="seek(event)"><div class="pf" id="pf"></div></div>
</div>
<script>
const S={subs_js},DUR={total};
let cur=-1,aF=true,cpt=false,play=false,ct=0,lT=null;
const sl=document.getElementById('sl');
const fr=document.createDocumentFragment();
S.forEach((s,i)=>{{
  const d=document.createElement('div');d.className='si';d.id='i'+i;d.onclick=()=>jump(i);
  const ts=document.createElement('span');ts.className='st';ts.textContent=fmt(s.s);
  const tx=document.createElement('span');tx.className='sx';tx.textContent=s.t;
  d.appendChild(ts);d.appendChild(tx);fr.appendChild(d);
}});
sl.appendChild(fr);
function fmt(v){{const h=Math.floor(v/3600),m=Math.floor((v%3600)/60),s=Math.floor(v%60);return h>0?[h,m,s].map(x=>String(x).padStart(2,'0')).join(':'):[m,s].map(x=>String(x).padStart(2,'0')).join(':');}}
function fmtF(v){{const h=Math.floor(v/3600),m=Math.floor((v%3600)/60),s=Math.floor(v%60);return[h,m,s].map(x=>String(x).padStart(2,'0')).join(':');}}
function fi(t){{let lo=0,hi=S.length-1,r=-1;while(lo<=hi){{const mid=(lo+hi)>>1;if(S[mid].s<=t){{r=mid;lo=mid+1;}}else hi=mid-1;}}return r;}}
function act(idx){{
  if(idx===cur)return;
  if(cur>=0){{const e=document.getElementById('i'+cur);if(e)e.classList.remove('act');}}
  cur=idx;
  if(idx>=0){{const e=document.getElementById('i'+idx);if(e){{e.classList.add('act');if(aF)e.scrollIntoView({{behavior:'smooth',block:'center'}});}}
  document.getElementById('npTx').textContent=S[idx].t;document.getElementById('npIx').textContent=(idx+1)+' / '+S.length;}}
}}
function jump(i){{ct=S[i].s;act(i);upd();}}
function upd(){{const p=(ct/DUR)*100;document.getElementById('pf').style.width=p+'%';document.getElementById('tL').textContent=fmtF(ct);document.getElementById('sTm').textContent=fmtF(ct);document.getElementById('sPct').textContent=Math.round(p)+'%';}}
function seek(e){{const r=document.getElementById('pb').getBoundingClientRect();ct=Math.max(0,Math.min(1,(e.clientX-r.left)/r.width))*DUR;act(fi(ct));upd();play=true;lT=null;}}
function frame(ts){{if(play){{if(lT!==null){{ct+=(ts-lT)/1000;if(ct>DUR){{ct=DUR;play=false;}}act(fi(ct));upd();}}lT=ts;}}else lT=null;requestAnimationFrame(frame);}}
requestAnimationFrame(frame);
document.addEventListener('keydown',e=>{{if(e.target.tagName==='INPUT')return;if(e.code==='Space'){{e.preventDefault();play=!play;if(play)lT=null;}}if(e.code==='ArrowRight'){{ct=Math.min(DUR,ct+10);act(fi(ct));upd();}}if(e.code==='ArrowLeft'){{ct=Math.max(0,ct-10);act(fi(ct));upd();}}}});
function tA(){{aF=!aF;document.getElementById('btnA').classList.toggle('on',aF);}}
function tC(){{cpt=!cpt;document.getElementById('btnC').classList.toggle('on',cpt);document.querySelectorAll('.si').forEach(l=>{{l.style.paddingTop=cpt?'4px':'';l.style.paddingBottom=cpt?'4px':'';l.style.marginBottom=cpt?'0':'';}});document.querySelectorAll('.sx').forEach(t=>{{t.style.fontSize=cpt?'12.5px':'';}});}}
function doQ(){{const q=document.getElementById('q').value.trim();let cnt=0;document.querySelectorAll('.si').forEach((line,i)=>{{const tx=line.querySelector('.sx');if(q&&S[i].t.includes(q)){{line.classList.add('sm');const ps=S[i].t.split(q);tx.innerHTML='';ps.forEach((p,pi)=>{{tx.appendChild(document.createTextNode(p));if(pi<ps.length-1){{const mk=document.createElement('mark');mk.textContent=q;tx.appendChild(mk);}}}});cnt++;}}else{{line.classList.remove('sm');tx.textContent=S[i].t;}}}});const row=document.getElementById('sqR');if(q){{row.style.display='flex';document.getElementById('sqC').textContent=cnt+' 处';const f=document.querySelector('.sm');if(f)f.scrollIntoView({{behavior:'smooth',block:'center'}});}}else row.style.display='none';}}
</script>
</body>
</html>"""

# ── 首页 HTML ─────────────────────────────────────────────
def build_index(pages: list) -> str:
    """
    pages: [{"title": str, "filename": str, "count": int, "duration": float}, ...]
    """
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    total_pages = len(pages)

    cards_html = ""
    for p in sorted(pages, key=lambda x: x["title"]):
        dur_str  = fmt_duration(p["duration"])
        count    = f'{p["count"]:,}'
        # 取标题前两个字作装饰字符（fallback 到序号）
        deco = p["title"][:1] if p["title"] else "·"
        cards_html += f"""
    <a class="card" href="subtitle/{esc(p['filename'])}">
      <div class="card-deco">{esc(deco)}</div>
      <div class="card-body">
        <div class="card-title">{esc(p['title'])}</div>
        <div class="card-meta">
          <span>🕐 {esc(dur_str)}</span>
          <span>{esc(count)} 句</span>
        </div>
      </div>
      <div class="card-arrow">→</div>
    </a>"""

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>字幕收藏</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;500&family=Crimson+Pro:ital,wght@0,300;0,400;1,300&display=swap');
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#faf9f7;--bg2:#f3f1ed;--bg3:#ebe8e3;
  --border:rgba(0,0,0,.08);--border2:rgba(0,0,0,.12);
  --gold:#a67c52;--gold2:#8b6914;
  --text:#2c2a26;--text-dim:#6b6560;--text-mute:#9a9590;
  --hover:rgba(166,124,82,.08);
}}
html{{scroll-behavior:smooth}}
body{{background:var(--bg);color:var(--text);font-family:'Noto Serif SC','Songti SC',serif;min-height:100vh}}
body::before{{content:'';position:fixed;inset:0;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.03'/%3E%3C/svg%3E");pointer-events:none;z-index:0;opacity:.5}}

/* Hero - 标题与搜索同一行 */
.hero{{
  position:relative;z-index:1;
  padding:48px 60px 36px;
  border-bottom:1px solid var(--border);
  max-width:1100px;margin:0 auto;
  display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;
}}
.hero-left{{display:flex;align-items:center;gap:16px;flex-wrap:wrap;}}
.hero-label{{
  font-family:'Crimson Pro',serif;font-size:11px;font-style:italic;
  letter-spacing:.3em;text-transform:uppercase;
  color:var(--gold);opacity:.85;margin-right:12px;
}}
.hero-title{{
  font-size:clamp(24px,4vw,40px);font-weight:300;
  letter-spacing:.06em;line-height:1.3;color:var(--text);
  white-space:nowrap;
}}
.hero-deco{{display:flex;align-items:center;gap:12px;}}
.deco-line{{width:32px;height:1px;background:linear-gradient(to right,var(--gold),transparent);opacity:.5;}}
.deco-dot{{width:4px;height:4px;border-radius:50%;background:var(--gold);opacity:.6;}}

/* 搜索 - 右侧图标，点击展开输入框 */
.search-wrap{{
  display:flex;align-items:center;justify-content:flex-end;
}}
.search-btn{{
  display:inline-flex;align-items:center;justify-content:center;
  width:40px;height:40px;border:1px solid var(--border2);
  background:var(--bg2);border-radius:8px;cursor:pointer;
  color:var(--text-mute);transition:all .2s;
}}
.search-btn:hover{{border-color:var(--gold);color:var(--gold);background:var(--hover);}}
.search-btn svg{{width:18px;height:18px;}}
.search-input{{
  width:0;padding:0;border:none;outline:none;opacity:0;
  font-family:'Noto Serif SC',serif;font-size:13px;color:var(--text);
  background:var(--bg2);border-radius:6px;transition:width .2s,opacity .2s,margin .2s;
}}
.search-wrap.open .search-input{{
  width:160px;margin-left:8px;padding:8px 12px;
  border:1px solid var(--border2);opacity:1;
}}
.search-wrap.open .search-input:focus{{border-color:var(--gold);}}
.search-input::placeholder{{color:var(--text-mute);}}

/* Grid - 一行展示一个网页 */
.grid{{
  position:relative;z-index:1;
  max-width:1100px;margin:0 auto;
  padding:0 60px 80px;
  display:grid;
  grid-template-columns:1fr;
  gap:12px;
}}

/* Card */
.card{{
  display:flex;align-items:center;gap:16px;
  padding:20px 22px;
  background:var(--bg2);
  border:1px solid var(--border);
  border-radius:8px;
  text-decoration:none;
  transition:all .22s ease;
  cursor:pointer;
}}
.card:hover{{
  background:var(--hover);
  border-color:rgba(201,168,76,.3);
  transform:translateY(-2px);
  box-shadow:0 8px 32px rgba(0,0,0,.4);
}}
.card.hidden{{display:none;}}

.card-deco{{
  width:40px;height:40px;flex-shrink:0;
  border:1px solid var(--border2);border-radius:6px;
  display:flex;align-items:center;justify-content:center;
  font-size:18px;color:var(--gold);opacity:.7;
  font-weight:300;letter-spacing:0;
  font-family:'Noto Serif SC',serif;
  transition:opacity .2s;
}}
.card:hover .card-deco{{opacity:1;}}

.card-body{{flex:1;min-width:0;}}
.card-title{{
  font-size:14px;font-weight:400;letter-spacing:.04em;
  color:var(--text);line-height:1.4;margin-bottom:6px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}}
.card-meta{{
  display:flex;gap:12px;
  font-family:'Crimson Pro',serif;font-size:11px;
  color:var(--text-mute);letter-spacing:.05em;
}}

.card-arrow{{
  font-family:'Crimson Pro',serif;font-size:16px;
  color:var(--text-mute);flex-shrink:0;
  transition:all .2s;
}}
.card:hover .card-arrow{{color:var(--gold);transform:translateX(3px);}}

/* Empty */
.empty{{
  position:relative;z-index:1;
  text-align:center;padding:80px 20px;
  font-family:'Crimson Pro',serif;font-size:14px;
  color:var(--text-mute);font-style:italic;
}}

/* Footer - 底部展示统计与说明 */
footer{{
  position:relative;z-index:1;
  text-align:center;padding:40px 32px;
  font-family:'Crimson Pro',serif;font-size:11px;
  color:var(--text-mute);letter-spacing:.1em;
  border-top:1px solid var(--border);
  display:flex;flex-direction:column;gap:8px;align-items:center;
}}
footer .footer-desc{{color:var(--text-dim);}}
footer .footer-meta{{display:flex;gap:24px;flex-wrap:wrap;justify-content:center;}}

/* Curtain */
.curtain{{position:fixed;inset:0;background:var(--bg);z-index:9998;animation:cr 1s ease forwards .05s}}
@keyframes cr{{to{{opacity:0;pointer-events:none}}}}

@media(max-width:768px){{
  .hero,.grid{{padding-left:20px;padding-right:20px;}}
  .hero{{padding-top:36px;padding-bottom:28px;}}
  .hero-left{{flex-direction:column;align-items:flex-start;}}
  .hero-title{{white-space:normal;}}
  .grid{{grid-template-columns:1fr;}}
}}
</style>
</head>
<body>
<div class="curtain"></div>

<div class="hero">
  <div class="hero-left">
    <span class="hero-label">字幕收藏</span>
    <div class="hero-title">字幕阅读 归档</div>
    <div class="hero-deco">
      <div class="deco-line"></div>
      <div class="deco-dot"></div>
    </div>
  </div>
  <div class="search-wrap" id="searchWrap">
    <button type="button" class="search-btn" id="searchBtn" title="搜索标题" aria-label="搜索">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
    </button>
    <input class="search-input" type="text" id="searchBox" placeholder="搜索标题…" oninput="filterCards()">
  </div>
</div>

{"<div class='grid' id='grid'>" + cards_html + "</div>" if pages else "<div class='empty'>暂无字幕页面，上传字幕文件后自动生成</div>"}

<footer>
  <div class="footer-desc">所有字幕页面，由 GitHub Actions 自动生成</div>
  <div class="footer-meta">
    <span id="totalPages">{total_pages} 篇内容</span>
    <span>{now} 最后更新</span>
  </div>
  <div>Subtitle2html</div>
</footer>

<script>
function filterCards() {{
  const q = document.getElementById('searchBox').value.trim().toLowerCase();
  document.querySelectorAll('.card').forEach(card => {{
    const title = card.querySelector('.card-title').textContent.toLowerCase();
    card.classList.toggle('hidden', q !== '' && !title.includes(q));
  }});
  const visible = document.querySelectorAll('.card:not(.hidden)').length;
  document.getElementById('totalPages').textContent = (q ? visible : {total_pages}) + ' 篇内容';
}}
document.getElementById('searchBtn').onclick = function() {{
  var wrap = document.getElementById('searchWrap');
  wrap.classList.toggle('open');
  if (wrap.classList.contains('open')) document.getElementById('searchBox').focus();
}};
</script>
</body>
</html>"""

# ──  rebuild index from subtitle/ folder ──────────────────
def rebuild_index_from_subtitle_dir() -> None:
    """扫描 subtitle/ 下所有 HTML，重新生成 index.html"""
    pages = []
    for html_file in OUTPUT_DIR.glob("*.html"):
        try:
            content = html_file.read_text(encoding="utf-8", errors="replace")
            title_m = re.search(r"<title>(.*?)</title>", content)
            title   = title_m.group(1) if title_m else html_file.stem
            count_m = re.search(r"(\d[\d,]+)\s*句字幕", content)
            dur_m   = re.search(r"(\d+)分(\d+)秒", content)
            count   = int((count_m.group(1) if count_m else "0").replace(",", ""))
            dur     = (int(dur_m.group(1)) * 60 + int(dur_m.group(2))) if dur_m else 0
            pages.append({
                "title":    title,
                "filename": html_file.name,
                "count":    count,
                "duration": float(dur),
            })
        except Exception:
            pages.append({
                "title":    html_file.stem,
                "filename": html_file.name,
                "count":    0,
                "duration": 0.0,
            })
    INDEX_PATH.write_text(build_index(pages), encoding="utf-8")


# ── 主逻辑 ────────────────────────────────────────────────
def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 1. 生成字幕页面
    subtitle_files = sorted([
        f for f in SUBTITLES_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXT
    ])

    pages = []
    ok = 0

    if not subtitle_files:
        print("subtitles/ 文件夹下没有找到字幕文件，跳过字幕页生成。")
    else:
        for src in subtitle_files:
            out_name = derive_output_name(src.stem)
            out_path = OUTPUT_DIR / out_name
            title    = derive_title(src.stem)

            print(f"处理: {src.name}  →  subtitle/{out_name}")
            try:
                subs = parse_file(src)
                if not subs:
                    print(f"  ⚠ 未解析到字幕，跳过")
                    continue
                html = build_html(subs, title)
                out_path.write_text(html, encoding="utf-8")
                pages.append({
                    "title":    title,
                    "filename": out_name,
                    "count":    len(subs),
                    "duration": subs[-1]["e"],
                })
                print(f"  ✓ {len(subs)} 句，已写入 {out_path}")
                ok += 1
            except Exception as e:
                print(f"  ✗ 失败: {e}")

        print(f"\n字幕页：{ok}/{len(subtitle_files)} 生成成功")

    # 2. 生成首页（扫描 subtitle/ 下所有 HTML）
    print(f"\n生成首页 index.html...")
    rebuild_index_from_subtitle_dir()
    print("✓ index.html 已生成")

if __name__ == "__main__":
    main()
