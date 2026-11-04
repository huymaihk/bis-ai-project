"""Reference-based Gemini image editing. Every result remains a draft."""
import base64
import hashlib
import io
import os
from pathlib import Path
from PIL import Image,ImageOps
from media_quality import checked_image

def edit_studio(source_path,background_path,output_path,sku,benchmark_path=None):
    from google import genai
    from google.genai import types
    from config import GEMINI_API_KEY
    model=os.getenv("BIS_IMAGE_MODEL","gemini-nano-banana-2.1")
    source=checked_image(Path(source_path).read_bytes())
    if min(source.size)<500:
        raise ValueError("Ảnh nguồn quá nhỏ; cần chọn ảnh gốc lớn hơn trước khi chỉnh sửa")
    prompt=("Create a photorealistic BIS Textile studio product photograph using the supplied images. "
            "Image 1 is the exact product identity, image 2 is the brand backdrop. "
            "Preserve the real object's geometry, labels, engraved numbers, logos and colors. "
            "Do not invent labels, quantities, parts, accessories, text or technical details. "
            "Change only background placement and natural studio illumination/contact shadows. "
            "Square output, sharp readable original labels, realistic material, object centered with margin. "
            "Any additional reference is for lighting/style only, NEVER replace the product with that reference. "
            "If source detail is unreadable, do not reconstruct invented text. Product identifier: "+str(sku))
    inputs=[{"type":"text","text":prompt}]
    paths=[source_path,background_path]+([benchmark_path] if benchmark_path else [])
    for path in paths:
        im=checked_image(Path(path).read_bytes())
        buf=io.BytesIO()
        im.convert("RGB").save(buf,format="PNG")
        inputs.append({"type":"image","data":base64.b64encode(buf.getvalue()).decode(),"mime_type":"image/png"})
    client=genai.Client(api_key=GEMINI_API_KEY,http_options=types.HttpOptions(timeout=60000))
    try:
        response=client.interactions.create(model=model,input=inputs)
        output=response.output_image
        if output is None or not output.data:
            raise ValueError("Model không trả ảnh; không có bản thành phẩm")
        raw=base64.b64decode(output.data)
        image=checked_image(raw)
        if min(image.size)<1000:
            raise ValueError("Ảnh AI trả về chưa đạt kích thước nguồn tối thiểu")
        target=Path(output_path)
        target.parent.mkdir(parents=True,exist_ok=True)
        # Preserve the original AI result and letterbox rather than stretching the product.
        raw_path=target.with_name(target.stem+"_original.png")
        image.save(raw_path,format="PNG")
        canvas=ImageOps.pad(image.convert("RGB"),(1254,1254),method=Image.Resampling.LANCZOS,color="white")
        canvas.save(target,format="PNG")
        return {"status":"PENDING_REVIEW","model":model,"preview_image":str(target),
                "original_image":str(raw_path),
                "source_sha256":hashlib.sha256(Path(source_path).read_bytes()).hexdigest(),
                "note":"AI có thể đổi chi tiết. Cần đối chiếu chữ/logo/hình khối với nguồn trước khi duyệt."}
    finally:
        client.close()

