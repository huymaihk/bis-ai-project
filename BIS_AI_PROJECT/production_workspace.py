"""BIS production workspace: explicit sources, editable drafts and verified outputs."""
import io
import json
from pathlib import Path
import hashlib
import streamlit as st
import streamlit.components.v1 as components
from persistent_memory import MemoryStore, atomic_json
from product_quality import render_product, validate_product, match_product, fingerprint, seo_draft
from safe_publish import source_text, publish_batch
from quality_jobs import JobRunner
from media_quality import studio_draft, download_image, rank_candidates
from pdf_candidates import render_picker
from memory_ui import render_memory_panel

def render_workspace(root,technical,media,knowledge,translator,memory,active_step=None):
    root=Path(root)
    from technical_runtime import ensure_current_technical
    technical=ensure_current_technical(technical, root)
    runner=JobRunner(root)
    folder=memory.root/"product_drafts"
    folder.mkdir(exist_ok=True)
    from workspace_design import apply_theme, render_overview, product_context
    st.sidebar.markdown('<div class="bis-brand">BIS<span> / </span>AI</div>',unsafe_allow_html=True)
    st.sidebar.caption("TEXTILE · PRODUCT WORKSPACE")
    light=st.sidebar.toggle("Giao diện sáng",value=False,key="bis_light_theme")
    apply_theme(light)
    overview=st.empty()
    st.sidebar.markdown('<div class="bis-side-label">KHÔNG GIAN LÀM VIỆC</div>',unsafe_allow_html=True)
    labels=["1 · Nguồn & dữ liệu","2 · Nội dung","3 · Ảnh","4 · Duyệt & xuất","5 · Tri thức & lịch sử"]
    tabs=st.tabs(labels) if active_step is None else [st.container() for _ in labels]
    if active_step is not None:
        st.subheader(labels[active_step])
    source_dir=root/"Google_Drive_Storage"/"1_Catalogues"
    source_dir.mkdir(exist_ok=True)
    sources=[root/"catalogue_sample.pdf"] if (root/"catalogue_sample.pdf").exists() else []
    sources+=list(source_dir.rglob("*.pdf"))
    if active_step is None or active_step == 0:
        with tabs[0]:
            st.markdown('### 1 · Kho tài liệu Catalogue')
            st.caption('Quét thư mục 1_Catalogues trên máy đang chạy BIS. Web Cloud không tự đọc ổ G của máy cá nhân; cần tải PDF lên hoặc đồng bộ file lên máy chủ.')
            if st.button('Quét thư mục Catalogue',key='q_scan_catalogues'):
                st.session_state['q_catalogue_files'] = sorted(str(p.relative_to(root)) for p in source_dir.rglob('*') if p.is_file() and p.suffix.lower()=='.pdf')
            if 'q_catalogue_files' in st.session_state:
                sources=[root/p for p in st.session_state['q_catalogue_files'] if (root/p).is_file()]
            ledger_path=memory.root/'catalogue_analysis.json'
            try:
                analysis=json.loads(ledger_path.read_text(encoding='utf-8'))
            except (OSError,ValueError):
                analysis={}
            upload=st.file_uploader("Thêm catalogue PDF",type=["pdf"],key="q_source_upload")
            if upload and st.button("Lưu tài liệu nguồn"):
                import pymupdf
                data=upload.getvalue()
                if len(data)>50*1024*1024:
                    st.error("PDF tối đa 50 MB")
                else:
                    try:
                        with pymupdf.open(stream=data,filetype="pdf") as d:
                            if d.needs_pass:
                                raise ValueError("PDF cần mật khẩu")
                        target=source_dir/(hashlib.sha256(data).hexdigest()[:12]+"_"+Path(upload.name).name)
                        target.write_bytes(data)
                        st.session_state['q_catalogue_files']=sorted(str(p.relative_to(root)) for p in source_dir.rglob('*') if p.is_file() and p.suffix.lower()=='.pdf')
                        st.rerun()
                    except Exception as exc:
                        st.error("Không đọc được tài liệu: "+type(exc).__name__)
            st.caption(f'{len(sources)} tài liệu · 🟢 Đã phân tích · ⚪ Chưa phân tích hoặc đã thay đổi')
            if not sources:
                st.info('Chưa có tài liệu. Quét thư mục hoặc tải một PDF lên để bắt đầu.')
            st.markdown('### 2 · Chọn tài liệu và phân tích')
            chosen=st.selectbox("Tài liệu đang làm việc",sources,
                                format_func=lambda p:('🟢 ' if analysis.get(str(p.relative_to(root)),{}).get('state')=='COMPLETED' and analysis.get(str(p.relative_to(root)),{}).get('sha256')==hashlib.sha256(p.read_bytes()).hexdigest() else '⚪ ')+p.relative_to(root).as_posix(),key="q_pdf") if sources else None
            if chosen:
                file_hash=hashlib.sha256(chosen.read_bytes()).hexdigest()
                record=analysis.get(str(chosen.relative_to(root)),{})
                done=record.get('sha256')==file_hash and record.get('state')=='COMPLETED'
                if done:
                    st.success('Đã phân tích tài liệu này thành công.')
                elif record:
                    st.warning('Tài liệu đã thay đổi hoặc lần phân tích trước chưa hoàn tất.')
                confirm=st.checkbox('Bạn có muốn phân tích lại tài liệu này không?',key='q_reanalyse_'+file_hash) if done else False
                if st.button('Phân tích toàn bộ tài liệu',disabled=done and not confirm,key='q_analyse_document'):
                    import pymupdf
                    key=str(chosen.relative_to(root))
                    analysis[key]={'sha256':file_hash,'state':'RUNNING'}
                    atomic_json(ledger_path,analysis)
                    try:
                        total_rows=0
                        needs_review=False
                        with pymupdf.open(chosen) as document:
                            if document.needs_pass:
                                raise ValueError('PDF cần mật khẩu')
                            progress=st.progress(0)
                            for index in range(len(document)):
                                rows=runner.run('catalogue_page',{'file':key,'sha256':file_hash,'page':index+1},
                                    lambda i=index: technical.extract_page(document[i].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).tobytes('jpeg'),i+1,len(document),page_text=document[i].get_text()))
                                if not isinstance(rows,list) or not rows:
                                    raise ValueError(f'Trang {index+1} chưa có kết quả xác minh; dùng trích từng trang để kiểm tra.')
                                needs_review = needs_review or any(row.get('analysis_model') == 'PyMuPDF-LocalFallback' for row in rows)
                                for row in rows:
                                    from media_quality import safe_name
                                    row.update(source_file=key,source_page=index+1,status='EXTRACTED_UNVERIFIED')
                                    row['custom_html']=render_product(row)
                                    target=folder/(safe_name(row['sku'])+'.json')
                                    if not target.exists():
                                        atomic_json(target,row)
                                    total_rows+=1
                                progress.progress((index+1)/len(document))
                        analysis[key]={'sha256':file_hash,'state':'NEEDS_REVIEW' if needs_review else 'COMPLETED','products':total_rows}
                        atomic_json(ledger_path,analysis)
                        memory.append('update',f'Đã phân tích {key}: {total_rows} kết quả; dữ liệu cần nghiệm thu.',source='catalogue_analysis')
                        st.rerun()
                    except Exception as exc:
                        analysis[key]={'sha256':file_hash,'state':'FAILED'}
                        atomic_json(ledger_path,analysis)
                        st.error('Phân tích chưa hoàn tất: '+str(exc))
            st.markdown("### 3 · Kiểm tra từng trang")
            st.caption("Dùng khi cần xem nguồn hoặc thử trích một trang trước khi phân tích toàn bộ.")
            page=st.number_input("Trang cần trích xuất",min_value=1,value=1,step=1,key="q_source_page")
            if chosen:
                if st.button("Xem trang",key="q_render_page"):
                    try:
                        import pymupdf
                        with pymupdf.open(chosen) as d:
                            st.image(d[int(page)-1].get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).tobytes("png"))
                    except Exception as exc:
                        st.error("Không xem được trang: "+type(exc).__name__)
                if st.button("Trích dữ liệu từ trang này",key="q_extract"):
                    try:
                        import pymupdf
                        def extract():
                            with pymupdf.open(chosen) as d:
                                if not 1<=page<=len(d):
                                    raise ValueError("Số trang vượt tài liệu")
                                page_item=d[int(page)-1]
                                return technical.extract_page(page_item.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).tobytes("jpeg"),int(page),len(d),page_text=page_item.get_text())
                        rows=runner.run("technical_extract",{"pdf":str(chosen),"page":page},extract)
                        if not rows:
                            st.warning("Chưa có sản phẩm trích xuất. Kiểm tra nội dung trang và trạng thái API.")
                        for row in rows:
                            from media_quality import safe_name
                            sku=safe_name(row["sku"])
                            row.update(source_file=str(chosen.relative_to(root)),status="EXTRACTED_UNVERIFIED")
                            row["custom_html"]=render_product(row)
                            target=folder/(sku+".json")
                            if target.exists():
                                st.warning(f"{sku} đã có bản làm việc; giữ bản hiện tại, không ghi đè.")
                            else:
                                atomic_json(target,row)
                        if rows:
                            st.rerun()
                    except Exception as exc:
                        st.error("Trích xuất chưa hoàn tất: "+type(exc).__name__)
    # Imported cached products are reference drafts; saving never overwrites source cache.
    products={}
    cache=root/"extracted_products_cache.json"
    if cache.exists():
        try:
            products={str(p["sku"]):p for p in json.loads(cache.read_text(encoding="utf-8"))
                      if p.get("sku")}
        except (ValueError,TypeError,KeyError):
            st.warning("Không đọc được cache sản phẩm; bản gốc được giữ.")
    if not products and (root/'catalog_master_data.py').exists():
        from catalog_master_data import CATALOG_MASTER
        products = {sku:dict(sku=sku,product_name=item.get('vi',''),product_name_en=item.get('en',''),
                            description=item.get('desc',''),source_file='catalogue_sample.pdf',
                            source_page=int(item.get('page') or 1),status='EXTRACTED_UNVERIFIED',evidence_quote='')
                    for sku,item in CATALOG_MASTER.items()}
    for path in folder.glob("*.json"):
        try:
            record=json.loads(path.read_text(encoding="utf-8"))
            products[str(record["sku"])]=record
        except (ValueError,KeyError):
            continue
    if not products:
        st.info("Nhập catalogue và trích một trang để bắt đầu.")
    selection=st.sidebar.selectbox("Sản phẩm đang làm việc",list(products),key="q_sku") if products else None
    render_overview(overview,products,sources,media.manifest)
    with st.sidebar:
        st.divider()
        st.caption("QUY TRÌNH PHỐI HỢP")
        st.markdown("**01** Technical · Tài liệu & dữ liệu\n\n**02** Marketing · Nội dung & SEO\n\n**03** Studio · Hình ảnh sản phẩm\n\n**04** Operations · Duyệt & xuất\n\n**05** Knowledge · Tri thức & lịch sử")
        st.divider()
        st.caption("Bộ nhớ lưu cục bộ. Kiểm tra trạng thái đồng bộ trong mục Tri thức & lịch sử.")
    product=dict(products[selection]) if selection else None

    if active_step is None or active_step == 1:
        with tabs[1]:
            product_context(product)
            if product:
                st.subheader("Biên tập dữ liệu có chứng cứ")
                # A form version tied to content prevents stale widget values after selecting another SKU.
                version=fingerprint(product)[:12]
                with st.form("q_edit_"+version):
                    vi=st.text_input("Tên tiếng Việt",product.get("product_name") or "")
                    en=st.text_input("Tên tiếng Anh",product.get("product_name_en") or "")
                    vendor=st.text_input("Hãng theo tài liệu",product.get("brand") or product.get("brand_evidence") or "")
                    description=st.text_area("Mô tả tiếng Việt",product.get("description") or "",height=160)
                    quote=st.text_area("Trích dẫn nguyên văn",product.get("evidence_quote") or "")
                    origin=st.text_input("Đường dẫn PDF nguồn trong dự án",product.get("source_file") or "catalogue_sample.pdf")
                    sourcepage=st.number_input("Trang chứng cứ",min_value=1,value=max(1,int(product.get("source_page") or 1)))
                    specs=st.text_area("Thông số đã xác minh (JSON)",json.dumps(product.get("specifications") or {},ensure_ascii=False))
                    hl=product.get("highlights") or []
                    highlights=st.text_area("Đặc điểm có chứng cứ (mỗi dòng một ý)","\n".join(hl) if isinstance(hl,list) else str(hl))
                    save=st.form_submit_button("Lưu và kiểm tra")
                if save:
                    try:
                        from media_quality import safe_name
                        data=json.loads(specs)
                        if not isinstance(data,dict):
                            raise ValueError("Thông số cần là JSON object")
                        updated=dict(product,product_name=vi,product_name_en=en,brand=vendor,description=description,
                                     evidence_quote=quote,source_file=origin,source_page=int(sourcepage),
                                     specifications=data,highlights=highlights.splitlines(),status="EXTRACTED_UNVERIFIED")
                        updated.pop("_review_hash",None)
                        updated["custom_html"]=render_product(updated)
                        memory.revise("product:"+selection,json.dumps(updated,ensure_ascii=False)[:18000],
                                      kind="correction",source="Người dùng biên tập; cần kiểm tra chứng cứ")
                        atomic_json(folder/(safe_name(selection)+".json"),updated)
                        st.rerun()
                    except (ValueError,TypeError) as exc:
                        st.error(str(exc))
                try:
                    report=validate_product(product,source_text(root,product))
                except Exception:
                    report=validate_product(product,None)
                if report["passed"]:
                    st.success("Đã qua kiểm tra cấu trúc và trích dẫn. Cần bạn duyệt tính đúng của thông số/mô tả.")
                else:
                    for err in report["errors"]:
                        st.warning(err)
                components.html(render_product(product),height=550,scrolling=True)
                seo=seo_draft(product)
                st.subheader("SEO song ngữ")
                meta=st.text_area("Meta description · mục tiêu 140–160 ký tự",
                                  product.get("meta_description") or seo["meta_description"],key="q_meta_"+selection)
                st.caption(f"{len(meta)} ký tự")
                if st.button("Lưu SEO",key="q_save_seo"):
                    from media_quality import safe_name
                    product.update(meta_description=meta,url_slug=seo["url_slug"],status="EXTRACTED_UNVERIFIED")
                    product.pop("_review_hash",None)
                    atomic_json(folder/(safe_name(selection)+".json"),product)
                    st.rerun()

    if active_step is None or active_step == 2:
        with tabs[2]:
            product_context(product)
            if product:
                st.subheader("Chọn ảnh đúng sản phẩm")
                pdf=root/(product.get("source_file") or "catalogue_sample.pdf")
                render_picker(media,selection,pdf)
                upload=st.file_uploader("Ảnh nguồn bạn chọn",type=["png","jpg","jpeg","webp"],key="q_image_upload")
                if upload and st.button("Lưu ảnh nguồn",key="q_image_save"):
                    try:
                        media.register_user_image(selection,upload.getvalue(),upload.name)
                        st.success("Đã lưu nguồn; cần tạo/nhập và duyệt ảnh thành phẩm.")
                    except Exception as exc:
                        st.error(str(exc))
                query=st.text_input("Tìm ảnh web",f'{product.get("brand") or "AATCC"} "{selection}" {product.get("product_name_en") or ""}',key="q_query_"+selection)
                if st.button("Tìm ảnh ứng viên",key="q_web_search"):
                    try:
                        rows=runner.run("search_images",{"query":query},lambda:media.search_web_images(query,8))
                        st.session_state["q_web_"+selection]=rank_candidates(rows,selection,product.get("product_name_en"),product.get("brand") or "")
                    except Exception as exc:
                        st.error(type(exc).__name__)
                for i,row in enumerate(st.session_state.get("q_web_"+selection,[])):
                    st.write(row.get("title") or "Ảnh ứng viên")
                    st.caption("Có mã trong metadata" if row["sku_evidence"] else "Chưa có chứng cứ mã SKU")
                    st.link_button("Xem nguồn",row.get("page_url") or row["image_url"])
                    # Fetch pixels only on explicit click, never load trackers as remote <img>.
                    if st.button("Tải ảnh để đối chiếu",key=f"q_web_load_{selection}_{i}"):
                        try:
                            st.session_state[f"q_web_bytes_{selection}_{i}"]=download_image(row["image_url"])
                        except Exception as exc:
                            st.error(type(exc).__name__)
                    data=st.session_state.get(f"q_web_bytes_{selection}_{i}")
                    if data:
                        st.image(data,width=260)
                        if st.button("Chọn ảnh này làm nguồn",key=f"q_web_choose_{selection}_{i}"):
                            media.register_user_image(selection,data,"web.png")
                            memory.append("update",json.dumps({"sku":selection,"source_url":row["image_url"],"state":"USER_SELECTED"},ensure_ascii=False),source="media_selection")
                            st.success("Đã lưu lựa chọn; chưa xác nhận chất lượng thành phẩm.")
                st.subheader("Ảnh studio và nghiệm thu")
                source=media.get_product_image_for_sku(selection)
                selected_heads=memory.heads('image-source:'+selection)
                if len(selected_heads)==1 and not selected_heads[0]['deleted']:
                    try:
                        selected_data=json.loads(selected_heads[0]['content'])
                        selected_path=(root/selected_data['path']).resolve()
                        if selected_data.get('sku')==selection and selected_path.is_relative_to((root/'Google_Drive_Storage'/'4_Product_Images').resolve()) and selected_path.is_file():
                            source=selected_path
                    except (ValueError,KeyError,TypeError):
                        pass
                if source:
                    st.image(str(source),width=260,caption="Ảnh nguồn hiện tại")
                backgrounds=media.get_backgrounds()
                bg=st.selectbox("Nền studio",backgrounds,format_func=lambda p:p.name,key="q_bg") if backgrounds else None
                remove=st.checkbox("Tách nền trắng bên ngoài (kiểm tra lại viền và vật thể trắng)",key="q_remove")
                if source and bg and st.button("Tạo bản ghép giữ chi tiết gốc"):
                    try:
                        target=media.preview_dir/(selection+"_preview.png")
                        result=runner.run("studio_draft",{"source":str(source),"bg":str(bg)},lambda:studio_draft(source,bg,target,remove_white=remove))
                        media.manifest[selection]=dict(result,sku=selection,preview_image=str(target))
                        media._save_manifest()
                        st.success("Đã tạo bản nháp. So với mẫu trước khi duyệt.")
                    except Exception as exc:
                        st.error(str(exc))
                if source and bg and st.button("Chỉnh ảnh bằng Gemini theo ảnh nguồn",key="q_ai_image"):
                    try:
                        from gemini_studio import edit_studio
                        target=media.preview_dir/(selection+"_preview.png")
                        result=runner.run("gemini_studio",{"sku":selection},lambda:edit_studio(source,bg,target,selection))
                        media.manifest[selection]=dict(result,sku=selection)
                        media._save_manifest()
                        st.success("Đã có bản AI chờ duyệt; đối chiếu chi tiết với ảnh nguồn.")
                    except Exception as exc:
                        st.error("Chưa tạo được ảnh AI: "+type(exc).__name__+". Kiểm tra quyền API, model và quota.")
                final=st.file_uploader("Nhập ảnh thành phẩm từ ChatGPT/Gemini web · 1254×1254",type=["png","jpg","jpeg"],key="q_final_upload")
                if final and st.button("Lưu bản thành phẩm chờ duyệt"):
                    try:
                        media.register_final_composite(selection,final.getvalue())
                    except Exception as exc:
                        st.error(str(exc))
                benchmarks=[p for p in media.final_dir.iterdir() if p.suffix.lower() in {".png",".jpg",".jpeg"} and "_approved_" not in p.name]
                benchmark=st.selectbox("Ảnh mẫu đối chiếu",benchmarks,format_func=lambda p:p.name) if benchmarks else None
                entry=media.manifest.get(selection,{})
                preview=entry.get("preview_image")
                if preview and Path(preview).exists():
                    c1,c2=st.columns(2)
                    c1.image(preview,caption="Bản chờ duyệt")
                    if benchmark:
                        c2.image(str(benchmark),caption="Mẫu tham chiếu · khác SKU cần đối chiếu đúng vật thể")
                    confirm=st.checkbox("Đã kiểm tra đúng SKU, chữ/logo, hình khối, độ nét và bóng đổ",key="q_image_confirm_"+selection)
                    if st.button("Duyệt ảnh thành phẩm",disabled=not confirm):
                        if media.approve_image(selection):
                            st.success("Đã duyệt đúng phiên bản ảnh.")
                        else:
                            st.error("Ảnh chưa hợp lệ.")
                if entry.get("status")=="APPROVED":
                    st.success("Có ảnh đã duyệt; thay ảnh thành phẩm cần duyệt lại.")

    if active_step is None or active_step == 3:
        with tabs[3]:
            product_context(product)
            if product:
                st.subheader("Duyệt và xuất bản nháp")
                storefile=root/"bistextile_existing_products.json"
                try:
                    snapshot=json.loads(storefile.read_text(encoding="utf-8"))
                except (ValueError,OSError):
                    snapshot=[]
                match=match_product(product,snapshot)
                st.write("Đối soát bản lưu:",match["state"],"—",match["reason"])
                st.caption("Cổng đăng sẽ quét lại toàn bộ Haravan trực tiếp trước mỗi lần tạo.")
                reviewed=st.checkbox("Đã đối chiếu dữ liệu với nguồn và ảnh đã duyệt",key="q_product_confirm_"+selection)
                if st.button("Duyệt phiên bản sản phẩm",disabled=not reviewed):
                    try:
                        from media_quality import safe_name
                        checked=validate_product(product,source_text(root,product))
                        if not checked["passed"]:
                            raise ValueError("; ".join(checked["errors"]))
                        if not 140<=len(product.get("meta_description") or "")<=160:
                            raise ValueError("Cần chỉnh SEO về 140–160 ký tự")
                        product["custom_html"]=render_product(product)
                        product["status"]="APPROVED"
                        product["_review_hash"]=fingerprint({k:v for k,v in product.items() if not k.startswith("_")})
                        atomic_json(folder/(safe_name(selection)+".json"),product)
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
                if st.button("Tạo bản nháp trên Haravan",disabled=product.get("status")!="APPROVED"):
                    result=runner.run("publish_draft",{"sku":selection},lambda:publish_batch([product],root))
                    st.json(result)
                st.download_button("Tải dữ liệu sản phẩm JSON",json.dumps(product,ensure_ascii=False,indent=2),
                                   "product.json",mime="application/json")
                st.download_button("Tải HTML",render_product(product),"product.html",mime="text/html")

    if active_step is None or active_step == 4:
        with tabs[4]:
            st.subheader("Tri thức và bộ nhớ")
            with st.expander("Thư viện tài liệu",expanded=False):
                if knowledge:
                    st.dataframe(knowledge.manifest,use_container_width=True)
                    st.caption("Danh mục tài liệu chưa đồng nghĩa nội dung đã được xác minh.")
            with st.expander("Tra cứu nội dung tài liệu",expanded=False):
                knowledge_docs=list((root/"Google_Drive_Storage"/"2_Manuals_Standards").rglob("*.pdf"))
                indexed=st.selectbox("Lập chỉ mục PDF",knowledge_docs,format_func=lambda p:p.name,key="q_index_pdf") if knowledge_docs else None
                if indexed and st.button("Đọc văn bản và lưu theo trang"):
                    try:
                        from knowledge_index import index_pdf
                        st.json(runner.run("knowledge_index",{"file":str(indexed)},lambda:index_pdf(root,indexed,max_pages=100)))
                    except Exception as exc:
                        st.error(type(exc).__name__)
                question=st.text_input("Tra cứu kiến thức",key="q_knowledge_query")
                if question:
                    st.text(memory.context(question,max_chars=9000))
            with st.expander("Dịch tài liệu",expanded=False):
                docs=list((root/"Google_Drive_Storage"/"2_Manuals_Standards").rglob("*.pdf"))
                doc=st.selectbox("Tài liệu cần dịch",docs,format_func=lambda p:p.name) if docs else None
                count=st.number_input("Số trang thử trước",min_value=1,max_value=5,value=1)
                if doc and translator and st.button("Dịch bản thử"):
                    try:
                        out=runner.run("translate",{"file":str(doc),"max_pages":count},
                                       lambda:translator.translate_document(doc,max_pages=count))
                        st.download_button("Tải bản dịch để kiểm tra bố cục",Path(out).read_bytes(),Path(out).name)
                        st.warning("Bản dịch cần kiểm tra thuật ngữ và bố cục; chưa chứng nhận giữ nguyên định dạng.")
                    except Exception as exc:
                        st.error("Dịch chưa hoàn tất: "+type(exc).__name__)
            with st.expander("Nhật ký tác vụ"):
                st.dataframe(runner.list_jobs(),use_container_width=True)
            render_memory_panel(memory)
