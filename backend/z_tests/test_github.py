from github import Github
from dotenv import load_dotenv
import os

load_dotenv()

g = Github(os.getenv("GITHUB_TOKEN"))

repo = g.get_user().create_repo(
    name="cto-test-repo",
    private=False
)

print(repo.html_url)