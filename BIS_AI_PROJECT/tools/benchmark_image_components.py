"""Optional isolated GitHub component benchmark; never writes product storage.

Run in a Python 3.12 environment with rembg[cpu] installed, not the BIS web env.
python tools/benchmark_image_components.py --output NEW_LAB_DIR source1.png source2.png
Optional --upscaler-exe path/to/realesrgan-ncnn-vulkan.exe (bundled models required).
Outputs are unapproved experiments; do not use this tool to certify identity/text.
"""
import argparse
import os
import hashlib
import json
import subprocess
import time
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--upscaler-exe',type=Path)
    parser.add_argument('sources',nargs='+',type=Path)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    os.environ.setdefault('NUMBA_DISABLE_JIT','1')
    from PIL import Image
    from rembg import remove,new_session
    session=new_session('u2netp',providers=['CPUExecutionProvider'])
    results=[]
    for i,source in enumerate(args.sources):
        start=time.monotonic()
        with Image.open(source) as image:
            cutout=remove(image,session=session)
            cutout.save(args.output/f'{i}_cutout.png')
            row=dict(source=source.name,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                     input_size=list(image.size),alpha_range=cutout.getchannel('A').getextrema(),
                     seconds=round(time.monotonic()-start,3),status='UNAPPROVED_EXPERIMENT')
        if args.upscaler_exe:
            exe=args.upscaler_exe.resolve()
            start=time.monotonic()
            response=subprocess.run([str(exe),'-i',str(source.resolve()),'-o',str((args.output/f'{i}_4x.png').resolve()),
                '-n','realesrgan-x4plus','-s','4','-t','64','-j','1:1:1'],cwd=exe.parent,capture_output=True,timeout=180)
            row.update(upscale_exit=response.returncode,upscale_seconds=round(time.monotonic()-start,3))
        results.append(row)
    (args.output/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False))

if __name__=='__main__': main()
