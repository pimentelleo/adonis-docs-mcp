"""Development guidelines for AdonisJS v7 + Edge.js monolithic projects."""

BACKEND_GUIDELINES = """\
# AdonisJS v7 Backend Guidelines

Follow these rules when writing backend code in an AdonisJS v7 project.

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

## When Unsure

- Use `get_doc` and `search_docs` to look up the official AdonisJS v7
  documentation before guessing.
- Use `edge_get_doc` and `edge_search_docs` for Edge template syntax.
- Read existing project code to understand conventions before adding new code.
"""


FRONTEND_GUIDELINES = """\
# Frontend Development Guidelines

Follow these rules when writing HTML, CSS, and frontend code in Edge templates.
The goal is to build clean, standard, accessible, and functional user interfaces.

## Semantic HTML

- Use proper semantic elements: `<header>`, `<nav>`, `<main>`, `<article>`,
  `<section>`, `<aside>`, `<footer>`, `<figure>`, `<figcaption>`, `<details>`,
  `<summary>`, `<dialog>`, `<time>`, `<mark>`, `<address>`.
- Only use `<div>` and `<span>` when no semantic element fits.
- Use `<button>` for actions and `<a>` for navigation. Never use
  `<div onclick>` or `<span class="link">`.

## Clean and Standard UI

- Create clean, predictable, and functional user interfaces.
- Rely on the CSS framework already installed in the project (e.g., Tailwind CSS,
  Bootstrap). If writing custom CSS, keep it simple and maintainable.
- Maintain a consistent rhythm for spacing (`margin`, `padding`, `gap`).
- Use clear typographic hierarchy for headings and body text.

## Accessibility (A11y)

- All interactive elements must have visible `:focus-visible` styles.
- All `<img>` must have meaningful `alt` text.
- Forms: every `<input>` must have a `<label>`. Use `<fieldset>` and
  `<legend>` for groups.
- Interactive elements must be keyboard-accessible (Tab, Enter, Escape).
- Use appropriate HTML `type` attributes: `type="email"`, `type="tel"`,
  `type="url"`, `type="search"`.

## Responsive Design

- Build layouts mobile-first. Ensure the interface works well on small screens
  before scaling up.
- Avoid horizontal scrolling at any viewport width.
- Ensure text and buttons remain readable and usable on all devices.

## Component States

- Every interactive component should handle: default, hover, focus, active,
  disabled, loading, and error states.
- Always include error states for forms and empty states for lists.
"""


CODE_QUALITY_GUIDELINES = """\
# Code Quality Guidelines (Anti-Slop)

Follow these rules when writing any code. They target the specific patterns
that make AI-generated code low-quality. Anti-slop, not anti-AI: genuinely
good work is fine, lazy generated slop is not.

Inspired by peakoss/anti-slop.

---

## Surgical changes only

- Touch only the files directly related to what was asked. Do not "improve"
  unrelated files, refactor nearby code, or reorganize the project.
- Keep changes small and focused. If a task needs 10 lines, write 10 lines.
  A 500-line diff for a simple feature is slop.
- Do not modify root config files (`package.json`, `tsconfig.json`,
  `.env.example`, `README.md`) unless the task explicitly requires it.

## No comment spam

- Do not add excessive inline comments. Code should be self-explanatory.
- Only comment *why* something non-obvious is done, never *what* the code does.
- Do not add file-header comments, section dividers (`// ---- Section ----`),
  or JSDoc blocks to every function.
- A file with more new comments than new logic is slop.

## No filler content

- Never output "Lorem ipsum", "TODO: implement", "Add your content here",
  "Example text", or any placeholder.
- Do not generate sample/demo data unless explicitly asked.
- Every string, label, and message must be real and contextual.
- Do not fabricate metrics ("50,000+ users", "+47% conversion") or
  testimonials. Use real data or a labelled placeholder (`—`).

## No bloated output

- Do not produce verbose explanations inside code. If something needs
  explaining, a single short comment suffices.
- Do not add multiple alternative approaches in comments ("you could also...").
- Do not add console.log/debug statements unless debugging was requested.
- Do not add emoji to code, commit messages, or comments.

## No invented structure

- Follow the project's existing file layout exactly. Look at how the project
  organizes controllers, models, views, and services before creating files.
- Do not create new top-level directories, new config files, or new
  organizational patterns.
- Name files and classes using the project's existing naming conventions —
  check existing files first.

## No unnecessary abstractions

- Do not create wrapper classes, base classes, utility modules, or "helper"
  files unless there is clear, repeated usage (3+ existing call sites).
- Do not add design patterns (Strategy, Factory, Observer) unless the
  complexity genuinely demands it.
- Do not create interfaces/types for objects used in only one place.

## No dependency additions

- Do not add new npm packages, frameworks, or tools unless explicitly asked.
- Work with what is already in `package.json`. Check existing dependencies
  before suggesting new ones.
- Especially do not add: CSS frameworks, animation libraries, icon packs,
  utility libraries (lodash, etc.), or testing tools not already present.

## No speculative code

- Build exactly what was asked. Do not add features, error handling, edge
  cases, or extensibility points that were not requested.
- Do not add "future-proofing" abstractions or configuration options.
- Do not handle errors that cannot realistically occur in the current context.

## No SPA leakage

- No `fetch()` / `axios` calls to render content that should be
  server-rendered.
- No client-side state management (Redux, Pinia, stores, signals).
- No client-side routing or history manipulation.
- No virtual DOM, reactive bindings, or component lifecycle in the browser.

## Use domain-specific naming

- Use names from the business domain: `InvoiceController`, not
  `DataController`; `billing/show.edge`, not `page.edge`.
- Match the naming style already used in the project.
- No generic names: `utils.ts`, `helpers.ts`, `common.ts`, `misc.ts`.
"""


# Keep combined for the MCP prompt (backward compat)
ADONISJS_STACK_GUIDELINES = (
    BACKEND_GUIDELINES + "\n---\n\n" + CODE_QUALITY_GUIDELINES + "\n---\n\n" + FRONTEND_GUIDELINES
)
