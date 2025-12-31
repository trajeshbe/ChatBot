# Taxonomy Classification - User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Using the Web Interface](#using-the-web-interface)
6. [Understanding Results](#understanding-results)
7. [Customizing Taxonomies](#customizing-taxonomies)
8. [Advanced Usage](#advanced-usage)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Introduction

### What is Taxonomy Classification?

Taxonomy Classification is an AI-powered tool that automatically categorizes text content (articles, documents, news) into predefined taxonomies. Using OpenAI's GPT-4o-mini model, it analyzes your content and provides:

- Multiple relevant classifications
- Relevancy scores for each classification
- Hierarchical categorization (taxonomy type, category, sub-category)
- Top 5 most relevant matches

### Who Should Use This Tool?

- **Content Managers**: Organize and tag articles automatically
- **News Organizations**: Categorize news articles for better discovery
- **Digital Libraries**: Classify documents and publications
- **Marketing Teams**: Tag content for audience targeting
- **Researchers**: Categorize academic papers and research articles
- **Agriculture Industry**: Classify farming and agribusiness content

### Key Benefits

- **Time Savings**: Automated classification vs. manual tagging
- **Consistency**: Standardized classifications across content
- **Accuracy**: AI-powered relevancy scoring
- **Flexibility**: Easy to customize taxonomies
- **Scalability**: Process individual articles or batches

---

## Getting Started

### Prerequisites

Before you begin, ensure you have:

1. **Python 3.8 or higher** installed on your system
2. **OpenAI API key** (get one from [OpenAI Platform](https://platform.openai.com/))
3. **Basic familiarity** with command line/terminal
4. **Internet connection** for API access

### Quick Start (5 Minutes)

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up API Key**
   Create a `.env` file with your OpenAI API key:
   ```
   API_KEY=sk-your-api-key-here
   ```

3. **Run the Application**
   ```bash
   streamlit run taxonomy.py
   ```

4. **Access the Interface**
   Open your browser to: http://localhost:8501

5. **Try It Out**
   - Paste an article into the text area
   - Click "Submit"
   - View your classifications!

---

## Installation

### Step 1: Download the Code

Navigate to the taxonomy_classification directory:
```bash
cd /path/to/taxonomy_classification
```

### Step 2: Create Virtual Environment (Recommended)

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- langchain==0.3.10
- langchain-community==0.3.10
- langchain-core==0.3.22
- langchain-openai==0.2.12
- streamlit==1.40.2

### Step 4: Verify Installation

```bash
python -c "import langchain; import streamlit; print('Installation successful!')"
```

You should see: `Installation successful!`

---

## Configuration

### Setting Up Your OpenAI API Key

#### Option 1: Using .env File (Recommended)

1. Create a file named `.env` in the taxonomy_classification directory
2. Add your API key:
   ```
   API_KEY=sk-your-openai-api-key-here
   ```
3. Save the file

**Security Note**: Never commit .env files to version control!

#### Option 2: Using Environment Variables

**On Windows (PowerShell):**
```powershell
$env:API_KEY="sk-your-openai-api-key-here"
```

**On macOS/Linux:**
```bash
export API_KEY="sk-your-openai-api-key-here"
```

#### Getting an OpenAI API Key

1. Visit https://platform.openai.com/
2. Sign up or log in
3. Navigate to API keys section
4. Create a new API key
5. Copy the key (you won't see it again!)
6. Add billing information (required for API usage)

### Choosing Your Taxonomy File

The system includes two taxonomy files:

1. **taxonomies.json** - General purpose taxonomies
   - Topic-based (Technology, Science, Health, etc.)
   - Geographical (by continent, country, region)
   - Event-based, Audience-based, Sentiment-based
   - Industry-specific, Format-based, Time-based

2. **taxonomies_agri.json** - Agricultural focus
   - All general taxonomies PLUS
   - Crops & Produce
   - Livestock & Animal Agriculture
   - Agribusiness & Markets
   - Precision Agriculture & AgTech
   - Sustainability & Environmental Impact

**To switch taxonomy files**, edit line 14 in `taxonomy.py`:
```python
# For general taxonomies (default)
with open("taxonomies.json", "r") as file:
    taxonomy = json.load(file)

# For agricultural taxonomies
with open("taxonomies_agri.json", "r") as file:
    taxonomy = json.load(file)
```

---

## Using the Web Interface

### Starting the Application

1. Open terminal in the taxonomy_classification directory
2. Run the Streamlit app:
   ```bash
   streamlit run taxonomy.py
   ```
3. Wait for the message:
   ```
   You can now view your Streamlit app in your browser.
   Local URL: http://localhost:8501
   Network URL: http://192.168.x.x:8501
   ```
4. Your browser should open automatically, or navigate to http://localhost:8501

### Interface Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Taxonomy Classification                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Please input your article                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │  [Paste your article text here]                    │   │
│  │                                                     │   │
│  │                                                     │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                    [Submit]                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-Step Usage

#### Step 1: Input Your Article

Click in the text area labeled "Please input your article" and paste or type your content.

**Example Article:**
```
Artificial intelligence and machine learning continue to transform
healthcare. Recent developments in deep learning have enabled more
accurate diagnosis of diseases from medical imaging. Researchers at
Stanford University have developed a new AI model that can detect
skin cancer with accuracy comparable to dermatologists. This technology
could make healthcare more accessible in remote areas.
```

#### Step 2: Submit for Classification

Click the **Submit** button below the text area.

#### Step 3: Wait for Processing

You'll see a spinner with the message "Please wait!!!" while the system:
- Sends your article to the AI model
- Analyzes content against all taxonomies
- Calculates relevancy scores
- Returns top 5 classifications

**Typical wait time**: 2-5 seconds

#### Step 4: View Results

Results appear in a table with four columns:

| taxonomy_type | category | sub_category | score |
|---------------|----------|--------------|-------|
| Topic-Based Taxonomies | General Topics | Technology | 9.5 |
| Industry/Domain-Specific Taxonomies | Technology News | AI and Machine Learning | 9.0 |
| Topic-Based Taxonomies | General Topics | Health | 8.5 |
| Industry/Domain-Specific Taxonomies | Health News | Medical Research | 8.0 |
| Format-Based Taxonomies | Breaking News | Breaking News | 7.5 |

### Working with Results

#### Sorting Results

Click on any column header to sort:
- Click once: Sort ascending
- Click twice: Sort descending
- Click three times: Reset to original order

#### Filtering Results

While the interface doesn't have built-in filtering, you can:
1. Use browser's Find function (Ctrl+F / Cmd+F)
2. Export results and filter in Excel/spreadsheet

#### Copying Results

1. Select cells or rows you want to copy
2. Use Ctrl+C (Windows) or Cmd+C (Mac)
3. Paste into your document or spreadsheet

---

## Understanding Results

### Result Columns Explained

#### taxonomy_type
The highest-level category from your taxonomy structure.

**Examples:**
- "Topic-Based Taxonomies"
- "Geographical Taxonomies"
- "Industry/Domain-Specific Taxonomies"
- "Agricultural Taxonomies"

**Usage**: Understand the broad classification domain

#### category
The mid-level category or sub-taxonomy within the taxonomy_type.

**Examples:**
- "General Topics" (under Topic-Based Taxonomies)
- "Technology News" (under Industry/Domain-Specific)
- "Crops & Produce" (under Agricultural Taxonomies)

**Usage**: Narrow down to specific topic areas

#### sub_category
The most specific classification value.

**Examples:**
- "Technology" (under General Topics)
- "AI and Machine Learning" (under Technology News)
- "Corn" (under Grain & Oilseeds)

**Usage**: The actual tag/label for your content

#### score
Relevancy score from 0 to 10 indicating how well the content matches this classification.

**Score Interpretation:**
- **9.0 - 10.0**: Highly relevant, core topic of the article
- **7.0 - 8.9**: Very relevant, significant topic coverage
- **5.0 - 6.9**: Moderately relevant, mentioned or related
- **3.0 - 4.9**: Somewhat relevant, tangentially related
- **0.0 - 2.9**: Minimally relevant, barely mentioned

### Why Only Top 5?

The system returns the top 5 most relevant classifications because:
- Focuses on the most important categories
- Prevents information overload
- Provides actionable classifications
- Reduces processing time

If you need more classifications, you can modify the prompt (see Advanced Usage).

### Example Classifications

#### Technology Article Example

**Article**: "Apple announces new iPhone with advanced AI-powered camera features and improved battery life."

**Expected Results:**
| taxonomy_type | category | sub_category | score |
|---------------|----------|--------------|-------|
| Topic-Based Taxonomies | General Topics | Technology | 10.0 |
| Industry/Domain-Specific Taxonomies | Technology News | Consumer Electronics | 9.5 |
| Topic-Based Taxonomies | Business | Startups | 7.0 |
| Format-Based Taxonomies | Breaking News | Breaking News | 6.5 |
| Behavioral/Engagement-Based | Trending Topics | Trending Topics | 6.0 |

#### Agricultural Article Example

**Article**: "Corn prices rise amid drought conditions in the Midwest, affecting farmers' crop insurance calculations."

**Expected Results (with taxonomies_agri.json):**
| taxonomy_type | category | sub_category | score |
|---------------|----------|--------------|-------|
| Agricultural Taxonomies | Crops & Produce | Corn | 10.0 |
| Agricultural Taxonomies | Climate Change & Weather | Droughts & Flooding | 9.5 |
| Agricultural Taxonomies | Agribusiness & Markets | Commodity Prices & Futures | 9.0 |
| Agricultural Taxonomies | Farm Management | Risk Management & Crop Insurance | 8.5 |
| Geographical Taxonomies | By Region | Midwest | 7.5 |

---

## Customizing Taxonomies

### Understanding Taxonomy Structure

Taxonomies are defined in JSON files with hierarchical structure:

```json
{
  "TopLevelCategory": {
    "SubCategory": ["Value1", "Value2", "Value3"]
  },
  "DirectCategory": ["DirectValue1", "DirectValue2"]
}
```

### Creating Custom Taxonomies

#### Example: E-commerce Product Taxonomy

Create a new file `taxonomies_ecommerce.json`:

```json
{
  "Product Categories": {
    "Electronics": {
      "Computers": ["Laptops", "Desktops", "Tablets"],
      "Mobile Devices": ["Smartphones", "Feature Phones", "Accessories"],
      "Audio": ["Headphones", "Speakers", "Sound Systems"]
    },
    "Clothing": {
      "Men's Wear": ["Shirts", "Pants", "Jackets"],
      "Women's Wear": ["Dresses", "Tops", "Skirts"],
      "Footwear": ["Sneakers", "Boots", "Sandals"]
    },
    "Home & Garden": {
      "Furniture": ["Sofas", "Tables", "Chairs"],
      "Decor": ["Lighting", "Rugs", "Wall Art"],
      "Garden": ["Plants", "Tools", "Outdoor Furniture"]
    }
  },
  "Price Range": ["Budget", "Mid-Range", "Premium", "Luxury"],
  "Brand Tier": ["Generic", "Popular", "Premium", "Designer"],
  "Target Audience": {
    "By Age": ["Children", "Teens", "Young Adults", "Adults", "Seniors"],
    "By Gender": ["Men", "Women", "Unisex"],
    "By Lifestyle": ["Professionals", "Students", "Athletes", "Homemakers"]
  },
  "Occasion": ["Everyday", "Work", "Formal", "Casual", "Sport", "Party"],
  "Seasonality": ["Spring", "Summer", "Fall", "Winter", "All-Season"]
}
```

#### Example: Legal Document Taxonomy

Create `taxonomies_legal.json`:

```json
{
  "Document Type": {
    "Contracts": ["Employment", "Service Agreement", "NDA", "Lease"],
    "Court Documents": ["Complaint", "Motion", "Brief", "Order"],
    "Corporate": ["Articles of Incorporation", "Bylaws", "Shareholder Agreement"],
    "Intellectual Property": ["Patent", "Trademark", "Copyright"]
  },
  "Practice Area": {
    "Litigation": ["Civil", "Criminal", "Administrative"],
    "Corporate": ["M&A", "Securities", "Governance"],
    "Real Estate": ["Commercial", "Residential", "Land Use"],
    "Intellectual Property": ["Patents", "Trademarks", "Copyrights"]
  },
  "Jurisdiction": {
    "Federal": ["District Court", "Circuit Court", "Supreme Court"],
    "State": ["Trial Court", "Appellate Court", "Supreme Court"]
  },
  "Party Type": ["Individual", "Corporation", "Government", "Non-Profit"],
  "Document Status": ["Draft", "Final", "Executed", "Amended", "Expired"]
}
```

### Applying Custom Taxonomies

1. Save your custom taxonomy JSON file in the taxonomy_classification directory
2. Modify `taxonomy.py` line 14:
   ```python
   with open("taxonomies_ecommerce.json", "r") as file:
       taxonomy = json.load(file)
   ```
3. Restart the Streamlit application

### Taxonomy Design Best Practices

#### 1. Keep It Hierarchical
```json
// Good - Clear hierarchy
{
  "Topic": {
    "Subtopic": ["Specific1", "Specific2"]
  }
}

// Avoid - Flat structure loses context
{
  "Categories": ["Specific1", "Specific2", "Specific3", ...]
}
```

#### 2. Use Descriptive Names
```json
// Good
{
  "Industry/Domain-Specific Taxonomies": {
    "Technology News": ["AI and Machine Learning", "Cybersecurity"]
  }
}

// Avoid
{
  "Cat1": {
    "SubCat": ["Val1", "Val2"]
  }
}
```

#### 3. Balance Breadth and Depth
- **Too broad**: "Technology" (too general)
- **Too specific**: "iPhone 15 Pro Max Camera Features" (too narrow)
- **Just right**: "Consumer Electronics", "Smartphones"

#### 4. Avoid Redundancy
```json
// Good
{
  "Topics": ["Technology", "Science", "Health"]
}

// Avoid - Redundant entries
{
  "Topics": ["Technology", "Tech", "Technology Sector"]
}
```

#### 5. Consider Your Use Case
- **News classification**: Focus on topics, events, geography
- **E-commerce**: Focus on products, prices, audiences
- **Legal**: Focus on document types, practice areas, jurisdictions
- **Healthcare**: Focus on conditions, treatments, specialties

---

## Advanced Usage

### Programmatic Usage (Without Streamlit)

You can use the classification engine in your own Python scripts:

```python
from taxonomy import ContentClassification
import json

# Initialize
classifier = ContentClassification()

# Load taxonomy
with open("taxonomies.json", "r") as f:
    taxonomy = json.load(f)

# Classify
article = "Your article text here..."
results_df = classifier.get_taxonomy_data(article, taxonomy)

# Work with results
print(results_df)
results_df.to_csv("classifications.csv", index=False)
```

### Batch Processing Multiple Articles

```python
import pandas as pd
from taxonomy import ContentClassification
import json

# Initialize
classifier = ContentClassification()
with open("taxonomies.json", "r") as f:
    taxonomy = json.load(f)

# Read articles from CSV
articles = pd.read_csv("articles.csv")  # Should have 'id' and 'text' columns

# Process each article
all_results = []
for idx, row in articles.iterrows():
    print(f"Processing article {idx + 1}/{len(articles)}...")

    df = classifier.get_taxonomy_data(row['text'], taxonomy)
    df['article_id'] = row['id']
    all_results.append(df)

# Combine results
final_results = pd.concat(all_results, ignore_index=True)
final_results.to_csv("all_classifications.csv", index=False)
print(f"Processed {len(articles)} articles!")
```

### Modifying Number of Results

To get more than 5 classifications, edit the prompt in `taxonomy.py`:

Find this section (around line 40):
```python
Based on the relevancy score, do consider top 5 taxonomies.
```

Change to:
```python
Based on the relevancy score, do consider top 10 taxonomies.
```

Also update line 48:
```python
Note: Please mind that output should contain top 10 taxonomies.
```

### Adjusting Temperature for Variety

The system uses temperature=0 for deterministic results. To add variety:

In `taxonomy.py`, around line 30:
```python
self.llm_model = init_chat_model(
    "gpt-4o-mini",
    model_provider="openai",
    temperature=0.3,  # Changed from 0
    api_key=self.api_key
)
```

**Temperature guide:**
- **0.0**: Deterministic, same results every time
- **0.1-0.3**: Slight variety, mostly consistent
- **0.4-0.7**: Moderate variety, balanced
- **0.8-1.0**: High variety, creative

### Filtering by Score Threshold

```python
# Get results
results_df = classifier.get_taxonomy_data(article, taxonomy)

# Filter only high-confidence results
high_confidence = results_df[results_df['score'] >= 7.0]
print(high_confidence)
```

### Exporting Results in Different Formats

```python
results_df = classifier.get_taxonomy_data(article, taxonomy)

# CSV
results_df.to_csv("results.csv", index=False)

# Excel
results_df.to_excel("results.xlsx", index=False)

# JSON
results_df.to_json("results.json", orient="records")

# HTML
results_df.to_html("results.html", index=False)
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "API_KEY not found in environment"

**Cause**: The .env file doesn't exist or doesn't contain the API key

**Solution:**
1. Create a `.env` file in the taxonomy_classification directory
2. Add: `API_KEY=your-key-here`
3. Restart the application

#### Issue: "FileNotFoundError: taxonomies.json"

**Cause**: The taxonomy file is missing or the path is incorrect

**Solution:**
1. Verify `taxonomies.json` exists in the directory
2. Check you're running the script from the correct directory
3. Verify the filename spelling in the code

#### Issue: "AuthenticationError: Invalid API key"

**Cause**: The API key is incorrect or expired

**Solution:**
1. Verify your API key at https://platform.openai.com/
2. Generate a new API key if needed
3. Update your .env file
4. Restart the application

#### Issue: "RateLimitError: Rate limit exceeded"

**Cause**: Too many API requests in a short time

**Solution:**
1. Wait a few minutes before retrying
2. Upgrade your OpenAI plan for higher limits
3. Implement rate limiting in your code
4. Process articles in smaller batches

#### Issue: Streamlit won't start

**Cause**: Port 8501 is already in use

**Solution:**
```bash
# Use a different port
streamlit run taxonomy.py --server.port 8502
```

#### Issue: Slow classification times

**Cause**: Long articles or network latency

**Solution:**
1. Shorten article length for testing
2. Check your internet connection
3. Consider using a faster model (though GPT-4o-mini is already optimized)
4. Implement caching for repeated classifications

#### Issue: Results don't make sense

**Cause**: Taxonomy doesn't match content type

**Solution:**
1. Verify you're using the correct taxonomy file
2. Create a custom taxonomy for your domain
3. Review and refine taxonomy categories
4. Provide more context in articles

### Debug Mode

To see detailed error messages, run with verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Best Practices

### Article Preparation

#### Do's:
- Provide complete sentences and paragraphs
- Include relevant context
- Use clear, descriptive language
- Keep articles focused on specific topics
- Include 100-1000 words for best results

#### Don'ts:
- Submit single words or phrases
- Include excessive formatting or code
- Submit unrelated concatenated texts
- Use articles in languages other than English (unless taxonomy supports it)

### Taxonomy Design

#### Do's:
- Align taxonomies with your use case
- Test with sample articles before finalizing
- Keep categories mutually exclusive where possible
- Use 3-7 main categories (not too few, not too many)
- Document your taxonomy structure

#### Don'ts:
- Create too many nested levels (max 3-4)
- Use ambiguous category names
- Overlap categories significantly
- Change taxonomies frequently in production

### Performance Optimization

#### For Single Classifications:
- Use default settings (temperature=0)
- Keep articles under 2000 words
- Cache results for repeated articles

#### For Batch Processing:
- Process in chunks of 10-20 articles
- Implement retry logic for failures
- Save intermediate results
- Monitor API usage and costs

### Cost Management

OpenAI API charges per token. To minimize costs:

1. **Shorten prompts**: Remove unnecessary instructions
2. **Limit article length**: Truncate very long articles
3. **Use caching**: Don't re-classify identical content
4. **Monitor usage**: Check your OpenAI dashboard regularly
5. **Set budgets**: Configure spending limits in OpenAI account

**Estimated costs** (as of 2025):
- GPT-4o-mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- Average article (500 words): ~$0.001 per classification
- 1000 articles: ~$1.00

### Security Best Practices

1. **Never commit API keys**: Use .env files and .gitignore
2. **Rotate keys regularly**: Generate new keys periodically
3. **Limit key permissions**: Use project-specific keys
4. **Monitor usage**: Watch for unauthorized access
5. **Sanitize inputs**: Validate article content before processing

### Quality Assurance

#### Testing New Taxonomies:
1. Create a test set of 10-20 representative articles
2. Classify with your new taxonomy
3. Review results for accuracy
4. Refine categories based on results
5. Repeat until satisfied

#### Monitoring Production Use:
1. Randomly sample classifications for review
2. Track classification consistency
3. Collect user feedback
4. Update taxonomies based on patterns
5. Document changes and reasons

---

## Getting Help

### Resources

1. **LangChain Documentation**: https://python.langchain.com/
2. **OpenAI API Documentation**: https://platform.openai.com/docs
3. **Streamlit Documentation**: https://docs.streamlit.io/

### Support Channels

- Review the project documentation
- Check the troubleshooting section
- Examine error messages carefully
- Test with simple examples first

### Providing Feedback

When reporting issues, include:
1. What you were trying to do
2. What happened instead
3. Error messages (if any)
4. Sample article (if relevant)
5. Taxonomy file used
6. Python version and OS

---

## Appendix

### Sample Articles for Testing

#### Technology Article
```
Quantum computing breakthrough: Scientists at IBM have developed a new
quantum processor with 433 qubits, marking a significant milestone in
quantum computing development. This advancement could accelerate drug
discovery, optimize financial modeling, and solve complex optimization
problems that are currently intractable for classical computers.
```

#### Health Article
```
A new study published in The Lancet reveals that regular exercise can
reduce the risk of cardiovascular disease by up to 30%. Researchers
followed 50,000 participants over 10 years, finding that just 150
minutes of moderate activity per week significantly improved heart
health outcomes and reduced mortality rates.
```

#### Agricultural Article
```
Precision agriculture technologies are transforming modern farming.
GPS-guided tractors, soil sensors, and drone imagery enable farmers
to optimize fertilizer application, reduce water usage, and increase
crop yields. Early adopters report 15-20% cost savings and improved
environmental sustainability.
```

### Keyboard Shortcuts

**In Streamlit interface:**
- `Ctrl/Cmd + Enter`: Submit form
- `Ctrl/Cmd + F`: Find in page
- `Ctrl/Cmd + R`: Refresh page

---

This user guide should help you get started with the Taxonomy Classification system. For technical details, see the Technical Architecture document. For API details, see the API Reference.
