# Technical Architecture - Email Bounce Intelligence

## System Overview

The Email Bounce Intelligence system is designed as a modular, scalable solution for analyzing email bounce notifications. It employs a multi-stage processing pipeline that transforms raw email content into actionable intelligence.

## Architecture Diagram

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[Streamlit Web Interface]
    end

    subgraph "Processing Pipeline"
        INPUT[Raw Email Input]
        PARSER[Email Parser]
        DIAGNOSTIC[Diagnostic Extractor]
        CLASSIFIER[Bounce Classifier]
        ANALYSIS[Analysis Engine]
        OUTPUT[Results & Recommendations]
    end

    subgraph "Data Storage"
        SESSION[Session State]
        EXPORT[Export Files CSV/TXT]
    end

    UI --> INPUT
    INPUT --> PARSER
    PARSER --> DIAGNOSTIC
    PARSER --> CLASSIFIER
    DIAGNOSTIC --> CLASSIFIER
    CLASSIFIER --> ANALYSIS
    ANALYSIS --> OUTPUT
    OUTPUT --> UI
    OUTPUT --> SESSION
    OUTPUT --> EXPORT

    style UI fill:#e1f5ff
    style PARSER fill:#fff4e1
    style DIAGNOSTIC fill:#fff4e1
    style CLASSIFIER fill:#fff4e1
    style ANALYSIS fill:#e8f5e9
    style OUTPUT fill:#f3e5f5
```

## Component Architecture

```mermaid
graph LR
    subgraph "EmailParser Component"
        EP1[Parse Headers]
        EP2[Extract Body]
        EP3[Extract DSN Info]
        EP4[Extract Original Message]
    end

    subgraph "DiagnosticExtractor Component"
        DE1[Extract SMTP Codes]
        DE2[Extract Recipient Info]
        DE3[Extract Server Metadata]
        DE4[Extract Error Details]
        DE5[Extract Network Info]
    end

    subgraph "BounceClassifier Component"
        BC1[Pattern Matching]
        BC2[SMTP Code Mapping]
        BC3[Enhanced Status Mapping]
        BC4[Confidence Scoring]
    end

    EP1 --> EP2
    EP2 --> EP3
    EP3 --> EP4

    DE1 --> DE2
    DE2 --> DE3
    DE3 --> DE4
    DE4 --> DE5

    BC1 --> BC4
    BC2 --> BC4
    BC3 --> BC4

    style EP1 fill:#bbdefb
    style DE1 fill:#c8e6c9
    style BC1 fill:#f8bbd0
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant Parser as EmailParser
    participant Extractor as DiagnosticExtractor
    participant Classifier as BounceClassifier
    participant Engine as Analysis Engine

    User->>UI: Paste email content
    User->>UI: Click "Analyze Email"
    UI->>Parser: parse_email(email_content)
    Parser->>Parser: Extract headers
    Parser->>Parser: Extract body content
    Parser->>Parser: Parse DSN information
    Parser-->>UI: parsed_email dict

    UI->>Extractor: extract_diagnostics(parsed_email)
    Extractor->>Extractor: Extract SMTP codes
    Extractor->>Extractor: Extract recipient email
    Extractor->>Extractor: Extract server info
    Extractor->>Extractor: Extract error details
    Extractor-->>UI: diagnostic_info dict

    UI->>Classifier: classify_bounce(parsed_email, diagnostic_info)
    Classifier->>Classifier: Check SMTP codes
    Classifier->>Classifier: Match patterns
    Classifier->>Classifier: Calculate confidence
    Classifier-->>UI: classification dict

    UI->>Engine: Generate recommendations
    Engine->>Engine: Assess risk level
    Engine->>Engine: Generate retry strategy
    Engine->>Engine: Create action items
    Engine-->>UI: complete_results

    UI-->>User: Display analysis results
    UI-->>User: Show recommendations
```

## Processing Flow

```mermaid
flowchart TD
    START([Start: Raw Email]) --> PARSE{Email Parser}
    PARSE -->|Success| EXTRACT[Extract Diagnostics]
    PARSE -->|Fallback| RAWPARSE[Parse as Raw Text]

    RAWPARSE --> EXTRACT

    EXTRACT --> CHECK1{Has Enhanced<br/>Status Code?}
    CHECK1 -->|Yes| MAP1[Map Enhanced Status]
    CHECK1 -->|No| CHECK2{Has SMTP Code?}

    CHECK2 -->|Yes| MAP2[Map SMTP Code]
    CHECK2 -->|No| PATTERN[Pattern Matching]

    MAP1 --> CLASSIFY[Classification Result]
    MAP2 --> CLASSIFY
    PATTERN --> CLASSIFY

    CLASSIFY --> CONFIDENCE[Calculate Confidence]
    CONFIDENCE --> RECOMMEND[Generate Recommendations]
    RECOMMEND --> RISK[Assess Risk Level]
    RISK --> DOMAIN[Domain Analysis]
    DOMAIN --> ACTIONS[Action Items]
    ACTIONS --> END([Complete Analysis])

    style START fill:#e3f2fd
    style PARSE fill:#fff9c4
    style CLASSIFY fill:#c8e6c9
    style END fill:#f3e5f5
```

## Class Architecture

### EmailParser Class

```mermaid
classDiagram
    class EmailParser {
        -header_patterns: Dict
        +parse_email(email_content) Dict
        -_clean_header(header_value) str
        -_extract_body(msg) str
        -_extract_dsn_info(msg) Dict
        -_parse_dsn_content(dsn_content) Dict
        -_extract_original_message_info(msg) Dict
        -_extract_bounce_info_from_body(body) Dict
        -_parse_raw_text(text_content) Dict
        +extract_recipient_email(parsed_email) str
        +extract_smtp_codes(parsed_email) Dict
    }
```

**Responsibilities:**
- Parse MIME-formatted email messages
- Extract headers, body, and attachments
- Parse DSN (Delivery Status Notification) sections
- Extract original message information
- Fallback to raw text parsing when needed

**Key Methods:**
- `parse_email()`: Main entry point for email parsing
- `_extract_dsn_info()`: Extracts structured delivery status data
- `_extract_bounce_info_from_body()`: Regex-based information extraction

### DiagnosticExtractor Class

```mermaid
classDiagram
    class DiagnosticExtractor {
        -smtp_code_pattern: str
        -email_pattern: str
        -server_patterns: Dict
        -diagnostic_patterns: Dict
        +extract_diagnostics(parsed_email) Dict
        -_extract_recipient_email(parsed_email) str
        -_extract_smtp_codes(body, headers, dsn_info) Dict
        -_extract_server_information(body, headers) Dict
        -_extract_diagnostic_codes(body, headers, dsn_info) Dict
        -_extract_delivery_status(dsn_info, headers) Dict
        -_extract_retry_information(body, headers) Dict
        -_extract_error_details(body) Dict
        -_extract_network_information(body, headers) Dict
        -_extract_timestamp(parsed_email) str
        +generate_diagnostic_summary(diagnostics) Dict
    }
```

**Responsibilities:**
- Extract SMTP and enhanced status codes
- Identify recipient email addresses
- Extract server metadata and responses
- Parse error messages and details
- Extract network routing information
- Compile retry and timing data

**Key Methods:**
- `extract_diagnostics()`: Comprehensive diagnostic extraction
- `_extract_smtp_codes()`: Parses SMTP error codes
- `_extract_server_information()`: Identifies mail server details

### BounceClassifier Class

```mermaid
classDiagram
    class BounceClassifier {
        -bounce_patterns: Dict
        -smtp_code_mapping: Dict
        -enhanced_status_mapping: Dict
        +classify_bounce(parsed_email, diagnostic_info) Dict
        -_initialize_bounce_patterns() Dict
        -_initialize_smtp_code_mapping() Dict
        -_initialize_enhanced_status_mapping() Dict
        -_calculate_pattern_score(text, patterns) float
        -_get_recommendations_for_type(bounce_type) List
        +get_bounce_severity_summary(classifications) Dict
        +get_category_summary(classifications) Dict
        +get_actionable_insights(classifications) Dict
    }
```

**Responsibilities:**
- Classify bounces into categories (Hard, Soft, Other, Auto-Reply)
- Map SMTP codes to bounce types
- Pattern matching for error messages
- Generate confidence scores
- Provide actionable recommendations

**Key Methods:**
- `classify_bounce()`: Main classification logic
- `_calculate_pattern_score()`: Pattern matching algorithm
- `get_actionable_insights()`: Generate analytics from classifications

## Data Models

### Parsed Email Structure

```python
{
    "subject": str,              # Email subject line
    "from": str,                 # Sender address
    "to": str,                   # Recipient address
    "date": str,                 # Send date/time
    "message_id": str,           # Unique message identifier
    "return_path": str,          # Return path address
    "auto_submitted": str,       # Auto-submission header
    "x_failed_recipients": str,  # Failed recipient header
    "content_type": str,         # MIME content type
    "body": str,                 # Email body text
    "headers": dict,             # All headers as key-value pairs
    "dsn_info": {                # Delivery Status Notification data
        "action": str,
        "status": str,
        "final_recipient": str,
        "diagnostic_code": str,
        ...
    },
    "original_message_info": {   # Original message metadata
        "original_subject": str,
        "original_from": str,
        "original_to": str,
        ...
    }
}
```

### Diagnostic Information Structure

```python
{
    "recipient_email": str,           # Bounced recipient address
    "smtp_code": str,                 # SMTP error code (e.g., "550")
    "enhanced_status_code": str,      # Enhanced code (e.g., "5.1.1")
    "server_response": str,           # Server error message
    "diagnostic_code": str,           # Full diagnostic code
    "remote_mta": str,                # Remote MTA hostname
    "reporting_mta": str,             # Reporting MTA hostname
    "action": str,                    # DSN action (failed, delayed, etc.)
    "timestamp": str,                 # Event timestamp
    "retry_info": {                   # Retry timing information
        "will_retry_until": str,
        "next_retry": str,
        ...
    },
    "server_metadata": {              # Server details
        "remote_mta": str,
        "reporting_mta": str,
        ...
    },
    "delivery_status": {              # Delivery status details
        "dsn_action": str,
        "dsn_status": str,
        ...
    },
    "error_details": {                # Specific error flags
        "connection_error": bool,
        "dns_error": bool,
        "authentication_error": bool,
        ...
    },
    "network_info": {                 # Network/routing data
        "ip_addresses": list,
        "hostnames": list,
        ...
    }
}
```

### Classification Result Structure

```python
{
    "category": str,          # Hard Bounce, Soft Bounce, Other, Auto Reply
    "type": str,              # Specific bounce type
    "severity": str,          # High, Medium, Low, Unknown
    "reason": str,            # Human-readable reason
    "recommendations": list,  # List of recommendation strings
    "confidence": float       # 0.0 to 1.0 confidence score
}
```

## Pattern Matching Algorithm

```mermaid
flowchart TD
    INPUT[Email Body + Subject] --> NORMALIZE[Normalize to Lowercase]
    NORMALIZE --> ITERATE[Iterate Bounce Patterns]

    ITERATE --> PATTERN1[Pattern 1: Invalid Recipient]
    ITERATE --> PATTERN2[Pattern 2: Domain Not Found]
    ITERATE --> PATTERN3[Pattern 3: Mailbox Full]
    ITERATE --> PATTERNN[Pattern N: ...]

    PATTERN1 --> SCORE1[Calculate Score 1]
    PATTERN2 --> SCORE2[Calculate Score 2]
    PATTERN3 --> SCORE3[Calculate Score 3]
    PATTERNN --> SCOREN[Calculate Score N]

    SCORE1 --> COMPARE[Compare All Scores]
    SCORE2 --> COMPARE
    SCORE3 --> COMPARE
    SCOREN --> COMPARE

    COMPARE --> BEST[Select Best Match]
    BEST --> THRESHOLD{Score > 0?}

    THRESHOLD -->|Yes| RETURN[Return Classification]
    THRESHOLD -->|No| UNKNOWN[Return Unknown]

    style INPUT fill:#e3f2fd
    style COMPARE fill:#fff9c4
    style RETURN fill:#c8e6c9
    style UNKNOWN fill:#ffccbc
```

**Algorithm Details:**

1. **Pattern Scoring**: For each bounce pattern:
   - Count matches against regex patterns
   - Calculate score = matches / total_patterns
   - Score ranges from 0.0 (no match) to 1.0 (all patterns match)

2. **Priority Hierarchy**:
   - Priority 1: Enhanced Status Code (confidence: 0.9)
   - Priority 2: SMTP Code (confidence: 0.8)
   - Priority 3: Pattern Matching (confidence: calculated score)

3. **Confidence Scoring**:
   - Enhanced Status Code match: 90% confidence
   - SMTP Code match: 80% confidence
   - Pattern match: Variable (based on pattern count)

## Classification Categories

### Hard Bounce Patterns (6 Types)

```mermaid
graph TD
    HARD[Hard Bounce] --> INVALID[Invalid Recipient<br/>User Unknown]
    HARD --> DOMAIN[Domain Not Found<br/>No MX Record]
    HARD --> BLOCKED[Blocked by Server<br/>Blacklisted]
    HARD --> POLICY[Policy Rejection<br/>SPF/DKIM/DMARC Fail]
    HARD --> SPAM[Spam Filter Rejection]
    HARD --> RESTRICTED[Restricted Address Type]

    style HARD fill:#ffcdd2
    style INVALID fill:#ef9a9a
    style DOMAIN fill:#ef9a9a
    style BLOCKED fill:#ef9a9a
    style POLICY fill:#ef9a9a
    style SPAM fill:#ef9a9a
    style RESTRICTED fill:#ef9a9a
```

### Soft Bounce Patterns (5 Types)

```mermaid
graph TD
    SOFT[Soft Bounce] --> FULL[Mailbox Full<br/>Quota Exceeded]
    SOFT --> GREY[Greylisting/Throttling<br/>Rate Limit]
    SOFT --> TEMP[Temporary Server Failure<br/>Timeout]
    SOFT --> SIZE[Message Too Large]
    SOFT --> ATTACH[Attachment/MIME Rejected]

    style SOFT fill:#fff9c4
    style FULL fill:#fff59d
    style GREY fill:#fff59d
    style TEMP fill:#fff59d
    style SIZE fill=#fff59d
    style ATTACH fill:#fff59d
```

## Retry Strategy Logic

```mermaid
flowchart TD
    START[Bounce Detected] --> CAT{Bounce Category}

    CAT -->|Hard Bounce| REMOVE[Do Not Retry<br/>Remove from List]
    CAT -->|Soft Bounce| TYPE{Bounce Type}
    CAT -->|Other| MANUAL[Manual Review Required]
    CAT -->|Auto Reply| CONTINUE[Continue Normal Delivery]

    TYPE -->|Mailbox Full| RETRY1[Retry in 24-48 hours]
    TYPE -->|Greylisting/Throttling| RETRY2[Retry in 1-4 hours]
    TYPE -->|Temporary Failure| RETRY3[Retry in 6-12 hours]
    TYPE -->|Other Soft| RETRY4[Retry in 4-8 hours<br/>with caution]

    style REMOVE fill:#ffcdd2
    style RETRY1 fill:#c8e6c9
    style RETRY2 fill:#c8e6c9
    style RETRY3 fill:#c8e6c9
    style RETRY4 fill:#fff9c4
    style MANUAL fill:#ffe0b2
```

## System Integration Points

```mermaid
graph TB
    subgraph "External Systems"
        ESP[Email Service Provider]
        DB[Database System]
        API[REST API]
        MONITOR[Monitoring System]
    end

    subgraph "Email Bounce Intelligence"
        CORE[Core Analysis Engine]
    end

    subgraph "Data Outputs"
        CSV[CSV Export]
        REPORT[Summary Reports]
        ALERTS[Alert System]
        DASHBOARD[Analytics Dashboard]
    end

    ESP -->|Bounce Emails| CORE
    DB -->|Historical Data| CORE
    API -->|Email Content| CORE

    CORE -->|Analysis Results| CSV
    CORE -->|Metrics| REPORT
    CORE -->|Critical Issues| ALERTS
    CORE -->|Statistics| DASHBOARD
    CORE -->|Trends| MONITOR

    style CORE fill:#4caf50
    style ESP fill:#2196f3
    style ALERTS fill=#ff9800
```

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Email Parsing | O(n) | n = email size in characters |
| Pattern Matching | O(p * m) | p = patterns, m = text length |
| SMTP Code Lookup | O(1) | Hash table lookup |
| Classification | O(p) | p = number of patterns |
| Full Analysis | O(n + p*m) | Combined parsing and classification |

### Space Complexity

| Component | Memory Usage | Notes |
|-----------|-------------|-------|
| Pattern Storage | ~50 KB | Static pattern definitions |
| Parsed Email | Variable | Proportional to email size |
| Session State | ~100 KB per email | Streamlit session storage |
| Export Data | Cumulative | Grows with analyzed emails |

## Error Handling Strategy

```mermaid
flowchart TD
    OP[Operation] --> TRY{Try Operation}
    TRY -->|Success| RETURN[Return Results]
    TRY -->|Exception| CATCH[Catch Exception]

    CATCH --> TYPE{Error Type}
    TYPE -->|Parse Error| FALLBACK1[Fallback: Raw Text Parse]
    TYPE -->|Encoding Error| FALLBACK2[Fallback: Ignore Encoding]
    TYPE -->|Missing Data| FALLBACK3[Return Default Values]
    TYPE -->|Unknown Error| LOG[Log Error & Return Safe Defaults]

    FALLBACK1 --> RETURN
    FALLBACK2 --> RETURN
    FALLBACK3 --> RETURN
    LOG --> RETURN

    style TRY fill:#e3f2fd
    style CATCH fill:#fff9c4
    style RETURN fill:#c8e6c9
    style LOG fill:#ffccbc
```

## Security Considerations

### Input Validation
- Email content sanitization
- Regex pattern limits to prevent ReDoS attacks
- File upload size restrictions
- Content type validation

### Data Privacy
- No persistent storage of email content
- Session-based data storage only
- No external API calls with sensitive data
- Local processing only

### Output Sanitization
- HTML escaping in UI display
- Safe file download mechanisms
- CSV injection prevention

## Scalability Considerations

### Current Limitations (Prototype)
- Single-threaded processing
- In-memory session storage
- No persistent database
- Manual batch processing

### Production Scaling Recommendations

```mermaid
graph TB
    subgraph "Scalable Architecture"
        LB[Load Balancer]
        API1[API Server 1]
        API2[API Server 2]
        QUEUE[Message Queue]
        WORKER1[Worker 1]
        WORKER2[Worker 2]
        CACHE[Redis Cache]
        DB[(Database)]
        S3[Object Storage]
    end

    LB --> API1
    LB --> API2
    API1 --> QUEUE
    API2 --> QUEUE
    QUEUE --> WORKER1
    QUEUE --> WORKER2
    WORKER1 --> CACHE
    WORKER2 --> CACHE
    WORKER1 --> DB
    WORKER2 --> DB
    WORKER1 --> S3
    WORKER2 --> S3

    style LB fill:#4caf50
    style QUEUE fill:#ff9800
    style DB fill:#2196f3
```

**Recommendations:**
1. Implement asynchronous processing with message queues
2. Add database for persistent storage and analytics
3. Use caching for pattern lookups and classifications
4. Implement horizontal scaling for worker processes
5. Add API layer for integration flexibility

## Technology Stack

### Core Technologies
- **Python 3.11+**: Main programming language
- **Streamlit 1.45+**: Web UI framework
- **Pandas 2.3+**: Data manipulation and export

### Standard Libraries
- **email**: Email parsing
- **re**: Regular expression matching
- **typing**: Type hints
- **datetime**: Timestamp handling
- **io**: File I/O operations

### Development Tools
- **uv**: Modern Python package manager
- **pyproject.toml**: Dependency management

## Configuration Management

### Pattern Configuration
Bounce patterns are defined in `BounceClassifier._initialize_bounce_patterns()`:
- Modular pattern definitions
- Easy to add new patterns
- Configurable confidence thresholds

### SMTP Code Mapping
Centralized mapping in `BounceClassifier._initialize_smtp_code_mapping()`:
- Standard SMTP codes (4xx, 5xx)
- Enhanced status codes (X.Y.Z format)
- Category and severity mapping

## Testing Strategy

### Recommended Test Coverage

1. **Unit Tests**
   - EmailParser: Header parsing, body extraction, DSN parsing
   - DiagnosticExtractor: SMTP code extraction, pattern matching
   - BounceClassifier: Classification accuracy, confidence scoring

2. **Integration Tests**
   - Full pipeline processing
   - Multiple bounce types
   - Edge cases and malformed emails

3. **Performance Tests**
   - Large email processing
   - Bulk analysis performance
   - Memory usage profiling

4. **UI Tests**
   - Streamlit component rendering
   - Export functionality
   - Session state management

## Deployment Architecture

### Development Environment
```
Local Machine → Streamlit Dev Server → Browser
```

### Production Environment (Recommended)
```
User → Load Balancer → Streamlit Apps (N instances) → Redis Cache → PostgreSQL
```

### Cloud Deployment Options
1. **AWS**: ECS + RDS + ElastiCache
2. **Azure**: App Service + Azure DB + Redis Cache
3. **GCP**: Cloud Run + Cloud SQL + Memorystore

## Monitoring and Observability

### Key Metrics to Track
- Classification accuracy rate
- Processing time per email
- Pattern match distribution
- Error rate by type
- User interaction patterns

### Logging Strategy
- Info: Successful classifications
- Warning: Fallback parsing, low confidence
- Error: Processing failures, exceptions
- Debug: Detailed pattern matching results

## API Extension Design

### Proposed REST API Endpoints

```
POST /api/v1/analyze
  - Analyze single email
  - Input: email content
  - Output: classification + diagnostics

POST /api/v1/batch-analyze
  - Analyze multiple emails
  - Input: array of emails
  - Output: array of results

GET /api/v1/patterns
  - Retrieve pattern definitions

PUT /api/v1/patterns/{pattern_id}
  - Update pattern definition

GET /api/v1/statistics
  - Get system statistics
```

## Version History

### v0.1.0 (Current)
- Initial prototype implementation
- Core classification engine
- Streamlit UI
- Basic export functionality

### Future Versions (Planned)
- v0.2.0: API endpoints
- v0.3.0: Database integration
- v0.4.0: Machine learning classification
- v1.0.0: Production-ready release

---

**Document Version**: 1.0
**Last Updated**: December 2025
**Maintained By**: Development Team
