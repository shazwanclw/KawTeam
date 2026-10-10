'use client';

import Link from 'next/link';
import {useRef,useState,type FormEvent} from 'react';
import {ArrowUp,Check,MessageSquare} from 'lucide-react';
import {api,type WorkspaceState} from '@/lib/workspace';
import type {Failsafe,ProcurementCase} from '@/lib/demo';
import {useDemo} from './workspace-context';

function AttentionItem({issue,request}:{issue:Failsafe;request:ProcurementCase}){
 const {profile,acceptState,notify}=useDemo();const [message,setMessage]=useState('');const [sending,setSending]=useState(false);
 const pending=useRef<{message:string;id:string}|null>(null);
 async function reply(e:FormEvent){
  e.preventDefault();if(!message.trim()||sending||profile==='observer')return;
  const attempt=pending.current?.message===message?pending.current:{message,id:crypto.randomUUID()};pending.current=attempt;setSending(true);
  try{const result=await api<{state:WorkspaceState}>('chat',{eventId:request.eventId,taskId:request.taskId||request.id,message:attempt.message,requestId:attempt.id});acceptState(result.state);pending.current=null;setMessage('');notify('Context added to your task.');}
  catch(error){notify(error instanceof Error?error.message:'Could not save your reply. Try again.');}
  finally{setSending(false);}
 }
 return <article className="project-failsafe-item"><div className="project-failsafe-top"><div><Link href={`/projects/${request.eventId}?task=${encodeURIComponent(request.taskId||request.id)}`}><MessageSquare size={13}/>{request.title}</Link><h3>{issue.title}</h3><p>{issue.detail}</p></div><span className="failsafe-attention-dot" title="Your attention needed"/></div><form onSubmit={reply}><label className="sr-only" htmlFor={`failsafe-${request.id}-${issue.id}`}>Reply to {issue.title}</label><textarea id={`failsafe-${request.id}-${issue.id}`} aria-label={`Reply to ${issue.title}`} placeholder="Add what KawTeam needs to continue…" value={message} onChange={e=>setMessage(e.target.value)} rows={2} maxLength={5000} disabled={sending||profile==='observer'} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();e.currentTarget.form?.requestSubmit();}}}/><button className="chat-send" aria-label={`Send context for ${issue.title}`} disabled={sending||profile==='observer'||!message.trim()}><ArrowUp size={18}/></button></form>{sending&&<p className="failsafe-saving" role="status">Updating your task…</p>}</article>;
}

export function ProjectFailsafes({projectId}:{projectId:string}){
 const {state}=useDemo();const issues=state.cases.filter(c=>c.eventId===projectId).flatMap(request=>(request.failsafes||[]).filter(f=>f.status==='open').map(issue=>({issue,request})));
 return <div className="project-failsafe-list">{issues.length?issues.map(({issue,request})=><AttentionItem key={`${request.id}-${issue.id}`} issue={issue} request={request}/>):<div className="project-no-tasks"><Check size={21}/><p>No attention needed<small>KawTeam will flag anything it cannot work out here.</small></p></div>}</div>;
}
