import os
import asyncio

# [B2] Wrong column name in RAG query
# processor.py Line 849: .eq("connected_repo_id", repo_id)
# The actual column in ci_runs is `repo_id`, not `connected_repo_id`.
# This silently causes the RAG context to always be empty.

print("=== [B2] RAG Column Mismatch Test ===")
print("In `app/agent/processor.py`, the `_fetch_similar_fixes` function runs:")
print("""
    past_runs = supabase.table("ci_runs")\\
        .select("id, error_message, commit_message")\\
        .eq("connected_repo_id", repo_id)\\
        .eq("status", "verified")\\
        .order("created_at", desc=True)\\
        .limit(3)\\
        .execute()
""")

print("\nHowever, the schema for `ci_runs` is:")
print("""
    CREATE TABLE public.ci_runs (
        id UUID PRIMARY KEY,
        repo_id UUID REFERENCES public.connected_repos(id),
        ...
    )
""")

print("Because Supabase/PostgREST gracefully handles missing columns in some setups by returning empty lists,")
print("or raises a PostgREST error that is swallowed, this feature is completely broken.")
print("Fix: Change `connected_repo_id` to `repo_id` in processor.py.")
