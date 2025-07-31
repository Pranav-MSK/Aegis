# cython: language_level=3
import os
import subprocess

def check_installation_information():
    output = {
        "is_git_repo": False,
        "git_branch": None,
        "git_commit": None,
        "git_repo": None,
        "last_commit_date": None,
        "last_commit_message": None,
        "update_available": False
    }

    if not os.path.isdir(".git"):
        return output

    try:
        with open(".git/HEAD", "r") as f:
            head = f.read().strip()
    except IOError:
        return output

    if head.startswith("ref: refs/heads/"):
        output["is_git_repo"] = True
        output["git_branch"] = head.replace("ref: refs/heads/", "")

    try:
        result = subprocess.run(["git", "log", "-1", "--pretty=format:%H|%ad|%s", "--date=short"],
                                capture_output=True, text=True, check=True)
        commit_data = result.stdout.split("|")
        output["git_commit"] = commit_data[0]
        output["last_commit_date"] = commit_data[1]
        output["last_commit_message"] = commit_data[2]
    except subprocess.CalledProcessError:
        pass

    try:
        result = subprocess.run(["git", "status", "-uno"], capture_output=True, text=True, check=True)
        output["update_available"] = "up to date" not in result.stdout
    except subprocess.CalledProcessError:
        pass

    return output
