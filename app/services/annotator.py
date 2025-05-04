import json
import os
import re
import sys
from difflib import SequenceMatcher

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import cv2
import easyocr
import fitz  # PyMuPDF
import numpy as np
from core.settings import get_settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


class ResumeAnnotator:
    """Resume annotator using EasyOCR with support for images and PDFs."""

    def __init__(self, file_path: str, json_data: dict):
        self.file_path = file_path
        self.json_data = json_data
        self.field_coordinates: dict[str, tuple[float, float, float, float]] = {}
        self.is_pdf = file_path.lower().endswith((".pdf", ".PDF"))
        self.images = self._load_images()
        self.img_height: int | None = None
        self.img_width: int | None = None
        self.reader = easyocr.Reader(["en"], gpu=self._is_gpu_available())
        self.tfidf_vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        self.field_colors = config.FIELD_COLORS
        self.default_color = config.DEFAULT_COLOR
        self.tfidf_fields = ["Name"]
        self.sequence_matcher_fields = ["Email", "Phone", "Location", "JobTitle"]
        # Fields we want to annotate
        self.annotate_fields = ["Name", "Email", "Phone", "Location", "JobTitle"]

    def _is_gpu_available(self):
        """Check if GPU is available for OCR."""
        try:
            settings = get_settings()
            if not settings.USE_GPU:
                return False

            import torch

            return torch.cuda.is_available()
        except ImportError:
            return False

    def _load_images(self):
        """Load image(s) from file."""
        if not self.is_pdf:
            img = cv2.imread(self.file_path)
            if img is None:
                raise ValueError(f"Could not read image at {self.file_path}")
            return [img]
        else:
            return self._convert_pdf_to_images()

    def _convert_pdf_to_images(self) -> list:
        """Convert PDF pages to images."""
        doc = fitz.open(self.file_path)
        imgs = []
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            np_img = np.frombuffer(pix.tobytes("png"), np.uint8)
            img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            if img is not None:
                imgs.append(img)
        doc.close()
        return imgs

    @staticmethod
    def normalize_bbox(bbox, w, h):
        """Normalize bounding box coordinates."""
        return (bbox[0] / w, bbox[1] / h, bbox[2] / w, bbox[3] / h)

    @staticmethod
    def denormalize_bbox(norm_bbox, w, h):
        """Denormalize bounding box coordinates."""
        return (
            int(norm_bbox[0] * w),
            int(norm_bbox[1] * h),
            int(norm_bbox[2] * w),
            int(norm_bbox[3] * h),
        )

    def find_text_locations(self, image) -> dict:
        """Find text locations in the image using OCR."""
        h, w = image.shape[:2]
        locs = {}
        for det in self.reader.readtext(image):
            bbox, text = det[0], det[1].lower()
            x1, y1 = min(bbox[0][0], bbox[3][0]), min(bbox[0][1], bbox[1][1])
            x2, y2 = max(bbox[1][0], bbox[2][0]), max(bbox[2][1], bbox[3][1])
            norm_bbox = self.normalize_bbox((int(x1), int(y1), int(x2), int(y2)), w, h)
            locs[text] = norm_bbox
            for word in text.split():
                if len(word) > 2:
                    locs[word] = norm_bbox
        return locs

    def find_tfidf_match(self, target: str, candidates: dict) -> tuple:
        """Find matching text using TF-IDF similarity."""
        target = target.lower()
        if len(target) <= 3:
            for cand, coords in candidates.items():
                if target == cand:
                    return cand, coords, 1.0
                if target in cand:
                    return cand, coords, 0.9
        if not candidates:
            return None, None, 0.0
        cand_texts = list(candidates.keys())
        if len(cand_texts) == 1:
            return cand_texts[0], candidates[cand_texts[0]], 0.8
        try:
            texts = [target] + cand_texts
            tfidf = self.tfidf_vectorizer.fit_transform(texts)
            sims = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()
            best = int(np.argmax(sims))
            return (
                cand_texts[best],
                candidates[cand_texts[best]],
                sims[best],
            )
        except Exception:
            best, best_score, best_coords = None, 0.0, None
            for cand, coords in candidates.items():
                if target in cand or cand in target:
                    ratio = len(min(target, cand, key=len)) / len(
                        max(target, cand, key=len)
                    )
                    if ratio > best_score:
                        best, best_score, best_coords = (
                            cand,
                            ratio,
                            coords,
                        )
            return best, best_coords, best_score

    def find_sequence_match(
        self, target: str, candidates: dict, field_type: str
    ) -> tuple:
        """Find matching text using sequence matching."""
        target = target.lower().strip()
        if target in candidates:
            return target, candidates[target], 1.0
        clean_target = self._preprocess_field(target, field_type)
        best, best_score, best_coords = None, 0.0, None
        for cand, coords in candidates.items():
            clean_cand = self._preprocess_field(cand, field_type)
            ratio = SequenceMatcher(None, clean_target, clean_cand).ratio()
            ratio = self._boost_similarity(clean_target, clean_cand, ratio, field_type)
            if ratio > best_score:
                best, best_score, best_coords = cand, ratio, coords
        return best, best_coords, best_score

    def _preprocess_field(self, text: str, field_type: str) -> str:
        """Preprocess field text for matching."""
        if field_type == "Email":
            return re.sub(r"[\s]", "", text)
        elif field_type == "Phone":
            return re.sub(r"[\s\-\(\)\+]", "", text)
        return text

    def _boost_similarity(
        self,
        target: str,
        cand: str,
        base_ratio: float,
        field_type: str,
    ) -> float:
        """Boost similarity score based on field type and content."""
        if field_type == "Email":
            if "@" in target and "@" in cand:
                return max(base_ratio, 0.8)
        elif field_type == "Phone":
            # Extract digits only from both strings
            dt = "".join(re.findall(r"\d", target))
            dc = "".join(re.findall(r"\d", cand))
            if dt and dc:
                ratio = SequenceMatcher(None, dt, dc).ratio()
                if ratio > 0.7:
                    return max(base_ratio, 0.75 + ratio * 0.2)
        return base_ratio

    def _extract_personal_info(self, json_obj):
        """Extract personal information fields from JSON data."""
        flat = {}
        if "PersonalInfo" in json_obj:
            for k, v in json_obj["PersonalInfo"].items():
                if v and v != "Not Found" and k in self.annotate_fields:
                    flat[k] = v
        return flat

    def _extract_work_info(self, json_obj):
        """Extract only JobTitle from work experience."""
        flat = {}
        if "WorkExperience" in json_obj and isinstance(
            json_obj["WorkExperience"], list
        ):
            for i, work in enumerate(json_obj["WorkExperience"]):
                if (
                    "JobTitle" in work
                    and work["JobTitle"]
                    and work["JobTitle"] != "Not Found"
                ):
                    key = f"JobTitle_{i + 1}" if i > 0 else "JobTitle"
                    flat[key] = work["JobTitle"]
        return flat

    def _flatten_json(self, json_obj):
        """Flatten nested JSON structure to be used for annotation."""
        flat = {}

        # Extract personal info
        personal_info = self._extract_personal_info(json_obj)
        flat.update(personal_info)

        # Extract job titles
        job_titles = self._extract_work_info(json_obj)
        flat.update(job_titles)

        return flat

    def annotate_document(
        self,
        output_dir: str,
        box_thickness: int = 2,
        text_size: float = 0.4,
    ):
        """Annotate the document with field bounding boxes."""
        results = self.process_document()
        os.makedirs(output_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(self.file_path))[0]
        annotated_images = []
        for page in results:
            idx = page["page"]
            annotated = self._annotate_image(
                self.images[idx],
                page["coordinates"],
                box_thickness,
                text_size,
            )
            annotated_images.append(annotated)
            fname = (
                f"{base}_page{idx + 1}.png"
                if len(self.images) > 1
                else f"{base}_annotated.png"
            )
            cv2.imwrite(os.path.join(output_dir, fname), annotated)
        return annotated_images

    def _annotate_image(self, image, field_coords, box_thickness, text_size):
        """Annotate a single image with field bounding boxes."""
        img_copy = image.copy()
        for field, norm_coords in field_coords.items():
            self._draw_annotation(
                img_copy, field, norm_coords, box_thickness, text_size
            )
        return img_copy

    def _draw_annotation(self, image, field, norm_coords, thickness, text_size):
        """Draw annotation box and label for a field."""
        h, w = image.shape[:2]
        x1, y1, x2, y2 = self.denormalize_bbox(norm_coords, w, h)

        # Get the field type (extract base field name before any underscore)
        field_type = field.split("_")[0]
        color = self.field_colors.get(field_type, self.default_color)

        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
        label_y = int(y1 - 10) if y1 > 30 else int(y2 + 20)
        cv2.putText(
            image,
            field,
            (x1, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            text_size,
            color,
            2,
        )

    def process_document(self):
        """Process the document to find field coordinates."""
        results = []
        for idx, img in enumerate(self.images):
            self.img_height, self.img_width = img.shape[:2]
            locs = self.find_text_locations(img)

            # For multi-page PDFs, we need to get the page-specific JSON data
            if self.is_pdf and len(self.images) > 1:
                page_key = f"page{idx + 1}"
                if "pages" in self.json_data and page_key in self.json_data["pages"]:
                    page_json = self.json_data["pages"][page_key]
                else:
                    page_json = self.json_data
            else:
                page_json = self.json_data

            # Flatten the JSON data for this page
            flat_json = self._flatten_json(page_json)

            self.field_coordinates = self._match_fields(locs, flat_json)
            results.append(
                {
                    "page": idx,
                    "coordinates": self.field_coordinates.copy(),
                    "dimensions": (self.img_width, self.img_height),
                }
            )
        return results

    def _match_fields(self, text_locations: dict, flat_json: dict) -> dict:
        """Match fields in the JSON data to text locations."""
        coords = {}

        for field, val in flat_json.items():
            # Only process the fields we want to annotate
            field_type = field.split("_")[0]
            if field_type not in self.annotate_fields:
                continue

            val_str = str(val).lower().strip()
            if not val_str:
                continue

            if val_str in text_locations:
                coords[field] = text_locations[val_str]
                continue

            # Determine which matching method to use based on field type
            if field_type in self.tfidf_fields:
                _, coord, score = self.find_tfidf_match(val_str, text_locations)
            elif field_type in self.sequence_matcher_fields:
                _, coord, score = self.find_sequence_match(
                    val_str, text_locations, field_type
                )
            else:
                _, coord, score = self.find_tfidf_match(val_str, text_locations)

            # Only include fields with a good match score
            if score >= 0.7 and coord:
                coords[field] = coord
        return coords

    def annotate_page(
        self,
        image,
        page_json,
        output_path,
        box_thickness=2,
        text_size=0.6,
    ):
        """Annotate a single page."""
        original_json = self.json_data
        self.json_data = page_json
        locs = self.find_text_locations(image)
        flat_json = self._flatten_json(page_json)
        field_coords = self._match_fields(locs, flat_json)
        annotated = self._annotate_image(image, field_coords, box_thickness, text_size)
        cv2.imwrite(output_path, annotated)
        self.json_data = original_json
        return annotated


def annotate_resume(file_path: str, json_file: str, output_dir: str) -> None:
    """
    Annotate a resume file using extracted JSON data.

    Args:
        file_path: Path to the resume file (PDF or PNG)
        json_file: Path to the extracted JSON data file
        output_dir: Directory to save annotated images
    """
    with open(json_file) as f:
        json_data = json.load(f)
    os.makedirs(output_dir, exist_ok=True)

    if "pages" in json_data:
        if file_path.lower().endswith((".pdf", ".PDF")):
            try:
                doc = fitz.open(file_path)
                annotator = ResumeAnnotator(
                    file_path, {}
                )  # Will override JSON per page
                for page_num in range(len(doc)):
                    page_key = f"page{page_num + 1}"
                    if page_key not in json_data["pages"]:
                        continue
                    page_data = json_data["pages"][page_key]
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img = cv2.imdecode(
                        np.frombuffer(pix.tobytes("png"), np.uint8),
                        cv2.IMREAD_COLOR,
                    )
                    base = os.path.splitext(os.path.basename(file_path))[0]
                    output_path = os.path.join(
                        output_dir, f"{base}_page{page_num + 1}.png"
                    )
                    annotator.annotate_page(img, page_data, output_path)
                doc.close()
            except Exception as e:
                print(f"Error annotating multi-page PDF: {e}")
                ResumeAnnotator(file_path, json_data).annotate_document(output_dir)
        else:
            page_data = json_data["pages"].get("page1", {})
            ResumeAnnotator(file_path, page_data).annotate_document(output_dir)
    else:
        ResumeAnnotator(file_path, json_data).annotate_document(output_dir)
