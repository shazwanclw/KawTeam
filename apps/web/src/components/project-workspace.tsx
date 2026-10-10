'use client';

import Link from 'next/link';
import {useSearchParams} from 'next/navigation';
import {useState} from 'react';
import {ArrowRight,Folder,Link2,MessageSquare} from 'lucide-react';
import type {EventMemory} from '@/lib/workspace';
import {projectTasks,taskCases,taskProgress} from '@/lib/tasks';
import {useDemo} from './workspace-context';
import {DriveMemory} from './project-controls';
import {ChatSurface} from './chat-surface';
import {ActivityTable} from './activity-views';
import {TaskDetail} from './task-detail';

export function ProjectWorkspace({project,taskId,onCreateProject}:{project:EventMemory;tab?:string;taskId?:string;onCreateProject:()=>void}){
 const params=useSearchParams();const {state}=useDemo();const [memory,setMemory]=useState(false);const [view,setView]=useState('tasks');
 const tasks=projectTasks(state,project);const task=tasks.find(t=>t.id===taskId);
 if(taskId&&!task)return <div className="flow-page"><h1>Task not found</h1><Link href={`/projects/${project.id}`}>Back to project</Link></div>;
 if(task)return <TaskDetail project={project} task={task}/>;
 return <div className="project-flow task-project">
  <header className="project-flow-heading"><div className="project-flow-title"><h1>{project.name}</h1>{project.sample&&<span className="flow-tag">Sample</span>}</div><button aria-label="Project memory" className="project-memory-button" onClick={()=>setMemory(true)}><Link2 size={16}/><span>{project.driveSource?'Drive context':'Project memory'}</span></button></header>
  <ChatSurface key={`${project.id}-${params.get('task')||'new'}-${params.get('vendor')||''}`} project={project} onCreateProject={onCreateProject}/>
  <section className="project-task-section">
   <div className="project-task-tabs" role="tablist" aria-label="Project tasks and activity">{[['tasks','All Task'],['activity','Recent Activity']].map(([id,label])=><button id={`project-${id}-tab`} key={id} role="tab" aria-label={label} aria-selected={view===id} aria-controls={`project-${id}-panel`} tabIndex={view===id?0:-1} onClick={()=>setView(id)} onKeyDown={e=>{if(['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();const next=id==='tasks'?'activity':'tasks';setView(next);document.getElementById(`project-${next}-tab`)?.focus();}}}>{label}{id==='tasks'&&<span>{tasks.length}</span>}</button>)}</div>
   <div role="tabpanel" id={`project-${view}-panel`} aria-labelledby={`project-${view}-tab`}>
    {view==='activity'?<ActivityTable projectId={project.id}/>:<div className="project-task-list">{tasks.map(t=>{const cases=taskCases(state,project.id,t.id);const progress=taskProgress(cases);const count=state.threads.find(thread=>thread.taskId===t.id&&thread.eventId===project.id)?.messages.length||0;return <Link key={t.id} className="project-task-row" aria-label={`Open task: ${t.name}`} href={`/projects/${project.id}/tasks/${t.id}`}><span className="project-task-icon"><MessageSquare size={18}/></span><span className="project-task-name"><strong>{t.name}</strong><small>{progress.secured?`${progress.secured} of ${progress.target} secured`:progress.approved?`${progress.approved} awaiting supplier confirmation`:count?`${count} messages · shared project context`:'Ready to continue'}</small></span>{progress.pending>0&&<span className="task-approval-count" data-task-approvals={progress.pending}>{progress.pending} {progress.pending===1?'approval':'approvals'}</span>}<ArrowRight size={16}/></Link>;})}{!tasks.length&&<div className="project-no-tasks"><Folder size={21}/><p>Your tasks will live here.<small>Send your first request above to start one.</small></p></div>}</div>}
   </div>
  </section>
  {memory&&<DriveMemory project={project} open={memory} onOpenChange={setMemory}/>}
 </div>;
}
