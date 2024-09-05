#!/usr/bin/env python3
import json
import logging
import pickle
from sys import base_exec_prefix
from typing import cast

from jira import JIRA
from jira.client import ResultList
from jira.resources import Issue
from jira2gitlab_config import *
from jira2gitlab_secrets import *
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress

loggingConsole = Console(stderr=True)
loggingHandler = RichHandler(console=loggingConsole)
logging.basicConfig(
    level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[loggingHandler]
)

log = logging.getLogger("rich")

# Jira users that could not be mapped to Gitlab users
jira_users = set()


def project_users(jira_project):
    # Load Jira project issues, with pagination (Jira has a limit on returned items)
    # This assumes they will all fit in memory
    start_at = 0
    jira_issues = []
    jira_server = JIRA(server=JIRA_URL, auth=JIRA_ACCOUNT)
    try:
        with open("issue.pickle", "rb") as pickle_file:
            jira_issues = pickle.load(pickle_file, encoding="UTF-8")
    except FileNotFoundError:
        # No picke exists, ignore to have it saved later on
        pass
    if len(jira_issues) == 0:
        result_list = jira_server.search_issues(
            jql_str=f"project={jira_project} ORDER BY key",
            startAt=start_at,
            maxResults=1,
            validate_query=False,
        )
        with Progress(console=loggingConsole) as progress:
            total = cast(ResultList, result_list).total
            task = progress.add_task(
                total=total,
                description=f"Loading Jira issues from project {jira_project}",
            )
            while True:
                jira_issues_batch = jira_server.search_issues(
                    jql_str=f"project={jira_project} ORDER BY key",
                    startAt=start_at,
                    json_result=True,
                    validate_query=False,
                )
                if not jira_issues_batch:
                    break

                start_at = start_at + len(jira_issues_batch)
                jira_issues.extend(jira_issues_batch)
                progress.update(
                    task,
                    advance=len(jira_issues_batch),
                    description=f"Loading Jira issues from project {jira_project} {len(jira_issues)}/{total}",
                )
        with open("issue.pickle", "wb") as pickle_file:
            pickle.dump(jira_issues, pickle_file)

    # Scan issues for users
    with Progress(console=loggingConsole) as progress:
        task = progress.add_task("Scanning issues...", total=len(jira_issues))
        for issue in jira_issues:
            # Reporter
            jira_users.add(issue.fields.reporter if issue.fields.reporter else "jira")

            # Assignee (can be empty)
            if issue.fields.assignee:
                jira_users.add(issue.fields.assignee)

            for comment in issue.fields.comment.comments:
                jira_users.add(comment.author)

            progress.update(task, advance=1)

    log.info(f"Found {len(jira_users)} users")
    result = map(
        lambda x: {
            "display_name": x.displayName,
            "email_address": x.emailAddress,
        },
        jira_users,
    )
    print(json.dumps([*result], indent=2, ensure_ascii=False))


for jira_project, gitlab_project in PROJECTS.items():
    log.info(f"Get participants of {jira_project}")
    project_users(jira_project)
