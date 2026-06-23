from __future__ import annotations

import logging
import re

import requests

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


def _extract_username(github_url: str) -> str | None:
    match = re.search(r"github\.com/([^/]+)", github_url)
    return match.group(1) if match else None


def fetch_and_display_github_info(github_url: str) -> dict:
    username = _extract_username(github_url)
    if not username:
        logger.warning("Could not extract GitHub username from URL: %s", github_url)
        return {}

    try:
        profile_resp = requests.get(
            f"{GITHUB_API_BASE}/users/{username}",
            timeout=10,
        )
        profile_resp.raise_for_status()
        profile = profile_resp.json()

        repos_resp = requests.get(
            f"{GITHUB_API_BASE}/users/{username}/repos",
            params={"sort": "updated", "per_page": 10},
            timeout=10,
        )
        repos_resp.raise_for_status()
        repos = repos_resp.json()

        repo_summaries = [
            {
                "name": r.get("name"),
                "description": r.get("description"),
                "language": r.get("language"),
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "url": r.get("html_url"),
            }
            for r in repos
            if not r.get("fork", False)
        ]

        github_data = {
            "profile": {
                "username": profile.get("login"),
                "name": profile.get("name"),
                "bio": profile.get("bio"),
                "public_repos": profile.get("public_repos", 0),
                "followers": profile.get("followers", 0),
                "url": profile.get("html_url"),
            },
            "repos": repo_summaries,
        }

        logger.info(
            "Fetched GitHub profile for %s (%d repos)",
            username,
            len(repo_summaries),
        )
        return github_data

    except requests.RequestException as exc:
        logger.warning("Failed to fetch GitHub data for %s: %s", username, exc)
        return {}
