import {useEffect, useState} from 'react';
import {bisFetch, embedded} from '../streamlitTransport';

const sections:Record<string,[number,string,string]> = {
  overview:[0,'Bắt đầu từ tài liệu','Chọn PDF → trích trang → kiểm tra → duyệt'],
  technical:[0,'Quét và phân tích Catalogue','Quét thư mục → chọn tài liệu → phân tích → kiểm tra dữ liệu'],
  marketing:[1,'Mở bàn biên tập và HTML','Kiểm tra chứng cứ, biên tập SEO và xem trước bài viết'],
  images:[2,'Mở studio xử lý ảnh','Chọn ảnh PDF/web, ghép nền, tạo bản AI và duyệt ảnh'],
  operations:[3,'Mở bàn kiểm duyệt','Đối soát bản lưu, duyệt phiên bản và xem cổng tạo nháp có bảo vệ'],
  knowledge:[4,'Mở công cụ tài liệu','Lập chỉ mục PDF, dịch bản thử và xem lịch sử tác vụ'],
  memory:[4,'Mở lịch sử và bộ nhớ','Xem nhật ký, xuất bộ nhớ và kiểm tra đồng bộ'],
};

export default function WorkflowPanel({tab, product, dirty, reload}:{tab:string;product:any;dirty:boolean;reload:()=>Promise<void>}) {
  const [report,setReport]=useState<any>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const section=sections[tab]||sections.overview;
  async function request(path:string,body?:unknown){
    const response=await bisFetch('/api/'+path,{method:body===undefined?'GET':'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-BIS-Request':'1'},body:body===undefined?undefined:JSON.stringify(body)});
    const result=await response.json();
    if(!response.ok)throw Error(typeof result.detail==='string'?result.detail:'Chưa xử lý được yêu cầu');
    return result;
  }
  useEffect(()=>{
    let active=true;setReport(null);setError('');
    if(product?.sku)request('workflow/'+encodeURIComponent(product.sku)+'/check').then(r=>{if(active)setReport(r);}).catch(e=>{if(active)setError(e.message);});
    return()=>{active=false;};
  },[product?.sku,product?._revision]);
  async function run(){
    setBusy(true);setError('');
    try {const r=await request('workflow/'+encodeURIComponent(product.sku)+'/check',{revision:product._revision});setReport(r);await reload();}
    catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  return <section className="live-panel bis-workflow" aria-label="Quy trình nghiệp vụ">
    <h2>{tab==='technical'?'Tiếp nhận và phân tích tài liệu':`Hồ sơ công việc ${product?.sku||''}`}</h2>
    <p>{section[2]}. Công cụ sử dụng cùng bản làm việc và bộ nhớ của BIS.</p>
    {tab==='technical'&&<ol className="technical-steps"><li><strong>01 · Tài liệu</strong><small>Quét thư mục hoặc tải PDF lên</small></li><li><strong>02 · Phân tích</strong><small>Chọn file và xác nhận chạy</small></li><li><strong>03 · Kiểm tra</strong><small>Đối chiếu SKU và chứng cứ</small></li></ol>}
    <div className="bis-workflow-actions">
      <button className="primary" disabled={busy||dirty||!embedded} onClick={async()=>{
        setBusy(true);setError('');
        try{await request('workspace/open',{step:section[0],sku:product?.sku||''});}
        catch(e){setError((e as Error).message);setBusy(false);}
      }}>{section[1]} ↗</button>
      <button disabled={busy||dirty||!product} onClick={run}>{busy?'Đang xử lý…':'Kiểm tra hồ sơ đã lưu'}</button>
    </div>
    {dirty&&<p role="status">Có chỉnh sửa chưa lưu. Lưu phiên bản trước khi mở công cụ hoặc kiểm tra hồ sơ.</p>}
    {!embedded&&<p>Công cụ nghiệp vụ mở trong website Streamlit BIS sau đăng nhập.</p>}
    {error&&<p role="alert">{error}</p>}
    {report?.checks?.length>0&&<details open={tab==='operations'}><summary>Kết quả kiểm tra gần nhất · {new Date(report.checked_at).toLocaleString('vi-VN')}</summary>
      {report.stale&&<p role="alert">Nội dung đã thay đổi sau lần kiểm tra. Cần chạy lại.</p>}
      <div className="bis-checks">{report.checks.map((c:any)=><article key={c.key}><strong>{c.label}</strong><span data-state={c.state}>{({PASS:'Qua kiểm tra',BLOCKED:'Cần bổ sung',REVIEW:'Cần đối chiếu',UNKNOWN:'Chưa xác minh'} as Record<string,string>)[c.state]||c.state}</span><p>{c.detail}</p></article>)}</div>
      <p>{report.detail}</p>
    </details>}
    <small>Chạy theo yêu cầu trong phiên hiện tại. Kiểm tra cục bộ không tự duyệt, không đăng Haravan; ảnh và nguồn thay đổi cần kiểm tra lại.</small>
  </section>;
}
