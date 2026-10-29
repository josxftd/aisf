"""Commit changed files under given paths through GitHub's REST API.

Commits created through the API with the workflow's GITHUB_TOKEN, and with no
author or committer set, are signed by GitHub and show as Verified.
Usage: python scripts/api_commit.py "<message>" data/raw [more paths]
Needs GITHUB_TOKEN, GITHUB_REPOSITORY and GITHUB_REF_NAME (set by Actions).
"""
import base64, json, os, subprocess, sys, urllib.request

API = "https://api.github.com/repos/" + os.environ["GITHUB_REPOSITORY"]
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
HDRS = {"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
        "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, headers=HDRS,
                                 data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def main():
    message, paths = sys.argv[1], sys.argv[2:]
    subprocess.run(["git", "add", "-A", "--", *paths], check=True)
    out = subprocess.run(["git", "diff", "--cached", "--name-status", "--no-renames", "--", *paths],
                         check=True, capture_output=True, text=True).stdout
    changes = [line.split("\t", 1) for line in out.splitlines() if line]
    if not changes:
        print("No changes to commit.")
        return
    head = call("GET", f"/git/ref/heads/{BRANCH}")["object"]["sha"]
    base_tree = call("GET", f"/git/commits/{head}")["tree"]["sha"]
    tree = []
    for status, name in changes:
        if status == "D":
            tree.append({"path": name, "mode": "100644", "type": "blob", "sha": None})
            continue
        with open(name, "rb") as f:
            blob = call("POST", "/git/blobs", {"content": base64.b64encode(f.read()).decode(), "encoding": "base64"})
        tree.append({"path": name, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    new_tree = call("POST", "/git/trees", {"base_tree": base_tree, "tree": tree})["sha"]
    commit = call("POST", "/git/commits", {"message": message, "tree": new_tree, "parents": [head]})
    call("PATCH", f"/git/refs/heads/{BRANCH}", {"sha": commit["sha"]})
    print(f"Committed {len(changes)} file(s) as {commit['sha'][:7]}, verified={commit['verification']['verified']}")


if __name__ == "__main__":
    main()
