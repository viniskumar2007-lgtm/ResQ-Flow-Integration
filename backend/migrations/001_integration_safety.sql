-- Safe to re-run. Resolve duplicate (user_id, local_id) values before
-- applying the unique index; this migration never deletes or rewrites incidents.

ALTER TABLE public.incidents
    ADD COLUMN IF NOT EXISTS local_id text,
    ADD COLUMN IF NOT EXISTS priority_score integer,
    ADD COLUMN IF NOT EXISTS priority_reasons jsonb,
    ADD COLUMN IF NOT EXISTS analysis_method text,
    ADD COLUMN IF NOT EXISTS machine_learning_used boolean,
    ADD COLUMN IF NOT EXISTS ai_confidence numeric;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM public.incidents
        WHERE local_id IS NOT NULL
          AND user_id IS NOT NULL
        GROUP BY user_id, local_id
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION
            'Duplicate user_id/local_id pairs exist; resolve them before enabling SOS idempotency';
    END IF;
END
$$;

CREATE UNIQUE INDEX IF NOT EXISTS incidents_user_local_id_unique
    ON public.incidents (user_id, local_id)
    WHERE local_id IS NOT NULL AND user_id IS NOT NULL;
