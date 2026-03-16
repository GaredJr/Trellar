# Dag 3

### 11.03.2026


Startet dagen med å få opp nettet på server linuxen min.
```
sudo iw dev wlp2s0 set power_save off
nmcli radio wifi off
nmcli radio wifi on
```
Hadde fortsatt problemet med at power saving så ut til å skru seg på etter tid, så jeg måtte skru dette av permament.

Deretter fikk jeg startet på supabase oppsettet.
Lagde et prosjekt som heter Trellar og skrudde på Email Auth.

Så fikk jeg codex til å sette opp det generelle i repoet her. Her er også SQLen som jeg fikk:

```
-- Trellar Supabase schema + RLS
-- Run this in Supabase SQL Editor.

create extension if not exists pgcrypto;

create table if not exists public.profiles (
    id uuid primary key references auth.users (id) on delete cascade,
    display_name text not null default '',
    email text not null default '',
    about text not null default '',
    created_at timestamptz not null default now()
);

create table if not exists public.user_settings (
    user_id uuid primary key references auth.users (id) on delete cascade,
    workspace_name text not null default 'Trellar Team',
    default_visibility text not null default 'private'
        check (default_visibility in ('private', 'workspace', 'public')),
    digest_frequency text not null default 'daily'
        check (digest_frequency in ('daily', 'weekly', 'off')),
    channel text not null default '#trellar-updates',
    card_template text not null default 'Owner - Due date - Acceptance criteria',
    updated_at timestamptz not null default now()
);

create table if not exists public.boards (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users (id) on delete cascade,
    slug text not null,
    name text not null,
    description text not null default '',
    members integer not null default 1,
    created_at timestamptz not null default now(),
    unique (owner_id, slug)
);

create table if not exists public.lanes (
    id uuid primary key default gen_random_uuid(),
    board_id uuid not null references public.boards (id) on delete cascade,
    name text not null,
    position integer not null,
    unique (board_id, position)
);

create table if not exists public.cards (
    id uuid primary key default gen_random_uuid(),
    board_id uuid not null references public.boards (id) on delete cascade,
    lane_id uuid not null references public.lanes (id) on delete cascade,
    title text not null,
    meta text not null default '',
    status text not null default 'New',
    position integer not null default 0,
    archived boolean not null default false,
    created_at timestamptz not null default now()
);

create table if not exists public.activity (
    id bigint generated always as identity primary key,
    owner_id uuid not null references auth.users (id) on delete cascade,
    board_name text not null default '',
    title text not null,
    created_at timestamptz not null default now()
);

create index if not exists boards_owner_idx on public.boards (owner_id, created_at);
create index if not exists lanes_board_idx on public.lanes (board_id, position);
create index if not exists cards_lane_idx on public.cards (lane_id, position);
create index if not exists cards_board_idx on public.cards (board_id);
create index if not exists activity_owner_idx on public.activity (owner_id, created_at desc);

alter table public.profiles enable row level security;
alter table public.user_settings enable row level security;
alter table public.boards enable row level security;
alter table public.lanes enable row level security;
alter table public.cards enable row level security;
alter table public.activity enable row level security;

drop policy if exists profiles_own on public.profiles;
create policy profiles_own on public.profiles
for all to authenticated
using ((select auth.uid()) = id)
with check ((select auth.uid()) = id);

drop policy if exists settings_own on public.user_settings;
create policy settings_own on public.user_settings
for all to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

drop policy if exists boards_own on public.boards;
create policy boards_own on public.boards
for all to authenticated
using ((select auth.uid()) = owner_id)
with check ((select auth.uid()) = owner_id);

drop policy if exists lanes_own_board on public.lanes;
create policy lanes_own_board on public.lanes
for all to authenticated
using (
    exists (
        select 1
        from public.boards b
        where b.id = lanes.board_id
          and b.owner_id = (select auth.uid())
    )
)
with check (
    exists (
        select 1
        from public.boards b
        where b.id = lanes.board_id
          and b.owner_id = (select auth.uid())
    )
);

drop policy if exists cards_own_board on public.cards;
create policy cards_own_board on public.cards
for all to authenticated
using (
    exists (
        select 1
        from public.boards b
        where b.id = cards.board_id
          and b.owner_id = (select auth.uid())
    )
)
with check (
    exists (
        select 1
        from public.boards b
        where b.id = cards.board_id
          and b.owner_id = (select auth.uid())
    )
);

drop policy if exists activity_own on public.activity;
create policy activity_own on public.activity
for all to authenticated
using ((select auth.uid()) = owner_id)
with check ((select auth.uid()) = owner_id);

```


Så brukte jeg ca en time på å få hosta serveren på en ssh tunnel via ubuntu serveren min.
Nå kjører den på http://localhost:8000
Da mangler det bare hovedsakelig å få den opp på en cloudflare tunnel så den er tilgjengelig overalt.


# Add cloudflare gpg key
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null

# Add this repo to your apt repositories
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main' | sudo tee /etc/apt/sources.list.d/cloudflared.list

# install cloudflared
sudo apt-get update && sudo apt-get install cloudflared

sudo cloudflared service install eyJhIjoiMTM2OTM2ZjBhYjA5MzJmZmM2MGEyYWNjZGNlZWZjMTUiLCJ0IjoiYzhmNjcwZmMtMzJhYy00ZWFkLWJmYjYtYjg2MTNhYmYwOWQ1IiwicyI6IllXVXpabU01WW1NdFpUVmxPUzAwTlRnMUxUazJaakV0TUdVeE0yWmlORFUxTlRjNSJ9