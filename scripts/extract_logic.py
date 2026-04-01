import os
import sys
import requests
from github import Github

def main():
    # 1. Get Variables
    token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_num = os.getenv("PR_NUMBER")

    if not gemini_key:
        print("❌ ERROR: GEMINI_API_KEY is missing from GitHub Secrets.")
        sys.exit(1)

    try:
        # 2. Simple Gemini Call (Using direct URL to avoid SDK 404 errors)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": "Write a 1-sentence test message: 'AI Pipeline is Online'"}]}]
        }
        
        print("📡 Testing API Connection...")
        response = requests.post(url, json=payload)
        res_json = response.json()

        if response.status_code != 200:
            print(f"❌ API Failure: {res_json}")
            sys.exit(1)

        ai_text = res_json['candidates'][0]['content']['parts'][0]['text']
        print(f"✅ AI Response: {ai_text}")

        # 3. Post to GitHub
        gh = Github(token)
        repo = gh.get_repo(repo_name)
        # If PR_NUMBER is missing (like on a merge), post to the latest commit instead
        if pr_num and pr_num != "None":
            target = repo.get_pull(int(pr_num))
            target.create_issue_comment(f"🤖 **Test Success:** {ai_text}")
        else:
            commit = repo.get_commit(os.getenv("GITHUB_SHA"))
            commit.create_comment(f"🤖 **Test Success:** {ai_text}")
            
        print("🚀 Success! Comment posted.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
