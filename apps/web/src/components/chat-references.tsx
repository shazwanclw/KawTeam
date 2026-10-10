'use client';

import {useState} from 'react';
import {FileText,Link2,Paperclip,X} from 'lucide-react';
import {Dialog,DialogContent,DialogDescription,DialogHeader,DialogTitle} from '@/components/ui/dialog';
import {Button} from '@/components/ui/button';

export function ReferenceTools({showDrive,driveUrl,onDrive,files,onFiles,disabled,onError}:{showDrive:boolean;driveUrl:string;onDrive:(url:string)=>void;files:File[];onFiles:(files:File[])=>void;disabled:boolean;onError:(message:string)=>void}){
 const [open,setOpen]=useState(false);const [url,setUrl]=useState('');
 function selectFiles(incoming:FileList|null){
  const next=[...files,...Array.from(incoming||[])];
  if(next.length>3){onError('Attach up to three reference files.');return;}
  if(next.some(f=>!(/\.(pdf|docx|xlsx|txt|md|csv)$/i.test(f.name)))){onError('Use PDF, DOCX, XLSX, TXT, Markdown or CSV files.');return;}
  if(next.reduce((sum,f)=>sum+f.size,0)>3*1024*1024){onError('Reference files must total 3 MB or less.');return;}
  onFiles(next);
 }
 return <>{showDrive&&<button type="button" className={`chat-tool-button ${driveUrl?'has-reference':''}`} aria-label="Add Google Drive link" title="Add Google Drive link" disabled={disabled} onClick={()=>{setUrl(driveUrl);setOpen(true);}}><Link2 size={17}/></button>}<label className={`chat-tool-button chat-file-picker ${disabled?'disabled':''}`} title="Attach reference files"><Paperclip size={17}/><span className="sr-only">Attach reference files</span><input type="file" aria-label="Attach reference files" accept=".pdf,.docx,.xlsx,.txt,.md,.csv" multiple disabled={disabled} onChange={e=>{selectFiles(e.currentTarget.files);e.currentTarget.value='';}}/></label><Dialog open={open} onOpenChange={setOpen}><DialogContent className="kt-dialog"><DialogHeader><span className="dialog-symbol"><Link2 size={22}/></span><DialogTitle>Add a Drive reference</DialogTitle><DialogDescription>This link will become the project’s shared context when you send your request.</DialogDescription></DialogHeader><form className="kt-form" onSubmit={e=>{e.preventDefault();try{const link=new URL(url.trim());if(!['drive.google.com','docs.google.com'].includes(link.hostname)||link.protocol!=='https:')throw new Error();onDrive(link.href);setOpen(false);}catch{onError('Enter a Google Drive folder or document link.');}}}><label htmlFor="chat-drive-link">Google Drive link<input id="chat-drive-link" type="url" value={url} onChange={e=>setUrl(e.target.value)} placeholder="https://drive.google.com/drive/folders/…" maxLength={1000} required autoFocus/></label><p className="field-help">KawTeam can read content it has permission to access.</p><div className="kt-dialog-footer"><Button type="button" variant="outline" onClick={()=>setOpen(false)}>Cancel</Button><Button disabled={!url.trim()||disabled}>Add reference</Button></div></form></DialogContent></Dialog></>;
}

export function ReferenceChips({driveUrl,onDrive,files,onFiles,disabled}:{driveUrl:string;onDrive:(url:string)=>void;files:File[];onFiles:(files:File[])=>void;disabled:boolean}){
 if(!driveUrl&&!files.length)return null;
 return <div className="chat-reference-chips" aria-label="Attached references">{driveUrl&&<span><Link2 size={14}/><a href={driveUrl} target="_blank" rel="noreferrer">Drive reference</a><button type="button" aria-label="Remove Drive reference" disabled={disabled} onClick={()=>onDrive('')}><X size={13}/></button></span>}{files.map((file,index)=><span key={`${file.name}-${index}`}><FileText size={14}/><span title={file.name}>{file.name}</span><button type="button" aria-label={`Remove ${file.name}`} disabled={disabled} onClick={()=>onFiles(files.filter((_,i)=>i!==index))}><X size={13}/></button></span>)}</div>;
}
