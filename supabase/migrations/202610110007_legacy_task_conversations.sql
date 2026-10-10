create or replace function public.kawteam_task_start(p_workspace uuid,p_secret text,p_event text,p_task jsonb,p_message jsonb,p_actor text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare event_data jsonb; existing_task jsonb; source_thread jsonb; copied_thread jsonb; task_id text:=p_task->>'id';
begin
 perform kawteam_private.authorize(p_workspace,p_secret);
 if p_actor not in ('organiser','teammate') then raise exception 'Read-only profile' using errcode='42501'; end if;
 if p_message->>'role'<>'user' or coalesce(length(task_id),0) not between 1 and 150 or coalesce(length(p_task->>'name'),0) not between 1 and 100 then raise exception 'Invalid task'; end if;
 perform pg_advisory_xact_lock(hashtextextended(p_workspace::text||'event'||p_event,0));
 event_data:=public.kawteam_record(p_workspace,p_secret,'event',p_event);
 if event_data is null then raise exception 'Event missing'; end if;
 select value into existing_task from jsonb_array_elements(coalesce(event_data->'tasks','[]'::jsonb)) where value->>'id'=task_id limit 1;
 if existing_task is null then
   if jsonb_array_length(coalesce(event_data->'tasks','[]'::jsonb))>=30 then raise exception 'Maximum 30 tasks per project'; end if;
   event_data:=jsonb_set(event_data,'{tasks}',coalesce(event_data->'tasks','[]'::jsonb)||jsonb_build_array(p_task));
   event_data:=public.kawteam_commit(p_workspace,p_secret,'event',p_event,event_data,(event_data->>'backendRevision')::int,'task-start-'||encode(extensions.digest(p_event||':'||task_id,'sha256'),'hex'),encode(extensions.digest(p_task::text,'sha256'),'hex'),p_actor);
   if p_task->>'sourceThreadId' is not null then
     if p_task->>'sourceThreadId'<>'event-'||p_event or task_id<>'legacy-'||p_event then raise exception 'Invalid legacy source'; end if;
     source_thread:=public.kawteam_record(p_workspace,p_secret,'thread',p_task->>'sourceThreadId');
     if source_thread is null then raise exception 'Legacy conversation missing'; end if;
     copied_thread:=jsonb_build_object('id','event-'||p_event||'-task-'||task_id,'eventId',p_event,'taskId',task_id,'messages',source_thread->'messages');
     perform public.kawteam_commit(p_workspace,p_secret,'thread',copied_thread->>'id',copied_thread,0,'legacy-copy-'||encode(extensions.digest(p_event||':'||task_id,'sha256'),'hex'),encode(extensions.digest(copied_thread::text,'sha256'),'hex'),p_actor);
   end if;
 end if;
 perform public.kawteam_project_chat(p_workspace,p_secret,p_event,task_id,p_message,null,p_actor);
 return event_data;
end; $$;
revoke all on function public.kawteam_task_start(uuid,text,text,jsonb,jsonb,text) from public;
grant execute on function public.kawteam_task_start(uuid,text,text,jsonb,jsonb,text) to anon,authenticated;
