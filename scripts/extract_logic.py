import os
import sys
import time
from github import Github, Auth
from google import genai

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
    
    # FORCING API VERSION V1 TO AVOID 404 NOT FOUND
    client = genai.Client(
        api_key=gemini_key,
        http_options={'api_version': 'v1'}
    )
    
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
            prompt = f"Draft a high-level 'How-to' guide for: {pr.title}."
            diff_display = "_No code changes found._"
        else:
            prompt = f"""
            Act as a Senior Technical Writer. Create a professional 'How-to' guide.
            Structure: 
            1. Short Description
            2. Prerequisites
            3. Step-by-step instructions
            4. Administrative notes
            
            Focus on the user's perspective.
            CODE: {diff_content}
            """
            diff_display = f"```diff\n{diff_content}\n```"

        print("🤖 Consulting Gemini 1.5 Flash (v1 Stable)...")
        # 5. Call Gemini
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        
        # 6. Build the Final Report
        final_report = f"## 🤖 Automated Documentation Draft\n\n{response.text}\n\n---\n### 📝 Raw Technical Diff\n{diff_display}"

        # 7. Post the comment
        print("✅ Posting report to GitHub...")
        pr.create_issue_comment(final_report)
        print("🚀 Success! Check your PR.")

    except Exception as e:
        if "429" in str(e):
            print("⏳ Rate limit hit. Waiting 60s for reset...")
            time.sleep(60)
            # Retry attempt
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            pr.create_issue_comment(f"## 🤖 Automated Documentation Draft\n\n{response.text}\n\n---\n### 📝 Raw Diff\n{diff_display}")
        else:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
