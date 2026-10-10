import {it} from 'node:test';
import assert from 'node:assert/strict';
import {initialState} from '../src/lib/demo.ts';
import {scheduledItems,scheduleForMonth,upcomingDateCount} from '../src/lib/schedule.ts';
import type {WorkspaceState} from '../src/lib/workspace.ts';
const state=():WorkspaceState=>({...initialState(),events:[{id:'event',name:'Show',backendRevision:1,facts:{eventDate:'2026-10-20',deadline:'2026-10-20'},tasks:[]}],documents:[],threads:[]});
it('deduplicates project dates and excludes invalid saved deadlines',()=>{
 const s=state();s.cases[0].eventId='event';s.cases[0].deadline='2026-10-20';s.cases[1].deadline='2026-02-30';assert.equal(scheduledItems(s).length,1);
});
it('lists upcoming and past dates only in the visible month, keeping today upcoming',()=>{
 const dates=[{id:'past',project:'Past',date:'2026-10-10',label:'Event',href:'/'},{id:'today',project:'Today',date:'2026-10-11',label:'Event',href:'/'},{id:'next',project:'Next',date:'2026-10-25',label:'Event',href:'/'},{id:'nov',project:'November',date:'2026-11-02',label:'Event',href:'/'}];
 const october=scheduleForMonth(dates,'2026-10','2026-10-11');assert.deepEqual(october.upcoming.map(d=>d.id),['today','next']);assert.deepEqual(october.past.map(d=>d.id),['past']);
 assert.deepEqual(scheduleForMonth(dates,'2026-11','2026-10-11').upcoming.map(d=>d.id),['nov']);assert.equal(scheduleForMonth(dates,'2026-09','2026-10-11').upcoming.length,0);
});
it('respects selected day and year boundaries when changing calendar month',()=>{
 const dates=[{id:'dec',project:'Dec',date:'2026-12-31',label:'Event',href:'/'},{id:'jan',project:'Jan',date:'2027-01-01',label:'Event',href:'/'}];
 assert.deepEqual(scheduleForMonth(dates,'2027-01','2027-01-01','2027-01-01').upcoming.map(d=>d.id),['jan']);assert.equal(scheduleForMonth(dates,'2026-12','2027-01-01').past.length,1);
});
it('sidebar count represents distinct upcoming dates rather than past dates or duplicate deadlines',()=>{
 const s=state();s.cases[0].deadline='2026-10-20';s.cases[1].deadline='2026-10-10';assert.equal(upcomingDateCount(s,'2026-10-11'),1);
});
