# LinkedIn auto-posting setup

One-time setup, about 10 minutes. After it, the flow is:

```
idea -> /li-post (draft in your voice) -> /li-human (clean + score)
     -> you say "yes" -> /li-publish (posts it to your feed)
```

Only posting to your own feed is automated, through LinkedIn's official API.
Comments, DMs and connection requests stay copy-and-paste: LinkedIn only gives
those permissions to approved partners, and bots that click around the site
get accounts restricted.

## 1. Create a LinkedIn developer app

1. Go to https://www.linkedin.com/developers/apps and click **Create app**.
2. App name: anything (e.g. "My post assistant").
3. LinkedIn Page: LinkedIn requires one. If you don't have a company page, create
   a simple one (it can just be your own name) and pick it.
4. Upload any logo, tick the agreement, **Create app**.

## 2. Turn on the two products

In the app, open the **Products** tab and click **Request access** on:

- **Share on LinkedIn** (lets the app post as you)
- **Sign In with LinkedIn using OpenID Connect** (lets it know who "you" is)

Both are usually approved instantly.

## 3. Add the redirect URL

**Auth** tab -> **Authorized redirect URLs for your app** -> add exactly:

```
http://localhost:8765/callback
```

On the same tab, note the **Client ID** and **Primary Client Secret**.
Never paste the secret into a chat.

## 4. Sign in once (on your own computer)

You need Python 3 installed. In a terminal, inside this repository:

```bash
export LINKEDIN_CLIENT_ID=paste-client-id
export LINKEDIN_CLIENT_SECRET=paste-client-secret
python3 .claude/skills/li-publish/auth.py
```

(On Windows PowerShell use `$env:LINKEDIN_CLIENT_ID="..."` instead of `export`.)

A browser opens, you approve, and the token is saved to
`~/.claude/linkedin/token`. It lasts 60 days; rerun this step when it expires.

## 5. Test without posting

```bash
echo "Testing my setup. #automation" > test.txt
python3 .claude/skills/li-publish/post.py test.txt --dry-run
```

Drop `--dry-run` when you want it live. It always asks you to type `yes` first.

## 6. Your voice profile

Copy `.claude/linkedin/voice.template.md` to `~/.claude/linkedin/voice.md` and
fill it in, or paste 3-5 of your posts into Claude and ask it to write the file.

## Using it from Claude Code cloud sessions

Cloud sessions block linkedin.com by default. To post from there:

- Environment settings -> **Network access** -> add `api.linkedin.com` to
  Allowed domains.
- Environment settings -> add an environment variable or secret
  `LINKEDIN_ACCESS_TOKEN` with the token from step 4
  (`cat ~/.claude/linkedin/token` on your computer).

Otherwise, run Claude Code on your own computer, where step 4 already put the
token in place.
