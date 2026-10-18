-- Keep the first copy of each exact duplicate; keep everything else (zero amounts are flagged, not removed).
DROP TABLE IF EXISTS txns_ranked;
CREATE TABLE txns_ranked AS
SELECT rowid AS raw_row, *,
       ROW_NUMBER() OVER (PARTITION BY Time, V1, V2, V3, V4, V5, V6, V7, V8, V9, V10, V11, V12, V13, V14, V15, V16, V17, V18, V19, V20, V21, V22, V23, V24, V25, V26, V27, V28, Amount, Class ORDER BY rowid) AS dup_rank
  FROM txns_raw;

DROP TABLE IF EXISTS txns_removed;
CREATE TABLE txns_removed AS
SELECT raw_row, Time, Amount, Class, 'exact duplicate' AS reason FROM txns_ranked WHERE dup_rank > 1;

DROP TABLE IF EXISTS txns;
CREATE TABLE txns AS
SELECT raw_row AS txn_id, Time, V1, V2, V3, V4, V5, V6, V7, V8, V9, V10, V11, V12, V13, V14, V15, V16, V17, V18, V19, V20, V21, V22, V23, V24, V25, V26, V27, V28, Amount, Class,
       CAST(Time / 3600 AS INTEGER)                        AS hours_since_start,
       CAST(Time / 3600 AS INTEGER) % 24                   AS hour_of_cycle,
       CASE WHEN Amount = 0 THEN 'zero'
            WHEN Amount < 1 THEN 'under $1'
            WHEN Amount < 10 THEN '$1-10'
            WHEN Amount < 50 THEN '$10-50'
            WHEN Amount < 200 THEN '$50-200'
            WHEN Amount < 1000 THEN '$200-1000'
            ELSE '$1000+' END                              AS amount_band
  FROM txns_ranked WHERE dup_rank = 1;
