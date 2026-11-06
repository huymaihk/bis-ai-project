import React,{useEffect,useState} from 'react';
import {Streamlit} from 'streamlit-component-lib';

export const embedded = window.parent !== window && window.location.pathname.includes('/component/');
type Work={id:string;url:string;method:string;body?:string;resolve:(r:Response)=>void;reject:(e:Error)=>void};
const queue:Work[]=[];
let current:Work|undefined;
let connected=false;
let framePending=false;
let lastHeight=0;
function fitFrame(){
  if(!embedded||framePending)return;
  framePending=true;
  requestAnimationFrame(()=>{
    framePending=false;
    const root=document.getElementById('root');
    if(!root)return;
    const height=Math.max(720,Math.ceil(Math.max(root.getBoundingClientRect().height,root.scrollHeight))+24);
    if(height!==lastHeight){lastHeight=height;Streamlit.setFrameHeight(height);}
  });
}
function next(){
  if(!connected||current||!queue.length)return;
  current=queue.shift();
  const {id,url,method,body}=current!;
  Streamlit.setComponentValue({id,url,method,body});
}
if(embedded){
  document.documentElement.classList.add('bis-embedded');
  const root=document.getElementById('root');
  if(root)new ResizeObserver(fitFrame).observe(root);
  // Images and expanded content can overflow without changing the root box.
  if(root)new MutationObserver(fitFrame).observe(root,{childList:true,subtree:true});
  document.addEventListener('load',fitFrame,true);
  window.addEventListener('resize',fitFrame);
  document.fonts.ready.then(fitFrame);
  Streamlit.events.addEventListener(Streamlit.RENDER_EVENT,(event:any)=>{
    connected=true;
    const response=event.detail.args.response;
    if(current&&response?.id===current.id){
      const work=current;current=undefined;
      if(response.error)work.reject(new Error(response.error));
      else{
        const bytes=Uint8Array.from(atob(response.body),c=>c.charCodeAt(0));
        work.resolve(new Response(bytes,{status:response.status,headers:{'Content-Type':response.content_type}}));
      }
    }
    fitFrame();
    next();
  });
  Streamlit.setComponentReady();
}

export function bisFetch(url:string,init:RequestInit={}):Promise<Response>{
  if(!embedded)return fetch(url,init);
  return new Promise((resolve,reject)=>{
    queue.push({id:crypto.randomUUID(),url,method:init.method||'GET',body:init.body as string|undefined,resolve,reject});
    next();
  });
}
export function ProtectedImage(props:React.ImgHTMLAttributes<HTMLImageElement>){
  const [src,setSrc]=useState<string>(),[failed,setFailed]=useState(false);
  useEffect(()=>{
    let active=true,objectUrl:string|undefined;
    setSrc(undefined);setFailed(false);
    if(!props.src)return;
    if(!embedded||!props.src.startsWith('/api/')){setSrc(props.src);return;}
    bisFetch(props.src).then(r=>{if(!r.ok)throw Error();return r.blob();}).then(b=>{
      objectUrl=URL.createObjectURL(b);if(active)setSrc(objectUrl);else URL.revokeObjectURL(objectUrl);
    }).catch(()=>{if(active)setFailed(true);});
    return()=>{active=false;if(objectUrl)URL.revokeObjectURL(objectUrl);};
  },[props.src]);
  return failed?<p role="alert">Không đọc được ảnh/trang PDF này.</p>:src?<img {...props} src={src}/>:<p>Đang đọc ảnh…</p>;
}
export function AssetLink({url,children,filename}:{url:string;children:React.ReactNode;filename?:string}){
  const [error,setError]=useState('');
  return <><button onClick={async()=>{
    try{
      const response=await bisFetch(url);if(!response.ok)throw Error('Không đọc được tệp');
      const blob=await response.blob();const src=URL.createObjectURL(blob);
      const a=document.createElement('a');a.href=src;a.download=filename||(blob.type.includes('pdf')?'tai-lieu.pdf':'anh-goc');a.click();
      setTimeout(()=>URL.revokeObjectURL(src),60000);
    }catch(e){setError((e as Error).message);}
  }}>{children}</button>{error&&<span role="alert">{error}</span>}</>;
}
