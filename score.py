from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from config import DEVELOPMENT_MODE
from evaluator import ResumeEvaluator
from github import fetch_and_display_github_info
from models import EvaluationData, GenericSGEvaluation, JSONResume
from pdf import PDFHandler
from prompt import DEFAULT_MODEL, MODEL_PARAMETERS
from prompts.template_manager import DEFAULT_ROLE, ROLE_TEMPLATE_MAP, is_sg_role
from transform import (
    convert_blog_data_to_text,
    convert_github_data_to_text,
    convert_json_resume_to_text,
    transform_evaluation_response,
)

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)5s - %(lineno)5d - %(funcName)33s - %(levelname)5s - %(message)s",
)

ROLE_DISPLAY_LABELS = {
    "general": "General / Any Role",
    "software": "Software / IT Jobs",
    "accounting_sg": "Accounting Jobs (Singapore)",
    "audit_sg": "Auditing Jobs (Singapore)",
    "hr_sg": "HR Jobs (Singapore)",
    "banking_sg": "Banking Jobs (Singapore)",
}

CATEGORY_ICONS = {
    "contact_and_summary": "📌",
    "work_experience": "💼",
    "education": "🎓",
    "skills": "💻",
    "projects": "🚀",
    "formatting_readability": "📄",
    "open_source": "🌐",
    "self_projects": "🚀",
    "production": "🏢",
    "technical_skills": "💻",
    "sg_technical_skills": "💻",
    "projects_and_delivery": "🚀",
    "production_experience": "🏢",
    "professional_readiness": "📋",
    "sg_certifications": "🎓",
    "accounting_experience": "📊",
    "finance_systems": "🖥️",
    "professional_communication": "🗣️",
    "sg_audit_credentials": "🏅",
    "audit_experience": "🔍",
    "controls_and_regulatory": "⚖️",
    "audit_tools_and_analysis": "🛠️",
    "sg_hr_credentials": "🎓",
    "hr_operations_and_specialisation": "👥",
    "stakeholder_management": "🤝",
    "hr_systems_and_compliance": "🧾",
    "sg_banking_credentials": "🏦",
    "banking_experience": "💼",
    "regulatory_and_risk": "⚠️",
    "systems_and_analysis": "📈",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate a resume PDF.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("pdf_path", help="Path to the resume PDF file.")
    parser.add_argument(
        "--role-type",
        choices=list(ROLE_TEMPLATE_MAP.keys()),
        default=DEFAULT_ROLE,
        help="Target evaluation rubric (default: %(default)s).",
    )
    parser.add_argument(
        "--target-job-title",
        default="",
        help="Optional job title, e.g. 'Data Analyst' or 'AML Analyst'.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=(
            "LLM model name to use for evaluation (default: %(default)s).
"
            "Examples:
"
            "  Ollama : llama3, mistral, gemma3, deepseek-r1
"
            "  Gemini : gemini-1.5-flash, gemini-1.5-pro"
        ),
    )
    return parser.parse_args()


def is_valid_resume_data(resume_data: JSONResume) -> bool:
    if not resume_data:
        return False
    return any([
        resume_data.basics is not None,
        bool(resume_data.work),
        bool(resume_data.education),
        bool(resume_data.skills),
        bool(resume_data.projects),
    ])


def find_profile(profiles, network: str):
    if not profiles:
        return None
    network = network.lower()
    return next(
        (p for p in profiles if p.network and p.network.lower() == network),
        None,
    )


def _safe_slug(value: str) -> str:
    if not value:
        return "generic"
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_") or "generic"


def _should_include_github(role_type: str) -> bool:
    return role_type == DEFAULT_ROLE


def _resume_cache_path(pdf_path: str) -> str:
    return f"cache/resumecache_{Path(pdf_path).stem}.json"


def _github_cache_path(pdf_path: str) -> str:
    return f"cache/githubcache_{Path(pdf_path).stem}.json"


def _evaluation_cache_path(
    pdf_path: str, role_type: str, target_job_title: str, model_name: str
) -> str:
    return (
        f"cache/evalcache_{_safe_slug(Path(pdf_path).stem)}_"
        f"{_safe_slug(role_type)}_{_safe_slug(target_job_title)}_"
        f"{_safe_slug(model_name)}.json"
    )


def _load_resume_data(pdf_path: str) -> Optional[JSONResume]:
    cache_filename = _resume_cache_path(pdf_path)

    if DEVELOPMENT_MODE and os.path.exists(cache_filename):
        try:
            cached_data = json.loads(Path(cache_filename).read_text(encoding="utf-8"))
            loaded_resume = JSONResume(**cached_data)
            if not is_valid_resume_data(loaded_resume):
                raise ValueError("Cached resume data contains no core content.")
            logger.info("Loaded cached resume data from %s", cache_filename)
            return loaded_resume
        except Exception as exc:
            logger.warning("Invalid resume cache %s: %s", cache_filename, exc)
            try:
                os.remove(cache_filename)
            except OSError:
                pass

    pdf_handler = PDFHandler()
    resume_data = pdf_handler.extract_json_from_pdf(pdf_path)
    if resume_data is None:
        return None

    if DEVELOPMENT_MODE and is_valid_resume_data(resume_data):
        os.makedirs("cache", exist_ok=True)
        Path(cache_filename).write_text(
            json.dumps(resume_data.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return resume_data


def _load_github_data(resume_data: JSONResume, pdf_path: str, role_type: str) -> dict:
    if not _should_include_github(role_type):
        return {}

    cache_filename = _github_cache_path(pdf_path)

    if DEVELOPMENT_MODE and os.path.exists(cache_filename):
        try:
            cached = json.loads(Path(cache_filename).read_text(encoding="utf-8"))
            if isinstance(cached, dict) and cached.get("profile"):
                logger.info("Loaded cached GitHub data from %s", cache_filename)
                return cached
            raise ValueError("GitHub cache is empty or malformed.")
        except Exception as exc:
            logger.warning("Invalid GitHub cache %s: %s", cache_filename, exc)
            try:
                os.remove(cache_filename)
            except OSError:
                pass

    profiles = resume_data.basics.profiles if resume_data and resume_data.basics else []
    github_profile = find_profile(profiles, "github")

    if not github_profile or not github_profile.url:
        return {}

    github_data = fetch_and_display_github_info(github_profile.url) or {}

    if DEVELOPMENT_MODE and isinstance(github_data, dict) and github_data.get("profile"):
        os.makedirs("cache", exist_ok=True)
        Path(cache_filename).write_text(
            json.dumps(github_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return github_data


def _build_resume_context(
    resume_data: JSONResume,
    github_data: dict | None = None,
    blog_data: dict | None = None,
    role_type: str = DEFAULT_ROLE,
) -> str:
    text = convert_json_resume_to_text(resume_data)
    if _should_include_github(role_type) and github_data:
        text += convert_github_data_to_text(github_data)
    if blog_data:
        text += convert_blog_data_to_text(blog_data)
    return text


def _evaluate_resume(
    pdf_path: str,
    resume_data: JSONResume,
    github_data: dict | None = None,
    blog_data: dict | None = None,
    role_type: str = DEFAULT_ROLE,
    target_job_title: str = "",
    model_name: str = DEFAULT_MODEL,
) -> Optional[EvaluationData | GenericSGEvaluation]:
    if resume_data is None:
        return None

    eval_cache_filename = _evaluation_cache_path(
        pdf_path=pdf_path,
        role_type=role_type,
        target_job_title=target_job_title,
        model_name=model_name,
    )

    if DEVELOPMENT_MODE and os.path.exists(eval_cache_filename):
        try:
            cached_data = json.loads(
                Path(eval_cache_filename).read_text(encoding="utf-8")
            )
            if is_sg_role(role_type):
                evaluation = GenericSGEvaluation(**cached_data)
            else:
                evaluation = EvaluationData(**cached_data)
            logger.info("Loaded cached evaluation from %s", eval_cache_filename)
            return evaluation
        except Exception as exc:
            logger.warning("Invalid eval cache %s: %s", eval_cache_filename, exc)
            try:
                os.remove(eval_cache_filename)
            except OSError:
                pass

    model_params = MODEL_PARAMETERS.get(model_name) or MODEL_PARAMETERS.get(DEFAULT_MODEL)
    evaluator = ResumeEvaluator(model_name=model_name, model_params=model_params)

    resume_text = _build_resume_context(
        resume_data=resume_data,
        github_data=github_data,
        blog_data=blog_data,
        role_type=role_type,
    )

    evaluation = evaluator.evaluate(
        resume_text=resume_text,
        role_type=role_type,
        target_job_title=target_job_title,
    )

    if DEVELOPMENT_MODE and evaluation:
        os.makedirs("cache", exist_ok=True)
        Path(eval_cache_filename).write_text(
            json.dumps(evaluation.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return evaluation


def _resolve_candidate_name(pdf_path: str, resume_data: JSONResume | None) -> str:
    if resume_data and resume_data.basics and resume_data.basics.name:
        return resume_data.basics.name
    return Path(pdf_path).stem


def _print_shared_footer(evaluation) -> None:
    if evaluation.bonus_points and evaluation.bonus_points.total > 0:
        print(f"
⭐ BONUS POINTS: +{evaluation.bonus_points.total}")
        if evaluation.bonus_points.breakdown:
            print(f"   {evaluation.bonus_points.breakdown}")

    if evaluation.deductions and evaluation.deductions.total > 0:
        print(f"
⚠️  DEDUCTIONS: -{evaluation.deductions.total}")
        if evaluation.deductions.reasons:
            print(f"   {evaluation.deductions.reasons}")

    if evaluation.key_strengths:
        print("
✅ KEY STRENGTHS:")
        for i, item in enumerate(evaluation.key_strengths, start=1):
            print(f"   {i}. {item}")

    if evaluation.areas_for_improvement:
        print("
🔧 AREAS FOR IMPROVEMENT:")
        for i, item in enumerate(evaluation.areas_for_improvement, start=1):
            print(f"   {i}. {item}")


def print_evaluation_results(
    evaluation: EvaluationData | GenericSGEvaluation | None,
    candidate_name: str,
    role_type: str = DEFAULT_ROLE,
    target_job_title: str = "",
    model_name: str = DEFAULT_MODEL,
) -> None:
    print("
" + "=" * 80)
    print(f"📊 RESUME EVALUATION RESULTS FOR: {candidate_name}")
    print(f"🎯 ROLE: {ROLE_DISPLAY_LABELS.get(role_type, role_type)}")
    print(f"🤖 MODEL: {model_name}")
    if target_job_title:
        print(f"🧭 TARGET JOB TITLE: {target_job_title}")
    print("=" * 80)

    if evaluation is None:
        print("❌ No evaluation data available.")
        print("=" * 80)
        return

    if isinstance(evaluation, GenericSGEvaluation):
        print(f"
🎯 OVERALL SCORE: {evaluation.total_score()}/{evaluation.max_score()}")
        print("
📈 DETAILED SCORES:")
        print("-" * 60)
        for category_name, category_data in evaluation.scores.items():
            icon = CATEGORY_ICONS.get(category_name, "📌")
            label = category_name.replace("_", " ").title()
            print(f"{icon} {label:<34} {category_data.score}/{category_data.max}")
            print(f"   Evidence: {category_data.evidence}
")
        _print_shared_footer(evaluation)
        print("
" + "=" * 80)
        return

    print(f"
🎯 OVERALL SCORE: {evaluation.total_score()}/{evaluation.max_score()}")
    print("
📈 DETAILED SCORES:")
    print("-" * 60)
    for category_name, category_data in [
        ("open_source", evaluation.scores.open_source),
        ("self_projects", evaluation.scores.self_projects),
        ("production", evaluation.scores.production),
        ("technical_skills", evaluation.scores.technical_skills),
    ]:
        icon = CATEGORY_ICONS.get(category_name, "📌")
        label = category_name.replace("_", " ").title()
        print(f"{icon} {label:<34} {category_data.score}/{category_data.max}")
        print(f"   Evidence: {category_data.evidence}
")

    _print_shared_footer(evaluation)
    print("
" + "=" * 80)


def _write_csv(
    pdf_path: str,
    resume_data: JSONResume | None,
    github_data: dict,
    evaluation: EvaluationData | GenericSGEvaluation | None,
    role_type: str,
    target_job_title: str,
) -> None:
    if not DEVELOPMENT_MODE or evaluation is None:
        return

    csv_row = transform_evaluation_response(
        file_name=os.path.basename(pdf_path),
        resume_data=resume_data,
        github_data=github_data,
        evaluation=evaluation,
        role_type=role_type,
        target_job_title=target_job_title,
    )

    csv_path = (
        "resume_evaluations.csv"
        if role_type == DEFAULT_ROLE
        else f"resume_evaluations_{role_type}.csv"
    )

    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=list(csv_row.keys()),
            extrasaction="ignore",
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(csv_row)


def main(
    pdf_path: str,
    role_type: str = DEFAULT_ROLE,
    target_job_title: str = "",
    model_name: str = DEFAULT_MODEL,
):
    resume_data = _load_resume_data(pdf_path)
    if resume_data is None:
        logger.error("Failed to extract resume data from %s", pdf_path)
        return None

    github_data = _load_github_data(resume_data, pdf_path, role_type)

    score = _evaluate_resume(
        pdf_path=pdf_path,
        resume_data=resume_data,
        github_data=github_data,
        role_type=role_type,
        target_job_title=target_job_title,
        model_name=model_name,
    )

    candidate_name = _resolve_candidate_name(pdf_path, resume_data)
    print_evaluation_results(
        evaluation=score,
        candidate_name=candidate_name,
        role_type=role_type,
        target_job_title=target_job_title,
        model_name=model_name,
    )

    _write_csv(
        pdf_path=pdf_path,
        resume_data=resume_data,
        github_data=github_data,
        evaluation=score,
        role_type=role_type,
        target_job_title=target_job_title,
    )

    return score


if __name__ == "__main__":
    args = parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"Error: File '{args.pdf_path}' does not exist.")
        sys.exit(1)

    main(
        pdf_path=args.pdf_path,
        role_type=args.role_type,
        target_job_title=args.target_job_title,
        model_name=args.model,
    )
