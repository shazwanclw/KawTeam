import {eligible,type ProcurementCase,type Activity,type Vendor} from './demo.ts';
export type SavedActivity=Activity & {occurredAt?:string};
export type ActivityRecord={id:string;case:ProcurementCase;event:SavedActivity;timestamp:number|null};
export type ConnectionRecord={key:string;vendor:Vendor;case:ProcurementCase;cases:ProcurementCase[];messages:NonNullable<ProcurementCase['messages']>;selectedCount:number};
export type ApprovalRecord={id:string;case:ProcurementCase;kind:'message'|'decision';status:'pending'|'approved';vendors:Vendor[]};
export function recentActivity(cases:ProcurementCase[],scope:{projectId?:string;taskId?:string|null}={},limit=15):ActivityRecord[]{
  const scoped=cases.filter(c=>(!scope.projectId||c.eventId===scope.projectId)&&(scope.taskId===undefined||(c.taskId||null)===scope.taskId));
  return scoped.flatMap((c,caseIndex)=>c.events.map((e,eventIndex)=>{
    const event=e as SavedActivity;const value=event.occurredAt||event.time;
    const timestamp=/^\d{4}-\d{2}-\d{2}T/.test(value)&&Number.isFinite(Date.parse(value))?Date.parse(value):null;
    return {id:`${c.id}-${e.id}`,case:c,event,timestamp,caseIndex,eventIndex};
  })).sort((a,b)=>(b.timestamp??-Infinity)-(a.timestamp??-Infinity)||a.caseIndex-b.caseIndex||b.eventIndex-a.eventIndex).slice(0,Math.max(0,limit));
}

const identity=(vendor:Vendor)=>`${vendor.name.trim().toLocaleLowerCase()}|${vendor.location.trim().toLocaleLowerCase()}`;
const recordedMessages=(c:ProcurementCase,vendorId:string)=>(c.messages||[]).filter(m=>m.vendorId===vendorId&&['sent','received'].includes(m.direction));
export function vendorConnections(cases:ProcurementCase[]):ConnectionRecord[]{
  const records=new Map<string,ConnectionRecord>();
  for(const c of cases){for(const vendor of c.vendors){
    const messages=recordedMessages(c,vendor.id);const selected=c.selectedVendorId===vendor.id;
    if(!messages.length&&!selected)continue;
    const key=identity(vendor);const record=records.get(key);
    if(record){if(!record.cases.some(existing=>existing.id===c.id))record.cases.push(c);record.messages.push(...messages.filter(message=>!record.messages.some(existing=>existing.id===message.id)));record.selectedCount+=Number(selected);}
    else records.set(key,{key,vendor,case:c,cases:[c],messages:[...messages],selectedCount:Number(selected)});
  }}
  return [...records.values()];
}

const malaysiaDate=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kuala_Lumpur',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
export function approvalItems(cases:ProcurementCase[],projectId?:string,today=malaysiaDate()):ApprovalRecord[]{
  return cases.filter(c=>!projectId||c.eventId===projectId).flatMap(c=>{
    const records:ApprovalRecord[]=[];
    if(c.draft.body.trim()&&['pending','approved'].includes(c.draft.status))records.push({id:`message-${c.id}`,case:c,kind:'message',status:c.draft.status as 'pending'|'approved',vendors:[]});
    const vendors=c.vendors.filter(v=>eligible(c,v)&&(!v.validUntil||v.validUntil>=today)&&((v.executionMode||'demo')!=='demo'||c.id==='case-totes'));
    if(!c.selectedVendorId&&c.stage==='decision'&&vendors.length)records.push({id:`decision-${c.id}`,case:c,kind:'decision',status:'pending',vendors});
    return records;
  });
}

export function agentStatus(cases:ProcurementCase[],working=false):{label:string;detail:string;state:string}{
  if(working)return {label:'Working on your request',detail:'This conversation has a request in progress.',state:'working'};
  if(cases.some(c=>(c.messages||[]).some((m,i,all)=>m.direction==='sent'&&!(m as typeof m & {replied?:boolean}).replied&&!all.slice(i+1).some(reply=>reply.vendorId===m.vendorId&&reply.direction==='received'))))return {label:'Awaiting supplier reply',detail:'A recorded outgoing message has no saved reply yet. Demo messages stay in the controlled outbox.',state:'waiting'};
  if(approvalItems(cases).some(r=>r.status==='pending'))return {label:'Awaiting your review',detail:'An exact outgoing draft or a confirmed supplier offer needs your team’s decision.',state:'review'};
  if(cases.some(c=>c.draft.status==='approved'))return {label:'Message approved',detail:'Approved draft saved. Sending is a separate, explicit action.',state:'review'};
  if(cases.some(c=>c.workflowPlan?.some(s=>s.status==='blocked')))return {label:'Needs a connection',detail:'Saved work has a blocked step. Open its activity to review the setup needed.',state:'blocked'};
  if(cases.length&&cases.every(c=>c.selectedVendorId))return {label:'Decisions recorded',detail:'Your team’s supplier choices are saved. No order or payment has been placed.',state:'ready'};
  return {label:cases.length?'Ready for the next step':'Ready for a request',detail:'No request is currently running in this conversation.',state:'ready'};
}
