-- Data-quality checks on the raw transactions table (one row per check).
SELECT 'exact duplicate rows' AS check_name,
       COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM txns_raw)) AS failing_rows,
       COUNT(*) AS total_rows FROM txns_raw
UNION ALL
SELECT 'missing values in any column', SUM(Time IS NULL OR V1 IS NULL OR V2 IS NULL OR V3 IS NULL OR V4 IS NULL OR V5 IS NULL OR V6 IS NULL OR V7 IS NULL OR V8 IS NULL OR V9 IS NULL OR V10 IS NULL OR V11 IS NULL OR V12 IS NULL OR V13 IS NULL OR V14 IS NULL OR V15 IS NULL OR V16 IS NULL OR V17 IS NULL OR V18 IS NULL OR V19 IS NULL OR V20 IS NULL OR V21 IS NULL OR V22 IS NULL OR V23 IS NULL OR V24 IS NULL OR V25 IS NULL OR V26 IS NULL OR V27 IS NULL OR V28 IS NULL OR Amount IS NULL OR Class IS NULL), COUNT(*) FROM txns_raw
UNION ALL
SELECT 'Class not 0 or 1', SUM(Class NOT IN (0, 1)), COUNT(*) FROM txns_raw
UNION ALL
SELECT 'negative Amount', SUM(Amount < 0), COUNT(*) FROM txns_raw
UNION ALL
SELECT 'zero Amount', SUM(Amount = 0), COUNT(*) FROM txns_raw
UNION ALL
SELECT 'Amount above 5000', SUM(Amount > 5000), COUNT(*) FROM txns_raw
UNION ALL
SELECT 'Time goes backwards', SUM(Time < prev_time), COUNT(*)
  FROM (SELECT Time, LAG(Time) OVER (ORDER BY rowid) AS prev_time FROM txns_raw);
