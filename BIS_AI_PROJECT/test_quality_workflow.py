"""Regression scenarios for the BIS workflow. No external writes or model calls."""
import base64
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
import pymupdf
from PIL import Image,ImageDraw
from product_quality import *
from persistent_memory import MemoryStore,atomic_json
from safe_publish import publish_one,scan_store
from pdf_candidates import candidates,archive,render_region
from media_quality import studio_draft,checked_image,rank_candidates
from quality_jobs import JobRunner

def image_bytes(size=(1254,1254)):
    out=io.BytesIO()
    Image.new("RGB",size,"white").save(out,format="PNG")
    return out.getvalue()

def product():
    p=dict(sku="03026A",product_name="Sổ tay AATCC",product_name_en="AATCC Technical Manual",
           brand="AATCC",description="Tài liệu phương pháp thử nghiệm.",source_page=1,
           evidence_quote="03026A AATCC Technical Manual",meta_description="A"*150)
    p["custom_html"]=render_product(p)
    return p

class ContentTests(unittest.TestCase):
    def test_identity_not_substring(self):
        self.assertFalse(token_present("03026A","03026AX"))
        self.assertTrue(token_present("03026A","#03026A /"))
    def test_variant_exact(self):
        self.assertEqual(match_product(product(),[{"id":1,"variants":[{"sku":"03026A"}]}])["state"],"MATCH")
    def test_variant_suffix_not_match(self):
        self.assertEqual(match_product(product(),[{"variants":[{"title":"03026AX"}]}])["state"],"NO_MATCH")
    def test_accessory_mention_review(self):
        self.assertEqual(match_product(product(),[{"title":"Other machine","body_html":"Accessory for 03026A"}])["state"],"REVIEW")
    def test_scattered_words_not_duplicate(self):
        p=dict(product(),product_name_en="Gray Scale Color Change")
        self.assertEqual(match_product(p,[{"body_html":"Gray equipment. Color printing. Scale weight. Change parts."}])["state"],"NO_MATCH")
    def test_core_ambiguous(self):
        self.assertEqual(match_product(product(),[{"title":"03026 manual"}])["state"],"REVIEW")
    def test_real_match_after_review(self):
        result=match_product(product(),[{"body_html":"03026A","id":1},{"variants_skus":["03026A"],"id":2}])
        self.assertEqual(result["id"],2)
    def test_empty_sku_review(self):
        self.assertEqual(match_product({},[])["state"],"REVIEW")
    def test_escape_html(self):
        s=render_product(dict(product(),description="<script>alert(1)</script>"))
        self.assertNotIn("<script>",s)
    def test_seven_blocks(self):
        self.assertEqual(render_product(product()).count('data-bis-block='),7)
    def test_no_invented_highlights(self):
        s=render_product(product())
        self.assertNotIn("CO/CQ",s)
        self.assertNotIn("chính hãng",s)
    def test_small_spec_merges(self):
        s=render_product(dict(product(),specifications={"Nguồn điện":"220V"}))
        self.assertIn("220V",s)
        self.assertNotIn("<table",s)
    def test_two_specs_table(self):
        s=render_product(dict(product(),specifications={"A":"1","B":"2"}))
        self.assertIn("width:39%",s)
        self.assertIn("width:61%",s)
    def test_source_validation(self):
        self.assertTrue(validate_product(product(),"03026A AATCC Technical Manual")["passed"])
    def test_quote_wrong_blocks(self):
        self.assertFalse(validate_product(product(),"03026A Other text")["passed"])
    def test_source_absent_blocks(self):
        self.assertFalse(validate_product(product())["passed"])
    def test_certificate_claim_blocks(self):
        p=dict(product(),description="CO/CQ chính hãng")
        p["custom_html"]=render_product(p)
        self.assertFalse(validate_product(p,"03026A AATCC Technical Manual")["passed"])
    def test_seo_no_fake_fallback(self):
        seo=seo_draft(product())
        self.assertNotIn("CO/CQ",seo["meta_description"])
        self.assertEqual(seo["_quality"]["state"],"NEEDS_REVIEW")

class FileTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.pdf=self.root/"catalogue_sample.pdf"
        with pymupdf.open() as d:
            p=d.new_page()
            p.insert_text((40,40),"03026A AATCC Technical Manual")
            p.insert_image(pymupdf.Rect(40,60,240,260),stream=image_bytes((600,600)))
            p=d.new_page()
            p.insert_text((40,40),"03026AX Other")
            d.save(self.pdf)
    def tearDown(self):
        self.tmp.cleanup()
    def test_pdf_candidates_exact_page(self):
        rows=candidates(self.pdf,"03026A")
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["page"],1)
    def test_zip_provenance(self):
        import zipfile
        z=zipfile.ZipFile(io.BytesIO(archive(candidates(self.pdf,"03026A"))))
        self.assertIn("provenance.json",z.namelist())
    def test_crop_coordinates(self):
        with Image.open(io.BytesIO(render_region(self.pdf,1,(0,0,50,50)))) as im:
            self.assertGreater(im.width,500)
        with self.assertRaises(ValueError):
            render_region(self.pdf,1,(90,0,20,100))
    def test_blank_sku(self):
        with self.assertRaises(ValueError):
            candidates(self.pdf,"")
    def test_invalid_image(self):
        with self.assertRaises(Exception):
            checked_image(b"<html>not an image</html>")
    def test_no_upscale_thumbnail(self):
        src=self.root/"s.png";src.write_bytes(image_bytes((250,250)))
        with self.assertRaises(ValueError):
            studio_draft(src,src,self.root/"out.png")
    def test_studio_dimensions_source_unchanged(self):
        src=self.root/"s.png";bg=self.root/"bg.png"
        image=Image.new("RGBA",(700,700),(0,0,0,0))
        ImageDraw.Draw(image).rectangle((100,100,600,600),fill="red")
        image.save(src);bg.write_bytes(image_bytes())
        old=src.read_bytes()
        studio_draft(src,bg,self.root/"out.png")
        self.assertEqual(src.read_bytes(),old)
        with Image.open(self.root/"out.png") as im:
            self.assertEqual(im.size,(1254,1254))
            self.assertEqual(im.getpixel((627,627)),(255,0,0))
    def test_candidate_ranking_not_verification(self):
        rows=rank_candidates([{"image_url":"https://example.com/03026A.png","title":"AATCC Technical Manual"},
                              {"image_url":"https://example.com/cat.png"}],"03026A","Technical Manual","AATCC")
        self.assertTrue(rows[0]["sku_evidence"])
        self.assertEqual(rows[0]["status"],"NEEDS_REVIEW")
    def test_job_error_persisted(self):
        r=JobRunner(self.root)
        with self.assertRaises(ValueError):
            r.run("bad",{},lambda:(_ for _ in ()).throw(ValueError("fail")))
        self.assertEqual(r.list_jobs()[0]["state"],"FAILED")
    def test_knowledge_reindex_retires_old_chunks(self):
        from knowledge_index import index_pdf
        index_pdf(self.root,self.pdf)
        self.assertIn("03026AX",MemoryStore(self.root).context("03026AX",max_chars=20000))
        self.pdf.unlink()
        with pymupdf.open() as d:
            page=d.new_page()
            page.insert_text((40,40),"New source content replacing old catalogue page entirely")
            d.save(self.pdf)
        index_pdf(self.root,self.pdf)
        self.assertNotIn("03026AX",MemoryStore(self.root).context("03026AX",max_chars=20000))

    def test_gemini_uses_reference_images_and_keeps_pending(self):
        from types import SimpleNamespace
        from gemini_studio import edit_studio
        a=self.root/"source.png";b=self.root/"backdrop.png"
        a.write_bytes(image_bytes((800,800)));b.write_bytes(image_bytes())
        raw=image_bytes((1024,1024))
        fake=Mock()
        fake.interactions.create.return_value=SimpleNamespace(output_image=SimpleNamespace(data=base64.b64encode(raw).decode()))
        with patch("google.genai.Client",return_value=fake):
            result=edit_studio(a,b,self.root/"draft.png","03026A")
        self.assertEqual(result["status"],"PENDING_REVIEW")
        self.assertEqual(len(fake.interactions.create.call_args.kwargs["input"]),3)
        fake.close.assert_called_once()

    def prepare(self):
        p=product()
        p["status"]="APPROVED"
        p["_review_hash"]=fingerprint({k:v for k,v in p.items() if not k.startswith("_")})
        f=self.root/"final.png";f.write_bytes(image_bytes())
        import hashlib
        atomic_json(self.root/"Google_Drive_Storage"/"image_review_manifest.json",
                    {"03026A":{"status":"APPROVED","final_image":str(f),
                               "approved_sha256":hashlib.sha256(f.read_bytes()).hexdigest()}})
        return p
    def client(self):
        c=Mock()
        def response(data):
            r=Mock();r.json.return_value=data;return r
        c.get.side_effect=lambda url,**kwargs:response({"products":[]} if url.endswith("/products.json") else
            {"product":{"id":12,"published_at":None,"variants":[{"sku":"03026A"}],"images":[{"id":1}]}})
        c.post.return_value=response({"product":{"id":12,"published_at":None}})
        return c
    def publish(self,p,c,enabled=True):
        with patch("safe_publish.sync_configured",return_value={"state":"synced"}):
            return publish_one(p,self.root,enabled=enabled,headers={},session=c)
    def test_checkpoint_failure_zero_post(self):
        p=self.prepare();c=self.client()
        with patch("safe_publish.sync_configured",return_value={"state":"pending"}):
            result=publish_one(p,self.root,enabled=True,headers={},session=c)
        self.assertEqual(result["status"],"BLOCKED")
        c.post.assert_not_called()

    def test_disabled_zero_network(self):
        c=self.client();self.assertEqual(self.publish(self.prepare(),c,False)["status"],"BLOCKED")
        c.get.assert_not_called();c.post.assert_not_called()
    def test_unapproved_zero_post(self):
        p=self.prepare();p["status"]="EXTRACTED_UNVERIFIED";c=self.client()
        self.assertEqual(self.publish(p,c)["status"],"BLOCKED");c.post.assert_not_called()
    def test_edit_after_approval_blocks(self):
        p=self.prepare();p["description"]="Changed";c=self.client()
        self.assertEqual(self.publish(p,c)["status"],"BLOCKED");c.post.assert_not_called()
    def test_image_change_blocks(self):
        p=self.prepare();(self.root/"final.png").write_bytes(image_bytes((1000,1000)))
        c=self.client();self.assertEqual(self.publish(p,c)["status"],"BLOCKED");c.post.assert_not_called()
    def test_live_scan_error_blocks(self):
        p=self.prepare();c=self.client();c.get.side_effect=TimeoutError()
        self.assertEqual(self.publish(p,c)["status"],"BLOCKED");c.post.assert_not_called()
    def test_success_hidden_readback_and_idempotent(self):
        p=self.prepare();c=self.client()
        self.assertEqual(self.publish(p,c)["status"],"SUCCESS")
        self.assertFalse(c.post.call_args.kwargs["json"]["product"]["published"])
        self.assertTrue(c.post.call_args.kwargs["json"]["product"]["images"][0]["attachment"])
        self.assertEqual(self.publish(p,c)["status"],"ALREADY_CREATED")
        self.assertEqual(c.post.call_count,1)
    def test_uncertain_never_reposts(self):
        p=self.prepare();c=self.client();c.post.side_effect=TimeoutError()
        self.assertEqual(self.publish(p,c)["status"],"RECONCILE_REQUIRED")
        self.assertEqual(self.publish(p,c)["status"],"RECONCILE_REQUIRED")
        self.assertEqual(c.post.call_count,1)
    def test_live_duplicate_blocks(self):
        p=self.prepare();c=self.client();r=Mock()
        r.json.return_value={"products":[{"variants":[{"sku":"03026A"}],"id":99}]}
        c.get.side_effect=None;c.get.return_value=r
        self.assertEqual(self.publish(p,c)["status"],"BLOCKED");c.post.assert_not_called()
    def test_readback_failure_uncertain(self):
        p=self.prepare();c=self.client();r=Mock();r.json.return_value={"products":[]}
        v=Mock();v.json.return_value={"product":{"id":12,"published":True}}
        c.get.side_effect=[r,v]
        self.assertEqual(self.publish(p,c)["status"],"RECONCILE_REQUIRED")
    def test_existing_lock_blocks(self):
        p=self.prepare();mem=MemoryStore(self.root)
        (mem.root/"publish.lock").write_text("other process")
        c=self.client();self.assertEqual(self.publish(p,c)["status"],"BLOCKED");c.post.assert_not_called()

if __name__=="__main__":
    unittest.main()
