from __future__ import annotations

from typing import Dict, List

from models import GenericSGEvaluation, JSONResume


def transform_parsed_data(parsed_data: Dict) -> Dict:
    try:
        if not isinstance(parsed_data, dict):
            return parsed_data

        if "basics" in parsed_data and len(parsed_data) > 1:
            return {
                "basics": transform_basics(parsed_data.get("basics", {})),
                "work": transform_work_experience(
                    parsed_data.get(
                        "work_experience",
                        parsed_data.get("work", parsed_data.get("experience", [])),
                    )
                ),
                "volunteer": transform_organizations(parsed_data.get("organizations", [])),
                "education": transform_education(parsed_data.get("education", [])),
                "awards": transform_achievements(
                    parsed_data.get(
                        "achievements",
                        parsed_data.get("awards", parsed_data.get("honors_and_awards", [])),
                    )
                ),
                "certificates": parsed_data.get("certificates", []),
                "publications": parsed_data.get("publications", []),
                "skills": transform_skills_comprehensive(parsed_data),
                "languages": parsed_data.get("languages", []),
                "interests": parsed_data.get("interests", []),
                "references": parsed_data.get("references", []),
                "projects": transform_projects_comprehensive(parsed_data),
                "meta": parsed_data.get("meta", {}),
            }

        if "basics" in parsed_data:
            return {"basics": transform_basics(parsed_data.get("basics", parsed_data))}

        if "work" in parsed_data or "work_experience" in parsed_data or "experience" in parsed_data:
            work_data = parsed_data.get(
                "work", parsed_data.get("work_experience", parsed_data.get("experience", []))
            )
            return {"work": transform_work_experience(work_data)}

        if "education" in parsed_data:
            return {"education": transform_education(parsed_data.get("education", []))}

        if (
            "skills" in parsed_data
            or "librariesFrameworks" in parsed_data
            or "toolsPlatforms" in parsed_data
            or "databases" in parsed_data
        ):
            return {"skills": transform_skills_comprehensive(parsed_data)}

        if "projects" in parsed_data or "projectsOpenSource" in parsed_data:
            return {"projects": transform_projects_comprehensive(parsed_data)}

        if (
            "awards" in parsed_data
            or "achievements" in parsed_data
            or "honors_and_awards" in parsed_data
        ):
            awards_data = parsed_data.get(
                "awards",
                parsed_data.get("achievements", parsed_data.get("honors_and_awards", [])),
            )
            return {"awards": transform_achievements(awards_data)}

        return parsed_data

    except Exception as exc:
        print(f"Error transforming parsed data: {exc}")
        return parsed_data


def extract_domain_from_url(url: str) -> str:
    try:
        if "://" in url:
            url = url.split("://", 1)[1]
        domain = url.split("/", 1)[0]
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def get_network_name(domain: str) -> str:
    domain_mapping = {
        "github.com": "GitHub",
        "linkedin.com": "LinkedIn",
        "leetcode.com": "LeetCode",
        "stackoverflow.com": "Stack Overflow",
        "hackerrank.com": "HackerRank",
        "behance.net": "Behance",
        "dev.to": "DEV Community",
        "twitter.com": "X",
        "x.com": "X",
    }
    return domain_mapping.get(domain, "")


def extract_username_from_url(url: str, domain: str) -> str:
    try:
        path = url.split(domain, 1)[1] if domain in url else ""
        if not path:
            return ""
        path = path.lstrip("/")
        parts = [part for part in path.split("/") if part]

        if not parts:
            return ""

        # Fix: return second segment (the actual username), not last segment
        if domain == "linkedin.com" and len(parts) >= 2 and parts[0] == "in":
            return parts[1]
        if domain == "linkedin.com" and len(parts) >= 1:
            return parts[0]
        if domain == "stackoverflow.com" and len(parts) >= 2:
            return parts[1]
        return parts[0]
    except Exception:
        return ""


def transform_basics(basics_data: Dict) -> Dict:
    if not isinstance(basics_data, dict):
        return basics_data

    profiles = basics_data.get("profiles", [])
    transformed_profiles = []

    if isinstance(profiles, list):
        for profile in profiles:
            if isinstance(profile, dict):
                transformed_profile = profile.copy()
                url = transformed_profile.get("url", "")
                network = transformed_profile.get("network")

                if url and not network:
                    domain = extract_domain_from_url(url)
                    network_name = get_network_name(domain)
                    if network_name:
                        transformed_profile["network"] = network_name
                    username = extract_username_from_url(url, domain)
                    if username:
                        transformed_profile["username"] = username

                transformed_profiles.append(transformed_profile)

    basics_data["profiles"] = transformed_profiles
    return basics_data


def parse_date_range(date_range: str) -> tuple:
    if not date_range:
        return None, None

    if "onwards" in date_range:
        start_part = date_range.replace("onwards", "").strip()
        return (start_part or None), "Present"

    month_tokens = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    if " " in date_range and any(month in date_range for month in month_tokens):
        parts = date_range.split(" ")
        if len(parts) >= 2:
            year = parts[-1]
            if "-" in parts[0] and len(parts[0].split("-")) == 2:
                start_month, end_month = parts[0].split("-")
                return f"{start_month} {year}", f"{end_month} {year}"
            return f"{parts[0]} {year}", None

    if "-" in date_range and len(date_range.split("-")) == 2:
        start_year, end_year = date_range.split("-")
        return f"{start_year}-01", f"{end_year}-12"

    return None, None


def transform_work_experience(work_list: List) -> List[Dict]:
    transformed = []
    for item in work_list or []:
        if not isinstance(item, dict):
            continue

        description = item.get("description", "")
        if isinstance(description, list):
            description = " ".join(description)

        start_date_input = item.get("startDate", "")
        if start_date_input and any(
            month in start_date_input
            for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        ):
            start_date, end_date = parse_date_range(start_date_input)
        else:
            start_date = item.get("startDate")
            end_date = item.get("endDate")

        transformed.append({
            "name": item.get("name", ""),
            "position": item.get("position", item.get("type", item.get("title", ""))),
            "url": item.get("url"),
            "startDate": start_date,
            "endDate": end_date,
            "summary": item.get("summary", description),
            "highlights": item.get("highlights", []),
        })
    return transformed


def transform_organizations(org_list: List) -> List[Dict]:
    transformed = []
    for item in org_list or []:
        if isinstance(item, dict):
            transformed.append({
                "organization": item.get("name", ""),
                "position": item.get("role", ""),
                "url": item.get("url"),
                "startDate": None,
                "endDate": "Present",
                "summary": None,
                "highlights": [],
            })
    return transformed


def transform_education(edu_list: List) -> List[Dict]:
    transformed = []
    for item in edu_list or []:
        if not isinstance(item, dict):
            continue
        if "degree" in item:
            score = item.get("gpa", item.get("percentage"))
            if score is not None:
                score = str(score)
            start_date, end_date = parse_date_range(item.get("years", ""))
            degree = item.get("degree", "")
            transformed.append({
                "institution": item.get("institution", ""),
                "url": item.get("url"),
                "area": degree.split(", ")[-1] if "," in degree else None,
                "studyType": degree.split(", ")[0] if "," in degree else degree,
                "startDate": start_date,
                "endDate": end_date,
                "score": score,
                "courses": [],
            })
        else:
            transformed.append(item)
    return transformed


def transform_achievements(achievements_list: List) -> List[Dict]:
    transformed = []
    for item in achievements_list or []:
        if not isinstance(item, dict):
            continue
        transformed.append({
            "title": item.get("title", item.get("name", "")),
            "date": f"{item.get('year')}-01" if item.get("year") else None,
            "awarder": item.get("awarder", item.get("organization", "")),
            "summary": item.get("summary", item.get("description")),
        })
    return transformed


def transform_skills(skills_list: List) -> List[Dict]:
    transformed = []
    for item in skills_list or []:
        if not isinstance(item, dict):
            continue
        if "category" in item:
            transformed.append({
                "name": item.get("category", ""),
                "level": None,
                "keywords": item.get("keywords", []),
            })
        else:
            transformed.append(item)
    return transformed


def transform_projects(projects_list: List) -> List[Dict]:
    transformed = []
    for item in projects_list or []:
        if not isinstance(item, dict):
            continue

        skills = []
        project_name = item.get("name", "")

        if "|" in project_name:
            name_parts = project_name.split("|")
            if len(name_parts) > 1:
                skills_part = name_parts[1].strip()
                skills = [s.strip() for s in skills_part.split(",")]
                item["name"] = name_parts[0].strip()

        technologies = item.get("technologies", [])
        if isinstance(technologies, str):
            technologies = [t.strip() for t in technologies.split(",")]

        if not skills and technologies:
            skills = technologies

        transformed.append({
            "name": item.get("name", ""),
            "startDate": None,
            "endDate": None,
            "description": item.get("description", ""),
            "highlights": [item.get("type", "")] if item.get("type") else [],
            "url": item.get("url"),
            "technologies": technologies,
            "skills": skills,
        })
    return transformed


def transform_skills_comprehensive(parsed_data: Dict) -> List[Dict]:
    skills = []
    if "skills" in parsed_data and isinstance(parsed_data["skills"], list):
        if parsed_data["skills"] and isinstance(parsed_data["skills"][0], str):
            skills.append({
                "name": "Programming Languages",
                "level": None,
                "keywords": parsed_data["skills"],
            })
        else:
            skills.extend(transform_skills(parsed_data["skills"]))

    for field, category_name in {
        "librariesFrameworks": "Libraries/Frameworks",
        "toolsPlatforms": "Tools/Platforms",
        "databases": "Databases",
    }.items():
        if field in parsed_data and isinstance(parsed_data[field], list):
            skills.append({"name": category_name, "level": None, "keywords": parsed_data[field]})

    return skills


def transform_projects_comprehensive(parsed_data: Dict) -> List[Dict]:
    projects = []
    if "projects" in parsed_data:
        projects.extend(transform_projects(parsed_data["projects"]))

    if "projectsOpenSource" in parsed_data:
        for item in parsed_data["projectsOpenSource"]:
            if not isinstance(item, dict):
                continue
            skills = []
            project_name = item.get("name", "")
            if "|" in project_name:
                name_parts = project_name.split("|")
                if len(name_parts) > 1:
                    skills = [s.strip() for s in name_parts[1].strip().split(",")]
                    item["name"] = name_parts[0].strip()
            projects.append({
                "name": item.get("name", ""),
                "startDate": None,
                "endDate": None,
                "description": item.get("summary", ""),
                "highlights": [],
                "url": item.get("url"),
                "technologies": item.get("technologies", []),
                "skills": skills,
            })
    return projects


def fetch_profile(profiles, network_names: List[str]):
    for network in network_names:
        profile = next(
            (p for p in profiles if p.network and p.network.lower() == network.lower()),
            None,
        )
        if profile:
            return profile
    return None


def _extract_resume_base_columns(csv_row: Dict, file_name: str, resume_data, github_data: dict):
    csv_row["file_name"] = file_name

    if resume_data and resume_data.basics:
        basics = resume_data.basics
        csv_row["name"] = basics.name or ""
        csv_row["email"] = basics.email or ""
        csv_row["phone"] = basics.phone or ""
        csv_row["location"] = (
            f"{basics.location.city}, {basics.location.region}"
            if basics.location and (basics.location.city or basics.location.region)
            else ""
        )
        csv_row["summary"] = basics.summary or ""

        if basics.profiles:
            github_profile = fetch_profile(basics.profiles, ["github"])
            linkedin_profile = fetch_profile(basics.profiles, ["linkedin"])
            twitter_profile = fetch_profile(basics.profiles, ["twitter", "x"])
            dev_profile = fetch_profile(basics.profiles, ["dev community", "dev"])
            behance_profile = fetch_profile(basics.profiles, ["behance"])

            for key, profile in [
                ("github", github_profile),
                ("linkedin", linkedin_profile),
                ("twitter", twitter_profile),
                ("dev", dev_profile),
                ("behance", behance_profile),
            ]:
                csv_row[f"{key}_url"] = profile.url if profile else ""
                csv_row[f"{key}_username"] = (
                    profile.username if profile and profile.username else ""
                )
        else:
            for prefix in ["github", "linkedin", "twitter", "dev", "behance"]:
                csv_row[f"{prefix}_url"] = ""
                csv_row[f"{prefix}_username"] = ""
    else:
        for col in ["name", "email", "phone", "location", "summary"]:
            csv_row[col] = ""
        for prefix in ["github", "linkedin", "twitter", "dev", "behance"]:
            csv_row[f"{prefix}_url"] = ""
            csv_row[f"{prefix}_username"] = ""

    if resume_data and resume_data.work:
        csv_row["total_work_experience"] = len(resume_data.work)
        latest_work = resume_data.work[0]
        csv_row["current_position"] = latest_work.position or ""
        csv_row["current_company"] = latest_work.name or ""
    else:
        csv_row["total_work_experience"] = 0
        csv_row["current_position"] = ""
        csv_row["current_company"] = ""

    if resume_data and resume_data.education:
        csv_row["total_education"] = len(resume_data.education)
        highest_edu = resume_data.education[0]
        csv_row["highest_degree"] = highest_edu.studyType or ""
        csv_row["institution"] = highest_edu.institution or ""
    else:
        csv_row["total_education"] = 0
        csv_row["highest_degree"] = ""
        csv_row["institution"] = ""

    if resume_data and resume_data.skills:
        all_skills = []
        for skill_category in resume_data.skills:
            if skill_category.keywords:
                all_skills.extend(skill_category.keywords)
        csv_row["total_skills"] = len(all_skills)
        csv_row["skills_list"] = ", ".join(all_skills[:10])
    else:
        csv_row["total_skills"] = 0
        csv_row["skills_list"] = ""

    csv_row["total_projects"] = (
        len(resume_data.projects) if resume_data and resume_data.projects else 0
    )

    profile_data = github_data.get("profile", github_data or {})
    csv_row["github_repos"] = profile_data.get("public_repos", 0) if isinstance(profile_data, dict) else 0
    csv_row["github_followers"] = profile_data.get("followers", 0) if isinstance(profile_data, dict) else 0
    csv_row["github_following"] = profile_data.get("following", 0) if isinstance(profile_data, dict) else 0
    csv_row["github_created_at"] = profile_data.get("created_at", "") if isinstance(profile_data, dict) else ""
    csv_row["github_bio"] = profile_data.get("bio", "") if isinstance(profile_data, dict) else ""


def _extract_software_scores(csv_row: Dict, evaluation) -> None:
    if evaluation and hasattr(evaluation, "scores"):
        scores = evaluation.scores
        csv_row["open_source_score"] = scores.open_source.score
        csv_row["open_source_max"] = scores.open_source.max
        csv_row["self_projects_score"] = scores.self_projects.score
        csv_row["self_projects_max"] = scores.self_projects.max
        csv_row["production_score"] = scores.production.score
        csv_row["production_max"] = scores.production.max
        csv_row["technical_skills_score"] = scores.technical_skills.score
        csv_row["technical_skills_max"] = scores.technical_skills.max
        csv_row["total_score"] = evaluation.total_score()
        csv_row["total_max"] = evaluation.max_score()
    else:
        for col in [
            "open_source_score", "open_source_max",
            "self_projects_score", "self_projects_max",
            "production_score", "production_max",
            "technical_skills_score", "technical_skills_max",
            "total_score", "total_max",
        ]:
            csv_row[col] = "N/A"


def _extract_sg_scores(csv_row: Dict, evaluation: GenericSGEvaluation) -> None:
    for category_name, category_score in evaluation.scores.items():
        csv_row[f"{category_name}_score"] = category_score.score
        csv_row[f"{category_name}_max"] = category_score.max
        csv_row[f"{category_name}_evidence"] = category_score.evidence
    csv_row["total_score"] = evaluation.total_score()
    csv_row["total_max"] = evaluation.max_score()


def _extract_bonus_deductions(csv_row: Dict, evaluation) -> None:
    if evaluation and hasattr(evaluation, "bonus_points"):
        csv_row["bonus_points"] = evaluation.bonus_points.total
        csv_row["bonus_breakdown"] = evaluation.bonus_points.breakdown
    else:
        csv_row["bonus_points"] = 0
        csv_row["bonus_breakdown"] = ""

    if evaluation and hasattr(evaluation, "deductions"):
        csv_row["deductions"] = evaluation.deductions.total
        csv_row["deduction_reasons"] = evaluation.deductions.reasons
    else:
        csv_row["deductions"] = 0
        csv_row["deduction_reasons"] = ""

    csv_row["key_strengths"] = (
        "; ".join(evaluation.key_strengths)
        if evaluation and hasattr(evaluation, "key_strengths")
        else ""
    )
    csv_row["areas_for_improvement"] = (
        "; ".join(evaluation.areas_for_improvement)
        if evaluation and hasattr(evaluation, "areas_for_improvement")
        else ""
    )


def transform_evaluation_response(
    file_name=None,
    resume_data=None,
    github_data=None,
    evaluation=None,
    role_type: str = "software",
    target_job_title: str = "",
) -> Dict:
    csv_row: Dict = {
        "role_type": role_type,
        "target_job_title": target_job_title or "",
    }
    _extract_resume_base_columns(
        csv_row=csv_row,
        file_name=file_name,
        resume_data=resume_data,
        github_data=github_data or {},
    )
    if isinstance(evaluation, GenericSGEvaluation):
        _extract_sg_scores(csv_row, evaluation)
    else:
        _extract_software_scores(csv_row, evaluation)
    _extract_bonus_deductions(csv_row, evaluation)
    return csv_row


def convert_json_resume_to_text(resume_data: JSONResume) -> str:
    text_parts = []

    if not resume_data:
        return ""

    if resume_data.basics:
        basics = resume_data.basics
        text_parts.append("=== BASIC INFORMATION ===")
        text_parts.append(f"Name: {basics.name or 'Not provided'}")
        text_parts.append(f"Email: {basics.email or 'Not provided'}")
        text_parts.append(f"Phone: {basics.phone or 'Not provided'}")
        text_parts.append(f"Website: {basics.url or 'Not provided'}")
        if basics.summary:
            text_parts.append(f"Summary: {basics.summary}")
        if basics.location:
            loc = basics.location
            location_parts = [
                p for p in [loc.address, loc.city, loc.region, loc.postalCode, loc.countryCode]
                if p
            ]
            if location_parts:
                text_parts.append(f"Location: {', '.join(location_parts)}")
        if basics.profiles:
            text_parts.append("Profiles:")
            for profile in basics.profiles:
                text_parts.append(f"  - {profile.network}: {profile.username} ({profile.url})")

    if resume_data.work:
        text_parts.append("\n=== WORK EXPERIENCE ===")
        for i, work in enumerate(resume_data.work, 1):
            text_parts.append(f"{i}. {work.position} at {work.name}")
            text_parts.append(f"   Period: {work.startDate} - {work.endDate}")
            if work.url:
                text_parts.append(f"   Website: {work.url}")
            if work.summary:
                text_parts.append(f"   Description: {work.summary}")
            if work.highlights:
                text_parts.append("   Key Achievements:")
                for h in work.highlights:
                    text_parts.append(f"   • {h}")

    if resume_data.education:
        text_parts.append("\n=== EDUCATION ===")
        for i, edu in enumerate(resume_data.education, 1):
            text_parts.append(f"{i}. {edu.studyType} in {edu.area}")
            text_parts.append(f"   Institution: {edu.institution}")
            text_parts.append(f"   Period: {edu.startDate} - {edu.endDate}")
            if edu.score:
                text_parts.append(f"   Score: {edu.score}")
            if edu.url:
                text_parts.append(f"   Website: {edu.url}")
            if edu.courses:
                text_parts.append(f"   Courses: {', '.join(edu.courses)}")

    if resume_data.skills:
        text_parts.append("\n=== SKILLS ===")
        for skill in resume_data.skills:
            text_parts.append(f"• {skill.name}")
            if skill.level:
                text_parts.append(f"  Level: {skill.level}")
            if skill.keywords:
                text_parts.append(f"  Keywords: {', '.join(skill.keywords)}")

    if resume_data.projects:
        text_parts.append("\n=== PROJECTS ===")
        for i, project in enumerate(resume_data.projects, 1):
            text_parts.append(f"{i}. {project.name}")
            if project.startDate and project.endDate:
                text_parts.append(f"   Period: {project.startDate} - {project.endDate}")
            if project.description:
                text_parts.append(f"   Description: {project.description}")
            if project.url:
                text_parts.append(f"   URL: {project.url}")
            if project.highlights:
                text_parts.append("   Highlights:")
                for h in project.highlights:
                    text_parts.append(f"   • {h}")

    if resume_data.awards:
        text_parts.append("\n=== AWARDS ===")
        for award in resume_data.awards:
            text_parts.append(f"• {award.title} - {award.awarder} ({award.date})")
            if award.summary:
                text_parts.append(f"  {award.summary}")

    if resume_data.certificates:
        text_parts.append("\n=== CERTIFICATES ===")
        for cert in resume_data.certificates:
            text_parts.append(f"• {cert.name} - {cert.issuer} ({cert.date})")
            if cert.url:
                text_parts.append(f"  URL: {cert.url}")

    if resume_data.publications:
        text_parts.append("\n=== PUBLICATIONS ===")
        for pub in resume_data.publications:
            text_parts.append(f"• {pub.name} - {pub.publisher} ({pub.releaseDate})")
            if pub.url:
                text_parts.append(f"  URL: {pub.url}")
            if pub.summary:
                text_parts.append(f"  {pub.summary}")

    if resume_data.languages:
        text_parts.append("\n=== LANGUAGES ===")
        for lang in resume_data.languages:
            text_parts.append(f"• {lang.language} - {lang.fluency}")

    if resume_data.interests:
        text_parts.append("\n=== INTERESTS ===")
        for interest in resume_data.interests:
            text_parts.append(f"• {interest.name}")
            if interest.keywords:
                text_parts.append(f"  Keywords: {', '.join(interest.keywords)}")

    if resume_data.references:
        text_parts.append("\n=== REFERENCES ===")
        for ref in resume_data.references:
            text_parts.append(f"• {ref.name}")
            if ref.reference:
                text_parts.append(f"  {ref.reference}")

    if resume_data.volunteer:
        text_parts.append("\n=== VOLUNTEER EXPERIENCE ===")
        for v in resume_data.volunteer:
            text_parts.append(f"• {v.position} at {v.organization}")
            text_parts.append(f"  Period: {v.startDate} - {v.endDate}")
            if v.url:
                text_parts.append(f"  Website: {v.url}")
            if v.summary:
                text_parts.append(f"  Description: {v.summary}")
            if v.highlights:
                text_parts.append("  Highlights:")
                for h in v.highlights:
                    text_parts.append(f"  • {h}")

    return "\n".join(text_parts)


def convert_github_data_to_text(github_data: dict) -> str:
    github_text = "\n\n=== GITHUB DATA ===\n"
    if "profile" in github_data:
        profile = github_data["profile"]
        github_text += "GitHub Profile:\n"
        github_text += f"- Username: {profile.get('username', 'N/A')}\n"
        github_text += f"- Name: {profile.get('name', 'N/A')}\n"
        github_text += f"- Bio: {profile.get('bio', 'N/A')}\n"
        github_text += f"- Public Repositories: {profile.get('public_repos', 'N/A')}\n"
        github_text += f"- Followers: {profile.get('followers', 'N/A')}\n"
        github_text += f"- Following: {profile.get('following', 'N/A')}\n"
        github_text += f"- Account Created: {profile.get('created_at', 'N/A')}\n"
        github_text += f"- Last Updated: {profile.get('updated_at', 'N/A')}\n"
    if "projects" in github_data:
        projects = github_data["projects"]
        github_text += f"\nGitHub Projects ({len(projects)} total):\n"
        for i, project in enumerate(projects[:10], 1):
            github_text += f"{i}. {project.get('name', 'N/A')}\n"
            github_text += f"   Description: {project.get('description', 'N/A')}\n"
            github_text += f"   URL: {project.get('github_url', 'N/A')}\n"
            if "github_details" in project:
                details = project["github_details"]
                github_text += f"   Stars: {details.get('stars', 'N/A')}\n"
                github_text += f"   Forks: {details.get('forks', 'N/A')}\n"
                github_text += f"   Language: {details.get('language', 'N/A')}\n"
            github_text += "\n"
    return github_text


def convert_blog_data_to_text(blog_data: dict) -> str:
    blog_text = "\n\n=== BLOG DATA ===\n"
    blog_text += f"Total Blogs Found: {blog_data.get('total_blogs', 'N/A')}\n"
    blog_text += f"Blog Score: {blog_data.get('blog_score', 'N/A')}/10.0\n"
    blog_text += f"Blog Details: {blog_data.get('blog_details', 'N/A')}\n"
    if "blogs" in blog_data:
        blog_text += "\nBlog URLs Found:\n"
        for i, blog in enumerate(blog_data["blogs"][:5], 1):
            blog_text += f"{i}. {blog.get('url', 'N/A')}\n"
            blog_text += f"   Score: {blog.get('score', 'N/A')}/10.0\n"
            blog_text += f"   Details: {blog.get('details', 'N/A')}\n\n"
    return blog_text
