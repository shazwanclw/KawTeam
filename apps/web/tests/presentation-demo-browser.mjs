import {chromium} from 'playwright';
import {readFile,mkdir} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {resolve} from 'node:path';

// Read-only snapshot exported after the remote reset. All browser gateway calls are mocked.
let fixture;
try { fixture=await readFile('test-results/premium/remote-demo-snapshot.json','utf8'); }
catch(error) {
 if(error.code!=='ENOENT')throw error;
 const python=resolve('../api/.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
 const result=spawnSync(python,['-c',"import json; from kawteam.demo_scenarios import build_demo; from kawteam.tasks import task_queue; from kawteam.workflow import fit; s=build_demo(); [(c.update(approvalQueue=task_queue(c)),[v.update(serverFit=fit(c,v)) for v in c['vendors']]) for c in s['cases']]; s.update(profile='organiser',storage='supabase'); print(json.dumps(s))"],{cwd:resolve('../api'),env:{...process.env,PYTHONPATH:'src'},encoding:'utf8'});
 assert.equal(result.status,0,'Offline fixture generation failed; set up the API virtual environment.');
 fixture=result.stdout;
}
const state=JSON.parse(fixture);
assert.equal(state.events.length,3);
assert.equal(state.cases.reduce((n,c)=>n+c.messages.length,0),88);
assert.equal(state.cases.find(c=>c.id==='demo-market-vendors').quantity,1);
const browser=await chromium.launch({headless:true});
await mkdir('test-results/premium/demo',{recursive:true});
try {
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 await page.route('**/api/kawteam/**',route=>{
  const path=new URL(route.request().url()).pathname;
  return route.fulfill({json:path.endsWith('/state')?state:path.endsWith('/connections')?{database:'connected',ai:'configured',email:'configured',search:'configured',workbuddy:'desktop_tools_available'}:path.endsWith('/automation/tick')?{processed:false}:{}});
 });
 const base=process.env.KAWTEAM_TEST_URL||'http://127.0.0.1:3000';
 for(const project of state.events){
  await page.goto(`${base}/projects/${project.id}`);
  await page.getByRole('heading',{name:project.name,exact:true}).waitFor();
  assert.equal(await page.locator('.project-task-row').count(),project.tasks.length);
  await page.screenshot({path:`test-results/premium/demo/${project.id}.png`,fullPage:true});
  await page.getByRole('button',{name:'Choose task',exact:true}).click();
  await page.getByRole('menuitem',{name:project.tasks[0].name,exact:true}).click();
  assert.equal(await page.locator('.chat-message').count(),2);
 }
 for(const request of state.cases){
  await page.goto(`${base}/projects/${request.eventId}/tasks/${request.taskId}`);
  await page.getByRole('heading',{name:request.title,exact:true}).waitFor();
  assert.equal(await page.locator('.task-history-button').count(),request.vendors.length);
  assert.equal(await page.locator('.task-supplier-row.secured').count(),request.approvalQueue.filter(r=>r.status==='secured').length);
  assert.equal(await page.getByRole('button',{name:'Check demo confirmation',exact:true}).count(),request.approvalQueue.filter(r=>r.status==='approved').length);
  await page.screenshot({path:`test-results/premium/demo/${request.id}.png`,fullPage:true});
  const vendor=request.vendors[0];
  await page.getByRole('button',{name:`Email history: ${vendor.name}`,exact:true}).click();
  assert.equal(await page.locator('.supplier-history-message').count(),request.messages.filter(m=>m.vendorId===vendor.id).length);
  await page.getByRole('dialog').getByRole('button',{name:'Close',exact:true}).click();
 }
 await page.goto(`${base}/overview/approvals`);
 await page.locator('.approval-reference-card').first().waitFor();
 assert.equal(await page.locator('.approval-reference-card').count(),8);
 await page.screenshot({path:'test-results/premium/demo/overview-approvals.png',fullPage:true});
 await page.goto(`${base}/connections`);
 await page.locator('.vendor-record').first().waitFor();
 assert.equal(await page.locator('.vendor-record').count(),19);
 console.log('PASS: remote-seeded three projects, four saved chats, eight approvals, nineteen connections, full email timelines and separate controlled confirmation controls; no provider calls.');
} finally { await browser.close(); }
