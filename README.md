# LA Resiliency Resources

A free, multilingual website that helps people in Los Angeles find food, housing, immigration,
health, and job resources. The resiliency co-chairs of the Los Angeles Stake choose the resources.
The site is in English, Spanish, Korean, Simplified and Traditional Chinese, Farsi, and Turkish.

- **Simple to share:** every language, topic, and resource has its own link, plus a printable
  flyer with a QR code.
- **Private:** search runs in the visitor's browser. Nothing they type is sent or stored.
- **Near-zero cost:** static hosting on GitHub Pages. Translation runs through Claude Code on a
  Claude subscription, and only when resources change.

## How it works

```
Google Sheet (co-chairs edit)
  └─ nightly GitHub Action (or "Run workflow" to publish now)
       ├─ pulls the Sheet and validates every row
       ├─ translates only new or changed text with Claude Code, plus search words people type
       ├─ checks every website link
       └─ opens a pull request with a summary ──► merge ──► site rebuilds on GitHub Pages
```

| Path | What it is |
| --- | --- |
| `data/resources.yaml` | English resources, synced from the Sheet |
| `data/categories.yaml`, `data/ui.yaml` | Topic tiles and the site's button and label text |
| `data/i18n/<lang>.json` | Saved translations, so unchanged text is never translated twice |
| `data/i18n/overrides/<lang>.yaml` | Corrections from native speakers (these always win) |
| `data/VERIFY.md` | Items the co-chairs need to confirm before launch |
| `backend/` | Python pipeline: `la-resiliency` CLI (Sheet sync, translation, export, link check) |
| `frontend/` | SvelteKit static site |

## For co-chairs: editing the Google Sheet

One row is one resource. Changes appear on the site after the nightly sync and review.

| Column | What to enter |
| --- | --- |
| `id` | Short name with lowercase letters, numbers, and dashes, like `tenant-power-toolkit`. **Don't change it after publishing**, because it is part of shared links. |
| `active` | Checked to show on the site. Uncheck to hide without deleting. |
| `category` | One of `detained`, `start-here`, `food`, `housing`, `benefits-health`, `immigration-legal`, `jobs`, `education-english`, `church` |
| `also_category` | Optional extra topics, separated by commas |
| `name` | Organization or program name. Never translated. |
| `url` | Full web address starting with `https://` |
| `phones` | One phone per line: `(888) 624-4752 \| Rapid response hotline \| es`. The label and language code are optional. |
| `description` | One or two plain sentences about what it is |
| `who_its_for`, `how_to_get_it`, `tip` | Optional. Put deadlines and warnings in `tip`. |
| `audience` | Blank for everyone, or `church_members`, `seniors`, `families`, `students` |
| `cost` | `free`, `paid`, `varies`, or blank |
| `status_ok` | Checked if help is available regardless of immigration status |
| `multilingual` | Checked if they offer interpreters or many languages |
| `lang_en` … `lang_tr` | Checked for each language their staff or hotline actually speaks |
| `other_languages` | Other language codes, like `km, vi` |
| `urgent` | Checked for time-critical help. Shown first, with a red edge. |
| `volatile` | Checked if amounts or rules change often, as a reminder to re-check |
| `last_verified` | Date someone last confirmed the details |

Keep internal notes in a separate tab. Only the Resources tab is published.

## One-time setup

The nightly Sheet sync skips itself until the `SHEET_CSV_URL` secret exists, so the site can
go live before the Sheet is ready.

1. **Sheet.** Run `just seed-csv`, then import `resources-for-sheet.csv` into a tab named
   *Resources*. Then *File → Share → Publish to web*: choose the Resources tab as CSV and copy
   the link.
2. **Secrets (Doppler).** Run `claude setup-token` (needs a Claude Pro, Max, Team, or Enterprise
   plan). Store the token as `CLAUDE_CODE_OAUTH_TOKEN`, alongside `SHEET_CSV_URL`, in Doppler
   project `la-resiliency-resources`. Connect Doppler's GitHub Actions sync so both become
   repository secrets. **The token expires after a year**; when translations start failing in
   the sync pull request, run `claude setup-token` again.
3. **Translating locally.** `just translate` uses your logged-in Claude Code and translates only
   what is new or changed. Progress is saved after each resource, so an interrupted run picks up
   where it stopped. `just translate-api` is the pay-per-token alternative (needs
   `ANTHROPIC_API_KEY`). Run `just check`, then `just preview`, and look through each
   language.
4. **GitHub.**
   - Under *Settings → Pages*, set the source to *GitHub Actions*.
   - Under *Settings → Actions → General*, allow GitHub Actions to create pull requests.
   - Without a custom domain, set the repository variable `BASE_PATH` to `/<repository-name>`.
5. **Domain.**
   - Add the domain to `frontend/static/CNAME` and set up DNS as GitHub Pages describes.
   - Set `SITE_URL` in `frontend/src/lib/config.ts` to the new address (scheme and host only,
     like `https://example.org`), and clear the `BASE_PATH` repository variable. Until then the
     site runs at `https://ryancraigdavis.github.io/la-resiliency-resources/`, and GitHub
     redirects that address to the custom domain once it is set up.
6. **Problem reports (optional).** Create a Google Form with a prefilled resource id field, and
   put its link in `REPORT_URL` in `frontend/src/lib/config.ts`.

## Fixing a translation

A native speaker can correct any text without touching the Sheet:

```yaml
# data/i18n/overrides/es.yaml
reviewed: [211-la, calfresh] # checked by a native speaker, no edits needed
ui_reviewed: true # hides the "translated by computer" note once the site text is checked
resources:
  calfresh:
    headline: Dinero cada mes para comprar comida
ui:
  search_button: Buscar
categories:
  food: { label: Comida }
```

## Local development

Needs `uv`, Node 22, `just`, and Claude Code (for translating).

```bash
cd backend && uv sync --all-groups && cd ../frontend && npm install && cd ..
just check     # lint and all tests
just dev       # http://localhost:5173
just preview   # the real static build at http://localhost:4173
just links     # check every resource website
```

## Costs

- **Hosting:** GitHub Pages is free. A custom domain is about $12 a year.
- **Translation:** Claude Opus 5 through Claude Code counts against the Claude plan's usage
  instead of billing per token. It runs only for new or changed text, so the nightly sync uses
  nothing when the Sheet hasn't changed. Through the API instead, the full first run would be
  about $3 in batch mode.
