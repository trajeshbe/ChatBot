# Relation Extractor Prototype - User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Using the Application](#using-the-application)
4. [Understanding Output](#understanding-output)
5. [Examples and Use Cases](#examples-and-use-cases)
6. [Best Practices](#best-practices)
7. [Limitations and Considerations](#limitations-and-considerations)
8. [Frequently Asked Questions](#frequently-asked-questions)

## Introduction

The Relation Extractor is designed to automatically identify and extract relationships from text. This guide will help you effectively use the application to extract meaningful relationships from various types of content.

### What is Relationship Extraction?

Relationship extraction is the task of identifying semantic relationships between entities in text. For example, in the sentence "John works at Microsoft," the relationship is:
- **Source**: John
- **Relation**: works at
- **Target**: Microsoft

## Getting Started

### Launching the Application

1. Open your terminal or command prompt
2. Navigate to the relation_extractor directory
3. Activate your virtual environment
4. Run the command:
   ```bash
   streamlit run app.py
   ```
5. The application will open in your default browser at `http://localhost:8501`

### Interface Overview

The application interface consists of:

1. **Title Bar**: "Relation Extraction using LLM"
2. **Input Area**: A text area where you enter or paste your text
3. **Submit Button**: Triggers the relationship extraction process
4. **Output Area**: Displays the extracted relationships in JSON format

## Using the Application

### Step-by-Step Process

#### Step 1: Prepare Your Text

Prepare the text from which you want to extract relationships. The text can be:
- A single sentence
- Multiple sentences
- Paragraphs from documents
- Excerpts from articles or reports
- Any natural language text

#### Step 2: Enter Text

1. Click on the text area labeled "Input Text"
2. Type or paste your text into the area
3. The text area supports multiple lines and can handle substantial text

#### Step 3: Submit for Processing

1. Click the submit button at the bottom of the form
2. A "Please wait" spinner will appear while processing
3. Processing time depends on text length and LLM API response time

#### Step 4: Review Results

Once processing completes:
1. The heading "Extracted Output" will appear
2. Relationships are displayed in structured JSON format
3. Review the source, relation, target, type, nature, and confidence scores

### Input Guidelines

#### Optimal Input Length

- **Minimum**: At least one complete sentence
- **Optimal**: 1-5 paragraphs (100-500 words)
- **Maximum**: Limited by LLM context window (typically 4000+ tokens)

#### Text Quality

For best results:
- Use complete sentences with proper grammar
- Include clear subject-verb-object structures
- Avoid excessive jargon without context
- Ensure entities are clearly named

#### Supported Content Types

The application can process:
- **Narrative Text**: Stories, news articles, biographies
- **Technical Content**: Research papers, technical documentation
- **Business Documents**: Reports, emails, meeting notes
- **Academic Text**: Essays, abstracts, literature reviews
- **Social Content**: Social media posts, reviews, comments

## Understanding Output

### Output Schema Structure

The output follows a hierarchical JSON structure:

```json
{
  "relationships": [
    {
      "relationship_name": {
        "type": "relationship_type",
        "nature": "relationship_nature",
        "relationships": [
          {
            "relation_instance": {
              "source": "entity_1",
              "relation": "relationship_verb",
              "target": "entity_2",
              "score": 0.95
            }
          }
        ]
      }
    }
  ]
}
```

### Field Descriptions

#### Top-Level Fields

- **relationships**: Array containing all identified relationship groups

#### Relationship Group Fields

- **type**: The category or type of relationship
  - Examples: "employment", "location", "ownership", "family"

- **nature**: The qualitative characteristic of the relationship
  - Examples: "professional", "personal", "hierarchical", "spatial"

#### Individual Relationship Fields

- **source**: The originating entity in the relationship
  - The subject or actor in the relationship

- **relation**: The connecting verb or relationship description
  - Describes how source and target are related

- **target**: The destination entity in the relationship
  - The object or recipient in the relationship

- **score**: Confidence score from 0.0 to 1.0
  - Higher scores indicate greater confidence
  - 0.0 = no confidence, 1.0 = maximum confidence
  - Typical range: 0.7-0.95 for clear relationships

### Interpreting Confidence Scores

| Score Range | Interpretation | Action |
|-------------|----------------|--------|
| 0.9 - 1.0 | Very High Confidence | Generally reliable |
| 0.8 - 0.89 | High Confidence | Likely accurate |
| 0.7 - 0.79 | Moderate Confidence | Review for accuracy |
| 0.6 - 0.69 | Low Confidence | Verify manually |
| < 0.6 | Very Low Confidence | May be incorrect |

## Examples and Use Cases

### Example 1: Simple Biographical Text

**Input:**
```
Albert Einstein was born in Ulm, Germany. He worked at the Swiss Patent Office
before becoming a professor at the University of Zurich. Einstein developed the
theory of relativity and won the Nobel Prize in Physics in 1921.
```

**Expected Output Structure:**
```json
{
  "relationships": [
    {
      "birth_location": {
        "type": "biographical",
        "nature": "spatial",
        "relationships": [
          {
            "birth": {
              "source": "Albert Einstein",
              "relation": "was born in",
              "target": "Ulm, Germany",
              "score": 0.95
            }
          }
        ]
      }
    },
    {
      "employment": {
        "type": "professional",
        "nature": "employment",
        "relationships": [
          {
            "job_1": {
              "source": "Albert Einstein",
              "relation": "worked at",
              "target": "Swiss Patent Office",
              "score": 0.92
            }
          },
          {
            "job_2": {
              "source": "Albert Einstein",
              "relation": "professor at",
              "target": "University of Zurich",
              "score": 0.93
            }
          }
        ]
      }
    },
    {
      "achievement": {
        "type": "recognition",
        "nature": "award",
        "relationships": [
          {
            "nobel": {
              "source": "Albert Einstein",
              "relation": "won",
              "target": "Nobel Prize in Physics",
              "score": 0.96
            }
          }
        ]
      }
    }
  ]
}
```

### Example 2: Business Context

**Input:**
```
Microsoft acquired LinkedIn for $26.2 billion in 2016. The deal was led by
CEO Satya Nadella and approved by the board of directors. LinkedIn operates
as a subsidiary of Microsoft.
```

**Key Relationships to Extract:**
- Microsoft → acquired → LinkedIn
- Satya Nadella → led → acquisition
- Board of directors → approved → deal
- LinkedIn → operates as → subsidiary of Microsoft

### Example 3: Academic/Research Text

**Input:**
```
The study was conducted at Harvard Medical School in collaboration with
MIT researchers. Dr. Sarah Johnson led the research team. The findings
were published in Nature Medicine and funded by the National Institutes
of Health.
```

**Key Relationships to Extract:**
- Study → conducted at → Harvard Medical School
- Harvard Medical School → collaboration with → MIT
- Dr. Sarah Johnson → led → research team
- Findings → published in → Nature Medicine
- Research → funded by → National Institutes of Health

### Example 4: Technical Documentation

**Input:**
```
The authentication service depends on the database layer. The API gateway
routes requests to the authentication service. Redis cache stores session
data and is accessed by the authentication service.
```

**Key Relationships to Extract:**
- Authentication service → depends on → database layer
- API gateway → routes to → authentication service
- Redis cache → stores → session data
- Authentication service → accesses → Redis cache

### Example 5: News Article

**Input:**
```
Apple announced its new iPhone 15 at an event in Cupertino. Tim Cook,
Apple's CEO, presented the device to thousands of attendees. The phone
features a camera system developed by Sony and will be manufactured by
Foxconn in China.
```

**Key Relationships to Extract:**
- Apple → announced → iPhone 15
- Event → held in → Cupertino
- Tim Cook → is CEO of → Apple
- Tim Cook → presented → iPhone 15
- Camera system → developed by → Sony
- iPhone 15 → manufactured by → Foxconn
- Manufacturing → located in → China

## Best Practices

### 1. Input Preparation

**DO:**
- Provide context-rich text
- Use complete sentences
- Include proper nouns and specific entities
- Keep text focused on a single topic or domain

**DON'T:**
- Submit extremely long documents without segmentation
- Use text with excessive abbreviations without explanation
- Mix multiple unrelated topics in one submission
- Include formatting artifacts or special characters

### 2. Iterative Refinement

If results are not satisfactory:

1. **Simplify the Text**: Break down complex sentences
2. **Add Context**: Provide more background information
3. **Clarify Entities**: Ensure entity names are clear and unambiguous
4. **Adjust Length**: Try shorter or longer text segments
5. **Resubmit**: The LLM may produce different results on retry

### 3. Validation and Verification

Always validate extracted relationships:

1. **Check Accuracy**: Verify relationships against source text
2. **Review Scores**: Pay attention to confidence scores
3. **Cross-Reference**: Compare with domain knowledge
4. **Document Issues**: Note any errors for pattern analysis

### 4. Optimal Use Cases

The tool performs best for:

- **Well-Structured Text**: Clear subject-verb-object patterns
- **Factual Content**: Objective statements about entities
- **Named Entities**: Specific people, places, organizations
- **Explicit Relationships**: Clearly stated connections

### 5. Handling Errors

If you see "Please try again...":

1. Check your internet connection
2. Verify API key is valid and has credits
3. Try simplifying the input text
4. Wait a moment and resubmit
5. Check logs for detailed error information

## Limitations and Considerations

### Known Limitations

1. **Implicit Relationships**: May miss relationships not explicitly stated
2. **Complex Dependencies**: Difficulty with multi-hop relationships
3. **Ambiguity**: May struggle with ambiguous pronouns or references
4. **Domain Specificity**: Performance varies by domain
5. **Language**: Optimized for English text

### Performance Factors

Output quality depends on:

- **Text Quality**: Grammar, structure, clarity
- **Entity Clarity**: How well entities are defined
- **Relationship Explicitness**: How clearly relationships are stated
- **Context**: Amount of surrounding information
- **LLM Capabilities**: Underlying model's knowledge and reasoning

### Privacy and Security

Important considerations:

- **Data Transmission**: Text is sent to OpenAI's API
- **Data Storage**: Check OpenAI's data retention policies
- **Sensitive Information**: Avoid submitting confidential data
- **Compliance**: Ensure usage complies with organizational policies

## Frequently Asked Questions

### Q1: How many relationships can the tool extract from one text?

**A**: There's no fixed limit. The tool will extract all identifiable relationships, but very long texts may be limited by the LLM's context window.

### Q2: Can I process multiple documents at once?

**A**: Currently, the interface supports one text input at a time. For batch processing, you would need to integrate the core logic into a custom script.

### Q3: What languages are supported?

**A**: The tool is optimized for English. Other languages may work but with varying accuracy depending on the LLM's training.

### Q4: How accurate are the confidence scores?

**A**: Confidence scores are generated by the LLM and represent relative confidence. They should be used as guidance rather than absolute measures.

### Q5: Can I customize the relationship types extracted?

**A**: The current prototype uses a general-purpose prompt. Customization would require modifying the prompt template in `output_schema.py`.

### Q6: Why do I sometimes get different results for the same text?

**A**: With temperature set to 0, results should be consistent. However, slight variations can occur due to LLM behavior. Temperature > 0 introduces randomness.

### Q7: How long does processing take?

**A**: Typically 2-10 seconds depending on text length and API response time. Longer texts may take up to 30 seconds.

### Q8: Can I export the results?

**A**: Currently, results are displayed in the interface. You can copy the JSON output manually. Export features would require custom development.

### Q9: What should I do if the output format is incorrect?

**A**: This may indicate the LLM didn't follow the schema. Check the logs, try simplifying the input, or adjust the temperature setting in config.yaml.

### Q10: Is there a cost for using this tool?

**A**: The tool requires an OpenAI API key, which has associated costs based on usage. Monitor your OpenAI account for billing details.

## Getting Help

If you encounter issues:

1. Review the [Setup Guide](2_Setup_Guide.md) for configuration help
2. Check the [API Reference](4_API_Reference.md) for technical details
3. Examine log files in the `logs/` directory
4. Review LangSmith traces if enabled
5. Contact the development team for support

## Next Steps

- Explore the [Architecture & Design](5_Architecture_Design.md) document to understand the system internals
- Review the [API Reference](4_API_Reference.md) for integration possibilities
- Experiment with different types of text to understand capabilities

---

**Document Version**: 1.0
**Last Updated**: December 2025
