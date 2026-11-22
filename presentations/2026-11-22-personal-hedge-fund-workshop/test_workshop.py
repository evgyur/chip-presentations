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
 def test_sample_math(self):
  d=json.loads((D/'sample-portfolio.json').read_text());ps=d['positions'];self.assertEqual(sum(abs(p['signed_size']*p['mark_price'])for p in ps),112000);self.assertEqual(sum(p['signed_size']*p['mark_price']for p in ps),48000);self.assertEqual(sum(p['signed_size']*(p['mark_price']-p['entry_price'])for p in ps),5500)
  self.assertEqual(d['margin_used']/d['equity']*100,25)
  self.assertEqual(sum(p['signed_size']*p['mark_price']*(-.1)for p in ps if p['symbol']!='SOL'),-1800)
  self.assertEqual(int(3000/((302-294)*10)),37)
 def test_skill_archive(self):
  with zipfile.ZipFile(D/'perps-dashboard-skill.zip') as z:
   self.assertEqual(set(z.namelist()),{'perps-dashboard/SKILL.md','perps-dashboard/template.html','perps-dashboard/sample-portfolio.json'});self.assertIsNone(z.testzip())
if __name__=='__main__':unittest.main()
