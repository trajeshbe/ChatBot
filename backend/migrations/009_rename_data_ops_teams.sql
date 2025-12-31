-- Migration 009: Rename Data Operations Teams with Professional Alternatives
-- Date: 2025-11-27
-- Purpose: Replace specific business unit names with generic professional alternatives

BEGIN;

-- Get Data Operations ID
DO $$
DECLARE
    data_ops_id UUID;
BEGIN
    SELECT id INTO data_ops_id FROM departments WHERE name = 'Data Operations';

    -- Alternative naming options - using professional generic names

    -- Option 1: Business Intelligence & Analytics focus
    UPDATE departments SET name = 'Business Intelligence Team' WHERE name = 'Air Business Distribution' AND parent_department_id = data_ops_id;
    UPDATE departments SET name = 'Analytics & Insights Team' WHERE name = 'ALF' AND parent_department_id = data_ops_id;
    UPDATE departments SET name = 'Market Research Team' WHERE name = 'DMS Construction Data Research' AND parent_department_id = data_ops_id;
    UPDATE departments SET name = 'Data Quality & Governance' WHERE name = 'DODs' AND parent_department_id = data_ops_id;
    UPDATE departments SET name = 'Customer Analytics Team' WHERE name = 'Glenigan FRO' AND parent_department_id = data_ops_id;
    UPDATE departments SET name = 'Digital Analytics Team' WHERE name = 'Haymarket' AND parent_department_id = data_ops_id;
    UPDATE departments SET name = 'Healthcare Data Team' WHERE name = 'HSJ' AND parent_department_id = data_ops_id;
    UPDATE departments SET name = 'Medical Research Team' WHERE name = 'HSJ On Medica' AND parent_department_id = data_ops_id;
    UPDATE departments SET name = 'Enterprise Data Team' WHERE name = 'Informa Connect - Data Research' AND parent_department_id = data_ops_id;
    UPDATE departments SET name = 'Strategic Planning Team' WHERE name = 'Leadership' AND parent_department_id = data_ops_id;
    UPDATE departments SET name = 'Growth Analytics Team' WHERE name = 'Leadscale' AND parent_department_id = data_ops_id;
    UPDATE departments SET name = 'Data Integration Team' WHERE name = 'LLI Data' AND parent_department_id = data_ops_id;
    UPDATE departments SET name = 'Public Sector Research' WHERE name = 'Political Engagement - Research Support' AND parent_department_id = data_ops_id;
    UPDATE departments SET name = 'Data Operations Quality' WHERE name = 'Quality' AND parent_department_id = data_ops_id;
    UPDATE departments SET name = 'Operational Analytics Team' WHERE name = 'Tactical Data' AND parent_department_id = data_ops_id;
    UPDATE departments SET name = 'Applied Research Team' WHERE name = 'Tactical Data Research' AND parent_department_id = data_ops_id;

END $$;

-- Verification
SELECT
    d_parent.name AS division,
    d.name AS team,
    d.is_active
FROM departments d
LEFT JOIN departments d_parent ON d.parent_department_id = d_parent.id
WHERE d_parent.name = 'Data Operations'
ORDER BY d.name;

COMMIT;
