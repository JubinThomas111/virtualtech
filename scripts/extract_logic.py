import os
import sys
from github import Github, Auth
from google import genai
import time

def main():
    # 1. Load and Clean Environment Variables
    token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    raw_pr = os.getenv("PR_NUMBER", "").strip().replace('“', '').replace('”', '').replace('"', '').replace("'", "")
    
    if not all([token, gemini_key, repo_name, raw_pr]):
        print("❌ Error: Missing environment variables.")
        return

    # 2. Initialize Clients
    auth = Auth.Token(token)
    gh = Github(auth=auth)
    client = genai.Client(api_key=gemini_key)
    
    try:
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(int(raw_pr))
        
        # 3. Collect the code changes
        diff_content = ""
        for file in pr.get_files():
            if file.filename.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.go')):
                if file.patch:
                    diff_content += f"\n--- File: {file.filename} ---\n{file.patch}\n"

        # 4. Prepare the Prompt (Handling the "Empty Diff" case)
        if not diff_content:
            # If no diff, we ask Gemini to write a guide based on the PR Title/Description instead
            print("⚠️ No code changes found. Generating guide based on PR metadata...")
            prompt = f"""
            Act as a Senior Technical Writer. 
            The user has not provided specific code changes yet, but here is the Pull Request info:
            Title: {pr.title}
            Description: {pr.body}

            Please draft a high-level 'How-to' guide structure based on this intent. 
            Explicitly mention that the technical implementation details are pending.
            Focus on the why and do not add any back-end details which are not necessary for an admin or an end user of this feature.
            """
            diff_display = "_No relevant code changes (diffs) detected in supported file types._"
        else:
            print("🤖 Code changes found. Consulting Gemini...")
            prompt = f"""
            Act as a Senior Technical Writer. Analyze these code changes and create a 'How-to' guide:
            Include a short descrition, followed by prerequisites, followed by step-by-step information. Add any notes that are necessary
            to administer the feature.
            {diff_content}
            """
            diff_display = f"```diff\n{diff_content}\n```"

        # 5. Call Gemini
        response = client.models.generate_content(model="models/gemini-1.5-flash", contents=prompt)
        
        # 6. Build the Final Report (Always includes both sections)
        final_report = f"""## 🤖 Automated Documentation Draft

{response.text}

---
### 📝 Raw Technical Diff
{diff_display}
"""

        # 7. Post the comment
        print("✅ Posting report to GitHub...")
        pr.create_issue_comment(final_report)
        print("🚀 Done!")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

        # 8. Retry logic if quota is reached
    print("🤖 Consulting Gemini...")
    response = client.models.generate_content(model="models/gemini-1.5-flash", contents=prompt)
except Exception as e:
    if "429" in str(e):
        print("⏳ Quota reached. Waiting 30 seconds before retrying...")
        time.sleep(30)
        response = client.models.generate_content(model="models/gemini-1.5-flash", contents=prompt)
    else:
        raise e
if __name__ == "__main__":
    main()
