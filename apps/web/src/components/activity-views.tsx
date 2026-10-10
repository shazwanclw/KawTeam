'use client';

import Link from 'next/link';
import {useSearchParams} from 'next/navigation';
import {useState} from 'react';
import {ArrowRight,CheckCircle2,ChevronRight,ExternalLink,Handshake,History} from 'lucide-react';
import {Dialog,DialogContent,DialogDescription,DialogHeader,DialogTitle} from '@/components/ui/dialog';
import {Button} from '@/components/ui/button';
import {useDemo} from './workspace-context';
import {agentStatus,approvalItems,recentActivity,vendorConnections,liaisonSummary,type ActivityRecord,type ApprovalRecord,type ConnectionRecord} from '@/lib/activity';
import {dateLabel,money,totalCost,type ProcurementCase} from '@/lib/demo';

const projectName=(events:{id:string;name:string}[],c:ProcurementCase)=>events.find(e=>e.id===c.eventId)?.name||'Unassigned sample';
const sourceHref=(value?:string)=>{try{const url=new URL(value||'');return url.protocol==='https:'||url.protocol==='http:'?url.href:null;}catch{return null;}};
const logTime=(r:ActivityRecord)=>r.timestamp===null?`${r.event.time} · sample time`:new Intl.DateTimeFormat('en-MY',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit',hour12:false,timeZone:'Asia/Kuala_Lumpur'}).format(new Date(r.timestamp));
const messageTime=(value:string)=>/^\d{4}-\d{2}-\d{2}T/.test(value)&&Number.isFinite(Date.parse(value))?new Intl.DateTimeFormat('en-MY',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit',hour12:false,timeZone:'Asia/Kuala_Lumpur'}).format(new Date(value)):value;
const caseHref=(c:ProcurementCase,tab='')=>`/cases/${encodeURIComponent(c.id)}${tab?'/'+tab:''}`;

function RequestContext({request}:{request:ProcurementCase}){
  return <div className="flow-request-context"><p>{request.goal}</p><dl><div><dt>Quantity</dt><dd>{request.quantity??'Not specified'}</dd></div><div><dt>Budget ceiling</dt><dd>{request.budgetSen!==null?money(request.budgetSen):request.unitBudgetSen?`${money(request.unitBudgetSen)} per item`:'Not specified'}</dd></div><div><dt>Deadline</dt><dd>{dateLabel(request.deadline)}</dd></div><div><dt>Location</dt><dd>{request.location||'Not specified'}</dd></div></dl></div>;
}

function MessageHistory({request,vendorId}:{request:ProcurementCase;vendorId?:string}){
  const messages=(request.messages||[]).filter(m=>(!vendorId||m.vendorId===vendorId)&&['sent','received'].includes(m.direction));
  return <section className="flow-history"><h3><History size={15}/>Supplier conversation</h3>{messages.length?messages.map(m=><article className={`flow-history-message ${m.direction}`} key={m.id}><div><strong>{m.direction==='received'?'Supplier reply':'Outgoing message'}</strong><span>{m.executionMode==='demo'?'Controlled demo · ':''}{messageTime(m.time||m.at||'')}</span></div><p>{m.body}</p></article>):<p className="flow-muted">No supplier messages have been sent or received for this request.</p>}</section>;
}

export function AgentStatus({projectId,taskId,working=false}:{projectId?:string;taskId?:string|null;working?:boolean}){
  const {state}=useDemo();const cases=state.cases.filter(c=>(!projectId||c.eventId===projectId)&&(taskId===undefined||(c.taskId||null)===taskId||(!c.taskId&&c.id===taskId)));const status=agentStatus(cases,working);
  return <span className={`flow-agent-status ${status.state}`} role="status" title={status.detail}><span className="flow-status-dot"/>{status.label}</span>;
}

export function ActivityTable({projectId,taskId}:{projectId?:string;taskId?:string|null}){
  const {state,loading}=useDemo();const records=recentActivity(state.cases,{projectId,taskId});const [selectedId,setSelectedId]=useState<string|null>(null);const selected=records.find(r=>r.id===selectedId);
  return <section className="flow-table-section"><div className="flow-table-scroll"><table className="flow-table flow-activity-table"><thead><tr><th scope="col">Activity</th>{!projectId&&<th scope="col">Project</th>}<th scope="col">Type</th><th scope="col">Recorded</th><th scope="col"><span className="sr-only">Details</span></th></tr></thead><tbody>{records.map(r=><tr key={r.id} onClick={()=>setSelectedId(r.id)}><td><button className="flow-row-button" onClick={()=>setSelectedId(r.id)} aria-label={`View activity: ${r.event.title}`}><strong>{r.event.title}</strong><span>{r.case.title}</span></button></td>{!projectId&&<td>{projectName(state.events,r.case)}</td>}<td><span className={`flow-type ${r.event.kind}`}>{r.event.kind==='mail'?'Outreach':r.event.kind==='offer'?'Supplier reply':r.event.kind==='human'?'Team action':'Research'}</span></td><td className="flow-time">{logTime(r)}</td><td><ChevronRight size={15}/></td></tr>)}</tbody></table></div>{!records.length&&<div className="flow-empty"><History size={25}/><h3>{loading?'Loading saved activity…':'No activity yet'}</h3><p>Your saved requests and actions will appear here as the work progresses.</p></div>}<Dialog open={!!selected} onOpenChange={open=>{if(!open)setSelectedId(null);}}><DialogContent className="flow-detail-dialog">{selected&&<><DialogHeader><DialogTitle>{selected.event.title}</DialogTitle><DialogDescription>{projectName(state.events,selected.case)} · {logTime(selected)}</DialogDescription></DialogHeader><div className="flow-detail-body"><p className="flow-detail-lead">{selected.event.detail}</p><h3>Request context</h3><RequestContext request={selected.case}/></div><div className="flow-dialog-actions">{selected.case.eventId&&<Link href={`/projects/${encodeURIComponent(selected.case.eventId)}`} className="flow-text-link">Open project<ArrowRight size={15}/></Link>}<Link href={caseHref(selected.case,'vendors')} className="flow-text-link">View request evidence<ArrowRight size={15}/></Link></div></>}</DialogContent></Dialog></section>;
}

function ApprovalDetail({record}:{record:ApprovalRecord}){
  const {profile,busy,perform}=useDemo();
  const [choice,setChoice]=useState<string|null>(null);
  const c=record.case;const summary=liaisonSummary(record);
  const projectHref=c.eventId?`/projects/${encodeURIComponent(c.eventId)}/tasks/${encodeURIComponent(c.taskId||c.id)}`:caseHref(c);
  const approved=record.status==='approved';
  async function approve(){
    if(approved||profile!=='organiser'||busy)return;
    if(record.kind==='message')await perform({type:'approve',caseId:c.id},'Exact draft approved. Nothing was sent.');
    else if(record.kind==='supplier')await perform({type:'approve-vendor',caseId:c.id,vendorId:record.vendors[0].id},'Supplier approved. Awaiting their separate confirmation.');
    else if(choice)await perform({type:'choose',caseId:c.id,vendorId:choice},'Supplier choice approved. No order was placed.');
  }
  return <>
    <div className="flow-detail-body approval-summary-body">
      <RequestContext request={c}/>
      <section className="liaison-summary"><h3>Liaising summary</h3><p>{summary.progress}</p>
        {record.kind==='message'&&<div className="liaison-proposal"><strong>{approved?'Approved enquiry':'Enquiry ready for approval'} · {summary.supplier}</strong><p>{summary.proposal}</p></div>}
      </section>
      {summary.replies.length>0&&<section className="liaison-replies"><h3>Latest replies</h3>{summary.replies.map(reply=><article key={reply.id}><div><strong>{reply.name}</strong>{reply.demo&&<span>Controlled demo</span>}</div><p>{reply.text}</p></article>)}</section>}
      {record.kind!=='message'&&<section className="liaison-offers"><h3>{approved?'Your approved supplier':record.kind==='supplier'?'Supplier ready for your decision':'Choose the supplier to approve'}</h3>{record.vendors.map(v=><label key={v.id} className={`liaison-offer ${choice===v.id||approved?'selected':''}`}>
        {!approved&&record.kind==='decision'&&<input type="radio" name={`supplier-${c.id}`} value={v.id} checked={choice===v.id} onChange={()=>setChoice(v.id)} disabled={profile!=='organiser'||busy}/>}
        <span><strong>{v.name}</strong><small>Delivery {dateLabel(v.arrival)}{v.validUntil?` · Quote valid until ${dateLabel(v.validUntil)}`:''}</small>{v.executionMode!=='live'&&<small>Illustrative sample terms</small>}</span><b>{money(totalCost(v))}</b>
      </label>)}</section>}
    </div>
    <div className="flow-dialog-actions"><Link href={projectHref} className="flow-text-link">Open in project<ArrowRight size={15}/></Link>{record.kind==='supplier'&&!approved&&<Button variant="outline" disabled={profile!=='organiser'||busy} onClick={()=>void perform({type:'reject-vendor',caseId:c.id,vendorId:record.vendors[0].id},'Supplier declined. The waitlist has been updated.')}>Reject</Button>}<Button className="approval-confirm" disabled={approved||profile!=='organiser'||busy||(record.kind==='decision'&&!choice)} onClick={()=>void approve()}>{busy?'Saving\u2026':'Approved'}<CheckCircle2 size={15}/></Button></div>
    <p className="flow-role-note">{profile!=='organiser'?'Only the organiser can approve.':record.kind==='message'?c.draft.status==='sent'?'This approved enquiry was sent in the controlled demo.':'Approval saves this enquiry. Sending is a separate step.':'Approval records your supplier choice. A separate supplier confirmation is required before secured.'}</p>
  </>;
}

function ApprovalCard({record,onReview}:{record:ApprovalRecord;onReview:()=>void}){
  const {state,profile,busy,perform}=useDemo();
  const c=record.case;const summary=liaisonSummary(record);const approved=record.status==='approved';
  const supplier=record.kind==='supplier'?record.vendors[0]:null;

  const approvalQuery=new URLSearchParams({approval:'1',request:c.id,...(supplier?{vendor:supplier.id}:{})});
  const projectHref=(c.eventId?`/projects/${encodeURIComponent(c.eventId)}/tasks/${encodeURIComponent(c.taskId||c.id)}`:caseHref(c))+`?${approvalQuery}`;
  async function approve(){
    if(approved||profile!=='organiser'||busy)return;
    if(record.kind==='supplier'&&supplier)await perform({type:'approve-vendor',caseId:c.id,vendorId:supplier.id},'Supplier approved. Awaiting their separate confirmation.');
    else if(record.kind==='message')await perform({type:'approve',caseId:c.id},'Exact draft approved. Nothing was sent.');
    else onReview();
  }
  return <article className="approval-reference-card">
    <div className="approval-reference-top"><span>{projectName(state.events,c)}</span><span className={`approval-reference-status ${approved?'approved':'pending'}`}>{approved?'Approved':'Approval needed'}</span></div>
    <h2>{c.title}</h2>
    <div className="approval-reference-recipient"><span>{record.kind==='message'?'Supplier enquiry':'Supplier choice'}</span><strong>{supplier?.name||(record.kind==='message'?summary.supplier:`${record.vendors.length} confirmed ${record.vendors.length===1?'offer':'offers'}`)}</strong>{supplier&&<b>{money(totalCost(supplier))}</b>}</div>
    <div className="approval-reference-message"><p>{record.kind==='message'?summary.proposal:c.goal}</p>{supplier&&<p className="approval-reference-terms">Delivery {dateLabel(supplier.arrival)}{supplier.validUntil?` \u00b7 Quote valid until ${dateLabel(supplier.validUntil)}`:''}</p>}</div>
    <div className="approval-reference-bottom"><span>{supplier?.executionMode!=='live'&&record.kind==='supplier'?'Controlled demo \u00b7 ':''}{summary.progress}</span><div><Link href={projectHref} className="flow-text-link">Open in project<ArrowRight size={14}/></Link>{!approved&&<Button disabled={profile!=='organiser'||busy} onClick={()=>void approve()}>{busy?'Saving\u2026':record.kind==='decision'?'Review choice':record.kind==='message'?'Approve enquiry':'Approve supplier'}<CheckCircle2 size={16}/></Button>}</div></div>
  </article>;
}

export function ApprovalTable({projectId}:{projectId?:string}){
  const {state,loading}=useDemo();const params=useSearchParams();const request=params.get('request');const checkpoint=params.get('checkpoint');
  const [selectedId,setSelectedId]=useState<string|null>(null);const [ignoredRequest,setIgnoredRequest]=useState<string|null>(null);const [filter,setFilter]=useState('pending');
  const records=approvalItems(state.cases,projectId);const visible=records.filter(r=>r.status===filter);
  const selected=records.find(r=>r.id===selectedId)||(!selectedId&&request!==ignoredRequest?records.find(r=>r.case.id===request&&(!checkpoint||r.kind===checkpoint)):undefined);
  return <section className="approval-reference-section">
    <div className="approval-reference-filters" role="group" aria-label="Approval status">{[['pending','Approval Needed'],['approved','Approved']].map(([key,label])=><button key={key} aria-pressed={filter===key} className={filter===key?'active':''} onClick={()=>setFilter(key)}>{label}</button>)}</div>
    <div className="approval-reference-queue">{visible.map(r=><ApprovalCard key={r.id} record={r} onReview={()=>setSelectedId(r.id)}/>)}</div>
    {!visible.length&&<div className="flow-empty"><CheckCircle2 size={25}/><h3>{loading?'Loading approvals\u2026':filter==='pending'?'No approvals waiting':'No approved requests yet'}</h3><p>{filter==='pending'?'Ready enquiries and confirmed supplier choices will appear here.':'Your approved enquiries and supplier choices will be kept here.'}</p></div>}
    <Dialog open={!!selected} onOpenChange={open=>{if(!open){setSelectedId(null);setIgnoredRequest(request);}}}><DialogContent className="flow-detail-dialog approval-summary-dialog">{selected&&<><DialogHeader><DialogTitle>Summary: {selected.case.title}</DialogTitle><DialogDescription className="sr-only">Request, supplier replies and approval</DialogDescription></DialogHeader><ApprovalDetail key={selected.id} record={selected}/></>}</DialogContent></Dialog>
  </section>;
}

function ConnectionDetail({connection}:{connection:ConnectionRecord}){
  const {state}=useDemo();const r=connection;const v=r.vendor;const url=sourceHref(v.sourceUrl);const demo=r.cases.every(c=>c.vendors.filter(other=>other.name.trim().toLowerCase()===v.name.trim().toLowerCase()).every(other=>other.executionMode!=='live'));
  return <><div className="flow-detail-body"><div className="flow-connection-summary"><span className="flow-vendor-initials">{v.initials}</span><div><strong>{v.name}</strong><p>{v.location}</p><span className="flow-type research">{demo?'Controlled demo relationship':'Recorded supplier relationship'}</span></div></div><p className="flow-detail-lead">{v.description}</p>{url&&<a className="flow-text-link" href={url} target="_blank" rel="noreferrer">View supplier source<ExternalLink size={13}/></a>}<section className="flow-connection-requests"><h3>Shared history</h3>{r.cases.map(c=><div key={c.id}><Link href={caseHref(c,'conversations')}><span><strong>{c.title}</strong><small>{projectName(state.events,c)}</small></span><ArrowRight size={15}/></Link><p>{c.vendors.some(other=>c.selectedVendorId===other.id&&other.name.trim().toLowerCase()===v.name.trim().toLowerCase())?'Your team recorded a supplier preference.':'Supplier messages are recorded for this request.'}</p>{c.vendors.filter(other=>other.name.trim().toLowerCase()===v.name.trim().toLowerCase()).map(other=><MessageHistory key={other.id} request={c} vendorId={other.id}/>)}</div>)}</section><p className="flow-muted">This relationship can be reused. Prices, quantities, delivery terms and approvals must be confirmed for each new request.</p></div><div className="flow-dialog-actions"><Link href={r.case.eventId?`/projects/${encodeURIComponent(r.case.eventId)}?vendor=${encodeURIComponent(v.id)}`:caseHref(r.case,'conversations')} className="flow-primary-link">{r.case.eventId?'Start a fresh request with this supplier':'Open supplier conversation'}<ArrowRight size={15}/></Link></div></>;
}

export function VendorConnections(){
  const {state,loading}=useDemo();const [query,setQuery]=useState('');const [selectedKey,setSelectedKey]=useState<string|null>(null);const records=vendorConnections(state.cases);const filtered=records.filter(r=>`${r.vendor.name} ${r.vendor.location}`.toLowerCase().includes(query.toLowerCase()));const selected=records.find(r=>r.key===selectedKey);
  return <section className="flow-table-section flow-connections-section">{records.length>0&&<label className="flow-connection-search"><span className="sr-only">Search connections</span><input aria-label="Search connections" placeholder="Search by supplier or location" value={query} onChange={e=>setQuery(e.target.value)}/></label>}<div className="vendor-library-grid">{filtered.map(r=><button key={r.key} className="vendor-record" aria-label={`View connection: ${r.vendor.name}`} onClick={()=>setSelectedKey(r.key)}><div className="vendor-record-top"><span className="flow-vendor-initials">{r.vendor.initials}</span><span className="flow-type research">{r.selectedCount?'Previously chosen':'Conversation recorded'}</span></div><h2>{r.vendor.name}</h2><p>{r.vendor.location}</p><div><span>{r.cases.length} {r.cases.length===1?'request':'requests'}</span><span>{r.messages.length} recorded {r.messages.length===1?'message':'messages'}</span><ArrowRight size={15}/></div>{r.vendor.executionMode!=='live'&&<small>Controlled demo supplier</small>}</button>)}</div>{!filtered.length&&<div className="flow-empty"><Handshake size={25}/><h3>{loading?'Loading connections…':query?'No matching suppliers':'Your relationships start here'}</h3><p>{query?'Try another name or location.':'Suppliers appear after a recorded conversation or an explicit choice by your team. Research candidates are kept with their request.'}</p></div>}<Dialog open={!!selected} onOpenChange={open=>{if(!open)setSelectedKey(null);}}><DialogContent className="flow-detail-dialog">{selected&&<><DialogHeader><DialogTitle>{selected.vendor.name}</DialogTitle><DialogDescription>Supplier relationship and saved conversation history</DialogDescription></DialogHeader><ConnectionDetail connection={selected}/></>}</DialogContent></Dialog></section>;
}
