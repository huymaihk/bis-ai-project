import {useEffect,useState} from 'react';
import {bisFetch} from '../streamlitTransport';
type Catalogue={id:string;name:string;path:string;sha256:string;size:number;state:string;completed_pages:number};
async function request(path:string,body?:unknown){
  const response=await bisFetch('/api/'+path,{method:body===undefined?'GET':'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-BIS-Request':'1'},body:body===undefined?undefined:JSON.stringify(body)});
  const result=await response.json();
  if(!response.ok)throw Error(typeof result.detail==='string'?result.detail:'Không xử lý được yêu cầu');
  return result;
}
const states:Record<string,string>={NEEDS_REVIEW:'Cần đối chiếu kết quả với nguồn',PARTIAL:'Đã phân tích một phần',NEW:'Chưa phân tích',RUNNING:'Chưa hoàn tất',FAILED:'Cần kiểm tra lại',COMPLETED:'Đã phân tích'};
export default function CatalogueTechnical(){
  const [files,setFiles]=useState<Catalogue[]>([]),[selected,setSelected]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(''),[scanned,setScanned]=useState(false),[confirm,setConfirm]=useState(false),[dialog,setDialog]=useState(false),[progress,setProgress]=useState(''),[detail,setDetail]=useState('');
  const [mode,setMode]=useState('full'),[from,setFrom]=useState(1),[to,setTo]=useState(1),[results,setResults]=useState<any[]>([]),[resultSku,setResultSku]=useState('');
  const result=results.find(r=>r.sku===resultSku);
  const file=files.find(f=>f.id===selected);
  async function scan(manual=false){
    const data=await request(manual?'catalogues/scan':'catalogues',manual?{}:undefined);
    setFiles(data.files);setDetail(data.detail);setScanned(true);
    setSelected(old=>data.files.some((f:Catalogue)=>f.id===old)?old:'');
  }
  useEffect(()=>{scan().catch(e=>setError(e.message));},[]);
  useEffect(()=>{
    setResults([]);setResultSku('');
    if(selected)request('catalogues/'+selected+'/results').then(d=>{setResults(d.products);setResultSku(d.products[0]?.sku||'');}).catch(e=>setError(e.message));
  },[selected,busy]);
  async function analyse(again=false,product?:any){
    if(!file)return;
    if(file.state==='COMPLETED'&&!again){setDialog(true);return;}
    setDialog(false);setBusy(true);setError('');setProgress('Chuẩn bị phân tích…');
    try{
      const run=await request(`catalogues/${file.id}/start`,{sha256:file.sha256,confirm:again,start_page:product?Number(product.source_page):mode==='full'?1:from,end_page:product?Number(product.source_page):mode==='full'?null:mode==='single'?from:to,sku:product?.sku||''});
      for(let page=run.start_page;page<=run.end_page;page++){
        setProgress(`Đang phân tích trang ${page}/${run.pages} · ${file.name}`);
        const result=await request(`catalogues/${file.id}/page`,{run:run.run,page});
        if(page===run.end_page)setProgress(['COMPLETED','PARTIAL'].includes(result.state)?`Đã xử lý ${result.completed_pages} trang · ${result.products} kết quả. Dữ liệu cần được nghiệm thu.`:`Đã xử lý · ${result.products} kết quả cần đối chiếu nguồn, chưa đánh dấu hoàn tất.`);
      }
    }catch(e){setError((e as Error).message);setProgress('Phân tích chưa hoàn tất.');}
    finally{await scan().catch(()=>{});setBusy(false);setConfirm(false);}
  }
  return <div className="catalogue-technical">
    <section className="live-panel catalogue-hero"><small>TECHNICAL / TÀI LIỆU VÀ DỮ LIỆU</small><h2>Từ tài liệu gốc.<br/>Đến sản phẩm chuẩn.</h2><p>Bóc tách mặt hàng trong các trang catalogue được chọn: SKU, tên, mô tả và thông số có trong nguồn. Không phải đọc nội dung bên trong cuốn sách được catalogue giới thiệu. Kết quả AI cần đối chiếu; phân tích xong không đồng nghĩa đã duyệt.</p><div className="technical-steps"><span>01 · Quét thư mục</span><span>02 · Chọn tài liệu</span><span>03 · Phân tích</span></div></section>
    <section className="live-panel"><div className="catalogue-heading"><div><h2>Kho Catalogue</h2><small>Google_Drive_Storage / 1_Catalogues</small></div><button className="primary" disabled={busy} onClick={async()=>{setBusy(true);setError('');try{await scan(true);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}>Quét thư mục</button></div><p>{detail}</p>
      <div className="catalogue-summary"><span>{files.length} tài liệu</span><span>🟢 {files.filter(f=>f.state==='COMPLETED').length} đã phân tích</span><span>⚪ {files.filter(f=>f.state!=='COMPLETED').length} cần xử lý</span></div>
      {scanned&&!files.length&&<p>Chưa tìm thấy PDF. Đặt file vào thư mục trên máy chạy BIS rồi bấm Quét thư mục.</p>}
      <div className="catalogue-files">{files.map(f=><button disabled={busy} aria-pressed={selected===f.id} data-completed={f.state==='COMPLETED'} key={f.id} onClick={()=>{setSelected(f.id);setConfirm(false);setDialog(false);setError('');setProgress('');}}><span className="catalogue-file-name">{f.state==='COMPLETED'?'🟢':'📄'} {f.name}</span><small>{f.path} · {(f.size/1024/1024).toFixed(2)} MB</small><span className="catalogue-status">{states[f.state]||f.state}</span></button>)}</div>
    </section>
    <section className="live-panel"><h2>Tài liệu cần phân tích</h2>{file?<><strong>{file.name}</strong><p>{states[file.state]||file.state} · Phân tích tạo bản làm việc để kiểm tra; bản sửa đã có được giữ lại.</p><div className="catalogue-range"><label>Phạm vi<select disabled={busy} value={mode} onChange={e=>setMode(e.target.value)}><option value="full">Toàn bộ tài liệu</option><option value="range">Khoảng trang</option><option value="single">Một trang</option></select></label>{mode!=='full'&&<label>{mode==='single'?'Trang':'Từ trang'}<input type="number" min="1" disabled={busy} value={from} onChange={e=>setFrom(Math.max(1,Number(e.target.value)))}/></label>}{mode==='range'&&<label>Đến trang<input type="number" min={from} disabled={busy} value={to} onChange={e=>setTo(Math.max(from,Number(e.target.value)))}/></label>}</div><button className="primary" disabled={busy} onClick={()=>analyse()}>{busy?'Đang phân tích…':file.state==='COMPLETED'?'Phân tích lại':'Phân tích tài liệu'}</button></>:<p>Chọn một tài liệu trong danh sách phía trên để bắt đầu.</p>}
    {dialog&&<div className="catalogue-confirm" role="alertdialog" aria-label="Xác nhận phân tích lại"><h3>Bạn có muốn phân tích lại tài liệu này không?</h3><p>{file?.name} đã được phân tích. Chạy lại sẽ gọi AI và có thể dùng thêm hạn mức API.</p><label><input type="checkbox" checked={confirm} onChange={e=>setConfirm(e.target.checked)}/> Tôi muốn phân tích lại</label><div className="bis-workflow-actions"><button className="primary" disabled={!confirm||busy} onClick={()=>analyse(true)}>Xác nhận phân tích lại</button><button onClick={()=>setDialog(false)}>Hủy</button></div></div>}
    {progress&&<p role="status">{progress}</p>}{error&&<p role="alert" className="catalogue-error">{error}</p>}</section>
    <section className="live-panel"><h2>Kết quả phân tích trong tài liệu</h2>{results.length?<><label>Mã sản phẩm<select disabled={busy} value={resultSku} onChange={e=>{setResultSku(e.target.value);setConfirm(false);}}>{results.map(r=><option key={r.sku} value={r.sku}>{r.sku} · {r.name_review?.state==='NAME_APPROVED'?r.name_review.suggested_name:r.product_name||r.product_name_en}</option>)}</select></label>{result&&<><TechnicalReview key={selected+':'+result.sku} file={file!} result={result}/>
<label><input type="checkbox" style={{width:'auto'}} checked={confirm} onChange={e=>setConfirm(e.target.checked)}/> Tôi muốn phân tích lại SKU {result.sku} trên trang nguồn</label><button disabled={busy||!confirm} onClick={()=>analyse(true,result)}>Yêu cầu phân tích lại sản phẩm</button></>}</>:<p>Chưa có kết quả của file này. Chọn tài liệu và phạm vi trang để phân tích.</p>}</section>
  </div>;
}

function TechnicalReview({file,result}:{file:Catalogue;result:any}){
  const [review,setReview]=useState(result.name_review),[name,setName]=useState(result.name_review?.suggested_name||result.product_name||''),[saving,setSaving]=useState(false),[message,setMessage]=useState(''),[source,setSource]=useState<any>(null),[loading,setLoading]=useState(false);
  useEffect(()=>{setReview(result.name_review);setName(result.name_review?.suggested_name||result.product_name||'');setSource(null);setMessage('');},[result]);
  const specs=[['Danh mục','category'],['Vật liệu','material'],['Màu','color'],['Khổ rộng (cm)','width_cm'],['Định lượng (g/m²)','weight_gsm'],['Kiểu dệt / kiểu dáng','pattern'],['Hoàn tất','finish'],['Đơn vị','unit'],['Giá USD','price_usd'],['Giá VNĐ','price_vnd']];
  return <div className="technical-review">
    <section><h3>1 · Nguồn PDF</h3><p>{file.name} · Trang {result.source_page} · SKU <strong>{result.sku}</strong></p><label>Tên tiếng Anh trong kết quả trích xuất</label><p><strong>{result.product_name_en||'Chưa trích được tên gốc'}</strong></p><blockquote>{result.evidence_quote||'Chưa có câu trích dẫn; cần mở trang để kiểm tra.'}</blockquote>
    <button disabled={loading} onClick={async()=>{setLoading(true);setMessage('');try{setSource(await request(`catalogues/${file.id}/source/${result.source_page}?sha256=${file.sha256}`));}catch(e){setMessage((e as Error).message);}finally{setLoading(false);}}}>{loading?'Đang mở…':'Xem trang PDF để đối chiếu'}</button>
    {source&&<details open><summary>Trang gốc và văn bản</summary><img style={{width:'100%',maxWidth:760}} src={source.image} alt={`Trang ${result.source_page} của ${file.name}`}/><pre style={{whiteSpace:'pre-wrap',maxHeight:260,overflow:'auto'}}>{source.text||'Trang không có lớp văn bản.'}</pre></details>}</section>
    <section><h3>2 · Kết quả đề xuất · chưa duyệt thông số</h3><p><strong>Tên AI:</strong> {result.product_name||'Chưa có'}</p><p>{result.description||'Nguồn chưa có mô tả được trích xuất.'}</p><small>Nguồn xử lý: {result.analysis_model||'Chưa ghi nhận'} · Thông tin cần đối chiếu PDF, không tự xem là chính xác.</small><details><summary>Thông số đã trích</summary><table><tbody>{specs.map(([label,key])=><tr key={key}><th style={{textAlign:'left',paddingRight:24}}>{label}</th><td>{result[key]??'Chưa có dữ liệu'}</td></tr>)}</tbody></table></details></section>
    <section><h3>3 · Duyệt tên và lưu hiệu chỉnh</h3><p>{review?.state==='NAME_APPROVED'?'Đã duyệt tên cho phiên bản PDF này.':'Tên chưa được duyệt.'} {review?.reason}</p><label>Tên tiếng Việt chuyên ngành<input maxLength={300} value={name} onChange={e=>setName(e.target.value)}/></label><p><small>Chỉ duyệt tên. Không duyệt thông số, không ghi đè bản nháp sản phẩm. Tên đã lưu được gợi ý lại cho cùng tài liệu, SKU và tên tiếng Anh.</small></p><button className="primary" disabled={saving||!name.trim()||!result.product_name_en} onClick={async()=>{setSaving(true);setMessage('');try{const next=await request(`catalogues/${file.id}/name`,{sku:result.sku,product_name_en:result.product_name_en,sha256:file.sha256,name,revision:review?.revision||[]});setReview(next);setMessage('Đã lưu tên vào bộ nhớ có phiên bản.');}catch(e){setMessage((e as Error).message);}finally{setSaving(false);}}}>{saving?'Đang lưu…':'Xác nhận tên và lưu bộ nhớ'}</button>{message&&<p role="status">{message}</p>}</section>
  </div>;
}
