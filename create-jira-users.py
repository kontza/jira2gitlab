#!/usr/bin/env python3
import json
import logging
from uuid import uuid4

import gitlab
from jira2gitlab_config import *
from jira2gitlab_secrets import *
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import track

console = Console(stderr=True)
FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")

access_token = GITLAB_TOKEN
project_id = 5
author_username = GITLAB_ADMIN

if __name__ == "__main__":
    log.info("Connecting...")
    gl = gitlab.Gitlab(GITLAB_URL, private_token=access_token, keep_base_url=True)
    log.info("  ok")

    log.info("Read users from JSON...")
    users = []
    with open("jira-users.json") as users_file:
        users = json.load(users_file)
    log.info("  ok")

    for user in track(users, description="Create users into Gitlab..."):
        try:
            gl.users.create(
                {
                    "email": user["email_address"],
                    "username": user["user_name"].split("@")[0],
                    "name": user["display_name"],
                    "password": str(uuid4()),
                }
            )
        except Exception as e:
            log.error(f"  failed to create {user['user_name']}: {e}")
