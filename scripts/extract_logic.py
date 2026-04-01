import os
import sys
from github import Github, Auth
from google import genai

def main():
    # 1. Environment Setup - Mapping to your Repository Secrets
    token = os.getenv("GITHUB_TOKEN") 
    gemini_key = os.getenv("GEMINI_API_KEY")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_num = os.getenv("PR_NUMBER")
    commit_sha = os.getenv("GITHUB_SHA")
    
    # Validation check for your team's demo
    if not all([token, gemini_key, repo_name]):
        print("❌ Error: Missing Critical Credentials.")
        print(f"DEBUG: Token Active: {bool(token)}, API Key Active: {bool(gemini_key)}")
        sys.exit(1)

    try:
        # 2. Initialize Clients (Forcing Stable v1 API for Broadcom Reliability)
        client = genai.Client(api_key=gemini_key, http_options={'api_version': 'v1'})
        gh = Github(auth=Auth.Token(token))
        repo = gh.get_repo(repo_name)

        diff_content = ""
        target_obj = None

        # 3. Context Logic: Determine if we are in a PR or a direct Push/Merge
        if pr_num and str(pr_num).isdigit() and pr_num != "None":
            print(f"🔍 Context: Analyzing Pull Request #{pr_num}")
            target_obj = repo.get_pull(int(pr_num))
            files = target_obj.get_files()
        elif commit_sha:
            print(f"🔍 Context: Analyzing Commit {commit_sha[:7]}")
            target_obj = repo.get_commit(commit_sha)
            files = target_obj.files
        else:
            print("❌ Error: Could not resolve PR or Commit context.")
            sys.exit(1)

        # 4. Extract Diff Content (The 'Meat' of the documentation)
        for file in files:
            if file.patch:
                diff_content += f"\n--- File: {file.filename} ---\n{file.patch}\n"

        if not diff_content:
            print("⚠️ No relevant code changes found. Skipping AI generation.")
            return

        # 5. Production AI Call (Gemini 1.5-Flash Stable)
        print("🤖 Consulting Stable Gemini 1.5-Flash...")
        
        prompt = f"""
        Act as a Senior Technical Writer. Analyze the following code changes and generate a 
        concise 'How-to' guide for a developer audience.
        
        Format your response like this:
        ### 🎯 Feature Overview
        (Describe what this change does in 2 sentences)
        
        ### 🛠️ Usage / Implementation
        (Step-by-step instructions or code snippets showing how to use the new logic)
        
        ### 📝 Prerequisites
        (List any new dependencies or requirements)
        
        CODE DIFFS TO SUMMARIZE:
        {diff_content[:8000]}
        """

        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        
        if not response.text:
            print("⚠️ AI returned an empty response.")
            return

        # 6. Post the Automated Comment
        comment_body = (
            f"## 📘 AI Documentation Draft\n\n"
            f"{response.text}\n\n"
            f"---\n*Verified Production Build | Powered by GH_TOKEN*"
        )
        
        if hasattr(target_obj, 'create_issue_comment'):
            target_obj.create_issue_comment(comment_body)
            print("🚀 Success! Posted to Pull Request conversation.")
        else:
            target_obj.create_comment(comment_body)
            print("🚀 Success! Posted to Commit history.")

    except Exception as e:
        print(f"❌ Critical Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
