import { NextRequest } from 'next/server';

export const maxDuration=120;

const allowed = /^(session|state|connections|actions|chat(?:\/references)?|events|email\/status|automation\/tick|events\/[^/]+\/(documents|tasks|settings|drive)|documents\/[^/]+|cases\/[^/]+\/(report|email\/(contact|send|sync|quote)))$/;

async function proxy(request: NextRequest, context: { params: Promise<{path:string[]}> }) {
  const path=(await context.params).path.join('/');
  if(!allowed.test(path)) return Response.json({detail:'Unknown API route.'},{status:404});
  const base=process.env.KAWTEAM_API_URL;
  const secret=process.env.KAWTEAM_GATEWAY_SECRET;
  if(!base || !secret) return Response.json({detail:'Backend environment is not configured.'},{status:503});
  if(request.method==='POST') {
    const origin=request.headers.get('origin');
    if(origin && origin!==request.nextUrl.origin && origin!==`http://${request.headers.get('host')}` && origin!==`https://${request.headers.get('host')}`)
      return Response.json({detail:'Request origin is not permitted.'},{status:403});
    if(Number(request.headers.get('content-length')||0)>4*1024*1024)
      return Response.json({detail:'Upload limit is 3 MB.'},{status:413});
  }
  const headers: Record<string,string>={'x-kawteam-gateway':secret};
  for(const key of ['cookie','content-type']) { const value=request.headers.get(key); if(value) headers[key]=value; }
  try {
    const upstream=await fetch(`${base.replace(/\/$/,'')}/${path}`,{method:request.method,headers,
      body:request.method==='GET'?undefined:await request.arrayBuffer(),cache:'no-store',signal:AbortSignal.timeout(90000)});
    const responseHeaders=new Headers({'content-type':upstream.headers.get('content-type')||'application/json','cache-control':'no-store'});
    const cookie=upstream.headers.get('set-cookie'); if(cookie) responseHeaders.set('set-cookie',cookie);
    return new Response(await upstream.arrayBuffer(),{status:upstream.status,headers:responseHeaders});
  } catch {
    return Response.json({detail:'Cannot reach the backend. Start FastAPI on port 8000 or check the deployment URL.'},{status:503});
  }
}

export const GET=proxy;
export const POST=proxy;
