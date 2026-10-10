import {describe,it} from 'node:test';
import assert from 'node:assert/strict';
import {initialState,type ProcurementCase} from '../src/lib/demo.ts';
import {recentActivity,vendorConnections,approvalItems,agentStatus} from '../src/lib/activity.ts';

const sample=():ProcurementCase=>({...structuredClone(initialState().cases[0]),eventId:'tech-night'});

describe('Saved activity ordering and scope',()=>{
  it('shows newest timestamped actions first and limits the table to 15',()=>{
    const c=sample();c.events=Array.from({length:20},(_,i)=>({id:`e${i}`,title:`Action ${i}`,detail:'Saved detail',time:`2026-10-10T10:${String(i).padStart(2,'0')}:00+08:00`,kind:'research' as const}));
    const items=recentActivity([c]);assert.equal(items.length,15);assert.equal(items[0].event.id,'e19');assert.equal(items[14].event.id,'e5');
  });
  it('uses occurredAt before a display clock and leaves undated sample actions behind dated work',()=>{
    const c=sample();c.events=[{id:'sample',title:'Sample',detail:'Old',time:'23:59',kind:'research'}, {id:'new',title:'New',detail:'Recorded',time:'09:00',occurredAt:'2026-10-11T09:00:00+08:00',kind:'research'}] as typeof c.events;
    assert.equal(recentActivity([c])[0].event.id,'new');
  });
  it('keeps project and subproject activity isolated',()=>{
    const a=sample(),b=sample(),d=sample();b.id='b';b.eventId='workshop';d.id='d';d.taskId='shirts';
    assert.equal(recentActivity([a,b,d],{projectId:'tech-night',taskId:'shirts'}).length,d.events.length);
    assert.equal(recentActivity([a,b,d],{projectId:'tech-night',taskId:null}).length,a.events.length);
  });
});

describe('Connection relationships',()=>{
  it('does not count discovery or prepared drafts as a supplier connection',()=>{
    assert.equal(vendorConnections([sample()]).length,0);
  });
  it('keeps only suppliers with actual recorded messages or a human choice',()=>{
    const c=sample();c.selectedVendorId='willow';c.messages=[{id:'sent',vendorId:'campus',direction:'sent',body:'Enquiry',time:'2026-10-10T10:00:00+08:00',executionMode:'demo'}];
    assert.deepEqual(vendorConnections([c]).map(r=>r.vendor.id).sort(),['campus','willow']);
  });
  it('ignores draft-shaped message records and deduplicates supplier identity across requests',()=>{
    const a=sample(),b=sample();a.selectedVendorId='willow';b.id='b';b.vendors[2].id='new-willow';b.selectedVendorId='new-willow';b.messages=[{id:'draft',vendorId:'campus',direction:'draft',body:'Not sent',time:'10:00',executionMode:'demo'}];
    const records=vendorConnections([a,b]);assert.equal(records.length,1);assert.equal(records[0].cases.length,2);assert.equal(records[0].selectedCount,2);
  });
  it('counts a request once when refreshed candidates repeat the same supplier identity',()=>{
    const c=sample();c.selectedVendorId='willow';c.vendors.push({...c.vendors[2],id:'willow-refresh'});c.messages=[{id:'reply',vendorId:'willow-refresh',direction:'received',body:'Confirmed',time:'10:00',executionMode:'demo'}];
    const records=vendorConnections([c]);assert.equal(records.length,1);assert.equal(records[0].cases.length,1);assert.equal(records[0].messages.length,1);
  });
});

describe('Human checkpoint eligibility',()=>{
  it('includes pending exact drafts and confirmed final decisions separately',()=>{
    const c=sample();assert.deepEqual(approvalItems([c],undefined,'2026-10-10').map(r=>r.kind),['message','decision']);
  });
  it('retains approved drafts awaiting explicit send and excludes completed human decisions',()=>{
    const c=sample();c.draft.status='approved';c.selectedVendorId='willow';c.stage='decided';
    const items=approvalItems([c],undefined,'2026-10-10');assert.equal(items.length,1);assert.equal(items[0].status,'approved');
  });
  it('does not request a final choice for unconfirmed, expired or unrelated sample quotes',()=>{
    const c=sample();c.vendors[2].validUntil='2026-10-09';assert.equal(approvalItems([c],undefined,'2026-10-10').some(r=>r.kind==='decision'),false);
    const unrelated=sample();unrelated.id='other';assert.equal(approvalItems([unrelated],undefined,'2026-10-10').some(r=>r.kind==='decision'),false);
  });
  it('keeps global overview project filters accurate',()=>{
    assert.equal(approvalItems([sample()],'different','2026-10-10').length,0);
  });
});

describe('Honest agent status',()=>{
  it('shows active work only while an actual request is running',()=>{
    assert.equal(agentStatus([],false).label,'Ready for a request');assert.equal(agentStatus([],true).label,'Working on your request');
  });
  it('distinguishes review and an unanswered supplier message',()=>{
    const c=sample();assert.equal(agentStatus([c],false).label,'Awaiting your review');c.draft.status='sent';c.messages=[{id:'s',vendorId:'willow',direction:'sent',body:'Hello',time:'10:00',executionMode:'demo'}];
    assert.equal(agentStatus([c],false).label,'Awaiting supplier reply');
  });
});
