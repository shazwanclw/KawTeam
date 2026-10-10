import {test} from 'node:test';
import assert from 'node:assert/strict';
import {initialState} from '../src/lib/demo.ts';
import {projectTasks, taskCases, taskProgress, taskDates} from '../src/lib/tasks.ts';
import {agentStatus,approvalItems} from '../src/lib/activity.ts';
import {scheduledItems} from '../src/lib/schedule.ts';
import type {WorkspaceState} from '../src/lib/workspace.ts';

const state=():WorkspaceState=>({...initialState(),events:[{id:'tech-night',name:'Tech Night',facts:{},backendRevision:1,tasks:[{id:'shirts',name:'Shirts',createdAt:'2026-10-11'}]}],documents:[],threads:[]});

test('saved tasks and legacy requests become distinct project task rows',()=>{
 const s=state();s.cases[0].eventId='tech-night';
 assert.deepEqual(projectTasks(s,s.events[0]).map(t=>t.id),['shirts','case-totes']);
 s.cases[0].taskId='shirts';
 assert.equal(projectTasks(s,s.events[0]).length,1);
 assert.equal(taskCases(s,'tech-night','shirts').length,1);
 assert.equal(taskCases(s,'elsewhere','shirts').length,0);
});

test('approved suppliers are not counted as secured and each pending vendor counts',()=>{
 const c=initialState().cases[0];c.selectionTarget=10;
 c.approvalQueue=[{vendorId:'willow',status:'approved',reason:''},{vendorId:'campus',status:'approval_needed',reason:''},{vendorId:'meridian',status:'secured',reason:''}];
 assert.deepEqual(taskProgress([c]),{target:10,secured:1,approved:1,pending:1});
});

test('task dates include only its saved deadline and current supplier arrival',()=>{
 const c=initialState().cases[0];c.approvalQueue=[{vendorId:'willow',status:'secured',reason:''}];
 const dates=taskDates([c],'2026-10-11');
 assert.equal(dates.length,2);assert.ok(dates.every(d=>d.date>='2026-10-11'));
 assert.equal(taskDates([c],'2026-11-01').length,0);
});

test('task approvals replace outgoing message checkpoints and status waits for confirmation',()=>{
 const c=initialState().cases[0];c.approvalQueue=[{vendorId:'willow',status:'approved',reason:''}];
 assert.equal(approvalItems([c]).length,1);
 assert.equal(approvalItems([c])[0].kind,'supplier');
 assert.equal(agentStatus([c]).label,'Awaiting supplier confirmation');
 c.approvalQueue[0].status='secured';
 assert.equal(agentStatus([c]).label,'Target secured');
});

test('ready quote expiry is included among a task\'s important dates',()=>{
 const c=initialState().cases[0];c.vendors[2].validUntil='2026-10-15';
 c.approvalQueue=[{vendorId:'willow',status:'approval_needed',reason:''}];
 assert.ok(taskDates([c],'2026-10-11').some(d=>d.date==='2026-10-15'&&d.label.includes('Quote expires')));
});

test('saved supplier commitments update the global calendar too',()=>{
 const s=state();const c=s.cases[0];c.eventId='tech-night';c.vendors[2].validUntil='2026-10-15';
 c.approvalQueue=[{vendorId:'willow',status:'approved',reason:''}];
 assert.ok(scheduledItems(s).some(d=>d.date==='2026-10-23'&&d.label.includes('delivery')));
 assert.ok(scheduledItems(s).some(d=>d.date==='2026-10-15'&&d.label.includes('Quote expires')));
 c.approvalQueue[0].status='secured';
 assert.ok(!scheduledItems(s).some(d=>d.label.includes('Quote expires')));
});

test('earlier project-wide conversations remain visible as legacy tasks',()=>{
 const s=state();s.threads=[{id:'event-tech-night',eventId:'tech-night',backendRevision:1,messages:[{id:'old',role:'user',body:'Earlier note',time:'2026-10-10T10:00:00Z'}]}];
 assert.ok(projectTasks(s,s.events[0]).some(t=>t.id==='legacy-tech-night'));
});
