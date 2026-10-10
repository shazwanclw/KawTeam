import {validDate} from './demo.ts';
import type {WorkspaceState} from './workspace.ts';

export type ScheduledItem={id:string;projectId?:string;project:string;label:string;date:string;href:string};
export const malaysiaToday=()=>{
 const parts=new Intl.DateTimeFormat('en',{timeZone:'Asia/Kuala_Lumpur',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
 return ['year','month','day'].map(key=>parts.find(p=>p.type===key)!.value).join('-');
};
export function scheduledItems(state:WorkspaceState):ScheduledItem[]{
 const items:ScheduledItem[]=[];
 for(const project of state.events){for(const [key,label] of [['eventDate','Event date'],['deadline','Delivery deadline']]){
  const date=project.facts[key];if(typeof date==='string'&&validDate(date)&&!items.some(item=>item.projectId===project.id&&item.date===date))items.push({id:`${project.id}-${key}`,projectId:project.id,project:project.name,label,date,href:`/projects/${project.id}`});
 }}
 for(const c of state.cases){if(!validDate(c.deadline)||items.some(item=>item.projectId&&item.projectId===c.eventId&&item.date===c.deadline))continue;
  const project=state.events.find(p=>p.id===c.eventId);items.push({id:c.id,projectId:c.eventId,project:project?.name||c.title,label:c.title,date:c.deadline,href:c.eventId?`/projects/${c.eventId}${c.taskId?`/tasks/${c.taskId}`:''}`:`/cases/${c.id}`});
 }
 for(const c of state.cases){
  const project=state.events.find(p=>p.id===c.eventId);const href=c.eventId?`/projects/${c.eventId}/tasks/${c.taskId||c.id}`:`/cases/${c.id}`;
  for(const row of c.approvalQueue||[]){
   if(!['approval_needed','approved','secured'].includes(row.status))continue;
   const v=c.vendors.find(v=>v.id===row.vendorId);if(!v)continue;
   if(v.arrival&&validDate(v.arrival))items.push({id:`${c.id}-${v.id}-arrival`,projectId:c.eventId,project:project?.name||c.title,label:`${v.name} · ${row.status==='secured'?'delivery':'proposed delivery'}`,date:v.arrival,href});
   if(row.status!=='secured'&&v.validUntil&&validDate(v.validUntil))items.push({id:`${c.id}-${v.id}-validity`,projectId:c.eventId,project:project?.name||c.title,label:`Quote expires · ${v.name}`,date:v.validUntil,href});
  }
 }
 return items.sort((a,b)=>a.date.localeCompare(b.date));
}
export function scheduleForMonth(items:ScheduledItem[],month:string,today=malaysiaToday(),selectedDate?:string|null){
 const visible=items.filter(item=>validDate(item.date)&&item.date.slice(0,7)===month&&(!selectedDate||item.date===selectedDate));
 return {upcoming:visible.filter(item=>item.date>=today),past:visible.filter(item=>item.date<today).reverse()};
}
export const upcomingDateCount=(state:WorkspaceState,today=malaysiaToday())=>new Set(scheduledItems(state).filter(item=>item.date>=today).map(item=>item.date)).size;
