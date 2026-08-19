#!/usr/bin/env python3
"""Read and write pull request state for the babysit skill."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time


POLL_SECONDS = 30
DEADLINE_SECONDS = 900
GH_ERROR_LIMIT = 3
LOG_LINES_BEFORE = 60
LOG_LINES_AFTER = 5
LOG_MAX_LINES = 200
ACTIONABLE_BUCKETS = {"fail", "pending", "cancel"}

STATE_FIELDS = (
    "number,id,url,state,isDraft,baseRefName,headRefOid,"
    "mergeable,mergeStateStatus,reviewDecision"
)
CHECK_FIELDS = "name,bucket,state,link,workflow"
LINK_IDS = re.compile(r"/runs/(\d+)/job/(\d+)")

THREADS_QUERY = """
query($owner:String!, $repo:String!, $number:Int!) {
  repository(owner:$owner, name:$repo) {
    pullRequest(number:$number) {
      reviewThreads(first: 100) {
        nodes {
          id isResolved isOutdated path line startLine viewerCanReply
          comments(first: 20) {
            nodes { databaseId author { login } body url }
          }
        }
      }
    }
  }
}
"""

REPLY_MUTATION = """
mutation($thread:ID!, $body:String!) {
  addPullRequestReviewThreadReply(
    input: {pullRequestReviewThreadId: $thread, body: $body}
  ) { comment { url } }
}
"""


class GhError(Exception):
    pass


class WatchError(Exception):
    pass


def _gh(args: list[str]) -> str:
    try:
        result = subprocess.run(["gh"] + args, capture_output=True, text=True)
    except FileNotFoundError:
        raise GhError("gh not found")
    if result.returncode != 0:
        raise GhError(result.stderr.strip() or f"gh {' '.join(args)} failed")
    return result.stdout


def _target(args: list[str], pr: str | None) -> list[str]:
    return args + [pr] if pr else args


def state(pr: str | None) -> dict:
    args = _target(["pr", "view"], pr) + ["--json", STATE_FIELDS]
    return json.loads(_gh(args))


def _owner_repo(url: str) -> tuple[str, str]:
    parts = url.split("/")
    return parts[3], parts[4]


def checks(pr: str | None, show_all: bool) -> list[dict]:
    args = _target(["pr", "checks"], pr) + ["--json", CHECK_FIELDS]
    # gh exits 1 when a check failed and 8 when checks are still pending, so the
    # exit code cannot separate a real error from a red check. The output can.
    result = subprocess.run(["gh"] + args, capture_output=True, text=True)
    if not result.stdout.strip():
        if "no check" in result.stderr.lower():
            return []
        raise GhError(result.stderr.strip() or "gh pr checks failed")

    rows = json.loads(result.stdout)
    for row in rows:
        match = LINK_IDS.search(row.get("link") or "")
        row["runId"] = match.group(1) if match else None
        row["jobId"] = match.group(2) if match else None
    if show_all:
        return rows
    return [row for row in rows if row["bucket"] in ACTIONABLE_BUCKETS]


def threads(pr: str | None, current: dict | None = None) -> list[dict]:
    # Derive owner and repo from the pull request itself. The {owner}/{repo}
    # placeholders resolve from the working directory, which is a different
    # repository whenever pr names one.
    current = current or state(pr)
    owner, repo = _owner_repo(current["url"])
    args = [
        "api",
        "graphql",
        "-F",
        f"owner={owner}",
        "-F",
        f"repo={repo}",
        "-F",
        f"number={current['number']}",
        "-f",
        f"query={THREADS_QUERY}",
    ]
    payload = json.loads(_gh(args))
    nodes = payload["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    return [node for node in nodes if not node["isResolved"]]


def logs(link: str) -> str:
    match = LINK_IDS.search(link)
    if not match:
        raise GhError(f"not a check link: {link}")
    owner, repo = _owner_repo(link)
    run_id, job_id = match.group(1), match.group(2)
    target = ["-R", f"{owner}/{repo}"]

    jobs = json.loads(_gh(["run", "view", run_id, "--json", "jobs"] + target))["jobs"]
    failed_steps: list[str] = []
    job_name = job_id
    for job in jobs:
        if str(job["databaseId"]) != job_id:
            continue
        job_name = job["name"]
        failed_steps = [
            step["name"]
            for step in job.get("steps", [])
            if step["conclusion"] == "failure"
        ]

    lines = _gh(["run", "view", "--job", job_id, "--log"] + target).splitlines()
    # ##[error] is emitted by the Actions runner, so it is present for any tool.
    marks = [i for i, line in enumerate(lines) if "##[error]" in line]
    if marks:
        start = max(0, marks[0] - LOG_LINES_BEFORE)
        end = min(len(lines), marks[-1] + LOG_LINES_AFTER + 1)
        excerpt = lines[start:end]
    else:
        excerpt = lines[-LOG_MAX_LINES:]

    header = f"job: {job_name}"
    if failed_steps:
        header += f"\nfailed steps: {', '.join(failed_steps)}"
    return header + "\n\n" + "\n".join(excerpt[-LOG_MAX_LINES:])


def reply(thread_id: str, body: str) -> str:
    args = [
        "api",
        "graphql",
        "-f",
        f"query={REPLY_MUTATION}",
        "-f",
        f"thread={thread_id}",
        "-f",
        f"body={body}",
    ]
    payload = json.loads(_gh(args))
    return payload["data"]["addPullRequestReviewThreadReply"]["comment"]["url"]


def _snapshot(pr: str | None) -> dict:
    current = state(pr)
    thread_map = {}
    for thread in threads(pr, current):
        comments = thread["comments"]["nodes"]
        thread_map[thread["id"]] = {
            "last": comments[-1]["databaseId"] if comments else None,
            "where": f"{thread['path']}:{thread['line']}",
        }
    return {
        "state": current["state"],
        "mergeable": current["mergeable"],
        "mergeStateStatus": current["mergeStateStatus"],
        "headRefOid": current["headRefOid"],
        "checks": {row["name"]: row["bucket"] for row in checks(pr, True)},
        "threads": thread_map,
    }


def _terminal(snapshot: dict) -> str | None:
    if snapshot["state"] != "OPEN":
        return f"state: {snapshot['state']}"
    # GitHub can set one field before the other while it computes the pair.
    if snapshot["mergeable"] == "CONFLICTING" or snapshot["mergeStateStatus"] == "DIRTY":
        return (
            f"conflict: mergeable={snapshot['mergeable']} "
            f"merge={snapshot['mergeStateStatus']}"
        )
    return None


def _difference(before: dict, after: dict) -> str | None:
    if before["headRefOid"] != after["headRefOid"]:
        return f"head: {after['headRefOid'][:8]}"
    if before["mergeStateStatus"] != after["mergeStateStatus"]:
        return f"merge: {after['mergeStateStatus']}"
    for name, bucket in after["checks"].items():
        if before["checks"].get(name) != bucket:
            return f"checks: {name}={bucket}"
    for thread_id, entry in after["threads"].items():
        previous = before["threads"].get(thread_id)
        if previous is None:
            return f"threads: new thread on {entry['where']}"
        if previous["last"] != entry["last"]:
            return f"threads: new comment on {entry['where']}"
    return None


def watch(pr: str | None) -> str:
    baseline = _snapshot(pr)
    stop = _terminal(baseline)
    if stop:
        raise WatchError(stop)

    deadline = time.monotonic() + DEADLINE_SECONDS
    failures = 0
    while time.monotonic() < deadline:
        time.sleep(POLL_SECONDS)
        try:
            current = _snapshot(pr)
        except GhError:
            failures += 1
            if failures >= GH_ERROR_LIMIT:
                raise
            continue
        failures = 0
        stop = _terminal(current)
        if stop:
            raise WatchError(stop)
        reason = _difference(baseline, current)
        if reason:
            return reason
    return "timeout"


USAGE = """usage: pr.py <command> [args]

  state   [<pr>]                 pull request state as JSON
  checks  [<pr>] [--all]         actionable checks as JSON
  logs    <link>                 failing job log excerpt
  threads [<pr>]                 unresolved review threads as JSON
  reply   <thread-id> <body>     reply to a review thread
  watch   [<pr>]                 block until the state changes, exit 1 on a stop
"""


def main() -> int:
    argv = sys.argv[1:]
    if not argv:
        print(USAGE, file=sys.stderr)
        return 1

    command, rest = argv[0], argv[1:]

    try:
        return _dispatch(command, rest)
    except (GhError, WatchError) as exc:
        print(f"pr: {exc}", file=sys.stderr)
        return 1


def _dispatch(command: str, rest: list[str]) -> int:
    if command == "state":
        print(json.dumps(state(rest[0] if rest else None), indent=2))
    elif command == "checks":
        show_all = "--all" in rest
        positional = [arg for arg in rest if arg != "--all"]
        rows = checks(positional[0] if positional else None, show_all)
        print(json.dumps(rows, indent=2))
    elif command == "logs":
        if len(rest) != 1:
            print(USAGE, file=sys.stderr)
            return 1
        print(logs(rest[0]))
    elif command == "threads":
        print(json.dumps(threads(rest[0] if rest else None), indent=2))
    elif command == "reply":
        if len(rest) != 2:
            print(USAGE, file=sys.stderr)
            return 1
        print(reply(rest[0], rest[1]))
    elif command == "watch":
        print(watch(rest[0] if rest else None))
    else:
        print(USAGE, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
