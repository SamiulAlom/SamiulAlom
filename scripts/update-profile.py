import os,json,urllib.request,datetime,collections,html,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
USER='SamiulAlom'
def api(path,query=None):
    headers={'User-Agent':'SamiulAlom-profile','Accept':'application/vnd.github+json'}
    if os.environ.get('GITHUB_TOKEN'): headers['Authorization']='Bearer '+os.environ['GITHUB_TOKEN']
    req=urllib.request.Request('https://api.github.com'+path,headers=headers,data=json.dumps({'query':query}).encode() if query else None)
    with urllib.request.urlopen(req,timeout=40) as res:return json.load(res)
def txt(x,y,s,size=14,color='#a6b6cd',weight=400):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="Segoe UI,Arial,sans-serif" font-size="{size}" font-weight="{weight}">{html.escape(str(s))}</text>'
def rect(x,y,w,h,fill='#101f35',r=12):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>'
def svg(height,body,title):return f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" viewBox="0 0 900 {height}" role="img"><title>{html.escape(title)}</title>'+rect(0,0,900,height,'#091321',20)+body+'</svg>'
profile=api('/users/'+USER)
repos=[]
for page in range(1,100):
    batch=api(f'/users/{USER}/repos?per_page=100&page={page}&type=owner')
    repos.extend(r for r in batch if not r.get('private'))
    if len(batch)<100:break
owned=[r for r in repos if not r['fork']]
langs=collections.Counter(r['language'] for r in owned if r['language'])
query='{ user(login:"SamiulAlom") { contributionsCollection { contributionCalendar { totalContributions weeks { contributionDays { date contributionCount color } } } } } }'
graph=api('/graphql',query)
if graph.get('errors'):raise RuntimeError('GitHub contribution query failed; retaining previous cards.')
calendar=graph['data']['user']['contributionsCollection']['contributionCalendar']
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%d %b %Y · %H:%M UTC')
body=txt(32,40,'GITHUB / LIVE SNAPSHOT',12,'#49dfd2',700)+txt(868,40,'',12)
metrics=[('PUBLIC REPOSITORIES',len(repos)),('FOLLOWERS',profile['followers']),('STARS · OWN REPOS',sum(r['stargazers_count'] for r in owned)),('CONTRIBUTIONS · YEAR',calendar['totalContributions'])]
for i,(label,value) in enumerate(metrics):
    x=32+i*212
    body+=rect(x,62,200,103)+txt(x+18,90,label,10,'#94aac7',600)+txt(x+18,140,value,36,'#edf7ff',700)
body+=txt(32,205,'A year of building',23,'#edf7ff',600)+txt(32,230,'Contribution activity reported by GitHub · rolling year',12)
weeks=calendar['weeks'][-53:]
colors=['#162941','#15505d','#167c80','#20b1a9','#53e6d5']
for i,week in enumerate(weeks):
    for d in week['contributionDays']:
        day=(datetime.date.fromisoformat(d['date']).weekday()+1)%7
        count=d['contributionCount'];level=0 if count==0 else 1 if count<3 else 2 if count<6 else 3 if count<10 else 4
        body+=f'<g><title>{d["date"]}: {count} contributions</title>'+rect(32+i*15,250+day*15,11,11,colors[level],2)+'</g>'
body+=txt(32,380,weeks[0]['contributionDays'][0]['date'],11)+txt(716,380,weeks[-1]['contributionDays'][-1]['date'],11)
body+=txt(32,425,'Tools behind the work',23,'#edf7ff',600)+txt(32,448,'Primary language by public, non-fork repository · not coding proficiency',12)
top=langs.most_common(6);denom=sum(langs.values()) or 1
palette=['#49dfd2','#7697ff','#d4a2ff','#f1bd68','#ed8eaa','#8db9c8']
for i,(name,value) in enumerate(top):
    col=i%2;row=i//2;x=32+col*430;y=480+row*54
    body+=txt(x,y,name,13,'#e3ecf7',600)+txt(x+330,y,f'{value} repos',12)
    body+=rect(x,y+10,386,6,'#172a42',3)+rect(x,y+10,386*value/denom,6,palette[i],3)
body+=txt(32,654,'Updated '+stamp,11)+txt(555,654,'Generated in this repository · daily refresh',11)
assets=ROOT/'assets';assets.mkdir(exist_ok=True)
(assets/'stats.svg').write_text(svg(680,body,'GitHub statistics and contribution activity for Md. Samiul Alom'),encoding='utf-8')
# An original vector banner. All text remains readable without animations or external assets.
hero='<defs><linearGradient id="accent"><stop stop-color="#49dfd2"/><stop offset="1" stop-color="#7697ff"/></linearGradient></defs>'
hero+='<path d="M0 305H900" stroke="url(#accent)" stroke-width="3"/>'
for x in range(560,901,24):hero+=f'<path d="M{x} 0V305" stroke="#142238" stroke-width="1"/>'
for y in range(0,306,24):hero+=f'<path d="M560 {y}H900" stroke="#142238" stroke-width="1"/>'
hero+=txt(38,47,'SAMIUL ALOM / RESEARCH & ENGINEERING',11,'#49dfd2',700)
hero+=txt(38,114,'Md. Samiul Alom',43,'#f2f7ff',700)+txt(38,159,'Exploring intelligence.',26,'#b5c7e1',500)+txt(38,194,'Building useful systems.',26,'#b5c7e1',500)
hero+=txt(38,254,'MEDICAL AI   /   NLP   /   COMPUTER VISION',11,'#49dfd2',600)
hero+=txt(38,280,'Dhaka, Bangladesh  ·  @SamiulAlom',12)
for radius in [60,93,125]:hero+=f'<circle cx="730" cy="151" r="{radius}" fill="none" stroke="#29405d" stroke-width="1"/>'
nodes=[(650,80),(793,72),(838,166),(758,244),(632,205),(730,151)]
for i,(x,y) in enumerate(nodes[:-1]):
    hero+=f'<path d="M{x} {y}L730 151" stroke="url(#accent)" stroke-width="1.5"/>'
    hero+=f'<circle cx="{x}" cy="{y}" r="7" fill="#49dfd2"/>'
hero+=rect(695,116,70,70,'#142e44',19)+txt(712,161,'AI',26,'#80eee0',700)
(assets/'hero.svg').write_text(svg(310,hero,'Md. Samiul Alom — AI research and useful software systems'),encoding='utf-8')
print('Generated profile graphics from public GitHub data:',len(repos),'repositories')
