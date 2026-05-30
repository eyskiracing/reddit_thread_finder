# Quickstart for Non-Technical Users

Generated: 2026-05-29T20:52:39+00:00

This guide is for people who want to **use** the Reddit Thread Finder without needing to understand all of the technical details.

The full technical documentation is still available in:

```text
README.md
SECURITY.md
SBOM.md
```

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

You need four things:

```text
1. Python installed on your computer
2. Reddit API credentials
3. The downloaded project folder
4. Terminal on Mac / Command Prompt or PowerShell on Windows
```

You do **not** need to give this tool your Reddit password.

---

## Step 1 — Unzip the project

Unzip the downloaded file.

You should see a folder named something like:

```text
reddit_thread_finder_secure_v7_easy_start
```

Open that folder.

---

## Step 2 — Add your Reddit API credentials

Inside the folder, find this file:

```text
.env.example
```

Make a copy of it and rename the copy to:

```text
.env
```

Open `.env` in a text editor and fill in these three values:

```text
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=
```

Example:

```text
REDDIT_CLIENT_ID=abc123
REDDIT_CLIENT_SECRET=xyz789
REDDIT_USER_AGENT=reddit-thread-finder/0.1 by u/yourusername
```

Do **not** add your Reddit password.

Do **not** share your `.env` file.

---

## Step 3 — Run the setup script

### On Mac

Double-click:

```text
setup_mac.command
```

If double-clicking does not work, open Terminal, go to the project folder, and run:

```bash
./setup_mac.command
```

### On Windows

Double-click:

```text
setup_windows.bat
```

You can also run it from Command Prompt or PowerShell.

---

## Step 4 — Run your first search

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

The tool will ask you questions. It will first help you narrow the pain point into a better Reddit search.

---

## New first step — Focus the pain point

The tool will ask a few questions before it searches Reddit.

This is because broad searches usually return noisy results.

Use this structure:

```text
[Who has the problem] is trying to [do what], but [current friction] makes it hard to [get desired outcome].
```

Example:

```text
Small ecommerce operators are trying to track returns and refund status, but they have to check Shopify, warehouse emails, and spreadsheets manually to know which customers are waiting for refunds.
```

Another example:

```text
Product managers are trying to find repeated feature requests, but feedback is scattered across Slack, sales notes, calls, and support tickets.
```

The tool may ask:

```text
Who has this problem?
What are they trying to do?
What makes it painful today?
What outcome do they want instead?
Any words that must be included?
Any words or topics to avoid?
```

Press Enter to skip any question you do not know.

---

## What the questions mean

### “What pain point are you looking for?”

Enter the problem you want to find discussions about.

Example:

```text
small businesses struggling with SOC 2 evidence collection
```

### “Search from what date?”

Enter a date in this format:

```text
YYYY-MM-DD
```

Example:

```text
2026-01-01
```

This means the tool will look for threads from January 1, 2026 through today.

### “Minimum semantic match score?”

This controls how strict the match should be.

Use:

```text
0.60 = broader search
0.70 = balanced search
0.80 = stricter search
```

Recommended starting point:

```text
0.70
```

### “How many thread links should be returned?”

This is how many results you want.

Recommended starting point:

```text
25
```

The maximum is:

```text
100
```

### “Search which subreddit(s)?”

You can press Enter to search all Reddit.

Or you can enter a few subreddits separated by commas.

Example:

```text
startups,cybersecurity,sysadmin,compliance
```

Maximum:

```text
5 subreddits
```

---

## Recommended first search

When prompted, try:

```text
Pain point:
small businesses struggling with SOC 2 evidence collection

From date:
2026-01-01

Minimum score:
0.70

Number of links:
25

Subreddits:
all
```

---

## How to read the results

Each result includes:

```text
Title
Subreddit
Date
Semantic score
Composite score
Pain signal
Reddit score
Number of comments
URL
Matched search queries
```

### Semantic score

How closely the thread title matches your topic.

Higher is better.

### Pain signal

Whether the title sounds like someone is describing a problem.

Higher may mean the thread is more useful for human review.

### Composite score

The overall ranking score.

This combines:

```text
semantic match
pain signal
engagement
recency
```

### URL

This is the Reddit thread link.

Open it in your browser and read the thread yourself.

---

## What to do after you find a thread

Before replying:

```text
1. Open the thread.
2. Read the full conversation.
3. Check the subreddit rules.
4. Decide whether your response would actually be useful.
5. Disclose your affiliation if relevant.
6. Respond as a human.
7. Do not spam communities.
8. Do not paste automated replies.
```

The goal is to find places where a thoughtful human response may be appropriate.

---

## If something goes wrong

### “Missing required environment variables”

Your `.env` file is missing one of these:

```text
REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET
REDDIT_USER_AGENT
```

Open `.env` and make sure all three are filled in.

---

### “Python was not found”

Python may not be installed or may not be available from your command line.

Install Python, then run the setup script again.

---

### “No matching threads found”

Try one of these:

```text
lower the minimum score from 0.80 to 0.70
use a broader topic
search from an earlier date
search all Reddit instead of specific subreddits
increase the number of links requested
```

---

### “Rate limit”

The tool is slowing down because Reddit is asking it to wait.

This is normal.

Try again later or use a smaller search.

---

### First run is slow

The first run may download the semantic matching model.

After that, it should usually be faster.

---

## Good default settings

Use these as a starting point:

```text
Minimum score: 0.70
Number of links: 25
Subreddits: all
```

For a broader search:

```text
Minimum score: 0.60
```

For a stricter search:

```text
Minimum score: 0.80
```

---

## Safety reminder

This tool is only for finding links.

It does not decide whether you should respond.

You are responsible for reading the thread, understanding the context, following subreddit rules, and responding appropriately.
