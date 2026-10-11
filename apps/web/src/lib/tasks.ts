import {validDate,type ProcurementCase} from './demo.ts';
import type {EventMemory,ProjectTask,WorkspaceState} from './workspace.ts';
import {malaysiaToday} from './schedule.ts';

export function projectTasks(state:WorkspaceState,project:EventMemory):ProjectTask[]{
 const tasks=[...(project.tasks||[])];
 for(const c of state.cases.filter(c=>c.eventId===project.id)){
  const id=c.taskId||c.id;
  if(!tasks.some(t=>t.id===id))tasks.push({id,name:c.title,createdAt:''});
 }
 const earlier=state.threads.find(t=>t.eventId===project.id&&!t.taskId&&t.messages.length);
 if(earlier&&!tasks.some(t=>t.id===`legacy-${project.id}`))tasks.push({id:`legacy-${project.id}`,name:'Earlier project conversation',createdAt:earlier.messages[0].time});
 return tasks;
}
export const taskCases=(state:WorkspaceState,projectId:string,taskId:string)=>state.cases.filter(c=>c.eventId===projectId&&(c.taskId===taskId||(!c.taskId&&c.id===taskId)));
export function supplierOutreachLabel(request:ProcurementCase,vendorId:string){
 const messages=(request.messages||[]).filter(m=>m.vendorId===vendorId);
 if(messages.some(m=>m.direction==='received'))return 'Reply received';
 if(messages.some(m=>m.direction==='sent'))return 'Email sent · Awaiting reply';
 return 'Not contacted';
}
export function taskProgress(cases:ProcurementCase[]){
 const latest=cases.at(-1);const rows=latest?.approvalQueue||[];
 return {target:latest?.selectionTarget||1,secured:rows.filter(r=>r.status==='secured').length,approved:rows.filter(r=>r.status==='approved').length,pending:rows.filter(r=>r.status==='approval_needed').length};
}
export function taskDates(cases:ProcurementCase[],today=malaysiaToday()){
 const dates:{id:string;label:string;date:string}[]=[];
 for(const c of cases){
  if(validDate(c.deadline)&&c.deadline>=today)dates.push({id:c.id+'-deadline',label:'Task deadline',date:c.deadline});
  for(const row of c.approvalQueue||[]){
   if(!['approved','secured','approval_needed'].includes(row.status))continue;
   const v=c.vendors.find(v=>v.id===row.vendorId);
   if(v?.arrival&&validDate(v.arrival)&&v.arrival>=today)dates.push({id:c.id+'-'+v.id,label:`${v.name} · ${row.status==='secured'?'delivery':'proposed delivery'}`,date:v.arrival});
   if(row.status!=='secured'&&v?.validUntil&&validDate(v.validUntil)&&v.validUntil>=today)dates.push({id:c.id+'-'+v.id+'-validity',label:`Quote expires · ${v.name}`,date:v.validUntil});
  }
 }
 return dates.filter((d,i,all)=>all.findIndex(other=>other.label===d.label&&other.date===d.date)===i).sort((a,b)=>a.date.localeCompare(b.date));
}
