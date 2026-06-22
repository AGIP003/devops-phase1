BEGIN;

ALTER TABLE public.categories OWNER TO jay;
ALTER TABLE public.payment_method_groups OWNER TO jay;
ALTER TABLE public.payment_methods OWNER TO jay;
ALTER TABLE public.transactions OWNER TO jay;
ALTER TABLE public.users OWNER TO jay;

ALTER SEQUENCE public.categories_id_seq OWNER TO jay;
ALTER SEQUENCE public.payment_method_groups_id_seq OWNER TO jay;
ALTER SEQUENCE public.payment_methods_id_seq OWNER TO jay;
ALTER SEQUENCE public.transactions_id_seq OWNER TO jay;
ALTER SEQUENCE public.users_id_seq OWNER TO jay;

ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS telegram_id BIGINT UNIQUE;

CREATE TABLE IF NOT EXISTS public.telegram_link_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES public.users(id) ON DELETE CASCADE,
    token VARCHAR(64) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE public.telegram_link_tokens OWNER TO jay;
ALTER SEQUENCE public.telegram_link_tokens_id_seq OWNER TO jay;

CREATE INDEX IF NOT EXISTS idx_telegram_link_tokens_user_id
    ON public.telegram_link_tokens (user_id);

CREATE INDEX IF NOT EXISTS idx_telegram_link_tokens_active
    ON public.telegram_link_tokens (token)
    WHERE used = FALSE;

COMMIT;
