import {chromium} from 'playwright';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';

// Isolated visual fixture: every application gateway call is mocked.
const phase=process.env.KAWTEAM_VISUAL_PHASE||'before';
const base=process.env.KAWTEAM_TEST_URL||'http://127.0.0.1:3000';
const dir=`test-results/premium/${phase}`;
await mkdir(dir,{recursive:true});
const project={id:'visual-project',name:'Tech Night',facts:{eventDate:'2026-10-25',deadline:'2026-10-22',location:'Subang Jaya'},backendRevision:1,tasks:[{id:'shirts',name:'T-shirt merchandise',createdAt:'2026-10-11'}]};
const vendor={id:'print',name:'Campus Print',initials:'CP',location:'Subang Jaya',color:'sage',executionMode:'demo',goodsSen:165000,deliverySen:5000,initialSen:180000,arrival:'2026-10-22',validUntil:'2026-10-20',specsConfirmed:true,status:'Ready',description:'Cotton event T-shirts with front screen printing.',strengths:['Within budget','Delivery included'],concerns:[],quoteRef:'CP-1022'};
const request={id:'visual-case',eventId:project.id,taskId:'shirts',title:'T-shirt merchandise',goal:'Source 50 printed shirts within RM2,000 for Tech Night.',quantity:50,budgetSen:200000,targetSen:200000,selectionTarget:1,location:'Subang Jaya',deadline:'2026-10-22',vendors:[vendor,{...vendor,id:'other',name:'Meridian Merchandise',initials:'MM',goodsSen:175000},{...vendor,id:'secured',name:'Willow Supply Studio',initials:'WS'}],events:[{id:'research',kind:'research',title:'Supplier research completed',detail:'Found suppliers matching the budget and printing requirements.',time:'2026-10-11T09:00:00+08:00'},{id:'outreach',kind:'mail',title:'Three suppliers contacted',detail:'Enquiries sent for cotton shirts and delivery to Subang Jaya.',time:'2026-10-11T10:00:00+08:00'},{id:'offers',kind:'offer',title:'Supplier terms ready for review',detail:'Campus Print confirmed the quote, printing and delivery.',time:'2026-10-11T12:00:00+08:00'}],stage:'decision',selectedVendorId:null,approvalQueue:[{vendorId:'print',status:'approval_needed',rank:1,reason:'Meets the brief with the lowest total cost'},{vendorId:'other',status:'waitlisted',rank:2,reason:'Meets the brief'},{vendorId:'secured',status:'secured',rank:3,reason:'Confirmed'}],messages:[{id:'outgoing',vendorId:'print',direction:'sent',body:'Hello, could you quote for 50 cotton shirts with front printing for Tech Night? Our budget is RM2,000 including delivery to Subang Jaya by 22 October.',subject:'Tech Night — printed shirts enquiry',at:'2026-10-11T09:00:00+08:00',executionMode:'demo'},{id:'reply',vendorId:'print',direction:'received',body:'We can supply 50 cotton shirts for RM1,650 plus RM50 delivery. The price includes front screen printing. Delivery by 22 October is available.',subject:'Re: Tech Night — printed shirts enquiry',receivedAtMs:String(Date.parse('2026-10-11T10:00:00+08:00')),executionMode:'demo'},{id:'clarify',vendorId:'print',direction:'sent',body:'Thank you. Please confirm the sizes can be mixed and that no additional setup charge applies.',at:'2026-10-11T11:00:00+08:00',executionMode:'demo'},{id:'confirmation',vendorId:'print',direction:'received',body:'Mixed sizes are included and there is no additional setup charge. The total is RM1,700, valid until 20 October.',receivedAtMs:String(Date.parse('2026-10-11T12:00:00+08:00')),executionMode:'demo'}],draft:{body:'',subject:'',recipient:'',status:'pending',revision:1}};
const state={version:2,profile:'organiser',events:[project],documents:[],threads:[{id:'visual-thread',eventId:project.id,taskId:'shirts',backendRevision:1,messages:[{id:'u1',role:'user',body:'Find 50 printed shirts within RM2,000 for Tech Night.',time:'2026-10-11T09:00:00Z'},{id:'a1',role:'assistant',body:'Three suppliers have replied. Campus Print confirmed 50 shirts for RM1,700 including printing and delivery. The offer is ready to review.',time:'2026-10-11T12:00:00Z'}]}],cases:[request]};
const selectors=['.flow-page-heading','.project-chat-heading','.chat-start h1','.chat-start h2','.chat-compose','.project-work-tabs','.project-task-row','.flow-table-section','.flow-table','.task-page','.task-section','.task-work-grid','.large-schedule','.flow-sidebar'];
const browser=await chromium.launch();
const reports=[];
try{
 for(const [device,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]){
  const page=await browser.newPage({viewport});
  await page.route('**/api/kawteam/**',route=>{const path=new URL(route.request().url()).pathname;return route.fulfill({json:path.endsWith('/state')?state:path.endsWith('/connections')?{database:'connected',ai:'configured',search:'configured',email:'configured',workbuddy:'desktop_tools_available'}:path.endsWith('/automation/tick')?{processed:false}:{}});});
  async function capture(name,path,action){
   await page.goto(base+path);await page.locator('.flow-app').waitFor();await page.waitForTimeout(450);
   if(action)await action();
   await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(350);
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${device}/${name} horizontal overflow`);
   const geometry=await page.evaluate(selectors=>Object.fromEntries(selectors.map(s=>[s,[...document.querySelectorAll(s)].map(el=>{const r=el.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};})])),selectors);
   const text=await page.locator('main').innerText();
   reports.push({name:`${device}-${name}`,geometry,text});
   await page.screenshot({path:`${dir}/${device}-${name}.png`,fullPage:true});
  }
  await capture('home','/');
  await capture('sidebar','/',()=>page.getByRole('button',{name:'Open navigation',exact:true}).click());
  await page.getByRole('button',{name:'Collapse navigation',exact:true}).click();
  await capture('project',`/projects/${project.id}`);
  await capture('transcript',`/projects/${project.id}`,async()=>{await page.getByRole('button',{name:'Choose task',exact:true}).click();await page.getByRole('menuitem',{name:'T-shirt merchandise',exact:true}).click();});
  await capture('task',`/projects/${project.id}/tasks/shirts`);
  await capture('history',`/projects/${project.id}/tasks/shirts`,()=>page.getByRole('button',{name:'Email history: Campus Print',exact:true}).click());
  await capture('activity','/overview/activity');
  await capture('approval','/overview/approval');
  await capture('calendar','/overview/calendar');
  await capture('connections','/connections');
  await page.close();
 }
 await writeFile(`${dir}/geometry.json`,JSON.stringify(reports,null,2));
 if(phase==='after'){
  const before=JSON.parse(await readFile('test-results/premium/before/geometry.json','utf8'));
  const changes=[];
  for(const report of reports){const prior=before.find(r=>r.name===report.name);assert.equal(report.text,prior.text,`${report.name} visible wording changed`);for(const [selector,boxes] of Object.entries(report.geometry)){assert.equal(boxes.length,prior.geometry[selector].length,`${report.name} ${selector} count changed`);boxes.forEach((box,i)=>{for(const dimension of ['x','y','width','height']){const delta=Math.abs(box[dimension]-prior.geometry[selector][i][dimension]);if(delta>1)changes.push({screen:report.name,selector,index:i,dimension,delta});}});}}
  await writeFile(`${dir}/layout-comparison.json`,JSON.stringify(changes,null,2));
  assert.equal(changes.length,0,'Component restyling must preserve measured layout geometry');
  console.log(`Captured ${reports.length} mocked screenshots; visible wording preserved; ${changes.length} geometry differences greater than 1px (inspect layout-comparison.json).`);
 }else console.log(`Captured ${reports.length} mocked baseline screenshots and geometry.`);
}finally{await browser.close();}
