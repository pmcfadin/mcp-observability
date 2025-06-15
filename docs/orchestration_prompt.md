# AI Agent Orchestration Prompt – **mcp-observability**

> Use this playbook whenever an autonomous agent (or human acting as one) needs to pick work, create issues, and log progress in this repository.

---

## 1 · Goals

1. Always work **inside a tracked GitHub Issue**.
2. Keep the open‐issue rate ≤ 5 per hour (see Cursor rule §6).
3. Follow the *Create-Before-Code* policy – no code without an issue.
4. Ensure transparent progress logging through comments, commits, and PRs.

---

## 2 · Pre-requisites

* GitHub CLI (`gh`) authenticated and in the repo root.
* `git` configured with an email/username the team recognises.
* Branch protection passes (CI green) before merging.

---

## 3 · High-Level Flow

```mermaid
flowchart TD
  A(List open epics) --> B(Select highest-priority epic)
  B --> C(Check for existing child issues)
  C -->|None| D(Create child issue from checklist)
  C -->|Some open| E(Pick a child issue)
  D --> E
  E --> F(Comment "⏳ Started" & create branch)
  F --> G(Implement work, commit, push)
  G --> H(Open PR referencing child issue)
  H --> I(Tests pass & code review)
  I --> J(Close child issue & comment on epic)
  J --> K(If all child issues closed → close epic)
```

---

## 4 · Detailed Steps & Command Snippets

### 4.1  List open epics

```bash
# Show all open epics (parent issues)
gh issue list --label epic --state open --limit 20 | cat
```

Choose the top-priority epic (oldest `created_at` or based on label `P0`, `P1`, etc.).

---

### 4.2  Inspect the epic

```bash
EPIC_ID=1  # example
gh issue view $EPIC_ID | cat
```

*The issue body contains an unchecked checklist of child tasks.*

---

### 4.3  Create missing child issue (max 5/hr)

If the task you want to tackle is only a checklist item (no linked issue yet):

```bash
CHILD_TITLE="Implement /health endpoint"
gh issue create \
  --title "$CHILD_TITLE" \
  --body "Tracks #$EPIC_ID\n\nAcceptance Criteria: …" \
  --label ai-task --assignee @me | cat

# Link it back to the epic
NEW_ID=$(gh issue list --search "$CHILD_TITLE" --json number -q '.[0].number')
gh issue comment $EPIC_ID "Tracks #$NEW_ID" | cat
```

---

### 4.4  Start work on a child issue

```bash
CHILD_ID=42  # issue you picked
SLUG=$(echo "$(gh issue view $CHILD_ID --json title -q .title)" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '-')
BRANCH="ai/$CHILD_ID-$SLUG"

gh issue comment $CHILD_ID "⏳ Started. Branch: $BRANCH" | cat
git checkout -b $BRANCH
```

---

### 4.5  Commit workflow

```bash
# After meaningful progress
git add .
git commit -m "feat: Add health endpoint (refs #$CHILD_ID)"

git push -u origin $BRANCH
```

---

### 4.6  Open a PR

```bash
gh pr create \
  --title "Close #$CHILD_ID: Add health endpoint" \
  --body "AI-generated implementation." \
  --head $BRANCH | cat
```

CI will run automatically. If it fails, push fixes until green.

---

### 4.7  Close the loop

```bash
PR_ID=$(gh pr view --json number -q .number)

gh issue close $CHILD_ID --comment "✅ Done. See PR #$PR_ID." | cat
```

Then update the epic:

```bash
gh issue comment $EPIC_ID "✅ Completed sub-task #$CHILD_ID" | cat

# If no unchecked tasks remain, close epic
if ! gh issue view $EPIC_ID --json taskLists -q '.taskLists[].items[] | select(.state=="OPEN")' | grep -q .; then
  gh issue close $EPIC_ID --comment "✅ Done. See merged PRs." | cat
fi
```

---

## 5 · Etiquette & Limits

| Rule | Reminder |
| ---- | -------- |
| **≤ 5 issues/hour** | Batch child issues – don't spam. |
| **Logs** | Use emojis: ⏳ Started, 🚧 Progress, ❗ Need input, ✅ Done. |
| **Secrets** | Never paste tokens or credentials. |
| **Branch name** | `ai/<issue-id>-<slug>` only. |

---

## 6 · Troubleshooting

* **gh authentication errors** – run `gh auth login` again.
* **Label missing** – create it: `gh label create ai-task --color BFD4F2`.
* **CI failing** – comment `🚧 CI failing, investigating` on the issue to log status.

---

*Last updated: 15 Jun 2025* 