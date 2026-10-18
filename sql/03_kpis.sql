-- Headline KPIs
DROP TABLE IF EXISTS kpi_summary;
CREATE TABLE kpi_summary AS
SELECT COUNT(*)                                             AS transactions,
       SUM(Class)                                           AS fraud_transactions,
       ROUND(10000.0 * SUM(Class) / COUNT(*), 2)            AS fraud_rate_bps,
       ROUND(SUM(Amount), 0)                                AS total_amount,
       ROUND(SUM(CASE WHEN Class = 1 THEN Amount END), 0)   AS fraud_amount,
       ROUND(10000.0 * SUM(CASE WHEN Class = 1 THEN Amount END) / SUM(Amount), 2) AS fraud_amount_rate_bps,
       ROUND(AVG(CASE WHEN Class = 1 THEN Amount END), 2)   AS avg_fraud_amount,
       ROUND(AVG(CASE WHEN Class = 0 THEN Amount END), 2)   AS avg_legit_amount
  FROM txns;

-- Fraud by amount band
DROP TABLE IF EXISTS fraud_by_amount_band;
CREATE TABLE fraud_by_amount_band AS
SELECT amount_band, COUNT(*) AS transactions, SUM(Class) AS fraud_transactions,
       ROUND(10000.0 * SUM(Class) / COUNT(*), 2) AS fraud_rate_bps,
       ROUND(100.0 * SUM(Class) / (SELECT SUM(Class) FROM txns), 1) AS share_of_all_fraud_pct,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM txns), 1)     AS share_of_all_txns_pct
  FROM txns GROUP BY amount_band;

-- Fraud by hour of the 24-hour cycle (the data starts at an unknown clock time, so this is hours since start, modulo 24)
DROP TABLE IF EXISTS fraud_by_hour_of_cycle;
CREATE TABLE fraud_by_hour_of_cycle AS
WITH h AS (SELECT hour_of_cycle, COUNT(*) AS transactions, SUM(Class) AS fraud_transactions FROM txns GROUP BY hour_of_cycle),
     r AS (SELECT *, NTILE(4) OVER (ORDER BY transactions) AS volume_quartile FROM h)
SELECT hour_of_cycle, transactions, fraud_transactions,
       ROUND(10000.0 * fraud_transactions / transactions, 2) AS fraud_rate_bps,
       volume_quartile   -- 1 = quietest quarter of hours by volume
  FROM r ORDER BY hour_of_cycle;

-- Fraud rate in quiet hours vs the rest
DROP TABLE IF EXISTS quiet_vs_busy;
CREATE TABLE quiet_vs_busy AS
SELECT CASE WHEN volume_quartile = 1 THEN 'quietest 25% of hours' ELSE 'other hours' END AS period,
       SUM(transactions) AS transactions, SUM(fraud_transactions) AS fraud_transactions,
       ROUND(10000.0 * SUM(fraud_transactions) / SUM(transactions), 2) AS fraud_rate_bps
  FROM fraud_by_hour_of_cycle GROUP BY 1;

-- Fraud by hour since the start of the two days: are attacks steady or bursty?
DROP TABLE IF EXISTS fraud_by_hour_since_start;
CREATE TABLE fraud_by_hour_since_start AS
SELECT hours_since_start, COUNT(*) AS transactions, SUM(Class) AS fraud_transactions,
       ROUND(10000.0 * SUM(Class) / COUNT(*), 2) AS fraud_rate_bps,
       ROUND(100.0 * SUM(Class) / (SELECT SUM(Class) FROM txns), 1) AS share_of_all_fraud_pct
  FROM txns GROUP BY hours_since_start;
