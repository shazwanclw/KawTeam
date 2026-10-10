import {eligible,type ProcurementCase,type Activity,type Vendor} from './demo.ts';
export type SavedActivity=Activity & {occurredAt?:string;milestone?:boolean};
export type ActivityRecord={id:string;case:ProcurementCase;event:SavedActivity;timestamp:number|null};
export type ConnectionRecord={key:string;vendor:Vendor;case:ProcurementCase;cases:ProcurementCase[];messages:NonNullable<ProcurementCase['messages']>;selectedCount:number};
export type ApprovalRecord={id:string;case:ProcurementCase;kind:'message'|'decision'|'supplier';status:'pending'|'approved';vendors:Vendor[]};
const sentMilestone=(event:SavedActivity)=>/message sent|suppliers? contacted|contacted \d+ suppliers?/i.test(event.title);
function isMilestone(event:SavedActivity){
  if(event.milestone!==undefined)return event.milestone;
  if(/brief.*understood|workflow.*plan|connection needed|draft updated|thinking|planning|step started/i.test(event.title))return false;
  return event.kind==='offer'||/compar(ed|ison)|sources collected|research prepared|price floor|counteroffer prepared|enquiry ready|supplier.*reused|message (sent|approved|returned)|team made the decision|ready for your|supplier.*(contacted|reply received)|backup supplier needed/i.test(event.title);
}
export function recentActivity(cases:ProcurementCase[],scope:{projectId?:string;taskId?:string|null}={},limit=15):ActivityRecord[]{
  const scoped=cases.filter(c=>(!scope.projectId||c.eventId===scope.projectId)&&(scope.taskId===undefined||(c.taskId||null)===scope.taskId));
  return scoped.flatMap((c,caseIndex)=>{
   const latestSend=c.events.findLastIndex(e=>sentMilestone(e));
   const sends=(c.messages||[]).filter(m=>m.direction==='sent');const contacted=new Set(sends.map(m=>m.vendorId)).size;
   return c.events.flatMap((e,eventIndex)=>{
    if(!isMilestone(e)||(sentMilestone(e)&&eventIndex!==latestSend))return [];
    const event:SavedActivity={...e};
    if(sentMilestone(event)&&contacted){event.title=`Contacted ${contacted} ${contacted===1?'supplier':'suppliers'}`;event.detail=`${contacted} ${contacted===1?'supplier has':'suppliers have'} received enquiries${sends.every(m=>m.executionMode==='demo')?' in the controlled demo':''}. Replies and confirmed terms are saved with this request.`;}
    if(/counteroffer prepared/i.test(event.title))event.title='Supplier enquiry ready for approval';
    const value=event.occurredAt||event.time;
    const timestamp=/^\d{4}-\d{2}-\d{2}T/.test(value)&&Number.isFinite(Date.parse(value))?Date.parse(value):null;
    return [{id:`${c.id}-${e.id}`,case:c,event,timestamp,caseIndex,eventIndex}];
   });
  }).sort((a,b)=>(b.timestamp??-Infinity)-(a.timestamp??-Infinity)||a.caseIndex-b.caseIndex||b.eventIndex-a.eventIndex).slice(0,Math.max(0,limit));
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
    if(c.approvalQueue){
      for(const row of c.approvalQueue.filter(r=>['approval_needed','approved','secured'].includes(r.status))){
        const v=c.vendors.find(v=>v.id===row.vendorId);
        if(v)records.push({id:`supplier-${c.id}-${v.id}`,case:c,kind:'supplier',status:row.status==='approval_needed'?'pending':'approved',vendors:[v]});
      }
      return records;
    }
    if(c.draft.body.trim()&&['pending','approved','sent'].includes(c.draft.status))records.push({id:`message-${c.id}`,case:c,kind:'message',status:c.draft.status==='pending'?'pending':'approved',vendors:[]});
    const vendors=c.vendors.filter(v=>eligible(c,v)&&(!v.validUntil||v.validUntil>=today)&&((v.executionMode||'demo')!=='demo'||c.id==='case-totes'));
    if(!c.selectedVendorId&&c.stage==='decision'&&vendors.length)records.push({id:`decision-${c.id}`,case:c,kind:'decision',status:'pending',vendors});
    const selected=c.vendors.find(v=>v.id===c.selectedVendorId);
    if(selected)records.push({id:`decision-${c.id}`,case:c,kind:'decision',status:'approved',vendors:[selected]});
    return records;
  });
}

const businessText=(body:string)=>body.split(/\n\s*\n/).flatMap(paragraph=>{
 const text=paragraph.trim();
 if(/^(thank you|thanks|regards|best regards)[,!]?\s*(\n[\s\S]*)?$/i.test(text)||/^sent from\b/i.test(text))return [];
 const content=text.replace(/^(hi|hello|dear)\b[^,\n]*,\s*/i,'').replace(/^thank you for\s+/i,'');
 return content?[content.charAt(0).toUpperCase()+content.slice(1)]:[];
}).join('\n\n').replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi,'[supplier contact]').trim();
export function liaisonSummary(record:ApprovalRecord){
 const c=record.case;
 const supplier=c.vendors.find(v=>v.id===c.draft.vendorId)||c.vendors.find(v=>c.draft.recipient.includes(v.name));
 const messages=(c.messages||[]).filter(m=>['sent','received'].includes(m.direction));
 const contacted=new Set(messages.filter(m=>m.direction==='sent').map(m=>m.vendorId)).size;
 const latest=new Map<string,NonNullable<ProcurementCase['messages']>[number]>();
 for(const message of messages){if(message.direction==='received')latest.set(message.vendorId,message);}
 const replies=[...latest.values()].map(message=>({id:message.id,vendorId:message.vendorId,name:c.vendors.find(v=>v.id===message.vendorId)?.name||'Supplier',text:businessText(message.body)||'Reply details are available in the project.',demo:message.executionMode==='demo'}));
 return {supplier:supplier?.name||'Supplier',contacted,progress:contacted?`${contacted} ${contacted===1?'supplier contacted':'suppliers contacted'}. ${replies.length} ${replies.length===1?'reply recorded':'replies recorded'}.`:'No sent enquiries are recorded for this request yet.',proposal:businessText(c.draft.body)||'Review the saved request details in the project.',replies};
}

export function agentStatus(cases:ProcurementCase[],working=false):{label:string;detail:string;state:string}{
  if(working)return {label:'Working on your request',detail:'This conversation has a request in progress.',state:'working'};
  if(cases.some(c=>c.approvalQueue?.some(r=>r.status==='approved')))return {label:'Awaiting supplier confirmation',detail:'Your team approved a supplier. Their matching confirmation is still needed.',state:'waiting'};
  if(cases.length&&cases.every(c=>(c.approvalQueue?.filter(r=>r.status==='secured').length||0)>=(c.selectionTarget||1)))return {label:'Target secured',detail:'Approved suppliers have matching saved confirmations. Demo confirmations remain illustrative.',state:'ready'};
  if(cases.some(c=>(c.messages||[]).some((m,i,all)=>m.direction==='sent'&&!(m as typeof m & {replied?:boolean}).replied&&!all.slice(i+1).some(reply=>reply.vendorId===m.vendorId&&reply.direction==='received'))))return {label:'Awaiting supplier reply',detail:'A recorded outgoing message has no saved reply yet. Demo messages stay in the controlled outbox.',state:'waiting'};
  if(approvalItems(cases).some(r=>r.status==='pending'))return {label:'Awaiting your review',detail:'An exact outgoing draft or a confirmed supplier offer needs your team’s decision.',state:'review'};
  if(cases.some(c=>c.draft.status==='approved'))return {label:'Message approved',detail:'Approved draft saved. Sending is a separate, explicit action.',state:'review'};
  if(cases.some(c=>c.workflowPlan?.some(s=>s.status==='blocked')))return {label:'Needs a connection',detail:'Saved work has a blocked step. Open its activity to review the setup needed.',state:'blocked'};
  if(cases.length&&cases.every(c=>c.selectedVendorId))return {label:'Decisions recorded',detail:'Your team’s supplier choices are saved. No order or payment has been placed.',state:'ready'};
  return {label:cases.length?'Ready for the next step':'Ready for a request',detail:'No request is currently running in this conversation.',state:'ready'};
}
