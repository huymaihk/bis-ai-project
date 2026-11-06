import {useEffect, useState} from 'react';
import {bisFetch, ProtectedImage, AssetLink} from '../streamlitTransport';

type Catalogue = {id: string; name: string; path: string; sha256: string; size: number; state: string; completed_pages: number; pages:number; done_pages:number[]; changed:boolean};

async function request(path: string, body?: unknown) {
  const response = await bisFetch('/api/' + path, {
    method: body === undefined ? 'GET' : 'POST',
    credentials: 'same-origin',
    headers: {'Content-Type': 'application/json', 'X-BIS-Request': '1'},
    body: body === undefined ? undefined : JSON.stringify(body)
  });
  const result = await response.json();
  if (!response.ok) throw Error(typeof result.detail === 'string' ? result.detail : 'Không xử lý được yêu cầu');
  return result;
}

const states: Record<string, string> = {
  NEEDS_REVIEW: 'Cần đối chiếu kết quả với nguồn',
  PARTIAL: 'Đã phân tích một phần',
  NEW: 'Chưa phân tích',
  RUNNING: 'Chưa hoàn tất',
  FAILED: 'Cần kiểm tra lại',
  COMPLETED: 'Đã phân tích'
};

export default function CatalogueTechnical() {
  const [files, setFiles] = useState<Catalogue[]>([]);
  const [selected, setSelected] = useState(() => {try{return sessionStorage.getItem('bis:technical:file')||'';}catch{return '';}});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [scanned, setScanned] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [dialog, setDialog] = useState(false);
  const [progress, setProgress] = useState('');
  const [runProgress,setRunProgress]=useState<{done:number;total:number}|null>(null);
  const [detail, setDetail] = useState('');

  const [forceRefresh,setForceRefresh]=useState(false);
  const [mode, setMode] = useState('full');
  const [from, setFrom] = useState(1);
  const [to, setTo] = useState(1);
  const [resultVersion, setResultVersion] = useState(0);
  const [batchCursor, setBatchCursor] = useState<any>(null);
  const [results, setResults] = useState<any[]>([]);
  const [resultSku, setResultSku] = useState('');

  // Unassigned pool & batch extraction
  const [batchStart, setBatchStart] = useState(1);
  const [batchEnd, setBatchEnd] = useState(5);
  const [unassignedPool, setUnassignedPool] = useState<any[]>([]);
  const [selectedUnassigned, setSelectedUnassigned] = useState<Set<string>>(new Set());
  const [assignTargetSku, setAssignTargetSku] = useState('');
  const [cropPage, setCropPage] = useState(1);
  const [cropX0, setCropX0] = useState(0);
  const [cropY0, setCropY0] = useState(0);
  const [cropX1, setCropX1] = useState(100);
  const [cropY1, setCropY1] = useState(100);
  const [cropMsg, setCropMsg] = useState('');

  const result = results.find(r => r.sku === resultSku);
  const file = files.find(f => f.id === selected);

  async function scan(manual = false) {
    const data = await request(manual ? 'catalogues/scan' : 'catalogues', manual ? {} : undefined);
    setFiles(data.files);
    setDetail(data.detail);
    setScanned(true);
    setSelected(old => data.files.some((f: Catalogue) => f.id === old) ? old : '');
  }

  useEffect(() => {
    scan().catch(e => setError(e.message));
  }, []);

  useEffect(() => {
    let active=true;
    try {sessionStorage.setItem("bis:technical:file",selected);} catch {}
    setResults([]);
    setResultSku('');
    setUnassignedPool([]);
    setSelectedUnassigned(new Set());
    if (selected) {
      request('catalogues/' + selected + '/results')
        .then(d => {
          if (!active) return;
          setResults(d.products);
          let saved='';
          try {saved=sessionStorage.getItem('bis:technical:sku:'+selected)||'';} catch {}
          setResultSku(old => d.products.some((r:any)=>r.sku===old) ? old : d.products.some((r:any)=>r.sku===saved) ? saved : d.products[0]?.sku||'');
          setAssignTargetSku(old => d.products.some((r:any)=>r.sku===old) ? old : d.products[0]?.sku||'');
        })
        .catch(e => {if(active)setError(e.message);});
    }
    return () => {active=false;};
  }, [selected, resultVersion]);

  async function analyse(again = false, product?: any, resume = false) {
    if (!file) return;
    if (!again && (file.changed || (!resume && file.completed_pages > 0))) {
      setDialog(true);
      return;
    }
    setDialog(false);
    setBusy(true);
    setError('');
    setProgress('Chuẩn bị phân tích…');
    try {
      const run = await request(`catalogues/${file.id}/start`, {
        sha256: file.sha256,
        confirm: again,
        resume,
        force_refresh: forceRefresh || !!product,
        start_page: product ? Number(product.source_page) : mode === 'full' ? 1 : from,
        end_page: product ? Number(product.source_page) : mode === 'full' ? null : mode === 'single' ? from : to,
        sku: product?.sku || ''
      });
      const pending:number[]=run.pending_pages || [];
      setRunProgress({done:0,total:pending.length});
      if(!pending.length)setProgress('Phạm vi này không còn trang chưa phân tích.');
      for (const page of pending) {
        if(page !== pending[0]) {setProgress("Chờ 4 giây giữa các trang…"); await new Promise(resolve => setTimeout(resolve,4000));}
        setProgress(`Đang phân tích trang ${page}/${run.pages} · ${file.name}`);
        const pageResult = await request(`catalogues/${file.id}/page`, {run: run.run, page});
        setRunProgress({done:pageResult.run_done,total:run.run_total});
        setProgress(`Đã xử lý trang ${page} · ${pageResult.cache_hit ? 'Dùng kết quả đã lưu, không gọi AI' : pageResult.last_input_mode==='TEXT' ? 'Phân tích từ văn bản PDF' : 'Phân tích ảnh và văn bản PDF'}`);
        if (page === pending[pending.length-1]) {
          setProgress(
            ['COMPLETED', 'PARTIAL'].includes(pageResult.state)
              ? `Đã xử lý ${pageResult.completed_pages} trang · ${pageResult.products} kết quả. Dữ liệu cần được nghiệm thu.`
              : `Đã xử lý · ${pageResult.products} kết quả cần đối chiếu nguồn, chưa đánh dấu hoàn tất.`
          );
        }
      }
    } catch (e) {
      setError((e as Error).message);
      setProgress('Đã dừng; các trang thành công được giữ lại. Dùng Tiếp tục để xử lý trang còn thiếu.');
    } finally {
      await scan().catch(() => {});
      setBusy(false);
      setConfirm(false);
      setResultVersion(v => v + 1);
    }
  }

  async function extractBatch(cursor?: any) {
    if (!file) return;
    setBusy(true);
    setCropMsg('');
    try {
      const data = await request('technical/pdf-extract-batch', {
        asset_id: file.id,
        start_page: cursor?.page || batchStart,
        end_page: cursor?.page > batchEnd ? null : batchEnd,
        image_offset: cursor?.offset || 0,
        max_images: 40
      });
      setUnassignedPool(data.images || []);
      setSelectedUnassigned(new Set());
      setBatchCursor(data.next_page ? {page:data.next_page, offset:data.next_offset} : null);
      setCropMsg(`Đã trích ${data.images?.length || 0} ảnh từ trang ${data.start_page}..${data.end_page}. Các ảnh nằm trong Khu vực chưa gán SKU.`);
    } catch (e) {
      setCropMsg((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function renderCrop() {
    if (!file) return;
    setBusy(true);
    setCropMsg('');
    try {
      const res = await request('technical/pdf-render-region', {
        asset_id: file.id,
        page: cropPage,
        crop: [cropX0, cropY0, cropX1, cropY1]
      });
      setUnassignedPool(prev => [res, ...prev]);
      setCropMsg(`Đã kết xuất vùng trang ${cropPage} (%: ${cropX0}, ${cropY0}, ${cropX1}, ${cropY1}). Ảnh được thêm vào Khu vực chưa gán SKU.`);
    } catch (e) {
      setCropMsg((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function assignAndSaveUnassigned() {
    if (!assignTargetSku) {
      setCropMsg('Vui lòng chọn SKU đích để gán ảnh.');
      return;
    }
    if (selectedUnassigned.size === 0) {
      setCropMsg('Vui lòng chọn ít nhất 1 ảnh để gán SKU.');
      return;
    }
    setBusy(true);
    try {
      const ids = Array.from(selectedUnassigned);
      const res = await request(`products/${encodeURIComponent(assignTargetSku)}/raw-images/save`, {
        candidate_ids: ids,
        confirm: true
      });
      setCropMsg(`Đã lưu ${res.saved_count} ảnh thô cho SKU ${assignTargetSku} vào Google_Drive_Storage/4_Product_Images/raw/.`);
      // Remove saved from unassigned
      setUnassignedPool(prev => prev.filter(img => !selectedUnassigned.has(img.id)));
      setSelectedUnassigned(new Set());
    } catch (e) {
      setCropMsg((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="catalogue-technical">
      <section className="live-panel catalogue-hero">
        <small>TECHNICAL / TÀI LIỆU VÀ DỮ LIỆU</small>
        <h2>Từ tài liệu gốc.<br/>Đến sản phẩm chuẩn.</h2>
        <p>
          Bóc tách mặt hàng trong các trang catalogue được chọn: SKU, tên, mô tả và thông số có trong nguồn.
          Trích xuất và lưu ảnh thô theo SKU vào <code>Google_Drive_Storage/4_Product_Images/raw/</code>.
          Kết quả AI cần đối chiếu; phân tích xong không đồng nghĩa đã duyệt.
        </p>
        <div className="technical-steps">
          <span>01 · Quét thư mục</span>
          <span>02 · Phân tích & Trích ảnh</span>
          <span>03 · Lưu ảnh thô theo SKU</span>
        </div>
      </section>

      <section className="live-panel">
        <div className="catalogue-heading">
          <div>
            <h2>Kho Catalogue</h2>
            <small>Google_Drive_Storage / 1_Catalogues</small>
          </div>
          <button
            className="primary"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              setError('');
              try {
                await scan(true);
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            Quét thư mục
          </button>
        </div>
        <p>{detail}</p>
        <div className="catalogue-summary">
          <span>{files.length} tài liệu</span>
          <span>🟢 {files.filter(f => f.state === 'COMPLETED').length} đã phân tích</span>
          <span>⚪ {files.filter(f => f.state !== 'COMPLETED').length} cần xử lý</span>
        </div>
        {scanned && !files.length && <p>Chưa tìm thấy PDF. Đặt file vào thư mục trên máy chạy BIS rồi bấm Quét thư mục.</p>}
        <div className="catalogue-files">
          {files.map(f => (
            <button
              disabled={busy}
              aria-pressed={selected === f.id}
              data-completed={f.state === 'COMPLETED'}
              key={f.id}
              onClick={() => {
                setSelected(f.id);
                setConfirm(false);
      setResultVersion(v => v + 1);
                setDialog(false);
                setError('');
                setProgress('');
              }}
            >
              <span className="catalogue-file-name">{f.state === 'COMPLETED' ? '🟢' : '📄'} {f.name}</span>
              <small>{f.path} · {(f.size / 1024 / 1024).toFixed(2)} MB</small>
              <span className="catalogue-status">{states[f.state] || f.state}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="live-panel">
        <h2>Tài liệu cần phân tích</h2>
        {file ? (
          <>
            <strong>{file.name}</strong>
            <p>{states[file.state] || file.state} · Phân tích tạo bản làm việc để kiểm tra; bản sửa đã có được giữ lại.</p>
            <div className="catalogue-range">
              <label>
                Phạm vi
                <select disabled={busy} value={mode} onChange={e => setMode(e.target.value)}>
                  <option value="full">Toàn bộ tài liệu</option>
                  <option value="range">Khoảng trang</option>
                  <option value="single">Một trang</option>
                </select>
              </label>
              {mode !== 'full' && (
                <label>
                  {mode === 'single' ? 'Trang' : 'Từ trang'}
                  <input
                    type="number"
                    min="1"
                    disabled={busy}
                    value={from}
                    onChange={e => setFrom(Math.max(1, Number(e.target.value)))}
                  />
                </label>
              )}
              {mode === 'range' && (
                <label>
                  Đến trang
                  <input
                    type="number"
                    min={from}
                    disabled={busy}
                    value={to}
                    onChange={e => setTo(Math.max(from, Number(e.target.value)))}
                  />
                </label>
              )}
            </div>
            <button className="primary" disabled={busy} onClick={() => analyse()}>
              {busy ? 'Đang phân tích…' : file.state === 'COMPLETED' ? 'Phân tích lại' : 'Phân tích tài liệu'}
            </button>
          </>
        ) : (
          <p>Chọn một tài liệu trong danh sách phía trên để bắt đầu.</p>
        )}

        {dialog && (
          <div className="catalogue-confirm" role="alertdialog" aria-label="Xác nhận phân tích lại">
            <h3>Bạn có muốn phân tích lại tài liệu này không?</h3>
            <p>{file?.name} có trang đã xử lý hoặc phiên bản đã thay đổi. Chạy lại sẽ gọi AI và có thể dùng thêm hạn mức API.</p>
            <label>
              <input type="checkbox" checked={confirm} onChange={e => setConfirm(e.target.checked)} />
              Tôi muốn phân tích lại
            </label>
            <div className="bis-workflow-actions">
              <button className="primary" disabled={!confirm || busy} onClick={() => analyse(true)}>
                Xác nhận phân tích lại
              </button>
              <button onClick={() => setDialog(false)}>Hủy</button>
            </div>
          </div>
        )}
        {file && <div>
          <p>Đã lưu kết quả: {file.completed_pages}/{file.pages} trang ({file.pages ? Math.round(file.completed_pages/file.pages*100) : 0}%). {file.changed ? 'PDF đã đổi — cần xác nhận phiên bản mới.' : ''}</p>
          <progress style={{width:'100%'}} max={file.pages || 1} value={file.completed_pages}/>
          {file.done_pages?.length > 0 && <details><summary>Trang đã xử lý</summary>{file.done_pages.join(', ')}</details>}
          <button disabled={busy} onClick={() => analyse(false, undefined, true)}>Tiếp tục trang chưa phân tích trong phạm vi đã chọn</button>
        </div>}
        {runProgress && <div role="status">Lượt hiện tại: {runProgress.done}/{runProgress.total} trang · {runProgress.total ? Math.round(runProgress.done/runProgress.total*100) : 100}%<progress style={{width:'100%'}} max={runProgress.total || 1} value={runProgress.done}/></div>}
        <label><input type="checkbox" style={{width:'auto'}} checked={forceRefresh} disabled={busy} onChange={e=>setForceRefresh(e.target.checked)}/> Phân tích mới bằng AI, bỏ qua kết quả đã lưu (dùng thêm hạn mức)</label>
        <p><small>PDF có chữ rõ được ưu tiên xử lý bằng văn bản; trang scan hoặc nhiều cột dùng thêm ảnh. Kết quả lưu vẫn cần đối chiếu nguồn.</small></p>
        {progress && <p role="status">{progress}</p>}
        {error && <p role="alert" className="catalogue-error">{error}</p>}
      </section>

      {file && (
        <details className="live-panel" style={{marginTop:'12px'}}>
          <summary style={{fontWeight:600, cursor:'pointer'}}>
            Trích toàn bộ ảnh trong PDF / Vùng PDF scan (Khu vực ảnh chưa gán SKU)
          </summary>
          <div style={{marginTop:'12px'}}>
            <p><small>Trích xuất theo từng nhóm trang để tránh quá tải bộ nhớ. Ảnh trích xuất chưa được tự động gán tên theo SKU.</small></p>
            <div className="catalogue-range">
              <label>
                Từ trang
                <input
                  type="number"
                  min="1"
                  disabled={busy}
                  value={batchStart}
                  onChange={e => setBatchStart(Math.max(1, Number(e.target.value)))}
                />
              </label>
              <label>
                Đến trang
                <input
                  type="number"
                  min={batchStart}
                  disabled={busy}
                  value={batchEnd}
                  onChange={e => setBatchEnd(Math.max(batchStart, Number(e.target.value)))}
                />
              </label>
              <button disabled={busy} onClick={() => extractBatch()} style={{alignSelf:'flex-end'}}>
                Trích ảnh trong khoảng trang
              </button>
            </div>

            <details style={{marginTop:'12px'}}>
              <summary>Trích vùng từ trang PDF scan / vector</summary>
              <div className="catalogue-range" style={{marginTop:'8px'}}>
                <label>Trang<input type="number" min="1" value={cropPage} onChange={e => setCropPage(Number(e.target.value))} /></label>
                <label>Trái (%)<input type="number" min="0" max="99" value={cropX0} onChange={e => setCropX0(Number(e.target.value))} /></label>
                <label>Trên (%)<input type="number" min="0" max="99" value={cropY0} onChange={e => setCropY0(Number(e.target.value))} /></label>
                <label>Phải (%)<input type="number" min="1" max="100" value={cropX1} onChange={e => setCropX1(Number(e.target.value))} /></label>
                <label>Dưới (%)<input type="number" min="1" max="100" value={cropY1} onChange={e => setCropY1(Number(e.target.value))} /></label>
              </div>
              <p><small>Lưu ý: Ảnh render từ vùng PDF scan / vector chưa phải ảnh sản phẩm tách riêng, cần xác nhận đúng vật thể.</small></p>
              <button disabled={busy} onClick={renderCrop}>Kết xuất vùng chọn</button>
            </details>

            {batchCursor && <button disabled={busy} onClick={() => extractBatch(batchCursor)}>Trích nhóm tiếp theo (trang {batchCursor.page})</button>}
        {cropMsg && <p role="status" style={{color:'#137333', marginTop:'8px'}}>{cropMsg}</p>}

            {unassignedPool.length > 0 && (
              <div style={{marginTop:'16px', padding:'12px', background:'#f8f9fa', borderRadius:'6px'}}>
                <h4>Khu vực ảnh chưa gán SKU ({unassignedPool.length} ảnh)</h4>
                <p><small>Chọn các ảnh bên dưới, chọn SKU đích rồi bấm "Xác nhận lưu ảnh thô". File sẽ được lưu dưới dạng SKU_1.png, SKU_2.png...</small></p>

                <div style={{display:'flex', gap:'12px', alignItems:'center', margin:'8px 0'}}>
                  <label>
                    SKU đích:
                    <select value={assignTargetSku} onChange={e => setAssignTargetSku(e.target.value)}>
                      {results.map(r => (
                        <option key={r.sku} value={r.sku}>{r.sku} · {r.product_name_en || r.product_name}</option>
                      ))}
                    </select>
                  </label>
                  <button
                    className="primary"
                    disabled={busy || selectedUnassigned.size === 0 || !assignTargetSku}
                    onClick={assignAndSaveUnassigned}
                  >
                    Gán SKU và lưu ảnh thô ({selectedUnassigned.size} ảnh)
                  </button>
                </div>

                <div className="sku-image-grid" style={{marginTop:'8px'}}>
                  {unassignedPool.map(img => {
                    const isSel = selectedUnassigned.has(img.id);
                    return (
                      <article key={img.id} style={{outline: isSel ? '2px solid #1a73e8' : '1px solid #ddd', padding:'8px'}}>
                        <ProtectedImage src={img.url} alt="Ảnh chưa gán SKU" style={{maxHeight:'140px', objectFit:'contain'}} />
                        <small style={{display:'block', marginTop:'4px'}}>
                          Trang {img.page} · {img.width} × {img.height} px
                        </small>
                        <label style={{display:'flex', alignItems:'center', gap:'6px', marginTop:'6px', cursor:'pointer'}}>
                          <input
                            type="checkbox"
                            checked={isSel}
                            onChange={() => {
                              const next = new Set(selectedUnassigned);
                              if (next.has(img.id)) next.delete(img.id);
                              else next.add(img.id);
                              setSelectedUnassigned(next);
                            }}
                          />
                          Chọn ảnh này
                        </label>
                      </article>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </details>
      )}

      <section className="live-panel">
        <h2>Kết quả phân tích trong tài liệu</h2>
        {results.length ? (
          <>
            <label>
              Mã sản phẩm
              <select
                disabled={busy}
                value={resultSku}
                onChange={e => {
                  setResultSku(e.target.value); try {sessionStorage.setItem('bis:technical:sku:'+selected,e.target.value);} catch {}
                  setConfirm(false);
      setResultVersion(v => v + 1);
                }}
              >
                {results.map(r => (
                  <option key={r.sku} value={r.sku}>
                    {r.sku} · {r.name_review?.display_name || r.product_name || r.product_name_en}
                  </option>
                ))}
              </select>
            </label>
            {result && (
              <>
                <TechnicalReview key={selected + ':' + result.sku} file={file!} result={result} />
                <label>
                  <input
                    type="checkbox"
                    style={{width: 'auto'}}
                    checked={confirm}
                    onChange={e => setConfirm(e.target.checked)}
                  />
                  Tôi muốn phân tích lại SKU {result.sku} trên trang nguồn
                </label>
                <button disabled={busy || !confirm} onClick={() => analyse(true, result)}>
                  Yêu cầu phân tích lại sản phẩm
                </button>
              </>
            )}
          </>
        ) : (
          <p>Chưa có kết quả của file này. Chọn tài liệu và phạm vi trang để phân tích.</p>
        )}
      </section>
    </div>
  );
}

function TechnicalReview({file, result}: {file: Catalogue; result: any}) {
  const [review, setReview] = useState(result.name_review);
  const [name, setName] = useState(result.name_review?.suggested_name || result.product_name || '');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [source, setSource] = useState<any>(null);
  const [sourceError,setSourceError]=useState('');
  const [zoom,setZoom]=useState(100);
  const [viewPage,setViewPage]=useState(Number(result.source_page));
  const [loading, setLoading] = useState(false);

  // Raw Image Candidates for SKU on page
  const [candidates, setCandidates] = useState<any[]>([]);
  const [showRejected, setShowRejected] = useState(false);
  const [selectedCands, setSelectedCands] = useState<Set<string>>(new Set());
  const [savedRawList, setSavedRawList] = useState<any[]>([]);
  const [candBusy, setCandBusy] = useState(false);
  const [candMsg, setCandMsg] = useState('');

  const sku = result.sku;

  async function loadSkuCandidates() {
    setCandBusy(true);
    setCandMsg('Đang tìm ảnh ứng viên trên trang chứa SKU…');
    try {
      const data = await request(`products/${encodeURIComponent(sku)}/image-search`, {asset_id: file.id});
      setCandidates(data.candidates || []);
      // Check already saved raw images
      const rawData = await request(`products/${encodeURIComponent(sku)}/raw-images`);
      setSavedRawList(rawData.raw_images || []);
      setCandMsg(data.candidates?.length
        ? `Tìm thấy ${data.candidates.length} ảnh ứng viên trên các trang chứa SKU ${sku}. Cùng trang chưa chứng minh đúng sản phẩm.`
        : 'Không tìm thấy ảnh nhúng trên trang chứa SKU. Bạn có thể trích từ khoảng trang hoặc cắt vùng trang PDF scan.');
    } catch (e) {
      setCandMsg((e as Error).message);
    } finally {
      setCandBusy(false);
    }
  }

  useEffect(() => {
    setReview(result.name_review);
    setName(result.name_review?.suggested_name || result.product_name || '');
    setMessage('');
    setCandidates([]);
    setSelectedCands(new Set());
    setSavedRawList([]);
    loadSkuCandidates();
  }, [result]);

  useEffect(() => {setViewPage(Number(result.source_page));setZoom(100);}, [file.id,result.sku,result.source_page]);
  useEffect(() => {
    let active=true;setLoading(true);setSource(null);setSourceError('');
    request(`catalogues/${file.id}/source/${viewPage}?sha256=${file.sha256}`)
      .then(data=>{if(active)setSource(data);})
      .catch(e=>{if(active)setSourceError(e.message);})
      .finally(()=>{if(active)setLoading(false);});
    return()=>{active=false;};
  }, [file.id,file.sha256,viewPage]);

  async function classifySelected(reason: string) {
    setCandBusy(true);
    try {
      await request(`products/${encodeURIComponent(sku)}/raw-images/feedback`, {
        candidate_ids: Array.from(selectedCands), reason, confirm: true
      });
      setSelectedCands(new Set());
      await loadSkuCandidates();
      setCandMsg(reason === 'RESET' ? 'Đã bỏ nhãn loại; ảnh được xét lại.' : 'Đã lưu phân loại cho SKU này. Ảnh bị loại được ẩn mặc định; không xóa file gốc.');
    } catch(e) { setCandMsg((e as Error).message); }
    finally { setCandBusy(false); }
  }

  async function saveRawSelected() {
    if (selectedCands.size === 0) {
      setCandMsg('Vui lòng chọn ít nhất 1 ảnh ứng viên.');
      return;
    }
    setCandBusy(true);
    setCandMsg('Đang lưu ảnh thô và cập nhật bộ nhớ hiệu chỉnh…');
    try {
      const ids = Array.from(selectedCands);
      const res = await request(`products/${encodeURIComponent(sku)}/raw-images/save`, {
        candidate_ids: ids,
        confirm: true
      });
      const savedCount = res.saved_count || 0;
      setCandMsg(`Đã xác nhận và lưu ${savedCount} ảnh thô cho SKU ${sku}. Naming: ${sku}_1.png, ${sku}_2.png... (chống trùng SHA256).`);
      setSelectedCands(new Set());
      const rawData = await request(`products/${encodeURIComponent(sku)}/raw-images`);
      setSavedRawList(rawData.raw_images || []);
    } catch (e) {
      setCandMsg((e as Error).message);
    } finally {
      setCandBusy(false);
    }
  }

  const specs = [
    ['Danh mục', 'category'],
    ['Vật liệu', 'material'],
    ['Màu', 'color'],
    ['Khổ rộng (cm)', 'width_cm'],
    ['Định lượng (g/m²)', 'weight_gsm'],
    ['Kiểu dệt / kiểu dáng', 'pattern'],
    ['Hoàn tất', 'finish'],
    ['Đơn vị', 'unit'],
    ['Giá USD', 'price_usd'],
    ['Giá VNĐ', 'price_vnd']
  ];

  return (
    <div className="technical-compare-layout">
      <aside className="technical-pdf-panel" aria-label="Trang catalogue đối chiếu">
        <h3>Trang catalogue gốc</h3>
        <p>{file.name} · Trang {viewPage} · SKU {sku}</p>
        <div className="technical-pdf-toolbar">
          <button disabled={loading || viewPage<=1} onClick={()=>setViewPage(p=>p-1)}>← Trang trước</button>
          <button disabled={loading || viewPage>=file.pages} onClick={()=>setViewPage(p=>p+1)}>Trang sau →</button>
          <button onClick={()=>setViewPage(Number(result.source_page))}>Về trang sản phẩm</button>
          <label>Phóng to <select value={zoom} onChange={e=>setZoom(Number(e.target.value))}>{[100,125,150,200,250].map(n=><option key={n} value={n}>{n}%</option>)}</select></label>
        </div>
        {loading && <p role="status">Đang mở trang catalogue…</p>}
        {sourceError && <p role="alert">{sourceError}</p>}
        {source && <><div className="technical-pdf-scroll" tabIndex={0} aria-label="Ảnh trang PDF, cuộn để đối chiếu"><img src={source.image} alt={`${file.name} trang ${viewPage}`} style={{width:`${zoom}%`,maxWidth:'none'}}/></div><details><summary>Văn bản trang gốc</summary><pre style={{whiteSpace:'pre-wrap',maxHeight:220,overflow:'auto'}}>{source.text || 'Trang không có lớp chữ.'}</pre></details></>}
      </aside>
    <div className="technical-review">
      <section>
        <h3>1 · Nguồn PDF</h3>
        <p>{file.name} · Trang {result.source_page} · SKU <strong>{result.sku}</strong></p>
        <label>Tên tiếng Anh trong kết quả trích xuất</label>
        <p><strong>{result.product_name_en || 'Chưa trích được tên gốc'}</strong></p>
        <blockquote>{result.evidence_quote || 'Chưa có câu trích dẫn; cần mở trang để kiểm tra.'}</blockquote>
        <button onClick={()=>{setViewPage(Number(result.source_page));setZoom(150);}}>Đối chiếu trang nguồn bên cạnh</button>
      </section>

      <section>
        <h3>2 · Trích ảnh từ PDF & Lưu kho ảnh thô (Google_Drive_Storage/4_Product_Images/raw/)</h3>
        <p><small>Ưu tiên ảnh trên trang chứa SKU {sku}. Hiển thị cùng tên PDF, số trang, tên tiếng Anh. Không coi mọi ảnh cùng trang đều thuộc SKU.</small></p>
        <p role="status">{candMsg}</p>

        {candidates.length > 0 && (
          <div style={{marginTop:'12px'}}>
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'8px'}}>
              <span>Đã chọn {selectedCands.size}/{candidates.length} ảnh ứng viên</span>
              <button
                className="primary"
                disabled={candBusy || selectedCands.size === 0}
                onClick={saveRawSelected}
              >
                Xác nhận lưu ảnh thô
              </button>
            </div>

            <p><small>Chọn ảnh rồi xác nhận đúng thao tác. Tên dưới ảnh là sản phẩm đang đối chiếu, chưa phải nhận diện ảnh.</small></p>
            <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
              <button disabled={candBusy || !selectedCands.size} onClick={() => classifySelected('NOT_PRODUCT')}>Xác nhận ảnh đã chọn không phải ảnh sản phẩm</button>
              <button disabled={candBusy || !selectedCands.size} onClick={() => classifySelected('OTHER_SKU')}>Ảnh sản phẩm khác SKU</button>
              <button disabled={candBusy || !selectedCands.size} onClick={() => classifySelected('RESET')}>Bỏ nhãn loại — xét lại ảnh</button>
            </div>
            <label><input type="checkbox" style={{width:'auto'}} checked={showRejected} onChange={e => {setShowRejected(e.target.checked);setSelectedCands(new Set());}}/> Hiện ảnh đã loại ({candidates.filter(c => c.calibration_status === 'REJECTED').length})</label>
            <p><small>Bộ nhớ dùng hash ảnh và SKU để lọc lần sau, chưa tự nhận diện mọi ảnh tương tự. Chưa xác minh đồng bộ bộ nhớ Cloud.</small></p>
            <div className="sku-image-grid">
              {candidates.filter(c => showRejected || c.calibration_status !== 'REJECTED').map(cand => {
                const isSelected = selectedCands.has(cand.id);
                return (
                  <article
                    key={cand.id}
                    style={{
                      outline: isSelected ? '2px solid #2e7d32' : '1px solid #ddd',
                      background: isSelected ? '#f6fbf6' : '#fff'
                    }}
                  >
                    <ProtectedImage src={cand.url} alt={`Ảnh ứng viên ${sku}`} style={{maxHeight:'160px', objectFit:'contain'}} />
                    <strong>{result.product_name_en || 'Chưa có tên tiếng Anh'}</strong>
                    <small style={{display:'block'}}>
                      PDF: {file.name} · Trang {cand.page} · {cand.width} × {cand.height} px
                    </small>
                    <small style={{color:'#666', display:'block'}}>
                      Mã băm SHA256: {cand.sha256?.slice(0, 12)}…
                    </small>
                    {cand.calibration_status === 'ACCEPTED' && (
                      <span className="live-chip" style={{background:'#e6f4ea', color:'#137333'}}>Đã từng lưu trước đây</span>
                    )}
                    {cand.calibration_status === 'REJECTED' && (
                      <span className="live-chip" style={{background:'#fce8e6', color:'#c5221f'}}>Đã được xác nhận loại cho SKU này</span>
                    )}
                    <label style={{display:'flex', alignItems:'center', gap:'6px', marginTop:'8px', cursor:'pointer', fontWeight:500}}>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {
                          const next = new Set(selectedCands);
                          if (next.has(cand.id)) next.delete(cand.id);
                          else next.add(cand.id);
                          setSelectedCands(next);
                        }}
                      />
                      Chọn ảnh để lưu hoặc phân loại
                    </label>
                  </article>
                );
              })}
            </div>
          </div>
        )}

        {savedRawList.length > 0 && (
          <div style={{marginTop:'16px', padding:'10px', background:'#f0f4f8', borderRadius:'6px'}}>
            <strong>Ảnh thô đã lưu cho {sku} ({savedRawList.length} ảnh):</strong>
            <ul style={{margin:'6px 0 0 16px', padding:0}}>
              {savedRawList.map(item => (
                <li key={item.filename}>
                  <code>{item.filename}</code> · {(item.size / 1024).toFixed(1)} KB · SHA256: <code>{item.sha256?.slice(0, 10)}…</code>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section>
        <h3>3 · Duyệt tên và lưu hiệu chỉnh</h3>
        <p>
          {review?.state === 'NAME_APPROVED' ? 'Đã duyệt tên cho phiên bản PDF này.' : 'Tên chưa được duyệt.'} {review?.reason}
        </p>
        <label>
          Tên tiếng Việt chuyên ngành
          <input maxLength={300} value={name} onChange={e => setName(e.target.value)} />
        </label>
        <p>
          <small>
            Chỉ duyệt tên. Không duyệt thông số, không ghi đè bản nháp sản phẩm. Tên đã lưu được gợi ý lại cho cùng tài liệu, SKU và tên tiếng Anh.
          </small>
        </p>
        <button
          className="primary"
          disabled={saving || !name.trim() || !result.product_name_en}
          onClick={async () => {
            setSaving(true);
            setMessage('');
            try {
              const next = await request(`catalogues/${file.id}/name`, {
                sku: result.sku,
                product_name_en: result.product_name_en,
                sha256: file.sha256,
                name,
                revision: review?.revision || []
              });
              setReview(next);
              setMessage('Đã lưu tên vào bộ nhớ có phiên bản.');
            } catch (e) {
              setMessage((e as Error).message);
            } finally {
              setSaving(false);
            }
          }}
        >
          {saving ? 'Đang lưu…' : 'Xác nhận tên và lưu bộ nhớ'}
        </button>
        {message && <p role="status">{message}</p>}
      </section>
    </div>
    </div>
  );
}
