"""User-supplied public page image discovery, bounded and read-only."""
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from media_quality import public_url, rank_candidates

def web_images(url, sku, name):
    for _ in range(5):
        public_url(url)
        with requests.get(url,timeout=15,stream=True,allow_redirects=False) as response:
            if response.status_code in (301,302,303,307,308):
                url=urljoin(url,response.headers.get('Location','')); continue
            response.raise_for_status()
            if 'text/html' not in response.headers.get('Content-Type','').lower():
                raise ValueError('Link cần trả về trang HTML công khai')
            chunks=[];size=0
            for chunk in response.iter_content(65536):
                size+=len(chunk)
                if size>2_000_000: raise ValueError('Trang vượt giới hạn 2 MB')
                chunks.append(chunk)
            soup=BeautifulSoup(b''.join(chunks),'html.parser')
            title=soup.title.get_text(' ',strip=True) if soup.title else ''
            rows=[]
            for tag in soup.select('img[src],img[data-src],meta[property="og:image"]')[:100]:
                src=tag.get('data-src') or tag.get('src') or tag.get('content')
                link=urljoin(url,src or '')
                if not link.startswith(('https://','http://')): continue
                rows.append({'image_url':link,'title':tag.get('alt') or title,'source_url':url})
            return rank_candidates(rows,sku,name,'')[:24]
    raise ValueError('Quá nhiều chuyển hướng')
