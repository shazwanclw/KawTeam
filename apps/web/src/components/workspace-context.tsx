'use client';

import {createContext,useContext,useEffect,useRef,useState,type ReactNode,type Dispatch,type SetStateAction} from 'react';
import {applyAction,initialState,restoreState,profiles,type Action,type DemoState,type ProfileId} from '@/lib/demo';
import {api,type WorkspaceState,type Connections} from '@/lib/workspace';
import {Icon} from './icon';

type ContextValue={state:WorkspaceState;profile:ProfileId;isApi:boolean;busy:boolean;loading:boolean;connections:Connections|null;
  navOpen:boolean;setNavOpen:Dispatch<SetStateAction<boolean>>;
  switchProfile:(id:ProfileId)=>Promise<void>;perform:(action:Action,message?:string)=>Promise<boolean>;
  refresh:()=>Promise<void>;acceptState:(value:WorkspaceState|((previous:WorkspaceState)=>WorkspaceState))=>void;notify:(message:string)=>void};
const Context=createContext<ContextValue|null>(null);
export function useDemo(){const value=useContext(Context);if(!value)throw new Error('Workspace provider missing');return value;}
const extend=(state:DemoState):WorkspaceState=>({...state,events:[],documents:[],threads:[]});

export function DemoProvider({children}:{children:ReactNode}) {
  const isApi=process.env.NEXT_PUBLIC_DATA_MODE==='api';
  const [state,setState]=useState<WorkspaceState>(()=>extend(isApi?{version:2,cases:[]}:initialState()));
  const [profile,setProfile]=useState<ProfileId>('organiser');
  const [navOpen,setNavOpen]=useState(false);
  const [toast,setToast]=useState('');const [loading,setLoading]=useState(isApi);const [busy,setBusy]=useState(false);
  const [connectionError,setConnectionError]=useState('');const [connections,setConnections]=useState<Connections|null>(null);
  const running=useRef(false);
  async function refresh(){
    if(!isApi)return;
    const value=await api<WorkspaceState & {profile:ProfileId}>('state');
    setState(value);setProfile(value.profile);setConnectionError('');
  }
  useEffect(()=>{
    let alive=true;
    async function boot(){
      try {
        if(isApi){
          let response=await fetch('/api/kawteam/state',{cache:'no-store'});
          if(response.status===401){
            const saved=localStorage.getItem('kawteam:profile');
            await api('session',{profile:profiles.some(p=>p.id===saved)?saved:'organiser'});
            response=await fetch('/api/kawteam/state',{cache:'no-store'});
          }
          const value=await response.json();
          if(!response.ok)throw new Error(value.detail||'Backend unavailable.');
          if(alive){setState(value);setProfile(value.profile);setConnections(await api<Connections>('connections'));}
        }else if(alive){setState(extend(restoreState(localStorage.getItem('kawteam:v2'))));}
      }catch(error){if(alive)setConnectionError(error instanceof Error?error.message:'Could not load the workspace.');}
      finally{if(alive)setLoading(false);}
    }
    void boot();
    const timer=setInterval(()=>{if(isApi && !running.current && document.visibilityState==='visible')void refresh().catch(()=>{});},15000);
    return()=>{alive=false;clearInterval(timer);};
    // Bootstrap once; subsequent refreshes and role changes are explicit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  },[isApi]);
  useEffect(()=>{if(!toast)return;const timer=setTimeout(()=>setToast(''),6500);return()=>clearTimeout(timer);},[toast]);
  async function perform(action:Action,message='Saved to your team workspace.'){
    if(running.current){setToast('Another action is saving. Try again in a moment.');return false;}
    running.current=true;setBusy(true);
    try{
      if(isApi){
        const current='caseId' in action?state.cases.find(c=>c.id===action.caseId):null;
        const value=await api<WorkspaceState & {profile:ProfileId}>('actions',{...action,expectedRevision:current?.backendRevision||0,requestId:crypto.randomUUID()});
        setState(value);
      }else{
        const next=applyAction(state,profile,action);setState(extend(next));localStorage.setItem('kawteam:v2',JSON.stringify(next));
      }
      setToast(message);return true;
    }catch(error){setToast(error instanceof Error?error.message:'Save failed.');if(isApi)await refresh().catch(()=>{});return false;}
    finally{running.current=false;setBusy(false);}
  }
  async function switchProfile(id:ProfileId){
    try{if(isApi)await api('session',{profile:id});setProfile(id);localStorage.setItem('kawteam:profile',id);setToast(`Viewing as ${profiles.find(p=>p.id===id)!.role}.`);}
    catch(error){setToast(error instanceof Error?error.message:'Profile change failed.');}
  }
  return <Context.Provider value={{state,profile,isApi,busy,loading,connections,navOpen,setNavOpen,switchProfile,perform,refresh,acceptState:setState,notify:setToast}}>
    {connectionError&&<div className="connection-error" role="alert">{connectionError}<button onClick={()=>void refresh().catch(e=>setConnectionError(e.message))}>Retry connection</button></div>}
    {children}
    {toast&&<div className="toast" role="status"><Icon name="check" size={18}/><span>{toast}</span><button aria-label="Dismiss notification" onClick={()=>setToast('')}><Icon name="close" size={16}/></button></div>}
  </Context.Provider>;
}
