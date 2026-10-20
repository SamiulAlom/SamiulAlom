import pathlib,html,math,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
BG='#0d0c20';PANEL='#17152f';INK='#f4f1ff';MUTED='#a6a0c5';PURPLE='#ab83ff';LIME='#dcff7b';PINK='#ff82c7';CYAN='#71e9ed'
def text(x,y,s,size=16,color=INK,weight=400,font='Segoe UI,Arial,sans-serif'):
 return f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{color}" font-weight="{weight}">{html.escape(str(s))}</text>'
def rect(x,y,w,h,fill=PANEL,r=20,stroke='none'):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'
def line(x,y,a,b,color='#373051'):return f'<path d="M{x} {y}L{a} {b}" stroke="{color}" fill="none"/>'
def wrap(w,h,body,title):
 return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><title>{html.escape(title)}</title><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="#a67bff"/><stop offset=".5" stop-color="#ff82c7"/><stop offset="1" stop-color="#71e9ed"/></linearGradient><radialGradient id="glow"><stop stop-color="#533c8b" stop-opacity=".6"/><stop offset="1" stop-color="#0d0c20" stop-opacity="0"/></radialGradient></defs><style>@keyframes drift{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-9px)}}}}@keyframes pulse{{0%,100%{{opacity:.45}}50%{{opacity:1}}}}.float{{animation:drift 6s ease-in-out infinite}}.pulse{{animation:pulse 3s ease-in-out infinite}}@media(prefers-reduced-motion:reduce){{.float,.pulse{{animation:none}}}}</style>{rect(0,0,w,h,BG,24)}{body}</svg>'''
def save(name,w,h,body,title): (ROOT/'assets'/name).write_text(wrap(w,h,body,title),encoding='utf-8')
def render(profile,repos,owned,langs,calendar,stamp):
 b='<ellipse cx="715" cy="220" rx="360" ry="260" fill="url(#glow)"/>'
 for x in range(0,980,32):
  for y in range(0,420,32):b+=f'<circle cx="{x}" cy="{y}" r=".8" fill="#51426b" opacity=".45"/>'
 b+=rect(32,27,916,1,'url(#g)',0)+text(36,64,'SA /',22,LIME,800)+text(103,61,'RESEARCHER. BUILDER. CURIOUS MIND.',11,MUTED,600)
 b+=text(36,120,'HELLO, WORLD. I’M',12,LIME,700)+text(32,190,'Samiul',72,INK,750)+text(32,262,'Alom.',72,INK,750)
 b+=text(36,310,'Intelligence with a purpose.',25,PURPLE,600)+text(36,344,'Medical AI · NLP · Computer Vision · Explainable AI',14,MUTED)+text(36,385,'DHAKA, BANGLADESH',11,LIME,600)
 b+='<g class="float">'+rect(584,101,346,234,'#1c1836',16,'#54406e')
 b+=rect(584,101,346,38,'#25203e',16)
 for i,c in enumerate([PINK,'#ffd182',LIME]): b+=f'<circle cx="{604+i*18}" cy="120" r="4" fill="{c}"/>'
 b+=text(676,125,'samiul / workspace',11,MUTED,400,'monospace')
 for i,(s,c) in enumerate([('$ whoami',LIME),('AI researcher + software builder',INK),('',INK),('focus = [',PURPLE),('  "healthcare", "language",',PINK),('  "vision", "useful systems"',CYAN),(']',PURPLE)]):b+=text(604,166+i*21,s,12,c,400,'monospace')
 b+='</g>'+rect(742,351,188,32,'#24203b',16)+text(761,372,'BUILD • LEARN • ITERATE',10,LIME,600)
 save('hero.svg',980,420,b,'Samiul Alom — AI researcher and software builder')
 # Focus strips double as an editorial visual introduction.
 b=''
 for i,(num,title,desc,color) in enumerate([('01','MEDICAL AI','Imaging & prediction',PINK),('02','LANGUAGE','Text & classification',CYAN),('03','SYSTEMS','Ideas into applications',LIME)]):
  x=i*326;b+=rect(x+8,8,310,108,PANEL,16)+text(x+26,36,num,12,color,700)+text(x+26,65,title,19,INK,700)+text(x+26,92,desc,13,MUTED)
 save('focus.svg',980,124,b,'Research focus: medical AI, language and useful systems')
 # Project illustrations are original abstract diagrams, not research results.
 projects=[('skin','Skin Lesion','Medical imaging experiments','JUPYTER / MEDICAL AI',PINK),('thyroid','Thyroid Segmentation','Exploring anatomical boundaries','JUPYTER / SEGMENTATION',PURPLE),('news','News Classification','Finding structure in language','JUPYTER / NLP',CYAN),('agro','AgroAI','Agriculture meets software','PYTHON / DJANGO',LIME)]
 for idx,(key,title,desc,tag,c) in enumerate(projects):
  b=rect(1,1,478,258,PANEL,20,'#38304f')+text(25,34,f'0{idx+1} / SELECTED WORK',10,c,700)+text(25,190,title,27,INK,700)+text(25,216,desc,13,MUTED)+text(25,241,tag,10,c,600)+text(438,36,'↗',23,c)
  if idx==0:
   for r in [48,35,22]:b+=f'<ellipse cx="245" cy="100" rx="{r*2}" ry="{r}" fill="none" stroke="{c}" opacity=".5"/>'
   b+='<path d="M135 100Q170 56 215 92T325 87Q346 124 278 138T135 100" fill="#ff82c7" opacity=".17"/>'
   b+=line(245,42,245,155,c)+line(130,100,355,100,c)
  elif idx==1:
   b+='<path d="M237 72C180 32 145 62 177 114S219 147 239 120C258 148 292 143 309 102S292 38 249 73Z" fill="#ab83ff" opacity=".2" stroke="#ab83ff" stroke-width="2"/>'
   for x,y in [(177,78),(207,58),(239,96),(278,60),(301,103),(263,133)]:b+=f'<circle cx="{x}" cy="{y}" r="4" fill="{c}"/>'
  elif idx==2:
   for i,w in enumerate([170,135,158]):b+=rect(75,61+i*28,w,9,'#3d5c6b',4)
   b+=line(260,70,320,100,c)+line(260,125,320,100,c)
   for j in range(3):b+=rect(333,53+j*34,80,24,'#20444d',7)+text(343,69+j*34,['TOPIC A','TOPIC B','TOPIC C'][j],9,c,600)
  else:
   b+='<path d="M234 145V72M234 114Q158 108 177 62Q234 61 234 114M234 94Q240 40 305 54Q306 95 234 94" fill="none" stroke="#dcff7b" stroke-width="3"/>'
   b+=rect(90,120,65,12,'#3d4e32',5)+rect(324,91,65,12,'#3d4e32',5)+line(155,126,199,126,c)+line(289,97,324,97,c)
  save('project-'+key+'.svg',480,260,b,title+' — '+desc)
 # Statistics: strong typographic tiles, full-year heatmap and language distribution.
 b=text(30,44,'THE WORK, IN NUMBERS',12,LIME,700)+text(30,81,'Small steps. Visible progress.',29,INK,700)
 vals=[(len(repos),'PUBLIC REPOS',PURPLE),(profile['followers'],'FOLLOWERS',PINK),(sum(r['stargazers_count'] for r in owned),'STARS / OWN REPOS',CYAN),(calendar['totalContributions'],'CONTRIBUTIONS / YEAR',LIME)]
 for i,(value,label,c) in enumerate(vals):
  x=30+i*233;b+=rect(x,105,220,112,PANEL,16)+rect(x+17,123,4,16,c,2)+text(x+30,136,label,10,MUTED,600)+text(x+20,192,value,44,c,700)
 b+=text(30,256,'CONTRIBUTION MAP',11,MUTED,600)
 weeks=calendar['weeks'][-53:]
 for i,w in enumerate(weeks):
  for d in w['contributionDays']:
   import datetime
   day=(datetime.date.fromisoformat(d['date']).weekday()+1)%7;n=d['contributionCount'];c=['#25203c','#49336f','#7147a5','#ab83ff','#dcff7b'][0 if not n else 1 if n<3 else 2 if n<6 else 3 if n<10 else 4]
   b+=f'<g><title>{d["date"]}: {n} contributions</title>'+rect(30+i*17,280+day*17,13,13,c,3)+'</g>'
 b+=text(30,422,weeks[0]['contributionDays'][0]['date'],11,MUTED)+text(830,422,weeks[-1]['contributionDays'][-1]['date'],11,MUTED)
 b+=text(30,471,'REPOSITORY DNA',11,LIME,700)+text(30,500,'Languages behind the projects',25,INK,600)
 top=langs.most_common(5);rest=sum(langs.values())-sum(v for _,v in top)
 if rest:top.append(('Other',rest))
 total=sum(langs.values()) or 1;x=30;colors=[PURPLE,PINK,CYAN,LIME,'#ffd182','#7f8dbb']
 for i,(name,v) in enumerate(top):
  width=920*v/total;b+=rect(x,523,width-2,14,colors[i],3);x+=width
 for i,(name,v) in enumerate(top):
  x=30+i%3*310;y=574+i//3*40;b+=f'<circle cx="{x+5}" cy="{y-5}" r="4" fill="{colors[i]}"/>'+text(x+18,y,f'{name} · {v}',13,INK,500)
 b+=text(30,658,'Primary languages of public, non-fork repositories. Counts are repositories, not proficiency.',11,MUTED)+text(30,683,'Updated '+stamp+' · Daily GitHub Actions refresh',11,MUTED)
 save('stats.svg',980,708,b,'Daily GitHub stats, contribution calendar and language distribution')
 # Recognizable official Devicon vector icons, stored locally for reliable rendering.
 icons=[('python','python-original'),('jupyter','jupyter-original'),('typescript','typescript-original'),('javascript','javascript-original'),('react','react-original'),('django','django-plain'),('postgresql','postgresql-original'),('git','git-original')]
 for name,file in icons:
  dest=ROOT/'assets/icons'/f'{name}.svg'
  if not dest.exists():
   with urllib.request.urlopen(f'https://raw.githubusercontent.com/devicons/devicon/master/icons/{name}/{file}.svg',timeout=30) as r:dest.write_bytes(r.read())
 b=text(30,43,'MY TOOLBOX',11,LIME,700)
 for i,(name,_) in enumerate(icons):
  import base64
  x=30+i*116;b+=rect(x,61,108,108,PANEL,14)+f'<image x="{x+32}" y="78" width="44" height="44" href="data:image/svg+xml;base64,{base64.b64encode((ROOT/"assets/icons"/(name+".svg")).read_bytes()).decode()}"/>'+text(x+54,151,name.title(),11,INK,500).replace(f'x="{x+54}"',f'x="{x+54}" text-anchor="middle"')
 save('stack.svg',980,190,b,'Python, Jupyter, TypeScript, JavaScript, React, Django, PostgreSQL and Git')
 b=text(35,51,'LET’S BUILD SOMETHING USEFUL.',23,LIME,700)+text(35,84,'Research ideas, thoughtful software, and the next interesting question.',15,MUTED)+text(910,70,'↗',45,PINK)
 save('connect.svg',980,120,b,'Connect with Samiul Alom on LinkedIn')

 # Contribution streaks use the same rolling-year data as the calendar.
 days=sorted([d for w in calendar['weeks'] for d in w['contributionDays']],key=lambda d:d['date'])
 best=run=0
 for d in days:
  run=run+1 if d['contributionCount'] else 0
  best=max(best,run)
 current=0
 recent=days[:-1] if days and not days[-1]['contributionCount'] else days
 for d in reversed(recent):
  if not d['contributionCount']:break
  current+=1
 active=sum(bool(d['contributionCount']) for d in days)
 b=text(30,40,'SHOWING UP, ONE DAY AT A TIME',11,LIME,700)
 for i,(value,label,c) in enumerate([(current,'CURRENT STREAK',PINK),(best,'LONGEST / ROLLING YEAR',PURPLE),(active,'ACTIVE DAYS / ROLLING YEAR',CYAN)]):
  x=30+i*313
  b+=rect(x,64,294,132,PANEL,16)+text(x+20,94,label,10,MUTED,600)
  b+=text(x+20,155,value,47,c,700)+text(x+100,155,'days',15,MUTED)
 b+=text(30,226,'Consecutive contribution days in GitHub’s calendar; current streak allows an unfinished today.',11,MUTED)
 save('streak.svg',980,250,b,'Current contribution streak, longest streak in rolling year, and active contribution days')
 # A local typing animation avoids depending on a remote typing-image service.
 b='<defs><clipPath id="typing"><rect width="0" height="90"><animate attributeName="width" values="0;900;900;0" keyTimes="0;.45;.88;1" dur="9s" repeatCount="indefinite"/></rect></clipPath></defs>'
 b+='<g clip-path="url(#typing)">'+text(28,56,'AI researcher. Software builder. Always exploring.',27,PURPLE,600,'monospace')+'</g>'
 save('typing.svg',980,90,b,'AI researcher. Software builder. Always exploring.')

 b=text(30,39,'RESEARCH • TEACHING • COMMUNITY',11,LIME,700)
 for i,(value,label,detail,c) in enumerate([('3.74 / 4','B.SC. CSE · IUBAT','Graduated January 2026',PURPLE),('8+','FACULTY COLLABORATORS','Cross-domain research',PINK),('350+','SEMINAR PARTICIPANTS','Students and faculty',CYAN)]):
  x=30+i*313
  b+=rect(x,61,294,143,PANEL,16)+text(x+20,92,label,10,MUTED,600)+text(x+20,142,value,38,c,700)+text(x+20,179,detail,12,MUTED)
 save('academic.svg',980,230,b,'Education and academic engagement from Samiul Alom’s CV')
