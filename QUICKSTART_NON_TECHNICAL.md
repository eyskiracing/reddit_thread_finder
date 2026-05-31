# Quickstart for Non-Technical Users

This guide is for people who want to **use** the Reddit Thread Finder without needing to understand all of the technical details.

The full technical documentation is in:

```text
README.md
SECURITY.md
SBOM.md
```

---

## Good news — no Reddit account needed

Previous versions of this tool required you to create a Reddit developer account, apply for API access, and fill in a credentials file. That process is no longer needed.

This version uses a free public data source called Arctic Shift. You can just install and run.

---

## What this tool does

This tool helps you find Reddit discussions related to a specific pain point.

For example:

```text
small businesses struggling with SOC 2 evidence collection
```

The tool returns links to Reddit threads that look relevant.

You open the links, read the threads yourself, and decide whether it makes sense to respond.

---

## What this tool does not do

This tool does **not**:

```text
post on Reddit
comment on Reddit
message Reddit users
write replies for you
collect Reddit comments
collect Reddit usernames
collect full thread content
```

It only finds thread links and lightweight metadata.

---

## What you need before you start

Three things:

```text
1. Python installed on your computer
2. The downloaded project folder
3. Terminal on Mac or Command Prompt on Windows
```

You do **not** need a Reddit account.
You do **not** need any API credentials.
You do **not** need to fill in any configuration files.

---

## Step 1 — Get the project

Download or clone from GitHub:

```text
https://github.com/Eyskiracing/reddit-thread-finder
```

Make sure you are on the `arctic-shift-backend` branch.

---

## Step 2 — Run the setup script

### On Mac

Double-click:

```text
setup_mac.command
```

If double-clicking does not work, open Terminal, navigate to the project folder, and run:

```bash
./setup_mac.command
```

### On Windows

Double-click:

```text
setup_windows.bat
```

---

## Step 3 — Run your first search

### On Mac

Double-click:

```text
run_mac.command
```

### On Windows

Double-click:

```text
run_windows.bat
```

---

## What happens when you run it

The tool guides you through a few steps:

**Step 1 — Describe the pain point**

Enter the problem you want to find discussions about in plain language.

**Step 2 — Narrow the search (Focus Builder)**

The tool asks a few optional questions to help make the search more specific:

```text
Who has this problem?
What are they trying to do?
What makes it painful today?
What outcome do they want?
Any words to include?
Any words to avoid?
```

Press Enter to skip any question.

**Step 3 — Subreddit discovery**

The tool automatically finds relevant Reddit communities for your topic and shows you a list:

```text
Suggested subreddits to search:
  1. r/customerservice     (relevance: high)
  2. r/sysadmin            (relevance: high)
  3. r/helpdesk            (relevance: medium)
  4. r/startups            (relevance: medium)

Search all of these? [Y/n]
```

Press Enter to search all of them, or type numbers to remove any you do not want.

**Step 4 — Set search parameters**

```text
Search from what date? (YYYY-MM-DD)
Minimum match score? (0.0 to 1.0)
How many links to return?
```

**Step 5 — Results**

The tool returns a list of Reddit thread links with scores. Open them in your browser and read them yourself.

---

## Recommended starting settings

```text
From date:      2026-01-01
Minimum score:  0.70
Number of links: 25
```

For a broader search: `0.60`
For a stricter search: `0.80`

---

## Note on data recency

This version uses archived Reddit data that may be 2–4 weeks behind real-time. If you enter a very recent date, the tool will automatically warn you and ask:

```
Would you like to use 2026-04-01 instead? [Y/n]:
```

Press **Enter** or type **Y** to let the tool adjust to a safer date. Type **N** if you want to keep your original date anyway (results may be sparse).

---

## How to read the results

Each result includes:

```text
Title           — the thread title
Subreddit       — which Reddit community it is in
Date            — when it was posted
Semantic score  — how closely it matches your topic
Composite score — overall ranking
Pain signal     — whether it sounds like someone describing a problem
Reddit score    — how many upvotes the thread received
Comments        — how many replies it has
URL             — the link to open in your browser
```

Open the URL and read the thread yourself before deciding whether to respond.

---

## What to do after you find a thread

```text
1. Open the thread.
2. Read the full conversation.
3. Check the subreddit rules.
4. Decide whether your response would be useful.
5. Disclose your affiliation if relevant.
6. Respond as a human.
7. Do not spam communities.
8. Do not paste automated replies.
```

---

## If something goes wrong

### "No matching threads found"

Try:

```text
Lower the minimum score from 0.70 to 0.60
Search from an earlier date
Accept more subreddits in the discovery step
Use a broader topic description
```

### "Could not reach Arctic Shift"

The data service may be temporarily unavailable. Try again in a few minutes.

### "Python was not found"

Python may not be installed. Install Python 3.10 or later and run the setup script again.

### First run is slow

The first run downloads the semantic matching model (about 80MB). After that, it runs faster.

---

## Safety reminder

This tool is only for finding links.

It does not decide whether you should respond.

You are responsible for reading the thread, understanding the context, following subreddit rules, and responding appropriately.
