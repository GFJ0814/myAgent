---
name: realtime_news
description: Find and summarize today's real-time news for a topic or breaking event.
enabled: true
---
# Realtime News

Find the latest available news for the user's requested topic or event, with a
strong preference for today's news.

Guidelines:
- Always use `news_search` first for news-related tasks.
- Prefer today's or the most recent headlines and mention the publication time.
- If the user mentions a specific event, search with the event keywords directly.
- Summarize the key facts from the returned headlines and links.
- If no same-day result is found, clearly state that and return the latest available news.
