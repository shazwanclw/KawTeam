'use client';

import {usePathname} from 'next/navigation';

/** Exact reference background materials; route mapping follows KawTeam's current navigation. */
export function Aurora(){
 const path=usePathname();
 const view=path.includes('calendar')?'calendar':path.includes('approval')?'approvals':path.includes('activity')?'activity':path==='/connections'?'connections':path.includes('/tasks/')?'tasks':'chat';
 return <div className="kt-aurora" aria-hidden="true" data-view={view}><span/><span/><span/><span/><span/></div>;
}
