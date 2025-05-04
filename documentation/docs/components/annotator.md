# Annotator

The Annotator component is responsible for creating visual annotations of the detected fields in resume documents. It highlights key information like names, contact details, and job titles directly on the document image, making it easy to verify extraction accuracy.

## Overview

The Resume Annotator provides the following capabilities:

1. **Visual Field Identification**: Highlights detected fields on the document
2. **Field Labeling**: Adds text labels for each detected field
3. **Multi-Page Support**: Annotates all pages in multi-page PDFs
4. **Color-Coded Categories**: Uses different colors for different field types
5. **Confidence Visualization**: Shows extraction confidence through box styles

## Architecture

The Annotator integrates with other components in the system:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   OCR Service   │      │    Extracted    │      │    Annotator    │
│  (Field Data)   │─────▶│    JSON Data    │─────▶│     Engine      │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                                          │
                                                          │
                                                          ▼
                                               ┌─────────────────────┐
                                               │  Annotated Images   │
                                               │  (PNG Output Files) │
                                               └─────────────────────┘
```

## Key Components

### ResumeAnnotator Class

The `ResumeAnnotator` class in `annotator.py` is the main class that handles:

- Loading document images (from PDF or PNG)
- Finding text locations using OCR
- Matching extracted fields to text locations
- Creating annotated images

```python
class ResumeAnnotator:
    """Resume annotator using EasyOCR with support for images and PDFs."""

    def __init__(self, file_path: str, json_data: dict):
        self.file_path = file_path
        self.json_data = json_data
        self.field_coordinates: Dict[str, Tuple[float, float, float, float]] = {}
        self.is_pdf = file_path.lower().endswith((".pdf", ".PDF"))
        self.images = self._load_images()
        self.img_height: Optional[int] = None
        self.img_width: Optional[int] = None
        self.reader = easyOCR.Reader(["en"], gpu=self._is_gpu_available())
        self.tfidf_vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        self.field_colors = config.FIELD_COLORS
        self.default_color = config.DEFAULT_COLOR
```

### Image Processing

The Annotator converts documents to images for processing:

- PDFs are converted to images using PyMuPDF
- Images are processed as-is
- Document structure is preserved for multi-page documents

```python
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
```

### Text Location Detection

The Annotator uses EasyOCR to find text locations in the document:

```python
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
```

### Field Matching

To match extracted fields to text locations, the Annotator employs two primary methods:

1. **TF-IDF Similarity**: For general text matching and name fields
   ```python
   def find_tfidf_match(self, target: str, candidates: dict) -> tuple:
       """Find matching text using TF-IDF similarity."""
       target = target.lower()
       # Implementation details...
       texts = [target] + cand_texts
       tfidf = self.tfidf_vectorizer.fit_transform(texts)
       sims = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()
       best = int(np.argmax(sims))
       return (cand_texts[best], candidates[cand_texts[best]], sims[best])
   ```

2. **Sequence Matching**: For structured fields like email and phone
   ```python
   def find_sequence_match(self, target: str, candidates: dict, field_type: str) -> tuple:
       """Find matching text using sequence matching."""
       # Implementation details...
       clean_target = self._preprocess_field(target, field_type)
       for cand, coords in candidates.items():
           clean_cand = self._preprocess_field(cand, field_type)
           ratio = SequenceMatcher(None, clean_target, clean_cand).ratio()
           ratio = self._boost_similarity(clean_target, clean_cand, ratio, field_type)
           # Find best match...
   ```

### Drawing Annotations

Once fields are matched to locations, the Annotator draws bounding boxes and labels:

```python
def _draw_annotation(self, image, field, norm_coords, thickness, text_size):
    """Draw annotation box and label for a field."""
    h, w = image.shape[:2]
    x1, y1, x2, y2 = self.denormalize_bbox(norm_coords, w, h)
    
    # Get the field type (extract base field name before any underscore)
    field_type = field.split('_')[0]
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
```

## Field Types and Colors

The Annotator uses a color-coding system to distinguish different field types:

| Field Type | Color | RGB Value |
|------------|-------|-----------|
| Name | Blue | (0, 0, 255) |
| Email | Orange | (255, 165, 0) |
| Phone | Green | (0, 255, 0) |
| Location | Red | (255, 0, 0) |
| JobTitle | Teal | (0, 128, 128) |
| Other | Indigo | (75, 0, 130) |

These colors can be customized in the `config.py` file.

## Workflow

The annotation process follows these steps:

1. **Document Loading**: The PDF or PNG file is loaded
2. **Text Extraction**: EasyOCR extracts text locations from each page
3. **Field Matching**: Extracted fields are matched to text locations
4. **Annotation Drawing**: Bounding boxes and labels are drawn on the document
5. **Output Generation**: Annotated images are saved to the annotations directory

```python
def annotate_document(self, output_dir: str, box_thickness: int = 2, text_size: float = 0.4):
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
```

## Multi-Page Handling

For multi-page PDFs, the Annotator:

1. Converts each page to an image
2. Creates a subdirectory for all annotations
3. Processes each page with its specific JSON data
4. Saves annotated images with page numbers in the filenames

```python
if file_path.lower().endswith((".pdf", ".PDF")):
    try:
        doc = fitz.open(file_path)
        annotator = ResumeAnnotator(file_path, {})  # Will override JSON per page
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
            output_path = os.path.join(output_dir, f"{base}_page{page_num + 1}.png")
            annotator.annotate_page(img, page_data, output_path)
        doc.close()
```

## Precision Optimization

The Annotator uses several techniques to improve matching precision:

1. **Field-Specific Preprocessing**: Special handling for emails, phone numbers
2. **Similarity Boosting**: Increases match confidence for specific patterns
3. **Whole Word Matching**: Prevents partial word matches
4. **Normalized Coordinates**: Uses relative coordinates for resolution independence

```python
def _preprocess_field(self, text: str, field_type: str) -> str:
    """Preprocess field text for matching."""
    if field_type == "Email":
        return re.sub(r"[\s]", "", text)
    elif field_type == "Phone":
        return re.sub(r"[\s\-\(\)\+]", "", text)
    return text

def _boost_similarity(self, target: str, cand: str, base_ratio: float, field_type: str) -> float:
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
```

## Usage Example

To use the Annotator component directly:

```python
from services.annotator import annotate_resume

# Annotate a resume using extracted JSON data
annotate_resume(
    file_path="path/to/resume.pdf",
    json_file="path/to/extracted_data.json",
    output_dir="path/to/output_directory"
)
```

Or through the API:

```bash
# Upload and process with annotation
curl -X POST -F "file=@resume.pdf" -F "annotate=true" http://localhost:8000/api/resumes/upload-and-process
```

## Next Steps

- **[OCR Service](ocr-service.md)**: Learn about the text extraction component
- **[Processing](processing.md)**: Explore the data validation and processing pipeline
- **[API Endpoints](../api/endpoints.md)**: See how to use the Annotator via API