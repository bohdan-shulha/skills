---
name: babysit
description: 'Watch the pull request of the current branch and keep it ready to merge. Read the checks, the merge state, and the unresolved review threads on each pass. Fix a failed check and update a stale branch, then push without a question. Make the code change for a review comment, but ask before the push and before the reply. Use when a pull request is open and needs supervision until the checks pass and the reviews get an answer.'
argument-hint: 'Optional pull request number or URL, e.g. "142"'
---

# Babysit

## Overview

Watch one pull request and keep it in a mergeable condition.
Each pass reads the state, acts on one concern, then waits for the state to change.
The skill handles three signals: a failed check, a conflict or a stale base branch, and an
unresolved review thread.

The skill never merges the pull request.

## When to Use

- A pull request is open and the checks still run.
- A check failed and the cause is in the branch.
- The base branch moved ahead of the branch.
- A reviewer left comments that need a code change and an answer.

Do not use this skill in these cases:

- No pull request exists yet. Open one first.
- You want the pull request merged. This skill stops when the pull request is ready.
- You want one status report. Run `pr.py state` and `pr.py checks` instead.

## Path Resolution

- Resolve `scripts/pr.py` from the directory that contains this file:
  `${CLAUDE_SKILL_DIR}/scripts/pr.py`.
- The commit step uses the `commit` skill. Its guard is at `commit/scripts/precommit_guard.py`,
  in the `commit` skill directory. The guard is **not** in the babysit directory. Do not look for
  `babysit/scripts/precommit_guard.py`.

## Autonomy

Three rules control every action:

1. Fix a failed check. Update a stale branch. Push the result. Do not ask first.
2. Make the code change for a review comment. Ask before the push. Ask before the reply.
3. Never merge the pull request.

## Preflight

Run these steps one time, before the first pass.

1. Confirm the working tree is clean:
   - `git status --porcelain`
   - Stop and ask the user when the output is not empty. Do not stash.
2. Confirm no merge and no rebase is in progress:
   - `ls "$(git rev-parse --git-dir)" | grep -E 'rebase-merge|rebase-apply|MERGE_HEAD'`
   - Stop and ask the user when the command finds a match.
3. Read the pull request:
   - `python3 ${CLAUDE_SKILL_DIR}/scripts/pr.py state`
   - The command exits 1 when no pull request exists. Report this and stop.
4. Record `number`, `baseRefName`, and `isDraft` for the later steps.

## Workflow

Repeat this pass until a stop condition or a guard applies.

1. Read the state:
   - `python3 ${CLAUDE_SKILL_DIR}/scripts/pr.py state`
   - `python3 ${CLAUDE_SKILL_DIR}/scripts/pr.py checks`
   - `python3 ${CLAUDE_SKILL_DIR}/scripts/pr.py threads`
2. Classify the state. Apply the precedence below.
3. Act on one concern only.
4. Wait. See *The Wait*.

**Precedence: the merge state first, then the checks, then the review threads.**

A base branch update changes the head commit. GitHub keys each check run to a commit SHA. Thus an
update discards every queued check run and starts them again. Correct the merge state first, or
one full check cycle becomes waste.

A review thread stays through a head change. The thread becomes `isOutdated`, but it stays
unresolved. A check run does not stay. This difference sets the order.

The checks come before the review threads, because check work needs no approval from the user.

**Keep the working tree clean at the start and at the end of each pass.**
This rule prevents a defect, not an untidy tree. The `commit` skill stages with `git add . -A`.
Uncommitted review changes in the tree go into the next check commit. The push then sends them
without the approval that rule 2 requires.

## Read the State

`pr.py` holds every GitHub command. Do not write a `gh` command by hand.

| Command | Result |
| --- | --- |
| `pr.py state [<pr>]` | number, id, url, state, isDraft, baseRefName, headRefOid, mergeable, mergeStateStatus, reviewDecision |
| `pr.py checks [<pr>]` | the checks that need an action or a wait |
| `pr.py checks [<pr>] --all` | every check |
| `pr.py logs <link>` | the log excerpt of a failed job |
| `pr.py threads [<pr>]` | the unresolved review threads |
| `pr.py reply <thread-id> <body>` | posts a reply, prints the comment URL |
| `pr.py watch [<pr>]` | blocks, prints one reason line |

`pr.py checks` hides a check that passed and a check that the run skipped. It returns a check with
the bucket `fail`, `pending`, or `cancel`. Use `--all` only for the final report.

`mergeStateStatus` controls the branch work:

- `DIRTY` — the branch has a conflict.
- `BEHIND` — the base branch moved ahead.
- `UNSTABLE` — a check failed, but the branch merges.
- `BLOCKED` — an approval is absent. A human must act.
- `CLEAN` or `HAS_HOOKS` — the merge state needs no action.
- `UNKNOWN` — GitHub still computes the value. Wait. Do not act.

## Fix Failed Checks

1. Read the failed checks:
   - `python3 ${CLAUDE_SKILL_DIR}/scripts/pr.py checks`
2. Read the log of the first failed check. Give the command the `link` field:
   - `python3 ${CLAUDE_SKILL_DIR}/scripts/pr.py logs "<link>"`
3. Decide the cause. See *Safety Rules* for an infrastructure failure.
4. Correct the cause in the code.
5. Commit with the `commit` skill. Do not run the guard by hand.
6. Push:
   - `git push`

## Update the Branch

Do all branch work in the local repository. Do not change a branch on the server.

`BEHIND` and `DIRTY` use the same steps. `BEHIND` means the base branch moved ahead. `DIRTY` means
GitHub found a conflict. Only step 3 separates them.

1. Get the new commits of the base branch:
   - `git fetch origin`
2. Merge the base branch into the current branch:
   - `git merge origin/<baseRefName>`
3. Read the result of the merge:
   - Git makes the merge commit when the merge has no conflict. Go to step 5.
   - Git stops when the merge has a conflict. Go to step 4.
4. Correct each conflict, then conclude the merge:
   - `python3 <commit_skill_dir>/scripts/precommit_guard.py`
   - `git add . -A`
   - `git commit --no-edit`
   - **Ask the user before the push.** A conflict resolution is a decision, not a mechanical step.
5. Push:
   - `git push`

Use `git commit --no-edit` in step 4. The command keeps the merge message that git prepared. This
step concludes a merge, so it does not use the `commit` skill and its message rules.

Never rebase. Never force push. A merge keeps the history in order, so `--force-with-lease` is
never necessary and a reviewer keeps their position in the diff.

Read the base branch name from `baseRefName`. Do not assume `main`.

## Answer Review Threads

1. Read the unresolved threads:
   - `python3 ${CLAUDE_SKILL_DIR}/scripts/pr.py threads`
2. Read the file at `path` and `line` for each thread. The command does not return the diff, because
   a diff makes the output too large.
3. Make the code change for each thread.
4. Write a reply for each thread.
5. **Stop. Show the user the diff, the thread, and each reply. Wait for approval.**
6. Commit with the `commit` skill after the user approves.
7. Push:
   - `git push`
8. Post each reply:
   - `python3 ${CLAUDE_SKILL_DIR}/scripts/pr.py reply <thread-id> "<body>"`

A thread with `isOutdated` set to `true` is still unresolved. It still needs an answer.

Do not resolve a thread. The reviewer resolves their own thread.

## The Wait

Call the wait only when work is in flight. Work is in flight when a check has the bucket `pending`,
or when `mergeable` is `UNKNOWN`. In all other conditions, go to *Stop Conditions*.

Run the command through Bash with `run_in_background` set to `true`:

- `python3 ${CLAUDE_SKILL_DIR}/scripts/pr.py watch`

The command blocks and polls every 30 seconds. It prints one reason line and exits when the state
changes. It prints `timeout` after 15 minutes. The harness starts the next pass when the command
exits.

Do not use a foreground `sleep`. The harness blocks a long foreground `sleep`.
Do not use `gh pr checks --watch`. That command rejects `--json`, and it returns immediately when
no check is pending.

The first pass does not wait.

## Stop Conditions

Stop and report when one of these conditions is true:

1. `state` is not `OPEN`. Someone merged or closed the pull request.
2. No check has the bucket `fail` or `pending`, `mergeStateStatus` is `CLEAN` or `HAS_HOOKS`, and
   no thread is unresolved. Report that the pull request is ready. Do not merge it.
3. Only a human action remains. An example is `BLOCKED` on an approval, or an unresolved thread
   with no work in flight. Report the condition and stop. The user starts the skill again later.
4. A guard applies.

## Guards

| Guard | Limit | Action |
| --- | --- | --- |
| The same failure fingerprint | 2 attempts | Stop and ask |
| Passes | 8 | Stop and report |
| Total time | 60 minutes | Stop and report |
| Pushes with no change of state | 2 | Stop and ask |
| Reads of `mergeable: UNKNOWN` | 3 | Stop and report |

The fingerprint is the check name and the first `##[error]` line. Remove the timestamp and the run
id from the line. The same fingerprint two times shows that the diagnosis is wrong. More attempts
do not correct it.

State the counter before each act step, so the user sees the limit.

## Safety Rules

- Never merge the pull request. Never resolve a review thread. Never run `gh pr ready`.
- Never amend a commit that is already pushed. Add a new commit.
- Never make a check pass by a change to the check. Do not delete a test. Do not skip a test. Do
  not mark a test as an expected failure. Do not edit a workflow file. Do not lower a threshold.
  Do not add a retry. Stop and ask the user when this is the only available correction.
- Handle a draft pull request in the same way. Report that the pull request is still a draft.
- A failure comes from the infrastructure, and not from the code, when both conditions are true:
  1. The failure is in the setup, the dependency download, the network, or a timeout.
  2. `git diff origin/<baseRefName>...HEAD --name-only` shows no file on that path.

  Then run `gh run rerun <run-id> --failed` one time. Count the rerun as one of the two attempts.
  Never change the product code for a suspected unstable test.
- Never check out the base branch. Never commit to it. Never push it.
- Commit with the `commit` skill. The guard can block on a log file or an untracked binary file. A
  check correction can produce such a file. A blocked guard ends the pass. Report the files.

## Ask the User

Stop and ask in these conditions:

1. The working tree is not clean at the start.
2. A merge or a rebase is already in progress.
3. A merge conflict needs a resolution, before the push.
4. A push carries a change for a review thread.
5. A reply is ready, before the reply goes out.
6. The same failure fingerprint occurs two times.
7. A guard applies.
8. A suspected unstable test fails again after one rerun.
9. The only available correction makes a check weaker.
10. A review thread asks for work outside the scope of the pull request.
11. Two reviewers disagree.

## Notes

- The skill needs `gh`, and `gh` needs authentication with the `repo` scope.
- `pr.py` uses `gh` only. It supports GitHub and no other remote.
- `pr.py` needs Python 3 and no other package.
