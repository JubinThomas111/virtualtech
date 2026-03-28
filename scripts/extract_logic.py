import os
import sys
from github import Github
from google import genai

def main():
    # 1. Initialize Clients - Added error checking for missing keys
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER")

    if not all([github_token, gemini_key, repo_name, pr_number]):
        print("❌ Error: Missing one or more environment variables.")
        return

    gh = Github(github_token)
    client = genai.Client(api_key=gemini_key)
    
    # 2. Identify the PR
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(int(pr_number))
    
    # 3. Collect the code changes (the diff)
    diff_content = ""
    for file in pr.get_files():
        # Filtering for your specific tech stack
        if file.filename.endswith(('.py', '.js', '.ts')):
            # Using 'patch' to get only what changed
            diff_content += f"\nFile: {file.filename}\n{file.patch}\n"

    if not diff_content:
        print("⚠️ No relevant code changes found in this PR.")
        return

    # 4. Ask Gemini to extract logic
    # We use a structured prompt to ensure the "How-to" guide format
    prompt = f"""
    Act as an expert Technical Writer. 
    Analyze the following code changes and write a clear 'How-to' guide section 
    explaining the NEW logic introduced. Use Markdown.
    
    CODE CHANGES:
    {diff_content}
    """
    
    print("🤖 Sending code to Gemini...")
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=prompt
    )
    
    # 5. Post the draft back to the PR
    if response.text:
        print("✅ Posting comment to GitHub...")
        pr.create_issue_comment(f"### 🤖 Automated Logic Draft\n\n{response.text}")
    else:
        print("❌ Gemini returned an empty response.")

if __name__ == "__main__":
    main()
