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
    commit_sha = os.getenv("GITHUB_SHA")
    
    if not all([token, gemini_key, repo_name]):
        print("❌ Error: Missing Credentials (GITHUB_TOKEN or GEMINI_API_KEY).")
        sys.exit(1)

    try:
        # 2. Initialize Clients
        # SDK handles stable endpoint discovery automatically
        client = genai.Client(api_key=gemini_key)
        gh = Github(auth=Auth.Token(token))
        repo = gh.get_repo(repo_name)

        diff_content = ""
        target_obj = None

        # 3. Context Detection (PR vs Push)
        if pr_num and str(pr_num).isdigit() and pr_num != "None":
            print(f"🔍 Context: PR #{pr_num}")
            target_obj = repo.get_pull(int(pr_num))
            files = target_obj.get_files()
        else:
            print(f"🔍 Context: Push/Merge (SHA: {commit_sha[:7]})")
            target_obj = repo.get_commit(commit_sha)
            files = target_obj.files

        for file in files:
            if file.patch:
                diff_content += f"\n--- {file.filename} ---\n{file.patch}\n"

        if not diff_content:
            print("⚠️ No changes found.")
            return

        # 4. AI Generation 
        print("🤖 Consulting Gemini 1.5-Flash (Production Tier)...")
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=f"Summarize these code as a Tech Writer:
            1. Summary - Include 2-3 sentences as a summary of the code
            2. Prerequisites
            3. How-to procedure
            4. Limitations
            5. References
            
            {diff_content[:8000]}"
        )
        
        comment = f"## 📘 AI Documentation Draft\n\n{response.text}\n\n---\n*Verified Production Build*"
        
        # 5. Post to GitHub
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
