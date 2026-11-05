"""
Unit tests for AGY_009 Flow AI & Google Drive Image Architecture.
Verifies:
- Exact SKU boundary matching (prevents 03026A matching 03026AB)
- Natural numerical sort order (1, 2, ..., 10)
- Candidate image extraction from catalogue PDF
- Deduplication via SHA256 when saving raw images
- Confirmation of completed image set with SHA256 change detection
- Calibration memory recording
- Flow AI export package contents
"""
import unittest
import tempfile
import shutil
import json
import hashlib
import io
import zipfile
from pathlib import Path

from raw_image_store import (
    matches_sku_exact,
    natural_sort_key,
    extract_sku_page_candidates,
    extract_pdf_batch,
    save_raw_product_images,
    list_raw_images,
)
from completed_images import (
    scan_completed_composites,
    confirm_completed_image_set,
    export_flow_ai_package,
    is_legacy_filename,
)
from persistent_memory import MemoryStore

class TestFlowDriveImages(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.raw_dir = self.temp_dir / "Google_Drive_Storage" / "4_Product_Images" / "raw"
        self.final_dir = self.temp_dir / "Google_Drive_Storage" / "6_Final_Composites"
        self.bg_dir = self.temp_dir / "Google_Drive_Storage" / "5_Studio_Backgrounds"
        self.mem_dir = self.temp_dir / "Google_Drive_Storage" / "8_AI_Memory"
        for d in [self.raw_dir, self.final_dir, self.bg_dir, self.mem_dir]:
            d.mkdir(parents=True, exist_ok=True)
        self.memory = MemoryStore(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_exact_sku_boundary_matching(self):
        # Must match
        self.assertTrue(matches_sku_exact("03026A_1.png", "03026A"))
        self.assertTrue(matches_sku_exact("03026A_2.jpg", "03026A"))
        self.assertTrue(matches_sku_exact("03026A_10.webp", "03026A"))
        self.assertTrue(matches_sku_exact("03026A_final.jpg", "03026A"))
        self.assertTrue(matches_sku_exact("03026A.png", "03026A"))
        self.assertTrue(matches_sku_exact("03026A_approved_abcdef123456.png", "03026A"))

        # Must NOT match
        self.assertFalse(matches_sku_exact("03026AB_1.png", "03026A"))
        self.assertFalse(matches_sku_exact("03026A1.png", "03026A"))
        self.assertFalse(matches_sku_exact("03026B_1.png", "03026A"))
        self.assertFalse(matches_sku_exact("03026A_draft_unrelated.png", "03026A"))

    def test_natural_numerical_sort(self):
        filenames = [
            "03026A_10.png",
            "03026A_1.png",
            "03026A_2.jpg",
            "03026A_20.png",
            "03026A_3.webp"
        ]
        sorted_names = sorted(filenames, key=natural_sort_key)
        self.assertEqual(sorted_names, [
            "03026A_1.png",
            "03026A_2.jpg",
            "03026A_3.webp",
            "03026A_10.png",
            "03026A_20.png"
        ])

    def test_legacy_filename_detection(self):
        self.assertTrue(is_legacy_filename("03026A_final.jpg", "03026A"))
        self.assertTrue(is_legacy_filename("03026A.png", "03026A"))
        self.assertTrue(is_legacy_filename("03026A_approved_123.png", "03026A"))
        self.assertFalse(is_legacy_filename("03026A_1.png", "03026A"))
        self.assertFalse(is_legacy_filename("03026A_2.jpg", "03026A"))

    def test_save_raw_deduplication(self):
        from PIL import Image
        def png(color):
            out = io.BytesIO(); Image.new('RGB', (40,40), color).save(out, format='PNG'); return out.getvalue()
        sample_bytes1 = png('red')
        sample_bytes2 = png('blue')

        item1 = {
            "image_bytes": sample_bytes1,
            "sha256": hashlib.sha256(sample_bytes1).hexdigest(),
            "width": 300,
            "height": 300,
            "page": 7,
            "xref": 101,
            "bbox": [10, 10, 310, 310]
        }
        item2 = {
            "image_bytes": sample_bytes2,
            "sha256": hashlib.sha256(sample_bytes2).hexdigest(),
            "width": 400,
            "height": 400,
            "page": 7,
            "xref": 102,
            "bbox": [10, 320, 310, 620]
        }

        # 1. Save item1 and item2
        res1 = save_raw_product_images(self.temp_dir, "03026A", [item1, item2], memory=self.memory)
        self.assertEqual(res1["saved_count"], 2)
        self.assertTrue((self.raw_dir / "03026A_1.png").exists())
        self.assertTrue((self.raw_dir / "03026A_2.png").exists())

        # 2. Re-saving item1 must NOT create 03026A_3.png (anti-collision dedup)
        res2 = save_raw_product_images(self.temp_dir, "03026A", [item1], memory=self.memory)
        self.assertEqual(res2["records"][0]["deduplicated"], True)
        self.assertEqual(res2["records"][0]["filename"], "03026A_1.png")
        self.assertFalse((self.raw_dir / "03026A_3.png").exists())

        # 3. Check calibration memory event
        events = self.memory.events()
        cal_events = [e for e in events if e.get("key") == "image-calibration:03026A"]
        self.assertTrue(len(cal_events) >= 1)
        content = json.loads(cal_events[0]["content"])
        self.assertIn("Bộ nhớ hiệu chỉnh", content["description"])
        self.assertIn(hashlib.sha256(sample_bytes1).hexdigest(), content["accepted_hashes"])

    def test_completed_composites_confirmation_and_tampering(self):
        # Create mock completed files in 6_Final_Composites
        img1_path = self.final_dir / "03026A_1.png"
        img2_path = self.final_dir / "03026A_2.jpg"
        img1_path.write_bytes(b"COMPOSITE_1_ORIGINAL")
        img2_path.write_bytes(b"COMPOSITE_2_ORIGINAL")

        # Create unrelated file that should NOT match
        unrelated_path = self.final_dir / "03026AB_1.png"
        unrelated_path.write_bytes(b"DIFFERENT_PRODUCT")

        # 1. Scan composites for 03026A
        found = scan_completed_composites(self.temp_dir, "03026A")
        filenames = [f["filename"] for f in found]
        self.assertIn("03026A_1.png", filenames)
        self.assertIn("03026A_2.jpg", filenames)
        self.assertNotIn("03026AB_1.png", filenames)

        # 2. Confirm image set with 03026A_1.png as primary
        items_to_confirm = [
            {"filename": "03026A_1.png", "sha256": hashlib.sha256(img1_path.read_bytes()).hexdigest()},
            {"filename": "03026A_2.jpg", "sha256": hashlib.sha256(img2_path.read_bytes()).hexdigest()}
        ]
        conf_res = confirm_completed_image_set(self.temp_dir, "03026A", items_to_confirm, primary_filename="03026A_1.png", memory=self.memory)
        self.assertEqual(conf_res["status"], "APPROVED_SET")
        self.assertEqual(conf_res["primary_image"], "03026A_1.png")

        # 3. Rescan: both should show confirmed, no mismatch
        found_after = scan_completed_composites(self.temp_dir, "03026A")
        item1_info = next(f for f in found_after if f["filename"] == "03026A_1.png")
        self.assertTrue(item1_info["is_confirmed"])
        self.assertTrue(item1_info["is_primary"])
        self.assertFalse(item1_info["hash_mismatch"])

        # 4. TAMPER TEST: Modify 03026A_1.png on disk
        img1_path.write_bytes(b"COMPOSITE_1_MODIFIED_EXTERNALLY")

        # 5. Rescan: must flag hash_mismatch == True
        found_tampered = scan_completed_composites(self.temp_dir, "03026A")
        tampered_info = next(f for f in found_tampered if f["filename"] == "03026A_1.png")
        self.assertTrue(tampered_info["hash_mismatch"])
        self.assertIsNotNone(tampered_info["warning"])

    def test_flow_ai_package_export(self):
        # Create raw image and backdrop
        raw_img = self.raw_dir / "03026A_1.png"
        raw_img.write_bytes(b"RAW_PRODUCT_IMAGE_DATA")
        bg_img = self.bg_dir / "BIS_BACKDROP_1254.png"
        bg_img.write_bytes(b"STUDIO_BACKDROP_IMAGE_DATA")

        zip_bytes = export_flow_ai_package(self.temp_dir, "03026A")
        self.assertGreater(len(zip_bytes), 100)

        import zipfile
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
            names = z.namelist()
            self.assertIn("FLOW_AI_PROMPT.txt", names)
            self.assertIn("FLOW_AI_METADATA.json", names)
            self.assertIn("01_RAW_03026A_1.png", names)
            self.assertIn("02_BACKDROP_BIS_BACKDROP_1254.png", names)
            prompt_content = z.read("FLOW_AI_PROMPT.txt").decode("utf-8")
            self.assertIn("70% to 80%", prompt_content)
            self.assertIn("ZERO HALLUCINATION", prompt_content)
            self.assertIn("03026A", prompt_content)


    def test_reject_stale_approval_wrong_sku_and_path(self):
        path = self.final_dir / '03026A_1.png'; path.write_bytes(b'before')
        old = hashlib.sha256(path.read_bytes()).hexdigest()
        path.write_bytes(b'after')
        for filename, digest in [('03026A_1.png',old),('../secret.png',old),('03026AB_1.png',old)]:
            with self.assertRaises(ValueError):
                confirm_completed_image_set(self.temp_dir,'03026A',[{'filename':filename,'sha256':digest}],filename)
        self.assertFalse((self.temp_dir/'Google_Drive_Storage/image_review_manifest.json').exists())
        for name in ['03026A_1_other.png','03026A_final_other.png','03026A_approved_abcdef_extra.png']:
            self.assertFalse(matches_sku_exact(name,'03026A'))

    def test_package_rejects_outside_and_wrong_sku(self):
        (self.bg_dir/'BIS_BACKDROP_1254.png').write_bytes(b'bg')
        (self.raw_dir/'03026AB_1.png').write_bytes(b'other')
        for name in ['../secret.png','03026AB_1.png']:
            with self.assertRaises(ValueError):
                export_flow_ai_package(self.temp_dir,'03026A',[name])

    def test_jpeg_saved_as_real_png_and_no_false_negative_learning(self):
        from PIL import Image
        out=io.BytesIO(); Image.new('RGB',(70,30),'green').save(out,format='JPEG')
        item={'image_bytes':out.getvalue()}
        res=save_raw_product_images(self.temp_dir,'03026A',[item],all_presented_items=[{'sha256':'unrelated'}],memory=self.memory)
        with Image.open(self.raw_dir/res['records'][0]['filename']) as image:
            self.assertEqual(image.format,'PNG'); self.assertEqual(image.size,(70,30))
        self.assertTrue(save_raw_product_images(self.temp_dir,'03026A',[item])['records'][0]['deduplicated'])
        event=[e for e in self.memory.events() if e['key']=='image-calibration:03026A'][-1]
        self.assertEqual(json.loads(event['content'])['rejected_hashes'],[])

    def test_pdf_batch_cursor_and_bounds(self):
        import pymupdf
        from PIL import Image
        pdf=self.temp_dir/'test.pdf'; doc=pymupdf.open(); page=doc.new_page()
        for n,color in enumerate(['red','green','blue']):
            out=io.BytesIO(); Image.new('RGB',(20,20),color).save(out,format='PNG')
            page.insert_image(pymupdf.Rect(n*30,0,n*30+20,20),stream=out.getvalue())
        doc.save(pdf); doc.close()
        first=extract_pdf_batch(pdf,1,1,2)
        second=extract_pdf_batch(pdf,first['next_page'],1,2,first['next_offset'])
        self.assertEqual(len(first['images'])+len(second['images']),3)
        self.assertIsNone(second['next_page'])
        with self.assertRaises(ValueError): extract_pdf_batch(pdf,2)

if __name__ == "__main__":
    unittest.main()
