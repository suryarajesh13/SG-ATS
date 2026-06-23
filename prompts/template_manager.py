from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

DEFAULT_ROLE = "software"

ROLE_TEMPLATE_MAP: Dict[str, str] = {
    "software": "resume_evaluation_criteria.jinja",
    "it_sg": "resume_evaluation_criteria_it_sg.jinja",
    "accounting_sg": "resume_evaluation_criteria_accounting_sg.jinja",
    "audit_sg": "resume_evaluation_criteria_audit_sg.jinja",
    "hr_sg": "resume_evaluation_criteria_hr_sg.jinja",
    "banking_sg": "resume_evaluation_criteria_banking_sg.jinja",
}

SG_ROLE_TYPES = {role for role in ROLE_TEMPLATE_MAP if role != DEFAULT_ROLE}


def is_sg_role(role_type: str) -> bool:
    return role_type in SG_ROLE_TYPES


class TemplateManager:
    def __init__(self, templates_dir: str | Path = TEMPLATES_DIR):
        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _normalize_template_name(self, template_name: str) -> str:
        return template_name if template_name.endswith(".jinja") else f"{template_name}.jinja"

    def render_template(self, template_name: str, **kwargs) -> str:
        normalized = self._normalize_template_name(template_name)
        try:
            template = self.env.get_template(normalized)
            return template.render(**kwargs)
        except TemplateNotFound as exc:
            raise FileNotFoundError(
                f"Template '{normalized}' not found in '{self.templates_dir}'."
            ) from exc

    def get_evaluation_criteria(
        self,
        role_type: str = DEFAULT_ROLE,
        text_content: str = "",
        target_job_title: str = "",
    ) -> str:
        template_name = ROLE_TEMPLATE_MAP.get(role_type, ROLE_TEMPLATE_MAP[DEFAULT_ROLE])
        return self.render_template(
            template_name,
            text_content=text_content,
            target_job_title=target_job_title,
            role_type=role_type,
        )

    def get_system_message(self, role_type: str = DEFAULT_ROLE) -> str:
        sg_system_template = self.templates_dir / "resume_evaluation_system_message_sg.jinja"
        if is_sg_role(role_type) and sg_system_template.exists():
            return self.render_template("resume_evaluation_system_message_sg.jinja")
        return self.render_template("resume_evaluation_system_message.jinja")

    def list_available_roles(self) -> List[str]:
        return list(ROLE_TEMPLATE_MAP.keys())
