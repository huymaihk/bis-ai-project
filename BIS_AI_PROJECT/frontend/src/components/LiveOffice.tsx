import React,{lazy,Suspense,useEffect,useRef,useState} from 'react';
import {SceneBoundary} from './SceneBoundary';
import {AgentRobotAvatar} from './AgentRobotAvatar';
import {DepartmentId} from '../types/bisTypes';
import type {RobotEyeStyle, RobotFinishPreset} from '../utils/agentOfficeSim';

const Canvas=lazy(()=>import('./AgentOffice3DCanvas').then(m=>({default:m.AgentOffice3DCanvas})));
const departments:[DepartmentId,string,string][]=[['technical','Technical','Nguồn và thông số'],['marketing','Marketing','Nội dung và SEO'],['imagestudio','Image Studio','Ảnh nguồn và thành phẩm'],['operations','Operations','Đối soát và duyệt'],['knowledge','Knowledge','Tài liệu và trích dẫn'],['memory','Memory','Lịch sử và hiệu chỉnh']];

export function LiveOffice({sku,onNavigate}:{sku:string;onNavigate:(id:string)=>void}){
  const [eyeStyle,setEyeStyle]=useState<RobotEyeStyle>('rounded');
  const [finish,setFinish]=useState<RobotFinishPreset>('anodized-metal');
  const [mode,setMode]=useState<'3d'|'image'>('3d');
  const [reduced,setReduced]=useState(()=>window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const [timeout,setTimedOut]=useState(false);
  const mount=useRef<HTMLDivElement>(null);
  useEffect(()=>{
    setTimedOut(false);
    if(mode!=='3d')return;
    const timer=window.setTimeout(()=>{
      if(!mount.current?.querySelector('[data-rendered="true"]')){setMode('image');setTimedOut(true);}
    },15000);
    return()=>window.clearTimeout(timer);
  },[mode,sku]);
  function navigate(id:DepartmentId){onNavigate(id==='imagestudio'?'images':id);}
  return <section className="bis-office">
    <div className="bis-office-heading"><div><span className="live-caption">BIS TEXTILE AI / PHÒNG ĐIỀU HÀNH</span><h2>Đội ngũ chuyên môn của bạn</h2><p>Chọn phòng ban để tiếp tục công việc cho {sku||'sản phẩm đang chọn'}.</p></div><div className="bis-office-controls"><button aria-pressed={mode==='3d'} onClick={()=>setMode('3d')}>3D tương tác</button><button aria-pressed={mode==='image'} onClick={()=>setMode('image')}>Ảnh toàn cảnh</button><label><input type="checkbox" checked={reduced} onChange={e=>setReduced(e.target.checked)}/> Giảm chuyển động</label></div></div>
    <p className="bis-office-disclosure">Nhân vật và hội thoại trong cảnh là mô phỏng thiết kế. Trạng thái nghiệp vụ thật nằm trong nhật ký bên dưới.</p>
    {timeout&&<p role="status">Cảnh 3D chưa khởi tạo xong. Đang hiển thị ảnh toàn cảnh; bạn có thể thử lại 3D.</p>}
    <div ref={mount} className="bis-office-stage">{mode==='3d'&&sku?<SceneBoundary key={sku}><Suspense fallback={<p>Đang khởi tạo văn phòng 3D…</p>}><Canvas activeProduct={{sku}} reduceMotion={reduced} eyeStyle={eyeStyle} finishPreset={finish} onChangeEyeStyle={setEyeStyle} onChangeFinishPreset={setFinish} onSelectDepartment={navigate}/></Suspense></SceneBoundary>:<img src="assets/aistudio/image_bff76a11.png" alt="Ảnh concept toàn cảnh văn phòng BIS; chọn phòng ban ở bên dưới"/>}</div>
    <div className="bis-departments">{departments.map(([id,name,role])=><button key={id} onClick={()=>navigate(id)}><AgentRobotAvatar department={id} size="sm" isActive={false} reduceMotion={reduced}/><span><strong>{name}</strong><small>{role}</small></span><span aria-hidden="true">↗</span></button>)}</div>
  </section>;
}

