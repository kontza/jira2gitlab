#!/usr/bin/env python3
import gitlab
from jira2gitlab_secrets import *
from rich.console import Console

console = Console()


access_token = GITLAB_TOKEN
project_id = 0000
author_username = GITLAB_ADMIN

console.log("Connecting...")
gl = gitlab.Gitlab(
    "https://gitlab.example.com", private_token=access_token, keep_base_url=True
)
console.log("  ... ok")
console.log("Get project...")
project = gl.projects.get(id=project_id)
console.log("  ... ok")
console.log("Get issues...")
issues = project.issues.list(iterator=True)
console.log("  ... ok")
console.log("Iterate over issues...")
for issue in issues:
    if issue.author["username"] == author_username:
        console.log(f"... deleting {issue.title}...")
        issue.delete()
        console.log("... ... ok")
    else:
        console.log(f"... not matched {issue.author['username']}")
