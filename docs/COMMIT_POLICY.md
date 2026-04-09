# Commit Message Policy

## 1. Format

Use this exact first-line format:

`type (scope): short description`

Important:
- Keep one space before `(` and after `)`.
- Use lowercase for `type` and `scope`.
- Use imperative mood in description (for example: `add`, `fix`, `update`).
- No trailing period in the first line.

## 2. Allowed Types

Use one of these:
- `feat`: new functionality
- `fix`: bug fix
- `docs`: documentation only
- `style`: formatting/style changes only, no logic
- `refactor`: code change without behavior change
- `perf`: performance improvement
- `test`: tests added/updated
- `build`: build/dependency/tooling changes
- `ci`: CI/CD workflow changes
- `chore`: maintenance tasks

## 3. Scope Rules

- Scope should be short and specific.
- Prefer area/module names, for example:
  - `data`
  - `xai`
  - `training`
  - `eval`
  - `results`
  - `repo`
- If uncertain, use a broad but meaningful scope.
- Avoid empty scope unless your team allows it.

## 4. Subject Line Rules

- 50-72 characters preferred.
- Clear and outcome-focused.
- Do not repeat the scope words unnecessarily.
- No emoji.

## 5. Body Rules (Optional)

Add a body only when needed:
- Why the change was made.
- What was changed at a high level.
- Any important context (tradeoffs, constraints).

Body style:
- Short paragraphs or concise bullets.
- Wrap around 72-100 chars when possible.
- Keep it brief.

## 6. Footer Rules (Optional)

Use footer lines only when relevant:
- Breaking changes:
  - `BREAKING CHANGE: ...`
- Issue references:
  - `Refs: #123`
  - `Closes: #456`

## Commit Template (Paste-Ready)

```text
type (scope): short imperative summary

Optional body:
- Why this change was needed.
- What changed.
- Important notes or constraints.

Optional footer:
Refs: #issue
BREAKING CHANGE: describe incompatible change
```

## Examples

```text
feat (xai): add cpu-safe shap sampling controls
```

```text
fix (training): clamp label ids before dicece loss
```

```text
docs (results): sync cpu long metrics in reports
```

```text
chore (repo): update origin url after repository rename
```

## Quick Rule of Thumb

- Small obvious change: first line only.
- Non-obvious or risky change: first line + short body.
- API/config breaking change: add `BREAKING CHANGE` footer.
