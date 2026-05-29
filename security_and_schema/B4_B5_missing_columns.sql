-- [B4] Missing `speculative` column
-- [B5] Missing `auto_merge` column

-- The backend code references these columns, but they are not in the schema.

-- Test 1: Try to query speculative (Will fail)
SELECT id, speculative FROM public.diagnoses LIMIT 1;
-- Expected: ERROR: column "speculative" does not exist

-- Test 2: Try to query auto_merge (Will fail)
SELECT id, auto_merge FROM public.connected_repos LIMIT 1;
-- Expected: ERROR: column "auto_merge" does not exist

-- Fix: Add these columns to the database schema, or remove the references from the backend code.
