# SG-ATS
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Forked from interviewstreet/hiring-agent](https://img.shields.io/badge/fork-interviewstreet%2Fhiring--agent-blue)](https://github.com/interviewstreet/hiring-agent)

AI-powered resume evaluation and scoring system, adapted for Singapore job-market use cases.

This repository is **forked from** [interviewstreet/hiring-agent](https://github.com/interviewstreet/hiring-agent) and has been modified by me to support additional job roles with Singapore-specific scoring assumptions, criteria, and grading rubrics.

## Overview

SG-ATS is a resume evaluation pipeline that:
- Extracts structured resume data from PDF files
- Enriches candidate context with GitHub data where relevant
- Uses LLM-based scoring to evaluate candidates
- Outputs structured scoring, strengths, and areas for improvement
- Supports both the original software rubric and multiple Singapore-specific role rubrics
- Provides an interactive mode for user-driven role selection before evaluation

The project keeps the original software engineering evaluation path while extending it for selected Singapore job families where hiring signals are different from generic global ATS scoring.

## Fork attribution

This project is based on the upstream repository:
- [interviewstreet/hiring-agent](https://github.com/interviewstreet/hiring-agent)

The original project focuses on AI-assisted resume evaluation and scoring. This fork extends that idea for practical Singapore-specific screening scenarios.

## What was modified in this fork

Compared with the upstream repository, this fork adds:

- Singapore-specific evaluation paths for:
  - Accounting jobs
  - Auditing jobs
  - HR jobs
  - Banking jobs
- **Merged Software and IT into a single unified rubric** (`software`) covering both software engineering and Singapore IT/tech roles
- **General resume checker** (`general`) — a role-agnostic rubric applicable to any industry or job type
- **Interactive mode** (`interactive.py`) — a menu-driven entry point where users select their target role before evaluation
- Role-based prompt templates using Jinja2
- Flexible scoring schemas for non-software job families
- Role-aware evaluation flow
- CSV export for Singapore-specific role outputs
- Rubric assumptions tailored to Singapore hiring context

## Supported role types

The system currently supports the following `role_type` values:

- `general` — role-agnostic rubric for any industry or job type
- `software` — unified Software Engineering and IT / tech rubric (merges original `software` and `it_sg`)
- `accounting_sg` — Singapore accounting roles
- `audit_sg` — Singapore auditing roles
- `hr_sg` — Singapore HR roles
- `banking_sg` — Singapore banking roles

> **Note:** The previously separate `it_sg` role type has been merged into `software`. If you were using `--role-type it_sg`, switch to `--role-type software`.

## Recent changes

### v2 — General checker + Interactive mode + IT/Software merge

**1. General resume checker (`general`)**

A new role-agnostic evaluation mode that scores any resume across six universal categories:

| Category | Max Score |
|---|---|
| Contact & Summary | 10 |
| Work Experience | 25 |
| Education | 15 |
| Skills | 15 |
| Projects | 20 |
| Formatting & Readability | 15 |
| **Total** | **100** |

Use this when you are not targeting a specific industry or want a quick broad assessment of a resume.

**2. Interactive mode (`interactive.py`)**

A new interactive entry point that guides the user through role selection before running an evaluation. Instead of passing `--role-type` via CLI flags, the user is presented with a numbered menu:

```
[1]  General / Any Role
[2]  Software / IT Jobs
[3]  Accounting Jobs 
[4]  Auditing Jobs 
[5]  HR Jobs 
[6]  Banking Jobs 
```

After selecting a role, the user is prompted for the PDF path, optional target job title, and LLM model name.

Run it with:

```bash
python interactive.py
```

**3. Software + IT merged into one role**

The `it_sg` role type has been removed and consolidated under `software`, now labelled **Software / IT Jobs**. The existing software rubric already covers the relevant technical signals for Singapore IT roles (stacks, deployments, certifications, projects). This simplifies role selection and avoids rubric duplication.

Files removed as a result:
- `prompts/templates/resume_evaluation_criteria_it_sg.jinja` — no longer needed

## Why Singapore-specific rubrics were added

A generic resume-scoring rubric is often too broad for Singapore hiring, because different professions are shaped by different local institutions, frameworks, and regulatory expectations.

This fork therefore uses **assumed role-specific criteria and grading rubrics** based on common Singapore hiring signals. These are not official standards, but practical screening assumptions designed to better reflect how employers in Singapore often assess resumes.

## Rubric justification by role

### 1) Software / IT jobs

The software rubric focuses on:
- Open-source contributions
- Self-initiated projects
- Production or deployment experience
- Technical skills depth

This covers both software engineering candidates and Singapore IT/tech roles. It values applied technical delivery, role-relevant stacks, certifications, and practical execution.

Examples of signals considered:
- Software, cloud, data, infrastructure, cybersecurity, or enterprise systems skills
- Deployments, shipped projects, production systems, APIs, dashboards, automation
- Open-source contributions, GitHub activity
- Certifications or job-ready pathways relevant to local ICT roles

### 2) General (any role)

The general rubric is industry-agnostic and applies to any candidate regardless of profession. It scores on:
- Contact information and professional summary
- Work experience quality and quantification
- Education relevance and completeness
- Skills breadth
- Projects and portfolio
- Resume formatting and ATS readability

Use this as a first-pass check before applying a role-specific rubric.

### 3) Accounting jobs in Singapore

The accounting rubric focuses on:
- Professional certifications and progression
- Accounting experience
- Finance systems and tools
- Communication and reporting capability

Examples of signals considered:
- CA (Singapore), SCAQ, ISCA-related progression
- ACCA, CPA Australia, ICAEW, or similar professional qualifications
- Full-set accounts, month-end close, reconciliations, reporting, GST-related work
- SAP, Oracle, Xero, QuickBooks, advanced Excel, finance reporting tools

This reflects the fact that accounting hiring in Singapore often rewards visible professional progression and practical finance operations capability.

### 4) Auditing jobs in Singapore

The audit rubric focuses on:
- Audit credentials
- Audit experience
- Controls and regulatory familiarity
- Audit tools and analytical ability

Examples of signals considered:
- External or internal audit experience
- Statutory audit, walkthroughs, controls testing, sampling, compliance work
- SFRS familiarity, ACRA-related exposure, audit reporting, risk/control understanding
- CaseWare, TeamMate, Excel, analytics, audit documentation quality

This reflects the stronger importance of assurance exposure, standards familiarity, and structured audit work in Singapore audit hiring.

### 5) HR jobs in Singapore

The HR rubric focuses on:
- HR credentials
- HR operations and specialization
- Stakeholder management
- HR systems and compliance

Examples of signals considered:
- IHRP-related progression
- Recruitment, onboarding, employee lifecycle, C&B, L&D, HRBP exposure
- HRIS / ATS / payroll systems
- Policy execution, coordination, documentation, and business partnering

This reflects how HR roles in Singapore are often evaluated on a mix of operational reliability, people-process ownership, and professional HR capability.

### 6) Banking jobs in Singapore

The banking rubric focuses on:
- Banking credentials
- Banking or operations experience
- Regulatory and risk awareness
- Systems and analytical skills

Examples of signals considered:
- Banking operations, relationship support, compliance, KYC, AML, onboarding, controls
- CMFAS or IBF-related signals where relevant
- Regulated environment exposure
- Reporting, reconciliations, transaction monitoring, analytical tooling

This reflects the higher importance of regulated-environment readiness in Singapore banking and financial-services hiring.

## Important note on the rubrics

These Singapore-specific rubrics are **assumed heuristics**, not official grading standards issued by any authority, employer, or regulator.

They are intended to:
- make resume scoring more relevant to Singapore hiring context,
- provide more explainable screening output,
- and reduce mismatch from using one generic scoring model across very different professions.

They should be treated as decision-support logic, not as a substitute for human hiring judgment.

## Scoring philosophy

All rubrics in this project follow these principles:

- Do **not** score based on name, gender, nationality, race, school prestige, or GPA alone
- Score based on role-relevant evidence
- Prefer demonstrated work, projects, tools, certifications, and outcomes
- Require evidence strings for every category
- Keep output structured and explainable

## Project structure

A simplified view of the main files:

- `score.py` — CLI entry point, caching, orchestration, printing, CSV export
- `interactive.py` — interactive menu-driven entry point for role selection
- `evaluator.py` — LLM evaluation dispatcher for software and Singapore roles
- `models.py` — Pydantic models for resume data and scoring output
- `transform.py` — resume transformation and CSV flattening utilities
- `prompt.py` — model/provider defaults
- `prompts/template_manager.py` — role-aware Jinja template loader
- `prompts/templates/` — scoring criteria templates and system messages
- `pdf.py` — PDF parsing / extraction pipeline
- `github.py` — GitHub enrichment logic

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/suryarajesh13/SG-ATS.git
cd SG-ATS
pip install -r requirements.txt
```

Set up your environment variables as needed using the provided example file.

## Usage

### Interactive mode (recommended)

```bash
python interactive.py
```

Follow the on-screen prompts to select a role, provide the PDF path, and optionally specify a target job title and model.

### CLI — General evaluation (any role / industry)

```bash
python score.py path/to/resume.pdf --role-type general
python score.py path/to/resume.pdf --role-type general --target-job-title "Data Analyst"
```

### CLI — Software / IT evaluation

```bash
python score.py path/to/resume.pdf --role-type software
python score.py path/to/resume.pdf --role-type software --target-job-title "Backend Engineer"
```

### CLI — Singapore accounting role

```bash
python score.py path/to/resume.pdf --role-type accounting_sg --target-job-title "Finance Executive"
```

### CLI — Singapore audit role

```bash
python score.py path/to/resume.pdf --role-type audit_sg --target-job-title "Audit Associate"
```

### CLI — Singapore HR role

```bash
python score.py path/to/resume.pdf --role-type hr_sg --target-job-title "HR Executive"
```

### CLI — Singapore banking role

```bash
python score.py path/to/resume.pdf --role-type banking_sg --target-job-title "AML Analyst"
```

## Output

The system can produce:
- Console-readable evaluation summaries
- Structured category scores
- Bonus points and deductions
- Key strengths
- Areas for improvement
- CSV exports for downstream analysis

## GitHub enrichment

GitHub enrichment is most relevant for:
- `software`

For non-technical roles such as accounting, audit, HR, and banking, GitHub signals are generally less important and are excluded from role-specific scoring emphasis. The `general` mode also does not use GitHub enrichment by default.

## Disclaimer

This repository is an experimental screening and evaluation tool.

It does **not**:
- guarantee hiring outcomes,
- represent official employer policy,
- replace interviews,
- replace regulator guidance,
- or certify candidate suitability.

The Singapore role rubrics are based on practical assumptions about what employers may value, not formal or legally binding standards.

## Acknowledgements

- Upstream project: [interviewstreet/hiring-agent](https://github.com/interviewstreet/hiring-agent)
- Singapore contextual inspiration from publicly available professional and skills frameworks relevant to ICT, accountancy, HR, and banking

## Maintainer note

This fork was created to explore how a resume scoring system can be adapted beyond software engineering and made more relevant for Singapore-specific roles using explainable, role-based evaluation logic. Recent updates add a general-purpose rubric, an interactive user interface for role selection, and a simplified role taxonomy by merging Software and IT into one unified evaluation path.
