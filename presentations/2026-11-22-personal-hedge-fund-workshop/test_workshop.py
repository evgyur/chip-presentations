#!/usr/bin/env python3
"""Focused static artifact checks for the personal hedge fund workshop."""
from pathlib import Path
from html.parser import HTMLParser
import json,re,unittest,zipfile,subprocess
D=Path(__file__).resolve().parent
class Tags(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.copy=[];self.urls=[];self.slides=[]
 def handle_starttag(self,tag,attrs):
  t=tag;d=dict(attrs)
  if 'id'in d:self.ids.append(d['id'])
  if 'data-prompt'in d:self.copy.append(d['data-prompt'])
  if t=='article' and 'slide' in d.get('class','').split():self.slides.append(d['id'])
  if t in ('a','iframe'):
   u=d.get('href',d.get('src',''))
   if u:self.urls.append(u)
class WorkshopTests(unittest.TestCase):
 def test_deck(self):
  s=(D/'slides.html').read_text();p=Tags();p.feed(s)
  self.assertEqual(len(p.slides),21);self.assertEqual(len(p.ids),len(set(p.ids)));self.assertEqual(len(p.copy),12)
  prompts=json.loads((D/'prompts.json').read_text());self.assertTrue(set(p.copy)<=set(prompts));self.assertIn('id="prompt-copy"',s)
  match=re.search(r'const NOTES=(.*?);\nconst slides=',s,re.S);assert match is not None
  notes=json.loads(match[1]);self.assertEqual(sum(x['seconds'] for x in notes),3600)
  self.assertNotIn('Terra',s);self.assertNotIn('Сначала установите Hermes',s)
  for u in p.urls:
   if not u.startswith(('https:','http:','#','data:')):self.assertTrue((D/u.split('#')[0]).exists(),u)
 def test_selected_wallet_math(self):
  d=json.loads((D/'portfolio.json').read_text());ps=d['positions'];self.assertEqual(len(ps),4)
  self.assertEqual(d['wallet'],'0x99460c6b44fd9d93528b3b6e3365793acb40bb46')
  self.assertEqual({p['symbol'] for p in ps},{'NEAR','HYPE','ZEC','xyz:ANT'})
  self.assertAlmostEqual(sum(abs(p['signed_size']*p['mark_price'])for p in ps),3211801.91772)
  self.assertAlmostEqual(d['equity'],sum(a['equity']for a in d['accounts']))
  event=json.loads((D/'hype-liquidation.json').read_text());self.assertEqual(event['coin'],'HYPE')
  self.assertEqual(event['fill_count'],113);self.assertEqual(len({f['tid']for f in event['fills']}),113)
  self.assertTrue(all(f['liquidation']['liquidatedUser']==d['wallet'] for f in event['fills']))
  self.assertAlmostEqual(event['size'],7800);self.assertAlmostEqual(event['closed_pnl'],-61047.54828)
  self.assertTrue(event['time_msk'].startswith('2026-11-20T16:32:27'))
  self.assertTrue(all(p['signed_size']>0 for p in ps))
  s=(D/'slides.html').read_text();self.assertNotIn('0xa00d',s);self.assertNotIn('убрать BTC',s)
  self.assertIn('−$96 354,06',s);self.assertIn('−$50 724,96',s)
 def test_snapshot_sources(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('snapshot',D/'materials/perps-dashboard/build_snapshot.py');assert spec is not None and spec.loader is not None
  m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  r=json.loads((D/'wallet-source.json').read_text());d=m.normalize_dexes(r['wallet'],r['snapshots'])
  self.assertEqual(d,json.loads((D/'portfolio.json').read_text()))
 def test_mtw2_dashboard_style(self):
  s=(D/'dashboard.html').read_text();reference=(D.parent/'2026-11-18-personal-hedge-fund/index.html').read_text()
  for selector in ['.rd{','.rd-top{','.rd-safe{','.rd-warn{']:
   rule=re.search(re.escape(selector)+r'[^}]+}',reference);assert rule is not None
   self.assertIn(rule[0],s)
  self.assertIn('font-family:Body',reference)
  self.assertIn('Body,Arial,sans-serif',s);self.assertIn('@font-face',s)
  self.assertIn('id="accounts"',s);self.assertIn('id="exclude"',s)
  self.assertNotIn('64<span>/100',s);self.assertNotIn('ROI за год',s)
  self.assertEqual((D/'materials/perps-dashboard/template.html').read_text(),s)
 def test_plain_language_copy(self):
  s=(D/'slides.html').read_text();visible=re.sub(r'srcdoc=".*?"(?=>)','',s,flags=re.S)
  for phrase in ['ХОЧУ СЕБЕ ТАКОЕ','ВОТ ГДЕ НАЧИНАЕТСЯ АГЕНТ','Не предсказатель','силы убеждения','МАЛЕНЬКИЙ ЗАВЕРШЁННЫЙ ЦИКЛ','Кто-то в X уже всё объяснил','А если убрать SOL','Покажите результат, затем дайте короткое поручение']:
   self.assertNotIn(phrase,visible)
  for title in ['Дашборд кошелька Hyperliquid','Собираем дашборд в Codex','Рассчитываем размер позиции','Что останется после мастер-класса']:
   self.assertIn('<h2>'+title+'</h2>',visible)
  match=re.search(r'const NOTES=(.*?);\nconst slides=',s,re.S);assert match is not None
  notes=json.loads(match[1])
  self.assertEqual(len(notes),21);self.assertEqual(len({tuple(n['bullets']) for n in notes}),21)
  self.assertEqual(3000//((300-294)*10),50);self.assertEqual(3000//((302-294)*10),37)
 def test_metric_number_layout(self):
  s=(D/'slides.html').read_text();rule=re.search(r'\.stat-proof strong\{([^}]+)\}',s);assert rule is not None
  self.assertIn('white-space:nowrap',rule[1]);self.assertIn('font:48px',rule[1])
  self.assertIn('grid-template-columns:repeat(3,minmax(0,1fr))',s)
 def test_moex_program_order(self):
  s=(D/'slides.html').read_text();articles=re.findall(r'<article\b.*?</article>',s,re.S)
  ids=[re.findall(r'id="([^"]+)"',a)[0] for a in articles]
  expected=['cover','team','agent','idea','parallel','news','tradingview','alfa','size','project','finish','setup']
  self.assertEqual(ids[:12],expected)
  for i,a in enumerate(articles):
   self.assertIn('data-index="'+str(i)+'"',a);self.assertIn('data-for="'+str(i)+'"',a)
  for a in articles[:11]:
   a=re.sub(r'src="data:[^"]*"','',a)
   for term in ['HYPE','Hyperliquid','0x9946','perps-dashboard-skill.zip']:self.assertNotIn(term,a)
  match=re.search(r'const NOTES=(.*?);\nconst slides=',s,re.S);assert match is not None
  notes=json.loads(match[1]);self.assertEqual(sum(n['seconds'] for n in notes[:12]),3600)
  self.assertTrue(all(n['seconds']==0 for n in notes[12:]))
  self.assertTrue(all('ДОПОЛНИТЕЛЬНО /' in a for a in articles[12:]))
 def test_team_job_titles(self):
  s=(D/'slides.html').read_text();a=re.findall(r'<article[^>]*id="team".*?</article>',s,re.S)[0]
  self.assertEqual(re.findall(r'<h3>(.*?)</h3>',a),['Информационный аналитик','Рыночный аналитик','Исследователь стратегий','Риск-менеджер','Трейдер','Управляющий капиталом'])
  self.assertEqual(a.count('class="teammate role-covered"'),3);self.assertEqual(a.count('class="teammate role-not-covered"'),3)
  self.assertEqual(a.count('Не разбираем в этом эфире.'),3)
 def test_skill_archive(self):
  with zipfile.ZipFile(D/'perps-dashboard-skill.zip') as z:
   self.assertEqual(set(z.namelist()),{'perps-dashboard/SKILL.md','perps-dashboard/template.html','perps-dashboard/portfolio.json','perps-dashboard/hype-liquidation.json','perps-dashboard/build_snapshot.py'});self.assertIsNone(z.testzip())
if __name__=='__main__':unittest.main()
