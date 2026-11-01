# LA Resiliency Resources. Run `just <recipe>`.

# Write the site data files from data/ (needed before dev, test, or build)
export:
    cd backend && uv run la-resiliency export

# Run the site locally at http://localhost:5173
dev: export
    cd frontend && npm run dev

# Build the static site into frontend/build
build: export
    cd frontend && npm run build

# Build, then serve the finished site at http://localhost:4173
preview: build
    cd frontend/build && python3 -m http.server 4173

# Lint and test everything
check: export
    cd backend && uv run la-resiliency validate && uv run ruff check . && uv run pytest -q
    cd frontend && npm test && npm run check

# Show which translations are missing and roughly what they would cost (no API calls)
translate-plan:
    cd backend && uv run la-resiliency translate --dry-run

# Translate new or changed text with Claude Code on your Claude plan
translate:
    cd backend && uv run la-resiliency translate

# Translate through the pay-per-token API instead (mode: direct or batch; key from Doppler)
translate-api mode="batch":
    cd backend && doppler run -- uv run la-resiliency translate --mode {{mode}}

# Preview what a Sheet sync would change, without writing anything or calling the API
sync-plan:
    cd backend && uv run la-resiliency sync --dry-run --no-links

# Check every resource website
links:
    cd backend && uv run la-resiliency check-links

# Write resources as CSV to import into the Google Sheet
seed-csv:
    cd backend && uv run la-resiliency seed-csv --out ../resources-for-sheet.csv
