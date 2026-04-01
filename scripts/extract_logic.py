import os
import sys
from github import Github, Auth
from google import genai

def main():
    # 1. Environment Setup
    token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_num = os.getenv("PR_NUMBER")
    # Fallback to the default GITHUB_SHA if a specific COMMIT_SHA isn't provided
    commit_sha = os.getenv("COMMIT_SHA") or os.getenv("GITHUB_SHA")
    
    if not all([token, gemini_key, repo_name]):
        print("❌ Error: Missing Critical Credentials (GITHUB_TOKEN or GEMINI_API_KEY).")
        sys.exit(1)

    try:
        # 2. Initialize Stable Clients
        # CRITICAL: We force 'v1' here to bypass the 404 v1beta errors
        client = genai.Client(
            api_key=gemini_key, 
            http_options={'api_version': 'v1'}
        )
        gh = Github(auth=Auth.Token(token))
        repo = gh.get_repo(repo_name)

        diff_content = ""
        target_obj = None

        # 3. Dynamic Context Detection (PR vs. Merge)
        if pr_num and str(pr_num).isdigit():
            print(f"🔍 Context: Analyzing Pull Request #{pr_num}")
            target_obj = repo.get_pull(int(pr_num))
            files = target_obj.get_files()
        elif commit_sha:
            print(f"🔍 Context: Analyzing Commit {commit_sha[:7]}")
            target_obj = repo.get_commit(commit_sha)
            files = target_obj.files
        else:
            print("❌ Error: Could not resolve a PR or Commit context.")
            sys.exit(1)

        # 4. Extract Code Diffs
        for file in files:
            if file.patch:
                diff_content += f"\n--- File: {file.filename} ---\n{file.patch}\n"

        if not diff_content:
            print("⚠️ No relevant code changes found. Skipping AI generation.")
            return

        # 5. Production AI Call
        print("🤖 Consulting Gemini 1.5-Flash (Stable Production Tier)...")
        
        prompt = f"""
        Act as a Senior Technical Writer at Broadcom. 
        Analyze the following code changes and generate a Diátaxis-style 'How-to' guide.
        
        Format:
        ### 🎯 Feature Overview
        ### 🛠️ Implementation Steps
        ### 📝 Technical Prerequisites
        
        CODE CHANGES:
        {diff_content[:10000]}
        """

        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        
        if not response.text:
            print("⚠️ AI returned an empty response.")
            return

        # 6. Post Documentation to GitHub
        comment_body = (
            f"## 📘 Automated AI Documentation Draft\n\n"
            f"{response.text}\n\n"
            f"---\n*Verified Production Pipeline | Stable 1.5-Flash*"
        )
        
        if hasattr(target_obj, 'create_issue_comment'):
            # It's a Pull Request
            target_obj.create_issue_comment(comment_body)
            print("🚀 Success! Posted to Pull Request.")
        else:
            # It's a direct Commit (post-merge)
            target_obj.create_comment(comment_body)
            print("🚀 Success! Posted to Commit History.")

    except Exception as e:
        print(f"❌ Critical Failure: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
