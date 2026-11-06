import {useState, useEffect} from 'react';
import {bisFetch, ProtectedImage, AssetLink} from '../streamlitTransport';

type CompletedImage = {
  filename: string;
  path: string;
  sha256: string;
  size: number;
  url: string;
  is_legacy: boolean;
  legacy_label: string | null;
  is_confirmed: boolean;
  is_primary: boolean;
  order: number;
  hash_mismatch: boolean;
  warning: string | null;
  modified_at: string;
};

async function request(path: string, body?: any) {
  const r = await bisFetch('/api/' + path, {
    method: body === undefined ? 'GET' : 'POST',
    headers: {'Content-Type': 'application/json', 'X-BIS-Request': '1'},
    body: body === undefined ? undefined : JSON.stringify(body)
  });
  const data = await r.json();
  if (!r.ok) throw Error(data.detail || 'Không xử lý được yêu cầu');
  return data;
}

export default function ImageSources({product, assets}: {product: any; assets: any[]}) {
  const [items, setItems] = useState<CompletedImage[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [primary, setPrimary] = useState<string>('');
  const [orders, setOrders] = useState<Record<string, number>>({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [backgroundFilename, setBackgroundFilename] = useState('Nền vật tư.png');
  const [scanTime, setScanTime] = useState<string>('');

  const sku = product?.sku || '';
  const base = 'products/' + encodeURIComponent(sku);

  async function loadImages() {
    if (!sku) return;
    setBusy(true);
    setMessage('Đang quét ảnh hoàn thiện trong Google_Drive_Storage/6_Final_Composites/…');
    try {
      const data = await request(base + '/completed-images');
      const loaded: CompletedImage[] = data.completed_images || [];
      setItems(loaded);
      setScanTime(new Date().toLocaleTimeString('vi-VN'));

      // Populate selected and primary from confirmed state or defaults
      const confirmedSet = new Set<string>();
      const orderMap: Record<string, number> = {};
      let foundPrimary = '';

      loaded.forEach((img, idx) => {
        orderMap[img.filename] = idx + 1;
        if (img.is_confirmed) {
          confirmedSet.add(img.filename);
          if (img.is_primary) foundPrimary = img.filename;
        }
      });

      setSelected(confirmedSet);
      setPrimary(foundPrimary || loaded[0]?.filename || '');
      setOrders(orderMap);

      const hasMismatch = loaded.some(img => img.hash_mismatch);
      if (hasMismatch) {
        setMessage('⚠️ Cảnh báo: Có tệp ảnh đã bị thay đổi nội dung trên đĩa sau khi xác nhận! Cần đối chiếu lại.');
      } else {
        setMessage(loaded.length
          ? `Đã tìm thấy ${loaded.length} ảnh hoàn thiện khớp chính xác SKU ${sku}.`
          : `Chưa có ảnh hoàn thiện nào cho SKU ${sku} trong Google_Drive_Storage/6_Final_Composites/.`);
      }
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    loadImages();
  }, [sku]);

  if (!product) return <p>Chọn SKU để xem ảnh hoàn thiện.</p>;

  function toggleSelect(filename: string) {
    const next = new Set(selected);
    if (next.has(filename)) {
      next.delete(filename);
      if (primary === filename) {
        const remaining = Array.from(next);
        setPrimary(remaining[0] || '');
      }
    } else {
      next.add(filename);
      if (!primary) setPrimary(filename);
    }
    setSelected(next);
  }

  function moveOrder(filename: string, direction: 'up' | 'down') {
    const sorted = [...items].sort((a, b) => (orders[a.filename] || 0) - (orders[b.filename] || 0));
    const idx = sorted.findIndex(i => i.filename === filename);
    if (idx < 0) return;
    const targetIdx = direction === 'up' ? idx - 1 : idx + 1;
    if (targetIdx < 0 || targetIdx >= sorted.length) return;

    const currentOrder = orders[filename] || idx + 1;
    const targetItem = sorted[targetIdx];
    const targetOrder = orders[targetItem.filename] || targetIdx + 1;

    setOrders({
      ...orders,
      [filename]: targetOrder,
      [targetItem.filename]: currentOrder
    });
  }

  async function confirmImageSet() {
    if (selected.size === 0) {
      setMessage('Vui lòng chọn ít nhất 1 ảnh vào bộ ảnh thành phẩm.');
      return;
    }
    setBusy(true);
    setMessage('Đang lưu xác nhận bộ ảnh và tính hash SHA256…');
    try {
      const selectedList = items
        .filter(img => selected.has(img.filename))
        .sort((a, b) => (orders[a.filename] || 0) - (orders[b.filename] || 0))
        .map(img => ({
          filename: img.filename,
          sha256: img.sha256,
          order: orders[img.filename] || 1
        }));

      await request(base + '/completed-images/confirm', {
        images: selectedList,
        primary_image: primary || selectedList[0].filename,
        confirm: true
      });

      setMessage('Đã xác nhận bộ ảnh thành phẩm cho SKU ' + sku + '. Đã lưu SHA256 chống thay đổi file.');
      await loadImages();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function downloadFlowPackage() {
    setBusy(true);
    try {
      const res = await bisFetch('/api/' + base + '/completed-images/package', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-BIS-Request': '1'},
        body: JSON.stringify({background_filename: backgroundFilename})
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Không thể tạo gói xuất Flow AI');
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `BIS_${sku}_flow_ai.zip`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 60000);
      setMessage('Đã tải gói ZIP (ảnh thô + phôi nền BIS + FLOW_AI_PROMPT.txt). Xử lý trên Flow AI rồi lưu kết quả vào 6_Final_Composites/.');
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const sortedItems = [...items].sort((a, b) => (orders[a.filename] || 0) - (orders[b.filename] || 0));
  const hasTamperAlert = items.some(img => img.hash_mismatch);

  return (
    <section className="live-panel">
      <p>Quét thư mục trên máy chạy BIS. Chưa xác minh đồng bộ Google Drive; website Cloud không đọc trực tiếp ổ G: trên máy bạn.</p>
      <div className="catalogue-heading">
        <div>
          <h2>Hình ảnh hoàn thiện · SKU {sku}</h2>
          <p><strong>{product.product_name_en || product.product_name}</strong></p>
          <small>Nguồn dữ liệu: Google_Drive_Storage / 6_Final_Composites · {scanTime ? `Quét lúc ${scanTime}` : ''}</small>
        </div>
        <div style={{display:'flex', gap:'8px', flexWrap:'wrap'}}>
          <button disabled={busy} onClick={loadImages}>
            Quét ảnh hoàn thiện
          </button>
          <label>Phôi nền Flow AI
            <select disabled={busy} value={backgroundFilename} onChange={e => setBackgroundFilename(e.target.value)}>
              <option value="Nền vật tư.png">Nền vật tư</option>
              <option value="Nền máy móc.png">Nền máy móc</option>
            </select>
          </label>
          <button disabled={busy} onClick={downloadFlowPackage}>
            Tải gói ảnh thô + prompt cho Flow AI (ZIP)
          </button>
        </div>
      </div>

      {hasTamperAlert && (
        <div className="live-error" role="alert" style={{margin:'12px 0', padding:'12px', border:'2px solid #b82d25', background:'#fff5f5'}}>
          <strong>⚠️ PHÁT HIỆN THAY ĐỔI TỆP TRÊN ĐĨA:</strong>
          <p>Tệp ảnh đã bị chỉnh sửa hoặc ghi đè sau lần xác nhận gần nhất (sai lệch mã băm SHA256). Vui lòng đối chiếu kỹ lại chữ, logo, thông số và nhấn "Xác nhận bộ ảnh thành phẩm" để cập nhật phiên bản mới.</p>
        </div>
      )}

      <div className="image-selection-bar" aria-live="polite" style={{marginTop:'12px'}}>
        <div>
          <strong>{busy ? 'Đang xử lý…' : message}</strong>
          <p style={{margin:'4px 0 0 0', fontSize:'0.9rem'}}>
            Đã chọn {selected.size}/{items.length} ảnh trong bộ · Ảnh chính: <strong>{primary || 'Chưa chọn'}</strong>
          </p>
        </div>
        <button
          className="primary"
          disabled={busy || selected.size === 0}
          onClick={confirmImageSet}
        >
          Xác nhận bộ ảnh thành phẩm
        </button>
      </div>

      {sortedItems.length === 0 ? (
        <div style={{padding:'32px', textAlign:'center', background:'#fcfaf7', border:'1px dashed #d9c8b4', borderRadius:'8px', marginTop:'16px'}}>
          <p>Chưa có ảnh nào khớp chính xác với SKU <strong>{sku}</strong> trong thư mục <code>Google_Drive_Storage/6_Final_Composites/</code>.</p>
          <p><small>Quy ước đặt tên thành phẩm Flow AI: <code>{sku}_1.png</code>, <code>{sku}_2.png</code>...</small></p>
          <button disabled={busy} onClick={downloadFlowPackage} style={{marginTop:'8px'}}>
            Tải gói ảnh thô + prompt để đưa vào Flow AI
          </button>
        </div>
      ) : (
        <div className="sku-image-grid" style={{marginTop:'20px'}}>
          {sortedItems.map((item, idx) => {
            const isSelected = selected.has(item.filename);
            const isPrimary = (primary === item.filename);

            return (
              <article
                key={item.filename}
                style={{
                  outline: isPrimary ? '3px solid #1a73e8' : isSelected ? '2px solid #2e7d32' : '1px solid #d9c8b4',
                  background: isSelected ? '#f6fbf6' : '#fff',
                  position: 'relative'
                }}
              >
                <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'4px'}}>
                  <span className="live-caption">Vị trí #{orders[item.filename] || idx + 1}</span>
                  <div style={{display:'flex', gap:'4px'}}>
                    {item.is_legacy && (
                      <span className="live-chip" style={{background:'#f0f0f0', fontSize:'0.75rem'}}>
                        {item.legacy_label || 'Tên cũ'}
                      </span>
                    )}
                    {item.hash_mismatch ? (
                      <span className="live-chip" style={{background:'#b82d25', color:'#fff', fontSize:'0.75rem'}}>
                        SHA256 Thay đổi
                      </span>
                    ) : item.is_confirmed ? (
                      <span className="live-chip" style={{background:'#e6f4ea', color:'#137333', fontSize:'0.75rem'}}>
                        Đã xác nhận
                      </span>
                    ) : (
                      <span className="live-chip" style={{background:'#fff3e0', color:'#e65100', fontSize:'0.75rem'}}>
                        Chờ duyệt
                      </span>
                    )}
                  </div>
                </div>

                <ProtectedImage
                  src={item.url}
                  alt={`Ảnh hoàn thiện cho ${sku}`}
                  style={{width:'100%', maxHeight:'240px', objectFit:'contain', background:'#f8f9fa', borderRadius:'4px'}}
                />

                <strong style={{display:'block', marginTop:'8px', color:'#202124'}}>
                  {product.product_name_en || product.product_name}
                </strong>
                <code style={{fontSize:'0.8rem', color:'#5f6368', display:'block', wordBreak:'break-all'}}>
                  {item.filename} ({(item.size / 1024).toFixed(1)} KB)
                </code>

                {item.warning && (
                  <small style={{color:'#b82d25', display:'block', fontWeight:600, marginTop:'4px'}}>
                    {item.warning}
                  </small>
                )}

                <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginTop:'8px', paddingTop:'8px', borderTop:'1px solid #eee'}}>
                  <AssetLink url={item.url}>
                    Mở / tải ảnh ↗
                  </AssetLink>
                  <div style={{display:'flex', gap:'4px'}}>
                    <button
                      type="button"
                      disabled={busy || idx === 0}
                      onClick={() => moveOrder(item.filename, 'up')}
                      style={{padding:'2px 8px', fontSize:'0.8rem'}}
                      title="Chuyển lên trước"
                    >
                      ▲ Lên
                    </button>
                    <button
                      type="button"
                      disabled={busy || idx === sortedItems.length - 1}
                      onClick={() => moveOrder(item.filename, 'down')}
                      style={{padding:'2px 8px', fontSize:'0.8rem'}}
                      title="Chuyển xuống sau"
                    >
                      ▼ Xuống
                    </button>
                  </div>
                </div>

                <div style={{marginTop:'10px', display:'flex', flexDirection:'column', gap:'6px'}}>
                  <label style={{display:'flex', alignItems:'center', gap:'8px', cursor:'pointer', fontWeight:500}}>
                    <input
                      type="checkbox"
                      style={{width:'auto'}}
                      checked={isSelected}
                      onChange={() => toggleSelect(item.filename)}
                    />
                    Chọn vào bộ ảnh sản phẩm
                  </label>

                  <label style={{display:'flex', alignItems:'center', gap:'8px', cursor:'pointer', fontSize:'0.9rem', color: isSelected ? '#1a73e8' : '#999'}}>
                    <input
                      type="radio"
                      name="primary-image"
                      style={{width:'auto'}}
                      disabled={!isSelected}
                      checked={isPrimary}
                      onChange={() => setPrimary(item.filename)}
                    />
                    Đặt làm ảnh chính (Primary)
                  </label>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
