-- [B1] & [E12] Iteration constraint crash
-- The processor.py code supports up to 4 iterations (process_iteration_2 can fire multiple times).
-- However, the database schema enforces: CHECK (iteration IN (1, 2))
-- If a CI run fails its fix branch for the second time, the system will try to insert 
-- iteration = 3 and crash completely.

-- Run this in Supabase SQL editor to see the crash:

INSERT INTO public.diagnoses (
    run_id, 
    iteration, 
    problem_summary, 
    root_cause, 
    fix_description, 
    fix_type, 
    required_secrets
) VALUES (
    '00000000-0000-0000-0000-000000000000', -- Replace with a valid run_id
    3, -- THIS TRIGGERS THE BUG
    'Test problem',
    'Test root cause',
    'Test fix',
    'manual_required',
    '[]'::jsonb
);

-- Expected Output:
-- ERROR: new row for relation "diagnoses" violates check constraint "diagnoses_iteration_check"
-- DETAIL: Failing row contains (..., 3, ...).
