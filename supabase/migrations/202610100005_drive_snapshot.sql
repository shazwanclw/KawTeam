-- Atomic replacement of current Drive documents and derived project memory.
create or replace function public.kawteam_drive_snapshot(p_workspace uuid,p_secret text,p_event text,p_expected integer,p_documents jsonb,p_archive jsonb,p_facts jsonb,p_fact_keys jsonb,p_source jsonb,p_actor text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare event_data jsonb; document jsonb; old_document jsonb; document_id text; run_id text:=extensions.gen_random_uuid()::text;
begin
 perform kawteam_private.authorize(p_workspace,p_secret);
 if p_actor not in ('organiser','teammate') then raise exception 'Read-only profile' using errcode='42501'; end if;
 if jsonb_typeof(p_documents)<>'array' or jsonb_array_length(p_documents)>20 or jsonb_typeof(p_archive)<>'array' or jsonb_typeof(p_facts)<>'object' then raise exception 'Invalid Drive snapshot'; end if;
 perform pg_advisory_xact_lock(hashtextextended(p_workspace::text || 'event' || p_event,0));
 event_data:=public.kawteam_record(p_workspace,p_secret,'event',p_event);
 if event_data is null then raise exception 'Event missing'; end if;
 if (event_data->>'backendRevision')::int<>p_expected then raise exception 'Stale Drive snapshot' using errcode='40001'; end if;
 for document in select value from jsonb_array_elements(p_documents) loop
  document_id:=document->>'id';
  if document->>'eventId' is distinct from p_event or document->>'driveFileId' is null or document->>'status'<>'ready' then raise exception 'Invalid project document'; end if;
  old_document:=public.kawteam_record(p_workspace,p_secret,'document',document_id);
  if old_document is not null and old_document->>'eventId' is distinct from p_event then raise exception 'Document scope mismatch' using errcode='42501'; end if;
  perform public.kawteam_commit(p_workspace,p_secret,'document',document_id,document,coalesce((old_document->>'backendRevision')::int,0),'drive-doc-'||run_id||'-'||document_id,encode(extensions.digest(document::text,'sha256'),'hex'),p_actor);
 end loop;
 for document_id in select value from jsonb_array_elements_text(p_archive) loop
  old_document:=public.kawteam_record(p_workspace,p_secret,'document',document_id);
  if old_document is null or old_document->>'eventId' is distinct from p_event or old_document->>'driveFileId' is null then raise exception 'Archive scope mismatch' using errcode='42501'; end if;
  old_document:=old_document||jsonb_build_object('status','archived');
  perform public.kawteam_commit(p_workspace,p_secret,'document',document_id,old_document,(old_document->>'backendRevision')::int,'drive-archive-'||run_id||'-'||document_id,encode(extensions.digest(old_document::text,'sha256'),'hex'),p_actor);
 end loop;
 if (select count(*) from public.kawteam_records where workspace_id=p_workspace and kind='document' and data->>'eventId'=p_event and coalesce(data->>'status','ready')<>'archived')>20 then raise exception 'Maximum 20 current project documents'; end if;
 event_data:=event_data||jsonb_build_object('facts',p_facts,'documentFactKeys',p_fact_keys,'driveSource',p_source,'memoryVersion',coalesce((event_data->>'memoryVersion')::int,0)+1);
 return public.kawteam_commit(p_workspace,p_secret,'event',p_event,event_data,p_expected,'drive-event-'||run_id,encode(extensions.digest(event_data::text,'sha256'),'hex'),p_actor);
end; $$;
create or replace function public.kawteam_documents(p_workspace uuid,p_secret text,p_event text) returns jsonb
language plpgsql security definer set search_path='' as $$
begin
 perform kawteam_private.authorize(p_workspace,p_secret);
 return coalesce((select jsonb_agg(data-'originalBase64' order by updated_at,id) from public.kawteam_records where workspace_id=p_workspace and kind='document' and data->>'eventId'=p_event and coalesce(data->>'status','ready')<>'archived'),'[]'::jsonb);
end; $$;
revoke all on function public.kawteam_drive_snapshot(uuid,text,text,integer,jsonb,jsonb,jsonb,jsonb,jsonb,text) from public;
grant execute on function public.kawteam_drive_snapshot(uuid,text,text,integer,jsonb,jsonb,jsonb,jsonb,jsonb,text) to anon,authenticated;
