#!/usr/bin/env python3
"""Render Playbook.md into a self-contained, searchable HTML artifact.

Usage:
    python3 Scripts/playbook_html.py [SRC.md] [OUT.html]

Defaults: repo-root Playbook.md -> repo-root Playbook.html
(repo root is resolved as the parent dir of this script's Scripts/ folder).
"""
import re, html, json, sys, os

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_REPO, "Playbook.md")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(_REPO, "Playbook.html")

# ---- phase hue map (semantic: the kill-chain stage) ----
PHASE_META = {
    "0":  ("#8a95a5", "Setup"),
    "1":  ("#38bdf8", "Recon"),
    "2":  ("#f59e0b", "Access"),
    "3":  ("#60a5fa", "Awareness"),
    "4":  ("#f97316", "PrivEsc"),
    "5":  ("#a78bfa", "Creds"),
    "6":  ("#eab308", "AD"),
    "7":  ("#34d399", "Lateral"),
    "8":  ("#2dd4bf", "Pivot"),
    "9":  ("#f472b6", "Exfil"),
    "10": ("#c084fc", "Persist"),
    "11": ("#3b82f6", "Blue"),
    "12": ("#94a3b8", "Toolbox"),
    "13": ("#22d3ee", "Cloud"),
    "14": ("#fb7185", "Report"),
    "A":  ("#8a95a5", "Keys"),
    "B":  ("#ef4444", "OSCP"),
    "C":  ("#10b981", "Medtech"),
}

def esc(s):
    return html.escape(s, quote=True)

def inline(s):
    """Inline markdown: escape, then code / bold / links."""
    # protect inline code spans first
    spans = []
    def stash(m):
        spans.append(m.group(1))
        return f"\x00{len(spans)-1}\x00"
    s = re.sub(r"`([^`]+)`", stash, s)
    s = esc(s)
    # bold
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    # links [text](url)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)",
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    # bare urls
    s = re.sub(r"(?<![\">=])(https?://[^\s<)]+)",
               r'<a href="\1" target="_blank" rel="noopener">\1</a>', s)
    # restore code spans
    def unstash(m):
        return "<code>" + esc(spans[int(m.group(1))]) + "</code>"
    s = re.sub(r"\x00(\d+)\x00", unstash, s)
    return s

def slugify(t):
    t = re.sub(r"[^\w\s-]", "", t.lower())
    return re.sub(r"[\s]+", "-", t.strip())[:60]

# ---- parse ----
with open(SRC) as f:
    lines = f.read().split("\n")

def clean_heading(txt):
    # strip leading emoji / symbols
    return re.sub(r"^[^\w]*", "", txt).strip()

# classify a heading -> ('phase', key, title) | ('sub', title) | ('leaf', title, level) | None(title page)
def classify(hashes, txt):
    c = clean_heading(txt)
    mphase = re.match(r"^(\d{1,2})\.\s+\S", c)
    msub   = re.match(r"^(\d{1,2})\.(\d{1,2})\b", c)
    mappx  = re.match(r"^Appendix\s+([ABC])\b", c)
    mbsub  = re.match(r"^B\.(\d+)\b", c)
    mcsub  = re.match(r"^C\.(\d+)\b", c)
    if "Spis treści" in txt or "📑" in txt:
        return ("skip",)
    if msub:
        return ("sub", txt)
    if mbsub:
        return ("sub", txt)
    if mcsub:
        return ("sub", txt)
    if mphase:
        return ("phase", mphase.group(1), txt)
    if mappx:
        return ("phase", mappx.group(1), txt)
    if hashes == 1 and ("Playbook" in txt):
        return ("title", txt)
    return ("leaf", txt, hashes)

phases = []          # list of dicts
cur_phase = None
cur_card = None
page_title = "Pentest Playbook"
i = 0
N = len(lines)

def new_card(kind="body", heading=None, hid=None):
    return {"kind": kind, "heading": heading, "hid": hid, "html": [], "text": []}

def push_card():
    global cur_card
    if cur_card and (cur_card["html"] or cur_card["heading"]):
        cur_phase["cards"].append(cur_card)
    cur_card = None

def emit(h, t=""):
    if cur_card is None:
        return
    cur_card["html"].append(h)
    if t:
        cur_card["text"].append(t)

while i < N:
    line = lines[i]
    hm = re.match(r"^(#{1,4})\s+(.*)$", line)
    if hm:
        hashes = len(hm.group(1)); txt = hm.group(2).strip()
        cls = classify(hashes, txt)
        if cls[0] == "skip":
            # skip until next heading
            i += 1
            while i < N and not re.match(r"^#{1,4}\s", lines[i]):
                i += 1
            continue
        if cls[0] == "title":
            page_title = clean_heading(txt)
            i += 1
            # skip following blockquote/intro until first phase
            continue
        if cls[0] == "phase":
            push_card()
            key = cls[1]
            color, short = PHASE_META.get(key, ("#8a95a5", ""))
            title = clean_heading(txt)
            slug = "p" + slugify(title)
            cur_phase = {"key": key, "title": title, "slug": slug,
                         "color": color, "short": short, "subs": [], "cards": []}
            phases.append(cur_phase)
            cur_card = new_card("intro")
            i += 1
            continue
        if cls[0] == "sub":
            push_card()
            title = clean_heading(txt)
            hid = cur_phase["slug"] + "-" + slugify(title)
            cur_phase["subs"].append({"title": title, "hid": hid})
            cur_card = new_card("sub", heading=title, hid=hid)
            emit("", title)
            i += 1
            continue
        if cls[0] == "leaf":
            lvl = cls[2]
            title = clean_heading(txt)
            if cur_card is None:
                cur_card = new_card("body")
            tag = "h4" if lvl <= 3 else "h5"
            emit(f'<{tag} class="leaf">{inline(title)}</{tag}>', title)
            i += 1
            continue
    # code fence
    if re.match(r"^```", line):
        lang = line.strip()[3:].strip()
        code = []
        i += 1
        while i < N and not lines[i].startswith("```"):
            code.append(lines[i]); i += 1
        i += 1  # skip closing fence
        raw = "\n".join(code)
        emit(f'<div class="code"><button class="copy" type="button" aria-label="Kopiuj">'
             f'<span class="ico">⧉</span><span class="lbl">copy</span></button>'
             f'<pre><code>{esc(raw)}</code></pre></div>', raw)
        continue
    # table
    if line.strip().startswith("|") and i+1 < N and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i+1]):
        header = [c.strip() for c in line.strip().strip("|").split("|")]
        i += 2
        rows = []
        while i < N and lines[i].strip().startswith("|"):
            rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
            i += 1
        th = "".join(f"<th>{inline(c)}</th>" for c in header)
        trs = ""
        for r in rows:
            tds = "".join(f"<td>{inline(c)}</td>" for c in r)
            trs += f"<tr>{tds}</tr>"
        emit(f'<div class="tblwrap"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>',
             " ".join(header) + " " + " ".join(" ".join(r) for r in rows))
        continue
    # blockquote (collect consecutive)
    if line.startswith(">"):
        buf = []
        while i < N and lines[i].startswith(">"):
            buf.append(lines[i][1:].lstrip()); i += 1
        text = " ".join(x for x in buf if x)
        emit(f'<blockquote>{inline(text)}</blockquote>', text)
        continue
    # list (collect consecutive - and * and numbered)
    if re.match(r"^\s*([-*]|\d+\.)\s+", line):
        items = []
        while i < N and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
            it = re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i])
            items.append(it); i += 1
        lis = "".join(f"<li>{inline(it)}</li>" for it in items)
        emit(f"<ul>{lis}</ul>", " ".join(items))
        continue
    # horizontal rule
    if re.match(r"^---+\s*$", line):
        i += 1
        continue
    # blank
    if line.strip() == "":
        i += 1
        continue
    # paragraph
    para = [line]
    i += 1
    while i < N and lines[i].strip() != "" and not re.match(r"^(#{1,4}\s|```|>|\s*([-*]|\d+\.)\s|---+\s*$|\|)", lines[i]):
        para.append(lines[i]); i += 1
    text = " ".join(para)
    emit(f"<p>{inline(text)}</p>", text)

push_card()

# ---- build HTML ----
def card_text(card):
    return " ".join(card["text"]).lower()

nav_html = []
main_html = []
for p in phases:
    # nav
    subs = "".join(
        f'<a class="nav-sub" href="#{s["hid"]}">{esc(s["title"])}</a>' for p_ in [p] for s in p["subs"]
    )
    nav_html.append(
        f'<div class="nav-phase" data-phase="{p["slug"]}" style="--hue:{p["color"]}">'
        f'<a class="nav-top" href="#{p["slug"]}"><span class="dot"></span>'
        f'<span class="ntxt">{esc(p["title"])}</span></a>'
        f'<div class="nav-subs">{subs}</div></div>'
    )
    # main
    cards_html = []
    for c in p["cards"]:
        dt = esc(card_text(c))
        head = ""
        cid = ""
        if c["kind"] == "sub" and c["heading"]:
            cid = f' id="{c["hid"]}"'
            head = f'<h3 class="card-h">{inline(c["heading"])}</h3>'
        body = "\n".join(x for x in c["html"] if x)
        if not body and not head:
            continue
        cards_html.append(
            f'<section class="card" data-text="{dt}"{cid}>{head}{body}</section>'
        )
    disp = re.sub(r"^\d+\.\s*", "", p["title"])
    disp = re.sub(r"^Appendix\s+[ABC]\s*[—-]\s*", "", disp)
    main_html.append(
        f'<section class="phase" id="{p["slug"]}" data-phase="{p["slug"]}" style="--hue:{p["color"]}">'
        f'<header class="phase-head">'
        f'<button class="collapse" type="button" aria-label="Zwiń"></button>'
        f'<span class="badge">{esc(p["key"])}</span>'
        f'<h2>{esc(disp)}</h2>'
        f'<span class="tag">{esc(p["short"])}</span>'
        f'</header>'
        f'<div class="phase-body">{"".join(cards_html)}</div>'
        f'</section>'
    )

TEMPLATE = r"""<title>__TITLE__</title>
<style>
:root{
  --bg:#0e1116; --surface:#161b22; --surface-2:#1b222c; --border:#232b36;
  --text:#d4dae2; --muted:#8a95a5; --faint:#5b6572;
  --accent:#56b6c2; --accent-soft:#56b6c233;
  --code-bg:#0b0e13; --code-text:#c8d3de; --code-kw:#7ee0ef;
  --font-mono:ui-monospace,"Cascadia Code","JetBrains Mono","SF Mono",Menlo,Consolas,monospace;
  --font-sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --shadow:0 1px 0 #ffffff08,0 8px 24px #00000040;
  color-scheme:dark;
}
@media (prefers-color-scheme:light){:root{
  --bg:#f4f6f9; --surface:#ffffff; --surface-2:#f0f3f7; --border:#dbe1ea;
  --text:#1a2230; --muted:#5a6675; --faint:#9aa5b3;
  --accent:#0f8ea0; --accent-soft:#0f8ea01a;
  --code-bg:#0e1420; --code-text:#d3ddea; --code-kw:#7ee0ef;
  --shadow:0 1px 2px #1a223010,0 8px 24px #1a223012; color-scheme:light;
}}
:root[data-theme="dark"]{
  --bg:#0e1116; --surface:#161b22; --surface-2:#1b222c; --border:#232b36;
  --text:#d4dae2; --muted:#8a95a5; --faint:#5b6572;
  --accent:#56b6c2; --accent-soft:#56b6c233; --code-bg:#0b0e13; --code-text:#c8d3de;
  --shadow:0 1px 0 #ffffff08,0 8px 24px #00000040; color-scheme:dark;
}
:root[data-theme="light"]{
  --bg:#f4f6f9; --surface:#ffffff; --surface-2:#f0f3f7; --border:#dbe1ea;
  --text:#1a2230; --muted:#5a6675; --faint:#9aa5b3;
  --accent:#0f8ea0; --accent-soft:#0f8ea01a; --code-bg:#0e1420; --code-text:#d3ddea;
  --shadow:0 1px 2px #1a223010,0 8px 24px #1a223012; color-scheme:light;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--font-sans);
  font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}

/* ---- layout ---- */
.wrap{display:grid;grid-template-columns:262px 1fr;min-height:100vh}
.sidebar{position:sticky;top:0;height:100vh;overflow-y:auto;border-right:1px solid var(--border);
  background:var(--surface);padding:0}
.brand{padding:18px 18px 12px;border-bottom:1px solid var(--border);position:sticky;top:0;
  background:var(--surface);z-index:2}
.brand .k{font-family:var(--font-mono);font-size:11px;letter-spacing:.22em;text-transform:uppercase;
  color:var(--accent)}
.brand h1{font-family:var(--font-mono);font-size:15px;margin:6px 0 0;font-weight:600;letter-spacing:-.01em}
.brand .sub{color:var(--muted);font-size:11.5px;margin-top:3px;font-family:var(--font-mono)}
nav{padding:8px 8px 40px}
.nav-phase{margin:1px 0}
.nav-top{display:flex;align-items:center;gap:9px;padding:6px 10px;border-radius:7px;color:var(--text);
  font-family:var(--font-mono);font-size:12.5px;font-weight:500}
.nav-top:hover{background:var(--surface-2);text-decoration:none}
.nav-top .dot{width:8px;height:8px;border-radius:2px;background:var(--hue);flex:none;
  box-shadow:0 0 0 3px color-mix(in srgb,var(--hue) 18%,transparent)}
.nav-phase.active>.nav-top{background:var(--surface-2)}
.nav-phase.active>.nav-top .ntxt{color:var(--hue)}
.nav-subs{display:none;flex-direction:column;padding:2px 0 6px 27px;gap:1px}
.nav-phase.active .nav-subs{display:flex}
.nav-sub{color:var(--muted);font-size:11.5px;padding:3px 8px;border-left:1px solid var(--border);
  border-radius:0 5px 5px 0;font-family:var(--font-sans)}
.nav-sub:hover{color:var(--text);border-left-color:var(--hue);background:var(--surface-2);text-decoration:none}

.main{min-width:0}
.topbar{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:12px;
  padding:12px 26px;background:color-mix(in srgb,var(--bg) 82%,transparent);
  backdrop-filter:blur(10px);border-bottom:1px solid var(--border)}
.search{position:relative;flex:1;max-width:560px}
.search input{width:100%;padding:9px 34px 9px 34px;border-radius:9px;border:1px solid var(--border);
  background:var(--surface);color:var(--text);font-family:var(--font-mono);font-size:13px;outline:none}
.search input:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.search .si{position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--faint);font-size:13px}
.search kbd{position:absolute;right:9px;top:50%;transform:translateY(-50%);font-family:var(--font-mono);
  font-size:10px;color:var(--faint);border:1px solid var(--border);border-radius:4px;padding:1px 5px}
.count{font-family:var(--font-mono);font-size:11.5px;color:var(--muted);white-space:nowrap}
.spacer{flex:1}
.tbtn{display:flex;align-items:center;gap:6px;background:var(--surface);border:1px solid var(--border);
  color:var(--muted);border-radius:8px;padding:8px 11px;cursor:pointer;font-family:var(--font-mono);font-size:12px}
.tbtn:hover{color:var(--text);border-color:var(--accent)}

.content{padding:26px 26px 120px;max-width:1000px}
.phase{margin:0 0 30px;scroll-margin-top:70px}
.phase-head{display:flex;align-items:center;gap:12px;padding:11px 0 12px;border-bottom:2px solid var(--hue);
  margin-bottom:16px;position:sticky;top:57px;background:var(--bg);z-index:3}
.phase-head .badge{font-family:var(--font-mono);font-weight:700;font-size:12.5px;color:#0b0e13;
  background:var(--hue);min-width:26px;height:26px;display:grid;place-items:center;border-radius:7px;padding:0 6px}
.phase-head h2{font-family:var(--font-mono);font-size:19px;margin:0;font-weight:600;letter-spacing:-.01em;flex:1}
.phase-head .tag{font-family:var(--font-mono);font-size:10.5px;text-transform:uppercase;letter-spacing:.14em;
  color:var(--hue);border:1px solid color-mix(in srgb,var(--hue) 40%,var(--border));border-radius:20px;padding:3px 10px}
.collapse{width:22px;height:22px;border:none;background:transparent;cursor:pointer;color:var(--muted);
  position:relative;flex:none}
.collapse::before{content:"";position:absolute;inset:0;margin:auto;width:7px;height:7px;
  border-right:2px solid currentColor;border-bottom:2px solid currentColor;transform:rotate(45deg);transition:transform .18s}
.phase.collapsed .collapse::before{transform:rotate(-45deg)}
.phase.collapsed .phase-body{display:none}

.phase-body{display:flex;flex-direction:column;gap:14px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px 18px;
  box-shadow:var(--shadow);scroll-margin-top:110px}
.card.intro{background:transparent;border:none;box-shadow:none;padding:2px 0}
.card-h{font-family:var(--font-mono);font-size:14.5px;margin:0 0 10px;font-weight:600;
  color:var(--text);display:flex;align-items:center;gap:8px}
.card-h::before{content:"";width:3px;height:15px;background:var(--hue);border-radius:2px;flex:none}
.card p{margin:9px 0}
.card h4.leaf{font-family:var(--font-mono);font-size:13px;margin:15px 0 7px;color:var(--accent);font-weight:600}
.card h5.leaf{font-family:var(--font-mono);font-size:12px;margin:12px 0 6px;color:var(--muted);
  text-transform:uppercase;letter-spacing:.08em;font-weight:600}
.card ul{margin:8px 0;padding-left:20px}
.card li{margin:3px 0}
:not(pre)>code{font-family:var(--font-mono);font-size:.86em;background:var(--surface-2);
  border:1px solid var(--border);border-radius:5px;padding:.08em .4em;color:var(--accent);word-break:break-word}
blockquote{margin:11px 0;padding:10px 14px;background:var(--accent-soft);
  border-left:3px solid var(--accent);border-radius:0 8px 8px 0;color:var(--text);font-size:14px}
blockquote code{background:transparent;border:none;color:inherit;padding:0}

/* ---- code blocks ---- */
.code{position:relative;margin:10px 0}
.code pre{margin:0;background:var(--code-bg);border:1px solid var(--border);border-radius:9px;
  padding:13px 15px;overflow-x:auto}
.code code{font-family:var(--font-mono);font-size:12.6px;line-height:1.65;color:var(--code-text);white-space:pre}
.copy{position:absolute;top:8px;right:8px;display:flex;align-items:center;gap:5px;
  background:var(--surface);border:1px solid var(--border);color:var(--muted);border-radius:7px;
  padding:4px 8px;cursor:pointer;font-family:var(--font-mono);font-size:10.5px;opacity:0;transition:opacity .15s}
.code:hover .copy,.copy:focus{opacity:1}
.copy:hover{color:var(--accent);border-color:var(--accent)}
.copy.done{color:#34d399;border-color:#34d39955}
.copy .ico{font-size:12px}

.tblwrap{overflow-x:auto;margin:11px 0}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border:1px solid var(--border);padding:7px 11px;text-align:left;vertical-align:top}
th{background:var(--surface-2);font-family:var(--font-mono);font-size:11.5px;text-transform:uppercase;
  letter-spacing:.05em;color:var(--muted);font-weight:600}
td code{white-space:nowrap}

.noresults{display:none;text-align:center;padding:60px 20px;color:var(--muted);font-family:var(--font-mono)}
.noresults.on{display:block}
mark{background:color-mix(in srgb,var(--accent) 32%,transparent);color:inherit;border-radius:2px;padding:0 1px}

.mobtogg{display:none}
@media (max-width:860px){
  .wrap{grid-template-columns:1fr}
  .sidebar{position:fixed;left:0;top:0;width:262px;z-index:20;transform:translateX(-100%);transition:transform .22s}
  .sidebar.open{transform:none}
  .mobtogg{display:flex}
  .content{padding:18px 15px 100px}
  .phase-head{top:56px}
  .search kbd{display:none}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
.scrim{display:none}
@media (max-width:860px){.scrim.on{display:block;position:fixed;inset:0;background:#0008;z-index:15}}
</style>

<div class="wrap">
  <aside class="sidebar" id="sidebar">
    <div class="brand">
      <div class="k">kill chain</div>
      <h1>Pentest Playbook</h1>
      <div class="sub">recon → root · OSCP ready</div>
    </div>
    <nav id="nav">__NAV__</nav>
  </aside>
  <div class="scrim" id="scrim"></div>

  <div class="main">
    <div class="topbar">
      <button class="tbtn mobtogg" id="menuBtn" aria-label="Menu">☰</button>
      <div class="search">
        <span class="si">⌕</span>
        <input id="q" type="search" placeholder="Szukaj komend, technik, narzędzi…" autocomplete="off" spellcheck="false">
        <kbd>/</kbd>
      </div>
      <span class="count" id="count"></span>
      <span class="spacer"></span>
      <button class="tbtn" id="themeBtn" aria-label="Motyw"><span id="themeIco">◐</span><span>motyw</span></button>
    </div>
    <div class="content">
      __MAIN__
      <div class="noresults" id="noresults">Brak wyników — spróbuj innej frazy.</div>
    </div>
  </div>
</div>

<script>
(function(){
  "use strict";
  // ---- copy buttons ----
  document.querySelectorAll(".copy").forEach(function(btn){
    btn.addEventListener("click",function(){
      var code=btn.parentElement.querySelector("code").textContent;
      navigator.clipboard.writeText(code).then(function(){
        btn.classList.add("done");
        var l=btn.querySelector(".lbl"); var prev=l.textContent; l.textContent="ok";
        setTimeout(function(){btn.classList.remove("done");l.textContent=prev;},1100);
      });
    });
  });

  // ---- theme toggle ----
  var root=document.documentElement, tb=document.getElementById("themeBtn");
  function cur(){var t=root.getAttribute("data-theme");if(t)return t;
    return matchMedia("(prefers-color-scheme:dark)").matches?"dark":"light";}
  tb.addEventListener("click",function(){
    var n=cur()==="dark"?"light":"dark"; root.setAttribute("data-theme",n);
    document.getElementById("themeIco").textContent=n==="dark"?"◐":"◑";
  });

  // ---- collapse phases ----
  document.querySelectorAll(".collapse").forEach(function(b){
    b.addEventListener("click",function(e){e.stopPropagation();
      b.closest(".phase").classList.toggle("collapsed");});
  });

  // ---- search / filter ----
  var q=document.getElementById("q"), cards=[].slice.call(document.querySelectorAll(".card")),
      phases=[].slice.call(document.querySelectorAll(".phase")),
      countEl=document.getElementById("count"), noRes=document.getElementById("noresults"),
      total=cards.length;
  function setCount(n){countEl.textContent=n===total?(total+" bloków"):(n+" / "+total);}
  setCount(total);
  var t=null;
  function run(){
    var term=q.value.trim().toLowerCase();
    var shown=0;
    cards.forEach(function(c){
      var hit=!term||c.getAttribute("data-text").indexOf(term)>-1;
      c.style.display=hit?"":"none"; if(hit)shown++;
    });
    phases.forEach(function(p){
      var any=p.querySelector('.card:not([style*="display: none"])');
      // recount visible cards inside
      var vis=[].slice.call(p.querySelectorAll(".card")).some(function(c){return c.style.display!=="none";});
      p.style.display=(!term||vis)?"":"none";
      if(term&&vis)p.classList.remove("collapsed");
    });
    noRes.classList.toggle("on",term&&shown===0);
    setCount(term?shown:total);
  }
  q.addEventListener("input",function(){clearTimeout(t);t=setTimeout(run,90);});
  // "/" focuses search; Esc clears
  document.addEventListener("keydown",function(e){
    if(e.key==="/"&&document.activeElement!==q){e.preventDefault();q.focus();}
    if(e.key==="Escape"&&document.activeElement===q){q.value="";run();q.blur();}
  });

  // ---- scrollspy ----
  var navPhases={};
  document.querySelectorAll(".nav-phase").forEach(function(n){navPhases[n.getAttribute("data-phase")]=n;});
  var obs=new IntersectionObserver(function(entries){
    entries.forEach(function(en){
      if(en.isIntersecting){
        var id=en.target.getAttribute("data-phase");
        Object.keys(navPhases).forEach(function(k){navPhases[k].classList.toggle("active",k===id);});
      }
    });
  },{rootMargin:"-15% 0px -75% 0px",threshold:0});
  phases.forEach(function(p){obs.observe(p);});

  // ---- mobile menu ----
  var sb=document.getElementById("sidebar"), scrim=document.getElementById("scrim");
  document.getElementById("menuBtn").addEventListener("click",function(){
    sb.classList.add("open");scrim.classList.add("on");});
  scrim.addEventListener("click",function(){sb.classList.remove("open");scrim.classList.remove("on");});
  document.getElementById("nav").addEventListener("click",function(e){
    if(e.target.closest("a")){sb.classList.remove("open");scrim.classList.remove("on");}});
})();
</script>
"""

out = (TEMPLATE
       .replace("__TITLE__", esc(page_title))
       .replace("__NAV__", "".join(nav_html))
       .replace("__MAIN__", "".join(main_html)))

with open(OUT, "w") as f:
    f.write(out)

print(f"wrote {OUT}: {len(out)} bytes, {len(phases)} phases, {sum(len(p['cards']) for p in phases)} cards")
