"""Read-only image candidates on pages containing an exact SKU."""
import re
import hashlib
import io
import zipfile
import pymupdf

def candidates(pdf_path, sku):
    sku = str(sku).strip()
    if not sku:
        raise ValueError("SKU không được trống")
    pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(sku) + r"(?![A-Za-z0-9])", re.I)
    result = []
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            if not pattern.search(page.get_text()):
                continue
            seen = set()
            for info in page.get_image_info(xrefs=True):
                xref = info.get("xref", 0)
                if not xref or xref in seen:
                    continue
                seen.add(xref)
                data = doc.extract_image(xref)
                smask = next((x[1] for x in page.get_images(full=True) if x[0]==xref), 0)
                if smask:
                    pix = pymupdf.Pixmap(pymupdf.Pixmap(doc,xref), pymupdf.Pixmap(doc,smask))
                    data.update(image=pix.tobytes("png"),ext="png")

                result.append(dict(page=page.number+1, xref=xref, bbox=list(info["bbox"]),
                    width=data["width"], height=data["height"], ext=data["ext"],
                    source_file=str(pdf_path), image_bytes=data["image"], sha256=hashlib.sha256(data["image"]).hexdigest(),
                    status="NEEDS_REVIEW"))
    return result

def archive(items):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        for i, item in enumerate(items):
            z.writestr(f"page_{item['page']}_image_{i+1}.{item['ext']}", item["image_bytes"])
        import json
        z.writestr("provenance.json", json.dumps(
            [{k:v for k,v in item.items() if k!="image_bytes"} for item in items],ensure_ascii=False,indent=2))
    return output.getvalue()

def render_picker(media_agent, sku, pdf_path):
    import streamlit as st
    with st.expander("Ảnh trên các trang PDF chứa đúng SKU", expanded=False):
        st.caption("Ảnh ứng viên cần bạn đối chiếu. Cùng trang chưa chứng minh cùng sản phẩm.")
        if st.button("Tìm ảnh theo SKU", key=f"pdf_find_{sku}"):
            try:
                st.session_state[f"pdf_candidates_{sku}"] = candidates(pdf_path, sku)
            except Exception as exc:
                st.error(f"Không đọc được PDF: {type(exc).__name__}")
        items = st.session_state.get(f"pdf_candidates_{sku}", [])
        if items:
            st.download_button("Tải toàn bộ ảnh ứng viên ZIP", archive(items),
                "pdf_candidates.zip", key=f"pdf_zip_{sku}")
        for i, item in enumerate(items):
            st.image(item["image_bytes"], width=240,
                caption=f"Trang {item['page']} • {item['width']} × {item['height']} • cần đối chiếu")
            st.download_button("Tải ảnh gốc", item["image_bytes"],
                f"page_{item['page']}_{i+1}.{item['ext']}", key=f"pdf_download_{sku}_{i}")
            if st.button("Chọn làm ảnh nguồn", key=f"pdf_choose_{sku}_{i}"):
                media_agent.register_user_image(sku, item["image_bytes"], f"selected.{item['ext']}")
                st.success("Đã lưu ảnh bạn chọn làm nguồn. Chưa duyệt ảnh thành phẩm.")


        with st.expander("Xem trang / cắt vùng ảnh (PDF scan hoặc ảnh vector)"):
            page_number=st.number_input("Trang PDF",min_value=1,value=1,key=f"crop_page_{sku}")
            left,right=st.columns(2)
            x0=left.number_input("Trái (%)",min_value=0,max_value=99,value=0,key=f"crop_x0_{sku}")
            y0=left.number_input("Trên (%)",min_value=0,max_value=99,value=0,key=f"crop_y0_{sku}")
            x1=right.number_input("Phải (%)",min_value=1,max_value=100,value=100,key=f"crop_x1_{sku}")
            y1=right.number_input("Dưới (%)",min_value=1,max_value=100,value=100,key=f"crop_y1_{sku}")
            if st.button("Xem toàn trang",key=f"crop_full_{sku}"):
                try:
                    data=render_region(pdf_path,int(page_number))
                    st.image(data,caption="Trang nguồn để đối chiếu vị trí SKU")
                    st.download_button("Tải trang xem trước",data,"source_page.png",key=f"full_dl_{sku}")
                except Exception as exc:
                    st.error(str(exc))
            if st.button("Tạo ảnh từ vùng đã chọn",key=f"crop_render_{sku}"):
                try:
                    data=render_region(pdf_path,int(page_number),(x0,y0,x1,y1))
                    st.session_state[f"crop_data_{sku}"]=data
                except Exception as exc:
                    st.error(str(exc))
            crop=st.session_state.get(f"crop_data_{sku}")
            if crop:
                st.image(crop,caption="Ảnh render từ vùng PDF, cần xác nhận đúng vật thể")
                st.download_button("Tải vùng ảnh",crop,"pdf_region.png",key=f"crop_dl_{sku}")
                if st.button("Chọn vùng này làm nguồn",key=f"crop_save_{sku}"):
                    media_agent.register_user_image(sku,crop,"region.png")
                    st.success("Đã lưu vùng bạn chọn làm ảnh nguồn.")


def render_region(pdf_path,page_number,region=(0,0,100,100)):
    x0,y0,x1,y1=region
    if not (0<=x0<x1<=100 and 0<=y0<y1<=100):
        raise ValueError("Vùng cắt không hợp lệ")
    with pymupdf.open(pdf_path) as doc:
        if not 1<=page_number<=len(doc):
            raise ValueError("Trang ngoài tài liệu")
        page=doc[page_number-1]
        w,h=page.rect.width,page.rect.height
        rect=pymupdf.Rect(w*x0/100,h*y0/100,w*x1/100,h*y1/100)
        return page.get_pixmap(matrix=pymupdf.Matrix(2,2),clip=rect,alpha=False).tobytes("png")
