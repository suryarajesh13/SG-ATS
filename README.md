# SG-ATS — AI Resume Scoring for Singapore Job Market

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Forked from interviewstreet/hiring-agent](https://img.shields.io/badge/fork-interviewstreet%2Fhiring--agent-blue)](https://github.com/interviewstreet/hiring-agent)

> Forked from [interviewstreet/hiring-agent](https://github.com/interviewstreet/hiring-agent).  
> Extended and adapted by [@suryarajesh13](https://github.com/suryarajesh13) for Singapore-specific
> job roles with localised grading rubrics across Audit, Accounting, IT, HR, and Banking.

---

## Table of Contents

- [Overview](#overview)
- [Supported Role Types](#supported-role-types)
- [AI Model Setup](#ai-model-setup)
- [Installation](#installation)
- [Usage](#usage)
- [Singapore Scoring Rubrics](#singapore-scoring-rubrics)
- [Caching](#caching)
- [Project Structure](#project-structure)
- [License](#license)
- [References](#references)

---

## Overview

SG-ATS is an AI-powered resume evaluation system that scores resumes against role-specific rubrics
tailored to the Singapore job market. It extracts structured data from PDF resumes using a local LLM
via Ollama, then evaluates the candidate against a scoring framework that reflects Singapore's
professional certification standards, industry expectations, and regulatory context.

This project was forked from [interviewstreet/hiring-agent](https://github.com/interviewstreet/hiring-agent)
and has been significantly modified to support Singapore-specific job roles with assumed grading criteria
and rubrics based on local industry standards.

---

## Supported Role Types

| Flag              | Role                           |
|-------------------|--------------------------------|
| `software`        | Software Engineering (default) |
| `it_sg`           | IT Jobs (Singapore)            |
| `accounting_sg`   | Accounting (Singapore)         |
| `audit_sg`        | Auditing (Singapore)           |
| `hr_sg`           | HR (Singapore)                 |
| `banking_sg`      | Banking & Financial Services   |

---

## AI Model Setup

SG-ATS uses **Ollama** to run LLMs locally on your machine. No API key is required for Ollama models.

### Step 1 — Install Ollama

Download and install from https://ollama.com/download.  
Choose the **Windows** installer and run it.

Verify installation:

```powershell
ollama --version
```

---

### Step 2 — Pull a Model

SG-ATS works best with `gemma3:12b`. Pull it before running the tool:

```powershell
ollama pull gemma3:12b
```

**Model recommendations by RAM:**

| Your RAM | Recommended Model | Notes                                       |
|----------|-------------------|---------------------------------------------|
| < 6 GB   | `phi3:mini`       | Fast but lower accuracy on structured JSON  |
| 8 GB     | `gemma2:9b`       | Good speed/accuracy balance                 |
| 16 GB    | `gemma3:12b`      | ✅ Best overall — recommended               |
| 32 GB+   | `gemma3:27b`      | Highest accuracy, slower                    |

> `gemma3:12b` is the recommended default. It scores highest on structured JSON output tasks,
> which this tool relies on for section extraction and evaluation. It runs well on 16 GB RAM.

---

### Step 3 — Start Ollama

Keep Ollama running in a **separate terminal** before using SG-ATS:

```powershell
ollama serve
```

Ollama listens on `http://localhost:11434` by default. You can confirm it is running by visiting
that URL in a browser — you should see `Ollama is running`.

---

### Step 4 — Configure the Model

Set the default model in `prompt.py`:

```python
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemma3:12b")
```

Or override it at runtime with the `--model` flag (see Usage below).

---

### Using Gemini Instead (Optional)

If you prefer Google Gemini over a local model, add your API key to a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

Then pass a Gemini model name at runtime:

```powershell
python score.py resume.pdf --role-type audit_sg --model gemini-1.5-flash
```

Get a Gemini API key at https://aistudio.google.com/app/apikey.

---

### Common Model Errors

| Error                              | Fix                                         |
|------------------------------------|---------------------------------------------|
| `ModuleNotFoundError`              | Run `pip install -r requirements.txt` again |
| `Connection refused on port 11434` | Ollama isn't running — run `ollama serve`   |
| `404 Not Found` on `/api/chat`     | Model not pulled — run `ollama pull gemma3:12b` |
| `.env not loaded`                  | Run `pip install python-dotenv`             |

---

## Installation

```powershell
# Clone the repo
git clone https://github.com/suryarajesh13/SG-ATS.git
cd SG-ATS

# Create a Python 3.12 environment (recommended)
conda create -n sgats python=3.12 -y
conda activate sgats

# Install dependencies
pip install -r requirements.txt
```

> ⚠️ Python 3.14 is not fully supported. Use Python 3.12 to avoid build failures with
> `pydantic-core` and other compiled packages.

---

## Usage

```powershell
python score.py "path\\to\\resume.pdf" --role-type <role> --target-job-title "<title>"
```

**Examples:**

```powershell
# Audit role
python score.py "C:\\resumes\\john.pdf" --role-type audit_sg --target-job-title "Associate FAAS EY"

# IT role with a specific model
python score.py "C:\\resumes\\jane.pdf" --role-type it_sg --target-job-title "Data Analyst" --model gemma3:12b

# Software engineering (default rubric)
python score.py "C:\\resumes\\alex.pdf"
```

**All flags:**

| Flag                  | Description                                   | Default      |
|-----------------------|-----------------------------------------------|--------------|
| `pdf_path`            | Path to resume PDF (required, positional)     | —            |
| `--role-type`         | Evaluation rubric to use                      | `software`   |
| `--target-job-title`  | Specific job title for context-aware scoring  | *(empty)*    |
| `--model`             | Ollama or Gemini model name                   | `gemma3:12b` |

---

## Singapore Scoring Rubrics

Each Singapore role is scored across 4 categories (total 100 points) plus optional bonus/deductions.

### Audit (`audit_sg`)

| Category                   | Max | Signals                                                    |
|----------------------------|-----|------------------------------------------------------------|
| `sg_audit_credentials`     | 30  | CA Singapore, ACCA, ICAEW, ISCA, CPA Australia             |
| `audit_experience`         | 35  | External/internal audit, SFRS, ACRA, walkthroughs          |
| `controls_and_regulatory`  | 25  | MAS regulations, compliance, risk frameworks               |
| `audit_tools_and_analysis` | 10  | CaseWare, TeamMate, Excel, data analytics                  |

**Rubric justification:** Singapore audit professionals are expected to hold qualifications
recognised by ISCA or equivalent bodies (ACCA, ICAEW, CPA Australia). Statutory audit exposure
under SFRS and familiarity with ACRA-regulated filings are core requirements for public accounting
firms such as the Big 4 operating in Singapore.

---

### Accounting (`accounting_sg`)

| Category                     | Max | Signals                                                  |
|------------------------------|-----|----------------------------------------------------------|
| `sg_certifications`          | 30  | CA Singapore, SCAQ, ISCA, ACCA, CPA Australia, ICAEW    |
| `accounting_experience`      | 35  | Full-set accounts, GST, month-end close, reporting       |
| `finance_systems`            | 25  | SAP, Oracle, Xero, QuickBooks, advanced Excel            |
| `professional_communication` | 10  | Report writing, stakeholder communication                |

**Rubric justification:** Singapore accounting roles require IRAS GST compliance awareness and
familiarity with SFRS. CA (Singapore) via ISCA is the primary professional qualification for
accountants in Singapore. Only a registered Public Accountant under ACRA may sign off on
Singapore-incorporated company audits.

---

### IT (`it_sg`)

| Category                  | Max | Signals                                                    |
|---------------------------|-----|------------------------------------------------------------|
| `sg_technical_skills`     | 35  | Software, cloud, data, infrastructure, cybersecurity       |
| `projects_and_delivery`   | 30  | Shipped projects, APIs, dashboards, automation             |
| `production_experience`   | 25  | Internship/work exposure, real systems, client delivery    |
| `professional_readiness`  | 10  | ICT certifications, communication skills                   |

**Rubric justification:** Based on Singapore's ICT Skills Framework and IMDA's national digital
talent strategy. Practical delivery and production exposure are weighted highly as Singapore
employers prioritise candidates who can contribute immediately in agile delivery environments.

---

### HR (`hr_sg`)

| Category                             | Max | Signals                                          |
|--------------------------------------|-----|--------------------------------------------------|
| `sg_hr_credentials`                  | 30  | IHRP certification, HR degrees or diplomas       |
| `hr_operations_and_specialisation`   | 35  | Recruitment, onboarding, C&B, L&D, HRBP          |
| `stakeholder_management`             | 25  | Business partnering, policy execution            |
| `hr_systems_and_compliance`          | 10  | HRIS, ATS, payroll, MOM compliance               |

**Rubric justification:** IHRP (Institute for Human Resource Professionals) is the national HR
credentialing body in Singapore. MOM compliance (Employment Act, CPF, work pass regulations) is
a mandatory operational requirement for all HR professionals in Singapore.

---

### Banking (`banking_sg`)

| Category                   | Max | Signals                                                    |
|----------------------------|-----|------------------------------------------------------------|
| `sg_banking_credentials`   | 30  | CMFAS, IBF certifications, finance qualifications          |
| `banking_experience`       | 35  | Banking ops, KYC, AML, onboarding, reconciliations         |
| `regulatory_and_risk`      | 25  | MAS regulations, AML/CFT, compliance, monitoring           |
| `systems_and_analysis`     | 10  | Excel, reporting tools, banking systems                    |

**Rubric justification:** MAS (Monetary Authority of Singapore) regulatory compliance and
CMFAS/IBF certifications are baseline requirements for client-facing and operations roles in
Singapore financial institutions. AML/CFT knowledge is mandated under Singapore's PSMA and
Banking Act frameworks.

> ⚠️ These rubrics are designed for resume screening and prioritisation only. They are not a
> substitute for human hiring judgment or professional licensing advice. Scores do not consider
> name, gender, nationality, race, school prestige, or GPA alone.

---

## Caching

When `DEVELOPMENT_MODE = True` in `config.py`, the tool caches results to avoid re-running
expensive LLM calls:

| Cache File                                              | Contents              |
|---------------------------------------------------------|-----------------------|
| `cache/resumecache_<name>.json`                         | Parsed resume JSON    |
| `cache/githubcache_<name>.json`                         | GitHub profile data   |
| `cache/evalcache_<name>_<role>_<title>_<model>.json`    | Evaluation scores     |

Delete the relevant cache file to force a fresh LLM run.

---

## Project Structure

```
SG-ATS/
├── score.py                    # Main entry point
├── evaluator.py                # LLM evaluation logic
├── pdf.py                      # PDF text extraction and section parsing
├── models.py                   # Pydantic data models
├── llm_utils.py                # LLM provider utilities
├── prompt.py                   # Model config and parameters
├── github.py                   # GitHub profile fetching
├── transform.py                # Data transformation utilities
├── config.py                   # App configuration
├── prompts/
│   ├── template_manager.py     # Jinja2 template routing
│   └── templates/              # Role-specific prompt templates
│       ├── system_message.jinja
│       ├── basics.jinja
│       ├── work.jinja
│       ├── education.jinja
│       ├── skills.jinja
│       ├── projects.jinja
│       ├── awards.jinja
│       ├── resume_evaluation_system_message.jinja
│       ├── resume_evaluation_system_message_sg.jinja
│       ├── resume_evaluation_criteria.jinja
│       ├── resume_evaluation_criteria_it_sg.jinja
│       ├── resume_evaluation_criteria_accounting_sg.jinja
│       ├── resume_evaluation_criteria_audit_sg.jinja
│       ├── resume_evaluation_criteria_hr_sg.jinja
│       └── resume_evaluation_criteria_banking_sg.jinja
├── cache/                      # Auto-generated cache files
├── LICENSE
├── NOTICE
└── requirements.txt
```

---

## License

MIT License

Modifications Copyright (c) 2026 Suryaraj  
Original Copyright (c) 2025 HackerRank (InterviewStreet Inc.)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## References

- [ISCA / CA (Singapore)](https://isca.org.sg)
- [ACCA Singapore](https://www.accaglobal.com/sg/en.html)
- [IHRP Certification](https://ihrp.sg/certifications-overview/)
- [IBF / CMFAS Singapore](https://www.ibf.org.sg)
- [MAS Regulations](https://www.mas.gov.sg)
- [IMDA ICT Skills Framework](https://www.imda.gov.sg)
- [Ollama](https://ollama.com)
- [Original upstream repo — interviewstreet/hiring-agent](https://github.com/interviewstreet/hiring-agent)
"""
