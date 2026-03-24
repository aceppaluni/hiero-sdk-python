import os
from github import Github
from openai import OpenAI

# --- CONFIG ---
REPO_NAME = os.getenv("GITHUB_REPOSITORY")

# --- INIT ---
gh = Github(os.getenv("GITHUB_TOKEN"))
repo = gh.get_repo(REPO_NAME)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- LOAD CONTEXT FILES ---
def load_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except:
        return ""

guidelines = load_file(".github/GOOD_FIRST_ISSUE_GUIDELINES.md")
template = load_file(".github/ISSUE_TEMPLATE/good_first_issue.md")

# pick a small file to analyze (MVP: first Python file found)
target_file = None
for root, _, files in os.walk("."):
    for file in files:
        if file.endswith(".py") and "test" not in file:
            target_file = os.path.join(root, file)
            break
    if target_file:
        break

code = load_file(target_file)[:4000]  # truncate for token safety

# --- PROMPT ---
prompt = f"""
You are a maintainer of a Python SDK.

Your task is to generate ONE "good first issue".

STRICT RULES:
- Must follow the provided guidelines
- Must follow the exact issue template
- Must be beginner-friendly
- Must take < 2 hours
- Must involve only 1–2 files
- Must include clear acceptance criteria
- If no valid issue exists, return ONLY: NONE

--- GUIDELINES ---
{guidelines}

--- ISSUE TEMPLATE ---
{template}

--- CODE TO ANALYZE ({target_file}) ---
{code}
"""

# --- CALL MODEL ---
response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": prompt}],
)

issue_text = response.choices[0].message.content.strip()

if issue_text == "NONE":
    print("No suitable issue found.")
    exit(0)

# --- CREATE ISSUE ---
issue = repo.create_issue(
    title=issue_text.split("\n")[0][:100],
    body=issue_text,
    labels=["good first issue"]
)

print(f"Issue created: {issue.html_url}")