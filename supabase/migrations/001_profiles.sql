-- Run in Supabase SQL Editor (Dashboard → SQL → New query)

create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  created_at timestamptz not null default now(),
  plan text not null default 'free' check (plan in ('free', 'pro')),
  plan_expires_at timestamptz,
  usage jsonb not null default '{}'::jsonb,
  bonus_analyses int not null default 0,
  discount_percent int not null default 0,
  referral_code text not null unique,
  referred_by uuid references public.profiles (id),
  referrals_verified int not null default 0,
  pending_referrals uuid[] not null default '{}'::uuid[]
);

create table if not exists public.report_history (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  created_at timestamptz not null default now(),
  filename text,
  verdict text,
  verdict_label text,
  ai_score int,
  report_data jsonb not null
);

create index if not exists report_history_user_created_idx
  on public.report_history (user_id, created_at desc);

alter table public.profiles enable row level security;
alter table public.report_history enable row level security;

create policy "Users read own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Users read own history"
  on public.report_history for select
  using (auth.uid() = user_id);

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, referral_code)
  values (new.id, upper(substr(replace(new.id::text, '-', ''), 1, 8)))
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
