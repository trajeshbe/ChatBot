# Implementation Code Examples - Project Estimator

## Excel Generation with ExcelJS

### 1. Creating the AIML_cost Sheet with Formulas

```javascript
import ExcelJS from 'exceljs';

async function createAIMLCostSheet(workbook, projectData, lookupRates) {
  const worksheet = workbook.addWorksheet('AIML_cost');
  
  // Headers
  worksheet.mergeCells('A1:G1');
  worksheet.getCell('A1').value = 'A. Customisation and Deployment of Solution - One off Cost';
  worksheet.getCell('A1').font = { bold: true, size: 14 };
  
  // Column headers
  const headers = ['Description', 'hrs_simple', 'hrs_medium', 'hrs', 'Cost per hour', 'total_cost', 'Notes'];
  worksheet.getRow(3).values = headers;
  
  let currentRow = 4;
  
  // Planning Phase Header
  worksheet.getCell(`A${currentRow}`).value = 'Planning - Customising Framework';
  worksheet.getCell(`D${currentRow}`).value = { formula: `SUM(D${currentRow+1}:D${currentRow+5})` };
  worksheet.getCell(`F${currentRow}`).value = { formula: `SUM(F${currentRow+1}:F${currentRow+5})` };
  
  currentRow++;
  
  // Planning Tasks
  const planningTasks = [
    { desc: 'Analysis of Input Sources and Schema Alignment', simple: 8, medium: 16 },
    { desc: 'Assess extraction options and tools', simple: 16, medium: 24 },
    { desc: 'Design retrieval-augmented extraction flow', simple: 16, medium: 32 },
    { desc: 'Analysis of Requirements', simple: 12, medium: 24 },
    { desc: 'Define confidence scoring logic', simple: 8, medium: 24 }
  ];
  
  planningTasks.forEach(task => {
    worksheet.getCell(`A${currentRow}`).value = task.desc;
    worksheet.getCell(`B${currentRow}`).value = task.simple;
    worksheet.getCell(`C${currentRow}`).value = task.medium;
    worksheet.getCell(`D${currentRow}`).value = task.medium; // Default to medium
    worksheet.getCell(`E${currentRow}`).value = { formula: 'lookup!$B$2' };
    worksheet.getCell(`F${currentRow}`).value = { formula: `D${currentRow}*E${currentRow}` };
    currentRow++;
  });
  
  // Project Management Costs Header
  const pmStartRow = currentRow;
  worksheet.getCell(`A${currentRow}`).value = 'Project Mgmt cost - Planning';
  worksheet.getCell(`D${currentRow}`).value = { formula: `SUM(D${currentRow+1}:D${currentRow+3})` };
  worksheet.getCell(`F${currentRow}`).value = { formula: `SUM(F${currentRow+1}:F${currentRow+3})` };
  
  currentRow++;
  
  // Solution Architect
  const planningRangeStart = 5;
  const planningRangeEnd = planningRangeStart + planningTasks.length - 1;
  worksheet.getCell(`A${currentRow}`).value = 'Solution Architect Effort';
  worksheet.getCell(`D${currentRow}`).value = { 
    formula: `ROUNDUP(SUM($D$${planningRangeStart}:$D$${planningRangeEnd})*lookup!I2,0)` 
  };
  worksheet.getCell(`E${currentRow}`).value = 40;
  worksheet.getCell(`F${currentRow}`).value = { formula: `D${currentRow}*E${currentRow}` };
  
  currentRow++;
  
  // PM Effort
  worksheet.getCell(`A${currentRow}`).value = 'PM Effort';
  worksheet.getCell(`D${currentRow}`).value = { 
    formula: `ROUNDUP(SUM($D$${planningRangeStart}:$D$${planningRangeEnd})*lookup!I3,0)` 
  };
  worksheet.getCell(`E${currentRow}`).value = { formula: 'lookup!$B$2' };
  worksheet.getCell(`F${currentRow}`).value = { formula: `D${currentRow}*E${currentRow}` };
  
  currentRow++;
  
  // BA Effort
  worksheet.getCell(`A${currentRow}`).value = 'BA Effort';
  worksheet.getCell(`D${currentRow}`).value = { 
    formula: `ROUNDUP(SUM($D$${planningRangeStart}:$D$${planningRangeEnd})*lookup!I4,0)` 
  };
  worksheet.getCell(`E${currentRow}`).value = { formula: 'lookup!$B$2' };
  worksheet.getCell(`F${currentRow}`).value = { formula: `D${currentRow}*E${currentRow}` };
  
  currentRow++;
  
  // Development Phase
  worksheet.getCell(`A${currentRow}`).value = 'Development - Framework';
  const devStartRow = currentRow;
  worksheet.getCell(`D${currentRow}`).value = { formula: `SUM(D${currentRow+1}:D${currentRow+5})` };
  worksheet.getCell(`F${currentRow}`).value = { formula: `SUM(F${currentRow+1}:F${currentRow+5})` };
  
  currentRow++;
  
  const devTasks = projectData.developmentTasks || [
    { desc: 'Component 1 Development', hours: 40 },
    { desc: 'Component 2 Development', hours: 60 },
    { desc: 'API Development', hours: 40 },
    { desc: 'Database Implementation', hours: 32 },
    { desc: 'Frontend Development', hours: 48 }
  ];
  
  devTasks.forEach(task => {
    worksheet.getCell(`A${currentRow}`).value = task.desc;
    worksheet.getCell(`D${currentRow}`).value = task.hours;
    worksheet.getCell(`E${currentRow}`).value = { formula: 'lookup!$C$2' }; // Dev rate
    worksheet.getCell(`F${currentRow}`).value = { formula: `D${currentRow}*E${currentRow}` };
    currentRow++;
  });
  
  const devEndRow = currentRow - 1;
  
  // Testing Phase
  worksheet.getCell(`A${currentRow}`).value = 'Testing';
  const testStartRow = currentRow;
  worksheet.getCell(`D${currentRow}`).value = { formula: `SUM(D${currentRow+1}:D${currentRow+3})` };
  worksheet.getCell(`F${currentRow}`).value = { formula: `SUM(F${currentRow+1}:F${currentRow+3})` };
  
  currentRow++;
  
  // Unit Testing
  worksheet.getCell(`A${currentRow}`).value = 'Dev Unit Testing';
  worksheet.getCell(`D${currentRow}`).value = { 
    formula: `ROUNDUP(D${devStartRow}*lookup!B9,0)` 
  };
  worksheet.getCell(`E${currentRow}`).value = { formula: 'lookup!$D$2' }; // Test rate
  worksheet.getCell(`F${currentRow}`).value = { formula: `D${currentRow}*E${currentRow}` };
  
  currentRow++;
  
  // QA Testing
  worksheet.getCell(`A${currentRow}`).value = 'QA Testing';
  worksheet.getCell(`D${currentRow}`).value = { 
    formula: `ROUNDUP(D${devStartRow}*lookup!B10,0)` 
  };
  worksheet.getCell(`E${currentRow}`).value = { formula: 'lookup!$D$2' };
  worksheet.getCell(`F${currentRow}`).value = { formula: `D${currentRow}*E${currentRow}` };
  
  currentRow++;
  
  // Integration Testing
  worksheet.getCell(`A${currentRow}`).value = 'Integration Testing';
  worksheet.getCell(`D${currentRow}`).value = { 
    formula: `ROUNDUP(D${devStartRow}*lookup!B11,0)` 
  };
  worksheet.getCell(`E${currentRow}`).value = { formula: 'lookup!$D$2' };
  worksheet.getCell(`F${currentRow}`).value = { formula: `D${currentRow}*E${currentRow}` };
  
  currentRow++;
  
  // PM & Contingency
  worksheet.getCell(`A${currentRow}`).value = 'PM & Contingency';
  worksheet.getCell(`D${currentRow}`).value = { 
    formula: `ROUNDUP((D${planningRangeStart-1}+D${devStartRow}+D${testStartRow})*lookup!I5,0)` 
  };
  worksheet.getCell(`E${currentRow}`).value = { formula: 'lookup!$B$2' };
  worksheet.getCell(`F${currentRow}`).value = { formula: `D${currentRow}*E${currentRow}` };
  
  currentRow++;
  
  // Infrastructure
  worksheet.getCell(`A${currentRow}`).value = 'Total Infra cost for initial phase';
  worksheet.getCell(`F${currentRow}`).value = { formula: 'unit_cost!B1' };
  
  currentRow++;
  
  // Grand Total
  worksheet.getCell(`A${currentRow}`).value = 'Total One-time development Cost';
  worksheet.getCell(`A${currentRow}`).font = { bold: true };
  worksheet.getCell(`F${currentRow}`).value = { 
    formula: `SUM(F${planningRangeStart-1},F${pmStartRow},F${devStartRow},F${testStartRow},F${currentRow-2},F${currentRow-1})` 
  };
  worksheet.getCell(`F${currentRow}`).font = { bold: true };
  
  // Format currency columns
  worksheet.getColumn('F').numFmt = '$#,##0.00';
  worksheet.getColumn('E').numFmt = '$#,##0.00';
  
  return worksheet;
}
```

### 2. Creating the AIML_COST_SUMMARY Sheet

```javascript
async function createCostSummarySheet(workbook) {
  const worksheet = workbook.addWorksheet('AIML_COST_SUMMARY');
  
  // Headers
  worksheet.getRow(1).values = ['Description', 'Hours', 'Cost'];
  worksheet.getRow(1).font = { bold: true };
  
  const summaryItems = [
    'Project Description',
    'Planning - Customising Framework',
    'Development - Framework',
    'Integration Effort',
    'Documentation',
    'Testing',
    'PM & Contingency',
    'Total Infra cost for initial phase',
    'Total One-time development Cost',
    'BAU - Ongoing Recurring Cost - monthly'
  ];
  
  let row = 2;
  summaryItems.forEach(item => {
    worksheet.getCell(`A${row}`).value = item;
    
    if (row > 2 && row < 9) {
      // VLOOKUP for hours
      worksheet.getCell(`B${row}`).value = {
        formula: `VLOOKUP(A${row},AIML_cost!$A:$D,4,0)`
      };
      // VLOOKUP for cost
      worksheet.getCell(`C${row}`).value = {
        formula: `VLOOKUP(A${row},AIML_cost!$A:$F,6,0)`
      };
    } else if (row === 9) {
      // Total
      worksheet.getCell(`C${row}`).value = {
        formula: `SUM(C3:C8)`
      };
      worksheet.getCell(`C${row}`).font = { bold: true };
    } else if (row === 10) {
      // BAU
      worksheet.getCell(`C${row}`).value = {
        formula: `unit_cost!B3`
      };
    }
    
    row++;
  });
  
  // Format
  worksheet.getColumn('B').numFmt = '#,##0';
  worksheet.getColumn('C').numFmt = '$#,##0.00';
  worksheet.getColumn('A').width = 50;
  
  return worksheet;
}
```

### 3. Creating the Lookup Sheet

```javascript
async function createLookupSheet(workbook, config) {
  const worksheet = workbook.addWorksheet('lookup');
  
  // Row 1: Headers
  worksheet.getRow(1).values = ['', 'plan', 'dev', 'testing', '', '', '', 'Role', 'Effort%'];
  
  // Labor costs
  worksheet.getCell('A2').value = 'Labor cost';
  worksheet.getCell('B2').value = config.planningRate || 25;
  worksheet.getCell('C2').value = config.devRate || 30;
  worksheet.getCell('D2').value = config.testingRate || 25;
  
  worksheet.getCell('A3').value = 'UI labor cost';
  worksheet.getCell('C3').value = config.uiDevRate || 22;
  
  // Testing percentages
  worksheet.getCell('A9').value = 'Dev Unit Testing';
  worksheet.getCell('B9').value = 0.20;
  worksheet.getCell('C9').value = 0.20;
  
  worksheet.getCell('A10').value = 'QA Testing';
  worksheet.getCell('B10').value = 0.25;
  worksheet.getCell('C10').value = 0.25;
  
  worksheet.getCell('A11').value = 'Integration Testing';
  worksheet.getCell('B11').value = 0.20;
  worksheet.getCell('C11').value = 0.20;
  
  // Role percentages
  worksheet.getCell('H2').value = 'Solution Architect';
  worksheet.getCell('I2').value = 0.10;
  
  worksheet.getCell('H3').value = 'PM';
  worksheet.getCell('I3').value = 0.05;
  
  worksheet.getCell('H4').value = 'BA';
  worksheet.getCell('I4').value = 0.05;
  
  worksheet.getCell('H5').value = 'Contingency';
  worksheet.getCell('I5').value = 0.10;
  
  // Format percentages
  worksheet.getColumn('I').numFmt = '0.0%';
  
  return worksheet;
}
```

### 4. Creating the unit_cost Sheet

```javascript
async function createUnitCostSheet(workbook, config) {
  const worksheet = workbook.addWorksheet('unit_cost');
  
  const oneTimeCost = config.infraOneTime || 280;
  const monthlyBAU = config.monthlyBAU || 1030;
  
  worksheet.getCell('A1').value = 'One time cost';
  worksheet.getCell('B1').value = oneTimeCost;
  
  worksheet.getCell('A2').value = 'infra';
  worksheet.getCell('B2').value = monthlyBAU;
  
  worksheet.getCell('A3').value = 'BAU per month';
  worksheet.getCell('B3').value = monthlyBAU;
  
  worksheet.getCell('A4').value = 'BAU per year';
  worksheet.getCell('B4').value = { formula: 'B3*12' };
  
  worksheet.getCell('A5').value = 'Total cost';
  worksheet.getCell('B5').value = { formula: 'B1+B4' };
  
  worksheet.getCell('A6').value = '# of entries per year';
  worksheet.getCell('B6').value = config.annualVolume || 12000;
  
  worksheet.getCell('A7').value = 'cost per document';
  worksheet.getCell('B7').value = { formula: 'B5/B6' };
  
  // Format
  worksheet.getColumn('B').numFmt = '#,##0.00';
  
  return worksheet;
}
```

### 5. Creating Resource Loading Sheet

```javascript
async function createResourceLoadingSheet(workbook, projectTimeline) {
  const worksheet = workbook.addWorksheet('Resource Loading');
  
  const weeks = 16;
  
  // Headers
  worksheet.getCell('A3').value = 'Streams';
  for (let i = 1; i <= weeks; i++) {
    worksheet.getCell(3, i + 1).value = `Week-${i}`;
  }
  
  const streams = [
    'Scraper',
    'AI/ML',
    'Frontend',
    'Backend',
    'QA',
    'Proj Mgmt'
  ];
  
  let row = 4;
  streams.forEach(stream => {
    worksheet.getCell(`A${row}`).value = stream;
    
    // Calculate week distribution based on task hours
    // This would pull from AIML_cost calculations
    for (let week = 1; week <= weeks; week++) {
      const hours = calculateWeekHours(stream, week, projectTimeline);
      worksheet.getCell(row, week + 1).value = hours;
    }
    
    row++;
  });
  
  // Total row
  worksheet.getCell(`A${row}`).value = 'Total';
  worksheet.getCell(`A${row}`).font = { bold: true };
  
  for (let week = 1; week <= weeks; week++) {
    const col = week + 1;
    worksheet.getCell(row, col).value = {
      formula: `SUM(${worksheet.getColumn(col).letter}4:${worksheet.getColumn(col).letter}${row-1})`
    };
  }
  
  return worksheet;
}

function calculateWeekHours(stream, week, timeline) {
  // Logic to distribute task hours across weeks
  // Based on AIML_cost task durations
  // This is simplified - actual implementation would be more complex
  
  const streamTasks = timeline[stream] || [];
  let weekHours = 0;
  
  streamTasks.forEach(task => {
    if (week >= task.startWeek && week <= task.endWeek) {
      weekHours += task.hoursPerWeek;
    }
  });
  
  return weekHours;
}
```

### 6. Main Function to Generate Complete Workbook

```javascript
async function generateEstimationWorkbook(projectData, config) {
  const workbook = new ExcelJS.Workbook();
  
  // Create all sheets
  await createLookupSheet(workbook, config);
  await createUnitCostSheet(workbook, config);
  await createAIMLCostSheet(workbook, projectData, config);
  await createCostSummarySheet(workbook);
  await createResourceLoadingSheet(workbook, projectData.timeline);
  
  // Save to buffer
  const buffer = await workbook.xlsx.writeBuffer();
  
  return buffer;
}
```

## BRD Generation with docx

### Creating Business Requirements Document

```javascript
import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } from 'docx';

async function generateBRD(projectData) {
  const doc = new Document({
    sections: [{
      properties: {},
      children: [
        // Title
        new Paragraph({
          text: "Business Requirements Document (BRD)",
          heading: HeadingLevel.HEADING_1,
          alignment: AlignmentType.CENTER,
          spacing: { after: 400 }
        }),
        
        // Project Information
        new Paragraph({
          text: "Project Information",
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 400, after: 200 }
        }),
        new Paragraph({
          children: [
            new TextRun({ text: "Project: ", bold: true }),
            new TextRun(projectData.name)
          ]
        }),
        new Paragraph({
          children: [
            new TextRun({ text: "Version: ", bold: true }),
            new TextRun("1.0")
          ]
        }),
        new Paragraph({
          children: [
            new TextRun({ text: "Date: ", bold: true }),
            new TextRun(new Date().toLocaleDateString())
          ]
        }),
        new Paragraph({
          children: [
            new TextRun({ text: "Prepared by: ", bold: true }),
            new TextRun("Merit – AI & Data Solutions Team")
          ],
          spacing: { after: 400 }
        }),
        
        // Introduction
        new Paragraph({
          text: "Introduction",
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 400, after: 200 }
        }),
        new Paragraph({
          text: projectData.introduction,
          spacing: { after: 200 }
        }),
        
        // Current Challenges
        new Paragraph({
          text: "Current Challenges",
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 400, after: 200 }
        }),
        ...projectData.challenges.map(challenge => 
          new Paragraph({
            text: `• ${challenge}`,
            bullet: { level: 0 }
          })
        ),
        
        // Proposed Solution
        new Paragraph({
          text: "Proposed Solution",
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 400, after: 200 }
        }),
        ...projectData.solutions.map(solution => 
          new Paragraph({
            text: `• ${solution}`,
            bullet: { level: 0 }
          })
        ),
        
        // Goals and Objectives
        new Paragraph({
          text: "Goals and Objectives",
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 400, after: 200 }
        }),
        ...projectData.goals.map((goal, index) => 
          new Paragraph({
            text: `${index + 1}. ${goal}`,
            numbering: {
              reference: "goals-numbering",
              level: 0
            }
          })
        ),
        
        // Scope
        new Paragraph({
          text: "Scope",
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 400, after: 200 }
        }),
        new Paragraph({
          text: "In Scope:",
          bold: true,
          spacing: { after: 100 }
        }),
        ...projectData.inScope.map(item => 
          new Paragraph({
            text: `• ${item}`,
            bullet: { level: 0 }
          })
        ),
        new Paragraph({
          text: "Out of Scope:",
          bold: true,
          spacing: { before: 200, after: 100 }
        }),
        ...projectData.outOfScope.map(item => 
          new Paragraph({
            text: `• ${item}`,
            bullet: { level: 0 }
          })
        ),
        
        // Functional Requirements
        new Paragraph({
          text: "Functional Requirements",
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 400, after: 200 }
        }),
        ...projectData.functionalRequirements.map((fr, index) => [
          new Paragraph({
            text: `FR${index + 1} – ${fr.title}`,
            bold: true,
            spacing: { before: 200, after: 100 }
          }),
          ...fr.items.map(item => 
            new Paragraph({
              text: `• ${item}`,
              bullet: { level: 0 }
            })
          )
        ]).flat()
      ]
    }]
  });
  
  const buffer = await Packer.toBuffer(doc);
  return buffer;
}
```

## Scope Analysis with Claude API

```javascript
async function analyzeProjectScope(scopeText) {
  const prompt = `Analyze the following project scope and extract structured information:

Project Scope:
${scopeText}

Provide a JSON response with:
{
  "projectName": "...",
  "projectType": "AI/ML | Web Application | Mobile App | Data Engineering",
  "complexity": "Simple | Medium | Complex",
  "components": [
    {
      "name": "...",
      "type": "Frontend | Backend | AI/ML | Database | Integration",
      "description": "...",
      "estimatedHours": number
    }
  ],
  "technologies": ["..."],
  "phases": {
    "planning": {
      "tasks": ["..."],
      "estimatedWeeks": number
    },
    "development": {
      "tasks": ["..."],
      "estimatedWeeks": number
    },
    "testing": {
      "tasks": ["..."],
      "estimatedWeeks": number
    }
  },
  "challenges": ["..."],
  "risks": ["..."],
  "brdContent": {
    "introduction": "...",
    "challenges": ["..."],
    "solutions": ["..."],
    "goals": ["..."],
    "inScope": ["..."],
    "outOfScope": ["..."],
    "functionalRequirements": [
      {
        "title": "...",
        "items": ["..."]
      }
    ]
  }
}`;

  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 4000,
      messages: [{
        role: 'user',
        content: prompt
      }]
    })
  });
  
  const data = await response.json();
  const analysisText = data.content[0].text;
  
  // Strip markdown code blocks if present
  const jsonText = analysisText
    .replace(/```json\n?/g, '')
    .replace(/```\n?/g, '')
    .trim();
  
  return JSON.parse(jsonText);
}
```

## Complete Workflow

```javascript
async function generateProjectEstimation(scopeText, config) {
  try {
    // 1. Analyze scope with Claude
    console.log('Analyzing project scope...');
    const analysis = await analyzeProjectScope(scopeText);
    
    // 2. Generate BRD
    console.log('Generating BRD document...');
    const brdBuffer = await generateBRD(analysis.brdContent);
    
    // 3. Generate Cost Estimation
    console.log('Generating cost estimation...');
    const excelBuffer = await generateEstimationWorkbook(analysis, config);
    
    // 4. Return both documents
    return {
      brd: brdBuffer,
      costEstimation: excelBuffer,
      summary: {
        totalHours: calculateTotalHours(analysis),
        totalCost: calculateTotalCost(analysis, config),
        timeline: calculateTimeline(analysis)
      }
    };
  } catch (error) {
    console.error('Error generating estimation:', error);
    throw error;
  }
}

function calculateTotalHours(analysis) {
  return analysis.components.reduce((sum, comp) => sum + comp.estimatedHours, 0);
}

function calculateTotalCost(analysis, config) {
  const hours = calculateTotalHours(analysis);
  const avgRate = (config.planningRate + config.devRate + config.testingRate) / 3;
  const devCost = hours * avgRate;
  const infraCost = config.infraOneTime + (config.monthlyBAU * 12);
  return devCost + infraCost;
}

function calculateTimeline(analysis) {
  return analysis.phases.planning.estimatedWeeks +
         analysis.phases.development.estimatedWeeks +
         analysis.phases.testing.estimatedWeeks;
}
```

---

**These code examples provide a solid foundation for implementing the project estimator in Claude Code.**
