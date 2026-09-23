-- ReturnReview persistent storage foundation for the shared Supabase Project Hub.
-- Scope: return_review only. No secret values belong in this file.
-- Before applying, the app must be registered in hub.apps with slug/schema return_review.

select hub.assert_app_scope('return_review', 'return_review');

create schema if not exists return_review authorization postgres;

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'return_review_backend') then
    create role return_review_backend
      login noinherit nosuperuser nocreatedb nocreaterole noreplication
      valid until 'infinity';
  end if;
end
$$;

alter role return_review_backend set search_path = return_review;
grant connect on database postgres to return_review_backend;
grant usage on schema return_review to return_review_backend;

create table if not exists return_review.return_cases (
  id varchar(36) primary key,
  external_case_id varchar(100) not null unique,
  product_name varchar(160) not null,
  product_category varchar(80) not null default 'cardboard_box',
  customer_reason text not null,
  status varchar(40) not null default 'DRAFT',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists ix_return_review_return_cases_external_case_id
  on return_review.return_cases(external_case_id);

create table if not exists return_review.case_images (
  id varchar(36) primary key,
  case_id varchar(36) not null references return_review.return_cases(id) on delete cascade,
  image_path text not null,
  content_type varchar(80) not null default 'image/jpeg',
  image_blob bytea not null,
  view_label varchar(40) not null default 'unspecified',
  width integer not null default 0,
  height integer not null default 0,
  quality_score double precision,
  quality_warning text,
  created_at timestamptz not null default now()
);
create index if not exists ix_return_review_case_images_case_id
  on return_review.case_images(case_id);

create table if not exists return_review.cv_inspections (
  id varchar(36) primary key,
  case_image_id varchar(36) not null unique
    references return_review.case_images(id) on delete cascade,
  model_version varchar(120) not null,
  product_similarity double precision,
  product_verified boolean not null default false,
  latency_ms double precision,
  raw_evidence jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists return_review.defect_findings (
  id varchar(36) primary key,
  inspection_id varchar(36) not null
    references return_review.cv_inspections(id) on delete cascade,
  defect_type varchar(80) not null default 'unknown',
  confidence double precision not null default 0,
  bbox_json jsonb,
  mask_path text,
  mask_content_type varchar(80),
  mask_blob bytea,
  affected_area_percent double precision,
  created_at timestamptz not null default now()
);
create index if not exists ix_return_review_defect_findings_inspection_id
  on return_review.defect_findings(inspection_id);

create table if not exists return_review.ai_reviews (
  id varchar(36) primary key,
  case_id varchar(36) not null references return_review.return_cases(id) on delete cascade,
  provider varchar(40) not null default 'deterministic',
  model_name varchar(120) not null default 'fallback',
  prompt_version varchar(40) not null default 'v1',
  review_json jsonb not null,
  recommendation varchar(80) not null,
  unsupported_claim_flag boolean not null default false,
  latency_ms double precision,
  created_at timestamptz not null default now()
);
create index if not exists ix_return_review_ai_reviews_case_id
  on return_review.ai_reviews(case_id);

create table if not exists return_review.reviewer_decisions (
  id varchar(36) primary key,
  case_id varchar(36) not null references return_review.return_cases(id) on delete cascade,
  reviewer_action varchar(60) not null,
  reviewer_notes text,
  edited_review_json jsonb,
  created_at timestamptz not null default now()
);
create index if not exists ix_return_review_reviewer_decisions_case_id
  on return_review.reviewer_decisions(case_id);

create table if not exists return_review.audit_events (
  id varchar(36) primary key,
  case_id varchar(36) not null,
  event_type varchar(80) not null,
  payload_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists ix_return_review_audit_events_case_id
  on return_review.audit_events(case_id);

grant select, insert, update, delete on all tables in schema return_review
  to return_review_backend;
alter default privileges for role postgres in schema return_review
  grant select, insert, update, delete on tables to return_review_backend;

alter table return_review.return_cases enable row level security;
alter table return_review.case_images enable row level security;
alter table return_review.cv_inspections enable row level security;
alter table return_review.defect_findings enable row level security;
alter table return_review.ai_reviews enable row level security;
alter table return_review.reviewer_decisions enable row level security;
alter table return_review.audit_events enable row level security;

drop policy if exists return_review_backend_all_return_cases on return_review.return_cases;
create policy return_review_backend_all_return_cases
  on return_review.return_cases for all to return_review_backend using (true) with check (true);

drop policy if exists return_review_backend_all_case_images on return_review.case_images;
create policy return_review_backend_all_case_images
  on return_review.case_images for all to return_review_backend using (true) with check (true);

drop policy if exists return_review_backend_all_cv_inspections on return_review.cv_inspections;
create policy return_review_backend_all_cv_inspections
  on return_review.cv_inspections for all to return_review_backend using (true) with check (true);

drop policy if exists return_review_backend_all_defect_findings on return_review.defect_findings;
create policy return_review_backend_all_defect_findings
  on return_review.defect_findings for all to return_review_backend using (true) with check (true);

drop policy if exists return_review_backend_all_ai_reviews on return_review.ai_reviews;
create policy return_review_backend_all_ai_reviews
  on return_review.ai_reviews for all to return_review_backend using (true) with check (true);

drop policy if exists return_review_backend_all_reviewer_decisions on return_review.reviewer_decisions;
create policy return_review_backend_all_reviewer_decisions
  on return_review.reviewer_decisions for all to return_review_backend using (true) with check (true);

drop policy if exists return_review_backend_all_audit_events on return_review.audit_events;
create policy return_review_backend_all_audit_events
  on return_review.audit_events for all to return_review_backend using (true) with check (true);
