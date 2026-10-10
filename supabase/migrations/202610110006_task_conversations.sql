create or replace function public.kawteam_project_chat(p_workspace uuid,p_secret text,p_event text,p_task text,p_message jsonb,p_case jsonb,p_actor text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare thread_id text:='event-'||p_event||case when p_task is null then '' else '-task-'||p_task end; thread_data jsonb; event_data jsonb; prior jsonb; user_message jsonb; message_id text:=p_message->>'id';
begin
 perform kawteam_private.authorize(p_workspace,p_secret);
 if p_actor not in ('organiser','teammate') then raise exception 'Read-only profile' using errcode='42501'; end if;
 event_data:=public.kawteam_record(p_workspace,p_secret,'event',p_event);
 if event_data is null then raise exception 'Event missing'; end if;
 if p_task is not null and not exists(select 1 from jsonb_array_elements(coalesce(event_data->'tasks','[]'::jsonb)) t where t->>'id'=p_task) then raise exception 'Task does not belong to project' using errcode='42501'; end if;
 perform pg_advisory_xact_lock(hashtextextended(p_workspace::text || 'thread' || thread_id,0));
 thread_data:=coalesce(public.kawteam_record(p_workspace,p_secret,'thread',thread_id),jsonb_build_object('id',thread_id,'eventId',p_event,'taskId',p_task,'messages','[]'::jsonb,'backendRevision',0));
 if p_message->>'role'='user' then
   select value into prior from jsonb_array_elements(thread_data->'messages') where value->>'id'=message_id limit 1;
   if prior is not null then
     if prior->>'body'<>p_message->>'body' then raise exception 'Idempotency key reused for a different message'; end if;
     return thread_data;
   end if;
 elsif p_message->>'role'='assistant' then
   select value into prior from jsonb_array_elements(thread_data->'messages') where value->>'inReplyTo'=p_message->>'inReplyTo' limit 1;
   if prior is not null then return thread_data; end if;
   select value into user_message from jsonb_array_elements(thread_data->'messages') where value->>'id'=p_message->>'inReplyTo' and value->>'role'='user' limit 1;
   if user_message is null then raise exception 'Missing user message'; end if;
 else raise exception 'Invalid message role'; end if;
 if jsonb_array_length(thread_data->'messages')>=150 then raise exception 'Conversation limit reached'; end if;
 if p_case is not null then
   if p_message->>'role'<>'assistant' or p_case->>'eventId'<>p_event or (p_case->>'taskId') is distinct from p_task or p_message->>'caseId'<>p_case->>'id' then raise exception 'Invalid resulting request'; end if;
   perform public.kawteam_commit(p_workspace,p_secret,'case',p_case->>'id',p_case,coalesce((p_case->>'backendRevision')::int,0),'task-case-'||encode(extensions.digest(thread_id||':'||(p_message->>'inReplyTo'),'sha256'),'hex'),encode(extensions.digest(p_case::text,'sha256'),'hex'),p_actor);
 end if;
 thread_data:=jsonb_set(thread_data,'{messages}',(thread_data->'messages')||jsonb_build_array(p_message));
 return public.kawteam_commit(p_workspace,p_secret,'thread',thread_id,thread_data,(thread_data->>'backendRevision')::int,'project-message-'||encode(extensions.digest(thread_id||':'||message_id,'sha256'),'hex'),encode(extensions.digest(p_message::text,'sha256'),'hex'),p_actor);
end; $$;

revoke all on function public.kawteam_project_chat(uuid,text,text,text,jsonb,jsonb,text) from public;
grant execute on function public.kawteam_project_chat(uuid,text,text,text,jsonb,jsonb,text) to anon,authenticated;

-- A new conversation and its first user message are saved together. Event lock
-- serialises concurrent task starts without losing another teammate's task.
create or replace function public.kawteam_task_start(p_workspace uuid,p_secret text,p_event text,p_task jsonb,p_message jsonb,p_actor text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare event_data jsonb; existing_task jsonb; task_id text:=p_task->>'id';
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
 end if;
 perform public.kawteam_project_chat(p_workspace,p_secret,p_event,task_id,p_message,null,p_actor);
 return event_data;
end; $$;
revoke all on function public.kawteam_task_start(uuid,text,text,jsonb,jsonb,text) from public;
grant execute on function public.kawteam_task_start(uuid,text,text,jsonb,jsonb,text) to anon,authenticated;
