import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';

if(process.env.KAWTEAM_ALLOW_SAMPLE_MUTATION!=='1')throw new Error('Run this check through apps/api/tests/live_task_browser.py so the sample is restored.');

const base=process.env.KAWTEAM_TEST_URL||'http://localhost:3000';
const browser=await chromium.launch();
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
await mkdir('test-results',{recursive:true});
async function profile(role){
 await page.getByRole('button',{name:/Switch profile/}).click();
 await page.getByRole('menuitem').filter({hasText:role}).click();
 await page.getByRole('button',{name:`Switch profile, currently ${role}`,exact:true}).waitFor();
}
async function prompt(message){
 await page.getByLabel('Message KawTeam').fill(message);
 const response=page.waitForResponse(r=>r.url().endsWith('/api/kawteam/chat')&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Send message',exact:true}).click();
 const r=await response;assert.ok(r.ok(),await r.text());return r.json();
}
try{
 await page.goto(base+'/');
 await page.locator('button[aria-label="Choose project"]:not(:disabled)').waitFor();
 await profile('Organiser');
 const name='QA Task Flow '+Date.now();
 const first=await prompt(`Find vendors for 50 shirts within RM2000 by 25 October 2026 in Subang Jaya for event ${name}.`);
 await writeFile('test-results/task-flow-created.json',JSON.stringify({id:first.eventId}));
 assert.ok(first.taskId);
 await page.waitForURL(/\/projects\//);
 assert.equal(await page.getByRole('navigation',{name:'Project sections',exact:true}).count(),0);
 await page.getByRole('tab',{name:'All Task',exact:true}).waitFor();
 assert.equal(await page.getByRole('link',{name:/Open task:/}).count(),1);
 const updated=await prompt('We only want 40 shirts now.');
 assert.equal(updated.taskId,first.taskId);
 const request=updated.state.cases.find(c=>c.id===first.assistant.caseId);
 assert.equal(request.quantity,40);
 assert.equal(updated.state.cases.filter(c=>c.taskId===first.taskId).length,1);
 await page.getByRole('button',{name:'Choose task',exact:true}).click();
 await page.getByRole('menuitem').filter({hasText:'New Task'}).click();
 assert.equal(await page.getByText('We only want 40 shirts now.',{exact:true}).count(),0);
 const second=await prompt('Find 10 vendors within RM5000 by 28 October 2026 in Subang Jaya.');
 assert.notEqual(second.taskId,first.taskId);
 const multi=second.state.cases.find(c=>c.id===second.assistant.caseId);
 assert.equal(multi.selectionTarget,10);
 await page.getByRole('button',{name:'Choose task',exact:true}).click();
 await page.getByRole('menuitem').filter({hasText:'T-shirt merchandise'}).click();
 await page.getByText('We only want 40 shirts now.',{exact:true}).waitFor();
 assert.equal(await page.getByText('Find 10 vendors within RM5000 by 28 October 2026 in Subang Jaya.',{exact:true}).count(),0);
 await page.getByRole('link',{name:'Open task: T-shirt merchandise',exact:true}).click();
 await page.getByRole('heading',{name:'Secured',exact:true}).waitFor();
 await page.getByText(/Nothing ready for approval yet/).waitFor();
 await page.getByRole('link',{name:'Continue conversation',exact:true}).click();
 await page.getByText('We only want 40 shirts now.',{exact:true}).waitFor();
 await page.reload();
 await page.getByText('We only want 40 shirts now.',{exact:true}).waitFor();
 await page.screenshot({path:'test-results/task-project-conversation.png',fullPage:true});
 await profile('Observer');
 assert.equal(await page.getByLabel('Message KawTeam').isDisabled(),true);
 await profile('Organiser');

 // The controlled sample exercises the actual persisted placement state machine.
 await page.goto(base+'/projects/tech-night/tasks/case-totes');
 await page.getByRole('button',{name:'Run sample liaison',exact:true}).click();
 await page.getByRole('button',{name:'Review supplier: Willow Supply Studio',exact:true}).waitFor();
 await page.getByRole('button',{name:'Review supplier: Willow Supply Studio',exact:true}).click();
 await page.getByRole('dialog').getByRole('button',{name:'Approved',exact:true}).waitFor();
 await page.getByRole('dialog').getByRole('button',{name:'Close',exact:true}).click();
 await profile('Teammate');
 await page.getByRole('button',{name:'Review supplier: Willow Supply Studio',exact:true}).click();
 assert.equal(await page.getByRole('dialog').getByRole('button',{name:'Approved',exact:true}).isDisabled(),true);
 await page.getByRole('dialog').getByRole('button',{name:'Close',exact:true}).click();
 await profile('Organiser');
 await page.screenshot({path:'test-results/task-approval-desktop.png',fullPage:true});
 // Global approval and the task badge refer to the same ready supplier checkpoint.
 await page.goto(base+'/projects/tech-night');
 await page.locator('[data-task-approvals="1"]').waitFor();
 assert.equal(await page.locator('[data-task-approvals="1"]').count(),1);
 await page.goto(base+'/overview/approvals');
 await page.getByRole('button',{name:/Review supplier decision: Totes/}).click();
 await page.getByRole('dialog').getByRole('button',{name:'Reject',exact:true}).click();
 await page.getByRole('dialog').waitFor({state:'hidden'});
 await page.getByRole('button',{name:/Review supplier decision: Totes/}).click();
 await page.getByRole('dialog').locator('.liaison-offers').getByText('Campus Printworks',{exact:true}).waitFor();
 await page.getByRole('dialog').getByRole('button',{name:'Approved',exact:true}).click();
 await page.getByRole('dialog').getByRole('button',{name:'Close',exact:true}).click();
 await page.goto(base+'/projects/tech-night/tasks/case-totes');
 await page.getByText('1 approved supplier is awaiting confirmation.',{exact:true}).waitFor();
 assert.equal(await page.locator('.secured-section .task-supplier-row').count(),0);
 await page.getByRole('button',{name:'Check demo confirmation',exact:true}).click();
 await page.locator('.secured-section .task-supplier-row').waitFor();
 assert.equal(await page.locator('.task-secured-count').innerText(),'1 / 1');
 await page.screenshot({path:'test-results/task-secured-desktop.png',fullPage:true});
 await page.reload();
 await page.locator('.secured-section .task-supplier-row').waitFor();
 for(const width of [390,768,1280]){
  await page.setViewportSize({width,height:1000});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),`Overflow at ${width}`);
 }
 await page.setViewportSize({width:390,height:1000});
 await page.screenshot({path:'test-results/task-secured-mobile.png',fullPage:true});
 assert.deepEqual(errors,[]);
 console.log('PASS: named project/new tasks, continued edits, isolation/reload, role restrictions, task/global approval, separate secured confirmation and responsive UI.');
}finally{await browser.close();}
