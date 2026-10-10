import {chromium} from 'playwright';
import assert from 'node:assert/strict';

const browser=await chromium.launch();
try{
 const page=await browser.newPage();
 let role='organiser';const sessions=[];
 await page.route('**/api/kawteam/**',route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/session')){role=route.request().postDataJSON().profile;sessions.push(role);}
  return route.fulfill({json:path.endsWith('/state')?{version:2,profile:role,events:[],documents:[],threads:[],cases:[]}:path.endsWith('/automation/tick')?{processed:false}:{}});
 });
 await page.goto((process.env.KAWTEAM_TEST_URL||'http://127.0.0.1:3000')+'/');
 await page.getByRole('button',{name:'Open navigation',exact:true}).click();
 await page.getByRole('button',{name:/Switch profile/}).click();
 const menu=page.getByRole('menu');await menu.waitFor();
 await page.keyboard.press('Escape');
 assert.equal(await page.getByRole('button',{name:'Collapse navigation',exact:true}).count(),1);
 await page.getByRole('button',{name:/Switch profile/}).click();await menu.waitFor();
 assert.ok(await menu.evaluate(el=>Number(getComputedStyle(el).zIndex)>Number(getComputedStyle(document.querySelector('.flow-sidebar')).zIndex)),'Profile menu must render above the sidebar');
 await page.getByRole('menuitem',{name:/Guest.*Observer/}).click();
 assert.ok(sessions.includes('observer'));
 await page.getByRole('button',{name:'Switch profile, currently Observer',exact:true}).waitFor();
 assert.equal(await page.getByRole('textbox',{name:'Message KawTeam',exact:true}).isDisabled(),true);
 assert.equal(await page.getByRole('button',{name:'New project',exact:true}).isDisabled(),true);
 await page.getByRole('button',{name:/Switch profile/}).click();
 await page.getByRole('menuitem',{name:/Aina Rahman.*Organiser/}).click();
 await page.getByRole('button',{name:'Switch profile, currently Organiser',exact:true}).waitFor();
 assert.equal(await page.getByRole('textbox',{name:'Message KawTeam',exact:true}).isDisabled(),false);
 assert.equal(await page.getByRole('button',{name:'New project',exact:true}).isDisabled(),false);
 const label=page.locator('.flow-profile-label');
 assert.equal(await label.evaluate(el=>getComputedStyle(el).textAlign),'left');
 assert.equal(await label.locator('small').evaluate(el=>getComputedStyle(el).textAlign),'left');
 await page.getByRole('link',{name:'Connections',exact:true}).click();
 await page.getByRole('heading',{name:'Connections',exact:true,level:1}).waitFor();
 assert.equal(await page.getByRole('button',{name:'Collapse navigation',exact:true}).count(),1);
 await page.getByRole('link',{name:'Chat',exact:true}).click();
 assert.equal(await page.getByRole('button',{name:'Collapse navigation',exact:true}).count(),1);
 await page.setViewportSize({width:390,height:844});
 await page.getByRole('button',{name:/Switch profile/}).click();await menu.waitFor();
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 console.log('PASS: visible profile menu, signed-session role changes, Observer editing restrictions and mobile layout; gateway mocked.');
}finally{await browser.close();}
