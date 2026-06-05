"""AGENTS.md template for AdonisJS v7 + Edge.js projects."""

AGENTS_MD_TEMPLATE = """\
# AGENTS.md

This project is built with **AdonisJS v7** and **Edge.js** templates
(server-rendered monolith). An MCP server is available with documentation
and development guidelines — **use it before guessing**.

## Before You Start

1. Call `get_backend_guidelines` — architecture rules, Edge template
   conventions, controller patterns, forms, models, and assets.
2. Call `get_frontend_guidelines` — rules for HTML, CSS, and UI
   development in Edge templates (semantic HTML, accessibility, responsive).
3. Call `get_code_quality_guidelines` — rules for code changes
   (surgical edits, no bloat, no filler, domain naming).

## When You Need Documentation

- **AdonisJS v7 docs:** `search_docs(query="...", version="v7")` or
  `get_doc(permalink="...", version="v7")`. Use `list_sections(version="v7")`
  to browse available pages.
- **Edge.js templates:** `edge_search_docs(query="...")` or
  `edge_get_doc(permalink="...")`. Use `edge_list_sections()` to browse.
- **Lucid ORM (models, queries, migrations):**
  `lucid_search_docs(query="...")` or `lucid_get_doc(permalink="...")`.
  Use `lucid_list_sections()` to browse.
- **Community packages:** `packages_search(query="...")` to find packages,
  `packages_get(name="...")` to read full README with install/usage docs.

## Key Rules

- This is a **server-rendered app**, not a SPA. Do not introduce React, Vue,
  Svelte, or any frontend framework.
- Controllers render Edge views directly. No REST API for frontend consumption.
- Use Edge layouts, partials, and components — do not duplicate HTML structure.
- Validate with VineJS validators, not manually in controllers.
- Use Lucid ORM models with migrations. Never modify the database directly.
- Follow the existing project structure. Do not invent new directories or
  patterns.
- Do not add npm packages unless explicitly asked. Work with what is already
  in `package.json`.
- Keep changes surgical — only touch files related to the task.
- Read existing code before adding new code. Match naming conventions.

## Stack Reference

| Layer | Technology | Docs Tool |
|-------|-----------|-----------|
| Framework | AdonisJS v7 | `search_docs`, `get_doc` |
| Templates | Edge.js | `edge_search_docs`, `edge_get_doc` |
| ORM | Lucid | `lucid_search_docs`, `lucid_get_doc` |
| Validation | VineJS | `search_docs(query="validation")` |
| Auth | @adonisjs/auth | `search_docs(query="auth")` |
| Packages | Community registry | `packages_search`, `packages_get` |
"""
