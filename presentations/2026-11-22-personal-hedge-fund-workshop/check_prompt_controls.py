"""Verify one shared copy/read toolbar, exact payloads and no duplicate slide controls."""
from pathlib import Path
import argparse,json
from importlib import import_module

def main():
 sync_playwright=import_module('playwright.sync_api').sync_playwright
 d=Path(__file__).resolve().parent;a=argparse.ArgumentParser();a.add_argument('--url');a.add_argument('--report');args=a.parse_args();P=json.loads((d/'prompts.json').read_text());E=json.loads((d/'exercises.json').read_text());report={'copy_checks':0,'read_checks':0,'visible_control_checks':0,'duplicates':0,'errors':[]}
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
  try:
   c=b.new_context(permissions=['clipboard-read','clipboard-write'],viewport={'width':1920,'height':1192});g=c.new_page();g.on('pageerror',lambda e:report['errors'].append(str(e)));g.goto(args.url or (d/'slides.html').as_uri());g.evaluate('document.fonts.ready');g.wait_for_function('window.__deck?.count===21');assert g.locator('.slide-prompt-controls,.slide-copy-prompt,.slide-open-prompt').count()==0
   for size in [(1920,1192),(1366,768),(1024,768),(390,844),(320,568),(844,390)]:
    g.set_viewport_size({'width':size[0],'height':size[1]});g.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
    for i,(sid,e) in enumerate(E.items()):
     g.evaluate('(i)=>__deck.show(i)',i)
     assert g.locator('#copy-slide-prompt').count()==1 and g.locator('#open-slide-prompt').count()==1
     assert g.locator('#copy-slide-prompt,#open-slide-prompt').evaluate_all('''es=>es.every(e=>{const r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return r.left>=0&&r.right<=innerWidth+1&&(hit===e||e.contains(hit))})'''),(sid,size)
     report['visible_control_checks']+=1
     if size==(1920,1192):
      g.locator('#copy-slide-prompt').click();assert g.evaluate('navigator.clipboard.readText()')==P[e['prompt']];report['copy_checks']+=1
      for button in g.locator('.slide.active [data-prompt]').all():
       key=button.get_attribute('data-prompt');button.click();assert g.evaluate('navigator.clipboard.readText()')==P[key];report['copy_checks']+=1
      g.locator('#open-slide-prompt').click();assert g.locator('#prompt-text').inner_text()==P[e['prompt']];g.keyboard.press('Escape');report['read_checks']+=1
   g.evaluate('__deck.show(1)');g.locator('#copy-slide-prompt').focus();g.keyboard.press('Enter');assert g.evaluate('navigator.clipboard.readText()')==P[E['setup']['prompt']]
   g.evaluate("()=>{navigator.clipboard.writeText=()=>Promise.reject(new Error('denied'))}");g.locator('#copy-slide-prompt').click();assert g.locator('#prompt-panel').get_attribute('aria-hidden')=='false';assert 'Ctrl+C' in g.locator('.prompt-status').inner_text();g.keyboard.press('Escape');report['fallback']='passed'
   assert not report['errors'];print(json.dumps(report,ensure_ascii=False,indent=2))
   if args.report:Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2))
  finally:b.close()
if __name__=='__main__':main()
