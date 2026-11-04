import React from 'react';

export class SceneBoundary extends React.Component<{children:React.ReactNode},{failed:boolean}> {
  state={failed:false};
  static getDerivedStateFromError(){return {failed:true};}
  render(){
    if(this.state.failed)return <section className="rounded-2xl border border-[#685043] p-4 bg-[#211813]">
      <img src="assets/aistudio/image_bff76a11.png" alt="Ảnh concept phòng điều hành BIS — không phải cảnh WebGL đang chạy" style={{width:'100%',height:'auto'}}/>
      <p role="alert">Không khởi tạo được cảnh WebGL trên trình duyệt này. Đang hiển thị ảnh concept. Bạn có thể chọn chế độ phòng 3D tĩnh hoặc danh sách tác vụ.</p>
    </section>;
    return this.props.children;
  }
}
