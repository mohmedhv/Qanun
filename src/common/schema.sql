PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS texts (
    text_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    number TEXT NOT NULL,
    title TEXT,
    date_signed TEXT,
    jo_number TEXT,
    jo_date TEXT,
    source_url TEXT,
    rank_level INTEGER NOT NULL CHECK (rank_level BETWEEN 1 AND 5),
    language TEXT NOT NULL DEFAULT 'fr',
    pdf_path TEXT,
    CHECK (date_signed IS NULL OR date_signed GLOB '????-??-??'),
    CHECK (jo_date IS NULL OR jo_date GLOB '????-??-??')
);

CREATE TABLE IF NOT EXISTS articles (
    article_id TEXT PRIMARY KEY,
    text_id TEXT NOT NULL REFERENCES texts(text_id),
    number TEXT NOT NULL,
    sort_key INTEGER NOT NULL,
    suffix TEXT,
    parent_title TEXT,
    parent_chapter TEXT,
    parent_section TEXT,
    content TEXT NOT NULL,
    paragraphs TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'in_force' CHECK (status IN ('in_force', 'repealed')),
    valid_from TEXT,
    valid_to TEXT,
    source_url TEXT,
    UNIQUE (text_id, number),
    CHECK (valid_from IS NULL OR valid_from GLOB '????-??-??'),
    CHECK (valid_to IS NULL OR valid_to GLOB '????-??-??')
);

CREATE TABLE IF NOT EXISTS relations (
    relation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('modifies', 'repeals', 'applies', 'adds', 'cites'))
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL REFERENCES articles(article_id),
    part INTEGER NOT NULL,
    n_parts INTEGER NOT NULL,
    text TEXT NOT NULL,
    text_for_embedding TEXT NOT NULL,
    n_chars INTEGER NOT NULL,
    source_url TEXT
);

CREATE INDEX IF NOT EXISTS idx_articles_text_number ON articles(text_id, number);
CREATE INDEX IF NOT EXISTS idx_articles_sort_key ON articles(text_id, sort_key);
CREATE INDEX IF NOT EXISTS idx_articles_validity ON articles(valid_from, valid_to);
CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id);

-- The P3 versions DDL is pending its actual schema; see docs/contract_open_questions.md.
