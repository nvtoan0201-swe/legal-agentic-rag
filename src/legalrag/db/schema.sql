-- Documents, their structural units, and document-level relations.
DROP TABLE IF EXISTS relations, units, documents CASCADE;

CREATE TABLE documents (
    doc_key           text PRIMARY KEY,          -- e.g. '45/2019/QH14'
    source_id         text NOT NULL,             -- id in the HF dataset ('legacy:<id>' if legacy only)
    legacy_id         bigint,
    so_ky_hieu        text NOT NULL,
    loai_van_ban      text NOT NULL,
    title             text NOT NULL,
    co_quan_ban_hanh  text,
    ngay_ban_hanh     date,
    ngay_co_hieu_luc  date,
    ngay_het_hieu_luc date,
    status_raw        text,                      -- as published in the dataset
    status            text NOT NULL,             -- resolved, see ingest/status.py
    status_source     text NOT NULL,
    status_flags      text[] NOT NULL DEFAULT '{}',
    domains           text[] NOT NULL,
    hop_rank          int,
    content_source    text NOT NULL,             -- vbpl_html | legacy_text | none
    parse_clean       boolean,
    parse_issues      jsonb,
    n_articles        int,
    dropped_share     real,                      -- signature lines discarded by the parser
    attached_share    real,                      -- text after the signature block (#kt units)
    preamble          text
);

CREATE TABLE units (
    unit_id   text PRIMARY KEY,                  -- e.g. '45/2019/QH14#d35-k2-a'
    doc_key   text NOT NULL REFERENCES documents ON DELETE CASCADE,
    kind      text NOT NULL,                     -- dieu | khoan | diem | phu_luc | body
    number    text,
    parent_id text REFERENCES units,
    ordinal   int NOT NULL,
    title     text,
    text      text NOT NULL,                     -- own text, children excluded
    chuong    text,
    muc       text
);
CREATE INDEX units_doc_idx ON units (doc_key);
CREATE INDEX units_parent_idx ON units (parent_id);

CREATE TABLE relations (
    id               bigserial PRIMARY KEY,
    actor_key        text REFERENCES documents,  -- NULL when outside the corpus
    target_key       text REFERENCES documents,
    actor_source_id  text,
    target_source_id text,
    rel              text NOT NULL,              -- replaces | repeals | amends | guides | ...
    label            text,                       -- original label on vbpl.vn
    source           text NOT NULL,              -- vbpl | override
    suspect          boolean NOT NULL DEFAULT false  -- actor issued before target
);
CREATE INDEX relations_actor_idx ON relations (actor_key);
CREATE INDEX relations_target_idx ON relations (target_key);
