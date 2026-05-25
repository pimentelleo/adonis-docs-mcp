"""Development guidelines for AdonisJS v7 + Edge.js monolithic projects."""

ADONISJS_STACK_GUIDELINES = """\
# AdonisJS v7 + Edge.js — Development Guidelines

You are working on a **server-rendered monolithic** application built with
AdonisJS v7 and Edge.js templates. Follow these rules strictly.

---

## Architecture: Server-Rendered Monolith

- This is **NOT** a SPA. Do not introduce React, Vue, Svelte, Angular, or any
  frontend framework. The UI is server-rendered with Edge templates.
- Do not create a REST/JSON API to feed a frontend client. Controllers render
  Edge views directly.
- Do not add client-side routers. Navigation is standard `<a>` links and form
  submissions handled by AdonisJS routes.
- Use **progressive enhancement**: pages must work without JavaScript first,
  then layer interactivity on top sparingly.

## Edge Templates

- Use Edge syntax (`@if`, `@each`, `@include`, `@component`, `@let`,
  `@unless`, `@inject`) — never invent custom helpers when a built-in tag
  exists.
- Use **Edge layouts** (`@component('layouts/app')` with `@slot`) for page
  structure. Do not duplicate `<html>`, `<head>`, `<body>` across views.
- Use **Edge partials** (`@include('partials/navbar')`) for shared fragments.
- Use **Edge components** with `$props` and `@slot` for reusable UI elements.
  Prefer this over copy-pasting HTML.
- Templates go in `resources/views/`. Follow the existing directory convention
  in the project — do not invent new folder structures.
- Keep templates lean. Business logic belongs in controllers or services, not
  in `.edge` files.
- Escape output by default (`{{ }}`). Only use `{{{ }}}` (raw) when you
  explicitly need unescaped HTML and understand the XSS implications.

## Controllers & Routing

- One controller per resource, following RESTful conventions:
  `index`, `create`, `store`, `show`, `edit`, `update`, `destroy`.
- Use `router.resource()` for CRUD routes.
- Controllers call services/models, then `return view.render('page', data)`.
- Keep controllers thin — extract business logic into **services**
  (`app/services/`) or **actions**.
- Use **route model binding** when available instead of manual
  `Model.findOrFail()`.

## Forms & Validation

- Use standard HTML `<form>` elements with `method="POST"` (or method spoofing
  `_method` for PUT/PATCH/DELETE).
- Validate with **VineJS** validators defined in `app/validators/`.
  Do not validate manually in controllers.
- Display validation errors using `@if(flashMessages.has('errors.<field>'))` in
  Edge templates. Use AdonisJS flash messages, not client-side validation.
- Include CSRF tokens in forms: `{{ csrfField() }}`.

## Models & Database

- Use Lucid ORM models in `app/models/`. Define relationships, computed
  properties, and hooks in the model.
- Use **migrations** for schema changes — never modify the database manually.
- Use **factories** and **seeders** for test/dev data.
- Scope queries with model query scopes rather than raw `WHERE` chains in
  controllers.

## Assets & Styling

- Use the **Vite** integration (`@vite()` tag in Edge) for CSS and JS assets.
- Write plain CSS or use the CSS tooling already configured in the project
  (check `vite.config.ts`). Do not add Tailwind, Bootstrap, or other
  frameworks unless they are already in the project.
- Keep client-side JavaScript minimal. If interactivity is needed, use small
  vanilla JS scripts or Alpine.js if already present.
- Do not add npm packages for things that can be done with a few lines of
  vanilla JS (dropdowns, toggles, modals).

## Anti-Slop Rules

These are the most important rules. Violating them produces AI slop.

1. **No invented structure.** Follow the project's existing file layout. Do not
   create new top-level directories or reorganize the project.
2. **No unnecessary abstractions.** Do not create wrapper classes, utility
   modules, or "helper" files unless there is clear, repeated usage (3+ call
   sites).
3. **No placeholder content.** Never output "Lorem ipsum", "TODO: implement",
   "Add your content here", or similar. Every piece of text must be real.
4. **No excessive comments.** Code should be self-explanatory. Only comment
   *why*, never *what*. Do not add JSDoc/docblocks to obvious methods.
5. **No over-engineering.** If a feature needs 10 lines, write 10 lines. Do
   not build an extensible plugin system for a simple feature.
6. **No technology additions.** Do not add new dependencies, frameworks, or
   tools unless explicitly asked. Work with what's already in `package.json`.
7. **No speculative code.** Do not add features, error handling, or edge cases
   that were not requested. Build exactly what is asked.
8. **No SPA patterns in a monolith.** No `fetch()` calls to render HTML that
   should be server-rendered. No client-side state management. No virtual DOM.
9. **No generic naming.** Use domain-specific names (`InvoiceController`, not
   `DataController`; `billing/show.edge`, not `page.edge`).
10. **Respect existing patterns.** Before writing new code, look at how the
    project already does similar things and follow that pattern exactly.

## When Unsure

- Use `get_doc` and `search_docs` to look up the official AdonisJS v7
  documentation before guessing.
- Use `edge_get_doc` and `edge_search_docs` for Edge template syntax.
- Read existing project code to understand conventions before adding new code.
"""
