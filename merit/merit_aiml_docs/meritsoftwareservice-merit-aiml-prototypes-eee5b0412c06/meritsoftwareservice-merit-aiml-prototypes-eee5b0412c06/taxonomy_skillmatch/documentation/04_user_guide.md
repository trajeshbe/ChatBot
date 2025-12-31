# User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Getting Started](#getting-started)
5. [Using the Web Interface](#using-the-web-interface)
6. [Using the Python API](#using-the-python-api)
7. [Preparing Input Files](#preparing-input-files)
8. [Understanding Results](#understanding-results)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)
11. [FAQ](#faq)

---

## Introduction

Welcome to the Taxonomy Skillmatch User Guide. This guide will help you use the system to classify resumes against hierarchical taxonomies and generate relevancy scores.

### What is Taxonomy Skillmatch?

Taxonomy Skillmatch is an AI-powered tool that:
- Analyzes resume content
- Matches skills against predefined job taxonomies
- Calculates relevancy scores
- Identifies the top 5 most suitable career paths

### Who Should Use This Guide?

- HR professionals and recruiters
- Career counselors
- Talent acquisition specialists
- Developers integrating the system
- Anyone needing automated resume classification

---

## Prerequisites

### System Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: Version 3.8 or higher
- **Internet Connection**: Required for OpenAI API access
- **RAM**: Minimum 4GB recommended
- **Storage**: At least 500MB free space

### Required Accounts

- **OpenAI Account**: For API access (requires valid API key)

### Technical Knowledge

- Basic file management skills
- Understanding of resume/CV formats
- Familiarity with JSON format (for taxonomy creation)

---

## Installation

### Step 1: Clone or Download the Project

Navigate to the project directory:

```bash
cd /path/to/taxonomy_skillmatch
```

### Step 2: Create a Virtual Environment (Recommended)

**On Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages**:
- langchain==0.3.10
- langchain-community==0.3.10
- langchain-core==0.3.22
- langchain-openai==0.2.12
- streamlit==1.40.2

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
touch .env  # On macOS/Linux
# Or create manually on Windows
```

Add your OpenAI API key:

```
API_KEY=sk-your-openai-api-key-here
```

**Getting an OpenAI API Key**:
1. Visit https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy and paste into `.env` file

### Step 5: Verify Configuration

Ensure `config.yaml` exists with:

```yaml
taxonomy:
  taxonomy_log_file: "log.txt"
```

### Step 6: Verify Installation

Run a quick test:

```bash
python -c "import streamlit, langchain, pandas; print('Installation successful!')"
```

---

## Getting Started

### Quick Start Guide

1. **Prepare Your Files**:
   - Resume file (`.txt` format)
   - Taxonomy file (`.json` format)

2. **Launch the Application**:
   ```bash
   streamlit run taxonomy.py
   ```

3. **Access the Web Interface**:
   - Browser opens automatically to `http://localhost:8501`
   - If not, manually navigate to the URL

4. **Upload Files and Submit**:
   - Upload your resume TXT file
   - Upload your taxonomy JSON file
   - Click "Submit"

5. **Review Results**:
   - View top match
   - Download CSV report
   - Analyze detailed scores

---

## Using the Web Interface

### Launching the Application

```bash
streamlit run taxonomy.py
```

**Expected Output**:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

### Interface Overview

```
┌─────────────────────────────────────────────┐
│         Taxonomy Skillmatch                 │
├─────────────────────────────────────────────┤
│                                             │
│  📄 Upload a CV File                        │
│  ┌───────────────────────────────────────┐ │
│  │ [Browse files...]                      │ │
│  └───────────────────────────────────────┘ │
│  Accepted format: TXT                       │
│                                             │
│  📊 Upload a Taxonomy File                  │
│  ┌───────────────────────────────────────┐ │
│  │ [Browse files...]                      │ │
│  └───────────────────────────────────────┘ │
│  Accepted format: JSON                      │
│                                             │
│  ┌───────────┐                             │
│  │  Submit   │                             │
│  └───────────┘                             │
└─────────────────────────────────────────────┘
```

### Step-by-Step Usage

#### Step 1: Upload Resume File

1. Click on "Upload a CV File" browse button
2. Navigate to your resume file
3. Select a `.txt` file
4. File name appears when selected

**Supported Format**: `.txt` (plain text)

**File Size**: No explicit limit, but larger files take longer to process

#### Step 2: Upload Taxonomy File

1. Click on "Upload a Taxonomy File" browse button
2. Navigate to your taxonomy file
3. Select a `.json` file
4. File name appears when selected

**Supported Format**: `.json`

#### Step 3: Submit for Processing

1. Ensure both files are uploaded
2. Click "Submit" button
3. Processing spinner appears: "Please wait!!!"
4. Wait for processing to complete (typically 10-30 seconds)

#### Step 4: View Results

Once processing completes, three sections appear:

**1. Download Button**:
```
┌─────────────┐
│  Download   │
└─────────────┘
```
- Click to download results as CSV
- Filename: `output.csv`

**2. Top Match Display**:
```
Most Relevant Taxonomy - Software Development > Web Development > Front-End Developer > React Developer
```
- Shows the highest scoring classification
- Displays full hierarchy path

**3. Results Table**:
```
| Industry              | Career Area         | Occupation Group     | Occupation          | score |
|----------------------|---------------------|---------------------|---------------------|-------|
| Software Development | Web Development     | Front-End Developer | React Developer     | 85.5  |
| Software Development | App Development     | Full Stack Developer| Front-End Specialist| 78.2  |
| ...                  | ...                 | ...                 | ...                 | ...   |
```

### Understanding the Interface

#### Visual Indicators

- **Spinner**: "Please wait!!!" - Processing in progress
- **Warning**: "Please try again..." - Error occurred
- **Markdown**: Bold text for top match highlight

#### Session Persistence

- Results persist during browser session
- Refresh page to clear and start over
- Submit new files to overwrite previous results

#### Download Options

**CSV Download**:
- Click "Download" button
- File saves to default downloads folder
- Contains all columns: Industry, Career Area, Occupation Group, Occupation, score
- No index column included
- Headers included

---

## Using the Python API

### Basic Usage

```python
from taxonomy import ContentClassification
import json

# Initialize the classifier
classifier = ContentClassification()

# Load resume
with open("path/to/resume.txt", "r", encoding="utf-8") as f:
    resume_content = f.read()

# Load taxonomy
with open("path/to/taxonomy.json", "r") as f:
    taxonomy_structure = json.load(f)

# Get results as DataFrame
results_df = classifier.get_taxonomy_data(resume_content, taxonomy_structure)

# Display results
print(results_df)
```

### Advanced Usage

#### Getting Raw JSON Response

```python
# Get raw dictionary response
response = classifier.get_response(resume_content, taxonomy_structure)

# Access results
for result in response['results']:
    print(f"Industry: {result['industry']}")
    print(f"Domain: {result['domain']}")
    print(f"Group: {result['group']}")
    print(f"Sub-Group: {result['sub_group']}")
    print(f"Score: {result['scores']}%")
    print("---")
```

#### Custom Processing

```python
# Get DataFrame
df = classifier.get_taxonomy_data(resume_content, taxonomy_structure)

# Filter by score threshold
high_matches = df[df['score'] >= 70]

# Get top 3 matches
top_3 = df.head(3)

# Sort by different column
df_sorted = df.sort_values(by='Industry')

# Export to different formats
df.to_excel("results.xlsx", index=False)
df.to_json("results.json", orient="records")
```

#### Batch Processing

```python
import os
import glob

classifier = ContentClassification()

# Load taxonomy once
with open("taxonomy.json", "r") as f:
    taxonomy = json.load(f)

# Process multiple resumes
results = {}
for resume_file in glob.glob("resumes/*.txt"):
    with open(resume_file, "r", encoding="utf-8") as f:
        resume = f.read()

    candidate_name = os.path.basename(resume_file).replace(".txt", "")
    results[candidate_name] = classifier.get_taxonomy_data(resume, taxonomy)

# Combine all results
import pandas as pd
combined = pd.DataFrame()
for name, df in results.items():
    df['Candidate'] = name
    combined = pd.concat([combined, df], ignore_index=True)

combined.to_csv("all_results.csv", index=False)
```

---

## Preparing Input Files

### Resume Files (TXT Format)

#### Guidelines

1. **Format**: Plain text (`.txt`)
2. **Encoding**: UTF-8
3. **Content**: Include all relevant professional information
4. **Length**: No strict limit, but be comprehensive

#### Recommended Resume Structure

```
[NAME]
[PROFESSIONAL TITLE]

PROFESSIONAL SUMMARY
[Brief overview of experience and expertise]

WORK EXPERIENCE
[Job Title] at [Company] ([Dates])
- [Responsibility/Achievement]
- [Responsibility/Achievement]

[Repeat for each position]

SKILLS
Technical Skills:
- [Skill category]: [Skill 1], [Skill 2], [Skill 3]
- [Skill category]: [Skill 1], [Skill 2]

EDUCATION
[Degree] in [Field] - [University] ([Year])

CERTIFICATIONS
- [Certification Name] ([Year])
```

#### Example Resume

```
John Doe
Senior React Developer

PROFESSIONAL SUMMARY
Experienced front-end developer with 5+ years of expertise in building scalable web applications using React, TypeScript, and modern JavaScript frameworks. Proven track record of delivering high-quality user interfaces and leading development teams.

WORK EXPERIENCE
Senior Front-End Developer at Tech Corp (2020-Present)
- Led development of React-based dashboard application serving 10,000+ users
- Implemented Redux state management architecture
- Mentored junior developers in React best practices
- Integrated TypeScript for type-safe code

Front-End Developer at StartupXYZ (2018-2020)
- Built responsive web applications using React and Material-UI
- Collaborated with UX designers to implement pixel-perfect designs
- Optimized application performance, reducing load time by 40%

SKILLS
Technical Skills:
- Frontend: React.js, Redux, TypeScript, JavaScript (ES6+), HTML5, CSS3
- Tools: Git, Webpack, npm, Jest, React Testing Library
- Other: RESTful APIs, Responsive Design, Agile/Scrum

EDUCATION
Bachelor of Science in Computer Science - State University (2018)

CERTIFICATIONS
- AWS Certified Developer Associate (2021)
- React Professional Certification (2020)
```

#### Tips for Better Results

1. **Be Comprehensive**: Include all relevant skills and experiences
2. **Use Standard Terms**: Use industry-standard terminology
3. **Quantify Achievements**: Include metrics and numbers when possible
4. **Update Regularly**: Keep resume current with latest skills
5. **Avoid Special Characters**: Stick to plain text formatting

### Taxonomy Files (JSON Format)

#### Structure Requirements

**Hierarchy Levels**:
1. **Level 1**: Industry (top level)
2. **Level 2**: Domain (career area)
3. **Level 3**: Group (occupation group)
4. **Level 4**: Sub-Group (specific job role with skills array)

#### JSON Schema

```json
{
  "Industry_Name": {
    "Domain_Name": {
      "Group_Name": {
        "SubGroup_Name": [
          "skill1",
          "skill2",
          "skill3"
        ]
      }
    }
  }
}
```

#### Complete Example

```json
{
  "Software Development": {
    "Web Development": {
      "Front-End Developer": {
        "React Developer": [
          "React.js",
          "Redux",
          "TypeScript",
          "JavaScript",
          "HTML5",
          "CSS3",
          "Git",
          "Webpack",
          "npm",
          "Jest"
        ],
        "Vue.js Developer": [
          "Vue.js",
          "Vuex",
          "JavaScript",
          "HTML5",
          "CSS3",
          "Git"
        ]
      },
      "Back-End Developer": {
        "Node.js Developer": [
          "Node.js",
          "Express.js",
          "MongoDB",
          "PostgreSQL",
          "REST API",
          "JavaScript",
          "Git"
        ]
      }
    },
    "Mobile Development": {
      "iOS Developer": {
        "Swift Developer": [
          "Swift",
          "SwiftUI",
          "UIKit",
          "Xcode",
          "iOS SDK",
          "Git"
        ]
      },
      "Android Developer": {
        "Kotlin Developer": [
          "Kotlin",
          "Android SDK",
          "Jetpack Compose",
          "Android Studio",
          "Git"
        ]
      }
    },
    "DevOps and Cloud Engineering": {
      "DevOps Engineering": {
        "CI/CD Specialist": [
          "Jenkins",
          "GitLab CI",
          "Docker",
          "Kubernetes",
          "Git",
          "Linux",
          "Bash"
        ]
      },
      "Cloud Engineering": {
        "AWS Engineer": [
          "AWS",
          "EC2",
          "S3",
          "Lambda",
          "CloudFormation",
          "Terraform"
        ]
      }
    }
  },
  "Data Science": {
    "Machine Learning": {
      "ML Engineer": {
        "Computer Vision Engineer": [
          "Python",
          "TensorFlow",
          "PyTorch",
          "OpenCV",
          "NumPy",
          "Pandas",
          "Scikit-learn"
        ],
        "NLP Engineer": [
          "Python",
          "NLTK",
          "SpaCy",
          "Transformers",
          "TensorFlow",
          "PyTorch"
        ]
      }
    },
    "Data Engineering": {
      "Data Engineer": {
        "ETL Developer": [
          "SQL",
          "Python",
          "Apache Spark",
          "Airflow",
          "Kafka",
          "Hadoop"
        ]
      }
    }
  }
}
```

#### Taxonomy Creation Best Practices

1. **Comprehensive Skill Lists**: Include all relevant skills for each role
2. **Consistent Naming**: Use standard industry terminology
3. **Logical Hierarchy**: Ensure parent-child relationships make sense
4. **Skill Specificity**: Be specific but not overly granular
5. **Regular Updates**: Keep taxonomy current with industry trends
6. **Balanced Coverage**: Ensure adequate representation across industries

#### Common Taxonomy Patterns

**Example Paths**:
- `Software Development > Web Development > Front-End Developer > React Developer`
- `Software Development > Application Development > Full Stack Developer > Front-End Specialist`
- `Software Development > DevOps and Cloud Engineering > DevOps Engineering > CI/CD Specialist`
- `Data Science > Machine Learning > ML Engineer > Computer Vision Engineer`

#### Validation Checklist

Before using your taxonomy:

- [ ] Valid JSON syntax (use JSON validator)
- [ ] Four-level hierarchy maintained
- [ ] All sub-groups have skill arrays
- [ ] No empty arrays
- [ ] Consistent formatting
- [ ] No duplicate entries
- [ ] Meaningful industry/domain/group/subgroup names

---

## Understanding Results

### Result Structure

Each result contains:

| Field | Description | Example |
|-------|-------------|---------|
| **Industry** | Top-level classification | "Software Development" |
| **Career Area** | Domain within industry | "Web Development" |
| **Occupation Group** | General job category | "Front-End Developer" |
| **Occupation** | Specific job role | "React Developer" |
| **score** | Relevancy percentage | 85.5 |

### Score Interpretation

**Score Ranges**:

- **90-100%**: Excellent match - Candidate highly qualified
- **75-89%**: Good match - Candidate well-suited
- **60-74%**: Moderate match - Candidate has relevant skills
- **45-59%**: Partial match - Some overlap exists
- **Below 45%**: Low match - Limited alignment

**Note**: Scores are relative and based on LLM assessment

### Example Results

```
| Industry              | Career Area         | Occupation Group     | Occupation           | score |
|----------------------|---------------------|---------------------|---------------------|-------|
| Software Development | Web Development     | Front-End Developer | React Developer     | 85.5  |
| Software Development | App Development     | Full Stack Developer| Front-End Specialist| 78.2  |
| Software Development | DevOps Engineering  | DevOps Engineering  | CI/CD Specialist    | 62.8  |
| Data Science         | Machine Learning    | ML Engineer         | NLP Engineer        | 45.3  |
| Design               | UX Design           | UI/UX Designer      | Web Designer        | 38.7  |
```

**Interpretation**:

1. **Top Match (85.5%)**: Strong React development skills evident
2. **Second Match (78.2%)**: Full-stack capabilities with front-end focus
3. **Third Match (62.8%)**: Some DevOps knowledge present
4. **Fourth Match (45.3%)**: Limited ML experience
5. **Fifth Match (38.7%)**: Minimal design background

### Top Match Display

**Format**:
```
Most Relevant Taxonomy - Software Development > Web Development > Front-End Developer > React Developer
```

**Reading the Path**:
- Industry: Software Development
- Career Area: Web Development
- Occupation Group: Front-End Developer
- Specific Role: React Developer

**Use Cases**:
- Quick candidate classification
- Resume screening shortcut
- Job recommendation
- Skills gap identification

### CSV Export Format

**Columns**: Industry, Career Area, Occupation Group, Occupation, score

**Example CSV**:
```csv
Industry,Career Area,Occupation Group,Occupation,score
Software Development,Web Development,Front-End Developer,React Developer,85.5
Software Development,App Development,Full Stack Developer,Front-End Specialist,78.2
Software Development,DevOps Engineering,DevOps Engineering,CI/CD Specialist,62.8
Data Science,Machine Learning,ML Engineer,NLP Engineer,45.3
Design,UX Design,UI/UX Designer,Web Designer,38.7
```

### Using Results for Decision Making

#### Recruitment Scenario

**Goal**: Fill React Developer position

**Analysis**:
1. Top score of 85.5% indicates strong candidate
2. Career area aligns perfectly (Web Development)
3. Occupation match is exact (React Developer)
4. **Decision**: Advance to interview

#### Career Guidance Scenario

**Goal**: Recommend career paths for candidate

**Analysis**:
1. Top 2 scores in Software Development (85.5%, 78.2%)
2. Strong front-end focus evident
3. Moderate DevOps knowledge (62.8%)
4. **Recommendation**: Front-End Developer career path with DevOps upskilling

#### Skills Gap Analysis

**Goal**: Identify training needs

**Analysis**:
1. High score in React (85.5%) - maintain
2. Good full-stack score (78.2%) - strengthen back-end
3. Lower ML score (45.3%) - opportunity for expansion
4. **Action**: Recommend ML fundamentals course

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "File missing: config file is not available in the path"

**Cause**: `config.yaml` not found

**Solution**:
1. Verify `config.yaml` exists in project directory
2. Check file name spelling (case-sensitive)
3. Create file with:
   ```yaml
   taxonomy:
     taxonomy_log_file: "log.txt"
   ```

#### Issue: "No API key found"

**Cause**: OpenAI API key not configured

**Solution**:
1. Create `.env` file in project root
2. Add line: `API_KEY=sk-your-key-here`
3. Replace with actual OpenAI API key
4. Restart application

#### Issue: "Please try again..." warning appears

**Cause**: Processing error occurred

**Solution**:
1. Check `log.txt` for detailed error
2. Verify resume file is valid TXT format
3. Verify taxonomy file is valid JSON
4. Ensure API key is valid and has credits
5. Check internet connection

#### Issue: Application won't start

**Cause**: Missing dependencies or Python version issue

**Solution**:
```bash
# Verify Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install -r requirements.txt

# Try running again
streamlit run taxonomy.py
```

#### Issue: Processing takes too long

**Cause**: Large resume or taxonomy, API latency

**Solution**:
1. Wait patiently (can take 30-60 seconds for large files)
2. Simplify resume if overly verbose
3. Reduce taxonomy size if massive
4. Check OpenAI API status page
5. Verify internet connection speed

#### Issue: Results don't make sense

**Cause**: Resume quality, taxonomy mismatch, or LLM interpretation

**Solution**:
1. Ensure resume has clear skills listed
2. Verify taxonomy includes relevant roles
3. Check that resume language matches taxonomy terms
4. Try rephrasing resume with more explicit skills
5. Review taxonomy for completeness

#### Issue: CSV download doesn't work

**Cause**: Browser settings or no results yet

**Solution**:
1. Ensure results are displayed before downloading
2. Check browser download settings
3. Try different browser
4. Check browser console for errors
5. Verify sufficient disk space

#### Issue: "Invalid JSON" error

**Cause**: Malformed taxonomy file

**Solution**:
1. Validate JSON at https://jsonlint.com
2. Check for:
   - Missing commas
   - Unclosed brackets
   - Quote mismatches
   - Trailing commas (not allowed in JSON)
3. Use JSON editor with validation

### Checking Logs

**Log File**: `log.txt` (created automatically)

**Location**: Same directory as `taxonomy.py`

**Reading Logs**:
```bash
# View entire log
cat log.txt

# View recent entries (Linux/Mac)
tail -n 20 log.txt

# View in real-time (Linux/Mac)
tail -f log.txt
```

**Log Entry Format**:
```
2025-12-20 10:30:45" ERROR: <exception_type> | <exception_message> | line <line_number> | <file_path> "
```

**Common Log Errors**:

1. **Authentication Error**: Invalid API key
2. **JSON Parse Error**: Malformed taxonomy
3. **File Not Found**: Missing input files
4. **Rate Limit Error**: API quota exceeded
5. **Network Error**: Connection issues

---

## Best Practices

### Resume Preparation

1. **Use Standard Formatting**: Avoid complex formatting
2. **List Skills Explicitly**: Don't rely on context alone
3. **Use Keywords**: Match taxonomy terminology
4. **Be Comprehensive**: Include all relevant experience
5. **Keep Updated**: Reflect current skills

### Taxonomy Design

1. **Start Broad**: Cover major industries first
2. **Add Depth Gradually**: Expand domains and roles over time
3. **Validate Regularly**: Test with real resumes
4. **Collaborate**: Get input from subject matter experts
5. **Version Control**: Track taxonomy changes

### Workflow Optimization

1. **Batch Processing**: Process multiple resumes in one session
2. **Reuse Taxonomies**: Use same taxonomy for consistency
3. **Save Results**: Export and archive CSV files
4. **Regular Updates**: Keep taxonomies current
5. **Quality Control**: Spot-check results periodically

### Performance Tips

1. **Optimize Resume Length**: Remove irrelevant content
2. **Streamline Taxonomy**: Focus on relevant paths
3. **Use Consistent Terms**: Reduce ambiguity
4. **Monitor API Usage**: Track costs and quotas
5. **Cache Results**: Store for reference

### Security Practices

1. **Protect API Keys**: Never commit to version control
2. **Sanitize Resumes**: Remove personal identifiers if needed
3. **Secure Access**: Limit who can use the system
4. **Regular Audits**: Review logs for anomalies
5. **Backup Data**: Save important taxonomies and results

---

## FAQ

### General Questions

**Q: What file formats are supported for resumes?**
A: Currently, only plain text (`.txt`) format is supported. Convert PDF/DOCX files to TXT before uploading.

**Q: How many resumes can I process?**
A: No hard limit, but each resume incurs OpenAI API costs. Process based on your API quota and budget.

**Q: How long does processing take?**
A: Typically 10-30 seconds per resume, depending on length and taxonomy size.

**Q: Can I use this offline?**
A: No, an internet connection is required for OpenAI API access.

**Q: Is my data stored?**
A: No, resume data is not persistently stored. Results exist only in the current session.

### Technical Questions

**Q: Can I change the LLM model?**
A: Yes, modify the `init_chat_model` parameters in `taxonomy.py`:
```python
self.llm_model = init_chat_model(
    "gpt-4",  # Change model here
    model_provider="openai",
    temperature=0,
    api_key=self.api_key
)
```

**Q: Can I customize the number of results?**
A: Yes, modify the prompt template to request a different number (currently set to 5).

**Q: How do I integrate this into my own application?**
A: Import the `ContentClassification` class and use the Python API (see "Using the Python API" section).

**Q: Can I add more taxonomy levels?**
A: The current structure supports 4 levels. Adding more requires modifying the Pydantic models and prompt template.

**Q: How are scores calculated?**
A: Scores are generated by the LLM based on skill matching. The exact algorithm is internal to the model.

### Troubleshooting Questions

**Q: Why do I get different results for the same resume?**
A: With temperature=0, results should be consistent. Variations may occur if taxonomy or resume changes.

**Q: What if taxonomy doesn't include my industry?**
A: Add your industry to the taxonomy JSON file following the 4-level structure.

**Q: Can I process non-English resumes?**
A: The system is optimized for English but may work with other languages. Ensure taxonomy matches the resume language.

**Q: What's the maximum file size?**
A: No explicit limit, but very large files may hit API token limits or time out.

**Q: How do I update dependencies?**
A: Run `pip install --upgrade -r requirements.txt`, but test thoroughly after updates.

### Cost and Usage Questions

**Q: How much does it cost to use?**
A: Costs depend on OpenAI API pricing for GPT-4o-mini. Check OpenAI's current pricing page.

**Q: Can I use a free API key?**
A: Yes, if you have free credits from OpenAI. Monitor usage to avoid exceeding limits.

**Q: How do I monitor API usage?**
A: Check your OpenAI dashboard for usage statistics and costs.

**Q: Are there rate limits?**
A: Yes, OpenAI enforces rate limits. See OpenAI documentation for current limits.

---

## Additional Resources

### External Documentation

- [LangChain Documentation](https://python.langchain.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

### Useful Tools

- **JSON Validators**: https://jsonlint.com/
- **TXT Converters**: Online PDF to TXT converters
- **Taxonomy Builders**: JSON editors with schema support

### Support

For additional support:
1. Check project documentation
2. Review log files for errors
3. Consult LangChain/Streamlit communities
4. Contact development team

---

**Last Updated**: December 2025
**Version**: 1.0 (Prototype)
