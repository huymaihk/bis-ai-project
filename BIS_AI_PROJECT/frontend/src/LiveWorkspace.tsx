import React, {lazy, Suspense, useEffect, useState} from 'react';
import {Home, FlaskConical, Megaphone, Image, Settings, BookOpen, Cpu, LogOut, ArrowUpRight} from 'lucide-react';
import './live.css';
import CatalogueTechnical from './components/CatalogueTechnical';
import ImageSources from './components/ImageSources';
import WorkflowPanel from './components/WorkflowPanel';
import {bisFetch, ProtectedImage, AssetLink, embedded} from './streamlitTransport';

const LiveOffice = lazy(()=>import('./components/LiveOffice').then(m=>({default:m.LiveOffice}))); 
type Asset = {id:string;name:string;folder:string;type:string;url:string};
type Product = Record<string, any> & {sku:string;_revision:string};
type MemoryRow = {key:string;conflict:boolean;heads:{id:string;content:string;created_at:string;source:string}[]};
async function api(path:string, method='GET', data?:unknown) {
  const response=await bisFetch('/api/'+path,{method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-BIS-Request':'1'},body:data===undefined?undefined:JSON.stringify(data)});
  const result=await response.json();
  if(!response.ok) throw new Error(typeof result.detail==='string'?result.detail:`Yêu cầu chưa thành công (${response.status})`);
  return result;
}
const nav=[['overview','Tổng quan',Home],['technical','Technical',FlaskConical],['marketing','Marketing',Megaphone],['images','Hình ảnh hoàn thiện',Image],['operations','Operations',Settings],['knowledge','Knowledge',BookOpen],['memory','Memory',Cpu]] as const;

export default function LiveWorkspace(){
  const [loading,setLoading]=useState(true);
  const [ready,setReady]=useState(false),[pin,setPin]=useState(''),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false);
  const [state,setState]=useState<any>(null),[assets,setAssets]=useState<Asset[]>([]),[mem,setMem]=useState<MemoryRow[]>([]);
  const [tab,setTab]=useState('overview'),[sku,setSku]=useState(''),[query,setQuery]=useState('');
  const [selectedAsset,setSelectedAsset]=useState<Asset|null>(null),[page,setPage]=useState(1),[source,setSource]=useState<Asset|null>(null);
  const [marketingPreview,setMarketingPreview]=useState<any>(null);
  const [fields,setFields]=useState<Record<string,any>>({}),[specs,setSpecs]=useState('{}');
  const [key,setKey]=useState(''),[content,setContent]=useState(''),[expected,setExpected]=useState<string[]>([]),[history,setHistory]=useState<any[]>([]),[answer,setAnswer]=useState('');
  const products:Product[]=state?.products||[];
  const product=products.find(p=>p.sku===sku);
  async function load(){
    const [s,a,m]=await Promise.all([api('state'),api('assets'),api('memory')]);
    setState(s);setAssets(a);setMem(m);setSku(old=>s.products.some((p:Product)=>p.sku===old)?old:(s.preferred_sku||s.products[0]?.sku||''));setReady(true);
  }
  useEffect(()=>{load().catch(e=>{setReady(false);setError(e.message);}).finally(()=>setLoading(false));},[]);
  useEffect(()=>{
    if(product){setFields(Object.fromEntries(['product_name','product_name_en','brand','description','evidence_quote','source_page','source_file','meta_description','meta_title','url_slug','highlights'].map(k=>[k,k==='highlights'?(Array.isArray(product[k])?product[k].join('\n'):product[k]||''):product[k]??''])));setSpecs(JSON.stringify(product.specifications||{},null,2));}
  },[sku,product?._revision]);
  useEffect(()=>{
    let active=true;setMarketingPreview(null);
    if(tab==='marketing'&&sku)api('products/'+encodeURIComponent(sku)+'/marketing').then(data=>{if(active)setMarketingPreview(data);}).catch(e=>{if(active)setError(e.message);});
    return()=>{active=false;};
  },[tab,sku,product?._revision]);
  async function action(fn:()=>Promise<void>){setBusy(true);setError('');setNotice('');try{await fn();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  async function saveProduct(){
    if(!product)return;
    const parsed=JSON.parse(specs);
    if(!parsed||Array.isArray(parsed)||typeof parsed!=='object')throw new Error('Thông số phải là JSON object');
    await api('products/'+encodeURIComponent(sku),'PUT',{revision:product._revision,fields:{...fields,highlights:String(fields.highlights||'').split('\n').map(v=>v.trim()).filter(Boolean),source_page:Number(fields.source_page)||1,specifications:parsed}});
    await load();setNotice('Đã lưu phiên bản mới. Nội dung cần được kiểm tra lại trước khi duyệt.');
  }
  const dirty=!!product && (Object.keys(fields).some(k=>String(fields[k]??'')!==String(k==='highlights'?(Array.isArray(product[k])?product[k].join('\n'):product[k]||''):product[k]??'')) || specs!==JSON.stringify(product.specifications||{},null,2));
  function field(name:string,label:string,multiline=false){return <label className="live-field" key={name}>{label}{multiline?<textarea value={fields[name]??''} onChange={e=>setFields({...fields,[name]:e.target.value})}/>:<input value={fields[name]??''} onChange={e=>setFields({...fields,[name]:e.target.value})}/>}</label>;}
  if(!ready&&(embedded||loading))return <main className="live-login"><section role="status"><h1>{loading?'Đang tải không gian BIS…':'Chưa tải được dữ liệu BIS'}</h1><p>{error||'Đang kết nối phiên đăng nhập hiện tại.'}</p>{!loading&&<button disabled={busy} onClick={()=>action(load)}>Thử tải lại</button>}<p>Phiên Streamlit đã quản lý đăng nhập. Nếu phiên hết hạn, tải lại trang để đăng nhập.</p></section></main>;
  if(!ready)return <main className="live-login"><form onSubmit={e=>{e.preventDefault();action(async()=>{await api('login','POST',{pin});setPin('');await load();});}}><div className="live-brand">BIS <span>TEXTILE AI</span></div><h1>Mở không gian làm việc</h1><p>Giao diện React · Kho dữ liệu BIS hiện có</p><label>PIN đăng nhập<input type="password" autoComplete="current-password" value={pin} onChange={e=>setPin(e.target.value)} required/></label><button disabled={busy}>Đăng nhập</button>{error&&<p role="alert">{error}</p>}</form></main>;

  return <div className="live-app" data-department={tab}><aside className="live-sidebar"><div className="live-brand">BIS <span>TEXTILE AI</span></div><p className="live-caption">PRODUCT WORKSPACE</p><nav>{nav.map(([id,label,Icon])=><button className={tab===id?'active':''} key={id} onClick={()=>{setTab(id);setQuery('');setError('');setNotice('');}}><Icon size={19}/>{label}</button>)}</nav><div className="live-sidebar-bottom"><label>Sản phẩm đang làm<select disabled={dirty||busy} value={sku} onChange={e=>setSku(e.target.value)}>{products.map(p=><option key={p.sku} value={p.sku}>{p.sku}</option>)}</select></label><p>{products.length} sản phẩm từ kho BIS</p><button onClick={()=>action(async()=>{await api('logout','POST',{});setReady(false);setState(null);setMem([]);setAssets([]);})}><LogOut size={16}/> Đăng xuất</button></div></aside>
  <div className="live-main"><header><div><span className="live-caption">BIS / {nav.find(n=>n[0]===tab)?.[1]}</span><h1>{sku||'Chưa có sản phẩm'}</h1><p>{product?.product_name||product?.product_name_en||'Nhập dữ liệu qua công cụ BIS hiện có'}</p></div><div className="live-chip">{product?.status==='APPROVED'?'Bản lưu đã duyệt':'Bản lưu cần kiểm tra'}</div></header>
  <div className="live-notifications" aria-live="polite">{error&&<div className="live-error" role="alert">{error}</div>}{notice&&<div className="live-success">{notice}</div>}</div>
  <main><nav className="bis-process" aria-label="Các bước xử lý sản phẩm">{[['technical','01','Nguồn'],['marketing','02','Nội dung'],['images','03','Hình ảnh hoàn thiện'],['operations','04','Duyệt & xuất']].map(([id,num,label])=><button key={id} aria-current={tab===id?'step':undefined} onClick={()=>setTab(id)}><span>{num}</span><strong>{label}</strong><ArrowUpRight size={15}/></button>)}</nav><div className="live-toolbar"><span>Dữ liệu lưu tại BIS · Đồng bộ Google cần kiểm tra</span><button disabled={busy||dirty} onClick={()=>action(load)}>Tải lại</button></div>
  {tab!=='technical'&&tab!=='images'&&<WorkflowPanel tab={tab} product={product} dirty={dirty} reload={load}/>}{tab==='technical'&&<CatalogueTechnical/>}
  {tab==='overview'&&<><Suspense fallback={<p>Đang mở phòng điều hành…</p>}><LiveOffice sku={sku} onNavigate={setTab}/></Suspense><h2>Nhật ký tác vụ đã lưu</h2>{state.jobs.length?<div className="live-list">{state.jobs.slice(0,15).map((j:any)=><article key={j.id}><strong>{j.task}</strong><span>{j.state}</span><small>{j.started_at}</small></article>)}</div>:<p>Chưa có nhật ký tác vụ. Agent chưa chạy trong phiên này.</p>}</>}
  {tab==='marketing'&&(product?<>
    <section className="live-panel"><small>MARKETING / BIÊN TẬP NỘI DUNG</small><h2>Biên tập dữ liệu có chứng cứ</h2><p>SKU {sku} · Làm việc ngay tại Marketing. Nội dung đã lưu vẫn cần kiểm tra trước khi duyệt.</p>
    <div className="catalogue-range">{field('product_name','Tên tiếng Việt')}{field('product_name_en','Tên tiếng Anh')}{field('brand','Hãng theo tài liệu')}</div>
    {field('description','Mô tả tiếng Việt · mục tiêu 250–450 ký tự',true)}<p>{String(fields.description||'').length} ký tự</p><button disabled={busy||dirty||!marketingPreview} onClick={()=>setFields({...fields,description:marketingPreview.copy.description,highlights:marketingPreview.copy.highlights.join('\n')})}>Gợi ý rút gọn và bỏ đặc điểm lặp ý</button>{field('highlights','Đặc điểm có chứng cứ · mỗi dòng một ý',true)}
    <details><summary>Chứng cứ và thông số nguồn</summary>{field('evidence_quote','Trích dẫn nguyên văn',true)}{field('source_file','Đường dẫn PDF nguồn trong dự án')}{field('source_page','Trang chứng cứ')}<label className="live-field">Thông số đã xác minh (JSON)<textarea value={specs} onChange={e=>setSpecs(e.target.value)}/></label></details>
    <h3>Tối ưu SEO</h3>{field('meta_title','Tiêu đề trang')}<p>{String(fields.meta_title||'').length}/70 ký tự</p>
    {field('meta_description','Mô tả trang',true)}<p>{String(fields.meta_description||'').length}/320 ký tự</p>
    {field('url_slug','Đường dẫn · phần sau /products/')}<p>https://bistextile.com/products/{fields.url_slug||'duong-dan-san-pham'}</p>
    {marketingPreview&&<><button disabled={busy||dirty} onClick={()=>setFields({...fields,meta_title:marketingPreview.seo.meta_title,meta_description:marketingPreview.seo.meta_description,url_slug:marketingPreview.seo.url_slug})}>Dùng gợi ý SEO từ bản đã lưu</button><div>{marketingPreview.seo.title_options?.map((title:string)=><button key={title} disabled={busy} onClick={()=>setFields({...fields,meta_title:title})}>{title}</button>)}</div></>}
    <div className="live-panel"><small>Xem trước tìm kiếm · minh họa, Google có thể hiển thị khác</small><h3 style={{color:'#1a0dab'}}>{fields.meta_title||'Tiêu đề trang'}</h3><p>{fields.meta_description||'Mô tả trang'}</p><small>https://bistextile.com/products/{fields.url_slug}</small></div>
    <div className="bis-workflow-actions"><button className="primary" disabled={busy||!dirty} onClick={()=>action(saveProduct)}>Lưu phiên bản</button><span>{dirty?'Có nội dung chưa lưu':'Đang xem bản đã lưu'}</span></div></section>
    <section className="live-panel"><h2>Xem trước bài viết đã lưu</h2><p>{dirty?'Bản xem trước chưa bao gồm chỉnh sửa chưa lưu.':'Bản xem trước theo phiên bản hiện tại.'}</p>{marketingPreview?<iframe title="Bản xem trước nội dung Marketing" sandbox="" srcDoc={marketingPreview.html} style={{width:'100%',height:550,border:'1px solid #d9c8b4',background:'#fff'}}/>:<p>Đang tải bản xem trước…</p>}</section>
    </>:<section className="live-panel"><p>Chọn sản phẩm hoặc phân tích tài liệu trong Technical để bắt đầu.</p></section>)}
  {tab==='images'&&<><section className="live-panel"><label>Chọn mã sản phẩm để xem ảnh hoàn thiện<select disabled={dirty||busy} value={sku} onChange={e=>setSku(e.target.value)}>{products.map(p=><option key={p.sku} value={p.sku}>{p.sku} · {p.product_name_en||p.product_name}</option>)}</select></label>{dirty&&<p>Lưu nội dung đang sửa trước khi đổi SKU.</p>}</section><ImageSources key={sku} product={product} assets={assets}/></>}
  {tab==='operations'&&<section className="live-panel"><h2>Duyệt và tạo nháp</h2><p>Trạng thái bản lưu: {product?.status||'Chưa có'}</p><p>Mở bàn kiểm duyệt phía trên để kiểm tra đúng phiên bản. Cổng tạo nháp giữ nguyên các điều kiện bảo vệ; kiểm tra hồ sơ cục bộ không cấp quyền xuất bản.</p><button disabled>Tạo bản nháp trên Haravan · chưa khả dụng</button></section>}
  {tab==='knowledge'&&<><h2>Thư viện tài liệu</h2><form className="live-search" onSubmit={e=>{e.preventDefault();action(async()=>setAnswer((await api('knowledge/search?q='+encodeURIComponent(query))).text));}}><input aria-label="Tra cứu tri thức" value={query} onChange={e=>setQuery(e.target.value)} placeholder="SKU, thuật ngữ, nội dung cần tra cứu…"/><button disabled={busy}>Tra cứu bộ nhớ</button></form>{answer&&<pre className="live-panel">{answer}</pre>}<div className="live-list">{assets.filter(a=>a.type==='pdf').map(a=><article key={a.id}><div><strong>{a.name}</strong><small>{a.folder}</small></div><AssetLink url={a.url}>Tải PDF ↗</AssetLink></article>)}</div></>}
  {tab==='memory'&&<div className="live-grid"><section className="live-panel"><h2>Bộ nhớ hiện hành</h2><input aria-label="Tìm bộ nhớ" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Tìm ghi chú…"/><div className="live-memory">{mem.filter(r=>(r.key+' '+r.heads.map(h=>h.content).join(' ')).toLowerCase().includes(query.toLowerCase())).map(r=><article key={r.key}><strong>{r.key}</strong>{r.conflict&&<p className="live-error">Có phiên bản xung đột — cần đối chiếu</p>}<p>{r.heads[0]?.content.slice(0,450)}</p><button onClick={()=>action(async()=>setHistory(await api('memory/history?key='+encodeURIComponent(r.key))))}>Xem phiên bản</button>{r.key.startsWith('user:')&&<button onClick={()=>{setKey(r.key.slice(5));setContent(r.heads[0].content);setExpected(r.heads.map(h=>h.id));}}>Sửa</button>}</article>)}</div></section><section className="live-panel"><h2>{expected.length?'Sửa ghi chú':'Thêm ghi chú'}</h2><label className="live-field">Tên ghi chú<input value={key} disabled={!!expected.length} onChange={e=>setKey(e.target.value)}/></label><label className="live-field">Nội dung<textarea value={content} onChange={e=>setContent(e.target.value)}/></label><button disabled={busy||!key.trim()} onClick={()=>action(async()=>{await api('memory','POST',{key:'user:'+key.trim(),content,expected});await load();setKey('');setContent('');setExpected([]);setNotice('Đã lưu bộ nhớ cục bộ với phiên bản mới.');})}>Lưu ghi chú</button>{expected.length>0&&<button disabled={busy} onClick={()=>action(async()=>{await api('memory','POST',{key:'user:'+key.trim(),content,expected,deleted:true});await load();setKey('');setContent('');setExpected([]);setNotice('Đã thu hồi; lịch sử vẫn được giữ.');})}>Thu hồi ghi chú</button>}<button onClick={()=>{setKey('');setContent('');setExpected([]);}}>Ghi chú mới</button><hr/><h3>Đồng bộ</h3><p>{state.sync.detail}</p><button disabled={busy} onClick={()=>action(async()=>{const s=await api('sync','POST',{});setState({...state,sync:s});setNotice(s.detail||`Trạng thái đồng bộ: ${s.state}`);})}>Thử đồng bộ Google</button><h3>Lịch sử phiên bản</h3>{history.map(h=><article key={h.id}><small>{h.created_at} · {h.deleted?'Đã thu hồi':'Bản lưu'}</small><pre>{h.content}</pre></article>)}</section></div>}
  </main></div></div>;
}
