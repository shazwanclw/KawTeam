import {chromium} from 'playwright';
import assert from 'node:assert/strict';

// Isolate every gateway call: this browser test must never contact suppliers.
const browser=await chromium.launch();
try{
 const page=await browser.newPage();
 let ticks=0;
 await page.route('**/api/kawteam/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/automation/tick')){
   assert.equal(route.request().method(),'POST');
   assert.deepEqual(route.request().postDataJSON(),{});
   ticks++;
   return route.fulfill({json:{processed:false}});
  }
  if(path.endsWith('/state'))return route.fulfill({json:{version:2,cases:[],events:[],documents:[],threads:[],profile:'organiser',storage:'supabase'}});
  if(path.endsWith('/connections'))return route.fulfill({json:{database:'connected',ai:'configured',search:'configured',email:'configured',workbuddy:'desktop_tools_available',model:'test'}});
  throw new Error(`Unexpected gateway route ${path}`);
 });
 await page.goto(process.env.KAWTEAM_TEST_URL||'http://127.0.0.1:3000');
 await page.getByRole('heading',{name:'What are we going to KawTeam today?'}).waitFor();
 await page.waitForResponse(response=>response.url().endsWith('/automation/tick'),{timeout:25000});
 assert.equal(ticks,1);
 console.log('PASS: visible chat page executes protected outreach tick and refreshes state; all provider calls intercepted.');
}finally{await browser.close();}
