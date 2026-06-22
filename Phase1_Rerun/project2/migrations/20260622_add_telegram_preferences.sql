BEGIN;

CREATE TABLE IF NOT EXISTS public.telegram_user_preferences (
    user_id INTEGER PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    default_payment_method VARCHAR(50) NOT NULL DEFAULT 'm-pesa',
    category_aliases JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMIT;
