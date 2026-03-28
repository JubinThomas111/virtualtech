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

        # 4. Prepare the Prompt
        if not diff_content:
            print("⚠️ No code changes found. Generating guide based on PR metadata...")
            prompt = f"""
            Act as a Senior Technical Writer. 
            PR Title: {pr.title}
            PR Description: {pr.body}

            Draft a high-level 'How-to' guide structure. 
            - Focus on the 'Why' (Purpose).
            - Do not include back-end details unnecessary for admins or end-users.
            - Explicitly mention that technical implementation details are pending.
            """
            diff_display = "_No relevant code changes detected in supported file types._"
        else:
            print("🤖 Code changes found. Preparing analysis...")
            prompt = f"""
            Act as a Senior Technical Writer. Analyze these code changes and create a professional 'How-to' guide.
            Use the following structure:
            1. **Short Description**: What this feature does.
            2. **Prerequisites**: What is needed before using/administering this.
            3. **Step-by-step Instructions**: How to use or configure the feature.
            4. **Administrative Notes**: Necessary notes for system administration.
            
            CODE CHANGES:
            {diff_content}
            """
            diff_display = f"```diff\n{diff_content}\n```"

        # 5. Call Gemini with nested Retry Logic
        print("🤖 Consulting Gemini 1.5 Flash...")
        try:
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        except Exception as e:
            if "429" in str(e):
                print("⏳ Quota reached. Waiting 60 seconds (Free Tier reset)...")
                time.sleep(60)
                response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            else:
                raise e
        
        # 6. Build and Post the Final Report
        final_report = f"""## 🤖 Automated Documentation Draft

{response.text}

---
### 📝 Raw Technical Diff
{diff_display}
"""

        print("✅ Posting report to GitHub...")
        pr.create_issue_comment(final_report)
        print("🚀 Done!")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
