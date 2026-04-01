import os
import sys
from github import Github, Auth
from google import genai

def main():
    token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_num = os.getenv("PR_NUMBER")
    commit_sha = os.getenv("COMMIT_SHA")
    
    if not all([token, gemini_key, repo_name]):
        print("❌ Error: Missing Credentials.")
        sys.exit(1)

    try:
        # Force the Stable v1 API Version
        client = genai.Client(api_key=gemini_key, http_options={'api_version': 'v1'})
        gh = Github(auth=Auth.Token(token))
        repo = gh.get_repo(repo_name)

        diff_content = ""
        target_obj = None

        # Logic for PR vs. Merge
        if pr_num and pr_num.isdigit():
            target_obj = repo.get_pull(int(pr_num))
            for file in target_obj.get_files():
                if file.patch:
                    diff_content += f"\n--- {file.filename} ---\n{file.patch}\n"
        else:
            target_obj = repo.get_commit(commit_sha)
            for file in target_obj.files:
                if file.patch:
                    diff_content += f"\n--- {file.filename} ---\n{file.patch}\n"

        if not diff_content:
            print("⚠️ No changes found.")
            return

        print("🤖 Consulting Stable Gemini 1.5-Flash...")
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=f"Act as a Tech Writer. Summarize: {diff_content[:8000]}"
        )
        
        comment = f"## 📘 AI Documentation Draft\n\n{response.text}\n\n---\n*Verified Production Build*"
        
        # Post to PR or Commit
        if hasattr(target_obj, 'create_issue_comment'):
            target_obj.create_issue_comment(comment)
        else:
            target_obj.create_comment(comment)
            
        print("🚀 Success!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
