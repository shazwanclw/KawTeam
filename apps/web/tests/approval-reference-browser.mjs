import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const browser=await chromium.launch();
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const vendor={id:'print',name:'Campus Print',initials:'CP',location:'Subang',executionMode:'demo',goodsSen:100000,deliverySen:0,arrival:'2026-10-25',specsConfirmed:true,strengths:[],concerns:[]};
 const c={id:'shirts-case',eventId:'cards',taskId:'shirts',title:'Shirts',goal:'Find 50 shirts',quantity:50,budgetSen:200000,deadline:'2026-10-25',vendors:[vendor],events:[],stage:'decision',approvalQueue:[{vendorId:'print',status:'approval_needed',rank:1}],messages:[{id:'enquiry',vendorId:'print',direction:'sent',body:'Quote for 50 shirts',executionMode:'demo'},{id:'reply',vendorId:'print',direction:'received',body:'50 shirts for RM1000. Delivery included.',executionMode:'demo'}],draft:{body:'',subject:'',recipient:'',status:'pending',revision:1},backendRevision:4};
 const state={version:2,profile:'observer',events:[{id:'cards',name:'Sunway Got Talent',facts:{},tasks:[{id:'shirts',name:'Shirts'}]}],documents:[],threads:[],cases:[c]};const actions=[];
 await page.route('**/api/kawteam/**',route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/state'))return route.fulfill({json:state});
  if(path.endsWith('/session')){state.profile=route.request().postDataJSON().profile;return route.fulfill({json:{}});}
  if(path.endsWith('/actions')){actions.push(route.request().postDataJSON());c.approvalQueue[0].status='approved';return route.fulfill({json:state});}
  return route.fulfill({json:{processed:false}});
 });
 const base=process.env.KAWTEAM_TEST_URL||'http://127.0.0.1:3000';
 await page.goto(base+'/overview/approvals');await page.locator('.approval-reference-card').waitFor();
 assert.equal(await page.locator('.flow-approval-table').count(),0);
 assert.equal(await page.locator('.approval-reference-reply').count(),0);
 assert.equal(await page.getByRole('button',{name:'View summary',exact:true}).count(),0);
 await page.getByRole('link',{name:'Open in project',exact:true}).click();
 await page.getByRole('dialog').getByRole('heading',{name:'Campus Print',exact:true}).waitFor();
 await page.getByRole('dialog').getByRole('button',{name:'Email history: Campus Print',exact:true}).click();
 await page.getByRole('heading',{name:'Email history',exact:true}).waitFor();
 assert.ok((await page.locator('.supplier-history-timeline').innerText()).includes('Quote for 50 shirts'));
 await page.keyboard.press('Escape');
 await page.keyboard.press('Escape');
 assert.equal(await page.getByRole('dialog').count(),0);
 await page.goto(base+'/overview/approvals');await page.locator('.approval-reference-card').waitFor();
 assert.deepEqual(await page.locator('.approval-reference-filters button').allTextContents(),['Approval Needed','Approved']);
 assert.equal(await page.getByRole('button',{name:'Approve supplier',exact:true}).isDisabled(),true);
 assert.equal(await page.getByRole('button',{name:'Return',exact:true}).count(),0);
 await page.getByRole('button',{name:'Open navigation',exact:true}).click();await page.getByRole('button',{name:/Switch profile/}).click();await page.getByRole('menuitem').filter({hasText:'Aina Rahman'}).click();
 await page.getByRole('button',{name:'Approve supplier',exact:true}).click();await page.locator('.approval-reference-card').waitFor({state:'detached'});
 assert.equal(actions.length,1);assert.equal(actions[0].type,'approve-vendor');assert.equal(actions[0].vendorId,'print');assert.equal(actions[0].expectedRevision,4);assert.equal(c.approvalQueue[0].status,'approved');
 await page.locator('.approval-reference-filters button').filter({hasText:'Approved'}).click();await page.locator('.approval-reference-card').waitFor();assert.equal(await page.getByRole('button',{name:'Approve supplier',exact:true}).count(),0);
 await page.goto(base+'/connections');await page.getByRole('button',{name:'View connection: Campus Print',exact:true}).waitFor();assert.equal(await page.locator('.flow-connections-table').count(),0);assert.equal(await page.locator('.flow-connections-section>.flow-section-heading').count(),0);
 await page.getByRole('textbox',{name:'Search connections'}).fill('not a supplier');assert.equal(await page.locator('.vendor-record').count(),0);
 await page.getByRole('textbox',{name:'Search connections'}).fill('Campus');await page.getByRole('button',{name:'View connection: Campus Print',exact:true}).click();await page.getByRole('dialog').getByRole('heading',{name:'Campus Print',exact:true}).waitFor();assert.ok((await page.getByRole('dialog').innerText()).includes('50 shirts for RM1000'));
 await page.keyboard.press('Escape');await page.setViewportSize({width:390,height:844});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.goto(base+'/overview/activity');await page.locator('.flow-activity-table').waitFor();assert.equal(await page.locator('.flow-table-section>.flow-section-heading').count(),0);
 console.log('PASS: approval roles/revision and human decision, two filters, connection-card search/history, activity header and mobile width. All calls mocked.');
}finally{await browser.close();}
