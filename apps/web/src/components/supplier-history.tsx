'use client';

import {ArrowDownLeft,ArrowUpRight,History,Mail} from 'lucide-react';
import {Dialog,DialogContent,DialogDescription,DialogHeader,DialogTitle} from '@/components/ui/dialog';
import type {ProcurementCase} from '@/lib/demo';

export function SupplierHistory({request,vendorId,onClose,onReturnFocus}:{request:ProcurementCase;vendorId:string|null;onClose:()=>void;onReturnFocus:()=>void}){
 const vendor=request.vendors.find(v=>v.id===vendorId);
 const messages=(request.messages||[]).filter(m=>m.vendorId===vendorId&&['sent','received'].includes(m.direction)).map((message,index)=>{
  const received=Number(message.receivedAtMs);
  const timestamp=received>0?received:Date.parse(message.at||message.time||'');
  return {message,index,timestamp};
 }).sort((a,b)=>{const first=Number.isFinite(a.timestamp),second=Number.isFinite(b.timestamp);return first&&second?a.timestamp-b.timestamp:first?-1:second?1:a.index-b.index;});
 return <Dialog open={!!vendor} onOpenChange={open=>{if(!open)onClose();}}><DialogContent className="kt-dialog supplier-history-dialog" onCloseAutoFocus={e=>{e.preventDefault();onReturnFocus();}}><DialogHeader><span className="dialog-symbol"><History size={21}/></span><DialogTitle>Email history</DialogTitle><DialogDescription>{vendor?.name} · {request.title}</DialogDescription></DialogHeader><div className="supplier-history-timeline">{messages.map(({message,timestamp})=><article key={message.id} className={`supplier-history-message ${message.direction}`}><span className="supplier-history-direction" aria-hidden="true">{message.direction==='sent'?<ArrowUpRight size={15}/>:<ArrowDownLeft size={15}/>}</span><div><header><strong>{message.direction==='sent'?'KawTeam sent':`${vendor?.name} replied`}</strong>{message.executionMode!=='live'&&<span className="flow-tag">Demo</span>}<time>{Number.isFinite(timestamp)?new Date(timestamp).toLocaleString('en-GB',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit',timeZone:'Asia/Kuala_Lumpur'}):message.time||'Time not recorded'}</time></header>{message.subject&&<h3>{message.subject}</h3>}<p className="supplier-history-message-body">{message.body}</p></div></article>)}{!messages.length&&<div className="supplier-history-empty"><Mail size={25}/><h3>No emails recorded yet</h3><p>Sent enquiries and supplier replies will appear here as the conversation progresses.</p></div>}</div><p className="supplier-history-note">Saved messages for this supplier and task, including earlier request revisions.</p></DialogContent></Dialog>;
}
