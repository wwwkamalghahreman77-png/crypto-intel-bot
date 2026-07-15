create table if not exists dex_discoveries (
    id bigint generated always as identity primary key,
    token text,
    network text,
    date_found text,
    security_score float8,
    dex_score float8,
    price_found float8,
    liquidity float8,
    volume float8,
    status text
);

create table if not exists crypto_reports (
    id bigint generated always as identity primary key,
    token text,
    date_found text,
    total_score float8,
    security float8,
    fundamental float8,
    news float8,
    technical float8,
    community float8,
    status text
);

create table if not exists performance_tracking (
    id bigint generated always as identity primary key,
    token text,
    initial_price float8,
    price_7d float8,
    price_30d float8,
    result text
);
