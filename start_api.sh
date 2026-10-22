#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
uvicorn backend.api.main:app --reload --port 8000
