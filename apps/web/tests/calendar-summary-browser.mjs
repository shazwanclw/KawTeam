import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';

const base=process.env.KAWTEAM_TEST_URL||'http://127.0.0.1:3000';
const events=['Sunway Got Talent','Kampus Weekend Market','Build Together Workshop'].map((name,i)=>({id:`project-${i}`,name,facts:{eventDate:'2026-10-25'},tasks:[],backendRevision:1}));
const cases=events.flatMap((project,index)=>Array.from({length:5},(_,i)=>({id:`case-${index}-${i}`,eventId:project.id,taskId:`task-${i}`,title:`Delivery ${i}`,goal:'Demonstration',quantity:50,budgetSen:100000,targetSen:100000,selectionTarget:1,location:'Subang Jaya',deadline:'2026-10-25',vendors:[{id:'vendor',name:`Supplier ${i}`,initials:'SP',location:'Subang Jaya',goodsSen:10000,deliverySen:0,initialSen:10000,arrival:'2026-10-25',validUntil:'2026-10-20',specsConfirmed:true,status:'Ready',strengths:[],concerns:[],executionMode:'demo'}],approvalQueue:[{vendorId:'vendor',status:'approval_needed',rank:1,reason:'Ready'}],events:[],messages:[],stage:'decision',draft:{body:'',subject:'',recipient:'',status:'pending',revision:1}})));
const state={version:2,profile:'organiser',events,cases,documents:[],threads:[]};
await mkdir('test-results/calendar-summary',{recursive:true});
const browser=await chromium.launch();
try{
 for(const [device,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]){
  const page=await browser.newPage({viewport});
  await page.route('**/api/kawteam/**',route=>route.fulfill({json:new URL(route.request().url()).pathname.endsWith('/state')?state:{processed:false}}));
  await page.goto(base+'/overview/calendar');
  await page.locator('.agenda-item').first().waitFor();
  assert.equal(await page.locator('.large-schedule>.panel-heading').count(),0);
  const cal=await page.locator('.kt-calendar').boundingBox();const legend=await page.locator('.schedule-note').boundingBox();
  assert.ok(legend.y-cal.y-cal.height>=0&&legend.y-cal.y-cal.height<16,`${device}: legend directly below calendar`);
  assert.ok(cal.width<=481,`${device}: compact calendar`);
  // Five supplier quotes per project are condensed to one project entry on each day.
  assert.equal(await page.locator('.agenda-item').count(),6);
  await page.locator('.agenda-item').filter({hasText:'Sunway Got Talent'}).first().click();
  await page.getByRole('dialog').waitFor();
  assert.equal(await page.locator('.calendar-detail-list>a').count(),5);
  assert.ok((await page.locator('.calendar-detail-list>a').first().getAttribute('href')).includes('/tasks/'));
  await page.keyboard.press('Escape');
  await page.locator('.rdp-button_next').click();
  assert.equal(await page.locator('.agenda-item').count(),0);
  assert.match(await page.locator('.agenda-month').innerText(),/November 2026/i);
  await page.locator('.rdp-button_previous').click();
  await page.locator('.agenda-item').first().waitFor();
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${device}: no horizontal overflow`);
  await page.screenshot({path:`test-results/calendar-summary/${device}.png`,fullPage:true});
  await page.close();
 }
 console.log('PASS: calendar caps daily project summaries, retains quote details/task links, changes month and fits desktop/mobile. All gateway calls mocked.');
}finally{await browser.close();}
