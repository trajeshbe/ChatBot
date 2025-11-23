# Project Estimator - Claude Code Quick Start Guide

## 📋 What You Have

You now have 3 comprehensive documents to build your Project Estimator:

1. **Claude_Code_Project_Estimator_Prompt.md** - Complete system specification
2. **Estimation_Logic_Quick_Reference.md** - Core calculation formulas and logic
3. **Implementation_Code_Examples.md** - Ready-to-use code snippets

## 🚀 How to Use These Documents with Claude Code

### Step 1: Initial Prompt to Claude Code

Copy and paste this starter prompt to Claude Code:

```
I need to build a web-based Project Estimator application based on the detailed 
specifications in the attached documents. This app should:

1. Accept project scope as input (text or file upload)
2. Use Claude API to analyze the scope and break it into tasks
3. Generate two outputs:
   - Business Requirements Document (Word .docx)
   - Cost Estimation Sheet (Excel .xlsx with formulas)

Key features:
- Interactive UI with editable cost tables
- Configurable billing rates and percentages
- Multiple Excel tabs with cross-references (AIML_cost, AIML_COST_SUMMARY, 
  lookup, unit_cost, Resource Loading)
- Formula preservation in Excel export
- All formulas and calculations must match the patterns in the 
  Estimation_Logic_Quick_Reference.md

Tech stack preference:
- Frontend: React with Next.js
- Excel generation: ExcelJS library
- Word generation: docx library
- Spreadsheet UI: Handsontable or AG Grid

Please review the attached documentation and let's start by:
1. Setting up the project structure
2. Creating the core estimation engine with proper formula logic
3. Building the UI components

I'll provide the documents in the next message.
```

### Step 2: Share the Documentation

After Claude Code responds, share the relevant sections:

**For Core Logic:**
```
Here's the core estimation logic that must be implemented:

[Paste the "Complete Calculation Flow" section from Estimation_Logic_Quick_Reference.md]
```

**For Excel Formulas:**
```
Here are the exact Excel formulas to implement:

[Paste the "Excel Formula Patterns" section from Estimation_Logic_Quick_Reference.md]
```

**For Code Examples:**
```
Here are working code examples for Excel generation:

[Paste specific sections from Implementation_Code_Examples.md as needed]
```

## 📊 Key Implementation Priorities

### Phase 1: Core Estimation Engine (Week 1)
```
Priority 1 tasks:
1. Set up project with Next.js, ExcelJS, docx
2. Implement lookup table logic
3. Build formula calculation engine
4. Test basic Excel generation with formulas

Ask Claude Code:
"Let's start with Phase 1. Create the project structure and implement the 
core estimation engine with the lookup table logic. Reference the formula 
patterns in the Estimation_Logic_Quick_Reference.md"
```

### Phase 2: Excel Generation (Week 1-2)
```
Priority 2 tasks:
1. Create AIML_cost sheet with all formulas
2. Create AIML_COST_SUMMARY with VLOOKUP formulas
3. Create lookup, unit_cost sheets
4. Verify formula integrity

Ask Claude Code:
"Now implement the complete Excel generation following the code examples 
in Implementation_Code_Examples.md. Ensure all formulas are preserved 
and cross-sheet references work correctly."
```

### Phase 3: UI Development (Week 2)
```
Priority 3 tasks:
1. Create scope input interface
2. Build configuration panel
3. Implement editable cost table
4. Add download functionality

Ask Claude Code:
"Create the UI following the layout specifications in 
Claude_Code_Project_Estimator_Prompt.md. Focus on the editable 
configuration panel and results display."
```

### Phase 4: BRD Generation (Week 2-3)
```
Priority 4 tasks:
1. Implement Claude API integration for scope analysis
2. Create BRD template with docx
3. Map analysis results to BRD sections
4. Test document generation

Ask Claude Code:
"Implement the BRD generation following the structure in the main prompt 
document. Use the scope analysis prompt template and docx code examples."
```

### Phase 5: Integration & Testing (Week 3)
```
Priority 5 tasks:
1. Connect all components
2. Test end-to-end workflow
3. Verify formula accuracy
4. Test download functionality

Ask Claude Code:
"Let's integrate everything and run comprehensive tests. Verify that:
- All Excel formulas calculate correctly
- VLOOKUP references work across sheets
- BRD sections are properly populated
- Downloads work for both file types"
```

## 🔧 Critical Implementation Rules

Share these rules explicitly with Claude Code:

```
CRITICAL RULES for implementation:

1. FORMULA PRESERVATION
   - Never hard-code calculated values
   - Use ExcelJS formula syntax: { formula: '=SUM(A1:A10)' }
   - Test exported Excel files to ensure formulas work

2. CELL REFERENCES
   - Absolute refs for lookups: =lookup!$B$2
   - Relative refs for row calculations: =D5*E5
   - Mixed refs for columns: =$E5

3. AUTO-CALCULATIONS (Must be formulas, not hard-coded)
   - SA Effort: =ROUNDUP(SUM(planning)*0.10, 0)
   - PM Effort: =ROUNDUP(SUM(all)*0.05, 0)
   - BA Effort: =ROUNDUP(SUM(planning)*0.05, 0)
   - Testing: =ROUNDUP(dev_hours*test_percentage, 0)
   - Contingency: =ROUNDUP(total*0.10, 0)

4. VLOOKUP SYNTAX
   - =VLOOKUP(search_key, range, index, FALSE)
   - Example: =VLOOKUP(A3, AIML_cost!$A:$D, 4, 0)

5. SHEET REFERENCES
   - Cross-sheet: lookup!B2
   - Same sheet: B2
   - Range: $A$1:$D$100

6. ROUNDING
   - Always ROUNDUP for hours (no partial hours)
   - Keep currency as decimal

7. EDITABLE vs FORMULA CELLS
   - Base hours (column D): Editable
   - Costs (column F): Formula-protected
   - Lookup values: Editable
   - Calculated totals: Formula-protected
```

## 🎯 Testing Checklist

Share this checklist with Claude Code for validation:

```
TESTING CHECKLIST:

Excel Generation:
[ ] All sheets created: AIML_cost, AIML_COST_SUMMARY, lookup, unit_cost, Resource Loading
[ ] Column headers present and formatted
[ ] All formulas preserved (not calculated values)
[ ] VLOOKUP references work across sheets
[ ] SUM formulas calculate correctly
[ ] ROUNDUP functions work properly
[ ] Currency formatting applied to cost columns
[ ] Percentage formatting applied to lookup percentages

Formula Accuracy:
[ ] Planning total = sum of planning tasks
[ ] SA effort = planning total × 0.10
[ ] PM effort = all tasks × 0.05
[ ] BA effort = planning total × 0.05
[ ] Dev unit testing = dev hours × 0.20
[ ] QA testing = dev hours × 0.25
[ ] Integration testing = dev hours × 0.20
[ ] Contingency = total hours × 0.10
[ ] Summary totals match detailed sheet

BRD Generation:
[ ] All required sections present
[ ] Proper heading hierarchy
[ ] Bullet points formatted correctly
[ ] Content properly populated from analysis
[ ] Professional formatting (fonts, spacing)
[ ] Document can be opened in Word

UI Functionality:
[ ] Scope input accepts text and file upload
[ ] Configuration values are editable
[ ] Changes recalculate in real-time
[ ] Cost table displays correctly
[ ] Edits persist during session
[ ] Download buttons work for both files
[ ] Generated files match specifications

Integration:
[ ] Claude API analysis works
[ ] Analysis results populate BRD correctly
[ ] Analysis results drive cost calculations
[ ] Downloads contain accurate data
[ ] Error handling for invalid inputs
[ ] Loading states during generation
```

## 💡 Common Issues & Solutions

### Issue 1: Formulas Not Preserved
```
If formulas become hard-coded values:

Check:
- Using { formula: '=...' } syntax in ExcelJS
- Not using { value: ... } for calculated cells
- workbook.xlsx.writeBuffer() not workbook.csv

Solution example:
❌ cell.value = D5 * E5
✅ cell.value = { formula: 'D5*E5' }
```

### Issue 2: VLOOKUP Not Working
```
If VLOOKUP returns #REF! or #N/A:

Check:
- Sheet name correct: AIML_cost not AIML cost
- Range includes all necessary columns
- Absolute reference: $A:$D not A:D
- Column index is 1-based (not 0-based)

Solution example:
❌ =VLOOKUP(A3, AIML_cost!A:D, 4, 0)
✅ =VLOOKUP(A3, AIML_cost!$A:$D, 4, 0)
```

### Issue 3: Cross-Sheet References Breaking
```
If references to other sheets don't work:

Check:
- Sheet exists before referencing it
- Sheet name has no special characters
- Using ! separator: lookup!B2
- Range format correct

Solution: Create sheets in order:
1. lookup (independent)
2. unit_cost (independent)
3. AIML_cost (references lookup)
4. AIML_COST_SUMMARY (references AIML_cost)
```

### Issue 4: ROUNDUP Not Working
```
If ROUNDUP gives unexpected results:

Check:
- Syntax: =ROUNDUP(number, digits)
- Second parameter is 0 for whole numbers
- Formula not hard-coded

Solution example:
❌ =ROUND(D4*0.10)
✅ =ROUNDUP(D4*0.10, 0)
```

## 📦 Deliverable Checklist

Before considering the project complete:

```
[ ] Web application deployed and accessible
[ ] All three tabs implemented (Scope, Configuration, Results)
[ ] Editable configuration with default values
[ ] Scope analysis via Claude API working
[ ] BRD generation with all sections
[ ] Excel generation with all 5 tabs
[ ] All formulas working in exported Excel
[ ] Download functionality for both files
[ ] Responsive UI design
[ ] Error handling and loading states
[ ] Documentation for end users
[ ] Code documentation for developers
[ ] Unit tests for calculation engine
[ ] Integration tests for document generation
[ ] Sample projects included
[ ] Configuration can be saved/loaded
```

## 🔄 Iterative Development with Claude Code

Recommended conversation flow:

### Round 1: Setup & Core Logic
```
"Let's create the project structure and implement the core calculation 
engine. Focus on accuracy of formulas first, UI can come later."
```

### Round 2: Excel Implementation
```
"Now let's implement complete Excel generation. I'll test the output 
file and report back if formulas aren't working correctly."
```

### Round 3: BRD Implementation
```
"Let's add BRD generation. Use the template structure from the 
documentation."
```

### Round 4: UI Implementation
```
"Now let's build the user interface with the three tabs as specified."
```

### Round 5: Integration
```
"Let's connect everything together and test the complete workflow."
```

### Round 6: Polish & Testing
```
"Let's add error handling, loading states, and polish the UI. Then 
run through the testing checklist."
```

## 📚 Reference Priority

When Claude Code asks questions, direct it to:

1. **For formula logic** → Estimation_Logic_Quick_Reference.md
2. **For code syntax** → Implementation_Code_Examples.md
3. **For overall architecture** → Claude_Code_Project_Estimator_Prompt.md

## 🎓 Tips for Best Results

1. **Be Iterative**: Don't try to build everything at once
2. **Test Frequently**: Download and open Excel files after each change
3. **Verify Formulas**: Open exported Excel and check formula bar
4. **Use Examples**: Point to specific code examples when asking for features
5. **Stay Focused**: Complete one phase before moving to next
6. **Document Changes**: Keep track of any deviations from specs

## 🚦 Go-Live Readiness

Your app is ready when:
- [ ] Can paste scope and get accurate estimation in <30 seconds
- [ ] Downloaded Excel has working formulas (not hard-coded values)
- [ ] Downloaded BRD has all sections properly populated
- [ ] Can edit configuration and see results update
- [ ] Can modify cost table and download reflects changes
- [ ] All formulas match the reference documentation
- [ ] UI is intuitive and professional

---

## Example First Prompt to Claude Code

```
Hi Claude Code! I need to build a Project Estimator web application. 
I have detailed specifications across three documents.

The app needs to:
1. Accept project scope description as input
2. Use your API to analyze the scope and extract requirements
3. Generate two outputs:
   a) Business Requirements Document (Word .docx)
   b) Cost Estimation Spreadsheet (Excel .xlsx) with 5 tabs and working formulas

The most critical aspect is maintaining formula integrity in the Excel export. 
All calculations must be formulas, not hard-coded values, and cross-sheet 
references must work.

I'll provide you with:
- Complete system specification
- Detailed formula reference with examples
- Working code snippets for Excel/Word generation

Tech stack:
- Next.js + React
- ExcelJS for Excel generation
- docx library for Word generation
- Handsontable for editable spreadsheet UI

Let's start by setting up the project structure and implementing the core 
calculation engine. Should I share the specifications now?
```

---

**You're now ready to start building with Claude Code!** 🚀
