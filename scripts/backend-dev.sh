#!/usr/bin/env bash
cd backend || exit 1
source .venv/bin/activate
uvicorn app.main:app --reload