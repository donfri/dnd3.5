const NEEDPW=window.NEEDPW;
let me=localStorage.getItem('dndname')||'', table=new URLSearchParams(location.search).get('table')||localStorage.getItem('dndtable')||'main', pw=localStorage.getItem('dndpw')||'';
let hereNow=[];
let primedBattle=false;
// a random id for this browser: the server binds your name to it so nobody else can answer as you
let ptoken=localStorage.getItem('dndtoken');
if(!ptoken){ptoken=(window.crypto&&crypto.randomUUID)?crypto.randomUUID():String(Math.random()).slice(2)+Date.now();localStorage.setItem('dndtoken',ptoken)}
let sess=localStorage.getItem('dndsess')||'';
function hdr(json){const h={'X-Player-Token':ptoken};if(sess)h['X-Session']=sess;else h['X-Password']=pw;if(json)h['Content-Type']='application/json';return h}
let next=0, polling=false, tab='story', unreadChat=0, lastState=null, stateTimer=null, primed=false;
const $=id=>document.getElementById(id), inp=$('inp');
const blocks={};
if(!NEEDPW){$('jpw').style.display='none';$('pwl').style.display='none'}
$('jname').value=me;$('jtable').value=table;$('jpw').value=pw;

// ---------------------------------------------------------------- tabs
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>showTab(b.dataset.tab));
function showTab(t){tab=t;panelOpen=(t=='story');applyPanel();setTimeout(updateMenuBar,0);document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.tab==t));
 document.querySelectorAll('.pane').forEach(p=>p.classList.toggle('on',p.id==t));
 if(t=='chat'){unreadChat=0;$('b-chat').style.display='none';$('chatin').focus()}
 if(t=='story')$('b-story').style.display='none';
 if(t=='party'||t=='journal'||t=='map')refreshState();
 $('bottom').style.display=(t=='chat')?'none':'block';
 const p=$(t);p.scrollTop=(t=='map')?0:p.scrollHeight}
// ---- phone menu (replaces the tab bar on small screens)
function toggleMenu(){const m=$('menu');if(m.style.display=='block'){m.style.display='none';return}
 let h='';document.querySelectorAll('nav#tabs button').forEach(b=>{const bd=b.querySelector('.badge');
  const label=b.childNodes[0].textContent.trim();
  h+=`<button class="${b.dataset.tab==tab?'on':''}" onclick="toggleMenu();showTab('${b.dataset.tab}')"><span>${label}</span>${bd&&bd.style.display!='none'?'<span class="badge">'+esc(bd.textContent)+'</span>':''}</button>`});
 h+='<hr><button onclick="toggleMenu();toggleAfk()"><span>&#9749; '+(away?"I'm back":'Step away (AFK)')+'</span></button>';
 h+='<button onclick="toggleMenu();toggleSettings()"><span>&#128266; Narrator &amp; settings</span></button>';
 m.innerHTML=h;m.style.display='block'}
document.addEventListener('click',e=>{const m=$('menu');if(m.style.display=='block'&&!m.contains(e.target)&&!$('curtab').contains(e.target))m.style.display='none'});
function updateMenuBar(){const b=document.querySelector(`nav#tabs button[data-tab="${tab}"]`);
 if(b)$('curlabel').textContent=b.childNodes[0].textContent.trim()+' \u25be';
 $('mdot').style.display=[...document.querySelectorAll('nav#tabs .badge')].some(x=>x.style.display!='none')?'block':'none'}
setInterval(updateMenuBar,800);
function toggleSettings(){const s=$('settings');s.style.display=s.style.display=='block'?'none':'block'}

// ---------------------------------------------------------------- text helpers
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function ansi(s){let out='',open=0;const parts=String(s).split(/\x1b\[([0-9;]*)m/);
 for(let i=0;i<parts.length;i++){if(i%2==0){out+=esc(parts[i]);continue}
  const codes=parts[i].split(';').filter(x=>x);while(open>0){out+='</span>';open--}
  if(!codes.length||codes[0]=='0')continue;
  out+='<span class="'+codes.map(c=>c=='1'?'b':c=='2'?'d':'c'+c).join(' ')+'">';open++}
 while(open>0){out+='</span>';open--}return out}
const strip=s=>String(s).replace(/\x1b\[[0-9;]*m/g,'');
function add(pane,html,cls){const d=document.createElement('div');if(cls)d.className=cls;d.innerHTML=html||'&nbsp;';$(pane).appendChild(d);
 const p=$(pane);while(p.childNodes.length>2500)p.removeChild(p.firstChild);return d}
function isRoll(t){return /\x1b\[([0-9]+;)*2(;[0-9]+)*m/.test(t)}
function isMenu(t){const s=strip(t);return /^\s{1,3}\d{1,2}\. /.test(s)||/^\s+0\. \(back\)/.test(s)}

// ---------------------------------------------------------------- join & poll
async function join(){if(N.mode!='off')audioKeepAlive(true);me=$('jname').value.trim()||'Player';table=$('jtable').value.trim()||'main';pw=$('jpw').value||pw;
 localStorage.setItem('dndname',me);localStorage.setItem('dndtable',table);if(NEEDPW&&pw){try{const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json','X-Password':pw},body:'{}'});
  if(r.ok){sess=(await r.json()).session;localStorage.setItem('dndsess',sess);localStorage.removeItem('dndpw');pw='';$('jpw').value=''}
  else if(!sess){alert(r.status==429?'Too many wrong passwords. Try again in 10 minutes.':'Wrong password');return}}catch(e){}}
 $('join').style.display='none';$('tname').textContent='table '+table;
 history.replaceState(null,'','?table='+encodeURIComponent(table));joined=true;lastAct=Date.now();poll();sendPrefs();inp.focus()}
function handle(ev){
 narrateEvent(ev);
 if(ev.t=='battle'){lastBattle=ev.b;renderStrip();
  if(ev.inline&&ev.b)add('story',battleHtml(ev.b,true),'bmap');
  else if(ev.b){const maps=$('story').querySelectorAll('.bmap');   // keep the newest map current
   if(maps.length)maps[maps.length-1].innerHTML=battleHtml(ev.b,true)}
  if(tab=='map'&&lastState)renderMap(lastState);return}
 if(ev.t=='line'){let t=ev.text;add('full',ansi(t));
  if(isRoll(t)){add('dicelog',ansi(t));if($('showrolls').checked)add('story',ansi(t));return}
  if(isMenu(t))return;
  if(/^\[[^\]|]+\| Day \d+/.test(strip(t)))return;   // status line: shown in header & Party tab
  if(ev.kind=='echo'){const last=$('story').lastElementChild,m=strip(t).match(/^> (.*?): (.*)$/);
   if(last&&last.classList.contains('echo')&&m&&last.dataset.who==m[1]&&last.dataset.n<4){last.insertAdjacentHTML('beforeend',' <span class="sep">\u203a</span> '+esc(m[2].replace(/\s+\(.*\)$/,'')));last.dataset.n++;return}
   const e=add('story',ansi(t),'echo');if(m){e.dataset.who=m[1];e.dataset.n=1}return}
  t=t.replace('-> \x1b[92mHIT','-> \x1b[92m\u2714 HIT').replace(/-> miss\b/,'-> \u2716 miss').replace('CRITICAL HIT!','\u2605 CRITICAL HIT!');
  const d=add('story',ansi(t),null);
  if(ev.kind!='echo'&&strip(t).trim())addReadButton(d)}
 else if(ev.t=='prompt'){add('full','<span class="c93">'+esc(ev.text)+'</span>')}
 else if(ev.t=='block'){blocks[ev.seq]=ev;
  add('story','&#128220; <span class="sheetlink" onclick="openBlock('+ev.seq+')">'+esc(ev.title)+' &mdash; open character sheet</span>');
  add('full',ansi(ev.text))}
 else if(ev.t=='dice'){const m=$('diceanim').value;if(primed&&(m=='all'||(m=='mine'&&ev.player&&ev.player.toLowerCase()==me.toLowerCase())))
   throwDice(ev.hero+': '+ev.what,ev.rolls,ev.total,ev.expr)}
 else if(ev.t=='roll'){if(primed&&$('diceanim').value!='off')throwDice(ev.who+(ev.label?' \u2014 '+ev.label:''),ev.rolls||[],ev.total,ev.expr);const html='<div class="froll">\ud83c\udfb2 <b>'+esc(ev.who)+'</b> rolled '+esc(ev.expr)+(ev.label?' <i>for '+esc(ev.label)+'</i>':'')+
   '<span class="tot">'+ev.total+'</span><div class="why">'+esc(ev.detail)+'</div></div>';
  add('dicelog',html);add('chatlog',html);add('full',html);
  if(tab!='chat'&&tab!='dice'&&primed&&ev.who!=me){unreadChat++;$('b-chat').textContent=unreadChat;$('b-chat').style.display='inline'}}
 else if(ev.t=='chat'){add('chatlog','<span class="who">'+esc(ev.who)+':</span> '+esc(ev.text));
  add('full','<span class="c95">['+esc(ev.who)+'] '+esc(ev.text)+'</span>');
  if(tab!='chat'&&primed&&ev.who!=me){unreadChat++;$('b-chat').textContent=unreadChat;$('b-chat').style.display='inline'}}}
// ---------------------------------------------------------------- away from keyboard
const IDLE_MS=(+new URLSearchParams(location.search).get('idlesec')||300)*1000;let away='',afkPending=false,lastAct=Date.now(),joined=false;
function renderAfk(){const pm=$('afkmode')&&$('afkmode').value=='party';$('afkbtn').classList.toggle('on',!!away);$('afkbtn').innerHTML=away?'&#9749; Away':'&#9749; AFK';
 $('afkbar').style.display=away?'block':'none';
 $('afktext').textContent=away=='idle'?"You've been idle for 5 minutes, so you're marked away. "+(pm?"The party can answer for your heroes.":"The computer plays your heroes in fights and others can answer for them.")+" Move the mouse or tap to come back.":
  "You're away. "+(pm?"The party can answer for your heroes.":"The computer plays your heroes in fights, and others can answer for them otherwise.")}
async function setAway(a,auto){if(!joined)return;afkPending=true;away=a?(auto?'idle':'manual'):'';renderAfk();
 try{await fetch('/api/afk',{method:'POST',headers:hdr(true),body:JSON.stringify({table,name:me,away:a,auto:!!auto})})}catch(e){}
 afkPending=false}
function toggleAfk(){setAway(!away,false)}
async function setAfkMode(m){await fetch('/api/afkmode',{method:'POST',headers:hdr(true),body:JSON.stringify({table,name:me,mode:m})}).catch(()=>{})}
function activity(){lastAct=Date.now();if(away=='idle'&&!afkPending)setAway(false)}
['mousemove','mousedown','keydown','touchstart','wheel'].forEach(ev=>window.addEventListener(ev,activity,{passive:true,capture:true}));
setInterval(()=>{if(joined&&!away&&Date.now()-lastAct>IDLE_MS)setAway(true,true)},10000);
// ---- the hero form: four short steps instead of a long run of questions
let formSeq=-1,F=null;
const sgnm=v=>{const m=Math.floor((v-10)/2);return (m>=0?'+':'')+m};
function openForm(ev){const sc=ev.form,keep=F&&F.draft;
 F={sc,step:keep?F.step:0,draft:keep?F.draft:{name:'',gender:'',race:sc.races[0].id,cls:sc.classes[0].id,alignment:'',method:'array',
   scores:{},buy:Object.fromEntries(sc.abilities.map(a=>[a.id,8])),build:'auto',kit:true},msg:''};
 $('mtitle').textContent='Create your hero';$('mplain').style.display='none';$('mbody').style.display='none';
 $('msheet').style.display='block';$('modal').style.display='flex';modalOpened();drawForm()}
function fcls(){return F.sc.classes.find(c=>c.id==F.draft.cls)}
function frace(){return F.sc.races.find(r=>r.id==F.draft.race)}
function fpool(){return F.draft.method=='roll'?F.sc.rolled:F.sc.array}
function fAuto(){const pool=fpool().slice().sort((a,b)=>b-a);F.draft.scores={};fcls().order.forEach((a,i)=>F.draft.scores[a]=pool[i]);F.msg='';drawForm()}
function fSpent(){return Object.values(F.draft.buy).reduce((n,v)=>n+F.sc.costs[v],0)}
function fSet(k,v){F.draft[k]=v;if(k=='cls'){const al=fcls().alignments;if(!al.includes(F.draft.alignment))F.draft.alignment=al.includes('Neutral Good')?'Neutral Good':al[0]}
 if(k=='method'||k=='cls')F.draft.scores={};drawForm()}
function fPick(ab,v){const d=F.draft.scores;if(v==='')delete d[ab];else d[ab]=+v;F.msg='';drawForm()}
function fBuy(ab,dv){const b=F.draft.buy,v=b[ab]+dv;if(v<8||v>18)return;const old=b[ab];b[ab]=v;if(fSpent()>F.sc.budget)b[ab]=old;drawForm()}
function fScores(){return F.draft.method=='buy'?F.draft.buy:F.draft.scores}
function fCheck(step){const d=F.draft;
 if(step==0&&!d.name.trim())return 'Give your hero a name.';
 if(step==2&&d.method!='buy'&&Object.keys(d.scores).length<6)return 'Give every ability a score (or tap "Recommended").';
 if(step==3&&!d.alignment)return 'Pick an alignment.';return ''}
function fGo(n){if(n>0){F.draft.name=($('f-name')||{value:F.draft.name}).value;F.draft.gender=($('f-gender')||{value:F.draft.gender}).value;
  F.msg=fCheck(F.step);if(F.msg){drawForm();return}}
 F.msg='';F.step=Math.max(0,Math.min(3,F.step+n));drawForm();$('msheet').scrollTop=0}
function fSubmit(){F.msg=fCheck(3);if(F.msg){drawForm();return}
 const d=F.draft;const spec={name:d.name.trim(),gender:d.gender.trim(),race:d.race,cls:d.cls,alignment:d.alignment,method:d.method,scores:fScores(),build:d.build,kit:d.kit};
 closeModal();send(JSON.stringify(spec))}
function drawForm(){const d=F.draft,sc=F.sc;if(!d.alignment)fSet('cls',d.cls);
 const card=(on,click,title,sub)=>`<button class="fcard${on?' on':''}" onclick="${click}"><b>${esc(title)}</b><span>${sub}</span></button>`;
 let h=`<div class="fsteps">${['Name & race','Class','Abilities','Finish'].map((t,i)=>`<span class="${i==F.step?'on':i<F.step?'done':''}">${i+1}. ${t}</span>`).join('')}</div>`;
 if(F.step==0){h+=`<label class="fl">Hero's name</label><input id="f-name" class="fin" maxlength="40" value="${esc(d.name).replace(/"/g,'&quot;')}" placeholder="e.g. Mira Stonehand">
  <label class="fl">Gender (optional)</label><input id="f-gender" class="fin" maxlength="20" value="${esc(d.gender).replace(/"/g,'&quot;')}">
  <label class="fl">Race</label><div class="fgrid">`+sc.races.map(r=>card(r.id==d.race,`F.draft.name=$('f-name').value;F.draft.gender=$('f-gender').value;fSet('race','${r.id}')`,r.name,
   esc(Object.entries(r.adj).map(([k,v])=>k.toUpperCase()+' '+(v>0?'+':'')+v).join(', ')||'no ability changes')+'<br>'+esc(r.traits.join('; ')))).join('')+'</div>'}
 if(F.step==1){h+='<label class="fl">Class</label><div class="fgrid">'+sc.classes.map(c=>card(c.id==d.cls,`fSet('cls','${c.id}')`,c.name,'d'+c.hd+' hit die<br>'+esc(c.desc))).join('')+'</div>'}
 if(F.step==2){const adj=frace().adj;
  h+=`<label class="fl">How to set your scores</label><div class="fseg">${[['array','Standard array'],['roll','Rolled dice'],['buy','Point buy']].map(([k,t])=>`<button class="${d.method==k?'on':''}" onclick="fSet('method','${k}')">${t}</button>`).join('')}</div>`;
  if(d.method!='buy'){const pool=fpool(),used=Object.values(d.scores);
   h+=`<div class="why" style="margin:6px 0">${d.method=='roll'?'The dice gave you':'Use each of'}: <b>${pool.join(', ')}</b>. <button class="flink" onclick="fAuto()">Recommended for a ${esc(fcls().name.toLowerCase())}</button></div>`;
   h+=sc.abilities.map(a=>{const left=pool.slice();used.forEach(u=>{if(u!==d.scores[a.id]){const i=left.indexOf(u);if(i>=0)left.splice(i,1)}});
    const cur=d.scores[a.id],fin=cur!=null?cur+(adj[a.id]||0):null;
    return `<div class="frow"><span class="fa">${esc(a.name)}${adj[a.id]?` <i>(${adj[a.id]>0?'+':''}${adj[a.id]} racial)</i>`:''}</span><select onchange="fPick('${a.id}',this.value)"><option value="">\u2013</option>${[...new Set(left)].map(v=>`<option${v===cur?' selected':''}>${v}</option>`).join('')}</select><span class="ff">${fin!=null?fin+' ('+sgnm(fin)+')':''}</span></div>`}).join('')}
  else{h+=`<div class="why" style="margin:6px 0">Points left: <b>${sc.budget-fSpent()}</b> of ${sc.budget}. Higher scores cost more.</div>`+
   sc.abilities.map(a=>{const v=d.buy[a.id],fin=v+(adj[a.id]||0);
    return `<div class="frow"><span class="fa">${esc(a.name)}${adj[a.id]?` <i>(${adj[a.id]>0?'+':''}${adj[a.id]} racial)</i>`:''}</span><span class="fpm"><button onclick="fBuy('${a.id}',-1)">\u2212</button><b>${v}</b><button onclick="fBuy('${a.id}',1)">+</button></span><span class="ff">${fin} (${sgnm(fin)})</span></div>`}).join('')}}
 if(F.step==3){h+=`<label class="fl">Alignment${fcls().alignments.length<9?' (limited for a '+esc(fcls().name.toLowerCase())+')':''}</label><div class="fseg wrap">${fcls().alignments.map(a=>`<button class="${d.alignment==a?'on':''}" onclick="fSet('alignment','${a}')">${a}</button>`).join('')}</div>
  <label class="fl">Skills, feats and spells</label><div class="fgrid">${card(d.build=='auto',"fSet('build','auto')",'Recommended build','The game picks sensible skills, feats and spells. Fastest.')}${card(d.build=='manual',"fSet('build','manual')",'I\'ll choose','You pick everything, one question at a time.')}</div>
  <label class="fl">Starting gear</label><div class="fgrid">${card(d.kit,"fSet('kit',true)",'Standard kit','The usual gear for your class.')}${card(!d.kit,"fSet('kit',false)",'Gold and shopping','Roll starting gold and buy your own.')}</div>
  <div class="why" style="margin-top:10px">${esc(d.name||'Your hero')}: ${esc(frace().name)} ${esc(fcls().name)}, ${esc(d.alignment)}</div>`}
 h+=`<div class="fmsg">${esc(F.msg)}</div><div class="fnav">${F.step?'<button onclick="fGo(-1)">\u2039 Back</button>':'<span></span>'}${F.step<3?'<button class="go" onclick="fGo(1)">Next \u203a</button>':'<button class="go" onclick="fSubmit()">Create hero</button>'}</div>`;
 $('msheet').innerHTML='<div class="fform">'+h+'</div>'}
// ---- dice pictures
const DIE_SHAPE={4:'50,6 94,88 6,88',6:'12,12 88,12 88,88 12,88',8:'50,4 94,50 50,96 6,50',
 10:'50,4 92,40 76,92 24,92 8,40',12:'50,4 95,37 78,92 22,92 5,37',20:'50,3 92,27 92,73 50,97 8,73 8,27'};
function dieSVG(sides,val,small){const pts=DIE_SHAPE[sides]||null;
 const crit=sides==20&&val==20,fum=sides==20&&val==1;
 const fill=crit?'#2c4a22':fum?'#4a2222':'#e0b44c',ink=crit?'#7ed957':fum?'#ff6b6b':'#1b1510';
 let body=pts?`<polygon points="${pts}" fill="${fill}" stroke="#7a6430" stroke-width="3" stroke-linejoin="round"/>`:`<circle cx="50" cy="50" r="45" fill="${fill}" stroke="#7a6430" stroke-width="3"/>`;
 if(sides==20)body+=`<polygon points="50,24 78,66 22,66" fill="none" stroke="${crit||fum?ink:'#9a7a30'}" stroke-width="2" opacity=".55"/>`;
 if(sides==6)body+=`<rect x="12" y="12" width="76" height="76" rx="14" fill="none" stroke="#7a6430" stroke-width="3"/>`;
 const fs=String(val).length>2?26:String(val).length>1?32:38,ty=sides==4?74:sides==20?60:62;
 return `<svg class="die${small?' small':''}${crit?' crit':''}${fum?' fumble':''}" viewBox="0 0 100 100"><g>${body}<text class="dv" x="50" y="${ty}" text-anchor="middle" font-size="${fs}" font-weight="bold" font-family="system-ui,sans-serif" fill="${ink}">${val}</text></g><text x="94" y="99" text-anchor="end" font-size="13" fill="#8d8378">d${sides}</text></svg>`}
function throwDice(label,rolls,total,expr){if(!rolls||!rolls.length)return;
 const tray=$('tray');while(tray.children.length>=3)tray.removeChild(tray.firstChild);
 const many=rolls.reduce((n,r)=>n+r[1].length,0),small=many>3;
 const t=document.createElement('div');t.className='throw';
 let dice='';for(const [sd,vals] of rolls)for(const v of vals.slice(0,12))dice+=dieSVG(sd,Math.abs(v),small);
 t.innerHTML=`<div class="tl">${esc(label)}</div><div class="row">${dice}${many>1||/[+-]\d/.test(expr||'')?'<span class="tot">= '+total+'</span>':''}</div>`;
 tray.appendChild(t);
 // numbers flicker while the dice tumble, then settle on the real result
 const texts=[...t.querySelectorAll('.dv')],finals=texts.map(x=>x.textContent),sides=[];
 for(const [sd,vals] of rolls)for(const v of vals.slice(0,12))sides.push(sd);
 let k=0;const iv=setInterval(()=>{k++;texts.forEach((x,i)=>x.textContent=k<9?1+Math.floor(Math.random()*sides[i]):finals[i]);if(k>=9)clearInterval(iv)},70);
 setTimeout(()=>{t.style.opacity='0';setTimeout(()=>t.remove(),600)},3200)}
// ---- dice preferences (kept in this browser; manual rolling is also told to the server)
function initDicePrefs(){const md=$('manualdice'),da=$('diceanim');
 md.checked=localStorage.getItem('manualdice')=='1';da.value=localStorage.getItem('diceanim')||'mine';
 md.onchange=()=>{localStorage.setItem('manualdice',md.checked?'1':'0');sendPrefs()};
 da.onchange=()=>{localStorage.setItem('diceanim',da.value);if(da.value!='off')throwDice('Test roll',[[20,[1+Math.floor(Math.random()*20)]]],0,'1d20')}}
async function sendPrefs(){if(!joined)return;try{await fetch('/api/prefs',{method:'POST',headers:hdr(true),body:JSON.stringify({table,name:me,manual_dice:$('manualdice').checked})})}catch(e){}}
initDicePrefs();
(function(){const ts=$('textsize');ts.value=localStorage.getItem('textsize')||'1';
 const ap=()=>document.documentElement.style.setProperty('--zoom',ts.value);ap();
 ts.onchange=()=>{localStorage.setItem('textsize',ts.value);ap()}})();
async function poll(){if(polling)return;polling=true;
 while(true){try{const r=await fetch('/api/poll?table='+encodeURIComponent(table)+'&since='+next+'&name='+encodeURIComponent(me),{headers:hdr()});
  if(r.status==403){alert('Please enter the table password again.');localStorage.removeItem('dndpw');localStorage.removeItem('dndsess');location.reload();return}
  if(r.status==429&&(await r.clone().json().catch(()=>({}))).error=='slow down'){await new Promise(z=>setTimeout(z,1500));continue}
  if(r.status==429||r.status==409||r.status==503){const e=await r.json().catch(()=>({}));polling=false;joined=false;
   alert(e.why||e.error||'The server refused to join.');$('join').style.display='flex';return}
  if(r.status==400){location.reload();return}
  const j=await r.json();
  if(j.reset){['story','dicelog','full','chatlog'].forEach(id=>$(id).innerHTML='')}
  for(const ev of j.events){if(ev.seq<next&&!j.reset)continue;handle(ev)}
  flushSpeech();
  const got=j.events.length;next=j.next;primed=true;
  if(j.waiting){const ps=j.events.filter(e=>e.t=='prompt');if(ps.length){showPrompt(ps[ps.length-1]);maybeAlert(j,ps[ps.length-1])}
   setOwner(j.owner,j.may_answer,j);
   if(tab!='story'&&tab!='chat'&&got)$('b-story').style.display='inline'}else{clearPrompt();setOwner('',false)}
  hereNow=j.here.map(x=>x.toLowerCase());$('here').textContent='• '+j.here.map(n=>(j.away||[]).includes(n)?n+' (away)':n).join(', ');
  if(j.me_away!==undefined&&!afkPending&&j.me_away!==away){away=j.me_away;renderAfk()}
  if(j.afk_mode&&$('afkmode').value!==j.afk_mode)$('afkmode').value=j.afk_mode;
  if(j.manual!==undefined&&j.manual!==$('manualdice').checked)sendPrefs();
  $('status').textContent=!j.waiting?'The GM is thinking…':(j.owner&&!j.may_answer?'Only '+j.owner+' can answer this one.':(j.owner?'':'Party decision — anyone at the table can answer.'));
  if(got){for(const id of ['story','dice','full']){const p=$(id);p.scrollTop=p.scrollHeight}scheduleState()}
 }catch(e){$('status').textContent='Connection lost, retrying…';await new Promise(r=>setTimeout(r,2000))}}}

// ---------------------------------------------------------------- choices
const GROUP_ORDER=['Actions','Fight','Travel','Move','Turn','Explore','Party','Tactics','Game'];
const GROUP_LABEL={Actions:'Do something here',Fight:'Attack & magic',Travel:'Go somewhere',Move:'Move',Tactics:'Tactics',Explore:'Explore',Party:'Party',Turn:'',Game:'More'};
let showMore=false;
function optButton(ev,o,i){const b=document.createElement('button');b.className='opt'+(ev.kind=='roll'?' rollbtn':'');let val;
 if(ev.kind=='confirm')val=(i==0?'y':'n');else if(ev.kind=='pause')val='';else val=(o=='(back)'?'0':String(i+1));
 // in the big action menus, the "(explanation)" part is a hint (hidden on phones)
 let label=esc(o);const m=ev.groups&&o.match(/^(.+?) (\(.+\))$/);
 if(m)label=esc(m[1])+' <span class="hint">'+esc(m[2])+'</span>';
 b.title=o;
 b.innerHTML=(ev.kind=='choose'?'<span class="n">'+(o=='(back)'?'0':(i+1))+'</span>':'')+label;b.onclick=()=>send(val);return b}
// ---- the choice panel: on phones it folds away on every tab except the story
let panelOpen=true;const phone=()=>window.matchMedia('(max-width:700px)').matches;
function applyPanel(){const has=!!$('prompt').textContent;
 $('bottom').classList.toggle('closed',phone()&&has&&!panelOpen);
 $('ptog').textContent=panelOpen?'hide \u25be':'choose \u25b4';$('ptog').style.visibility=has?'visible':'hidden'}
function togglePanel(){if(!phone())return;panelOpen=!panelOpen;applyPanel()}
window.addEventListener('resize',applyPanel);
function showPrompt(ev){curPrompt=ev;if(!showMore&&followIntent(ev))return;$('prompt').textContent=ev.text.replace(/:\s*$/,'');const box=$('opts');box.innerHTML='';
 const opts=ev.options||[];$('bottom').classList.toggle('hasopts',opts.length>0||ev.kind=='form');applyPanel();
 if(ev.kind=='form'){const row=document.createElement('div');row.className='row';row.style.display='flex';row.style.flexWrap='wrap';row.style.gap='6px';
  const b1=document.createElement('button');b1.className='opt rollbtn';b1.textContent='\u270d Open the hero form';b1.onclick=()=>openForm(ev);
  const b2=document.createElement('button');b2.className='opt';b2.textContent='Answer questions one at a time instead';b2.onclick=()=>send('{}');
  row.appendChild(b1);row.appendChild(b2);box.appendChild(row);
  if(formSeq!=ev.seq&&(!ev.owner||ev.owner.toLowerCase()==me.toLowerCase())){formSeq=ev.seq;openForm(ev)}
  return}
 if(!ev.groups){const row=document.createElement('div');row.className='row';row.style.display='flex';row.style.flexWrap='wrap';row.style.gap='6px';
  opts.forEach((o,i)=>row.appendChild(optButton(ev,o,i)));box.appendChild(row);return}
 const by={};opts.forEach((o,i)=>{const g=ev.groups[i]||'Game';(by[g]=by[g]||[]).push([o,i])});
 for(const g of GROUP_ORDER.concat(Object.keys(by).filter(k=>!GROUP_ORDER.includes(k)))){if(!by[g])continue;
  const fight=!!ev.keys;
  if((g=='Game'||(fight&&g=='Tactics'))&&!showMore){if(!$('more')){const m=document.createElement('button');m.id='more';
    const n=opts.filter((o,i)=>{const gg=ev.groups[i]||'Game';return gg=='Game'||(fight&&gg=='Tactics')}).length;
    m.textContent=fight?'More actions: maneuvers, tactics, look ('+n+') \u25be':'More options (sheet, journal, save, help\u2026) \u25be';
    m.onclick=()=>{showMore=true;showPrompt(ev)};box.appendChild(m)}continue}
  const d=document.createElement('div');d.className='grp';
  if(GROUP_LABEL[g])d.innerHTML='<div class="gl">'+esc(GROUP_LABEL[g]||g)+'</div>';
  const row=document.createElement('div');row.className='row';by[g].forEach(([o,i])=>{const b=optButton(ev,o,i);if(g=='Actions'||g=='Fight')b.classList.add('primary');row.appendChild(b)});
  d.appendChild(row);box.appendChild(d)}}
function setOwner(owner,may,j){const o=$('owner');o.className='';o.textContent='';$('bottom').classList.remove('locked');
 if(!owner){if(j){o.className='party';o.textContent='\ud83d\udc65 Party decision \u2014 anyone at the table can answer.'}return}
 if(owner.toLowerCase()==me.toLowerCase()){o.className='mine';o.textContent='\u2b50 Your decision, '+me+'!'}
 else if(!may){o.className='theirs';o.textContent='\u23f3 Waiting for '+owner+'\u2026';$('bottom').classList.add('locked')}
 else if(j&&(j.away||[]).map(x=>x.toLowerCase()).includes(owner.toLowerCase())){o.className='party';
  o.textContent='\u2615 '+owner+' is away \u2014 '+(j.afk_mode=='party'?'the party plays for them. Anyone can answer.':
   'anyone can answer; in a fight the computer answers after a moment.')}
 else{o.className='party';o.textContent='\ud83d\udc65 '+owner+' isn\'t at the table \u2014 the party plays for them. Anyone can answer.'}}
function clearPrompt(){curPrompt=null;$('prompt').textContent='';$('opts').innerHTML='';showMore=false;$('bottom').classList.remove('hasopts');applyPanel()}
async function send(text){inp.value='';clearPrompt();if(away)setAway(false);
 const r=await fetch('/api/input',{method:'POST',headers:hdr(true),body:JSON.stringify({table,name:me,text})});
 const j=await r.json();if(!j.ok)$('status').textContent=j.why||'Not accepted.'}
async function sendChat(){const t=$('chatin');if(!t.value.trim())return;
 await fetch('/api/chat',{method:'POST',headers:hdr(true),body:JSON.stringify({table,name:me,text:t.value})});t.value=''}

// ---------------------------------------------------------------- turn alerts
const AL={mine:localStorage.getItem('amine')!='0',party:localStorage.getItem('aparty')!='0',sound:localStorage.getItem('asound')!='0'};
let lastAlertSeq=-1,flashTimer=null;const baseTitle=document.title;
for(const [id,k] of [['amine','mine'],['aparty','party'],['asound','sound']]){const el=$(id);el.checked=AL[k];
 el.onchange=()=>{AL[k]=el.checked;localStorage.setItem(id,el.checked?'1':'0');if(k=='sound'&&el.checked)chime()}}
function chime(){const ctx=audioCtx();if(!ctx)return;const t=ctx.currentTime;
 [[660,0],[880,0.18]].forEach(([f,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=f;o.type='sine';
  g.gain.setValueAtTime(0.0001,t+d);g.gain.exponentialRampToValueAtTime(0.25,t+d+0.02);g.gain.exponentialRampToValueAtTime(0.0001,t+d+0.35);
  o.connect(g);g.connect(ctx.destination);o.start(t+d);o.stop(t+d+0.4)})}
function enableNotify(){if(!('Notification' in window)){alert('This browser does not support notifications.');return}
 Notification.requestPermission().then(p=>{$('anotify').textContent=p=='granted'?'Desktop notifications on \u2713':'Notifications blocked by the browser'})}
if('Notification' in window&&Notification.permission=='granted')$('anotify').textContent='Desktop notifications on \u2713';
function flashTitle(msg){if(flashTimer)return;let on=false;flashTimer=setInterval(()=>{document.title=(on=!on)?msg:baseTitle},900)}
function stopFlash(){if(flashTimer){clearInterval(flashTimer);flashTimer=null}document.title=baseTitle}
window.addEventListener('focus',stopFlash);document.addEventListener('visibilitychange',()=>{if(!document.hidden)stopFlash()});
function maybeAlert(j,ev){if(!primed||ev.seq<=lastAlertSeq)return;lastAlertSeq=ev.seq;
 const mineTurn=j.owner&&j.owner.toLowerCase()==me.toLowerCase();
 const partyTurn=!mineTurn&&(!j.owner||j.may_answer);
 if(!(mineTurn&&AL.mine)&&!(partyTurn&&AL.party))return;
 if(!document.hidden&&document.hasFocus())return;
 const msg=mineTurn?'\u2b50 Your turn!':(j.owner?'\ud83d\udc65 Play for '+j.owner:'\ud83d\udc65 Party decision');
 flashTitle(msg+' \u2014 D&D');
 if(AL.sound)chime();
 if('Notification' in window&&Notification.permission=='granted'){
  try{const n=new Notification(msg,{body:ev.text.replace(/:\s*$/,''),tag:'dnd-turn'});n.onclick=()=>{window.focus();n.close()}}catch(e){}}}

// ---------------------------------------------------------------- free rolls
['d4','d6','d8','d10','d12','d20','d100','2d6','4d6kh3'].forEach(d=>{const b=document.createElement('button');b.type='button';b.className='q';b.textContent=d;b.onclick=()=>freeRoll(d);$('quick').appendChild(b)});
async function freeRoll(expr){if(!expr.trim())return;
 const r=await fetch('/api/roll',{method:'POST',headers:hdr(true),body:JSON.stringify({table,name:me,expr,label:$('rlabel').value})});
 const j=await r.json();$('rmsg').textContent=j.ok?'':j.why;if(j.ok)$('rexpr').value=''}

// ---------------------------------------------------------------- party & journal
function scheduleState(){clearTimeout(stateTimer);stateTimer=setTimeout(refreshState,700)}
async function refreshState(){try{const r=await fetch('/api/state?table='+encodeURIComponent(table),{headers:hdr()});
 const s=await r.json();if(s.busy)return;lastState=s;if(s.battle!==undefined&&!primedBattle){lastBattle=s.battle;primedBattle=true}renderParty(s);renderJournal(s);renderMap(s);renderStrip();
 $('where').textContent=s.active?('📍 '+s.location+' • '+s.time):''}catch(e){}}
function renderParty(s){const el=$('party');if(!s.active){el.innerHTML='<div class="empty">Start or load a game to see your party.</div>';return}
 el.innerHTML='<div class="cards">'+s.party.map((p,i)=>{
  const pct=Math.max(0,Math.min(100,100*p.hp/p.max_hp));const col=pct>50?'var(--green)':pct>25?'#f4d35e':'var(--red)';
  const xp=p.xp_next?`XP ${p.xp} / ${p.xp_next}`:`XP ${p.xp} (max level)`;
  return `<div class="card"><h3>${esc(p.name)}</h3><div class="sub">${esc(p.race)} ${esc(p.classes)}${p.player?' • played by '+esc(p.player):''}</div>
  <div class="bar"><i style="width:${pct}%;background:${col}"></i></div>
  <div style="font-size:13px">HP <b>${p.hp}</b> / ${p.max_hp}${p.temp_hp?' (+'+p.temp_hp+' temp)':''} ${p.status!='ok'?'<span class="chip" style="color:var(--red)">'+esc(p.status)+'</span>':''}</div>
  <div class="stats"><span>AC <b>${p.ac}</b></span><span>touch ${p.touch}</span><span>flat ${p.flat}</span>${p.spells?'<span>spells ready: '+p.spells+'</span>':''}</div>
  <div style="font-size:13px;color:var(--dim)">${xp} • ${esc(p.money)}</div>
  ${p.can_level?'<div class="lvl">⬆ Can level up! (choose "Level up!" in More options)</div>':''}
  <div>${p.effects.map(e=>'<span class="chip">'+esc(e)+'</span>').join('')}</div>
  <button onclick="openSheet(${i})">Character sheet &amp; gear</button>
  ${(p.player||'').toLowerCase()==me.toLowerCase()?'<span class="chip" style="color:var(--green)">your hero</span>':(hereNow.includes((p.player||'').toLowerCase())?'':`<button onclick="claimHero(${i})">\ud83c\udfad Play this hero</button>`)}</div>`}).join('')+'</div>'}
async function claimHero(i){const r=await fetch('/api/claim',{method:'POST',headers:hdr(true),body:JSON.stringify({table,name:me,hero:i})});
 const j=await r.json();if(!j.ok)alert(j.why);refreshState()}
function wrapName(name,max){const words=name.split(' ');const lines=[];let cur='';
 for(const w of words){if((cur+' '+w).trim().length>max&&cur){lines.push(cur);cur=w}else cur=(cur+' '+w).trim()}
 if(cur)lines.push(cur);return lines.slice(0,3)}
let lastBattle=null;
const TOKC={pc:'#7ed957',ally:'#5fd3c4',foe:'#ff6b6b'};
const TERR={wall:'#5e554c',tree:'#2f6b2a',crate:'#7a5a30',deep:'#0c1d33',chasm:'#050403',water:'#3d6f99',rubble:'#3a332d',brush:'#2f4224',mud:'#4d3b25'};
// ---- the bar under the header: turn order in a fight, the party's hit points otherwise
function renderStrip(){const el=$('strip');let h='';
 if(lastBattle&&lastBattle.order&&lastBattle.order.length){
  h='<span class="sl">Turn</span>'+lastBattle.order.map(o=>`<span class="chipx ${o.side}${o.name==lastBattle.current?' cur':''}${o.down?' down':''}">${o.name==lastBattle.current?'\u25b6 ':''}${esc(o.name)} <i>${esc(o.hp)}</i></span>`).join('')}
 else if(lastState&&lastState.active&&lastState.party){
  h=lastState.party.map((p,i)=>{const pct=Math.max(0,Math.min(100,100*p.hp/Math.max(1,p.max_hp)));
   return `<span class="chipx pc${p.hp<=0?' down':''}" onclick="openSheet(${i})">\u2665 ${esc(p.name.split(' ')[0])} <i>${p.hp}/${p.max_hp}</i><b class="hpb"><b style="width:${pct}%;background:${pct>50?'var(--green)':pct>25?'var(--gold)':'var(--red)'}"></b></b></span>`}).join('')}
 el.innerHTML=h;el.style.display=h?'flex':'none';
 const c=el.querySelector('.cur');if(c&&c.scrollIntoView)c.scrollIntoView({block:'nearest',inline:'center'})}
// ---- tapping the battle map: a foe = attack it, an empty square = move there
let intent=null;
function mapTap(e){const svg=e.target.closest('.bmap svg');if(!svg||!lastBattle||!curPrompt)return;
 const r=svg.getBoundingClientRect(),vb=svg.viewBox.baseVal,S=26;
 const x=Math.floor(((e.clientX-r.left)/r.width*vb.width+vb.x-1)/S),y=Math.floor(((e.clientY-r.top)/r.height*vb.height+vb.y-1)/S);
 if(x<0||y<0||x>=lastBattle.w||y>=lastBattle.h)return;
 const tok=lastBattle.tokens.find(t=>x>=t.x&&x<t.x+(t.size||1)&&y>=t.y&&y<t.y+(t.size||1)),keys=curPrompt.keys||[];
 if(/^Move to which square/.test(curPrompt.text)){if(!tok)send(x+','+y);return}
 if(!keys.length){return}
 if(tok&&tok.side=='foe'){const i=keys.indexOf('attack');if(i<0){flash('No attack left this turn.');return}
  intent={foe:tok.name,at:Date.now()};send(String(i+1))}
 else if(!tok){const i=keys.indexOf('move_to');if(i<0){flash('No movement left this turn.');return}
  intent={sq:x+','+y,at:Date.now()};send(String(i+1))}}
function flash(msg){$('status').textContent=msg}
document.addEventListener('click',mapTap);
function followIntent(ev){if(!intent||Date.now()-intent.at>20000){intent=null;return false}
 if(ev.keys){intent=null;return false}
 if(intent.sq&&/^Move to which square/.test(ev.text)){const v=intent.sq;intent=null;send(v);return true}
 if(intent.foe&&ev.options){const i=ev.options.findIndex(o=>o.startsWith(intent.foe+' ('));
  if(i>=0){intent=null;send(String(i+1));return true}}
 return false}
let curPrompt=null;
function battleHtml(b,crop){const S=26,W=b.w*S,H=b.h*S;
 const ys=b.tokens.map(t=>t.y);let y0=0,y1=b.h-1;
 if(crop&&ys.length){y0=Math.max(0,Math.min(...ys)-1);y1=Math.min(b.h-1,Math.max(...ys)+1)}
 let svg=`<svg viewBox="0 ${y0*S} ${W+2} ${(y1-y0+1)*S+2}" width="${W+2}" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif">`;
 svg+=`<rect x="1" y="1" width="${W}" height="${H}" fill="${b.dark?'#0b0a09':'#1b1714'}" stroke="#4a4038"/>`;
 for(let x=1;x<b.w;x++)svg+=`<line x1="${x*S+1}" y1="1" x2="${x*S+1}" y2="${H+1}" stroke="#2c2621"/>`;
 for(let y=1;y<b.h;y++)svg+=`<line x1="1" y1="${y*S+1}" x2="${W+1}" y2="${y*S+1}" stroke="#2c2621"/>`;
 for(const c of (b.terrain||[])){const X=c.x*S+1,Y=c.y*S+1,f=TERR[c.k]||TERR.wall;
  if(c.k=='tree')svg+=`<rect x="${X}" y="${Y}" width="${S}" height="${S}" fill="#1b1714"/><circle cx="${X+S/2}" cy="${Y+S/2}" r="${S/2-3}" fill="${f}" stroke="#13240f"/>`;
  else svg+=`<rect x="${X}" y="${Y}" width="${S}" height="${S}" fill="${f}"/>`;
  if(c.k=='rubble')svg+=`<circle cx="${X+8}" cy="${Y+9}" r="2.5" fill="#8d8378"/><circle cx="${X+17}" cy="${Y+15}" r="3" fill="#8d8378"/><circle cx="${X+10}" cy="${Y+19}" r="2" fill="#8d8378"/>`;
  if(c.k=='brush')svg+=`<path d="M${X+6} ${Y+20}l3-9l3 9M${X+14} ${Y+21}l3-11l3 11" stroke="#7fa35a" fill="none"/>`;
  if(c.k=='water'||c.k=='deep')svg+=`<path d="M${X+4} ${Y+12}q4-4 8 0t8 0" stroke="#7fb0d9" fill="none" opacity=".7"/>`;
  if(c.k=='crate')svg+=`<rect x="${X+3}" y="${Y+3}" width="${S-6}" height="${S-6}" fill="none" stroke="#2d2010"/><path d="M${X+3} ${Y+3}L${X+S-3} ${Y+S-3}" stroke="#2d2010"/>`}
 const at={};b.tokens.forEach(t=>at[t.name]=t);const cx=t=>t.x*S+S*(t.size||1)/2+1,cy=t=>t.y*S+S*(t.size||1)/2+1;
 const drawn=new Set();
 for(const t of b.tokens)for(const n of t.engaged){const o=at[n];if(!o)continue;const k=[t.name,n].sort().join('|');if(drawn.has(k))continue;drawn.add(k);
  svg+=`<line x1="${cx(t)}" y1="${cy(t)}" x2="${cx(o)}" y2="${cy(o)}" stroke="#e0b44c" stroke-width="2" opacity=".55"/>`}
 for(const t of b.tokens){const col=t.down?'#6b5d50':TOKC[t.side];
  svg+=`<circle cx="${cx(t)}" cy="${cy(t)}" r="${S*(t.size||1)/2-2}" fill="${col}" stroke="${t.flying?'#fff':'#111'}" stroke-width="${t.flying?2:1}"${t.flying?' stroke-dasharray="3 2"':''}><title>${esc(t.name)} (${esc(t.hp)})</title></circle>`;
  svg+=`<text x="${cx(t)}" y="${cy(t)+4}" text-anchor="middle" font-size="12" font-weight="bold" fill="#111">${esc(t.label)}</text>`}
 svg+='</svg>';
 const leg=b.tokens.map(t=>`<span style="white-space:nowrap"><b style="background:${t.down?'#6b5d50':TOKC[t.side]}">${esc(t.label)}</b>${esc(t.name)} <span style="opacity:.8">${esc(t.hp)}${t.down?', down':''}${t.flying?', flying':''}</span></span>`).join(' &nbsp; ');
 const tl=(b.legend||[]).map(l=>`<span style="white-space:nowrap"><i style="display:inline-block;width:11px;height:11px;border-radius:2px;vertical-align:-1px;margin-right:3px;background:${TERR[l.k]}"></i>${esc(l.name)}${l.slow?' (slow)':''}</span>`).join(' &nbsp; ');
 return svg+`<div class="bl">${leg}${tl?'<br>'+tl:''}<br>Each square is 5 ft. Gold lines join foes locked in melee.</div>`}
function renderMap(s){const el=$('map');if(!s.active||!s.map){el.innerHTML='<div class="empty">Start or load a game to see the map.</div>';return}
 const bt=(lastBattle!==undefined&&lastBattle!==null)?lastBattle:null;
 const top=bt?`<div class="bmap"><h3>Battle${bt.round?' &mdash; round '+bt.round:''}</h3>${battleHtml(bt)}</div><h3>Area map</h3>`:'';
 const m=s.map,W=150,H=74,BW=124,BH=50;
 const xs=m.nodes.map(n=>n.x),ys=m.nodes.map(n=>n.y),minx=Math.min(...xs),miny=Math.min(...ys);
 const cx=n=>(n.x-minx)*W+W/2+10,cy=n=>(n.y-miny)*H+H/2+10;
 const width=(Math.max(...xs)-minx+1)*W+20,height=(Math.max(...ys)-miny+1)*H+20;
 const byId={};m.nodes.forEach(n=>byId[n.id]=n);
 let svg=`<svg viewBox="0 0 ${width} ${height}" width="${width}" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif">`;
 for(const e of m.edges){const a=byId[e.a],b=byId[e.b];if(!a||!b)continue;
  const dash=(!a.visited||!b.visited)?' stroke-dasharray="5 4"':'';
  svg+=`<line x1="${cx(a)}" y1="${cy(a)}" x2="${cx(b)}" y2="${cy(b)}" stroke="${e.trap?'#ff6b6b':'#6b5d50'}" stroke-width="3"${dash}/>`;
  const mx=(cx(a)+cx(b))/2,my=(cy(a)+cy(b))/2;
  if(e.locked)svg+=`<text x="${mx}" y="${my+5}" text-anchor="middle" font-size="15">&#128274;</text>`;
  else if(e.trap)svg+=`<text x="${mx}" y="${my+5}" text-anchor="middle" font-size="15">&#9888;&#65039;</text>`;
  else if(e.dir=='up'||e.dir=='down')svg+=`<text x="${mx+9}" y="${my-3}" font-size="11" fill="#8d8378">${e.dir=='up'?'&#8593; stairs':'&#8595; stairs'}</text>`}
 for(const n of m.nodes){const x=cx(n)-BW/2,y=cy(n)-BH/2;
  const fill=n.current?'#3a2f16':n.visited?(n.town?'#1f2a1c':'#26211d'):'#14110f';
  const stroke=n.current?'#e0b44c':n.visited?'#5a4f45':'#4a4038';
  svg+=`<rect x="${x}" y="${y}" width="${BW}" height="${BH}" rx="8" fill="${fill}" stroke="${stroke}" stroke-width="${n.current?3:1.5}"${n.visited?'':' stroke-dasharray="4 3"'}/>`;
  const lines=n.visited?wrapName(n.name,17):['unexplored'];
  lines.forEach((ln,i)=>{svg+=`<text x="${cx(n)}" y="${cy(n)-((lines.length-1)*7)+i*14+4}" text-anchor="middle" font-size="12" fill="${n.visited?(n.current?'#e0b44c':'#e8e0d4'):'#6b5d50'}">${esc(ln)}</text>`});
  if(n.current)svg+=`<text x="${x+BW-6}" y="${y+13}" text-anchor="end" font-size="11">&#11088;</text>`}
 svg+='</svg>';
 el.innerHTML=top+svg+'<div class="legend">&#11088; you are here &middot; dashed = not explored yet &middot; &#128274; locked &middot; &#9888;&#65039; known trap &middot; '+esc(s.location)+'</div>'}
function renderJournal(s){const el=$('journal');if(!s.active){el.innerHTML='<div class="empty">No journal yet.</div>';return}
 el.innerHTML=`<div class="jsec"><h3>${esc(s.adventure)}</h3><div>📍 ${esc(s.location)} • ${esc(s.time)}${s.heroic?' • heroic mode':''}</div></div>
 <div class="jsec"><h3>Quest log &amp; notes</h3>${s.journal.length?'<ul>'+s.journal.slice().reverse().map(j=>'<li>'+esc(j)+'</li>').join('')+'</ul>':'<div class="empty">Nothing yet. Talk to people!</div>'}</div>
 <div class="jsec"><h3>Places visited</h3><div>${s.visited.map(v=>'<span class="chip">'+esc(v)+'</span>').join('')}</div></div>`}
let sheetIdx=null,showAllSkills=false;
function openSheet(i){sheetIdx=i;const p=lastState.party[i];$('mtitle').textContent=p.name+' — character sheet';
 $('mbody').innerHTML=esc(p.sheet);$('mbody').style.display='none';$('mplain').style.display='inline-block';$('mplain').textContent='Plain text';
 $('msheet').style.display='block';$('msheet').innerHTML=renderSheet(p.sheet_data);$('modal').style.display='flex';modalOpened();$('msheet').scrollTop=0}
function togglePlain(){const plain=$('mbody').style.display=='none';$('mbody').style.display=plain?'block':'none';$('msheet').style.display=plain?'none':'block';$('mplain').textContent=plain?'Formatted':'Plain text'}
async function openBlock(seq){const b=blocks[seq];await refreshState();
 const i=lastState&&lastState.party?lastState.party.findIndex(p=>b.title.toLowerCase().startsWith(p.name.toLowerCase())):-1;
 if(i>=0){openSheet(i);return}
 $('mtitle').textContent=b.title;$('msheet').style.display='none';$('mplain').style.display='none';$('mbody').style.display='block';$('mbody').innerHTML=ansi(b.text);$('modal').style.display='flex';modalOpened()}
const sgn=n=>(n>=0?'+':'')+n;
function canManageHero(i){if(!lastState||!lastState.can_manage)return false;const p=lastState.party[i];
 const owner=(p.player||'').toLowerCase();return !owner||owner==me.toLowerCase()||!hereNow.includes(owner)}
const EQUIPPABLE=['weapon','armor','shield','ring','cloak','amulet','bracers','gloves','head','belt'];
function itemButtons(e,others){const b=[];const h=sheetIdx;
 if(EQUIPPABLE.includes(e.kind)){
  if(e.equipped)b.push(`<button onclick="itemAct(${h},${e.idx},'unequip')">Unequip</button>`);
  else{b.push(`<button onclick="itemAct(${h},${e.idx},'equip')">Equip</button>`);
   if(e.kind=='weapon'&&(e.hands=='light'||e.hands=='one'))b.push(`<button onclick="itemAct(${h},${e.idx},'equip_off')">Off hand</button>`)}}
 if(e.use=='antitoxin'||(e.use&&e.target&&!['enemy','enemies'].includes(e.target))){
  b.push(`<button onclick="itemAct(${h},${e.idx},'use',${h})">Use</button>`);
  if(e.use=='spell'&&e.target=='ally'&&others.length)b.push(`<select onchange="if(this.value!=='')itemAct(${h},${e.idx},'use',+this.value)"><option value="">Use on…</option>${others.map(([p,i])=>`<option value="${i}">${esc(p.name)}</option>`).join('')}</select>`)}
 if(others.length)b.push(`<select onchange="if(this.value!=='')itemAct(${h},${e.idx},'give',+this.value)"><option value="">Give to…</option>${others.map(([p,i])=>`<option value="${i}">${esc(p.name)}</option>`).join('')}</select>`);
 b.push(`<button class="danger" onclick="if(confirm('Drop ${esc(e.name).replace(/'/g,'')}?'))itemAct(${h},${e.idx},'drop')">Drop</button>`);
 return '<div class="ia">'+b.join('')+'</div>'}
async function itemAct(hero,item,action,target){
 const r=await fetch('/api/item',{method:'POST',headers:hdr(true),body:JSON.stringify({table,name:me,hero,item,action,target:target==null?-1:target})});
 const j=await r.json();if(!j.ok){alert(j.why);return}
 await refreshState();if($('modal').style.display=='flex'&&sheetIdx!=null){const sc=$('msheet').scrollTop;openSheet(sheetIdx);$('msheet').scrollTop=sc}}
function why(parts){return parts&&parts.length?esc(parts.join(', ')):''}
function renderSheet(d){if(!d)return '<div class="empty">No sheet.</div>';
 const pct=Math.max(0,Math.min(100,100*d.hp/d.max_hp)),col=pct>50?'var(--green)':pct>25?'#f4d35e':'var(--red)';
 let h=`<div class="sh-head"><h2>${esc(d.name)}</h2>
  <div class="sub">${esc(d.race)} ${esc(d.classes)} · ${esc(d.alignment)}${d.deity?' · worships '+esc(d.deity):''}${d.player?' · played by '+esc(d.player):''}</div>
  <div class="meta">${esc(d.size)}, speed ${d.speed} ft.${d.gender?' · '+esc(d.gender):''}${d.age?', age '+d.age:''}${d.height?', '+esc(d.height):''}${d.weight?', '+esc(d.weight):''} · ${esc(d.vision)} vision · speaks ${esc(d.languages.join(', '))}</div>
  <div class="meta">XP ${d.xp}${d.xp_next?' / '+d.xp_next+' for level '+(d.level+1):' (max level)'}${d.can_level?' &nbsp;<b style="color:var(--green)">⬆ ready to level up</b>':''}</div></div>`;
 h+=`<div class="sh-row sh-sec"><div><h4>Ability scores</h4><div class="abil">`+d.abilities.map(a=>
   `<div title="${esc(a.notes.join(', ')||'base score')}"><div class="k">${a.key}</div><div class="m">${sgn(a.mod)}</div><div class="s">score ${a.score}${a.notes.length?' *':''}</div></div>`).join('')+
   `</div><div class="why" style="margin-top:6px">Big number: the modifier added to rolls. * hover to see racial / level changes.</div></div>`;
 h+=`<div><h4>Combat</h4><div style="display:flex;justify-content:space-between"><span><b style="font-size:18px">${d.hp}</b> / ${d.max_hp} hit points${d.temp_hp?' (+'+d.temp_hp+' temp)':''}</span><span class="why">${esc(d.status)} · hit dice ${esc(d.hit_dice)}</span></div>
   <div class="hpbar"><i style="width:${pct}%;background:${col}"></i></div>
   <div class="tiles"><div class="tile big" title="${why(d.ac.parts)}"><div class="k">Armor class</div><div class="v">${d.ac.total}</div></div>
   <div class="tile" title="vs touch attacks: ignores armor, shield and natural armor"><div class="k">Touch</div><div class="v">${d.ac.touch}</div></div>
   <div class="tile" title="when caught off guard: no Dex bonus"><div class="k">Flat-footed</div><div class="v">${d.ac.flat}</div></div>
   <div class="tile"><div class="k">Initiative</div><div class="v">${sgn(d.init)}</div></div>
   <div class="tile"><div class="k">Base attack</div><div class="v">${sgn(d.bab)}</div></div>
   <div class="tile"><div class="k">Grapple</div><div class="v">${sgn(d.grapple)}</div></div></div>
   <div class="why" style="margin:6px 0 10px">AC = 10${d.ac.parts.length?', '+why(d.ac.parts):''}</div>
   <div class="tiles">`+d.saves.map(sv=>`<div class="tile" style="flex:1"><div class="k">${sv.name}</div><div class="v">${sgn(sv.total)}</div><div class="why">${why(sv.parts)||'no bonus'}</div></div>`).join('')+`</div>
   <div class="why" style="margin-top:6px">Armor check penalty ${d.acp} · max Dex bonus ${d.max_dex==null?'none':sgn(d.max_dex)} · arcane spell failure ${d.asf}%</div></div></div>`;
 h+=`<div class="sh-sec"><h4>Attacks</h4><table class="sh"><tr><th>Weapon</th><th style="text-align:right">To hit</th><th style="text-align:right">Damage</th><th>Critical</th><th>Type</th><th>Range</th><th></th></tr>`+
   d.attacks.map(a=>`<tr class="${a.state=='stowed'?'dim':''}"><td><b>${esc(a.name)}</b> <span class="why">${esc(a.state)}</span>${a.proficient?'':' <span style="color:var(--red)">(not proficient)</span>'}<div class="why">${why(a.parts)}</div></td>
   <td class="n">${esc(a.bonus)}</td><td class="n">${esc(a.damage)}</td><td>${esc(a.crit)}</td><td>${esc(a.type)}</td><td>${esc(a.range)}</td><td class="why">${esc(a.ammo)}</td></tr>`).join('')+`</table></div>`;
 const sk=d.skills.filter(s=>showAllSkills||(s.usable&&(s.ranks>0||s.class_skill)));
 h+=`<div class="sh-row sh-sec"><div><h4>Skills <button class="toggle" onclick="showAllSkills=!showAllSkills;$('msheet').innerHTML=renderSheet(lastState.party[sheetIdx].sheet_data)">${showAllSkills?'show only my skills':'show all '+d.skills.length}</button></h4>
   <table class="sh"><tr><th>Skill</th><th style="text-align:right">Bonus</th><th style="text-align:right">Ranks</th><th>Ability</th></tr>`+
   sk.map(s=>`<tr class="${s.usable?'':'dim'}" title="${why(s.parts)}"><td>${s.class_skill?'<span class="star">★</span> ':''}${esc(s.name)}${s.usable?'':' <span class="why">(needs training)</span>'}</td>
   <td class="n">${s.usable?sgn(s.total):'—'}</td><td class="n" style="font-weight:normal">${s.ranks||''}</td><td class="why">${s.ability}</td></tr>`).join('')+
   `</table><div class="why" style="margin-top:4px">★ class skill · hover a skill to see its math. Untrained skills use just your ability modifier.</div></div>`;
 h+=`<div><h4>Feats</h4>`+(d.feats.length?d.feats.map(f=>`<div style="margin-bottom:6px"><b>${esc(f.name)}</b><div class="why">${esc(f.desc)}</div></div>`).join(''):'<div class="why">None</div>')+
   `<h4 style="margin-top:14px">Special abilities</h4>`+d.specials.map(x=>`<div style="margin-bottom:3px">• ${esc(x)}</div>`).join('')+
   (d.daily.length?`<div style="margin-top:6px"><b>Uses left today:</b> ${esc(d.daily.join(' · '))}</div>`:'')+`</div></div>`;
 for(const sp of d.spells){h+=`<div class="sh-sec"><h4>${esc(sp.class)} spells · caster level ${sp.cl} · ${esc(sp.ability)}</h4>`;
  for(const L of sp.levels){h+=`<div style="margin-bottom:6px"><b>${L.level==0?'Cantrips (level 0)':'Level '+L.level}</b> <span class="why">${L.left} of ${L.per_day} left today · save DC ${L.dc}</span><br>`+
   (sp.prepared?L.slots.map(x=>`<span class="spl ${x.used?'used':''}">${esc(x.name)}${x.domain?' (domain)':''}</span>`).join(''):L.known.map(x=>`<span class="spl">${esc(x)}</span>`).join(''))+`</div>`}
  if(sp.domains.length)h+=`<div class="why">Domains: ${esc(sp.domains.join(', '))}${sp.spontaneous_cure?' · can swap any prepared spell for a cure spell':''}</div>`;
  if(sp.spellbook.length)h+=`<div class="why">Spellbook: ${esc(sp.spellbook.join(', '))}</div>`;
  h+=`</div>`}
 if(d.effects.length||d.afflictions.length)h+=`<div class="sh-sec"><h4>Active effects</h4>`+d.effects.concat(d.afflictions).map(e=>`<span class="spl">${esc(e)}</span>`).join('')+`</div>`;
 const mine=sheetIdx!=null&&lastState&&canManageHero(sheetIdx);
 const others=(lastState&&lastState.party?lastState.party:[]).map((p,i)=>[p,i]).filter(([p,i])=>i!=sheetIdx&&p.status!='DEAD');
 h+=`<div class="sh-sec" id="sh-gear"><h4>Equipment · ${esc(d.money)} · ${d.carried} lb. carried (${esc(d.load)} load, max ${d.heavy} lb.)</h4><table class="sh"><tr><th>Item</th><th style="text-align:right">Qty</th><th>Worn / held</th><th style="text-align:right">lb.</th>${mine?'<th></th>':''}</tr>`+
   d.equipment.map(e=>`<tr><td>${esc(e.name)}${e.desc?'<div class="why">'+esc(e.desc)+'</div>':''}</td><td class="n" style="font-weight:normal">${e.qty>1?e.qty:''}</td><td>${e.slot?'<span style="color:var(--green)">'+esc(e.slot)+'</span>':''}</td><td class="n" style="font-weight:normal">${e.weight}</td>${mine?'<td>'+itemButtons(e,others)+'</td>':''}</tr>`).join('')+`</table>`+
   (lastState&&!lastState.can_manage?'<div class="why" style="margin-top:6px">Gear can be changed while exploring, between actions (not in combat or while the game is asking something else).</div>':
    (!mine&&sheetIdx!=null?'<div class="why" style="margin-top:6px">Only this hero\'s player can change their gear.</div>':''))+`</div>`;
 return h}
function closeModal(){if($('modal').style.display!='flex')return;$('modal').style.display='none';
 if(history.state&&history.state.modal)history.back()}
// the phone's Back button (or Escape) closes a sheet instead of leaving the page
function modalOpened(){if(!(history.state&&history.state.modal))history.pushState({modal:1},'')}
window.addEventListener('popstate',()=>{if($('modal').style.display=='flex')$('modal').style.display='none'});
document.addEventListener('keydown',e=>{if(e.key=='Escape')closeModal()});
document.addEventListener('keydown',e=>{if(e.key=='Escape'){closeModal();$('settings').style.display='none'}});

// ---------------------------------------------------------------- narrator
// Two engines:
//  * "server": the server renders speech with Piper (a neural voice) and we play it
//    through one Web Audio stream: clean, no OS speech engine involved.
//  * "browser": the Web Speech API with this computer's voices (fallback).
const N={mode:localStorage.getItem('nmode')||'off',engine:localStorage.getItem('nengine')||'server',
 voice:localStorage.getItem('nvoice')||'',npc:localStorage.getItem('npcvoice')||'',
 rate:parseFloat(localStorage.getItem('nrate')||'1'),vol:parseFloat(localStorage.getItem('nvol')||'0.5'),
 smooth:localStorage.getItem('nsmooth')=='1'};
let tts={available:false,voices:{}}, voices=[], speechQueue=[];
function useServer(){return N.engine=='server'&&tts.available}
function smoothText(t){if(!N.smooth)return t;
 return t.replace(/\.{3}|…/g,',').replace(/([.!?;:])(["”’']?)(\s+|$)/g,(m,p,q,sp)=>(sp?', ':''))
         .replace(/[“”"]/g,'').replace(/,\s*,/g,',').replace(/,\s*$/,'').trim()}
function loadVoices(){if(!('speechSynthesis' in window))return;
 voices=speechSynthesis.getVoices().filter(v=>/^en/i.test(v.lang));if(!voices.length)voices=speechSynthesis.getVoices();
 for(const [id,cur] of [['nvoice',N.voice],['npcvoice',N.npc]]){const sel=$(id);sel.innerHTML='';
  voices.forEach(v=>{const o=document.createElement('option');o.value=v.name;o.textContent=v.name.replace(/Microsoft |Google /g,'');sel.appendChild(o)});
  if(cur&&voices.some(v=>v.name==cur))sel.value=cur;
  else if(voices.length){const pref=voices.findIndex(v=>/natural|neural|daniel|google uk english male|alex/i.test(v.name));sel.selectedIndex=id=='npcvoice'?Math.min(1,voices.length-1):Math.max(0,pref)}}}
if('speechSynthesis' in window){speechSynthesis.onvoiceschanged=loadVoices}
// collect text during one batch of events (merging lines for the same speaker)
function speak(text,role){if(N.mode=='off'||!text)return;
 const last=speechQueue[speechQueue.length-1];
 if(last&&last.role==role)last.text+=' '+text;else speechQueue.push({text,role})}
// ---- Web Audio: one always-open output stream (also stops device sleep/wake pops)
let actx=null,gainNode=null,nextAt=0,sources=[],playChain=Promise.resolve(),epoch=0;
function audioCtx(){try{if(!actx){const AC=window.AudioContext||window.webkitAudioContext;if(!AC)return null;
  actx=new AC();gainNode=actx.createGain();gainNode.connect(actx.destination);
  const osc=actx.createOscillator(),g=actx.createGain();osc.frequency.value=30;g.gain.value=0.0003;osc.connect(g);g.connect(actx.destination);osc.start()}
 if(actx.state=='suspended')actx.resume();gainNode.gain.value=N.vol;return actx}catch(e){return null}}
function audioKeepAlive(on){if(on)audioCtx()}
function stopSpeech(){epoch++;for(const s of sources){try{s.stop()}catch(e){}}sources=[];nextAt=0;playChain=Promise.resolve();
 if('speechSynthesis' in window)speechSynthesis.cancel()}
function serverSay(text,role){const ctx=audioCtx();if(!ctx){browserSay(text,role);return}
 const my=epoch;
 const audio=fetch('/api/tts',{method:'POST',headers:hdr(true),
   body:JSON.stringify({table,text,role,speed:N.rate})})
  .then(r=>{if(!r.ok)throw new Error('tts '+r.status);return r.arrayBuffer()})
  .then(b=>new Promise((ok,bad)=>ctx.decodeAudioData(b,ok,bad)));
 playChain=playChain.then(()=>audio).then(buf=>{if(my!=epoch)return;
   const s=ctx.createBufferSource();s.buffer=buf;s.connect(gainNode);
   const t=Math.max(ctx.currentTime+0.05,nextAt);s.start(t);nextAt=t+buf.duration+0.3;
   window.__ttsPlayed=(window.__ttsPlayed||0)+1;sources.push(s);s.onended=()=>{sources=sources.filter(x=>x!==s)}})
  .catch(()=>{if(my==epoch)browserSay(text,role)})}
function browserSay(text,role){if(!('speechSynthesis' in window))return;audioCtx();
 const txt=smoothText(text.trim());if(!txt)return;const u=new SpeechSynthesisUtterance(txt);
 const v=voices.find(v=>v.name==$(role=='npc'?'npcvoice':'nvoice').value);if(v)u.voice=v;
 u.rate=N.rate;u.volume=N.vol;u.pitch=1;speechSynthesis.speak(u)}
function flushSpeech(){const q=speechQueue;speechQueue=[];if(N.mode=='off')return;
 for(const item of q){
  // split very long passages at sentence ends (~1200 chars per piece)
  const sentences=item.text.match(/[^.!?]+[.!?”"']*\s*|.+$/g)||[item.text];
  let buf='';const parts=[];
  for(const sn of sentences){if((buf+sn).length>1200&&buf){parts.push(buf);buf=''}buf+=sn}
  if(buf.trim())parts.push(buf);
  for(const part of parts){if(useServer())serverSay(part.trim(),item.role);else browserSay(part,item.role)}}}
// ---- per-line "read this again" buttons
function addReadButton(d){const b=document.createElement('span');b.className='rd';b.title='Read this aloud';
 b.innerHTML='&#128264;';b.onclick=e=>{e.stopPropagation();readLine(d)};d.appendChild(b)}
function lineText(d){const c=d.cloneNode(true);c.querySelectorAll('.rd').forEach(x=>x.remove());return c.textContent.trim()}
function readLine(d){let t=lineText(d);if(!t)return;
 let role='gm';const m=t.match(/^([A-Z][\w' .-]{0,30}): \u201c(.*)\u201d$/);
 if(m){role='npc';t=m[1]+' says: '+m[2]}
 t=t.replace(/^>\s*/,'').replace(/: d20=.*?-> */,'. ').replace(/\bd20=\S+/g,'').replace(/[◆—]/g,' ').replace(/\s+/g,' ').trim();
 if(!t)return;
 stopSpeech();audioCtx();
 document.querySelectorAll('#story>div.reading').forEach(x=>x.classList.remove('reading'));
 d.classList.add('reading');setTimeout(()=>d.classList.remove('reading'),Math.min(15000,1500+t.length*70));
 if(useServer())serverSay(t,role);else browserSay(t,role)}
function narrateEvent(ev){if(!primed||N.mode=='off')return;
 if(ev.t=='narrate'){speak(ev.text,ev.kind=='npc'?'npc':'gm')}
 else if(ev.t=='line'&&N.mode=='all'){let t=ev.text;
  if(/\x1b\[([0-9]+;)*(2|96|95|93|33)(;[0-9]+)*m/.test(t))return;
  const colored=/\x1b\[([0-9]+;)*(91|92|31|32)(;[0-9]+)*m/.test(t);
  t=strip(t).trim();
  if(!t||/^(\d+\.|>|--|\||=|\+|\[)/.test(t))return;
  if(/\bHP -?\d+\/|\| melee:|: (unhurt|scratched|wounded|badly wounded|near death|dead)\b/.test(t))return;
  if(!colored&&!/\b(attacks|casts|takes \d+|slain|falls|rushes|flees|charges|CHARGES|drinks|pours|moves|closes in|turned|crumbles|wakes|asleep|PARALYZED|prone|stabilizes|dying)\b/.test(t))return;
  t=t.replace(/: d20=.*?-> */,'. ').replace(/\(.*?\)/g,'');speak(t,'gm')}}
function test(msg){stopSpeech();if(N.mode!='off'){speak(msg,'gm');flushSpeech()}}
function showEngine(){$('browservoices').style.display=useServer()?'none':'block';
 $('servernote').textContent=N.engine=='server'?(tts.available?'Server voices: narrator '+(tts.voices.gm||'?')+', characters '+(tts.voices.npc||'?')+'.':
   'The server voice isn\'t installed on this server, so this computer\'s voices are used instead.'):''}
(function initNarrator(){loadVoices();const m=$('nmode'),r=$('nrate'),e=$('nengine');m.value=N.mode;r.value=N.rate;e.value=N.engine;
 fetch('/api/tts/status').then(x=>x.json()).then(s=>{tts=s;showEngine()}).catch(()=>showEngine());
 m.onchange=()=>{N.mode=m.value;localStorage.setItem('nmode',N.mode);test('The narrator is ready.')};
 e.onchange=()=>{N.engine=e.value;localStorage.setItem('nengine',N.engine);showEngine();test('This is how the narrator sounds.')};
 r.onchange=()=>{N.rate=parseFloat(r.value);localStorage.setItem('nrate',r.value);test('This is the narrator speed.')};
 const sm=$('nsmooth');sm.checked=N.smooth;sm.onchange=()=>{N.smooth=sm.checked;localStorage.setItem('nsmooth',sm.checked?'1':'0');test('Testing. One sentence. Then another.')};
 const vo=$('nvol');vo.value=N.vol;vo.oninput=()=>{N.vol=parseFloat(vo.value);localStorage.setItem('nvol',vo.value);if(gainNode)gainNode.gain.value=N.vol};
 vo.onchange=()=>test('This is the narrator volume.');
 $('nvoice').onchange=ev=>localStorage.setItem('nvoice',ev.target.value);
 $('npcvoice').onchange=ev=>localStorage.setItem('npcvoice',ev.target.value);
 $('showrolls').checked=localStorage.getItem('showrolls')=='1';$('showrolls').onchange=ev=>localStorage.setItem('showrolls',ev.target.checked?'1':'0')})();

if(me&&(!NEEDPW||pw||sess)){join()}
