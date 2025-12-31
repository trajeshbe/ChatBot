# SpendSmart: User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Using Filters](#using-filters)
4. [Semantic Search](#semantic-search)
5. [Exploring Visualizations](#exploring-visualizations)
6. [Knowledge Graph Network](#knowledge-graph-network)
7. [Exporting Data](#exporting-data)
8. [Tips and Best Practices](#tips-and-best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Frequently Asked Questions](#frequently-asked-questions)

## Getting Started

### Accessing SpendSmart

1. **Launch the Application**
   - Navigate to the SpendSmart URL provided by your administrator
   - The application runs on port 5000 or as configured
   - Compatible with modern web browsers (Chrome, Firefox, Safari, Edge)

2. **First-Time Setup**
   - On first load, SpendSmart automatically generates synthetic procurement data
   - Wait 3-5 seconds for data generation and graph construction
   - You'll see a progress spinner: "Generating synthetic procurement data..."

3. **Initial Dashboard**
   - Once loaded, you'll see the main dashboard with:
     - Key metrics at the top (Total Contracts, Total Value, etc.)
     - Semantic search interface
     - Tabbed visualizations
     - Sidebar filters

### Interface Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ SpendSmart - AI-Powered Procurement Intelligence Platform       │
├──────────────┬──────────────────────────────────────────────────┤
│  SIDEBAR     │  MAIN CONTENT AREA                               │
│              │                                                   │
│ Data Mgmt    │  Key Metrics: [Contracts] [Value] [Avg] [...]   │
│ Filters      │                                                   │
│ - Buyer      │  Semantic Search: [___________________] [Search] │
│ - Region     │                                                   │
│ - Framework  │  Tabs:                                           │
│ - Category   │  [Overview] [Supplier] [Trends] [Network] [Data] │
│ - Year       │                                                   │
│              │  [Visualizations and data displays]              │
│ Export       │                                                   │
│              │                                                   │
└──────────────┴──────────────────────────────────────────────────┘
```

## Dashboard Overview

### Key Metrics Bar

At the top of the dashboard, you'll always see five key metrics:

| Metric | Description | Example |
|--------|-------------|---------|
| **Total Contracts** | Number of contracts in current view | 30 |
| **Total Value** | Sum of all contract values | £45.2M |
| **Average Value** | Mean contract value | £1.5M |
| **Unique Suppliers** | Number of distinct suppliers | 27 |
| **Unique Buyers** | Number of distinct buyers | 18 |

**Key Points**:
- Metrics update automatically when you apply filters
- Values are formatted for readability (£1.5M instead of £1,500,000)
- Click metrics for detailed breakdowns (future feature)

### Understanding the Data

**Synthetic Data Fields**:

The generated procurement data includes:

- **Contract_ID**: Unique identifier (e.g., CNT-2024-0001)
- **Buyer_Name**: Government organization (NHS England, Ministry of Defence, etc.)
- **Supplier_Name**: Company providing services (Accenture, Capgemini, etc.)
- **Contract_Title**: Descriptive title of the contract
- **Category**: Type of service (IT Services, Cybersecurity, Legal Services, etc.)
- **CPV_Code**: Common Procurement Vocabulary code
- **Framework**: Government framework if used (G-Cloud 13, DOS6, etc.)
- **Region**: UK region (London, Scotland, Wales, etc.)
- **Contract_Value**: Value in GBP (£)
- **Award_Date**: When contract was awarded
- **Start_Date**: Contract start date
- **End_Date**: Contract end date

## Using Filters

### Accessing Filters

Filters are located in the left sidebar under "Filters" section.

### Available Filters

#### 1. Buyer Filter

**Purpose**: Focus on specific government organizations

**How to Use**:
1. Click the "Buyer" dropdown
2. Select a buyer from the list (or "All" to see everything)
3. Results update automatically

**Example Use Cases**:
- Analyze NHS England's procurement patterns
- Compare Ministry of Defence spending
- Review local council contracts

#### 2. Region Filter

**Purpose**: Analyze procurement by geographic region

**Available Regions**:
- London
- South East
- South West
- East of England
- West Midlands
- East Midlands
- Yorkshire and Humber
- North West
- North East
- Scotland
- Wales
- Northern Ireland

**Example Use Cases**:
- Regional spending analysis
- Identify regional supplier preferences
- Compare London vs. regional procurement

#### 3. Framework Filter

**Purpose**: Analyze framework usage and efficiency

**Available Frameworks**:
- G-Cloud 13
- DOS6 (Digital Outcomes and Specialists 6)
- CCS Technology Products 2
- Crown Hosting Data Centres
- Network Services 2
- Professional Services
- Management Consultancy Framework 4
- Legal Services 3
- Facilities Management
- Construction Works & Associated Services
- (None) - Direct awards outside frameworks

**Example Use Cases**:
- Measure G-Cloud adoption
- Compare framework vs. non-framework contracts
- Identify framework optimization opportunities

#### 4. Category Filter

**Purpose**: Focus on specific types of procurement

**Available Categories** (20 total):
- IT Services
- Cybersecurity
- Software Licensing
- Hardware
- Professional Services
- Legal Services
- Facilities Management
- Construction
- Maintenance
- Consultancy
- Training
- Telecommunications
- Cloud Services
- Data Analytics
- Project Management
- Security Services
- Cleaning Services
- Catering
- Transport
- Energy Management

**Example Use Cases**:
- IT spending analysis
- Cybersecurity investment review
- Professional services comparison

#### 5. Award Year Filter

**Purpose**: Analyze procurement by time period

**How to Use**:
1. Click "Award Year" dropdown
2. Select a year (or "All" for all years)
3. Data filters to contracts awarded in that year

**Example Use Cases**:
- Year-over-year comparison
- Budget year analysis
- Historical trend review

### Filter Combinations

**Filters work together** - you can combine multiple filters for precise analysis.

**Example Combinations**:

1. **NHS IT Spending in London**:
   - Buyer: NHS England
   - Category: IT Services
   - Region: London

2. **2024 G-Cloud Cybersecurity Contracts**:
   - Framework: G-Cloud 13
   - Category: Cybersecurity
   - Award Year: 2024

3. **Ministry of Defence Professional Services**:
   - Buyer: Ministry of Defence
   - Category: Professional Services

### Clearing Filters

To clear a filter:
1. Select "All" from the dropdown
2. OR regenerate data (clears all filters)

## Semantic Search

### What is Semantic Search?

Semantic search lets you ask questions in plain English instead of using filters. The AI understands your intent and finds relevant data.

### How to Use Semantic Search

```
┌─────────────────────────────────────────────────────────────┐
│ Ask a question about procurement data:                      │
│ [Show me NHS cybersecurity contracts ___________________]  │
│                                                              │
│ Or try a sample query: [Select a suggestion ▼]  [🗑️ Clear]  │
└─────────────────────────────────────────────────────────────┘
```

**Steps**:

1. **Enter Your Question**
   - Type your question in plain English
   - Be specific but natural
   - Examples: "Show me NHS cybersecurity contracts", "Top 5 IT suppliers"

2. **Submit the Query**
   - Press Enter or click outside the text box
   - Wait 2-3 seconds for AI processing

3. **Review Results**
   - Query Understanding: Shows how AI interpreted your question
   - Filters Applied: Lists filters extracted from your query
   - Results: Displays matching contracts
   - AI Insights: Generated business insights

### Query Types and Examples

#### Entity-Based Queries

Find contracts related to specific entities.

**Examples**:
- "Show me NHS cybersecurity contracts"
- "Ministry of Defence procurement"
- "Accenture contracts in London"

**What Happens**:
- AI identifies entity (NHS = buyer, Accenture = supplier)
- Applies appropriate filters
- Returns matching contracts

#### Top-N Queries

Get ranked lists of top performers.

**Examples**:
- "Top 5 IT suppliers for government"
- "Highest value contracts in 2024"
- "Top 3 buyers by spending"

**What Happens**:
- AI identifies ranking criteria (value, count, etc.)
- Sorts data appropriately
- Limits results to requested number

#### Trend Queries

Analyze patterns over time.

**Examples**:
- "NHS spending trends"
- "Cybersecurity spending over time"
- "Monthly procurement patterns"

**What Happens**:
- AI identifies temporal analysis request
- Groups data by time periods
- Generates trend visualizations

#### Comparison Queries

Compare different dimensions.

**Examples**:
- "Compare regional spending"
- "Framework efficiency analysis"
- "Small vs large contract values"

**What Happens**:
- AI identifies comparison dimensions
- Calculates metrics for each group
- Presents comparative analysis

#### Framework Queries

Analyze framework usage.

**Examples**:
- "G-Cloud 13 framework usage"
- "Framework adoption by department"
- "Compare framework vs direct procurement"

**What Happens**:
- AI filters by framework
- Calculates utilization metrics
- Provides efficiency insights

### Understanding Query Results

When you submit a query, you'll see:

#### 1. Query Understanding Section

```
🎯 Query Understanding
─────────────────────────────────────────────
Intent: NHS cybersecurity spending analysis
Analysis Type: Overview

Filters Applied:
• Buyer_Name: NHS England
• Category: Cybersecurity
```

This shows how the AI interpreted your question.

#### 2. Results Metrics

```
📊 Results (8 contracts found)
─────────────────────────────────────────────
Contracts: 8
Total Value: £4.2M
Suppliers: 5
Buyers: 1
```

Quick overview of what was found.

#### 3. AI Insights

```
🧠 AI Insights
─────────────────────────────────────────────
• NHS England has invested £4.2M in cybersecurity across 8 contracts,
  with an average value of £525K per contract.

• Supplier concentration is moderate with the top supplier accounting
  for 35% of total spend.

• Spending shows a 23% increase over the past 12 months, aligned with
  national security initiatives.

• Recommendation: Consider consolidating to 3-4 strategic partners to
  leverage volume discounts while maintaining diversity.
```

AI-generated business insights and recommendations.

#### 4. Top Results Table

A table showing the most relevant contracts with key details:
- Buyer Name
- Supplier Name
- Contract Title
- Category
- Contract Value
- Framework
- Award Date

#### 5. Analysis-Specific Visualization

Depending on the analysis type:
- **Supplier Analysis**: Bar chart of top suppliers
- **Comparison**: Pie chart of category distribution
- **Trend**: Line chart of spending over time

### Sample Queries

Click the "Or try a sample query" dropdown to see pre-written examples:

1. "Show me NHS cybersecurity contracts"
2. "Top 5 IT suppliers for government departments"
3. "Ministry of Defence spending trends"
4. "G-Cloud 13 framework usage"
5. "London region procurement patterns"
6. "Highest value contracts in 2024"
7. "Professional services suppliers"
8. "Compare regional spending"
9. "Framework efficiency analysis"
10. "Small vs large contract values"

**Tip**: Start with sample queries to learn the system, then create your own.

### Tips for Effective Queries

✅ **DO**:
- Be specific: "NHS IT contracts" not just "IT"
- Use natural language: "Show me..." or "Find..."
- Specify numbers: "Top 5" or "Last 12 months"
- Mention specific entities: Names of buyers, suppliers, frameworks

❌ **DON'T**:
- Use SQL syntax or technical jargon
- Make queries too vague: "Show everything"
- Use abbreviations AI might not recognize
- Include irrelevant information

## Exploring Visualizations

SpendSmart provides five tabbed visualization sections.

### Tab 1: Overview Dashboard

**Purpose**: High-level procurement overview

**Components**:

1. **Spend Distribution by Category** (Bar Chart)
   - Shows total spending for each category
   - Horizontal bars, sorted by value
   - Hover for exact amounts

2. **Total Spend by Region** (Bar Chart)
   - Regional spending breakdown
   - Identifies high-spend regions
   - Hover for details

3. **Framework Utilization** (Table)
   - Framework usage statistics
   - Columns: Total Value, Contract Count, Unique Suppliers
   - Sorted by total value

**How to Use**:
- Identify highest-spending categories
- Compare regional patterns
- Assess framework adoption

**Example Insights**:
- "IT Services account for 40% of total spend"
- "London region has 3x more contracts than other regions"
- "G-Cloud 13 is the most-used framework"

### Tab 2: Supplier Analysis

**Purpose**: Deep-dive into supplier performance

**Components**:

1. **Top 10 Suppliers by Total Contract Value** (Bar Chart)
   - Ranked supplier list
   - Shows supplier concentration
   - Identify key relationships

2. **Supplier Diversity by Buyer** (Scatter Plot)
   - X-axis: Number of unique suppliers per buyer
   - Y-axis: Total spend per buyer
   - Hover to see buyer names
   - Analyze correlation between diversity and spending

**How to Use**:
- Identify top suppliers for negotiation
- Assess supplier concentration risk
- Compare buyer supplier diversity strategies

**Example Insights**:
- "Top 3 suppliers account for 60% of spending"
- "Buyers with more supplier diversity tend to spend more"
- "Accenture is the top supplier across multiple categories"

### Tab 3: Trend Analysis

**Purpose**: Understand spending patterns over time

**Components**:

1. **Monthly Procurement Spend Trend** (Line Chart)
   - Total spending by month
   - Identify seasonal patterns
   - Spot anomalies or spikes

2. **Spending Trends by Category** (Multi-Line Chart)
   - One line per category
   - Compare category growth rates
   - Color-coded for clarity

**How to Use**:
- Track spending over time
- Identify seasonal patterns
- Validate budget allocation
- Forecast future needs

**Interactions**:
- Hover over points for exact values
- Click legend items to show/hide categories
- Zoom by selecting area (drag mouse)

**Example Insights**:
- "Spending peaks in March and September (fiscal year-end)"
- "Cloud Services spending up 45% year-over-year"
- "Cybersecurity shows steady growth trend"

### Tab 4: Network Graph

**Purpose**: Visualize procurement relationships

**Understanding the Network Graph**:

```
Network Graph Components:

Nodes (Circles):
┌──────────────┬─────────┬────────────────┐
│ Node Type    │ Color   │ Size Based On  │
├──────────────┼─────────┼────────────────┤
│ Buyer        │ Blue    │ Connections    │
│ Supplier     │ Orange  │ Connections    │
│ Contract     │ Green   │ Value          │
│ Category     │ Red     │ Connections    │
│ Framework    │ Purple  │ Connections    │
│ Region       │ Brown   │ Connections    │
└──────────────┴─────────┴────────────────┘

Edges (Lines):
• Buyer → Contract: AWARDED
• Contract → Supplier: DELIVERED_BY
• Contract → Category: CATEGORISED_AS
• Contract → Framework: UNDER_FRAMEWORK
• Buyer → Region: LOCATED_IN
• Supplier → Framework: PARTICIPATES_IN
```

**How to Use**:

1. **Full Network View** (default):
   - Shows all relationships
   - Navigate with mouse (pan and zoom)
   - Hover over nodes for details
   - Click legend to show/hide node types

2. **Focused View** (select a buyer):
   - Filter by specific buyer in sidebar
   - Network shows only that buyer's relationships
   - See buyer-specific metrics
   - Analyze supplier concentration

**Interactions**:
- **Zoom**: Mouse wheel or pinch
- **Pan**: Click and drag background
- **Hover**: See node/edge details
- **Legend**: Click to show/hide node types

**Example Insights**:
- "NHS England works with 12 suppliers across 8 categories"
- "Accenture participates in 5 different frameworks"
- "Ministry of Defence has dense supplier network (high concentration)"

### Tab 5: Data Table

**Purpose**: Detailed, searchable data access

**Features**:

1. **Column Selection**:
   - Checkbox: "Show All Columns"
   - Unchecked: Shows 8 key columns
   - Checked: Shows all 12 columns

2. **Pagination**:
   - Select records per page: 10, 25, 50, 100
   - Navigate pages with number input
   - Shows "Page X of Y"

3. **Summary Statistics**:
   - Displayed below table
   - Shows mean, median, std, min, max for numerical columns
   - Updates with filtered data

**How to Use**:
- Browse detailed contract information
- Verify specific contract details
- Identify contracts meeting specific criteria
- Cross-reference with visualizations

**Key Columns** (default):
- Buyer_Name
- Supplier_Name
- Contract_Title
- Category
- Contract_Value
- Framework
- Region
- Award_Date

**All Columns** (when checked):
- All key columns PLUS:
- Contract_ID
- CPV_Code
- Start_Date
- End_Date

## Knowledge Graph Network

### What is a Knowledge Graph?

A knowledge graph represents data as a network of connected entities. In SpendSmart:

- **Entities**: Buyers, Suppliers, Contracts, Categories, Frameworks, Regions
- **Relationships**: How entities connect (AWARDED, DELIVERED_BY, etc.)

### Reading the Network Graph

**Node Interpretation**:

| Visual Feature | Meaning |
|----------------|---------|
| Node Size | Larger = more valuable or more connected |
| Node Color | Different colors for different entity types |
| Node Position | Closer = more related (algorithmically determined) |

**Edge Interpretation**:

| Visual Feature | Meaning |
|----------------|---------|
| Edge Presence | Relationship exists |
| Edge Thickness | Contract value (thicker = higher value) |

### Use Cases

1. **Supplier Relationship Mapping**:
   - Visualize which suppliers work with which buyers
   - Identify cross-buyer suppliers
   - Assess supplier diversity

2. **Framework Participation**:
   - See which suppliers participate in frameworks
   - Identify framework-heavy buyers
   - Analyze framework coverage

3. **Category Concentration**:
   - Visualize spending across categories
   - Identify specialized vs. diversified suppliers
   - Assess category-buyer relationships

4. **Regional Patterns**:
   - See buyer distribution across regions
   - Identify regional supplier preferences

### Network Statistics

At the bottom of the Network Graph tab:

```
Network Statistics
─────────────────────────────────────
Total Nodes: 156
Total Edges: 289
Network Density: 0.024
```

**Interpreting Statistics**:

- **Total Nodes**: Number of entities in the network
- **Total Edges**: Number of relationships
- **Network Density**:
  - Range: 0.0 to 1.0
  - Low (< 0.1): Sparse network, selective relationships
  - High (> 0.5): Dense network, highly interconnected
  - 0.024 = Relatively sparse, typical for procurement networks

## Exporting Data

### CSV Export

**Steps**:

1. **Apply Filters** (optional):
   - Set desired filters in sidebar
   - Only filtered data will be exported

2. **Click Export Button**:
   - Sidebar → "Export Data" section
   - Click "Download Filtered Data as CSV"

3. **Download File**:
   - Browser downloads CSV file
   - Filename format: `procurement_data_YYYYMMDD_HHMMSS.csv`

**What's Exported**:
- All contracts matching current filters
- All columns (not just displayed ones)
- Raw data (not formatted versions)

**Uses**:
- Import into Excel for custom analysis
- Load into BI tools (Tableau, Power BI)
- Share with stakeholders
- Create custom reports

### Future Export Options

Coming soon:
- PDF reports
- PowerPoint presentations
- Graph data (JSON, GEXF)
- Custom report templates

## Tips and Best Practices

### General Usage Tips

1. **Start Broad, Then Narrow**:
   - Begin with no filters to see full dataset
   - Apply filters incrementally to focus

2. **Use Semantic Search for Complex Queries**:
   - Instead of multiple filters, try natural language
   - Example: "Top 5 NHS IT suppliers in 2024" is easier than 4 filters

3. **Combine Filters and Search**:
   - Apply broad filters first (e.g., Buyer)
   - Use semantic search for specific questions

4. **Leverage Multiple Tabs**:
   - Overview for high-level understanding
   - Supplier Analysis for vendor relationships
   - Trends for temporal patterns
   - Network for relationship mapping
   - Data Table for details

### Analysis Workflows

#### Workflow 1: Buyer Spend Analysis

1. Select buyer from sidebar
2. Review Overview tab metrics
3. Check Supplier Analysis for top vendors
4. Examine Trends for spending patterns
5. Export data for detailed analysis

#### Workflow 2: Category Deep-Dive

1. Select category (e.g., IT Services)
2. Use semantic search: "Top suppliers in IT Services"
3. Review AI insights
4. Check Trend Analysis for category growth
5. Examine Network Graph for supplier relationships

#### Workflow 3: Framework Efficiency

1. Select framework (e.g., G-Cloud 13)
2. Review Overview tab for utilization stats
3. Compare with "All" to see framework vs. non-framework
4. Use semantic search: "G-Cloud 13 efficiency analysis"
5. Check Network Graph for framework participation

#### Workflow 4: Regional Comparison

1. Use semantic search: "Compare regional spending"
2. Review regional breakdown in Overview tab
3. Select each region individually to see details
4. Compare supplier diversity across regions
5. Export data for each region

### Performance Tips

1. **Large Datasets**:
   - Use filters to reduce data volume
   - Apply pagination in Data Table (10-25 records per page)
   - Close unused browser tabs

2. **Slow Search**:
   - OpenAI API calls take 2-5 seconds (normal)
   - Check internet connection if slower
   - Try simpler queries

3. **Graph Rendering**:
   - Large networks (>100 nodes) may take time to render
   - Use focused view (select specific buyer) for better performance
   - Zoom and pan slowly for smooth experience

## Troubleshooting

### Common Issues and Solutions

#### Issue: "No data matches the selected filters"

**Cause**: Filter combination too restrictive

**Solution**:
1. Check filter settings in sidebar
2. Remove one filter at a time
3. Start with broader filters
4. Use "All" to reset filters

#### Issue: "Search error: API timeout"

**Cause**: OpenAI API unavailable or slow

**Solution**:
1. Wait a moment and try again
2. Check internet connection
3. Try a simpler query
4. Use filters instead of semantic search

#### Issue: "Network graph not displaying"

**Cause**: Empty dataset or rendering issue

**Solution**:
1. Check if filters have excluded all data
2. Refresh browser page (F5)
3. Try focused view (select specific buyer)
4. Clear browser cache

#### Issue: "Data Table shows only 10 records"

**Cause**: Pagination setting

**Solution**:
1. Change "Records per page" to 25, 50, or 100
2. Navigate pages using page number input
3. This is normal behavior, not an error

#### Issue: "Visualizations not updating"

**Cause**: Tab not active or rendering delay

**Solution**:
1. Click on the specific tab
2. Wait 1-2 seconds for rendering
3. Try changing a filter to trigger update
4. Refresh browser if persists

### Getting Help

If issues persist:

1. **Refresh the Page**: Often resolves UI glitches
2. **Regenerate Data**: Use sidebar to generate fresh data
3. **Contact Support**: Reach out to your system administrator
4. **Check Browser Compatibility**: Use Chrome, Firefox, Safari, or Edge (latest versions)

## Frequently Asked Questions

### Data Questions

**Q: Is this real procurement data?**
A: No, the demo uses synthetic (generated) data for demonstration purposes. It mimics realistic patterns but doesn't represent actual government contracts.

**Q: Can I upload my own data?**
A: Not in the current version. Future releases will support data import from Contracts Finder API and CSV uploads.

**Q: How many records can SpendSmart handle?**
A: The current version generates 20-50 records. Production versions can handle thousands to millions of records with proper infrastructure.

**Q: Why do I see "None" in Framework column?**
A: Many contracts are awarded outside government frameworks (direct awards). This is realistic and expected.

### Search Questions

**Q: What languages does semantic search support?**
A: Currently English only. Multi-language support is planned.

**Q: How does the AI understand my queries?**
A: SpendSmart uses OpenAI's GPT-4o-mini model, which is trained on vast amounts of text and can understand context, intent, and domain-specific terminology.

**Q: Can I save my queries?**
A: Not yet. Saved queries and dashboards are planned for future releases.

**Q: Why do search results sometimes differ from filters?**
A: Semantic search may interpret queries differently than you intended. Review the "Query Understanding" section to see how it was interpreted.

### Visualization Questions

**Q: What do the colors mean in the network graph?**
A: Each entity type has a color:
- Blue: Buyers
- Orange: Suppliers
- Green: Contracts
- Red: Categories
- Purple: Frameworks
- Brown: Regions

**Q: Why are some nodes bigger than others?**
A: Node size represents importance - either contract value (for contracts) or number of connections (for other nodes).

**Q: Can I export the network graph?**
A: Not in the current version. Graph export (JSON, GEXF) is coming in future releases.

**Q: How do I interpret network density?**
A: Network density ranges from 0 to 1:
- 0.0-0.1: Sparse (selective relationships)
- 0.1-0.3: Moderate
- 0.3-1.0: Dense (highly interconnected)
Most procurement networks are sparse (0.02-0.05).

### Technical Questions

**Q: What browsers are supported?**
A: Modern versions of Chrome, Firefox, Safari, and Edge. Internet Explorer is not supported.

**Q: Why does the page refresh sometimes?**
A: Streamlit (the framework) reruns the app when you interact with controls. This is normal behavior.

**Q: Can I use SpendSmart on mobile?**
A: While it works on mobile browsers, the experience is optimized for desktop/laptop screens (minimum 1024px width recommended).

**Q: How is my data secured?**
A: All data is stored in-memory during your session only. No data is persisted to disk or shared. Synthetic data contains no sensitive information.

### Analysis Questions

**Q: How do I identify savings opportunities?**
A: Look for:
- High supplier concentration (negotiate better rates)
- Low framework utilization (move to frameworks for savings)
- Category spending spikes (investigate and optimize)
- Multiple suppliers for same service (consolidate)

**Q: What's a good supplier diversity ratio?**
A: It depends on context, but generally:
- 5-10 suppliers per £10M spend is balanced
- Too few = concentration risk
- Too many = management overhead
Use the Supplier Diversity scatter plot to assess.

**Q: How do I measure framework efficiency?**
A: Compare:
- Framework vs. non-framework contract values
- Number of contracts per framework
- Supplier participation rates
- Average contract size on framework vs. off-framework

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Tab` | Move to next input field |
| `Shift + Tab` | Move to previous input field |
| `Enter` | Submit semantic search query |
| `F5` | Refresh page / Regenerate data |
| `Ctrl + F` (in table) | Browser find in table |

## Glossary

**Buyer**: Government organization awarding contracts (NHS, MoD, Councils)

**Category**: Type of goods/services procured (IT, Cybersecurity, Legal)

**Contract Value**: Total monetary value of the contract in GBP

**CPV Code**: Common Procurement Vocabulary - standardized classification

**Framework**: Pre-established agreement for specific goods/services (G-Cloud, DOS)

**Knowledge Graph**: Network representation of data showing entity relationships

**Node**: Entity in the graph (buyer, supplier, contract, etc.)

**Edge**: Relationship between nodes (awarded, delivered by, etc.)

**Semantic Search**: AI-powered natural language query capability

**Supplier**: Company or organization delivering goods/services

**Synthetic Data**: Computer-generated data mimicking real patterns

## Conclusion

SpendSmart is designed to make procurement intelligence accessible to everyone, from technical analysts to senior executives. Whether you're using filters for precise analysis or semantic search for quick insights, the platform provides multiple pathways to the answers you need.

**Remember**:
- Start simple and build complexity
- Use semantic search for natural questions
- Leverage visualizations for different perspectives
- Export data for deeper analysis
- Combine features for comprehensive insights

For additional support, training, or feature requests, contact your system administrator or the SpendSmart support team.

**Happy analyzing!**
