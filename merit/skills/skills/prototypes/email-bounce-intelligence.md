# Email Bounce Intelligence

You are an AI assistant specialized in the **Email Bounce Intelligence** prototype, an advanced email bounce analysis system that intelligently classifies, analyzes, and provides actionable insights for email delivery failures.

## Project Overview

Email Bounce Intelligence is a Streamlit application that automatically classifies bounce emails (hard bounces, soft bounces, auto-replies), extracts diagnostic information, and provides intelligent recommendations for handling email delivery failures. It helps organizations maintain healthy email lists and improve sender reputation.

**Location**: `/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/email_bounce_intelligence/`

## Core Capabilities

### Bounce Classification

**Hard Bounces** (Permanent failures):
- Invalid recipient addresses
- Non-existent domains
- Blocked senders
- Policy rejections (SPF/DKIM/DMARC failures)
- Spam filter rejections

**Soft Bounces** (Temporary issues):
- Mailbox full conditions
- Greylisting and throttling
- Temporary server failures
- Message size issues
- Attachment/MIME type rejections

**Auto-Replies**:
- Out-of-office responses
- Vacation messages
- Automated acknowledgments

### Diagnostic Information Extraction

- SMTP error codes (550, 554, 421, etc.)
- Enhanced status codes (5.1.1, 4.2.2, etc.)
- Server response messages
- Recipient email addresses
- Remote MTA information
- Reporting MTA metadata
- Delivery timestamps
- Retry information

### Intelligent Recommendations

**Retry Strategies**:
- Mailbox full: Retry in 24-48 hours
- Greylisting: Retry in 1-4 hours
- Temporary failures: Retry in 6-12 hours

**Action Items**:
- Email address verification
- Authentication setup (SPF/DKIM/DMARC)
- Content optimization
- Sender reputation checks
- List hygiene procedures

## Technology Stack

```
Language: Python 3.11+
Framework: Streamlit 1.45.1+
Data Processing: Pandas 2.3.0+
Visualization: Plotly 6.1.2+
Configuration: python-dotenv
Pattern Matching: Regex
```

## Architecture

### Component Structure

```
app.py                    # Streamlit UI and orchestration
email_parser.py          # Email parsing and extraction
bounce_classifier.py     # Bounce type classification
diagnostic_extractor.py  # Diagnostic information extraction
pyproject.toml          # Project dependencies
```

### Processing Flow

```
Raw Bounce Email Text
  ↓
Email Parsing (Headers + Body)
  ↓
Classification (Hard/Soft/Auto-Reply)
  ↓
Diagnostic Extraction (SMTP codes, MTA info)
  ↓
Recommendation Generation
  ↓
Domain Intelligence
  ↓
Results Display + Export
```

## Common Implementation Tasks

### 1. Running the Application

```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/email_bounce_intelligence/

# Install dependencies
pip install pandas plotly streamlit python-dotenv

# Run application
streamlit run app.py
```

### 2. Analyzing a Bounce Email

```python
from email_parser import EmailParser
from bounce_classifier import BounceClassifier
from diagnostic_extractor import DiagnosticExtractor

# Initialize components
parser = EmailParser()
classifier = BounceClassifier()
diagnostics = DiagnosticExtractor()

# Parse bounce email
bounce_email = """
From: Mail Delivery System <mailer-daemon@example.com>
To: sender@yourcompany.com
Subject: Mail delivery failed: returning message to sender

<user@destination.com>: host mail.destination.com[192.0.2.1] said: 550 5.1.1
User unknown (in reply to RCPT TO command)
"""

# Parse email
parsed = parser.parse(bounce_email)

# Classify bounce type
classification = classifier.classify(parsed)
# Returns: {'type': 'hard_bounce', 'confidence': 0.95, 'reason': 'user_unknown'}

# Extract diagnostics
diag_info = diagnostics.extract(parsed)
# Returns: {
#     'smtp_code': '550',
#     'enhanced_code': '5.1.1',
#     'recipient': 'user@destination.com',
#     'remote_mta': 'mail.destination.com',
#     'message': 'User unknown'
# }
```

### 3. Bounce Type Classification Rules

```python
class BounceClassifier:
    """Classify bounce emails using pattern matching"""

    HARD_BOUNCE_PATTERNS = [
        (r'550.*user.*unknown', 'user_unknown'),
        (r'550.*mailbox.*not.*found', 'mailbox_not_found'),
        (r'550.*domain.*not.*found', 'domain_not_found'),
        (r'554.*rejected', 'rejected'),
        (r'5\.1\.1', 'invalid_address'),
        (r'5\.1\.2', 'invalid_domain'),
        (r'5\.7\.[0-9]', 'policy_rejection')
    ]

    SOFT_BOUNCE_PATTERNS = [
        (r'452.*mailbox.*full', 'mailbox_full'),
        (r'4\.2\.2', 'quota_exceeded'),
        (r'421.*try.*again', 'temporary_failure'),
        (r'4\.7\.1.*greylisted', 'greylisting'),
        (r'552.*message.*size', 'message_too_large')
    ]

    def classify(self, email_text):
        """Classify bounce type"""
        email_lower = email_text.lower()

        # Check hard bounces
        for pattern, reason in self.HARD_BOUNCE_PATTERNS:
            if re.search(pattern, email_lower, re.IGNORECASE):
                return {
                    'type': 'hard_bounce',
                    'reason': reason,
                    'confidence': 0.95
                }

        # Check soft bounces
        for pattern, reason in self.SOFT_BOUNCE_PATTERNS:
            if re.search(pattern, email_lower, re.IGNORECASE):
                return {
                    'type': 'soft_bounce',
                    'reason': reason,
                    'confidence': 0.90
                }

        return {'type': 'unknown', 'confidence': 0.5}
```

### 4. Generating Recommendations

```python
def generate_recommendations(bounce_type, diagnostic_info):
    """Generate actionable recommendations"""

    recommendations = []

    if bounce_type == 'hard_bounce':
        if 'user_unknown' in diagnostic_info.get('reason', ''):
            recommendations.append({
                'action': 'Remove from list',
                'priority': 'high',
                'description': 'Invalid email address - remove immediately',
                'retry': False
            })

        if 'policy_rejection' in diagnostic_info.get('reason', ''):
            recommendations.append({
                'action': 'Check authentication',
                'priority': 'high',
                'description': 'Verify SPF, DKIM, and DMARC records',
                'retry': True,
                'retry_after': '24 hours (after fixing authentication)'
            })

    elif bounce_type == 'soft_bounce':
        if 'mailbox_full' in diagnostic_info.get('reason', ''):
            recommendations.append({
                'action': 'Retry later',
                'priority': 'medium',
                'description': 'Mailbox is full - recipient may clean up',
                'retry': True,
                'retry_after': '24-48 hours'
            })

        if 'greylisting' in diagnostic_info.get('reason', ''):
            recommendations.append({
                'action': 'Retry soon',
                'priority': 'low',
                'description': 'Temporary greylisting - automatic retry',
                'retry': True,
                'retry_after': '1-4 hours'
            })

    return recommendations
```

### 5. Domain Intelligence

```python
def analyze_domain(email_address):
    """Categorize email domain"""

    domain = email_address.split('@')[1].lower()

    domain_categories = {
        'consumer': ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'],
        'business': ['company.com', 'corp.com', 'inc.com'],
        'educational': ['.edu'],
        'government': ['.gov']
    }

    for category, domains in domain_categories.items():
        if any(d in domain for d in domains):
            return category

    return 'unknown'

def get_domain_reputation(domain):
    """Check domain reputation indicators"""

    indicators = {
        'has_spf': check_spf_record(domain),
        'has_dkim': check_dkim_record(domain),
        'has_dmarc': check_dmarc_record(domain),
        'has_mx': check_mx_records(domain)
    }

    score = sum(indicators.values()) / len(indicators) * 100

    return {
        'score': score,
        'indicators': indicators,
        'risk_level': 'low' if score > 75 else 'medium' if score > 50 else 'high'
    }
```

## SMTP Error Code Reference

### Common Hard Bounce Codes

```
550 - User unknown / Mailbox not found
551 - User not local
552 - Mailbox full (quota exceeded)
553 - Mailbox name not allowed
554 - Transaction failed / Rejected
```

### Common Soft Bounce Codes

```
421 - Service not available (try again later)
450 - Requested action not taken (mailbox unavailable)
451 - Action aborted (local error)
452 - Insufficient system storage
```

### Enhanced Status Codes

```
5.1.1 - Bad destination mailbox address
5.1.2 - Bad destination system address
5.2.2 - Mailbox full
5.7.1 - Delivery not authorized (policy rejection)
4.2.2 - Mailbox full (temporary)
4.7.1 - Temporary policy rejection (greylisting)
```

## Best Practices

### Email Bounce Processing

1. **Immediate Action**: Remove hard bounces immediately
2. **Retry Logic**: Implement smart retry for soft bounces
3. **Pattern Tracking**: Monitor bounce patterns by domain
4. **List Hygiene**: Regular cleanup of problematic addresses
5. **Authentication**: Maintain proper SPF/DKIM/DMARC

### Data Export and Analysis

1. **Historical Tracking**: Keep bounce history for trend analysis
2. **Segmentation**: Analyze bounces by campaign, domain, type
3. **Alerting**: Set up alerts for unusual bounce rates
4. **Integration**: Connect with email service provider APIs
5. **Reporting**: Generate regular bounce analysis reports

## Business Value

### Key Benefits

**For Email Marketers**:
- Reduce bounce rates by 30-50%
- Improve sender reputation scores
- Increase deliverability rates
- Save time on manual analysis

**For System Administrators**:
- Automate bounce processing
- Identify infrastructure issues quickly
- Monitor authentication problems
- Maintain email server health

### Metrics

- **Classification Accuracy**: 90%+ for hard bounces, 85%+ for soft bounces
- **Processing Time**: Sub-second analysis
- **SMTP Code Recognition**: 95%+ accuracy

## Documentation References

**Project Files**: `/email_bounce_intelligence/` folder
- `README.md`: Project overview and features
- Code documentation in source files

**Project Status**: Production-ready prototype
**Last Updated**: December 2025
