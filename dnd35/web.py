"""Online play: a tiny web server so remote players share one live game table.

    python -m dnd35.web --port 8080

Everyone who opens the page sees the same GM output in real time and can click
menu choices or type answers. There's also a chat sidebar and a "who's here"
list. Standard library only (no installs), so it runs anywhere, including Fly.io.

Environment variables:
    PORT              port to listen on (default 8080)
    TABLE_PASSWORD    if set, players must enter this password to join
    DND35_SAVE_DIR    where save files go (use a persistent volume on Fly.io)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List, Optional, Sequence
from urllib.parse import parse_qs, urlparse

from .ui import UI, Color, QuitGame, c

MAX_EVENTS = 4000
POLL_SECONDS = 25
ANSI_RE = re.compile(r"\033\[[0-9;]*m")
SPEECH_RE = re.compile(r"^([A-Z][\w' .-]{0,30}): \u201c(.*)\u201d$")


class WebUI(UI):
    """A UI whose screen is an event log shared by every connected browser."""

    def __init__(self, table: "Table"):
        super().__init__()
        self.table = table
        self._pending_options: Optional[List[str]] = None
        self._pending_kind = "text"

    # output -> events
    def out(self, text: str = "", style: Sequence[str] = ()) -> None:
        line = c(text, *style) if style else str(text)
        self.table.emit({"t": "line", "text": line})

    # narration (read aloud by browsers that turn the narrator on)
    def para(self, text: str, style: Sequence[str] = (), indent: str = "") -> None:
        plain = " ".join(str(text).split())
        if plain and ("bcyan" in style or "bmagenta" in style or "byellow" in style):
            m = SPEECH_RE.match(plain)
            if m:
                self.table.emit({"t": "narrate", "kind": "npc", "who": m.group(1),
                                 "text": m.group(2)})
            else:
                self.table.emit({"t": "narrate", "kind": "gm", "text": plain})
        super().para(text, style, indent)

    def header(self, text: str) -> None:
        title = text.strip()
        if title and not title.startswith(("TABLE", "NEW GAME", "HERO ")):
            words = " ".join(w.capitalize() for w in title.lower().split())
            self.table.emit({"t": "narrate", "kind": "title", "text": words + "."})
        super().header(text)

    # input <- browser
    def _raw_input(self, prompt: str) -> str:
        opts = self._pending_options
        kind = self._pending_kind
        self.table.emit({"t": "prompt", "text": ANSI_RE.sub("", prompt), "options": opts,
                         "kind": kind})
        text, who = self.table.wait_input()
        shown = text if text else "(enter)"
        self.table.emit({"t": "line", "text": c(f"> {shown}", "bold") +
                         (c(f"   ({who})", "dim") if who else "")})
        if text.strip().lower() in ("/quit", "/exit"):
            return ""  # nobody can kill the shared table from a browser
        return text

    def choose(self, prompt, options, allow_cancel=False, default=None):
        if options:
            opts = [ANSI_RE.sub("", o) for o in options]
            if allow_cancel:
                opts = opts + ["(back)"]
            return self._with_options(opts, "choose", super().choose, prompt, options,
                                      allow_cancel, default)
        return super().choose(prompt, options, allow_cancel, default)

    def confirm(self, prompt, default=True):
        return self._with_options(["Yes", "No"], "confirm", super().confirm, prompt, default)

    def pause(self):
        return self._with_options(["Continue"], "pause", super().pause)

    def ask(self, prompt, default=None):
        if self._pending_kind == "text":
            self._pending_options = None
        return super().ask(prompt, default)

    def _with_options(self, opts, kind, fn, *args):
        prev = (self._pending_options, self._pending_kind)
        self._pending_options, self._pending_kind = opts, kind
        try:
            return fn(*args)
        finally:
            self._pending_options, self._pending_kind = prev


class Table:
    """One shared game. Runs the normal game loop in a background thread."""

    def __init__(self, name: str):
        self.name = name
        self.events: List[dict] = []
        self.first_seq = 0
        self.seq = 0
        self.cond = threading.Condition()
        self.inputs: List[tuple] = []
        self.waiting = False
        self.presence: Dict[str, float] = {}
        self.ui = WebUI(self)
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def emit(self, ev: dict) -> None:
        with self.cond:
            ev["seq"] = self.seq
            self.seq += 1
            self.events.append(ev)
            if len(self.events) > MAX_EVENTS:
                drop = len(self.events) - MAX_EVENTS
                del self.events[:drop]
                self.first_seq = self.events[0]["seq"]
            self.cond.notify_all()

    def wait_input(self):
        with self.cond:
            self.waiting = True
            while not self.inputs:
                self.cond.wait()
            self.waiting = False
            return self.inputs.pop(0)

    def submit(self, text: str, who: str) -> bool:
        with self.cond:
            if not self.waiting:
                return False
            self.inputs.append((text[:200], who[:30]))
            self.cond.notify_all()
            return True

    def chat(self, text: str, who: str) -> None:
        self.emit({"t": "chat", "who": who[:30], "text": text[:500]})

    def poll(self, since: int, who: str, timeout: float = POLL_SECONDS) -> dict:
        if who:
            self.presence[who[:30]] = time.time()
        deadline = time.time() + timeout
        with self.cond:
            while self.seq <= since and time.time() < deadline:
                self.cond.wait(timeout=max(0.1, deadline - time.time()))
            start = max(since, self.first_seq)
            evs = [e for e in self.events if e["seq"] >= start]
            now = time.time()
            here = sorted(n for n, t in self.presence.items() if now - t < POLL_SECONDS + 10)
            return {"events": evs, "next": self.seq, "here": here, "waiting": self.waiting,
                    "reset": since < self.first_seq}

    def _run(self) -> None:
        from .game import main_menu
        Color.enabled = True
        while True:
            try:
                self.ui.header(f"TABLE '{self.name}' IS OPEN")
                self.ui.para("Everyone at this table sees the same game. Click a choice or "
                             "type an answer. In combat, the game names whose turn it is; "
                             "that player should answer. Use the chat box to talk.")
                main_menu(self.ui)
            except QuitGame:
                pass
            except Exception:  # keep the table alive no matter what
                self.ui.out("The GM fumbled the dice (internal error). Restarting the "
                            "main menu; load the autosave to continue.", ("bred",))
                self.ui.out(traceback.format_exc(), ("dim",))
            time.sleep(0.5)


TABLES: Dict[str, Table] = {}
TABLES_LOCK = threading.Lock()


def get_table(name: str) -> Table:
    name = re.sub(r"[^a-zA-Z0-9_-]", "", name)[:32] or "main"
    with TABLES_LOCK:
        if name not in TABLES:
            TABLES[name] = Table(name)
        return TABLES[name]


class Handler(BaseHTTPRequestHandler):
    server_version = "dnd35/1"

    def log_message(self, fmt, *args):  # quieter logs
        if os.environ.get("DND35_VERBOSE"):
            super().log_message(fmt, *args)

    def _auth(self, qs) -> bool:
        pw = os.environ.get("TABLE_PASSWORD")
        if not pw:
            return True
        given = self.headers.get("X-Password") or qs.get("pw", [""])[0]
        return given == pw

    def _json(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        if u.path in ("/", "/index.html"):
            data = PAGE.replace("__NEEDPW__", "true" if os.environ.get("TABLE_PASSWORD")
                                else "false").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if u.path == "/healthz":
            self._json({"ok": True})
            return
        if u.path == "/api/poll":
            if not self._auth(qs):
                self._json({"error": "bad password"}, 403)
                return
            t = get_table(qs.get("table", ["main"])[0])
            since = int(qs.get("since", ["0"])[0] or 0)
            self._json(t.poll(since, qs.get("name", [""])[0]))
            return
        self.send_error(404)

    def do_POST(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        if not self._auth(qs):
            self._json({"error": "bad password"}, 403)
            return
        length = min(int(self.headers.get("Content-Length", 0) or 0), 10000)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            body = {}
        t = get_table(body.get("table", "main"))
        who = str(body.get("name", ""))[:30]
        if u.path == "/api/input":
            ok = t.submit(str(body.get("text", "")), who)
            self._json({"ok": ok})
        elif u.path == "/api/chat":
            t.chat(str(body.get("text", "")), who)
            self._json({"ok": True})
        else:
            self.send_error(404)


PAGE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>D&amp;D 3.5 Table</title>
<style>
:root{--bg:#14110f;--panel:#1e1a17;--ink:#e8e0d4;--dim:#8d8378;--gold:#e0b44c;--line:#3a332d}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 ui-monospace,Menlo,Consolas,monospace;height:100vh;display:flex;flex-direction:column}
header{padding:8px 14px;border-bottom:1px solid var(--line);display:flex;gap:14px;align-items:center;flex-wrap:wrap}
header b{color:var(--gold)}
#here{color:var(--dim)}
#narr{margin-left:auto;display:flex;gap:6px;align-items:center;color:var(--dim);font-size:13px}
#narr select,#narr button{background:#0f0d0c;color:var(--ink);border:1px solid #4a4038;border-radius:6px;padding:3px 6px;font:inherit;font-size:13px}
#narr input{width:70px;flex:none;padding:0}
main{flex:1;display:flex;min-height:0}
#log{flex:1;overflow-y:auto;padding:10px 14px;white-space:pre-wrap;word-break:break-word}
#side{width:300px;border-left:1px solid var(--line);display:flex;flex-direction:column;background:var(--panel)}
#chatlog{flex:1;overflow-y:auto;padding:8px;font-size:13px}
#chatlog .who{color:var(--gold)}
#chatform{display:flex;border-top:1px solid var(--line)}
#bottom{border-top:1px solid var(--line);padding:8px 14px;background:var(--panel)}
#prompt{color:var(--gold);margin-bottom:6px;white-space:pre-wrap}
#opts{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:6px;max-height:34vh;overflow-y:auto}
#opts button{background:#2b2520;color:var(--ink);border:1px solid #4a4038;border-radius:6px;padding:5px 9px;font:inherit;font-size:13px;cursor:pointer;text-align:left}
#opts button:hover{border-color:var(--gold)}
#opts button .n{color:var(--gold);margin-right:6px}
form{display:flex;gap:6px}
input{flex:1;background:#0f0d0c;color:var(--ink);border:1px solid #4a4038;border-radius:6px;padding:7px;font:inherit}
button.go{background:var(--gold);color:#1b1408;border:0;border-radius:6px;padding:0 14px;font:inherit;font-weight:bold;cursor:pointer}
#status{color:var(--dim);font-size:12px;margin-top:4px}
.b{font-weight:bold}.d{opacity:.6}
.c31,.c91{color:#ff6b6b}.c32,.c92{color:#7ee081}.c33,.c93{color:#f4d35e}
.c34,.c94{color:#6fa8ff}.c35,.c95{color:#e08ce0}.c36,.c96{color:#7fd8e6}
.chat{color:#c9a7ff}
#join{position:fixed;inset:0;background:rgba(0,0,0,.85);display:flex;align-items:center;justify-content:center}
#join div{background:var(--panel);padding:22px;border:1px solid var(--gold);border-radius:10px;width:340px}
#join input{width:100%;margin:6px 0 12px}
@media (max-width:800px){#side{display:none}}
</style></head><body>
<div id="join"><div>
<h2 style="margin-top:0;color:var(--gold)">Join the table</h2>
<label>Your name</label><input id="jname" maxlength="30" placeholder="e.g. Alice">
<label>Table</label><input id="jtable" maxlength="32" value="main">
<label id="pwl">Password</label><input id="jpw" type="password">
<button class="go" style="width:100%;padding:9px" onclick="join()">Join</button>
</div></div>
<header><b>D&amp;D 3.5 &mdash; table <span id="tname"></span></b><span id="here"></span>
<span id="narr">&#128266; Narrator
<select id="nmode" title="What the narrator reads"><option value="off">off</option><option value="story">story</option><option value="all">story + combat</option></select>
<select id="nvoice" title="Narrator voice"></select>
<select id="npcvoice" title="Voice for characters' dialogue"></select>
<input id="nrate" type="range" min="0.7" max="1.4" step="0.05" title="Speed">
<button onclick="speechSynthesis.cancel()" title="Skip what's being read">skip</button></span></header>
<main><div id="log"></div>
<div id="side"><div style="padding:8px;color:var(--gold)">Table chat</div><div id="chatlog"></div>
<form id="chatform" onsubmit="sendChat();return false"><input id="chatin" placeholder="say something..."><button class="go">&#9166;</button></form></div></main>
<div id="bottom"><div id="prompt"></div><div id="opts"></div>
<form onsubmit="send(inp.value);return false"><input id="inp" autocomplete="off" placeholder="type an answer or a number"><button class="go">Send</button></form>
<div id="status"></div></div>
<script>
const NEEDPW=__NEEDPW__;
let me=localStorage.getItem('dndname')||'', table=new URLSearchParams(location.search).get('table')||localStorage.getItem('dndtable')||'main', pw=localStorage.getItem('dndpw')||'';
let next=0, polling=false;
const log=document.getElementById('log'), inp=document.getElementById('inp'), opts=document.getElementById('opts'), prompt_=document.getElementById('prompt');
if(!NEEDPW){document.getElementById('jpw').style.display='none';document.getElementById('pwl').style.display='none'}
document.getElementById('jname').value=me;document.getElementById('jtable').value=table;
function join(){me=document.getElementById('jname').value.trim()||'Player';table=document.getElementById('jtable').value.trim()||'main';pw=document.getElementById('jpw').value;
 localStorage.setItem('dndname',me);localStorage.setItem('dndtable',table);localStorage.setItem('dndpw',pw);
 document.getElementById('join').style.display='none';document.getElementById('tname').textContent=table;
 history.replaceState(null,'','?table='+encodeURIComponent(table));poll();inp.focus()}
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function ansi(s){let out='',open=0;const parts=s.split(/\x1b\[([0-9;]*)m/);
 for(let i=0;i<parts.length;i++){if(i%2==0){out+=esc(parts[i]);continue}
  const codes=parts[i].split(';').filter(x=>x);while(open>0){out+='</span>';open--}
  if(!codes.length||codes[0]=='0')continue;
  const cls=codes.map(c=>c=='1'?'b':c=='2'?'d':'c'+c).join(' ');out+='<span class="'+cls+'">';open++}
 while(open>0){out+='</span>';open--}return out}
// ---------------------------------------------------------------- narrator
const N={mode:localStorage.getItem('nmode')||'off',voice:localStorage.getItem('nvoice')||'',
 npc:localStorage.getItem('npcvoice')||'',rate:parseFloat(localStorage.getItem('nrate')||'1')};
let voices=[], primed=false;
function loadVoices(){if(!('speechSynthesis' in window)){document.getElementById('narr').style.display='none';return}
 voices=speechSynthesis.getVoices().filter(v=>/^en/i.test(v.lang));if(!voices.length)voices=speechSynthesis.getVoices();
 for(const [id,cur,label] of [['nvoice',N.voice,'narrator'],['npcvoice',N.npc,'dialogue']]){const sel=document.getElementById(id);sel.innerHTML='';
  voices.forEach(v=>{const o=document.createElement('option');o.value=v.name;o.textContent=label+': '+v.name.replace(/Microsoft |Google |Online \(Natural\)/g,'').slice(0,28);sel.appendChild(o)});
  if(cur&&voices.some(v=>v.name==cur))sel.value=cur;
  else if(voices.length){const pref=voices.findIndex(v=>/natural|neural|daniel|google uk english male|alex/i.test(v.name));sel.selectedIndex=id=='npcvoice'?Math.min(1,voices.length-1):Math.max(0,pref)}}}
if('speechSynthesis' in window){speechSynthesis.onvoiceschanged=loadVoices}
function pickVoice(name){return voices.find(v=>v.name==name)}
function speak(text,voiceName,pitch){if(N.mode=='off'||!text||!('speechSynthesis' in window))return;
 // short chunks avoid browsers cutting long utterances off
 const chunks=text.match(/[^.!?]+[.!?\u201d"']*|.+$/g)||[text];
 for(const ch of chunks){const t=ch.trim();if(!t)continue;const u=new SpeechSynthesisUtterance(t);
  const v=pickVoice(voiceName);if(v)u.voice=v;u.rate=N.rate;u.pitch=pitch||1;speechSynthesis.speak(u)}}
function narrateEvent(ev){if(!primed||N.mode=='off')return;
 if(ev.t=='narrate'){if(ev.kind=='npc')speak(ev.text,document.getElementById('npcvoice').value,1.05);
  else speak(ev.text,document.getElementById('nvoice').value,ev.kind=='title'?0.9:1)}
 else if(ev.t=='line'&&N.mode=='all'){let t=ev.text;
  if(/\x1b\[([0-9]+;)*(2|96|95|93|33)(;[0-9]+)*m/.test(t))return; // dice math, story (read already), headers
  const colored=/\x1b\[([0-9]+;)*(91|92|31|32)(;[0-9]+)*m/.test(t);
  t=t.replace(/\x1b\[[0-9;]*m/g,'').trim();
  if(!t||/^(\d+\.|>|--|\||=|\+|\[)/.test(t))return;
  if(/\bHP -?\d+\/|\| melee:|: (unhurt|scratched|wounded|badly wounded|near death|dead)\b/.test(t))return;
  if(!colored&&!/\b(attacks|casts|takes \d+|slain|falls|rushes|flees|charges|CHARGES|drinks|pours|moves|closes in|turned|crumbles|wakes|asleep|PARALYZED|prone|stabilizes|dying)\b/.test(t))return;
  t=t.replace(/: d20=.*?-> */,'. ').replace(/\(.*?\)/g,'');speak(t,document.getElementById('nvoice').value,1)}
 else if(ev.t=='chat'&&N.mode!='off'){}}
function initNarrator(){loadVoices();const m=document.getElementById('nmode'),r=document.getElementById('nrate');
 m.value=N.mode;r.value=N.rate;
 m.onchange=()=>{N.mode=m.value;localStorage.setItem('nmode',N.mode);speechSynthesis.cancel();
   if(N.mode!='off')speak('The narrator is ready.',document.getElementById('nvoice').value,1)};
 r.oninput=()=>{N.rate=parseFloat(r.value);localStorage.setItem('nrate',r.value)};
 document.getElementById('nvoice').onchange=e=>localStorage.setItem('nvoice',e.target.value);
 document.getElementById('npcvoice').onchange=e=>localStorage.setItem('npcvoice',e.target.value)}
initNarrator();

function addLine(html,cls){const d=document.createElement('div');if(cls)d.className=cls;d.innerHTML=html||'&nbsp;';log.appendChild(d)}
function showPrompt(ev){prompt_.textContent=ev.text;opts.innerHTML='';
 (ev.options||[]).forEach((o,i)=>{const b=document.createElement('button');let val;
  if(ev.kind=='confirm')val=(i==0?'y':'n');else if(ev.kind=='pause')val='';else val=(o=='(back)'?'0':String(i+1));
  b.innerHTML=(ev.kind=='choose'?'<span class="n">'+(o=='(back)'?'0':(i+1))+'</span>':'')+esc(o);b.onclick=()=>send(val);opts.appendChild(b)})}
function clearPrompt(){prompt_.textContent='';opts.innerHTML=''}
async function poll(){if(polling)return;polling=true;
 while(true){try{const r=await fetch('/api/poll?table='+encodeURIComponent(table)+'&since='+next+'&name='+encodeURIComponent(me),{headers:{'X-Password':pw}});
  if(r.status==403){alert('Wrong password');localStorage.removeItem('dndpw');location.reload();return}
  const j=await r.json();if(j.reset){log.innerHTML=''}
  const atBottom=log.scrollHeight-log.scrollTop-log.clientHeight<80;
  for(const ev of j.events){if(ev.seq<next&&!j.reset)continue;
   narrateEvent(ev);
   if(ev.t=='line'){addLine(ansi(ev.text))}
   else if(ev.t=='prompt'){addLine('<span class="c93">'+esc(ev.text)+'</span>')}
   else if(ev.t=='chat'){addLine('<span class="chat">['+esc(ev.who)+'] '+esc(ev.text)+'</span>');
     const c=document.createElement('div');c.innerHTML='<span class="who">'+esc(ev.who)+':</span> '+esc(ev.text);const cl=document.getElementById('chatlog');cl.appendChild(c);cl.scrollTop=cl.scrollHeight}}
  next=j.next;primed=true;
  if(j.waiting){const evs=j.events.filter(e=>e.t=='prompt');if(evs.length)showPrompt(evs[evs.length-1])}else{clearPrompt()}
  document.getElementById('here').textContent='At the table: '+j.here.join(', ');
  document.getElementById('status').textContent=j.waiting?'Waiting for an answer...':'The GM is thinking...';
  if(atBottom||j.events.length)log.scrollTop=log.scrollHeight;
 }catch(e){document.getElementById('status').textContent='Connection lost, retrying...';await new Promise(r=>setTimeout(r,2000))}}}
async function send(text){inp.value='';clearPrompt();
 const r=await fetch('/api/input',{method:'POST',headers:{'Content-Type':'application/json','X-Password':pw},body:JSON.stringify({table,name:me,text})});
 const j=await r.json();if(!j.ok)document.getElementById('status').textContent='The GM is not waiting for input right now.'}
async function sendChat(){const t=document.getElementById('chatin');if(!t.value.trim())return;
 await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json','X-Password':pw},body:JSON.stringify({table,name:me,text:t.value})});t.value=''}
if(me&&(!NEEDPW||pw)){join()}
</script></body></html>
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Host a shared D&D 3.5 table on the web")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    args = ap.parse_args(argv)
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    srv.daemon_threads = True
    print(f"D&D 3.5 table running on http://{args.host}:{args.port}/  (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
