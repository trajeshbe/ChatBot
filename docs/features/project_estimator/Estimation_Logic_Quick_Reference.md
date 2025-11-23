# Project Estimator - Core Estimation Logic Reference

## Quick Reference: Calculation Formulas

### 1. Base Task Effort Calculation

```
Task_Hours = Base_Hours × Complexity_Multiplier

Where Complexity_Multiplier:
- Simple: 0.5 - 1.0
- Medium: 1.0 - 2.0
- Complex: 2.0 - 4.0
```

### 2. Role-Based Overhead (Auto-Added)

```excel
Solution Architect Hours = ROUNDUP(Total_Planning_Hours × 0.10, 0)
PM Hours = ROUNDUP(Total_All_Hours × 0.05, 0)
BA Hours = ROUNDUP(Total_Planning_Hours × 0.05, 0)
```

### 3. Testing Overhead (Auto-Calculated from Development)

```excel
Dev_Unit_Testing_Hours = Development_Hours × 0.20
QA_Testing_Hours = Development_Hours × 0.25
Integration_Testing_Hours = Development_Hours × 0.20

Total_Testing_Hours = Development_Hours × 0.65
```

### 4. Contingency

```excel
Contingency_Hours = Total_All_Hours × 0.10
```

### 5. Cost Calculation

```excel
Task_Cost = Task_Hours × Billing_Rate

Where Billing_Rate:
- Planning: $25/hour
- Development: $30/hour
- Testing: $25/hour
- UI Development: $22/hour
- Solution Architect: $40/hour
- Scraping Development: $22/hour
```

### 6. Infrastructure Costs

```excel
One_Time_Infrastructure = $280 (default)
Monthly_BAU = $1,030 (default)
Annual_BAU = Monthly_BAU × 12
Total_First_Year = One_Time + Annual_BAU + Development_Cost
Cost_Per_Document = Total_First_Year / Annual_Volume
```

## Excel Formula Patterns

### AIML_cost Sheet Formulas

**Row 4: Planning Phase Total**
```excel
D4: =SUM(D5:D9)
F4: =SUM(F5:F9)
```

**Row 5-9: Individual Planning Tasks**
```excel
D5: 8  (or user input)
E5: =lookup!$B$2
F5: =D5*$E5
```

**Row 11: Solution Architect Effort**
```excel
D11: =ROUNDUP(SUM($D$5:$D$9)*lookup!B7,0)
E11: 40
F11: =D11*$E11
```

**Row 12: PM Effort**
```excel
D12: =ROUNDUP(SUM($D$5:$D$9)*lookup!B8,0)
E12: =lookup!$B$2
F12: =D12*$E12
```

**Row 14: Development Phase Total**
```excel
D14: =SUM(D15:D23)
F14: =SUM(F15:F23)
```

**Testing Calculations**
```excel
Dev_Unit_Testing_Hours: =ROUNDUP(D14*lookup!B9,0)
QA_Testing_Hours: =ROUNDUP(D14*lookup!B10,0)
Integration_Testing_Hours: =ROUNDUP(D14*lookup!B11,0)
```

### AIML_COST_SUMMARY Formulas

```excel
C3: =VLOOKUP($A3,AIML_cost!$A:$D,4,0)
C10: =SUM(C3:C9)
```

### Resource Loading Formulas

```excel
Week_Allocation = Task_Hours / 7
Daily_Per_Resource = Week_Allocation / 2 / 5
```

## Lookup Table Structure

| Item | Plan | Dev | Test |
|------|------|-----|------|
| Labor cost | 25 | 30 | 25 |
| UI labor cost | - | 22 | - |
| Dev Unit Testing | 0.20 | 0.20 | - |
| QA Testing | 0.25 | 0.25 | - |
| Integration Testing | 0.20 | 0.20 | - |

| Role | Effort % |
|------|----------|
| Solution Architect | 0.10 |
| PM | 0.05 |
| BA | 0.05 |
| Contingency | 0.10 |

## Task Categorization Logic

### Planning Tasks Pattern
- "Analysis" → Planning
- "Design" → Planning
- "Assessment" → Planning
- "Requirements" → Planning
- "Architecture" → Planning

### Development Tasks Pattern
- "Build" → Development
- "Implement" → Development
- "Develop" → Development
- "Create" → Development
- "Code" → Development

### Integration Tasks Pattern
- "Integration" → Integration
- "Connect" → Integration
- "API" → Integration
- "Workflow" → Integration

### Testing Tasks Pattern
- Auto-generated from development
- "Unit Test" → Testing
- "QA" → Testing
- "Integration Test" → Testing

### Documentation Tasks Pattern
- "Documentation" → Documentation
- "Manual" → Documentation
- "Guide" → Documentation

## Effort Estimation Heuristics

### AI/ML Projects
```
Component Analysis: 16-24 hours
Model Development: 40-80 hours per model
Training & Tuning: 20-40 hours per model
Integration: 24-48 hours
Testing: 40% of development time
```

### Web Applications
```
Backend API: 8-16 hours per endpoint
Frontend Component: 4-8 hours per component
Database Design: 16-24 hours
Authentication: 24-32 hours
Deployment: 8-16 hours
```

### Data Processing
```
ETL Pipeline: 24-40 hours
Data Validation: 16-24 hours
Error Handling: 16-24 hours
Monitoring: 8-16 hours
```

## Complete Calculation Flow

```
1. User provides scope → Claude analyzes
2. Identify components → Map to task templates
3. Apply complexity multiplier → Get base hours
4. Calculate phase totals:
   - Planning: Sum of planning tasks
   - Development: Sum of dev tasks
   - Integration: Sum of integration tasks
5. Auto-add overhead:
   - SA: Planning × 0.10
   - PM: Total × 0.05
   - BA: Planning × 0.05
6. Auto-calculate testing:
   - Unit: Dev × 0.20
   - QA: Dev × 0.25
   - Integration: Dev × 0.20
7. Add contingency: Total × 0.10
8. Calculate costs:
   - Each phase × respective rate
   - Infrastructure: one-time + BAU
9. Generate resource loading:
   - Distribute hours across timeline
10. Create summary and export
```

## Excel Tab Dependencies

```
AIML_cost (main)
    ↓
    References: lookup (for rates and percentages)
    ↓
    Referenced by: AIML_COST_SUMMARY (VLOOKUPs)
    ↓
    Referenced by: Resource_Loading (week calculations)
    
unit_cost (independent)
    ↓
    Provides: Infrastructure costs

lookup (independent)
    ↓
    Provides: All rates and percentages
```

## Sample Project Breakdown

**Example: AI Document Extraction System (Medium Complexity)**

```
Planning (72 hrs × $25 = $1,800):
  - Requirements Analysis: 16 hrs
  - Architecture Design: 24 hrs
  - Schema Design: 32 hrs
  + SA Overhead: 7 hrs
  + PM Overhead: 4 hrs
  + BA Overhead: 4 hrs

Development (240 hrs × $30 = $7,200):
  - PDF Parser: 40 hrs
  - ML Classification: 80 hrs
  - Extraction Engine: 60 hrs
  - API Development: 40 hrs
  - Frontend: 20 hrs

Integration (48 hrs × $30 = $1,440):
  - System Integration: 24 hrs
  - API Integration: 24 hrs

Testing (96 hrs × $25 = $2,400):
  - Unit Testing: 48 hrs (240 × 0.20)
  - QA Testing: 60 hrs (240 × 0.25)
  - Integration: 48 hrs (240 × 0.20)

Documentation (24 hrs × $25 = $600):
  - Technical Docs: 12 hrs
  - User Manual: 8 hrs
  - Deployment Guide: 4 hrs

PM & Contingency (48 hrs × $25 = $1,200):
  - PM: 24 hrs (480 × 0.05)
  - Contingency: 48 hrs (480 × 0.10)

Infrastructure:
  - One-time: $280
  - BAU (annual): $12,360

TOTAL: $27,280
```

## Key Rules for Claude Code Implementation

1. **Always preserve formulas** - Never hard-code calculated values
2. **Maintain cell references** - Use correct Excel reference notation
3. **Apply auto-calculations** - SA, PM, BA, Testing, Contingency must be automatic
4. **Use VLOOKUP correctly** - Range references must include sheet name
5. **Round up** - Use ROUNDUP for hour calculations (never partial hours)
6. **Link tabs** - Summary pulls from main sheet via VLOOKUP
7. **Editable cells** - Base hours (column D) should be editable
8. **Formula cells** - Cost calculations (column F) should be protected formulas
9. **Lookup references** - Always use absolute references ($B$2) for lookups
10. **Resource loading** - Auto-distribute hours across timeline based on phase totals

---

**This is the core logic to implement in Claude Code for accurate project estimation**
