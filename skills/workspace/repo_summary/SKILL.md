---
name: repo_summary
description: Summarize a repository or working directory with the available tools.
enabled: true
---
# Repo Summary

Inspect the target repository or directory and produce a concise summary.

Guidelines:
- Use `shell_exec` to inspect the directory tree when helpful.
- Use `file_read` to read the most relevant files before summarizing.
- Prefer concise outputs focused on structure, purpose, and important files.
- If the task does not specify a path, work from the current project directory.
