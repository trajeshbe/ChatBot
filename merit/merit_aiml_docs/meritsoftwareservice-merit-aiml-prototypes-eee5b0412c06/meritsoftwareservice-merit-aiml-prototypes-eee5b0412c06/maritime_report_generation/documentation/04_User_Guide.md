# Maritime Report Generation - User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Maritime Casualty Reporting](#maritime-casualty-reporting)
4. [Maritime Report Generation](#maritime-report-generation)
5. [Tips and Best Practices](#tips-and-best-practices)
6. [Troubleshooting](#troubleshooting)
7. [FAQs](#faqs)
8. [Support](#support)

## Introduction

### What is Maritime Report Generation?

The Maritime Report Generation system is an AI-powered tool that helps maritime professionals automate the creation and standardization of maritime casualty reports. The system provides two main capabilities:

1. **Maritime Casualty Reporting**: Extracts structured data from unstructured incident reports
2. **Maritime Report Generation**: Transforms raw incident reports into professionally formatted, standardized reports

### Who Should Use This System?

- Lloyd's Agents and Maritime Correspondents
- Maritime Insurance Adjusters
- Port Authority Personnel
- Ship Owners and Operators
- Maritime Safety Officers
- Classification Society Representatives
- Legal and Compliance Teams

### Benefits

- Reduce report preparation time by 75-85%
- Ensure consistent report formatting
- Automatically extract critical incident data
- Enrich reports with vessel information (IMO, GT)
- Standardize language and terminology
- Generate professional reports in seconds

## Getting Started

### System Requirements

- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection
- No special software installation required

### Accessing the System

The system consists of two separate web applications:

1. **Maritime Casualty Reporting**: For data extraction
   - URL: `http://[server-address]:8501`
   - Run command: `streamlit run maritime_casualty_reporting.py`

2. **Maritime Report Generation**: For report standardization
   - URL: `http://[server-address]:8501`
   - Run command: `streamlit run maritime_report_generation.py`

### User Interface Overview

Both applications feature a clean, intuitive interface:

- **Title Bar**: Shows application name
- **Input Area**: Large text box for entering incident reports
- **Action Button**: Triggers processing
- **Results Area**: Displays extracted data or formatted reports
- **Download Button**: Exports results

## Maritime Casualty Reporting

### Purpose

Extract structured data from unstructured maritime incident reports for analysis, reporting, and system integration.

### Step-by-Step Guide

#### Step 1: Access the Application

1. Open your web browser
2. Navigate to the Maritime Casualty Reporting application
3. You will see the title: "Maritime Casualty Reporting - Intelligent Information Extraction"

#### Step 2: Prepare Your Input

Gather your incident report text. This can be from:
- Email notifications
- Radio messages
- Authority reports
- Coastguard communications
- Vessel operator statements
- Any maritime incident documentation

**Input can be in any format** - the system will extract relevant information.

#### Step 3: Enter Incident Text

1. Click in the text area labeled "Enter Incident text:"
2. Paste or type your incident report
3. The text area accommodates long reports (200+ lines)

**Example Input**:
```
LONDON, 15 Jan -- Following received from Lloyd's Agents,
timed 1430 UTC: General cargo vessel MV PLAYA DE PESMAR UNO
experienced engine failure in position 51.30N 001.25E,
approximately 15 nautical miles southeast of Ramsgate, UK,
at 1200 UTC today. Vessel was en route from Rotterdam to
Antwerp with 24 crew on board. Coastguard dispatched tug
assistance. No injuries reported. No pollution observed.
```

#### Step 4: Extract Data

1. Review your input for completeness
2. Click the **"Extract Data"** button
3. A spinner will appear with message "Please wait..."
4. Processing typically takes 5-15 seconds

#### Step 5: Review Extracted Data

Once processing completes, a structured table appears with extracted information:

| Key | Value |
|-----|-------|
| vessel_name | MV PLAYA DE PESMAR UNO |
| imo_number | - |
| number_of_crew | 24 |
| date_of_incident | 15 Jan |
| reported_time_utc | 1200 UTC |
| nature_of_incident | Engine failure |
| latitude_longitude | 51.30N 001.25E |
| reference_point | 15 nautical miles southeast of Ramsgate, UK |
| severity_of_incident | Moderate |
| total_casualties | 0 |
| pollution_reported | No |
| reported_by | Lloyd's Agents |
| ... | ... |

**What the data includes**:
- **Vessel Information**: Name, IMO, crew count, operator, contact details
- **Incident Details**: Date, time, nature, cause, severity
- **Location**: Coordinates, reference points, distance from shore
- **Casualties**: Numbers and nationalities
- **Environmental**: Pollution, spills, financial impact
- **Reporting**: Source, timestamp, publisher

#### Step 6: Download Results

1. Review the extracted data for accuracy
2. Click the **"Download CSV"** button (📥 icon)
3. Save the file as `extracted_data.csv`
4. The file can be opened in Excel, imported into databases, or used for analysis

#### Step 7: Process Additional Reports

To process another report:
1. Clear the text area or paste new text
2. Click "Extract Data" again
3. Previous results are replaced with new extraction

### Understanding the Output

#### Field Meanings

**Vessel Information Fields**:
- `vessel_name`: Name of the vessel involved
- `imo_number`: International Maritime Organization identification number
- `number_of_crew`: Total persons on board
- `owner_operator`: Company owning or operating the vessel
- `contact_information`: Company contact details

**Incident Detail Fields**:
- `date_of_incident`: When the incident occurred
- `reported_time_utc`: Time reported in UTC
- `nature_of_incident`: Type (Fire, Collision, Grounding, Mechanical Failure, etc.)
- `potential_cause`: Root cause (Human Error, Mechanical, Natural Calamity, etc.)

**Location Fields**:
- `latitude_longitude`: GPS coordinates
- `reference_point`: Descriptive location
- `distance_from_shore`: How far from land
- `port_of_call`: Relevant port
- `severity_of_incident`: Low, Moderate, High, Critical

**Casualty Fields**:
- `total_casualties`: Number of deaths/injuries
- `crew_nationalities`: Countries of crew members

**Environmental Fields**:
- `pollution_reported`: Yes/No
- `oil_spill`: Yes/No
- `hazardous_cargo_spill`: Yes/No
- `estimated_financial_loss`: Scale or amount

**Reporting Fields**:
- `reported_by`: Who reported the incident
- `source_of_report`: Origin of information
- `report_timestamp_utc`: When report was created
- `published_by`: Publishing entity
- `published_on`: Publication date/time

#### Missing Data

If information is not found in the input text, the field will show **"-"**. This is normal and expected for incomplete reports.

## Maritime Report Generation

### Purpose

Transform unedited, informal incident reports into professionally formatted, standardized maritime casualty reports following industry house style guidelines.

### Step-by-Step Guide

#### Step 1: Access the Application

1. Open your web browser
2. Navigate to the Maritime Report Generation application
3. You will see the title: "Maritime Report Generation"

#### Step 2: Prepare Your Unedited Report

Gather your raw incident report that needs formatting. This might include:
- Informal incident descriptions
- Incomplete vessel information
- Non-standard terminology
- Reports missing IMO or gross tonnage data

#### Step 3: Enter Unedited Report

1. Click in the text area labeled "Unedited Report:"
2. Paste or type your raw incident text
3. Don't worry about formatting or completeness

**Example Unedited Input**:
```
The cargo ship PLAYA DE PESMAR UNO from Spain had engine
problems today around noon near Ramsgate. The ship was
going from Rotterdam to Antwerp. They have 24 crew members.
A tugboat is helping them. Nobody got hurt and there's no
oil in the water. The coastguard is keeping watch.
```

#### Step 4: Edit Report

1. Review your input
2. Click the **"Edit Report"** button
3. Processing begins with several steps:
   - Extracting vessel name (3-5 seconds)
   - Searching for IMO number (5-8 seconds)
   - Searching for gross tonnage (5-8 seconds)
   - Generating formatted report (3-5 seconds)
4. Total processing time: 20-30 seconds

#### Step 5: Review Edited Report

Once complete, the professionally formatted report appears:

**Example Edited Output**:
```
MV PLAYA DE PESMAR UNO (SPAIN)

LONDON, 15 January 2024 -- Following received from Lloyd's
Agents, timed 1430 UTC:

General cargo vessel MV PLAYA DE PESMAR UNO (IMO: 9876543,
3,245 gt, built 2015), en route from Rotterdam, Netherlands
to Antwerp, Belgium, with 24 crew on board, reported
experiencing main engine failure in position 51.30N 001.25E,
approximately 15 nautical miles southeast of Ramsgate, UK,
at 1200 UTC, 15 January 2024.

The vessel lost propulsion while transiting the English
Channel. UK Coastguard was notified immediately and dispatched
the tug ANGLIAN SOVEREIGN to provide assistance.

The vessel was towed safely to Ramsgate anchorage where
engineers are conducting repairs. No injuries to crew were
reported. No pollution was observed.

As of 1800 UTC, the vessel remains at anchor awaiting
completion of repairs before resuming passage to Antwerp.
```

**What has changed**:
- Title formatted: VESSEL NAME (FLAG)
- Vessel details enriched: Added IMO 9876543, GT 3,245
- Professional structure: Dateline, summary, actions, status
- Neutral language: "experiencing failure" instead of "had problems"
- Complete information: Times in UTC, full location details
- Proper sign-off: Professional conclusion

#### Step 6: Download Report

1. Review the edited report
2. Click the **"Download Report (TXT)"** button (📄 icon)
3. Save the file as `incident_report.txt`

The downloaded file contains:
```
### User Input Text ###
[Your original unedited report]

### Generated Content ###
[The professionally formatted report]
```

This allows you to keep both versions for reference.

#### Step 7: Process Additional Reports

To edit another report:
1. Clear the text area or paste new text
2. Click "Edit Report" again
3. Previous results are replaced with new formatted report

### Understanding the Editing Process

#### Automatic Enrichment

The system automatically:

1. **Identifies the vessel name** from your text
2. **Searches web databases** for:
   - IMO number (7-digit vessel identification)
   - Gross Tonnage (vessel size in GT)
3. **Adds missing information** to the report in standard format
4. **Applies house style rules** for professional presentation

#### House Style Rules Applied

**Title Formatting**:
- Vessel names in CAPITAL LETTERS
- Flag in brackets: `MV PLAYA DE PESMAR UNO (SPAIN)`

**Report Structure**:
- Dateline (location, date)
- Opening: "Following received from [source], timed [time]:"
- Vessel details: Name, IMO, GT, build year
- Route: "en route from [origin] to [destination]"
- Incident description
- Actions taken
- Current status

**Language Standardization**:
- "experienced engine failure" (not "had engine problems")
- "sustained damage" (not "suffered damage")
- "came in contact with" (not "collided with")
- Eliminates casual language ("around noon" → "at 1200 UTC")

**Information Enhancement**:
- Vague times made precise (if available)
- Locations standardized (coordinates + description)
- Professional terminology throughout

## Tips and Best Practices

### For Best Results

#### Input Preparation

1. **Include as much detail as possible**:
   - Vessel names (including prefixes like MV, MS)
   - Dates and times
   - Locations (coordinates and descriptions)
   - Incident descriptions
   - Actions taken
   - Source information

2. **Don't worry about formatting**:
   - System handles any input format
   - Informal language is fine (it will be standardized)
   - Incomplete information is acceptable

3. **Provide context**:
   - Source of the report
   - When information was received
   - Reporter's organization

#### Maximizing Accuracy

**Maritime Casualty Reporting**:
- More detailed input = more accurate extraction
- Include numerical data explicitly (crew count, coordinates)
- Mention incident types clearly (fire, collision, grounding)
- Specify severity if known

**Maritime Report Generation**:
- Provide vessel name clearly (automatic enrichment depends on it)
- Include any known vessel details (IMO, GT) to improve accuracy
- Mention flag/nationality of vessel
- Describe incident clearly for proper language standardization

### Reviewing Results

#### Data Extraction Review

Always verify extracted data, especially:
- **Dates and times**: Ensure correct interpretation
- **Coordinates**: Check if properly extracted
- **Numerical values**: Verify crew count, casualties
- **Incident type**: Confirm nature of incident is correct

#### Report Generation Review

Check the formatted report for:
- **Vessel identification**: Correct name, IMO, GT
- **Timeline accuracy**: Dates and times properly formatted
- **Location precision**: Coordinates and descriptions match source
- **Completeness**: All important details included
- **Tone**: Professional and neutral throughout

### Working Efficiently

#### Batch Processing

For multiple reports:
1. Process one report at a time
2. Download results after each
3. Keep a folder organized by date or vessel
4. Name downloads descriptively (e.g., `MV_PLAYA_2024_01_15.csv`)

#### Integrating with Workflows

**Data Extraction → Analysis**:
- Export CSV files
- Import into Excel or database
- Use for trend analysis, statistics

**Report Generation → Distribution**:
- Generate TXT files
- Copy formatted report to email
- Submit to reporting authorities
- Archive in document management system

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Please enter text to extract data"

**Cause**: Text area is empty
**Solution**: Paste or type incident text before clicking button

#### Issue: "Please try again" error message

**Causes**:
- Network connectivity issues
- OpenAI API temporarily unavailable
- Malformed input causing processing error

**Solutions**:
1. Check internet connection
2. Wait 10-30 seconds and retry
3. Simplify input (remove special characters)
4. Try with a different incident report
5. Contact system administrator if persistent

#### Issue: Many fields show "-" in extracted data

**Cause**: Information not present in input text
**Solutions**:
- Normal behavior for incomplete reports
- Add more detail to input if available
- Manually supplement missing information after export

#### Issue: No IMO or GT found in generated report

**Causes**:
- Vessel name not recognized
- Vessel not in public databases
- Search engine temporarily unavailable

**Solutions**:
- Verify vessel name spelling
- Try alternative vessel name formats
- Manually add IMO/GT to downloaded report
- System continues without this data (not a failure)

#### Issue: Processing takes very long

**Causes**:
- Normal for Report Generation (20-30 seconds)
- Network latency
- High system load

**Solutions**:
- Wait patiently (avoid clicking multiple times)
- If exceeds 60 seconds, refresh page and retry
- Check internet connection speed

#### Issue: Formatted report has incorrect information

**Causes**:
- Ambiguous input text
- LLM misinterpretation

**Solutions**:
- Review original input for clarity
- Manually correct downloaded report
- Provide more explicit details in input
- Report issue to administrators for improvement

### Error Messages

| Message | Meaning | Action |
|---------|---------|--------|
| "Please enter text to extract data" | Empty input field | Add text before processing |
| "Please try again" | Processing error | Retry after short wait |
| Page not loading | Connection issue | Check URL and network |
| Spinner runs indefinitely | System hang | Refresh page and retry |

### Performance Issues

If the system seems slow:

1. **Check your connection**: Speed test your internet
2. **Browser cache**: Clear cache and reload page
3. **Browser choice**: Try Chrome or Firefox for best performance
4. **System load**: Avoid during peak usage times
5. **Report complexity**: Very long reports (>2000 words) may be slower

## FAQs

### General Questions

**Q: Do I need to install any software?**
A: No, the system runs entirely in your web browser. No installation required.

**Q: Can I use this on mobile devices?**
A: Yes, but desktop/laptop recommended for easier text entry and review.

**Q: Is my data saved or stored?**
A: No, all processing is session-based. Data is not stored after you close the browser.

**Q: Can multiple people use the system simultaneously?**
A: Yes, each user has their own independent session.

### Data Extraction Questions

**Q: What languages are supported?**
A: Currently, the system works best with English-language reports.

**Q: How accurate is the data extraction?**
A: Accuracy is typically 90-95% for well-formatted reports. Always review results.

**Q: Can I edit the extracted data before downloading?**
A: Currently, no in-app editing. Download CSV and edit in Excel if needed.

**Q: What format is the CSV file?**
A: Standard CSV with two columns (Key, Value), UTF-8 encoding.

### Report Generation Questions

**Q: How does the system find IMO numbers?**
A: It searches web databases using the vessel name and parses results using AI.

**Q: What if the wrong IMO is found?**
A: Review the downloaded report and manually correct the IMO number.

**Q: Can I customize the house style?**
A: Not currently - the system follows standard Lloyd's-style formatting.

**Q: How is vessel gross tonnage validated?**
A: The system checks if GT > 200 (typical threshold). Values below may be flagged.

**Q: Can I process reports in other languages?**
A: Currently optimized for English. Other languages may have mixed results.

### Technical Questions

**Q: What AI model is used?**
A: OpenAI GPT-4o-mini-2024-07-18 for all processing.

**Q: How long are reports stored?**
A: Reports are not stored. Session data clears when you close the browser.

**Q: Can I integrate this with other systems?**
A: Currently standalone. API integration is a potential future enhancement.

**Q: Is there a maximum report length?**
A: No strict limit, but reports over 2000 words may process more slowly.

## Support

### Getting Help

If you encounter issues not covered in this guide:

1. **Check Documentation**: Review all sections of this guide
2. **Retry**: Many issues resolve with a simple retry
3. **Contact Administrator**: Reach out to your system administrator
4. **Collect Details**: Note the error message and what you were doing

### Providing Feedback

To report issues or suggest improvements:
- Document the specific problem
- Include example input text (if not sensitive)
- Describe expected vs. actual results
- Note any error messages

### Training and Onboarding

For new users:
- Review this guide thoroughly
- Start with simple, short reports
- Progress to complex reports as you gain confidence
- Practice with historical reports (non-critical)

### Best Practices for Success

1. **Start Simple**: Begin with straightforward reports
2. **Verify Results**: Always review extracted data and formatted reports
3. **Keep Originals**: Save original reports alongside processed versions
4. **Build Familiarity**: Regular use improves efficiency
5. **Share Knowledge**: Train colleagues on effective use

## Appendix: Example Workflows

### Workflow 1: Insurance Claim Processing

1. Receive incident notification email
2. Copy incident text to Maritime Casualty Reporting
3. Extract structured data
4. Download CSV
5. Import to claims processing system
6. Use extracted data to populate claim fields

### Workflow 2: Authority Reporting

1. Receive raw incident report from vessel
2. Copy to Maritime Report Generation
3. System enriches with IMO, GT
4. Review formatted report
5. Download professional report
6. Submit to maritime authority

### Workflow 3: Incident Database Population

1. Collect multiple incident reports
2. Process each through Maritime Casualty Reporting
3. Download all CSV files
4. Merge CSV files
5. Import to incident tracking database
6. Run analytics and generate statistics

### Workflow 4: Lloyd's Agent Reporting

1. Receive incident information from local contacts
2. Draft initial report
3. Run through Maritime Report Generation
4. System applies house style and enriches vessel data
5. Review and make manual adjustments if needed
6. Download and submit to Lloyd's List Intelligence

## Conclusion

The Maritime Report Generation system is a powerful tool for automating and standardizing maritime casualty reporting. By following this guide, you can efficiently process incident reports, extract critical data, and generate professional documentation that meets industry standards.

Remember: The system is designed to assist, not replace, professional judgment. Always review results before using them for official purposes.

For the best experience, practice with sample reports, verify outputs carefully, and integrate the system into your existing workflows gradually.

Happy reporting!
