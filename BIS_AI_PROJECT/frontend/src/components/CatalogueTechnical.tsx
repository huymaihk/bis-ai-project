import {useEffect,useState} from 'react';
import {bisFetch} from '../streamlitTransport';
type Catalogue={id:string;name:string;path:string;sha256:string;size:number;state:string;completed_pages:number};
async function request(path:string,body?:unknown){
  const response=await bisFetch('/api/'+path,{method:body===undefined?'GET':'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-BIS-Request':'1'},body:body===undefined?undefined:JSON.stringify(body)});
  const result=await response.json();
  if(!response.ok)throw Error(typeof result.detail==='string'?result.detail:'Không xử lý được yêu cầu');
  return result;
}
const states:Record<string,string>={NEEDS_REVIEW:'Không tìm thấy sản phẩm · cần đối chiếu',NEW:'Chưa phân tích',RUNNING:'Chưa hoàn tất',FAILED:'Cần kiểm tra lại',COMPLETED:'Đã phân tích'};
export default function CatalogueTechnical(){
  const [files,setFiles]=useState<Catalogue[]>([]),[selected,setSelected]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(''),[scanned,setScanned]=useState(false),[confirm,setConfirm]=useState(false),[dialog,setDialog]=useState(false),[progress,setProgress]=useState(''),[detail,setDetail]=useState('');
  const file=files.find(f=>f.id===selected);
  async function scan(manual=false){
    const data=await request(manual?'catalogues/scan':'catalogues',manual?{}:undefined);
    setFiles(data.files);setDetail(data.detail);setScanned(true);
    setSelected(old=>data.files.some((f:Catalogue)=>f.id===old)?old:'');
  }
  useEffect(()=>{scan().catch(e=>setError(e.message));},[]);
  async function analyse(again=false){
    if(!file)return;
    if(file.state==='COMPLETED'&&!again){setDialog(true);return;}
    setDialog(false);setBusy(true);setError('');setProgress('Chuẩn bị phân tích…');
    try{
      const run=await request(`catalogues/${file.id}/start`,{sha256:file.sha256,confirm:again});
      for(let page=1;page<=run.pages;page++){
        setProgress(`Đang phân tích trang ${page}/${run.pages} · ${file.name}`);
        const result=await request(`catalogues/${file.id}/page`,{run:run.run,page});
        if(page===run.pages)setProgress(result.state==='COMPLETED'?`Đã xử lý ${result.completed_pages} trang · ${result.products} kết quả. Dữ liệu cần được nghiệm thu.`:'Đã đọc hết tài liệu nhưng không có sản phẩm. Cần đối chiếu, chưa đánh dấu xanh.');
      }
    }catch(e){setError((e as Error).message);setProgress('Phân tích chưa hoàn tất.');}
    finally{await scan().catch(()=>{});setBusy(false);setConfirm(false);}
  }
  return <div className="catalogue-technical">
    <section className="live-panel catalogue-hero"><small>TECHNICAL / TÀI LIỆU VÀ DỮ LIỆU</small><h2>Từ tài liệu gốc.<br/>Đến sản phẩm chuẩn.</h2><p>Quét kho Catalogue, chọn tài liệu rồi phân tích. Trạng thái được lưu theo từng phiên bản file.</p><div className="technical-steps"><span>01 · Quét thư mục</span><span>02 · Chọn tài liệu</span><span>03 · Phân tích</span></div></section>
    <section className="live-panel"><div className="catalogue-heading"><div><h2>Kho Catalogue</h2><small>Google_Drive_Storage / 1_Catalogues</small></div><button className="primary" disabled={busy} onClick={async()=>{setBusy(true);setError('');try{await scan(true);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}>Quét thư mục</button></div><p>{detail}</p>
      <div className="catalogue-summary"><span>{files.length} tài liệu</span><span>🟢 {files.filter(f=>f.state==='COMPLETED').length} đã phân tích</span><span>⚪ {files.filter(f=>f.state!=='COMPLETED').length} cần xử lý</span></div>
      {scanned&&!files.length&&<p>Chưa tìm thấy PDF. Đặt file vào thư mục trên máy chạy BIS rồi bấm Quét thư mục.</p>}
      <div className="catalogue-files">{files.map(f=><button disabled={busy} aria-pressed={selected===f.id} data-completed={f.state==='COMPLETED'} key={f.id} onClick={()=>{setSelected(f.id);setConfirm(false);setDialog(false);setError('');setProgress('');}}><span className="catalogue-file-name">{f.state==='COMPLETED'?'🟢':'📄'} {f.name}</span><small>{f.path} · {(f.size/1024/1024).toFixed(2)} MB</small><span className="catalogue-status">{states[f.state]||f.state}</span></button>)}</div>
    </section>
    <section className="live-panel"><h2>Tài liệu cần phân tích</h2>{file?<><strong>{file.name}</strong><p>{states[file.state]||file.state} · Phân tích tạo bản làm việc để kiểm tra; bản sửa đã có được giữ lại.</p><button className="primary" disabled={busy} onClick={()=>analyse()}>{busy?'Đang phân tích…':file.state==='COMPLETED'?'Phân tích lại':'Phân tích tài liệu'}</button></>:<p>Chọn một tài liệu trong danh sách phía trên để bắt đầu.</p>}
    {dialog&&<div className="catalogue-confirm" role="alertdialog" aria-label="Xác nhận phân tích lại"><h3>Bạn có muốn phân tích lại tài liệu này không?</h3><p>{file?.name} đã được phân tích. Chạy lại sẽ gọi AI và có thể dùng thêm hạn mức API.</p><label><input type="checkbox" checked={confirm} onChange={e=>setConfirm(e.target.checked)}/> Tôi muốn phân tích lại</label><div className="bis-workflow-actions"><button className="primary" disabled={!confirm||busy} onClick={()=>analyse(true)}>Xác nhận phân tích lại</button><button onClick={()=>setDialog(false)}>Hủy</button></div></div>}
    {progress&&<p role="status">{progress}</p>}{error&&<p role="alert" className="catalogue-error">{error}</p>}</section>
  </div>;
}
