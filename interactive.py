rom __future__ import annotations

import os

ROLE_MENU = {
    "1": ("general", "General / Any Role"),
    "2": ("software", "Software / IT Jobs"),
    "3": ("accounting_sg", "Accounting Jobs"),
    "4": ("audit_sg", "Auditing Jobs"),
    "5": ("hr_sg", "HR Jobs"),
    "6": ("banking_sg", "Banking Jobs"),
}


def prompt_role() -> tuple[str, str]:
    print("")
    print("=" * 55)
    print("  SG-ATS  -  Resume Checker")
    print("=" * 55)
    print("Select the type of resume you are checking:")
    print("")
    for key, (_, label) in ROLE_MENU.items():
        print("  [" + key + "]  " + label)
    print("")
    while True:
        choice = input("Enter your choice (1-6): ").strip()
        if choice in ROLE_MENU:
            role_type, label = ROLE_MENU[choice]
            print("")
            print("Selected: " + label)
            print("")
            return role_type, label
        print("Invalid choice. Please enter a number from 1 to 6.")


def prompt_pdf_path() -> str:
    while True:
        path = input("Path to resume PDF: ").strip().strip('"').strip("'")
        if os.path.isfile(path) and path.lower().endswith(".pdf"):
            return path
        print("File not found or not a PDF: " + path)


def prompt_job_title() -> str:
    return input("Target job title (optional, press Enter to skip): ").strip()


def prompt_model(default_model: str) -> str:
    model = input("LLM model name (press Enter for default '" + default_model + "'): ").strip()
    return model if model else default_model


def main() -> None:
    role_type, _ = prompt_role()
    pdf_path = prompt_pdf_path()
    job_title = prompt_job_title()

    from prompt import DEFAULT_MODEL
    from score import main as run_evaluation

    model = prompt_model(DEFAULT_MODEL)

    print("")
    print("Evaluating resume, please wait...")
    print("")
    run_evaluation(
        pdf_path=pdf_path,
        role_type=role_type,
        target_job_title=job_title,
        model_name=model,
    )


if __name__ == "__main__":
    main()

