-- Nifty 100 Financial Intelligence Platform - Exploratory SQL Queries
-- Deliverable D-04 (Sprint 1, Section 24)

-- 1. Company Record Count & Universe Verification
SELECT COUNT(*) AS total_companies FROM companies;

-- 2. Data Coverage and Year Distribution across Companies
SELECT 
    c.id, 
    c.company_name, 
    COUNT(DISTINCT p.year) AS pl_years,
    COUNT(DISTINCT b.year) AS bs_years,
    COUNT(DISTINCT cf.year) AS cf_years
FROM companies c
LEFT JOIN profitandloss p ON c.id = p.company_id
LEFT JOIN balancesheet b ON c.id = b.company_id
LEFT JOIN cashflow cf ON c.id = cf.company_id
GROUP BY c.id
ORDER BY pl_years ASC;

-- 3. Top 10 ROE Companies (Latest Year)
SELECT 
    r.company_id, 
    c.company_name, 
    r.return_on_equity_pct 
FROM financial_ratios r 
JOIN companies c ON r.company_id = c.id 
WHERE r.year = (SELECT MAX(year) FROM financial_ratios) 
ORDER BY r.return_on_equity_pct DESC 
LIMIT 10;

-- 4. Debt-Free Companies (Latest Year)
SELECT 
    company_id, 
    year, 
    debt_to_equity 
FROM financial_ratios 
WHERE debt_to_equity = 0 
  AND year = (SELECT MAX(year) FROM financial_ratios);

-- 5. Companies with Consecutive Positive FCF (>= 5 Years)
SELECT 
    company_id, 
    COUNT(*) AS positive_fcf_yrs 
FROM financial_ratios 
WHERE free_cash_flow_cr > 0 
GROUP BY company_id 
HAVING positive_fcf_yrs >= 5
ORDER BY positive_fcf_yrs DESC;

-- 6. Sector Median ROE
SELECT 
    s.broad_sector, 
    ROUND(AVG(r.return_on_equity_pct), 1) AS median_roe,
    COUNT(DISTINCT r.company_id) AS company_count
FROM financial_ratios r 
JOIN sectors s ON r.company_id = s.company_id 
WHERE r.year = (SELECT MAX(year) FROM financial_ratios) 
GROUP BY s.broad_sector 
ORDER BY median_roe DESC;

-- 7. Capital Allocation Pattern Count
SELECT 
    pattern_label, 
    COUNT(*) AS companies 
FROM capital_allocation 
WHERE year = (SELECT MAX(year) FROM capital_allocation) 
GROUP BY pattern_label 
ORDER BY companies DESC;

-- 8. High Growth Companies: Revenue CAGR > 15% (5yr)
SELECT 
    r.company_id, 
    c.company_name, 
    r.revenue_cagr_5yr 
FROM financial_ratios r 
JOIN companies c ON r.company_id = c.id 
WHERE r.revenue_cagr_5yr > 15 
ORDER BY r.revenue_cagr_5yr DESC;

-- 9. Documentation Gap: Missing Annual Reports
SELECT 
    c.id, 
    c.company_name, 
    (2024 - COUNT(d.Year)) AS missing_yrs 
FROM companies c 
LEFT JOIN documents d ON c.id = d.company_id AND d.Year >= 2015 
GROUP BY c.id 
HAVING missing_yrs > 2 
ORDER BY missing_yrs DESC;

-- 10. Peer Group Rankings (ROE)
SELECT 
    p.peer_group_name, 
    r.company_id, 
    r.return_on_equity_pct, 
    RANK() OVER (PARTITION BY p.peer_group_name ORDER BY r.return_on_equity_pct DESC) AS roe_rank 
FROM financial_ratios r 
JOIN peer_groups p ON r.company_id = p.company_id 
WHERE r.year = (SELECT MAX(year) FROM financial_ratios);

-- 11. Null & Missing Value Audits on Financial Statements
SELECT 
    'profitandloss' AS tbl,
    SUM(CASE WHEN sales IS NULL THEN 1 ELSE 0 END) AS null_sales,
    SUM(CASE WHEN operating_profit IS NULL THEN 1 ELSE 0 END) AS null_op,
    SUM(CASE WHEN net_profit IS NULL THEN 1 ELSE 0 END) AS null_pat
FROM profitandloss;
