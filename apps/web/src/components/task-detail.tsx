'use client';

import Link from 'next/link';
import {useRef,useState} from 'react';
import {ArrowLeft,ArrowRight,CalendarDays,CheckCircle2,ChevronRight,Clock3,Handshake,History,MessageSquare} from 'lucide-react';
import {Dialog,DialogContent,DialogDescription,DialogHeader,DialogTitle} from '@/components/ui/dialog';
import {Button} from '@/components/ui/button';
import type {EventMemory,ProjectTask} from '@/lib/workspace';
import {dateLabel,money,totalCost,type ProcurementCase} from '@/lib/demo';
import {taskCases,taskDates,taskProgress,supplierOutreachLabel} from '@/lib/tasks';
import {liaisonSummary} from '@/lib/activity';
import {useDemo} from './workspace-context';
import {SupplierHistory} from './supplier-history';

const labels={approval_needed:'Approval needed',waitlist:'Waitlist',approved:'Awaiting confirmation',secured:'Secured',rejected:'Declined',not_selected:'Not selected',liaising:'Liaison pending',needs_terms:'Terms need attention'};

export function SupplierReview({request,vendorId,onClose}:{request:ProcurementCase;vendorId:string|null;onClose:()=>void}){
 const {perform,profile,busy}=useDemo();const v=request.vendors.find(v=>v.id===vendorId);const row=request.approvalQueue?.find(r=>r.vendorId===vendorId);
 const summary=v?liaisonSummary({id:v.id,case:request,kind:'supplier',status:row?.status==='approval_needed'?'pending':'approved',vendors:[v]}):null;
 async function decide(type:'approve-vendor'|'reject-vendor'){
  if(!v)return;
  if(await perform({type,caseId:request.id,vendorId:v.id},type==='approve-vendor'?'Supplier approved. Awaiting their separate confirmation.':'Supplier declined. The waitlist has been updated.'))onClose();
 }
 return <Dialog open={!!v} onOpenChange={open=>{if(!open)onClose();}}><DialogContent className="flow-detail-dialog approval-summary-dialog">{v&&summary&&<>
  <DialogHeader><DialogTitle>{v.name}</DialogTitle><DialogDescription>{request.title} · {row?(row.status==='liaising'?supplierOutreachLabel(request,v.id):labels[row.status]):'Supplier summary'}</DialogDescription></DialogHeader>
  <div className="flow-detail-body"><div className="flow-request-context"><p>{request.goal}</p><dl><div><dt>Quoted total</dt><dd>{money(totalCost(v))}</dd></div><div><dt>Delivery</dt><dd>{dateLabel(v.arrival)}</dd></div><div><dt>Quantity</dt><dd>{request.quantity??'Not specified'}</dd></div><div><dt>Task budget</dt><dd>{request.budgetSen!==null?money(request.budgetSen):request.unitBudgetSen?`${money(request.unitBudgetSen)} per item`:'Not specified'}</dd></div></dl></div>
   <section className="liaison-summary"><h3>Liaising summary</h3><p>{summary.progress}</p><p>{row?.reason}</p></section>
   <section className="liaison-replies"><h3>Latest supplier reply</h3>{summary.replies.filter(r=>r.vendorId===v.id).map(reply=><article key={reply.id}><div><strong>{reply.name}</strong>{reply.demo&&<span>Controlled demo</span>}</div><p>{reply.text}</p></article>)}{!summary.replies.some(r=>r.vendorId===v.id)&&<p className="flow-muted">No final quotation reply is recorded yet.</p>}</section>
  </div>
  {row?.status==='approval_needed'&&<div className="flow-dialog-actions"><Button variant="outline" disabled={busy||profile!=='organiser'} onClick={()=>void decide('reject-vendor')}>Reject</Button><Button className="approval-confirm" disabled={busy||profile!=='organiser'} onClick={()=>void decide('approve-vendor')}>Approved<CheckCircle2 size={15}/></Button></div>}
  <p className="flow-role-note">{profile!=='organiser'?'Only the organiser can approve suppliers.':v.executionMode!=='live'?'Illustrative demo terms. Approval is separate from supplier confirmation.':'Approval records your choice. Supplier confirmation is still required.'}</p>
 </>}</DialogContent></Dialog>;
}

export function TaskDetail({project,task}:{project:EventMemory;task:ProjectTask}){
 const {state,profile,busy,perform}=useDemo();const cases=taskCases(state,project.id,task.id);const request=cases.at(-1);const progress=taskProgress(cases);const dates=taskDates(cases);const [selected,setSelected]=useState<string|null>(null);const [history,setHistory]=useState<string|null>(null);const historyTrigger=useRef<HTMLButtonElement|null>(null);
 const rows=request?.approvalQueue||[];const secured=rows.filter(r=>r.status==='secured');const queue=rows.filter(r=>r.status!=='secured');
 const isDemo=request?.id==='case-totes'&&request.quantity===300&&request.vendors.every(v=>v.executionMode!=='live');
 return <div className="task-page">
  <Link href={`/projects/${project.id}`} className="task-back"><ArrowLeft size={14}/>{project.name}</Link>
  <header className="task-heading"><div><h1>{task.name}</h1><p>{request?[request.quantity!==null?`${request.quantity} ${request.selectionTarget&&request.selectionTarget>1?'per supplier':'items'}`:null,request.budgetSen!==null?`${money(request.budgetSen)} task budget`:request.unitBudgetSen?`${money(request.unitBudgetSen)} per item`:null].filter(Boolean).join(' · ')||'Sourcing request':'A focused conversation, with your project context.'}</p></div><Link className="task-chat-link" href={`/projects/${project.id}?task=${task.id}`}><MessageSquare size={16}/>Continue conversation<ArrowRight size={14}/></Link></header>
  <div className="task-content-grid"><div className="task-main-column">
   {request?.automation&&<p className="task-section-description" role="status">{request.automation.status==='queued'?(request.automation.lastTickAt?'Supplier outreach is in progress.':'Supplier outreach is queued.'):request.automation.status==='awaiting_replies'?'Awaiting supplier replies.':request.automation.status==='review_ready'?'Supplier quotations are ready for your review.':request.automation.status==='paused'?'Supplier outreach is paused.':'Supplier outreach needs attention.'}{request.automation.error&&` ${request.automation.error}`}</p>}
   <section className="task-section secured-section"><div className="task-section-title"><h2>Secured</h2><span className="task-secured-count">{progress.secured}<small> / {progress.target}</small></span></div><p className="task-section-description">Approved by your team. Confirmed by the supplier.</p>
    {secured.map(row=>{const v=request!.vendors.find(v=>v.id===row.vendorId)!;return <div className="task-supplier-with-history" key={v.id}><button className="task-supplier-row secured" onClick={()=>setSelected(v.id)}><span className="task-supplier-mark"><CheckCircle2 size={18}/></span><span className="task-supplier-name"><strong>{v.name}</strong><small>{v.executionMode!=='live'?'Controlled demo · ':''}Delivery {dateLabel(v.arrival)}</small></span><span className="task-row-price">{money(totalCost(v))}</span><ChevronRight size={16}/></button><button className="task-history-button" aria-label={`Email history: ${v.name}`} title="Email history" onClick={e=>{historyTrigger.current=e.currentTarget;setHistory(v.id);}}><History size={17}/></button></div>;})}
    {!secured.length&&<div className="task-quiet-empty"><Handshake size={20}/><p>No suppliers secured yet.<small>{progress.approved?`${progress.approved} approved ${progress.approved===1?'supplier is':'suppliers are'} awaiting confirmation.`:'Your approved suppliers will appear here once they confirm.'}</small></p></div>}
   </section>
   <section className="task-section task-approval-section"><div className="task-section-title"><h2>Approval</h2><span className="task-small-count">{progress.pending} needed</span></div><p className="task-section-description">Final replies first, ranked by confirmed cost and delivery. {progress.target===1?'One supplier to secure.':`${progress.target} suppliers to secure.`}</p>
    {isDemo&&!request?.taskWorkflowVersion&&<div className="task-demo-control"><p>Try the full liaison flow with the saved tote sample.<small>Explicitly simulated enquiries and replies. No external email.</small></p><Button variant="outline" disabled={busy||profile==='observer'} onClick={()=>void perform({type:'liaise-task',caseId:request!.id},'Controlled liaison completed across the supplier pool.')}>Run sample liaison</Button></div>}
    {isDemo&&request?.taskWorkflowVersion&&request.vendors.every(v=>v.liaisonStatus!=='ready')&&<div className="task-demo-control"><p>The sample has no completed liaison yet.</p><Button variant="outline" disabled={busy||profile==='observer'} onClick={()=>void perform({type:'liaise-task',caseId:request.id},'Controlled liaison completed across the supplier pool.')}>Run sample liaison</Button></div>}
    {queue.map(row=>{const v=request!.vendors.find(v=>v.id===row.vendorId)!;return <div className={`task-candidate ${row.status}`} key={v.id}>
     <div className="task-supplier-with-history"><button className="task-supplier-row" onClick={()=>setSelected(v.id)} aria-label={`Review supplier: ${v.name}`}><span className="task-rank">{row.rank?String(row.rank).padStart(2,'0'):'—'}</span><span className="task-supplier-name"><strong>{v.name}</strong><small>{['needs_terms','liaising'].includes(row.status)?row.reason:v.executionMode!=='live'?'Controlled demo supplier':v.location}</small></span><span className="task-row-price">{money(totalCost(v))}</span><span className={`task-queue-status ${row.status}`}>{row.status==='liaising'?supplierOutreachLabel(request!,v.id):labels[row.status]}</span><ChevronRight size={15}/></button><button className="task-history-button" aria-label={`Email history: ${v.name}`} title="Email history" onClick={e=>{historyTrigger.current=e.currentTarget;setHistory(v.id);}}><History size={17}/></button></div>
     {row.status==='approved'&&isDemo&&<div className="task-confirm-row"><span>Waiting for a separate supplier confirmation.</span><button disabled={busy||profile!=='organiser'} onClick={()=>void perform({type:'confirm-vendor',caseId:request!.id,vendorId:v.id},'Controlled supplier confirmation recorded. Secured in demo.')}>Check demo confirmation<ArrowRight size={13}/></button></div>}
    </div>;})}
    {!queue.length&&<div className="task-quiet-empty"><Clock3 size={20}/><p>{secured.length?'Your target has been secured.':'Nothing ready for approval yet.'}<small>{request?.vendors.length?'Supplier liaison and final terms will appear here.':'This task is saved. Supplier research needs its provider connection.'}</small></p></div>}
   </section>
  </div><aside className="task-dates-column"><div className="task-section-title"><h2>Upcoming events</h2><CalendarDays size={17}/></div><p className="task-section-description">Important dates for this task.</p>{dates.map(d=><div className="task-date-row" key={d.id}><span className="task-date-mark"><b>{new Date(d.date+'T12:00:00+08:00').toLocaleDateString('en-GB',{day:'numeric',timeZone:'Asia/Kuala_Lumpur'})}</b><small>{new Date(d.date+'T12:00:00+08:00').toLocaleDateString('en-GB',{month:'short',timeZone:'Asia/Kuala_Lumpur'})}</small></span><span>{d.label}<small>{dateLabel(d.date)}</small></span></div>)}{!dates.length&&<p className="task-dates-empty">No upcoming dates saved for this task.</p>}<Link href="/overview/calendar" className="flow-text-link">Open calendar<ArrowRight size={14}/></Link></aside></div>
  {request&&<SupplierHistory request={request} vendorId={history} onClose={()=>setHistory(null)} onReturnFocus={()=>historyTrigger.current?.focus()}/>}
  {request&&<SupplierReview request={request} vendorId={selected} onClose={()=>setSelected(null)}/>}
 </div>;
}
