import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const browser=await chromium.launch();
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 await page.goto((process.env.KAWTEAM_TEST_URL||'http://127.0.0.1:3000')+'/projects/tech-night');
 await page.getByRole('heading',{name:'Tech Night',exact:true}).waitFor();
 assert.equal(await page.getByRole('navigation',{name:'Project sections',exact:true}).count(),0);
 await page.getByRole('button',{name:'Choose task',exact:true}).waitFor();
 await page.getByRole('tab',{name:'All Task',exact:true}).waitFor();
 await page.getByRole('tab',{name:'Recent Activity',exact:true}).waitFor();
 await page.getByRole('link',{name:/Open task: Totes for the tech crowd/}).click();
 await page.getByRole('heading',{name:'Secured',exact:true}).waitFor();
 await page.getByRole('heading',{name:'Approval',exact:true}).waitFor();
 await page.getByRole('heading',{name:'Upcoming events',exact:true}).waitFor();
 console.log('PASS: task-first project and secured/approval/date layout');
}finally{await browser.close();}
