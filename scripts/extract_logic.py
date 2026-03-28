import os
import sys
from github import Github, Auth
from google import genai

def main():
    # 1. Load and Clean Environment Variables
    # These are the "exports" you run in your Mac terminal
    token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    
    # Cleaning PR_NUMBER to remove accidental spaces or "Smart Quotes" (curly quotes)
    raw_pr = os.getenv("PR_NUMBER", "").strip().replace('“', '').replace('”', '').replace('"', '').replace("'", "")
    
    if not all([token, gemini_key, repo_name, raw_pr]):
        print("❌ Error: Missing environment variables. Please check your exports.")
        print(f"DEBUG -> TOKEN: {'Set' if token else 'MISSING'}")
        print(f"DEBUG -> REPO: {repo_name if repo_name else 'MISSING'}")
        print(f"DEBUG -> PR: {raw_pr if raw_pr else 'MISSING'}")
        return

    # 2. Initialize Clients (Using modern Auth to avoid Deprecation Warnings)
    auth = Auth.Token(token)
    gh = Github(auth=auth)
    client = genai.Client(api_key=gemini_key)
    
    try:
        # 3. Connect to the Specific Repository and Pull Request
        print(f"📂 Connecting to {repo_name}...")
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(int(raw_pr))
        
        print(f"🔍 Analyzing PR #{raw_pr}: '{pr.title}'")
        
        # 4. Collect the code changes (the diff)
        diff_content = ""
        files = pr.get_files()
        
        for file in files:
            # Filter for your technical writing target files
            if file.filename.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.go')):
                if file.patch:
                    diff_content += f"\n--- File: {file.filename} ---\n{file.patch}\n"

        if not diff_content:
            print("⚠️ No relevant code changes found in this PR to analyze.")
            return

        # 5. Ask Gemini to extract logic for the Tech Writer
        # This prompt is optimized for technical documentation
        prompt = f"""
        Act as a Senior Technical Writer. 
        Analyze the following code changes and create a professional 'How-to' guide section.
        
        Your response must include:
        1. **Purpose**: Explain WHY these changes were made and what problem they solve.
        2. **Logic Flow**: A step-by-step breakdown of how the new code functions.
        3. **Writer's Note**: Mention any security implications, edge cases, or dependencies.

        CODE CHANGES TO ANALYZE:
        {diff_content}
        """
        
        print("🤖 Consulting Gemini 2.0 Flash for logic extraction...")
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        
        # 6. Build the Final Markdown Report for the PR Comment
        # We combine the AI's explanation with the raw color-coded diff
        final_report = f"""## 🤖 Automated Documentation Draft
        
{response.text}

---
### 📝 Raw Technical Diff
*Technical writers: Use the diff below to verify the AI's logic extraction for accuracy.*

```diff
{diff_content}
"""
        # 7. Post the comment to the Pull Request Conversation tab
    print("✅ Posting comprehensive report to GitHub...")
    pr.create_issue_comment(final_report)
    print(f"🚀 Success! View the update here: https://github.com/{repo_name}/pull/{raw_pr}")

except Exception as e:
    print(f"❌ An error occurred: {e}")

if name == "main":
main()

        
