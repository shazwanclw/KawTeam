import type { DemoState } from './demo';

export type AssistantSettings={mode:'general'|'research'|'liaise';instructions:string;shortlistSize:number;preferredVendorId:string|null};
export type ProjectTask={id:string;name:string;createdAt:string};
export type DriveSource={url:string;status:'awaiting_access'|'ready'|'partial'|'error';fileCount:number;lastSyncedAt:string|null;message:string;errors?:{name:string;message:string}[];memorySource?:{url:string;fileCount:number;lastSyncedAt:string|null}};
export type EventMemory={id:string;name:string;sample?:boolean;backendRevision:number;memoryVersion?:number;facts:Record<string,string|number>;tasks?:ProjectTask[];assistantSettings?:AssistantSettings;createdAt?:string;driveSource?:DriveSource};
export type EventDocument={id:string;eventId:string;name:string;size:number;characters:number;status:string;sample?:boolean;text?:string};
export type ChatMessage={id:string;role:'user'|'assistant';body:string;time:string;provider?:string;citations?:string[];caseId?:string;inReplyTo?:string;attachments?:{id:string;name:string}[]};
export type Thread={id:string;eventId:string;taskId?:string|null;messages:ChatMessage[];backendRevision:number};
export type WorkspaceState=DemoState & {events:EventMemory[];documents:EventDocument[];threads:Thread[]};
export type Connections={database:string;ai:string;search:string;email:string;workbuddy:string;model:string};

export async function api<T>(path:string,body?:unknown):Promise<T> {
  const response=await fetch(`/api/kawteam/${path}`,{method:body?'POST':'GET',headers:body instanceof FormData?undefined:body?{'content-type':'application/json'}:undefined,
    body:body instanceof FormData?body:body?JSON.stringify(body):undefined,cache:'no-store'});
  const value=await response.json();
  if(!response.ok) throw new Error(typeof value.detail==='string'?value.detail:'The request failed validation. Check your message and event details.');
  return value as T;
}
