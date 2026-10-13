---
name: li-publish
description: >-
  Publish an approved LinkedIn post to the user's own feed through LinkedIn's
  official Posts API. Use only after a draft from li-post (or the user) has
  been humanized and the user has explicitly said yes to posting it, or when
  the user says "post it", "publish this to LinkedIn", "send it live".
---

# li-publish

The last step after li-post and li-human. It sends one post to the user's own
feed with `post.py`, using LinkedIn's official API. It does not comment, DM,
connect, like or schedule; LinkedIn does not allow those for personal apps.

## Rules

1. **Explicit yes, every time.** Only publish text the user has seen in full
   and approved in this conversation. Approval of one draft never carries to
   another, or to an edited version of the same draft.
2. **No placeholders.** If the draft still contains `{{...}}`, stop and ask
   for the real value. `post.py` refuses these too.
3. **Humanized first.** Run li-human's `humanize.py` and `detect.py` on the
   draft before showing it for approval.
4. **Never handle the token.** Never ask the user to paste their token or
   client secret into chat. They live in `~/.claude/linkedin/token` or the
   `LINKEDIN_ACCESS_TOKEN` environment variable / environment secret.

## Steps

```bash
# 1. save the approved text exactly as approved
#    (e.g. .claude/linkedin/outbox/2026-10-13.txt)
# 2. preview the exact request, no network
python3 post.py outbox/2026-10-13.txt --dry-run
# 3. publish (asks for a typed yes; pass --yes only if the user already said
#    yes to this exact text in chat)
python3 post.py outbox/2026-10-13.txt
```

`--visibility CONNECTIONS` limits the post to 1st-degree connections.

## When it fails

| Error | Meaning | Fix |
|---|---|---|
| No token | never signed in here | user runs `auth.py` on their computer (see `.claude/linkedin/SETUP.md`) |
| 401 | token expired (60 days) | rerun `auth.py` |
| 403 | app lacks Share on LinkedIn | add the product in the developer portal |
| 426 | API version retired | set `LINKEDIN_VERSION` to a recent YYYYMM |
| connect / 403 from proxy | this machine cannot reach linkedin.com | run it on the user's computer, or allow `api.linkedin.com` in the cloud environment's network settings |

If it cannot post, hand the user the final text as a copy-ready block so they
can paste it into LinkedIn themselves.
