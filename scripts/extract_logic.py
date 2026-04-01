import os
import sys
from github import Github, Auth
from google import genai

def main():
    # 1. Setup Environment
    token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_num = os.getenv("PR_NUMBER")
    
    if not all([token, gemini_key, repo_name, pr_num]):
        print("❌ Error: Missing required environment variables.")
        sys.exit(1)

    try:
        # 2. Initialize Clients (Fixed Deprecation)
        client = genai.Client(api_key=gemini_key)
        # Using the new Auth.Token method to avoid warnings
        gh = Github(auth=Auth.Token(token))
        
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(int(pr_num))

        # 3. Extract Diffs
        diff_content = ""
        for file in pr.get_files():
            if file.patch:
                diff_content += f"\n--- File: {file.filename} ---\n{file.patch}\n"
        
        if not diff_content:
            print("⚠️ No changes found.")
            return

        # 4. STABLE MODEL CALL (No gemini-2.0)
        # We use gemini-1.5-flash as the stable anchor
        print("🤖 Consulting gemini-1.5-flash...")
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=f"Act as a Tech Writer. Summarize these changes: {diff_content[:8000]}"
        )
        
        # 5. Post Comment
        comment = f"## 📘 AI Documentation Draft\n\n{response.text}\n\n---\n*Verified Stable Build*"
        pr.create_issue_comment(comment)
        print("🚀 Success!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
