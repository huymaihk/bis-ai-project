"""Authenticated Streamlit controls for persistent memory."""
import json
import time
import uuid
from persistent_memory import sync_configured


def maintain_memory(store, force=False):
    import streamlit as st
    store.refresh_sources()
    count = len(store.events())
    last = st.session_state.get("_memory_sync", {})
    if force or last.get("count") != count or time.time() - last.get("at", 0) > 120:
        result = sync_configured(store)
        st.session_state["_memory_sync"] = dict(at=time.time(), count=len(store.events()), result=result)
    return st.session_state.get("_memory_sync", {}).get("result", {"state": "local"})


def render_memory_panel(store):
    import streamlit as st
    st.subheader("Bộ nhớ dài hạn & lịch sử tương tác")
    st.caption("Bộ nhớ chung của dự án BIS. Bản sửa giữ lại lịch sử; hội thoại được nạp lại khi mở phiên mới.")
    result = maintain_memory(store)
    if result.get("state") == "synced":
        st.success(f"Đã đồng bộ Google Sheets • nhận {result['received']} • gửi {result['sent']} sự kiện")
    else:
        st.warning(result.get("detail", "Có sự kiện đồng bộ không hợp lệ, cần kiểm tra."))
    if store.read_errors:
        st.error(f"{len(store.read_errors)} file bộ nhớ không đọc được. Bản gốc vẫn được giữ.")
    if st.button("Đồng bộ ngay", key="memory_sync_now"):
        maintain_memory(store, force=True)
        st.rerun()

    query = st.text_input("Tìm kiến thức / nội dung lịch sử", key="memory_query")
    rows = store.current()
    visible = [r for r in rows if not query or query.casefold() in
               (r["key"] + " ".join(e["content"] for e in r["heads"])).casefold()]
    if visible:
        keys = [r["key"] for r in visible]
        key = st.selectbox("Mục kiến thức", keys, key="memory_selected")
        row = next(r for r in visible if r["key"] == key)
        ids = [e["id"] for e in row["heads"]]
        if row["conflict"]:
            st.warning("Có nhiều bản sửa đồng thời. Xem các bản và nhập nội dung thống nhất.")
        for e in row["heads"]:
            st.caption(f"Nguồn: {e['source']} • {e['created_at']}")
            st.text(e["content"])
        version_key = "_".join(ids)
        with st.form("memory_edit_" + version_key):
            edited = st.text_area("Nội dung đã hiệu chỉnh", row["heads"][-1]["content"],
                                  height=150, max_chars=20000)
            reason = st.text_input("Lý do sửa", max_chars=250)
            withdraw = st.checkbox("Thu hồi mục này khỏi ngữ cảnh AI (vẫn giữ lịch sử)")
            submitted = st.form_submit_button("Lưu bản hiệu chỉnh")
        if submitted:
            try:
                store.revise(key, edited, expected=ids, deleted=withdraw,
                             kind="correction", source="Người dùng: " + reason)
                maintain_memory(store, force=True)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        with st.expander("Các phiên bản của mục này"):
            for e in reversed([e for e in store.events() if e["key"] == key]):
                st.text(f"{e['created_at']} | {e['actor']} | {e['source']}\n{e['content']}")
    with st.form("memory_add_note"):
        title = st.text_input("Tên kiến thức / quyết định mới", max_chars=200)
        content = st.text_area("Nội dung cần AI ghi nhớ lâu dài", max_chars=20000)
        add = st.form_submit_button("Ghi nhớ")
    if add and title.strip() and content.strip():
        store.revise("note:" + title.strip(), content, source="Người dùng xác nhận")
        maintain_memory(store, force=True)
        st.rerun()
    with st.expander("Lịch sử tương tác (200 tin gần nhất; bản xuất chứa toàn bộ)"):
        messages = [e for e in store.events() if e["kind"] == "message"
                    and (not query or query.casefold() in e["content"].casefold())]
        for e in messages[-200:]:
            st.text(f"{e['created_at']} | {e['session']} | {e['actor']}\n{e['content']}")
    st.download_button("Tải bộ nhớ hiện hành cho Codex / Antigravity", store.export_markdown(),
                       "BIS_MEMORY_CURRENT.md", mime="text/markdown")
    st.download_button("Sao lưu toàn bộ lịch sử (JSON)", json.dumps(store.events(), ensure_ascii=False, indent=2),
                       "BIS_MEMORY_EVENTS.json", mime="application/json")
    uploaded = st.file_uploader("Khôi phục / hợp nhất bản sao lưu JSON", type=["json"], key="memory_restore")
    if uploaded is not None and st.button("Hợp nhất bản sao lưu", key="memory_merge"):
        try:
            if uploaded.size > 25 * 1024 * 1024:
                raise ValueError("Giới hạn bản sao lưu: 25 MB.")
            events = json.load(uploaded)
            if not isinstance(events, list):
                raise ValueError("Cần danh sách sự kiện.")
            for e in events:
                store.validate(e)
            for e in events:
                store.import_event(e)
            maintain_memory(store, force=True)
            st.rerun()
        except (ValueError, KeyError, TypeError) as exc:
            st.error("Không thể nhập bản sao lưu: " + str(exc))

