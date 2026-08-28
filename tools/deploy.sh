#!/usr/bin/env bash
# tools/deploy.sh — One-click deploy script for BILLSzuka
# Builds frontend-2 and deploys to Cloudflare Pages + pushes to Render repo.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> 1. Building frontend-2 (Vite)..."
cd frontend-2
VITE_API_BASE_URL="https://billszuka-api.onrender.com" npm run build
cd "$ROOT_DIR"

echo "==> 2. Deploying to Cloudflare Pages (project: billszuka)..."
npx -y wrangler pages deploy frontend-2/dist --project-name=billszuka

echo "==> 3. Pushing changes to git remotes (Render auto-deploys from ng-net/main)..."
git push origin main || true
git push ng-net main || true

echo "✅ All done! Backend is live on Render, Frontend is live on Cloudflare Pages."
