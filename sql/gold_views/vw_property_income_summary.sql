CREATE OR ALTER VIEW gold.vw_property_income_summary AS
SELECT
    property_id,
    property_name,
    property_type,
    city,
    state,
    total_units,
    active_lease_count,
    CAST(occupancy_rate AS decimal(9, 4)) AS occupancy_rate,
    CAST(monthly_rent_roll AS decimal(18, 2)) AS monthly_rent_roll,
    CAST(annualized_rent AS decimal(18, 2)) AS annualized_rent,
    CAST(market_value AS decimal(18, 2)) AS market_value,
    CAST(income_yield AS decimal(9, 4)) AS income_yield,
    CASE
        WHEN occupancy_rate >= 0.90 THEN 'Healthy'
        WHEN occupancy_rate >= 0.75 THEN 'Watch'
        ELSE 'Under-occupied'
    END AS occupancy_band
FROM silver.property_income;
