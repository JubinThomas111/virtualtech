import os
import sys
from github import Github, Auth
from google import genai

def main():
    token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_num = os.getenv("PR_NUMBER")
    commit_sha = os.getenv("GITHUB_SHA")
    
    if not all([token, gemini_key, repo_name]):
        print("❌ Error: Missing Credentials.")
        sys.exit(1)

    try:
        # FORCE STABLE V1 API - This bypasses all 404/v1beta issues
        client = genai.Client(api_key=gemini_key, http_options={'api_version': 'v1'})
        gh = Github(auth=Auth.Token(token))
        repo = gh.get_repo(repo_name)

        diff_content = ""
        target_obj = None

        # Logic for PR vs. Push
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

        print("🤖 Consulting Stable Gemini 1.5-Flash...")
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=f"Act as a Tech Writer. 

            Act as a Senior Technical Writer. Analyze the following code changes and generate a 
        concise 'How-to' guide for a developer audience.
        
        Format:
        ### 🎯 Feature Overview
        (Describe what this change does in 2 sentences)
        
        ### 🛠️ Usage / Implementation
        (Step-by-step instructions or code snippets showing how to use the new logic)
        
        ### 📝 Prerequisites
        (List any new dependencies or requirements)
        
        CODE DIFFS:
        {diff_content}
            Summarize these changes: {diff_content[:8000]}"
        )
        
        comment = f"## 📘 AI Documentation Draft\n\n{response.text}\n\n---\n*Verified Production Build*"
        
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
