"""Image intake and pixel-preserving draft composition. No generative identity guesses."""
import hashlib
import io
import re
from pathlib import Path
from urllib.parse import urlparse
import ipaddress
import socket
import requests
from PIL import Image, ImageOps, ImageFilter
from product_quality import token_present

def checked_image(data):
    if len(data)>25*1024*1024:
        raise ValueError("Ảnh vượt 25 MB")
    with Image.open(io.BytesIO(data)) as im:
        if im.width*im.height>30_000_000:
            raise ValueError("Ảnh vượt 30 triệu pixel")
        im.load()
        return ImageOps.exif_transpose(im).convert("RGBA")

def safe_name(sku):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}",str(sku)):
        raise ValueError("SKU không hợp lệ")
    return str(sku)

def public_url(url):
    p=urlparse(url)
    if p.scheme not in {"https","http"} or not p.hostname or p.username or p.password:
        raise ValueError("URL ảnh không hợp lệ")
    for info in socket.getaddrinfo(p.hostname,p.port or (443 if p.scheme=="https" else 80)):
        if not ipaddress.ip_address(info[4][0]).is_global:
            raise ValueError("URL phải là nguồn công khai")
    return url

def download_image(url):
    for _ in range(5):
        public_url(url)
        with requests.get(url,stream=True,timeout=20,allow_redirects=False) as response:
            if response.status_code in {301,302,303,307,308}:
                from urllib.parse import urljoin
                url=urljoin(url,response.headers.get("Location",""))
                continue
            response.raise_for_status()
            if not response.headers.get("Content-Type","").lower().startswith("image/"):
                raise ValueError("Nguồn trả về không phải ảnh")
            parts=[]; size=0
            for block in response.iter_content(65536):
                size+=len(block)
                if size>25*1024*1024:
                    raise ValueError("Ảnh vượt giới hạn")
                parts.append(block)
            data=b"".join(parts)
            checked_image(data)
            return data
    raise ValueError("Quá nhiều lần chuyển hướng")

def rank_candidates(rows,sku,name,brand):
    words=set(re.findall(r"\w+",str(name).casefold()))-{"the","and","for","of"}
    result=[];seen=set()
    for row in rows:
        url=row.get("image_url") or ""
        if not url or url in seen:
            continue
        seen.add(url)
        title=str(row.get("title") or "")
        evidence=title+" "+url+" "+str(row.get("page_url") or "")
        exact=token_present(sku,evidence)
        overlap=len(words & set(re.findall(r"\w+",evidence.casefold())))
        result.append({**row,"score":(50 if exact else 0)+overlap*3+(10 if brand and brand.casefold() in evidence.casefold() else 0),
                       "sku_evidence":exact,"status":"NEEDS_REVIEW"})
    return sorted(result,key=lambda x:x["score"],reverse=True)

def studio_draft(source_path,background_path,output_path, *, remove_white=False):
    data=Path(source_path).read_bytes()
    im=checked_image(data)
    if min(im.size)<500:
        raise ValueError(f"Nguồn {im.width}×{im.height} quá nhỏ cho ảnh studio; chọn ảnh gốc lớn hơn")
    if remove_white:
        import cv2
        import numpy as np
        arr=np.array(im)
        h,w=arr.shape[:2]
        mask=np.zeros((h+2,w+2),np.uint8)
        rgb=arr[:,:,:3].copy()
        # Only near-neutral white connected to the outside may be removed.
        eligible=(rgb.min(axis=2)>238)&((rgb.max(axis=2)-rgb.min(axis=2))<10)
        binary=(eligible*255).astype("uint8")
        for x,y in [(0,0),(w-1,0),(0,h-1),(w-1,h-1)]:
            if binary[y,x]:
                cv2.floodFill(binary,mask,(x,y),255,flags=4|cv2.FLOODFILL_MASK_ONLY|(255<<8))
        arr[:,:,3][mask[1:-1,1:-1]==255]=0
        im=Image.fromarray(arr)
    bounds=im.getbbox()
    if not bounds:
        raise ValueError("Không tìm thấy vật thể sau tách nền")
    im=im.crop(bounds)
    # Refuse invented detail from upscaling; native size caps the object size.
    scale=min(850/im.width,850/im.height,1.0)
    size=(max(1,round(im.width*scale)),max(1,round(im.height*scale)))
    im=im.resize(size,Image.Resampling.LANCZOS)
    with Image.open(background_path) as bg:
        if min(bg.size)<1000:
            raise ValueError("Phông nền nguồn cần ít nhất 1000 pixel mỗi chiều")
        canvas=ImageOps.fit(bg.convert("RGBA"),(1254,1254),method=Image.Resampling.LANCZOS)
    x=(1254-im.width)//2
    y=min(1040-im.height,(1254-im.height)//2+80)
    shadow=Image.new("RGBA",canvas.size)
    alpha=Image.new("L",canvas.size)
    alpha.paste(im.getchannel("A"),(x+8,y+12))
    alpha=alpha.filter(ImageFilter.GaussianBlur(12)).point(lambda v:int(v*.28))
    shadow.putalpha(alpha)
    canvas=Image.alpha_composite(canvas,shadow)
    canvas.alpha_composite(im,(x,y))
    Path(output_path).parent.mkdir(parents=True,exist_ok=True)
    canvas.convert("RGB").save(output_path,format="PNG")
    return {"source_sha256":hashlib.sha256(data).hexdigest(),"size":[1254,1254],
            "object_size":list(size),"status":"PENDING_REVIEW",
            "note":"Bản ghép bảo toàn pixel; cần kiểm tra nền, chữ, logo và độ chân thật."}

