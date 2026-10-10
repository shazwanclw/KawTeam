'use client';

import Link from 'next/link';
import {useRouter,useSearchParams} from 'next/navigation';
import {useEffect,useRef,useState,type FormEvent} from 'react';
import {ArrowUp,ArrowRight,Check,ChevronDown,Folder,MessageSquare,Link2,Search,Plus} from 'lucide-react';
import {DropdownMenu,DropdownMenuContent,DropdownMenuItem,DropdownMenuLabel,DropdownMenuSeparator,DropdownMenuTrigger} from '@/components/ui/dropdown-menu';
import {api,type EventMemory,type EventDocument,type WorkspaceState,type ChatMessage} from '@/lib/workspace';
import {money,type ProcurementCase} from '@/lib/demo';
import {projectTasks} from '@/lib/tasks';
import {useDemo} from './workspace-context';
import {DocumentPreview,DriveMemory} from './project-controls';
import {AgentStatus} from './activity-views';

function WorkflowCard({request}:{request:ProcurementCase}){
 const href=request.eventId?`/projects/${request.eventId}/tasks/${request.taskId||request.id}`:`/cases/${request.id}`;
 return <div className="chat-result">
  <div className="chat-result-head"><span>{request.workflowMode==='liaise'?<MessageSquare size={18}/>:<Search size={18}/>}</span><div><strong>{request.title}</strong><p>{request.quantity} {request.selectionTarget&&request.selectionTarget>1?'per supplier':'items'} · {money(request.budgetSen)} budget</p></div><small>{request.vendors.length?`${request.vendors.length} candidates`:'Request saved'}</small></div>
  <Link href={href}>View task<ArrowRight size={15}/></Link>
 </div>;
}

export function ChatSurface({project:fixedProject,taskId,onCreateProject}:{project?:EventMemory;taskId?:string;onCreateProject:()=>void}){
 const router=useRouter();const params=useSearchParams();const {state,profile,acceptState,notify,loading}=useDemo();
 const queryVendor=state.cases.flatMap(c=>c.vendors).find(v=>v.id===params.get('vendor'));
 const [selectedId,setSelectedId]=useState<string|null>(null);
 const [selectedTaskId,setSelectedTaskId]=useState<string|null>(taskId||params.get('task'));
 const [input,setInput]=useState(()=>queryVendor?`I want to request a fresh quotation from ${queryVendor.name}. `:'');
 const [sending,setSending]=useState(false);const [memory,setMemory]=useState(false);const [preview,setPreview]=useState<EventDocument|null>(null);
 const pending=useRef<{message:string;id:string;scope:string|null}|null>(null);const bottom=useRef<HTMLDivElement>(null);
 const project=fixedProject||state.events.find(p=>p.id===selectedId);
 const tasks=project?projectTasks(state,project):[];
 const activeTaskId=fixedProject?(taskId||selectedTaskId):null;
 const task=tasks.find(t=>t.id===activeTaskId);
 const messages=project&&activeTaskId?(state.threads.find(t=>t.eventId===project.id&&t.taskId===activeTaskId)||state.threads.find(t=>activeTaskId===`legacy-${project.id}`&&t.eventId===project.id&&!t.taskId))?.messages||[]:[];
 const hasConversation=messages.length>0||sending;
 useEffect(()=>{if(messages.length||sending)bottom.current?.scrollIntoView({behavior:'smooth',block:'nearest'});},[messages.length,sending]);

 async function send(e:FormEvent){
  e.preventDefault();if(!input.trim()||sending||profile==='observer'||loading)return;
  const message=input;const scope=project?`${project.id}:${activeTaskId||'new'}`:null;
  const request=pending.current?.message===message&&pending.current.scope===scope?pending.current:{message,id:crypto.randomUUID(),scope};
  pending.current=request;setSending(true);setInput('');
  try{
   const result=await api<{assistant:ChatMessage;eventId:string;taskId:string;state:WorkspaceState}>('chat',{message,eventId:project?.id||null,taskId:activeTaskId,requestId:request.id});
   acceptState(result.state);pending.current=null;
   if(fixedProject&&result.eventId===fixedProject.id)setSelectedTaskId(result.taskId);
   else router.push(`/projects/${result.eventId}?task=${encodeURIComponent(result.taskId)}`);
  }catch(error){setInput(message);notify(error instanceof Error?error.message:'Your message could not be saved. Try again.');}
  finally{setSending(false);}
 }
 async function openDocument(id:string){try{setPreview(await api<EventDocument>(`documents/${id}`));}catch(error){notify(error instanceof Error?error.message:'Could not open saved context.');}}

 const picker=fixedProject?<DropdownMenu>
  <DropdownMenuTrigger className="chat-project-picker" aria-label="Choose task" disabled={sending||loading}><MessageSquare size={16}/><span>{task?.name||'New Task'}</span><ChevronDown size={14}/></DropdownMenuTrigger>
  <DropdownMenuContent className="chat-picker-menu" align="start"><DropdownMenuLabel>Continue a task, or start fresh</DropdownMenuLabel><DropdownMenuItem onSelect={()=>{if(taskId)router.push(`/projects/${project!.id}`);else setSelectedTaskId(null);}}><Plus size={16}/><span>New Task<small>A separate conversation</small></span>{!activeTaskId&&<Check size={14}/>}</DropdownMenuItem><DropdownMenuSeparator/>{tasks.map(t=><DropdownMenuItem key={t.id} onSelect={()=>{if(taskId)router.push(`/projects/${project!.id}?task=${t.id}`);else setSelectedTaskId(t.id);}}><MessageSquare size={16}/><span>{t.name}</span>{t.id===activeTaskId&&<Check size={14}/>}</DropdownMenuItem>)}</DropdownMenuContent>
 </DropdownMenu>:<DropdownMenu>
  <DropdownMenuTrigger className="chat-project-picker" aria-label="Choose project" disabled={sending||loading}><Folder size={16}/><span>{project?.name||'Choose project'}</span><ChevronDown size={14}/></DropdownMenuTrigger>
  <DropdownMenuContent className="chat-picker-menu" align="start"><DropdownMenuLabel>What is this task for?</DropdownMenuLabel><DropdownMenuItem onSelect={()=>setSelectedId(null)}><MessageSquare size={16}/><span>No project yet<small>Start from your prompt</small></span>{!project&&<Check size={14}/>}</DropdownMenuItem><DropdownMenuSeparator/>{state.events.map(p=><DropdownMenuItem key={p.id} onSelect={()=>setSelectedId(p.id)}><Folder size={16}/><span>{p.name}</span>{p.id===project?.id&&<Check size={14}/>}</DropdownMenuItem>)}{!state.events.length&&<DropdownMenuItem disabled={profile==='observer'} onSelect={onCreateProject}><Plus size={16}/><span>Add a project<small>Or just start a conversation</small></span></DropdownMenuItem>}</DropdownMenuContent>
 </DropdownMenu>;
 const composer=<div className="chat-compose-area"><form className="chat-compose" onSubmit={send}><label className="sr-only" htmlFor="chat-message">Message KawTeam</label><textarea id="chat-message" value={input} rows={hasConversation?2:3} maxLength={5000} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();e.currentTarget.form?.requestSubmit();}}} placeholder={profile==='observer'?'Observer view · switch profile to continue':task?'Ask a question or update this task…':fixedProject?'What would you like to get done?':'Tell us what you’re looking for…'} disabled={profile==='observer'||sending||loading}/><div className="chat-compose-tools"><div>{picker}{project&&<button type="button" className="chat-tool-button" aria-label="Project memory" onClick={()=>setMemory(true)}><Link2 size={17}/></button>}</div><button className="chat-send" type="submit" aria-label="Send message" disabled={sending||!input.trim()||profile==='observer'||loading}><ArrowUp size={21}/></button></div></form></div>;

 return <section className={`chat-surface ${hasConversation?'with-conversation':'start-conversation'}`} aria-label={fixedProject?'Project chat':'Main chat'}>
  {hasConversation?<><div className="chat-conversation-status"><AgentStatus projectId={project?.id} taskId={activeTaskId} working={sending}/><span>{task?.name||'New task'}</span></div><div className="chat-transcript">{messages.map(message=><article className={`chat-message ${message.role}`} key={message.id}><div className="chat-message-avatar">{message.role==='user'?'You':'K'}</div><div className="chat-message-body"><div className="chat-message-meta"><strong>{message.role==='user'?'Your team':message.provider==='setup_required'?'KawTeam · connection note':'KawTeam'}</strong><time>{new Date(message.time).toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit',timeZone:'Asia/Kuala_Lumpur'})}</time></div><p>{message.body}</p>{message.citations?.length?<div className="chat-citations">{Array.from(new Set(message.citations)).map(id=><button key={id} onClick={()=>void openDocument(id)}>{state.documents.find(d=>d.id===id)?.name||'Project context'}<ArrowRight size={12}/></button>)}</div>:null}{message.caseId&&state.cases.find(c=>c.id===message.caseId)&&<WorkflowCard request={state.cases.find(c=>c.id===message.caseId)!}/>}</div></article>)}{sending&&<div className="chat-working" role="status"><span className="chat-working-mark">K</span><span>Saving your task<span className="working-dots">···</span></span></div>}<div ref={bottom}/></div>{composer}</>:<div className="chat-start">
   {fixedProject?<><span className="chat-start-kicker">ONE TASK. LET’S GET IT MOVING.</span><h2>{task?`Continue ${task.name}`:'What are we going to KawTeam today?'}</h2><p>{task?'Your conversation and project context are right here.':`Start a task for ${fixedProject.name}. We’ll keep everything together.`}</p></>:<><div className="chat-start-emblem" aria-hidden="true"><span>K</span><i/></div><span className="chat-start-kicker">A LITTLE LESS SEARCHING. A LITTLE MORE DOING.</span><h1>What are we going to<br/><span>KawTeam today?</span></h1><p>Find the right people. Keep the conversation moving. You make the call.</p></>}{composer}
  </div>}
  {project&&memory&&<DriveMemory key={project.id} project={project} open={memory} onOpenChange={setMemory}/>}<DocumentPreview document={preview} onClose={()=>setPreview(null)}/>
 </section>;
}
