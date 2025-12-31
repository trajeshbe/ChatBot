# API Reference - Email Bounce Intelligence

## Overview

This document provides comprehensive API documentation for all classes, methods, and data structures in the Email Bounce Intelligence system. This reference is intended for developers who need to understand, maintain, or extend the codebase.

## Table of Contents

1. [EmailParser Class](#emailparser-class)
2. [DiagnosticExtractor Class](#diagnosticextractor-class)
3. [BounceClassifier Class](#bounceclassifier-class)
4. [Application Functions](#application-functions)
5. [Data Structures](#data-structures)
6. [Constants and Enumerations](#constants-and-enumerations)
7. [Error Handling](#error-handling)
8. [Usage Examples](#usage-examples)

---

## EmailParser Class

**Location**: `email_parser.py`

**Purpose**: Parses raw email content and extracts structured information from bounce notification emails.

### Class Definition

```python
class EmailParser:
    """
    Parses email content and extracts structured information from bounce emails
    """
```

### Constructor

#### `__init__(self)`

Initializes the EmailParser with predefined header patterns.

**Parameters**: None

**Returns**: None

**Example**:
```python
parser = EmailParser()
```

**Attributes Initialized**:
- `header_patterns` (Dict[str, str]): Dictionary of regex patterns for common email headers

### Public Methods

#### `parse_email(email_content: Any) -> Dict[str, Any]`

Main method to parse email content and extract relevant information.

**Parameters**:
- `email_content` (str | bytes | EmailMessage): Raw email content in various formats

**Returns**:
- `Dict[str, Any]`: Dictionary containing parsed email information with the following structure:
  ```python
  {
      "subject": str,
      "from": str,
      "to": str,
      "date": str,
      "message_id": str,
      "return_path": str,
      "auto_submitted": str,
      "x_failed_recipients": str,
      "content_type": str,
      "body": str,
      "headers": Dict[str, str],
      "dsn_info": Dict[str, Any],
      "original_message_info": Dict[str, str],
      # Additional bounce-specific fields
      "smtp_code": Optional[str],
      "enhanced_status_code": Optional[str],
      "failed_recipient": Optional[str],
      ...
  }
  ```

**Raises**:
- No exceptions raised; falls back to raw text parsing on error

**Example**:
```python
parser = EmailParser()
email_text = """From: MAILER-DAEMON@example.com
To: sender@example.com
Subject: Undelivered Mail
...
"""
parsed = parser.parse_email(email_text)
print(parsed["subject"])  # "Undelivered Mail"
print(parsed["smtp_code"])  # "550"
```

**Behavior**:
1. Accepts string, bytes, or EmailMessage objects
2. Attempts standard email parsing
3. Falls back to raw text parsing if standard parsing fails
4. Extracts DSN information if available
5. Extracts original message information
6. Performs additional bounce-specific extraction from body

#### `extract_recipient_email(parsed_email: Dict[str, Any]) -> Optional[str]`

Extracts the recipient email address from parsed email data.

**Parameters**:
- `parsed_email` (Dict[str, Any]): Previously parsed email data

**Returns**:
- `Optional[str]`: Recipient email address or None if not found

**Example**:
```python
recipient = parser.extract_recipient_email(parsed_email)
print(recipient)  # "user@example.com"
```

**Priority Order**:
1. failed_recipient field
2. x_failed_recipients header
3. to field
4. DSN final_recipient
5. Original message original_to

#### `extract_smtp_codes(parsed_email: Dict[str, Any]) -> Dict[str, Optional[str]]`

Extracts SMTP and enhanced status codes from parsed email.

**Parameters**:
- `parsed_email` (Dict[str, Any]): Previously parsed email data

**Returns**:
- `Dict[str, Optional[str]]`: Dictionary with keys:
  - `smtp_code`: SMTP error code (e.g., "550")
  - `enhanced_status_code`: Enhanced status code (e.g., "5.1.1")

**Example**:
```python
codes = parser.extract_smtp_codes(parsed_email)
print(codes["smtp_code"])  # "550"
print(codes["enhanced_status_code"])  # "5.1.1"
```

### Private Methods

#### `_clean_header(header_value: str) -> str`

Cleans and decodes email header values.

**Parameters**:
- `header_value` (str): Raw header value

**Returns**:
- `str`: Cleaned and decoded header value

#### `_extract_body(msg: EmailMessage) -> str`

Extracts the body content from an email message.

**Parameters**:
- `msg` (EmailMessage): Email message object

**Returns**:
- `str`: Extracted body text

**Behavior**:
- Handles multipart messages
- Extracts text/plain parts
- Includes delivery-status parts
- Decodes content appropriately

#### `_extract_dsn_info(msg: EmailMessage) -> Dict[str, Any]`

Extracts Delivery Status Notification information.

**Parameters**:
- `msg` (EmailMessage): Email message object

**Returns**:
- `Dict[str, Any]`: DSN information dictionary

#### `_parse_dsn_content(dsn_content: str) -> Dict[str, str]`

Parses DSN content using regex patterns.

**Parameters**:
- `dsn_content` (str): Raw DSN text

**Returns**:
- `Dict[str, str]`: Parsed DSN fields

#### `_extract_original_message_info(msg: EmailMessage) -> Dict[str, str]`

Extracts information about the original bounced message.

**Parameters**:
- `msg` (EmailMessage): Email message object

**Returns**:
- `Dict[str, str]`: Original message metadata

#### `_extract_bounce_info_from_body(body: str) -> Dict[str, Any]`

Extracts bounce-specific information from email body using regex.

**Parameters**:
- `body` (str): Email body text

**Returns**:
- `Dict[str, Any]`: Extracted bounce information

#### `_parse_raw_text(text_content: str) -> Dict[str, Any]`

Fallback parser for raw text when standard parsing fails.

**Parameters**:
- `text_content` (str): Raw email text

**Returns**:
- `Dict[str, Any]`: Parsed data with default structure

### Attributes

```python
header_patterns: Dict[str, str] = {
    'return_path': r'Return-Path:\s*<(.+?)>',
    'auto_submitted': r'Auto-Submitted:\s*(.+)',
    'x_failed_recipients': r'X-Failed-Recipients:\s*(.+)',
    'delivery_date': r'Delivery-Date:\s*(.+)',
    'final_recipient': r'Final-Recipient:\s*rfc822;\s*(.+)',
    'action': r'Action:\s*(.+)',
    'status': r'Status:\s*(.+)',
    'diagnostic_code': r'Diagnostic-Code:\s*(.+)',
    'remote_mta': r'Remote-MTA:\s*(.+)',
}
```

---

## DiagnosticExtractor Class

**Location**: `diagnostic_extractor.py`

**Purpose**: Extracts comprehensive diagnostic information from parsed bounce emails.

### Class Definition

```python
class DiagnosticExtractor:
    """
    Extracts diagnostic information from bounce emails including SMTP codes,
    recipient addresses, server metadata, and response messages
    """
```

### Constructor

#### `__init__(self)`

Initializes the DiagnosticExtractor with patterns and configurations.

**Parameters**: None

**Returns**: None

**Example**:
```python
extractor = DiagnosticExtractor()
```

**Attributes Initialized**:
- `smtp_code_pattern` (str): Regex pattern for SMTP codes
- `email_pattern` (str): Regex pattern for email addresses
- `server_patterns` (Dict[str, str]): Server information patterns
- `diagnostic_patterns` (Dict[str, str]): Diagnostic field patterns

### Public Methods

#### `extract_diagnostics(parsed_email: Dict[str, Any]) -> Dict[str, Any]`

Main method to extract comprehensive diagnostic information.

**Parameters**:
- `parsed_email` (Dict[str, Any]): Parsed email data from EmailParser

**Returns**:
- `Dict[str, Any]`: Comprehensive diagnostic information with structure:
  ```python
  {
      "recipient_email": Optional[str],
      "smtp_code": Optional[str],
      "enhanced_status_code": Optional[str],
      "server_response": Optional[str],
      "diagnostic_code": Optional[str],
      "remote_mta": Optional[str],
      "reporting_mta": Optional[str],
      "action": Optional[str],
      "timestamp": Optional[str],
      "retry_info": Dict[str, Any],
      "server_metadata": Dict[str, Any],
      "delivery_status": Dict[str, Any],
      "error_details": Dict[str, Any],
      "network_info": Dict[str, Any]
  }
  ```

**Example**:
```python
extractor = DiagnosticExtractor()
diagnostics = extractor.extract_diagnostics(parsed_email)
print(diagnostics["smtp_code"])  # "550"
print(diagnostics["recipient_email"])  # "user@example.com"
print(diagnostics["server_response"])  # "User unknown"
```

**Processing Steps**:
1. Extracts recipient email address
2. Extracts SMTP and enhanced status codes
3. Extracts server information
4. Extracts diagnostic codes and messages
5. Extracts delivery status information
6. Extracts retry and timing information
7. Extracts error details
8. Extracts network and routing information
9. Extracts timestamp information

#### `generate_diagnostic_summary(diagnostics: Dict[str, Any]) -> Dict[str, Any]`

Generates a summary of diagnostic information completeness.

**Parameters**:
- `diagnostics` (Dict[str, Any]): Diagnostic information from extract_diagnostics()

**Returns**:
- `Dict[str, Any]`: Summary with structure:
  ```python
  {
      "has_recipient": bool,
      "has_smtp_code": bool,
      "has_enhanced_status": bool,
      "has_server_response": bool,
      "has_diagnostic_code": bool,
      "has_timestamp": bool,
      "error_count": int,
      "server_count": int,
      "completeness_score": float  # 0.0 to 1.0
  }
  ```

**Example**:
```python
summary = extractor.generate_diagnostic_summary(diagnostics)
print(f"Completeness: {summary['completeness_score']:.0%}")
```

### Private Methods

#### `_extract_recipient_email(parsed_email: Dict[str, Any]) -> Optional[str]`

Extracts recipient email address from multiple sources.

**Returns**: Email address or None

#### `_extract_smtp_codes(body: str, headers: Dict, dsn_info: Dict) -> Dict[str, Optional[str]]`

Extracts SMTP and enhanced status codes.

**Returns**: Dictionary with smtp_code and enhanced_status_code

#### `_extract_server_information(body: str, headers: Dict) -> Dict[str, Any]`

Extracts mail server information.

**Returns**: Server metadata dictionary

#### `_extract_diagnostic_codes(body: str, headers: Dict, dsn_info: Dict) -> Dict[str, Optional[str]]`

Extracts diagnostic codes and related information.

**Returns**: Diagnostic information dictionary

#### `_extract_delivery_status(dsn_info: Dict, headers: Dict) -> Dict[str, Any]`

Extracts delivery status information.

**Returns**: Delivery status dictionary

#### `_extract_retry_information(body: str, headers: Dict) -> Dict[str, Any]`

Extracts retry and timing information.

**Returns**: Retry information dictionary

#### `_extract_error_details(body: str) -> Dict[str, Any]`

Extracts detailed error information and flags.

**Returns**: Error details dictionary with boolean flags

#### `_extract_network_information(body: str, headers: Dict) -> Dict[str, Any]`

Extracts network and routing information.

**Returns**: Network information dictionary

#### `_extract_timestamp(parsed_email: Dict[str, Any]) -> Optional[str]`

Extracts timestamp from various sources.

**Returns**: Timestamp string or None

### Attributes

```python
smtp_code_pattern: str = r'(\d{3})\s+(\d\.\d\.\d)'
email_pattern: str = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'

server_patterns: Dict[str, str] = {
    'remote_mta': r'Remote-MTA:\s*dns;\s*([^\s\r\n]+)',
    'reporting_mta': r'Reporting-MTA:\s*dns;\s*([^\s\r\n]+)',
    # ... additional patterns
}

diagnostic_patterns: Dict[str, str] = {
    'diagnostic_code': r'Diagnostic-Code:\s*(.+)',
    'status_code': r'Status:\s*(\d\.\d\.\d)',
    # ... additional patterns
}
```

---

## BounceClassifier Class

**Location**: `bounce_classifier.py`

**Purpose**: Classifies bounce emails into categories and provides intelligent recommendations.

### Class Definition

```python
class BounceClassifier:
    """
    Classifies bounce emails into standard categories and provides recommendations
    """
```

### Constructor

#### `__init__(self)`

Initializes the BounceClassifier with patterns and mappings.

**Parameters**: None

**Returns**: None

**Example**:
```python
classifier = BounceClassifier()
```

**Attributes Initialized**:
- `bounce_patterns` (Dict): Bounce pattern definitions
- `smtp_code_mapping` (Dict): SMTP code to category mapping
- `enhanced_status_mapping` (Dict): Enhanced status code mapping

### Public Methods

#### `classify_bounce(parsed_email: Dict[str, Any], diagnostic_info: Dict[str, Any]) -> Dict[str, Any]`

Main method to classify a bounce email.

**Parameters**:
- `parsed_email` (Dict[str, Any]): Parsed email data
- `diagnostic_info` (Dict[str, Any]): Diagnostic information

**Returns**:
- `Dict[str, Any]`: Classification result with structure:
  ```python
  {
      "category": str,  # "Hard Bounce", "Soft Bounce", "Other", "Auto Reply"
      "type": str,  # Specific bounce type
      "severity": str,  # "High", "Medium", "Low", "Unknown"
      "reason": str,  # Human-readable reason
      "recommendations": List[str],  # List of recommendations
      "confidence": float  # 0.0 to 1.0
  }
  ```

**Example**:
```python
classifier = BounceClassifier()
classification = classifier.classify_bounce(parsed_email, diagnostic_info)
print(f"Category: {classification['category']}")
print(f"Type: {classification['type']}")
print(f"Confidence: {classification['confidence']:.0%}")
for rec in classification['recommendations']:
    print(f"- {rec}")
```

**Classification Priority**:
1. Enhanced status code (confidence: 0.9)
2. SMTP code (confidence: 0.8)
3. Pattern matching (confidence: calculated)

**Categories**:
- **Hard Bounce**: Permanent delivery failures
  - Invalid Recipient Address
  - Domain Not Found
  - Blocked by Server
  - Policy Rejection (SPF/DKIM/DMARC Fail)
  - Spam Filter Rejection
  - Restricted Address Type

- **Soft Bounce**: Temporary delivery issues
  - Mailbox Full
  - Greylisting or Throttling
  - Temporary Server Failure
  - Message Too Large
  - Attachment or MIME Type Rejected

- **Other**: Requires review
  - Authentication Required
  - Rate Limited
  - Malformed Header
  - Server Misconfiguration
  - Unknown Bounce Reason

- **Auto Reply**: Automatic responses
  - Out of Office

#### `get_bounce_severity_summary(classifications: List[Dict[str, Any]]) -> Dict[str, int]`

Gets summary of bounce severities from multiple classifications.

**Parameters**:
- `classifications` (List[Dict[str, Any]]): List of classification results

**Returns**:
- `Dict[str, int]`: Severity counts
  ```python
  {
      "High": int,
      "Medium": int,
      "Low": int,
      "Unknown": int
  }
  ```

**Example**:
```python
severity_summary = classifier.get_bounce_severity_summary(classifications)
print(f"High severity: {severity_summary['High']}")
```

#### `get_category_summary(classifications: List[Dict[str, Any]]) -> Dict[str, int]`

Gets summary of bounce categories.

**Parameters**:
- `classifications` (List[Dict[str, Any]]): List of classification results

**Returns**:
- `Dict[str, int]`: Category counts

**Example**:
```python
category_summary = classifier.get_category_summary(classifications)
print(f"Hard Bounces: {category_summary['Hard Bounce']}")
```

#### `get_actionable_insights(classifications: List[Dict[str, Any]]) -> Dict[str, Any]`

Generates actionable insights from multiple classifications.

**Parameters**:
- `classifications` (List[Dict[str, Any]]): List of classification results

**Returns**:
- `Dict[str, Any]`: Insights with structure:
  ```python
  {
      "total_bounces": int,
      "hard_bounce_rate": float,
      "soft_bounce_rate": float,
      "most_common_type": str,
      "most_common_type_count": int,
      "high_confidence_rate": float,
      "severity_distribution": Dict[str, int],
      "category_distribution": Dict[str, int]
  }
  ```

**Example**:
```python
insights = classifier.get_actionable_insights(classifications)
print(f"Hard bounce rate: {insights['hard_bounce_rate']:.1%}")
print(f"Most common: {insights['most_common_type']}")
```

### Private Methods

#### `_initialize_bounce_patterns() -> Dict[str, Dict[str, Any]]`

Initializes bounce pattern definitions.

**Returns**: Dictionary of bounce patterns with structure:
```python
{
    "pattern_name": {
        "category": str,
        "type": str,
        "severity": str,
        "patterns": List[str],  # Regex patterns
        "recommendations": List[str]
    }
}
```

#### `_initialize_smtp_code_mapping() -> Dict[str, Dict[str, str]]`

Initializes SMTP code to bounce type mapping.

**Returns**: SMTP code mapping dictionary

#### `_initialize_enhanced_status_mapping() -> Dict[str, Dict[str, str]]`

Initializes enhanced status code mapping.

**Returns**: Enhanced status code mapping dictionary

#### `_calculate_pattern_score(text: str, patterns: List[str]) -> float`

Calculates how well text matches given patterns.

**Parameters**:
- `text` (str): Text to analyze
- `patterns` (List[str]): List of regex patterns

**Returns**:
- `float`: Score from 0.0 to 1.0 (percentage of patterns matched)

**Algorithm**:
```python
score = number_of_matching_patterns / total_patterns
```

#### `_get_recommendations_for_type(bounce_type: str) -> List[str]`

Gets recommendations for a specific bounce type.

**Parameters**:
- `bounce_type` (str): Bounce type name

**Returns**:
- `List[str]`: List of recommendation strings

### Bounce Pattern Examples

```python
# Hard Bounce - Invalid Recipient
{
    'category': 'Hard Bounce',
    'type': 'Invalid Recipient Address',
    'severity': 'High',
    'patterns': [
        r'user\s+unknown',
        r'no\s+such\s+user',
        r'invalid\s+recipient',
        # ... more patterns
    ],
    'recommendations': [
        'Remove email from mailing list permanently',
        'Verify email address spelling and format',
        'Update contact database with correct information'
    ]
}
```

### SMTP Code Mapping

```python
smtp_code_mapping = {
    '421': {'category': 'Soft Bounce', 'type': 'Service Unavailable', 'severity': 'Low'},
    '550': {'category': 'Hard Bounce', 'type': 'Mailbox Unavailable', 'severity': 'High'},
    '554': {'category': 'Hard Bounce', 'type': 'Transaction Failed', 'severity': 'High'},
    # ... additional mappings
}
```

### Enhanced Status Code Mapping

```python
enhanced_status_mapping = {
    '5.1.1': {'category': 'Hard Bounce', 'type': 'Bad Destination Mailbox', 'severity': 'High'},
    '5.2.2': {'category': 'Soft Bounce', 'type': 'Mailbox Full', 'severity': 'Medium'},
    '4.4.1': {'category': 'Soft Bounce', 'type': 'Connection Timeout', 'severity': 'Low'},
    # ... additional mappings
}
```

---

## Application Functions

**Location**: `app.py`

### Main Application Function

#### `main()`

Main Streamlit application entry point.

**Parameters**: None

**Returns**: None

**Description**: Initializes and runs the Streamlit web interface.

### Helper Functions

#### `get_retry_recommendation(bounce_category: str, bounce_type: str) -> str`

Provides intelligent retry recommendations.

**Parameters**:
- `bounce_category` (str): Bounce category
- `bounce_type` (str): Specific bounce type

**Returns**:
- `str`: Retry recommendation text

**Example**:
```python
rec = get_retry_recommendation("Soft Bounce", "Mailbox Full")
print(rec)  # "🔄 Retry in 24-48 hours"
```

**Recommendations**:
- Hard Bounce: "❌ Do not retry - Remove from list"
- Soft Bounce - Mailbox Full: "🔄 Retry in 24-48 hours"
- Soft Bounce - Greylisting: "🔄 Retry in 1-4 hours"
- Soft Bounce - Temporary: "🔄 Retry in 6-12 hours"
- Other: "⚠️ Manual review required"

#### `get_actionable_steps(bounce_category: str, bounce_type: str) -> List[str]`

Generates specific actionable steps.

**Parameters**:
- `bounce_category` (str): Bounce category
- `bounce_type` (str): Specific bounce type

**Returns**:
- `List[str]`: List of actionable steps

**Example**:
```python
steps = get_actionable_steps("Hard Bounce", "Invalid Recipient")
for step in steps:
    print(f"- {step}")
# - Verify email address spelling
# - Check if recipient changed email
# - Remove from active campaigns
# - Update contact database
```

#### `analyze_domain_reputation(email_address: str) -> str`

Analyzes domain characteristics.

**Parameters**:
- `email_address` (str): Email address to analyze

**Returns**:
- `str`: Domain analysis result

**Example**:
```python
analysis = analyze_domain_reputation("user@gmail.com")
print(analysis)  # "Consumer email (gmail.com)"
```

**Categories**:
- Consumer email (gmail.com, yahoo.com, etc.)
- Business email (corporate domains)
- Educational institution (.edu)
- Government domain (.gov)
- Custom domain

#### `display_current_email_results()`

Displays enhanced email analysis results in Streamlit UI.

**Parameters**: None (uses session state)

**Returns**: None

**Description**: Renders analysis results with intelligent insights.

#### `process_single_email(email_content, filename, email_parser, bounce_classifier, diagnostic_extractor) -> Dict[str, Any]`

Processes a single email through the complete pipeline.

**Parameters**:
- `email_content` (str): Raw email content
- `filename` (str): Name/identifier for the email
- `email_parser` (EmailParser): Parser instance
- `bounce_classifier` (BounceClassifier): Classifier instance
- `diagnostic_extractor` (DiagnosticExtractor): Extractor instance

**Returns**:
- `Dict[str, Any]`: Complete analysis result

**Processing Pipeline**:
1. Parse email
2. Extract diagnostics
3. Classify bounce
4. Combine results

**Example**:
```python
parser = EmailParser()
extractor = DiagnosticExtractor()
classifier = BounceClassifier()

result = process_single_email(
    email_content,
    "bounce_001.txt",
    parser,
    extractor,
    classifier
)
```

#### `generate_csv_export() -> str`

Generates CSV data for export.

**Parameters**: None (uses session state)

**Returns**:
- `str`: CSV formatted data

**Example**:
```python
csv_data = generate_csv_export()
# Returns CSV with all analyzed emails
```

#### `generate_summary_report() -> str`

Generates a summary report.

**Parameters**: None (uses session state)

**Returns**:
- `str`: Summary report text

**Example**:
```python
report = generate_summary_report()
print(report)
# Bounce-Back Email Analysis Summary Report
# ===========================================
# Total Emails Analyzed: 15
# ...
```

---

## Data Structures

### Parsed Email Dictionary

```python
ParsedEmail = {
    "subject": str,
    "from": str,
    "to": str,
    "date": str,
    "message_id": str,
    "return_path": str,
    "auto_submitted": str,
    "x_failed_recipients": str,
    "content_type": str,
    "body": str,
    "headers": Dict[str, str],
    "dsn_info": Dict[str, Any],
    "original_message_info": Dict[str, str],
    "smtp_code": Optional[str],
    "enhanced_status_code": Optional[str],
    "failed_recipient": Optional[str],
    "server_response": Optional[str],
    "mailbox_full": Optional[bool],
    "user_unknown": Optional[bool],
    "domain_error": Optional[bool],
    "spam_related": Optional[bool],
    "connection_timeout": Optional[bool]
}
```

### Diagnostic Information Dictionary

```python
DiagnosticInfo = {
    "recipient_email": Optional[str],
    "smtp_code": Optional[str],
    "enhanced_status_code": Optional[str],
    "server_response": Optional[str],
    "diagnostic_code": Optional[str],
    "remote_mta": Optional[str],
    "reporting_mta": Optional[str],
    "action": Optional[str],
    "timestamp": Optional[str],
    "retry_info": {
        "will_retry_until": Optional[str],
        "next_retry": Optional[str],
        "retry_timeout": Optional[str],
        "giving_up": Optional[str],
        "max_attempts": Optional[str]
    },
    "server_metadata": {
        "remote_mta": Optional[str],
        "reporting_mta": Optional[str],
        "received_from": Optional[str],
        "smtp_server": Optional[str],
        "mx_record": Optional[str],
        "smtp_greeting": Optional[str],
        "server_response": Optional[str]
    },
    "delivery_status": {
        "dsn_action": Optional[str],
        "dsn_status": Optional[str],
        "delivery_date": Optional[str],
        "last_attempt": Optional[str],
        "auto_submitted": Optional[str]
    },
    "error_details": {
        "connection_error": Optional[bool],
        "dns_error": Optional[bool],
        "authentication_error": Optional[bool],
        "permission_error": Optional[bool],
        "quota_error": Optional[bool],
        "virus_error": Optional[bool],
        "spam_error": Optional[bool],
        "size_error": Optional[bool],
        "error_message": Optional[str]
    },
    "network_info": {
        "ip_addresses": Optional[List[str]],
        "hostnames": Optional[List[str]],
        "received_headers": Optional[List[str]]
    }
}
```

### Classification Result Dictionary

```python
ClassificationResult = {
    "category": str,  # "Hard Bounce" | "Soft Bounce" | "Other" | "Auto Reply"
    "type": str,  # Specific bounce type description
    "severity": str,  # "High" | "Medium" | "Low" | "Unknown"
    "reason": str,  # Human-readable explanation
    "recommendations": List[str],  # List of recommendation strings
    "confidence": float  # 0.0 to 1.0
}
```

### Complete Analysis Result Dictionary

```python
AnalysisResult = {
    "filename": str,
    "recipient_email": str,
    "smtp_code": str,
    "bounce_type": str,
    "bounce_category": str,
    "bounce_reason": str,
    "server_response": str,
    "diagnostic_code": str,
    "severity": str,
    "recommendations": List[str],
    "timestamp": str,
    "original_sender": str,
    "subject": str
}
```

---

## Constants and Enumerations

### Bounce Categories

```python
BOUNCE_CATEGORIES = [
    "Hard Bounce",
    "Soft Bounce",
    "Other",
    "Auto Reply"
]
```

### Severity Levels

```python
SEVERITY_LEVELS = [
    "High",
    "Medium",
    "Low",
    "Unknown"
]
```

### Common SMTP Codes

```python
SMTP_CODES = {
    "421": "Service Unavailable",
    "450": "Temporary Failure",
    "451": "Processing Error",
    "452": "Insufficient Storage",
    "500": "Syntax Error",
    "501": "Parameter Error",
    "502": "Command Not Implemented",
    "503": "Bad Command Sequence",
    "504": "Parameter Not Implemented",
    "550": "Mailbox Unavailable",
    "551": "User Not Local",
    "552": "Storage Allocation Exceeded",
    "553": "Mailbox Name Invalid",
    "554": "Transaction Failed"
}
```

### Enhanced Status Codes

```python
ENHANCED_STATUS_CODES = {
    "5.1.1": "Bad Destination Mailbox",
    "5.1.2": "Bad Destination System",
    "5.1.3": "Bad Destination Address Syntax",
    "5.2.1": "Mailbox Disabled",
    "5.2.2": "Mailbox Full",
    "5.3.0": "Other System Error",
    "5.4.1": "No Answer From Host",
    "5.4.4": "Unable to Route",
    "5.5.1": "Invalid Command",
    "5.7.1": "Delivery Not Authorized",
    "5.7.2": "Mailing List Expansion Prohibited",
    "4.2.2": "Mailbox Full (Temporary)",
    "4.4.1": "Connection Timeout",
    "4.4.2": "Connection Dropped"
}
```

---

## Error Handling

### Exception Handling Strategy

The system uses a defensive programming approach with graceful degradation:

```python
try:
    # Primary operation
    result = parse_email(content)
except EmailParsingError:
    # Fallback to raw text parsing
    result = parse_raw_text(content)
except Exception as e:
    # Log error and return safe defaults
    logger.error(f"Unexpected error: {e}")
    result = get_default_result()
```

### Common Error Scenarios

#### 1. Malformed Email Content

**Scenario**: Email content is not properly formatted

**Handling**:
- EmailParser falls back to `_parse_raw_text()`
- Extracts what it can using regex patterns
- Returns partial results with defaults for missing fields

#### 2. Missing DSN Information

**Scenario**: Email lacks Delivery Status Notification section

**Handling**:
- DiagnosticExtractor searches body text
- Uses pattern matching as fallback
- Returns None for unavailable fields

#### 3. Encoding Issues

**Scenario**: Email contains non-UTF-8 characters

**Handling**:
```python
content.decode('utf-8', errors='ignore')
```
- Ignores problematic characters
- Continues processing with available data

#### 4. Classification Uncertainty

**Scenario**: No clear pattern match found

**Handling**:
- Returns "Unknown" or "Other" category
- Sets low confidence score
- Provides generic recommendations

---

## Usage Examples

### Example 1: Complete Analysis Pipeline

```python
from email_parser import EmailParser
from diagnostic_extractor import DiagnosticExtractor
from bounce_classifier import BounceClassifier

# Initialize components
parser = EmailParser()
extractor = DiagnosticExtractor()
classifier = BounceClassifier()

# Raw email content
email_content = """
From: MAILER-DAEMON@example.com
To: sender@mycompany.com
Subject: Undelivered Mail Returned to Sender

The following address failed:
  user@nonexistent.com
  550 5.1.1 User unknown
"""

# Step 1: Parse email
parsed_email = parser.parse_email(email_content)
print(f"Subject: {parsed_email['subject']}")
print(f"Body length: {len(parsed_email['body'])}")

# Step 2: Extract diagnostics
diagnostics = extractor.extract_diagnostics(parsed_email)
print(f"Recipient: {diagnostics['recipient_email']}")
print(f"SMTP Code: {diagnostics['smtp_code']}")
print(f"Enhanced Code: {diagnostics['enhanced_status_code']}")

# Step 3: Classify bounce
classification = classifier.classify_bounce(parsed_email, diagnostics)
print(f"Category: {classification['category']}")
print(f"Type: {classification['type']}")
print(f"Severity: {classification['severity']}")
print(f"Confidence: {classification['confidence']:.1%}")

# Step 4: Get recommendations
for i, rec in enumerate(classification['recommendations'], 1):
    print(f"{i}. {rec}")
```

### Example 2: Batch Processing

```python
import glob

parser = EmailParser()
extractor = DiagnosticExtractor()
classifier = BounceClassifier()

# Process multiple bounce files
bounce_files = glob.glob("bounces/*.txt")
results = []

for filepath in bounce_files:
    with open(filepath, 'r') as f:
        email_content = f.read()

    # Process through pipeline
    parsed = parser.parse_email(email_content)
    diag = extractor.extract_diagnostics(parsed)
    classification = classifier.classify_bounce(parsed, diag)

    results.append({
        'file': filepath,
        'recipient': diag['recipient_email'],
        'category': classification['category'],
        'type': classification['type'],
        'severity': classification['severity']
    })

# Generate insights
insights = classifier.get_actionable_insights(results)
print(f"Total bounces: {insights['total_bounces']}")
print(f"Hard bounce rate: {insights['hard_bounce_rate']:.1%}")
print(f"Most common type: {insights['most_common_type']}")
```

### Example 3: Custom Pattern Addition

```python
classifier = BounceClassifier()

# Add custom bounce pattern
classifier.bounce_patterns['custom_rejection'] = {
    'category': 'Hard Bounce',
    'type': 'Custom Rejection',
    'severity': 'High',
    'patterns': [
        r'custom\s+error\s+pattern',
        r'specific\s+rejection'
    ],
    'recommendations': [
        'Custom recommendation 1',
        'Custom recommendation 2'
    ]
}

# Use classifier normally
classification = classifier.classify_bounce(parsed_email, diagnostics)
```

### Example 4: Diagnostic Summary

```python
extractor = DiagnosticExtractor()

# Extract diagnostics
diagnostics = extractor.extract_diagnostics(parsed_email)

# Generate summary
summary = extractor.generate_diagnostic_summary(diagnostics)

print(f"Data completeness: {summary['completeness_score']:.0%}")
print(f"Has SMTP code: {summary['has_smtp_code']}")
print(f"Has recipient: {summary['has_recipient']}")
print(f"Error count: {summary['error_count']}")
```

### Example 5: Export Results

```python
import pandas as pd

# Analyze multiple emails
results = []
for email_content in email_list:
    parsed = parser.parse_email(email_content)
    diag = extractor.extract_diagnostics(parsed)
    classification = classifier.classify_bounce(parsed, diag)

    results.append({
        'recipient': diag['recipient_email'],
        'category': classification['category'],
        'type': classification['type'],
        'severity': classification['severity'],
        'smtp_code': diag['smtp_code'],
        'confidence': classification['confidence']
    })

# Create DataFrame and export
df = pd.DataFrame(results)
df.to_csv('bounce_analysis_results.csv', index=False)

# Generate summary
print("\nBounce Category Distribution:")
print(df['category'].value_counts())
print("\nSeverity Distribution:")
print(df['severity'].value_counts())
```

---

## Version Information

**API Version**: 0.1.0
**Python Version**: 3.11+
**Last Updated**: December 2025

## Changelog

### Version 0.1.0 (Initial Release)
- EmailParser class with full email parsing
- DiagnosticExtractor with comprehensive extraction
- BounceClassifier with 50+ patterns
- Streamlit web interface
- CSV and text export functionality

---

## Contact and Support

For API questions, bug reports, or feature requests, contact the development team.

---

**Document Version**: 1.0
**Maintained By**: Development Team
