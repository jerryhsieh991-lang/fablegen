# Using fablegen inside Claude Code

`fablegen` is a plain CLI, so any agentic CLI can call it. To wire it into Claude Code
as a `/fable-gen` slash command:

1. Install the CLI once (from the repo root):

   ```bash
   pip install -e .
   ```

   Now `fablegen` is on your PATH. (No install? Use `python -m fablegen ...` from the repo.)

2. Copy the command into your Claude Code commands directory:

   ```bash
   cp claude_code/commands/fable-gen.md ~/.claude/commands/fable-gen.md
   ```

3. In Claude Code, type:

   ```
   /fable-gen build a Rust CLI that watches a folder and syncs to S3
   ```

Claude Code runs `fablegen new "<your text>"` and hands you the master prompt.
Switch to Fable 5 (`/model claude-fable-5`) and paste it as your first message —
ideally at high/xhigh effort for hard tasks.

The same `fable-gen.md` pattern works in any tool that supports shell-backed commands.
