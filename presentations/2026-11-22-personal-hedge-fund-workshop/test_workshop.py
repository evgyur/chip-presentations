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
 def test_skill_archive(self):
  with zipfile.ZipFile(D/'perps-dashboard-skill.zip') as z:
   self.assertEqual(set(z.namelist()),{'perps-dashboard/SKILL.md','perps-dashboard/template.html','perps-dashboard/portfolio.json','perps-dashboard/hype-liquidation.json','perps-dashboard/build_snapshot.py'});self.assertIsNone(z.testzip())
if __name__=='__main__':unittest.main()
