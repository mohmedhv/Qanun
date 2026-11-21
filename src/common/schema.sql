PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS texts (
    text_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    number TEXT NOT NULL,
    title TEXT NOT NULL,
    date_signed TEXT,
    jo_number TEXT,
    jo_date TEXT,
    language TEXT NOT NULL DEFAULT 'fr',
    rank_level INTEGER NOT NULL CHECK (rank_level BETWEEN 1 AND 5),
    source_url TEXT,
    pdf_path TEXT,
    CHECK (date_signed IS NULL OR date_signed GLOB '????-??-??'),
    CHECK (jo_date IS NULL OR jo_date GLOB '????-??-??')
);

CREATE TABLE IF NOT EXISTS articles (
    article_id INTEGER PRIMARY KEY AUTOINCREMENT,
    text_id TEXT NOT NULL REFERENCES texts(text_id) ON DELETE CASCADE,
    article_number TEXT NOT NULL,
    parent_title TEXT,
    parent_chapter TEXT,
    content TEXT NOT NULL,
    version_no INTEGER NOT NULL DEFAULT 1,
    valid_from TEXT,
    valid_to TEXT,
    status TEXT NOT NULL CHECK (status IN ('in_force', 'repealed')),
    modified_by_text_id TEXT REFERENCES texts(text_id),
    source_url TEXT,
    CHECK (valid_from IS NULL OR valid_from GLOB '????-??-??'),
    CHECK (valid_to IS NULL OR valid_to GLOB '????-??-??')
);

CREATE TABLE IF NOT EXISTS relations (
    from_text_id TEXT NOT NULL REFERENCES texts(text_id) ON DELETE CASCADE,
    to_text_id TEXT NOT NULL REFERENCES texts(text_id) ON DELETE CASCADE,
    to_article_number TEXT NOT NULL DEFAULT '',
    relation_type TEXT NOT NULL CHECK (relation_type IN ('modifies', 'repeals', 'applies', 'adds')),
    PRIMARY KEY (from_text_id, to_text_id, to_article_number, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_articles_text_number ON articles(text_id, article_number);
CREATE INDEX IF NOT EXISTS idx_articles_validity ON articles(valid_from, valid_to);
CREATE INDEX IF NOT EXISTS idx_relations_to_text ON relations(to_text_id);
