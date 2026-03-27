import os
import sys
from github import Github
from google import genai

def main():
    # 1. Initialize Clients
    gh = Github(os.getenv("GITHUB_TOKEN"))
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # 2. Identify the PR
    repo = gh.get_repo(os.getenv("GITHUB_REPOSITORY"))
    pr = repo.get_pull(int(os.getenv("PR_NUMBER")))
    
    # 3. Collect the code changes (the diff)
    diff_content = ""
    for file in pr.get_files():
        if file.filename.endswith(('.py', '.js', '.ts')):
            diff_content += f"\nFile: {file.filename}\n{file.patch}"

    if not diff_content:
        print("No relevant code changes found.")
        return

    # 4. Ask Gemini to extract logic
    prompt = f"Act as a Technical Writer. Summarize the logic changes in this code for a 'How-to' guide:\n{diff_content}"
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    
    # 5. Post the draft back to the PR
    pr.create_issue_comment(f"### 🤖 Automated Logic Draft\n\n{response.text}")

if __name__ == "__main__":
    main()
