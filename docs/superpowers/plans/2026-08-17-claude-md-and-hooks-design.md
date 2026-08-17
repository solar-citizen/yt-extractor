# CLAUDE.md and Session Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finalize and verify the repository documentation (`CLAUDE.md`, `README.MD`) and establish project-wide configuration standards for Claude Code and subagents.

**Architecture:** Maintain clear documentation and cross-platform installation guidelines without breaking existing Python services (`YouTubeService`, `FFmpegService`, `MetadataService`, `TimestampService`).

**Tech Stack:** Python 3, `yt-dlp`, `ffmpeg`, `black`.

## Global Constraints

- Never duplicate full installation instructions between `README.MD` and `CLAUDE.md`; `README.MD` contains cross-platform user setup (Windows winget, Ubuntu apt), while `CLAUDE.md` provides architectural rules and conventions for Claude.
- Strict class-oriented service design and type hints.
- Maintain error handling robustness in batch processing.

---

### Task 1: Verify Documentation and Settings Structure

**Files:**
- Check: `CLAUDE.md`
- Check: `README.MD`
- Check: `.claude/settings.json` (if present)

**Interfaces:**
- Consumes: Existing project structure (`config.py`, `main.py`, `services/`, `models/`, `utils/`)
- Produces: Verified and clean markdown files with no syntax errors.

- [ ] **Step 1: Check markdown file formatting**

Run: `head -n 20 CLAUDE.md README.MD`
Expected: Correct headers, clear Windows and Ubuntu setup sections, and accurate architectural references.

- [ ] **Step 2: Commit documentation files**

```bash
git add CLAUDE.md README.MD
git commit -m "docs: add comprehensive CLAUDE.md and cross-platform README.MD instructions"
```
