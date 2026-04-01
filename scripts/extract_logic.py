import os
import sys
from github import Github, Auth
from google import genai

def main():
    # 1. Setup
    token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_num = os.getenv("PR_NUMBER")
    commit_sha = os.getenv("COMMIT_SHA")
    
    if not all([token, gemini_key, repo_name]):
        print("❌ Error: Missing Critical Credentials.")
        sys.exit(1)

    try:
        # 2. Initialize
        client = genai.Client(api_key=gemini_key)
        gh = Github(auth=Auth.Token(token))
        repo = gh.get_repo(repo_name)

        diff_content = ""
        target_object = None

        # 3. Context-Aware Extraction
        if pr_num and pr_num != "None" and pr_num != "":
            print(f"🔍 Event: Pull Request #{pr_num}")
            target_object = repo.get_pull(int(pr_num))
            for file in target_object.get_files():
                if file.patch:
                    diff_content += f"\n--- File: {file.filename} ---\n{file.patch}\n"
        else:
            print(f"🔍 Event: Merge/Push detected (SHA: {commit_sha[:7]})")
            # If no PR, get the diff from the specific commit
            commit = repo.get_commit(commit_sha)
            target_object = commit
            for file in commit.files:
                if file.patch:
                    diff_content += f"\n--- File: {file.filename} ---\n{file.patch}\n"

        if not diff_content:
            print("⚠️ No code changes detected.")
            return

        # 4. Gemini Analysis (Stable 1.5-Flash)
        print("🤖 Generating Documentation...")
        prompt = f"Act as a Senior Tech Writer. Generate a Diátaxis 'How-to' guide for these changes: {diff_content[:8000]}"
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        
        # 5. Smart Posting
        comment_body = f"## 📘 AI Documentation Draft\n\n{response.text}\n\n---\n*Type: Automated CI/CD Documentation*"
        
        if hasattr(target_object, 'create_issue_comment'):
            # It's a Pull Request
            target_object.create_issue_comment(comment_body)
        else:
            # It's a Commit (Merge to Main)
            target_object.create_comment(comment_body)
            
        print("🚀 Success! Documentation posted.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
