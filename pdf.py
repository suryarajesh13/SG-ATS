from __future__ import annotations

import json
import logging
import os
import time
from typing import Dict, Optional

import pymupdf

from llm_utils import extract_json_from_response, initialize_llm_provider
from models import (
    AwardsSection,
    Basics,
    BasicsSection,
    EducationSection,
    JSONResume,
    ProjectsSection,
    SkillsSection,
    WorkSection,
)
from prompt import DEFAULT_MODEL, MODEL_PARAMETERS
from prompts.template_manager import TemplateManager
from pymupdf_rag import to_markdown
from transform import transform_parsed_data

logger = logging.getLogger(__name__)


class PDFHandler:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self.template_manager = TemplateManager()
        self.provider = initialize_llm_provider(self.model_name)

    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

            with pymupdf.open(pdf_path) as doc:
                resume_text = to_markdown(doc, pages=range(doc.page_count))
                logger.debug(
                    "Extracted text from PDF: %s characters",
                    len(resume_text) if resume_text else 0,
                )
                return resume_text
        except Exception as exc:
            logger.error("An error occurred while reading the PDF: %s", exc)
            return None

    def _call_llm_for_section(
        self,
        section_name: str,
        prompt: str,
        return_model=None,
    ) -> Optional[Dict]:
        try:
            start_time = time.time()
            logger.debug(
                "Extracting %s section using model %s...",
                section_name,
                self.model_name,
            )

            model_params = MODEL_PARAMETERS.get(
                self.model_name,
                {"temperature": 0.1, "top_p": 0.9},
            )

            section_system_message = self.template_manager.render_template(
                "system_message",
                section_name_param=section_name,
            )
            if not section_system_message:
                logger.error(
                    "Failed to render system message template for %s",
                    section_name,
                )
                return None

            kwargs = {}
            if return_model is not None:
                kwargs["format"] = return_model.model_json_schema()

            response = self.provider.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": section_system_message},
                    {"role": "user", "content": prompt},
                ],
                temperature=model_params.get("temperature", 0.1),
                top_p=model_params.get("top_p", 0.9),
                **kwargs,
            )

            if isinstance(response, dict):
                response_text = response.get("message", {}).get("content", "")
            else:
                response_text = getattr(response, "text", str(response))

            response_text = extract_json_from_response(response_text)

            json_start = response_text.find("{")
            json_end = response_text.rfind("}")
            if json_start != -1 and json_end != -1:
                response_text = response_text[json_start : json_end + 1]

            parsed_data = json.loads(response_text)
            transformed_data = transform_parsed_data(parsed_data)

            total_time = time.time() - start_time
            logger.debug(
                "Successfully extracted %s section in %.2f seconds",
                section_name,
                total_time,
            )
            return transformed_data

        except json.JSONDecodeError as exc:
            logger.error("Error parsing JSON for %s section: %s", section_name, exc)
            logger.error("Raw response: %s", response_text)
            return None
        except Exception as exc:
            logger.error("Error calling LLM for %s section: %s", section_name, exc)
            return None

    def extract_basics_section(self, resume_text: str) -> Optional[Dict]:
        prompt = self.template_manager.render_template(
            "basics",
            text_content=resume_text,
        )
        if not prompt:
            logger.error("Failed to render basics template")
            return None
        return self._call_llm_for_section("basics", prompt, BasicsSection)

    def extract_work_section(self, resume_text: str) -> Optional[Dict]:
        prompt = self.template_manager.render_template(
            "work",
            text_content=resume_text,
        )
        if not prompt:
            logger.error("Failed to render work template")
            return None
        return self._call_llm_for_section("work", prompt, WorkSection)

    def extract_education_section(self, resume_text: str) -> Optional[Dict]:
        prompt = self.template_manager.render_template(
            "education",
            text_content=resume_text,
        )
        if not prompt:
            logger.error("Failed to render education template")
            return None
        return self._call_llm_for_section("education", prompt, EducationSection)

    def extract_skills_section(self, resume_text: str) -> Optional[Dict]:
        prompt = self.template_manager.render_template(
            "skills",
            text_content=resume_text,
        )
        if not prompt:
            logger.error("Failed to render skills template")
            return None
        return self._call_llm_for_section("skills", prompt, SkillsSection)

    def extract_projects_section(self, resume_text: str) -> Optional[Dict]:
        prompt = self.template_manager.render_template(
            "projects",
            text_content=resume_text,
        )
        if not prompt:
            logger.error("Failed to render projects template")
            return None
        return self._call_llm_for_section("projects", prompt, ProjectsSection)

    def extract_awards_section(self, resume_text: str) -> Optional[Dict]:
        prompt = self.template_manager.render_template(
            "awards",
            text_content=resume_text,
        )
        if not prompt:
            logger.error("Failed to render awards template")
            return None
        return self._call_llm_for_section("awards", prompt, AwardsSection)

    def extract_json_from_text(self, resume_text: str) -> Optional[JSONResume]:
        try:
            return self._extract_all_sections_separately(resume_text)
        except Exception as exc:
            logger.error("Error extracting JSON from text: %s", exc)
            return None

    def extract_json_from_pdf(self, pdf_path: str) -> Optional[JSONResume]:
        try:
            logger.debug("Extracting text from PDF: %s", pdf_path)
            text_content = self.extract_text_from_pdf(pdf_path)

            if not text_content:
                logger.error("Failed to extract text from PDF")
                return None

            logger.debug(
                "Successfully extracted %s characters from PDF",
                len(text_content),
            )
            return self._extract_all_sections_separately(text_content)

        except Exception as exc:
            logger.error("Error during PDF to JSON extraction: %s", exc)
            return None

    def _extract_section_data(
        self,
        text_content: str,
        section_name: str,
    ) -> Optional[Dict]:
        section_extractors = {
            "basics": self.extract_basics_section,
            "work": self.extract_work_section,
            "education": self.extract_education_section,
            "skills": self.extract_skills_section,
            "projects": self.extract_projects_section,
            "awards": self.extract_awards_section,
        }

        extractor = section_extractors.get(section_name)
        if extractor is None:
            logger.error("Invalid section name: %s", section_name)
            logger.error("Valid sections: %s", list(section_extractors.keys()))
            return None

        return extractor(text_content)

    def _empty_resume_payload(self) -> Dict:
        return {
            "basics": None,
            "work": [],
            "volunteer": [],
            "education": [],
            "awards": [],
            "certificates": [],
            "publications": [],
            "skills": [],
            "languages": [],
            "interests": [],
            "references": [],
            "projects": [],
            "meta": {},
        }

    def _extract_single_section(
        self,
        text_content: str,
        section_name: str,
    ) -> Optional[Dict]:
        section_data = self._extract_section_data(text_content, section_name)
        if not section_data:
            return None

        complete_resume = self._empty_resume_payload()
        complete_resume.update(section_data)
        return complete_resume

    def _extract_all_sections_separately(
        self,
        text_content: str,
    ) -> Optional[JSONResume]:
        start_time = time.time()
        sections = ["basics", "work", "education", "skills", "projects", "awards"]
        complete_resume = self._empty_resume_payload()

        for section_name in sections:
            section_data = self._extract_section_data(text_content, section_name)

            if not section_data:
                logger.error(
                    "Failed to extract %s section. Aborting extraction to prevent partial data.",
                    section_name,
                )
                return None

            complete_resume.update(section_data)
            logger.debug("Successfully extracted %s section", section_name)

        try:
            if complete_resume.get("basics") and isinstance(
                complete_resume["basics"], dict
            ):
                complete_resume["basics"] = Basics(**complete_resume["basics"])

            json_resume = JSONResume(**complete_resume)

            total_time = time.time() - start_time
            logger.info(
                "Total time for separate section extraction: %.2f seconds",
                total_time,
            )
            return json_resume

        except Exception as exc:
            logger.error("Error creating JSONResume object: %s", exc)
            return None
