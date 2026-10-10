import {chromium} from 'playwright';
import assert from 'node:assert/strict';

// Every gateway call is intercepted; this suite cannot send a supplier email.
const browser=await chromium.launch();
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const project={id:'compact',name:'Tech Night',facts:{},backendRevision:1,tasks:[{id:'shirts',name:'Shirts',createdAt:'2026-10-11'}]};
 const issue={id:'quantity',code:'missing_quantity',title:'Shirt quantity needed',detail:'Enquiries can continue; add the quantity when you know it.',requiredFields:['quantity'],status:'open',createdAt:'2026-10-11'};
 const state={version:2,profile:'organiser',events:[project],documents:[],threads:[],cases:[{id:'shirts-case',eventId:'compact',taskId:'shirts',title:'Shirts',goal:'Find shirts',quantity:null,budgetSen:200000,targetSen:null,location:null,deadline:'2026-10-25',vendors:[],events:[],stage:'research',selectedVendorId:null,failsafes:[issue],draft:{body:'',subject:'',recipient:'',status:'pending',revision:1}}]};
 let finishChat;let posted;
 await page.route('**/api/kawteam/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/state'))return route.fulfill({json:state});
  if(path.endsWith('/connections'))return route.fulfill({json:{database:'connected',ai:'configured',search:'configured',email:'configured',workbuddy:'desktop_tools_available',model:'test'}});
  if(path.endsWith('/automation/tick'))return route.fulfill({json:{processed:false}});
  if(path.endsWith('/session'))return route.fulfill({json:{}});
  if(path.endsWith('/chat')){
   posted=route.request().postDataJSON();
   if(!state.threads.length)state.threads=[{id:'thread',eventId:'compact',taskId:'shirts',backendRevision:1,messages:[]}];
   state.threads[0].messages.push({id:posted.requestId,role:'user',body:posted.message,time:'2026-10-11T04:00:00Z'});
   await new Promise(resolve=>{finishChat=resolve;});
   state.cases[0].failsafes[0].status='resolved';
   const assistant={id:'a-'+posted.requestId,inReplyTo:posted.requestId,role:'assistant',body:'Updated your task. I?m continuing the enquiries.',time:'2026-10-11T04:00:01Z'};
   state.threads[0].messages.push(assistant);
   return route.fulfill({json:{eventId:'compact',taskId:'shirts',assistant,state}});
  }
  throw new Error(`Unexpected route ${path}`);
 });
 await page.clock.install();
 const base=process.env.KAWTEAM_TEST_URL||'http://127.0.0.1:3000';
 await page.goto(base+'/overview/activity');
 await page.getByRole('heading',{name:'Recent Activity',exact:true,level:1}).waitFor();
 assert.equal(await page.locator('.flow-topbar-brand,.flow-topbar-location,.flow-page-heading .flow-eyebrow').count(),0);
 assert.ok((await page.getByRole('heading',{name:'Recent Activity',exact:true,level:1}).boundingBox()).y<90);
 await page.getByRole('button',{name:'Open navigation',exact:true}).click();
 await page.getByRole('button',{name:/Switch profile/}).waitFor();
 await page.getByRole('link',{name:'Tech Night',exact:true}).click();
 await page.getByRole('tab',{name:'Failsafe',exact:true}).waitFor();
 assert.equal(await page.getByRole('tab').count(),3);
 assert.equal(await page.locator('.chat-start-kicker').count(),0);
 assert.equal(await page.locator('.flow-app').evaluate(el=>el.classList.contains('nav-open')),true);
 const title=await page.getByRole('heading',{name:'Tech Night',exact:true}).boundingBox();
 const slogan=await page.getByRole('heading',{name:'Just KawTeam it!',exact:true}).boundingBox();
 assert.ok(slogan.y-title.y<130);
 assert.equal(await page.getByRole('tab',{name:'Failsafe',exact:true}).innerText(),'Failsafe\n1');
 await page.getByRole('tab',{name:'Recent Activity',exact:true}).focus();await page.keyboard.press('ArrowRight');
 assert.equal(await page.getByRole('tab',{name:'Failsafe',exact:true}).getAttribute('aria-selected'),'true');
 await page.getByRole('textbox',{name:'Reply to Shirt quantity needed'}).fill('We need 50 shirts');
 await page.getByRole('button',{name:'Send context for Shirt quantity needed'}).click();
 assert.equal(posted.taskId,'shirts');assert.equal(posted.eventId,'compact');finishChat();
 await page.getByRole('tab',{name:'Failsafe',exact:true}).waitFor({state:'detached'});
 assert.equal(await page.getByRole('tab').count(),2);
 assert.equal(await page.getByRole('tab',{name:'All Task',exact:true}).getAttribute('aria-selected'),'true');
 await page.getByRole('tab',{name:'Recent Activity',exact:true}).focus();await page.keyboard.press('ArrowRight');
 assert.equal(await page.getByRole('tab',{name:'All Task',exact:true}).getAttribute('aria-selected'),'true');
 await page.getByRole('button',{name:'Choose task',exact:true}).click();await page.getByRole('menuitem',{name:'Shirts',exact:true}).click();
 await page.getByRole('textbox',{name:'Message KawTeam'}).fill('Update the colour to blue');
 await page.getByRole('button',{name:'Send message',exact:true}).click();
 await page.getByRole('status').filter({hasText:'Thinking'}).waitFor();
 assert.equal(await page.locator('.chat-message.user').filter({hasText:'Update the colour to blue'}).count(),1);
 const poll=page.waitForResponse(r=>r.url().endsWith('/state'));await page.clock.fastForward(15000);await poll;
 assert.equal(await page.locator('.chat-message.user').filter({hasText:'Update the colour to blue'}).count(),1);
 finishChat();await page.getByRole('status').filter({hasText:'Thinking'}).waitFor({state:'hidden'});
 assert.equal(await page.locator('.chat-message.user').filter({hasText:'Update the colour to blue'}).count(),1);
 assert.equal(await page.locator('.chat-message.user').filter({hasText:'We need 50 shirts'}).count(),1);
 assert.equal(await page.locator('.chat-message.assistant').count(),2);
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(300);
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 console.log('PASS: compact shell, persistent sidebar profile, Failsafe counts/resolution, keyboard tabs, optimistic thinking and mobile width; all gateway calls mocked.');
}finally{await browser.close();}
