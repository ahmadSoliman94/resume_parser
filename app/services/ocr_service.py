import json
import os
import re
import sys
import tempfile
import time
from typing import Any

import config
import cv2
import fitz  # PyMuPDF
from autogen import AssistantAgent, UserProxyAgent, register_function
from dependencies import get_model_and_processor
from qwen_vl_utils import process_vision_info
from services.processing import validate_cv_data

from app.dependencies import get_autogen_config
from app.services.annotator import annotate_resume

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


def doc_parser(file_path: str) -> str:
    """
    Extract text from the resume document and return the JSON output.
    For multi-page PDFs, keep each page's data separate.

    Args:
        file_path: Path to the resume file (PDF, PNG, or DOCX)

    Returns:
        JSON string with extracted data
    """
    # Ensure we have an absolute path
    file_path = os.path.abspath(file_path)

    # Verify the file exists
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get model and processor
    model, processor = get_model_and_processor()

    # Handle DOCX files by converting to PDF first
    if file_path.lower().endswith((".docx", ".DOCX")):
        try:
            # Convert DOCX to PDF using a utility function (to be implemented)
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
                tmp_pdf_path = tmp_pdf.name
                # TODO: Implement DOCX to PDF conversion
                # For now, we'll just raise an exception
                raise NotImplementedError("DOCX processing not yet implemented")

            # Process the PDF file
            doc_result = doc_parser(tmp_pdf_path)

            # Clean up temp file
            if os.path.exists(tmp_pdf_path):
                os.remove(tmp_pdf_path)

            return doc_result

        except Exception as e:
            # Preserve original exception context with 'from e'
            raise Exception(f"Error processing DOCX file: {str(e)}") from e

    # Check if the file is a PDF with multiple pages
    if file_path.lower().endswith((".pdf", ".PDF")):
        try:
            doc = fitz.open(file_path)
            # If multiple pages, process each one separately
            if len(doc) > 1:
                all_pages_data: dict[str, dict[str, Any]] = {"pages": {}}

                # Create a temp directory for page images
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Convert each page to image and process
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        zoom = 2.0
                        mat = fitz.Matrix(zoom, zoom)
                        pix = page.get_pixmap(matrix=mat)

                        # Save page as image in temp directory
                        temp_img_path = os.path.join(temp_dir, f"page{page_num}.png")
                        pix.save(temp_img_path)

                        # Verify temp image was created successfully
                        if not os.path.isfile(temp_img_path):
                            raise FileNotFoundError(
                                f"Failed to create temporary image: {temp_img_path}"
                            )

                        # Process this page with VLM
                        page_messages = [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image",
                                        "image": temp_img_path,
                                        "resized_height": 1600,
                                        "resized_width": 960,
                                    },
                                    {
                                        "type": "text",
                                        "text": config.SYSTEM_PROMPT,
                                    },
                                ],
                            }
                        ]

                        text_prompt = processor.apply_chat_template(
                            page_messages,
                            tokenize=False,
                            add_generation_prompt=True,
                        )
                        image_inputs, video_inputs = process_vision_info(page_messages)
                        inputs = processor(
                            text=[text_prompt],
                            images=image_inputs,
                            videos=video_inputs,
                            padding=True,
                            return_tensors="pt",
                        )
                        inputs = inputs.to("cuda")
                        generated_ids = model.generate(**inputs, max_new_tokens=1024)
                        generated_ids_trimmed = [
                            out_ids[len(in_ids) :]
                            for in_ids, out_ids in zip(
                                inputs.input_ids, generated_ids, strict=False
                            )
                        ]
                        output_text = processor.batch_decode(
                            generated_ids_trimmed,
                            skip_special_tokens=True,
                            clean_up_tokenization_spaces=True,
                        )[0]

                        # Extract JSON from page
                        json_match = re.search(r"\{.*\}", output_text, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                            try:
                                page_data = json.loads(json_str)

                                # For the first page, save personal info
                                if page_num == 0:
                                    # Store first page's data as-is
                                    all_pages_data["pages"][f"page{page_num + 1}"] = (
                                        page_data
                                    )
                                else:
                                  
                                    if (
                                        "pages" in all_pages_data
                                        and "page1" in all_pages_data["pages"]
                                    ):
                                        # Preserve personal info from first page
                                        page_data["PersonalInfo"] = all_pages_data[
                                            "pages"
                                        ]["page1"]["PersonalInfo"]

                                    all_pages_data["pages"][f"page{page_num + 1}"] = (
                                        page_data
                                    )
                            except json.JSONDecodeError:
                                all_pages_data["pages"][f"page{page_num + 1}"] = {
                                    "error": "Invalid JSON returned for this page"
                                }

                # Save multi-page result to extraction folder
                base_filename = os.path.splitext(os.path.basename(file_path))[0]
                extraction_file = os.path.join(
                    config.EXTRACTION_DIR, f"{base_filename}.json"
                )

                # Validate the extracted data
                validated_data = validate_cv_data(all_pages_data)

                # Save validated result
                with open(extraction_file, "w", encoding="utf-8") as f:
                    json.dump(
                        validated_data,
                        f,
                        indent=4,
                        ensure_ascii=False,
                    )
                return json.dumps(validated_data, indent=4, ensure_ascii=False)

            else:  # for a single-page PDF
                # Create a temp directory for the page image
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Convert the page to image
                    page = doc.load_page(0)  # Get the first (only) page
                    zoom = 2.0
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat)

                    # Save page as image in temp directory
                    temp_img_path = os.path.join(temp_dir, "page0.png")
                    pix.save(temp_img_path)

                    # Process this image with VLM
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "image": temp_img_path,
                                    "resized_height": 1600,
                                    "resized_width": 960,
                                },
                                {
                                    "type": "text",
                                    "text": config.SYSTEM_PROMPT,
                                },
                            ],
                        }
                    ]

                    # Process with VLM
                    text_prompt = processor.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True
                    )
                    image_inputs, video_inputs = process_vision_info(messages)
                    inputs = processor(
                        text=[text_prompt],
                        images=image_inputs,
                        videos=video_inputs,
                        padding=True,
                        return_tensors="pt",
                    )
                    inputs = inputs.to("cuda")
                    generated_ids = model.generate(**inputs, max_new_tokens=1024)
                    generated_ids_trimmed = [
                        out_ids[len(in_ids) :]
                        for in_ids, out_ids in zip(
                            inputs.input_ids, generated_ids, strict=False
                        )
                    ]
                    output_text = processor.batch_decode(
                        generated_ids_trimmed,
                        skip_special_tokens=True,
                        clean_up_tokenization_spaces=True,
                    )[0]

                    # Extract JSON from response
                    json_match = re.search(r"\{.*\}", output_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        try:
                            data = json.loads(json_str)
                            # Wrap in a pages structure for consistency
                            single_page_data = {"pages": {"page1": data}}

                            base_filename = os.path.splitext(
                                os.path.basename(file_path)
                            )[0]
                            extraction_file = os.path.join(
                                config.EXTRACTION_DIR, f"{base_filename}.json"
                            )
                            with open(extraction_file, "w", encoding="utf-8") as f:
                                json.dump(
                                    single_page_data, f, indent=4, ensure_ascii=False
                                )
                            return json.dumps(
                                single_page_data, indent=4, ensure_ascii=False
                            )
                        except json.JSONDecodeError:
                            return output_text
                    else:
                        return output_text
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            # Continue with regular processing as fallback

    # Regular processing for single page documents (image)
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": file_path,
                    "resized_height": 1600,
                    "resized_width": 960,
                },
                {"type": "text", "text": config.SYSTEM_PROMPT},
            ],
        }
    ]

    text_prompt = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text_prompt],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to("cuda")
    generated_ids = model.generate(**inputs, max_new_tokens=1024)
    generated_ids_trimmed = [
        out_ids[len(in_ids) :]
        for in_ids, out_ids in zip(inputs.input_ids, generated_ids, strict=False)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True,
    )[0]

    json_match = re.search(r"\{.*\}", output_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
        try:
            data = json.loads(json_str)
            # For single page, wrap in a pages structure for consistency
            single_page_data = {"pages": {"page1": data}}

            base_filename = os.path.splitext(os.path.basename(file_path))[0]
            extraction_file = os.path.join(
                config.EXTRACTION_DIR, f"{base_filename}.json"
            )
            with open(extraction_file, "w", encoding="utf-8") as f:
                json.dump(single_page_data, f, indent=4, ensure_ascii=False)
            return json.dumps(single_page_data, indent=4, ensure_ascii=False)
        except json.JSONDecodeError:
            return output_text
    else:
        return output_text


def process_resume(
    file_path: str, use_annotator: bool = True, generate_summary: bool = True
) -> dict[str, Any]:
    """
    Process a resume with OCR, optional annotation, and optional summary generation.

    Args:
        file_path: Path to the resume file
        use_annotator: Whether to annotate the extracted fields
        generate_summary: Whether to generate a professional summary

    Returns:
        Dictionary with processing results and metadata
    """
    start_time = time.time()

    # Ensure we have an absolute path
    file_path = os.path.abspath(file_path)
    file_name = os.path.basename(file_path)
    base_filename = os.path.splitext(file_name)[0]

    # Check if file exists before processing
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Setup autogen
    llm_config = get_autogen_config()
    user = UserProxyAgent(
        name="human",
        llm_config=False,
        is_termination_msg=lambda msg: "TERMINATE" in msg.get("content", ""),
        human_input_mode="NEVER",
        code_execution_config=False,
        max_consecutive_auto_reply=1,
    )

    # Create OCR agent
    ocr_agent = AssistantAgent(
        name="OCR_Agent",
        system_message=(
            "You are an expert OCR agent for resumes and CVs. Your job is to "
            "extract text and structured data from the resume image. You'll "
            "call the 'doc_parser' tool. After extraction, the data will be "
            "processed further as needed."
        ),
        llm_config=llm_config,
        code_execution_config=False,
        max_consecutive_auto_reply=1,
    )

    # Register function
    register_function(
        doc_parser,
        caller=ocr_agent,
        executor=user,
        name="doc_parser",
        description=(
            "Extract text from the resume document and return the JSON "
            "output with page-specific data."
        ),
    )
    ocr_message = (
        f"Please extract the resume data from file '{file_path}' using 'doc_parser'."
    )

    # Run OCR extraction
    _ = user.initiate_chat(
        ocr_agent,
        message=ocr_message,
        clear_history=True,
        silent=True,
    )

    # Setup for annotation and summary
    base_filename = os.path.splitext(os.path.basename(file_path))[0]
    json_file_path = os.path.join(config.EXTRACTION_DIR, f"{base_filename}.json")

    # Generate summary if requested
    if generate_summary:
        summary_agent = AssistantAgent(
            name="Summary_Agent",
            system_message=(
                "You are an expert resume analyst. Your job is to generate a "
                "professional summary based on the extracted resume data. "
                "You'll call the 'generate_summary' tool."
            ),
            llm_config=llm_config,
            code_execution_config=False,
            max_consecutive_auto_reply=1,
        )

        # Register summary function
        register_function(
            generate_summary_from_json,
            caller=summary_agent,
            executor=user,
            name="generate_summary",
            description=(
                "Generate a professional summary based on the extracted resume data."
            ),
        )

        summary_message = (
            f"Please generate a professional summary from the extracted resume data "
            f"in '{json_file_path}' using 'generate_summary'."
        )

        _ = user.initiate_chat(
            summary_agent,
            message=summary_message,
            clear_history=True,
            silent=True,
        )

    # Collect annotation image paths
    annotation_paths = []

    # Handle annotation if requested
    if use_annotator:
        annotator_agent = AssistantAgent(
            name="Annotator_Agent",
            system_message=(
                "You are an expert resume annotator. Using the JSON data "
                "(saved as the extraction result file), your job is to "
                "annotate the resume image with field bounding boxes by "
                "calling the 'annotate_resume' tool. For multi-page PDFs, "
                "each page will be annotated separately with its own JSON data."
            ),
            llm_config=llm_config,
            code_execution_config=False,
            max_consecutive_auto_reply=1,
        )

        # Register annotation function
        register_function(
            annotate_resume,
            caller=annotator_agent,
            executor=user,
            name="annotate_resume",
            description=(
                "Annotate the resume document using the JSON data from the "
                "extraction result file."
            ),
        )

        # For PDFs with multiple pages, create a subfolder
        if file_path.lower().endswith((".pdf", ".PDF")):
            try:
                doc = fitz.open(file_path)
                annotated_folder = os.path.join(config.ANNOTATIONS_DIR, base_filename)
                doc.close()
            except Exception:
                annotated_folder = config.ANNOTATIONS_DIR
        else:
            annotated_folder = os.path.join(config.ANNOTATIONS_DIR, base_filename)

        os.makedirs(annotated_folder, exist_ok=True)

        annotator_message = (
            f"Now, please annotate the resume file '{file_path}' using the "
            f"extracted JSON data from '{json_file_path}' by calling "
            f"'annotate_resume' with file_path='{file_path}', "
            f"json_file='{json_file_path}', "
            f"output_dir='{annotated_folder}'. For multi-page PDFs, make "
            f"sure to annotate each page separately with its own data."
        )

        _ = user.initiate_chat(
            annotator_agent,
            message=annotator_message,
            clear_history=True,
            silent=True,
        )

        # Collect annotation URLs
        if file_path.lower().endswith((".pdf", ".PDF")):
            try:
                doc = fitz.open(file_path)
                if len(doc) > 1:
                    for i in range(len(doc)):
                        annotation_filename = f"{base_filename}_page{i + 1}.png"
                        annotation_path = (
                            f"api/static/annotations/{base_filename}/"
                            f"{annotation_filename}"
                        )
                        annotation_paths.append(annotation_path)
                else:
                    annotation_filename = f"{base_filename}_page1.png"
                    annotation_path = (
                        f"api/static/annotations/{base_filename}/{annotation_filename}"
                    )
                    annotation_paths.append(annotation_path)
                doc.close()
            except Exception:
                pass
        else:
            annotation_filename = f"{base_filename}_annotated.png"
            annotation_path = (
                f"api/static/annotations/{base_filename}/{annotation_filename}"
            )
            annotation_paths.append(annotation_path)

    # Calculate the total execution time
    total_execution_time = time.time() - start_time

    # Build pages data in the new format
    pages_data = []
    try:
        # Load original JSON data
        with open(json_file_path, encoding="utf-8") as f:
            extracted_data = json.load(f)

        if "pages" in extracted_data:
            # Get real image dimensions
            image_dimensions = {}
            if file_path.lower().endswith((".pdf", ".PDF")):
                try:
                    doc = fitz.open(file_path)
                    for i in range(len(doc)):
                        # Get actual page dimensions
                        page = doc.load_page(i)
                        rect = page.rect
                        image_dimensions[i + 1] = (
                            int(rect.width),
                            int(rect.height),
                        )
                    doc.close()
                except Exception as e:
                    print(f"Error getting PDF dimensions: {str(e)}")
                    # Default to a reasonable size if we can't get actual dimensions
                    image_dimensions[1] = (595, 842)  # A4 in points
            else:
                # For regular images, get actual dimensions
                try:
                    img = cv2.imread(file_path)
                    if img is not None:
                        height, width = img.shape[:2]
                        image_dimensions[1] = (width, height)
                    else:
                        image_dimensions[1] = (800, 1200)  # Default fallback
                except Exception as e:
                    print(f"Error getting image dimensions: {str(e)}")
                    image_dimensions[1] = (800, 1200)  # Default fallback

            # Process each page
            for page_key, page_data in extracted_data["pages"].items():
                # Extract page number from the key (e.g., "page1" -> 1)
                page_num = int(page_key.replace("page", ""))

                # Get dimensions for this page
                width, height = image_dimensions.get(page_num, (800, 1200))

                # Create data array for personal info
                data_array = []
                if "PersonalInfo" in page_data:
                    for field_name, field_value in page_data["PersonalInfo"].items():
                        if field_value and field_value != "Not Found":
                            data_array.append(
                                {
                                    "text": field_value,
                                    "label_name": field_name,
                                }
                            )

                # Add Education data
                if "Education" in page_data and isinstance(
                    page_data["Education"], list
                ):
                    for i, edu in enumerate(page_data["Education"]):
                        for field_name, field_value in edu.items():
                            if field_value and field_value != "Not Found":
                                data_array.append(
                                    {
                                        "text": field_value,
                                        "label_name": f"Education_{i + 1}_{field_name}",
                                    }
                                )

                # Add Work Experience data
                if "WorkExperience" in page_data and isinstance(
                    page_data["WorkExperience"], list
                ):
                    for i, work in enumerate(page_data["WorkExperience"]):
                        for field_name, field_value in work.items():
                            if field_value and field_value != "Not Found":
                                data_array.append(
                                    {
                                        "text": field_value,
                                        "label_name": f"Work_{i + 1}_{field_name}",
                                    }
                                )

                # Add Skills data
                if "Skills" in page_data:
                    skills = page_data["Skills"]
                    # Technical Skills
                    if "TechnicalSkills" in skills and isinstance(
                        skills["TechnicalSkills"], list
                    ):
                        for i, skill in enumerate(skills["TechnicalSkills"]):
                            if skill and skill != "Not Found":
                                data_array.append(
                                    {
                                        "text": skill,
                                        "label_name": f"TechnicalSkill_{i + 1}",
                                    }
                                )
                    # Languages
                    if "Languages" in skills and isinstance(skills["Languages"], list):
                        for i, lang in enumerate(skills["Languages"]):
                            if lang and lang != "Not Found":
                                data_array.append(
                                    {
                                        "text": lang,
                                        "label_name": f"Language_{i + 1}",
                                    }
                                )
                    # Add summary if available
                    if "Summary" in page_data and page_data["Summary"]:
                        data_array.append(
                            {
                                "text": page_data["Summary"],
                                "label_name": "Summary",
                                "is_visible": False,  # Don't visualize the summary
                            }
                        )

                pages_data.append(
                    {
                        "image_id": f"{base_filename}_page{page_num}",
                        "image_width_px": width,
                        "image_height_px": height,
                        "data": data_array,
                        "page_num": page_num,
                    }
                )
    except Exception as e:
        print(f"Error creating pages data: {str(e)}")

    # Create the response format
    response = {
        "file_id": base_filename,
        "processing_time_sec": round(total_execution_time, 2),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pages": pages_data,
        "image_urls": annotation_paths,
        "message": "Resume processed successfully",
        "summary_generated": generate_summary,
    }

    # Save in new format
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(response, f, indent=4, ensure_ascii=False)

    # Save execution info to logs
    logs_file = os.path.join(config.LOGS_DIR, f"{base_filename}_logs.json")
    with open(logs_file, "w", encoding="utf-8") as f:
        json.dump(response, f, indent=4, ensure_ascii=False)

    return response


def generate_summary_from_json(json_file_path: str) -> str:
    """
    Generate a professional summary based on the extracted resume data.

    Args:
        json_file_path: Path to the extracted JSON data file

    Returns:
        JSON string with the generated summary
    """
    import json
    import os

    # Ensure we have an absolute path
    json_file_path = os.path.abspath(json_file_path)

    # Verify the file exists
    if not os.path.isfile(json_file_path):
        raise FileNotFoundError(f"JSON file not found: {json_file_path}")

    # Get model and processor
    model, processor = get_model_and_processor()

    # Load the JSON data
    with open(json_file_path, encoding="utf-8") as f:
        extracted_data = json.load(f)

    # Prepare the data for summary generation
    resume_text = ""
    if "pages" in extracted_data:
        # Get the first page data
        first_page_key = next(iter(extracted_data["pages"]))
        page_data = extracted_data["pages"][first_page_key]

        # Format personal info
        if "PersonalInfo" in page_data:
            personal_info = page_data["PersonalInfo"]
            resume_text += "PERSONAL INFORMATION:\n"
            for key, value in personal_info.items():
                if value and value != "Not Found":
                    resume_text += f"{key}: {value}\n"

        # Format education
        if "Education" in page_data and isinstance(page_data["Education"], list):
            resume_text += "\nEDUCATION:\n"
            for edu in page_data["Education"]:
                deg = edu.get("Degree", "Not Found")
                inst = edu.get("Institution", "Not Found")
                date = edu.get("GradDate", "Not Found")
                if deg != "Not Found" or inst != "Not Found":
                    resume_text += f"- {deg} at {inst}"
                    if date != "Not Found":
                        resume_text += f", {date}"
                    resume_text += "\n"

        # Format experience
        if "WorkExperience" in page_data and isinstance(
            page_data["WorkExperience"], list
        ):
            resume_text += "\nWORK EXPERIENCE:\n"
            for work in page_data["WorkExperience"]:
                title = work.get("JobTitle", "Not Found")
                company = work.get("Company", "Not Found")
                duration = work.get("Duration", "Not Found")
                resp = work.get("Responsibilities", "Not Found")

                if title != "Not Found" or company != "Not Found":
                    resume_text += f"- {title} at {company}"
                    if duration != "Not Found":
                        resume_text += f", {duration}"
                    resume_text += "\n"
                    if resp != "Not Found":
                        resume_text += f"  Responsibilities: {resp}\n"

        # Format skills
        if "Skills" in page_data:
            skills = page_data["Skills"]
            resume_text += "\nSKILLS:\n"

            if "TechnicalSkills" in skills:
                tech_skills = skills["TechnicalSkills"]
                if isinstance(tech_skills, list) and tech_skills:
                    resume_text += f"- Technical Skills: {', '.join(tech_skills)}\n"
                elif tech_skills and tech_skills != "Not Found":
                    resume_text += f"- Technical Skills: {tech_skills}\n"

            if "Languages" in skills:
                languages = skills["Languages"]
                if isinstance(languages, list) and languages:
                    resume_text += f"- Languages: {', '.join(languages)}\n"
                elif languages and languages != "Not Found":
                    resume_text += f"- Languages: {languages}\n"

    # Generate the summary using the configured model
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": config.SUMMARY_PROMPT + "\n\nResume Data:\n" + resume_text,
                }
            ],
        }
    ]

    text_prompt = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    inputs = processor(
        text=[text_prompt],
        padding=True,
        return_tensors="pt",
    )

    inputs = inputs.to("cuda")
    generated_ids = model.generate(**inputs, max_new_tokens=512)
    generated_ids_trimmed = [
        out_ids[len(in_ids) :]
        for in_ids, out_ids in zip(inputs.input_ids, generated_ids, strict=False)
    ]

    output_text = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True,
    )[0]

    # Extract JSON from response
    import re

    json_match = re.search(r"\{.*\}", output_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)

        try:
            summary_data = json.loads(json_str)

            # Update the original JSON with the summary
            if "pages" in extracted_data:
                for page_key in extracted_data["pages"]:
                    extracted_data["pages"][page_key]["Summary"] = summary_data.get(
                        "Summary", ""
                    )

            # Save the updated JSON
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(extracted_data, f, indent=4, ensure_ascii=False)

            return json.dumps(summary_data, indent=4, ensure_ascii=False)

        except json.JSONDecodeError:
            # If JSON parsing fails, create a basic summary
            summary = {
                "Summary": (
                    "Unable to generate a proper summary from the extracted data."
                )
            }

            # Save the updated JSON with basic summary
            if "pages" in extracted_data:
                for page_key in extracted_data["pages"]:
                    extracted_data["pages"][page_key]["Summary"] = summary["Summary"]

            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(extracted_data, f, indent=4, ensure_ascii=False)

            return json.dumps(summary, indent=4, ensure_ascii=False)

    else:
        # If no JSON found, create a basic summary
        summary = {
            "Summary": ("Unable to generate a proper summary from the extracted data.")
        }

        # Save the updated JSON with basic summary
        if "pages" in extracted_data:
            for page_key in extracted_data["pages"]:
                extracted_data["pages"][page_key]["Summary"] = summary["Summary"]

        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, indent=4, ensure_ascii=False)

        return json.dumps(summary, indent=4, ensure_ascii=False)
