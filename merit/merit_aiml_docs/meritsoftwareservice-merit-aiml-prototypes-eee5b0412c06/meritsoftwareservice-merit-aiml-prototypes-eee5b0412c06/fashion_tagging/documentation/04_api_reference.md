# Fashion Image Tagger - API Reference

## Table of Contents
1. [Overview](#overview)
2. [FashionAnalyzer Class](#fashionanalyzer-class)
3. [Public Methods](#public-methods)
4. [Private Methods](#private-methods)
5. [Data Structures](#data-structures)
6. [Fashion Ontology Schema](#fashion-ontology-schema)
7. [Error Handling](#error-handling)
8. [Code Examples](#code-examples)
9. [Integration Guide](#integration-guide)

---

## Overview

The Fashion Image Tagger exposes its functionality through the `FashionAnalyzer` class, which provides methods for analyzing fashion images, validating results, and exporting data in various formats.

### Module Information
- **Module Name**: `fashion_analyzer.py`
- **Class**: `FashionAnalyzer`
- **Dependencies**: `openai`, `json`, `os`, `base64`
- **Python Version**: 3.11+

### Quick Start

```python
from fashion_analyzer import FashionAnalyzer

# Initialize analyzer
analyzer = FashionAnalyzer()

# Load image
with open('product.jpg', 'rb') as f:
    image_bytes = f.read()

# Analyze image
result = analyzer.analyze_image(image_bytes)

# Export results
json_output = analyzer.export_to_json(result)
csv_output = analyzer.export_to_csv_format(result)
```

---

## FashionAnalyzer Class

### Class Definition

```python
class FashionAnalyzer:
    """
    Fashion image analysis engine using OpenAI's GPT-4o Vision model.

    Analyzes fashion product images and extracts structured attributes
    according to a predefined fashion ontology.
    """
```

### Constructor

#### `__init__(self)`

Initializes the FashionAnalyzer with OpenAI client and fashion ontology.

**Parameters:**
- None

**Returns:**
- None

**Raises:**
- `Exception`: If OPENAI_API_KEY environment variable is not set
- `FileNotFoundError`: If fashion_ontology.json file is not found
- `json.JSONDecodeError`: If fashion_ontology.json has invalid JSON

**Example:**
```python
import os
os.environ['OPENAI_API_KEY'] = 'sk-...'

analyzer = FashionAnalyzer()
```

**Instance Attributes:**
- `self.client`: OpenAI client instance
- `self.ontology`: Dictionary containing fashion taxonomy

**Environment Variables Required:**
- `OPENAI_API_KEY`: OpenAI API key with GPT-4o access

---

## Public Methods

### analyze_image()

#### `analyze_image(self, image_bytes: bytes) -> Dict[str, Any]`

Analyzes a fashion image and returns structured attributes.

**Parameters:**
- `image_bytes` (bytes): Raw image bytes (JPG, PNG, WEBP)

**Returns:**
- `Dict[str, Any]`: Validated analysis result with structure:
  ```python
  {
      "Gender": str | None,
      "ProductType": str | None,
      "KeyAttributes": {
          "Color": str | None,
          "Pattern": str | None,
          "Material": str | None,
          "Style": str | None
      },
      "ProductSpecificAttributes": {
          # Varies by ProductType
      }
  }
  ```

**Raises:**
- `json.JSONDecodeError`: If API returns invalid JSON
- `Exception`: For API errors, network issues, or processing failures

**Processing Steps:**
1. Encodes image to base64
2. Generates analysis prompt with ontology
3. Calls OpenAI GPT-4o Vision API
4. Parses JSON response
5. Validates and cleans result
6. Returns structured output

**Example:**
```python
with open('dress.jpg', 'rb') as f:
    image_bytes = f.read()

result = analyzer.analyze_image(image_bytes)
print(result['ProductType'])  # "Dresses"
print(result['KeyAttributes']['Color'])  # "Navy"
```

**API Configuration:**
- Model: `gpt-4o`
- Temperature: `0.1` (low for consistency)
- Max Tokens: `1500`
- Top P: `0.9`
- Response Format: `json_object`
- Image Detail: `high`

---

### get_product_type_attributes()

#### `get_product_type_attributes(self, product_type: str) -> Dict[str, list]`

Returns all possible specific attributes for a given product type.

**Parameters:**
- `product_type` (str): Product type from ontology (e.g., "Topwear", "Dresses")

**Returns:**
- `Dict[str, list]`: Dictionary of attribute names and their possible values
- `{}`: Empty dict if product type not found

**Example:**
```python
topwear_attrs = analyzer.get_product_type_attributes("Topwear")
# Returns:
# {
#     "SleeveLength": ["Sleeveless", "Short", "3/4th", "Full"],
#     "Neckline": ["Round Neck", "V-Neck", "Polo", "Boat Neck", "Collared"],
#     "Fit": ["Slim", "Regular", "Oversized"]
# }

footwear_attrs = analyzer.get_product_type_attributes("Footwear")
# Returns:
# {
#     "HeelType": ["Flat", "Block", "Wedge", "Stiletto"],
#     "ToeStyle": ["Round", "Pointed", "Open", "Square"],
#     "ClosureType": ["Slip-On", "Laces", "Buckle", "Velcro"]
# }
```

---

### get_key_attributes()

#### `get_key_attributes(self) -> Dict[str, list]`

Returns all key attributes that apply to all product types.

**Parameters:**
- None

**Returns:**
- `Dict[str, list]`: Dictionary of key attribute names and their possible values

**Example:**
```python
key_attrs = analyzer.get_key_attributes()
# Returns:
# {
#     "Color": ["Red", "Burgundy", "Blue", "Navy", ...],
#     "Pattern": ["Solid", "Striped", "Printed", "Checked", "Floral"],
#     "Material": ["Cotton", "Denim", "Polyester", ...],
#     "Style": ["Casual", "Formal", "Party", "Sports", "Ethnic"]
# }
```

---

### export_to_json()

#### `export_to_json(self, analysis_result: Dict[str, Any], filename: str = "fashion_tags.json") -> str`

Exports analysis result to JSON format.

**Parameters:**
- `analysis_result` (Dict[str, Any]): Analysis result from `analyze_image()`
- `filename` (str, optional): Filename for export (not used in return, for reference only)

**Returns:**
- `str`: Formatted JSON string with indentation

**Raises:**
- `Exception`: If JSON serialization fails

**Example:**
```python
result = analyzer.analyze_image(image_bytes)
json_output = analyzer.export_to_json(result)

# Save to file
with open('output.json', 'w') as f:
    f.write(json_output)

# Or parse
import json
data = json.loads(json_output)
```

**Output Format:**
```json
{
  "Gender": "Woman",
  "ProductType": "Dresses",
  "KeyAttributes": {
    "Color": "Navy",
    "Pattern": "Solid",
    "Material": "Cotton",
    "Style": "Casual"
  },
  "ProductSpecificAttributes": {
    "DressLength": "Midi",
    "SleeveType": "Short"
  }
}
```

---

### export_to_csv_format()

#### `export_to_csv_format(self, analysis_result: Dict[str, Any]) -> str`

Exports analysis result to CSV format (flattened structure).

**Parameters:**
- `analysis_result` (Dict[str, Any]): Analysis result from `analyze_image()`

**Returns:**
- `str`: CSV string with header and data rows

**Raises:**
- `Exception`: If CSV formatting fails

**Example:**
```python
result = analyzer.analyze_image(image_bytes)
csv_output = analyzer.export_to_csv_format(result)

# Save to file
with open('output.csv', 'w') as f:
    f.write(csv_output)
```

**Output Format:**
```csv
Gender,ProductType,KeyAttributes_Color,KeyAttributes_Pattern,KeyAttributes_Material,KeyAttributes_Style,ProductSpecific_DressLength,ProductSpecific_SleeveType
Woman,Dresses,Navy,Solid,Cotton,Casual,Midi,Short
```

**Column Naming Convention:**
- Basic attributes: `Gender`, `ProductType`
- Key attributes: `KeyAttributes_{AttributeName}`
- Product-specific: `ProductSpecific_{AttributeName}`

---

## Private Methods

### _load_ontology()

#### `_load_ontology(self) -> Dict[str, Any]`

Loads the fashion ontology from JSON file.

**Parameters:**
- None

**Returns:**
- `Dict[str, Any]`: Complete ontology dictionary

**Raises:**
- `FileNotFoundError`: If fashion_ontology.json not found
- `json.JSONDecodeError`: If JSON is malformed

**File Location:**
- Must be in same directory as fashion_analyzer.py
- Filename: `fashion_ontology.json`

---

### _encode_image_to_base64()

#### `_encode_image_to_base64(self, image_bytes: bytes) -> str`

Converts image bytes to base64 string for API transmission.

**Parameters:**
- `image_bytes` (bytes): Raw image data

**Returns:**
- `str`: Base64-encoded string

**Example:**
```python
with open('image.jpg', 'rb') as f:
    image_bytes = f.read()

base64_str = analyzer._encode_image_to_base64(image_bytes)
# Returns: "iVBORw0KGgoAAAANSUhEUgAA..."
```

---

### _create_analysis_prompt()

#### `_create_analysis_prompt(self) -> str`

Creates a comprehensive prompt for fashion image analysis.

**Parameters:**
- None

**Returns:**
- `str`: 230-line detailed analysis prompt

**Prompt Structure:**
1. Expert role definition
2. Analysis methodology (5 steps)
3. Step 1: Basic attributes
4. Step 2: Key attributes
5. Step 3: Product-specific attributes
6. Critical accuracy rules
7. Special attention sections
8. Mandatory JSON structure
9. Mandatory attribute requirements

**Prompt Engineering Techniques:**
- Few-shot learning examples within descriptions
- Explicit value definitions
- Mandatory field enforcement
- Edge case handling
- Consistency rule reminders

---

### _validate_and_clean_result()

#### `_validate_and_clean_result(self, result: Dict[str, Any]) -> Dict[str, Any]`

Validates AI result against ontology and cleans invalid values.

**Parameters:**
- `result` (Dict[str, Any]): Raw result from OpenAI API

**Returns:**
- `Dict[str, Any]`: Validated and cleaned result

**Validation Steps:**
1. Initialize validated structure with all fields
2. Validate Gender against ontology
3. Validate ProductType against ontology
4. Validate each KeyAttribute
5. Validate ProductSpecificAttributes based on ProductType
6. Apply normalization for variations
7. Apply consistency rules

**Normalization Applied:**
- Case-insensitive matching
- Common variation mapping (e.g., "long sleeve" → "Full")
- Partial string matching with similarity threshold
- Null conversion for invalid/uncertain values

---

### _normalize_attribute_value()

#### `_normalize_attribute_value(self, value: str, valid_options: list) -> Optional[str]`

Normalizes attribute values to handle case variations and synonyms.

**Parameters:**
- `value` (str): Raw attribute value from API
- `valid_options` (list): List of valid values from ontology

**Returns:**
- `str`: Normalized value from ontology
- `None`: If no valid match found

**Normalization Strategy:**
1. Exact match (case-insensitive)
2. Common mapping lookup (42 predefined)
3. Partial match (>50% similarity)
4. Return None if no match

**Common Mappings (Selected):**

| Input | Output | Category |
|-------|--------|----------|
| short sleeve, half sleeve, t-shirt sleeve | Short | Sleeve |
| long sleeve, full sleeve | Full | Sleeve |
| 3/4 sleeve, three quarter | 3/4th | Sleeve |
| navy, navy blue, dark blue | Blue | Color |
| gray, silver | Grey | Color |
| plain | Solid | Pattern |
| checkered, check | Checked | Pattern |
| cotton blend | Cotton | Material |
| poly | Polyester | Material |
| faux leather | Leather | Material |

---

### _apply_consistency_rules_new_schema()

#### `_apply_consistency_rules_new_schema(self, result: Dict[str, Any]) -> Dict[str, Any]`

Applies logical consistency rules to improve accuracy.

**Parameters:**
- `result` (Dict[str, Any]): Validated result before consistency checks

**Returns:**
- `Dict[str, Any]`: Result with consistency rules applied

**Rules Applied:**

| Product Type | Rule | Correction |
|-------------|------|------------|
| Topwear | Neckline="Polo" | Convert to "Collared" |
| Topwear | SleeveLength missing | Set to None (mandatory) |
| Dresses | SleeveType missing | Set to None (mandatory) |
| Footwear | ToeStyle missing + HeelType="Flat" | Infer "Round" |
| Outerwear | Style="Sports" | Convert to "Casual" |

---

## Data Structures

### Analysis Result Structure

```python
{
    "Gender": str | None,  # "Man", "Woman", "Boy", "Girl", "Unisex"
    "ProductType": str | None,  # "Topwear", "Bottomwear", "Dresses", etc.
    "KeyAttributes": {
        "Color": str | None,  # 28 possible values
        "Pattern": str | None,  # 5 possible values
        "Material": str | None,  # 11 possible values
        "Style": str | None  # 5 possible values
    },
    "ProductSpecificAttributes": {
        # Dynamic based on ProductType
        # See Product-Specific Attributes section
    }
}
```

### Product-Specific Attributes by Type

#### Topwear
```python
{
    "SleeveLength": str | None,  # "Sleeveless", "Short", "3/4th", "Full"
    "Neckline": str | None,  # "Round Neck", "V-Neck", "Polo", "Boat Neck", "Collared"
    "Fit": str | None  # "Slim", "Regular", "Oversized"
}
```

#### Bottomwear
```python
{
    "Length": str | None,  # "Short", "Ankle", "Full"
    "Fit": str | None,  # "Slim", "Straight", "Relaxed", "Flared"
    "WaistRise": str | None  # "Low Rise", "Mid Rise", "High Rise"
}
```

#### Dresses
```python
{
    "DressLength": str | None,  # "Mini", "Knee Length", "Midi", "Maxi"
    "SleeveType": str | None  # "Sleeveless", "Short", "3/4th", "Full", "Cap", "Puff", "Bell"
}
```

#### Jumpsuits
```python
{
    "SleeveType": str | None,  # "Sleeveless", "Short", "3/4th", "Full"
    "Neckline": str | None,  # "Round Neck", "V-Neck", "Halter", "Strapless", "Overall", "Square Neck"
    "Length": str | None,  # "Short", "Ankle", "Full"
    "Fit": str | None  # "Slim", "Regular", "Wide Leg"
}
```

#### Footwear
```python
{
    "HeelType": str | None,  # "Flat", "Block", "Wedge", "Stiletto"
    "ToeStyle": str | None,  # "Round", "Pointed", "Open", "Square"
    "ClosureType": str | None  # "Slip-On", "Laces", "Buckle", "Velcro"
}
```

#### Outerwear
```python
{
    "ClosureType": str | None,  # "Buttoned", "Zipped", "Open Front"
    "CollarStyle": str | None  # "Lapel", "Mandarin", "Shawl", "Hooded"
}
```

#### Accessories
```python
{}  # No specific attributes defined
```

---

## Fashion Ontology Schema

### Complete Ontology Structure

```json
{
  "Gender": [
    "Man", "Woman", "Boy", "Girl", "Unisex"
  ],
  "ProductType": [
    "Topwear", "Bottomwear", "Dresses", "Jumpsuits",
    "Footwear", "Outerwear", "Accessories"
  ],
  "KeyAttributes": {
    "Color": [
      "Red", "Burgundy", "Blue", "Navy", "Black", "White",
      "Green", "Forest Green", "Yellow", "Mustard",
      "Pink", "Purple", "Magenta", "Orange", "Coral",
      "Brown", "Tan", "Grey", "Charcoal", "Beige", "Cream",
      "Teal", "Turquoise", "Maroon", "Olive", "Gold", "Silver",
      "Multicolor"
    ],
    "Pattern": [
      "Solid", "Striped", "Printed", "Checked", "Floral"
    ],
    "Material": [
      "Cotton", "Denim", "Polyester", "Leather", "Silk",
      "Linen", "Rayon", "Wool", "Cashmere", "Acrylic", "Nylon"
    ],
    "Style": [
      "Casual", "Formal", "Party", "Sports", "Ethnic"
    ]
  },
  "ProductSpecificAttributes": {
    "Topwear": {
      "SleeveLength": ["Sleeveless", "Short", "3/4th", "Full"],
      "Neckline": ["Round Neck", "V-Neck", "Polo", "Boat Neck", "Collared"],
      "Fit": ["Slim", "Regular", "Oversized"]
    },
    "Bottomwear": {
      "Length": ["Short", "Ankle", "Full"],
      "Fit": ["Slim", "Straight", "Relaxed", "Flared"],
      "WaistRise": ["Low Rise", "Mid Rise", "High Rise"]
    },
    "Dresses": {
      "DressLength": ["Mini", "Knee Length", "Midi", "Maxi"],
      "SleeveType": ["Sleeveless", "Short", "3/4th", "Full", "Cap", "Puff", "Bell"]
    },
    "Jumpsuits": {
      "SleeveType": ["Sleeveless", "Short", "3/4th", "Full"],
      "Neckline": ["Round Neck", "V-Neck", "Halter", "Strapless", "Overall", "Square Neck"],
      "Length": ["Short", "Ankle", "Full"],
      "Fit": ["Slim", "Regular", "Wide Leg"]
    },
    "Footwear": {
      "HeelType": ["Flat", "Block", "Wedge", "Stiletto"],
      "ToeStyle": ["Round", "Pointed", "Open", "Square"],
      "ClosureType": ["Slip-On", "Laces", "Buckle", "Velcro"]
    },
    "Outerwear": {
      "ClosureType": ["Buttoned", "Zipped", "Open Front"],
      "CollarStyle": ["Lapel", "Mandarin", "Shawl", "Hooded"]
    },
    "Accessories": {}
  }
}
```

---

## Error Handling

### Exception Types

#### Initialization Errors

**Missing API Key**
```python
Exception: OPENAI_API_KEY environment variable not set
```
**Handling:**
```python
import os
os.environ['OPENAI_API_KEY'] = 'your-key-here'
```

**Missing Ontology File**
```python
FileNotFoundError: Fashion ontology file not found. Please ensure fashion_ontology.json exists.
```
**Handling:**
- Ensure fashion_ontology.json is in the same directory
- Verify file permissions

**Invalid Ontology JSON**
```python
json.JSONDecodeError: Invalid JSON format in fashion ontology file.
```
**Handling:**
- Validate JSON syntax
- Check for trailing commas, quotes

#### Analysis Errors

**API Call Failure**
```python
Exception: Failed to analyze image: [specific error]
```
**Common Causes:**
- Network connectivity issues
- Invalid API key
- Rate limiting
- API service outage

**JSON Parse Failure**
```python
json.JSONDecodeError: Failed to parse AI response as JSON
```
**Causes:**
- API returned non-JSON response
- Malformed JSON in response

### Error Handling Best Practices

```python
from fashion_analyzer import FashionAnalyzer

try:
    analyzer = FashionAnalyzer()
except FileNotFoundError as e:
    print(f"Ontology file missing: {e}")
    exit(1)
except Exception as e:
    print(f"Initialization failed: {e}")
    exit(1)

try:
    with open('product.jpg', 'rb') as f:
        image_bytes = f.read()

    result = analyzer.analyze_image(image_bytes)

except FileNotFoundError:
    print("Image file not found")
except json.JSONDecodeError as e:
    print(f"Invalid response format: {e}")
except Exception as e:
    print(f"Analysis failed: {e}")
```

---

## Code Examples

### Example 1: Basic Analysis

```python
from fashion_analyzer import FashionAnalyzer
import os

# Set API key
os.environ['OPENAI_API_KEY'] = 'sk-...'

# Initialize
analyzer = FashionAnalyzer()

# Load image
with open('dress.jpg', 'rb') as f:
    image_bytes = f.read()

# Analyze
result = analyzer.analyze_image(image_bytes)

# Print results
print(f"Product Type: {result['ProductType']}")
print(f"Color: {result['KeyAttributes']['Color']}")
print(f"Material: {result['KeyAttributes']['Material']}")
```

### Example 2: Batch Processing

```python
import os
from pathlib import Path
from fashion_analyzer import FashionAnalyzer

analyzer = FashionAnalyzer()

# Process all images in directory
image_dir = Path('product_images')
results = []

for image_path in image_dir.glob('*.jpg'):
    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    try:
        result = analyzer.analyze_image(image_bytes)
        results.append({
            'filename': image_path.name,
            'analysis': result
        })
        print(f"Processed: {image_path.name}")
    except Exception as e:
        print(f"Failed: {image_path.name} - {e}")

# Export all results
with open('batch_results.json', 'w') as f:
    import json
    json.dump(results, f, indent=2)
```

### Example 3: Conditional Export

```python
from fashion_analyzer import FashionAnalyzer

analyzer = FashionAnalyzer()

with open('product.jpg', 'rb') as f:
    image_bytes = f.read()

result = analyzer.analyze_image(image_bytes)

# Export only if product type is detected
if result['ProductType']:
    json_output = analyzer.export_to_json(result)
    csv_output = analyzer.export_to_csv_format(result)

    # Save both formats
    with open('output.json', 'w') as f:
        f.write(json_output)

    with open('output.csv', 'w') as f:
        f.write(csv_output)
else:
    print("Product type not detected, skipping export")
```

### Example 4: Custom Filtering

```python
from fashion_analyzer import FashionAnalyzer

analyzer = FashionAnalyzer()

with open('product.jpg', 'rb') as f:
    result = analyzer.analyze_image(f.read())

# Filter only complete results (no null values)
def is_complete(result):
    if not result['Gender'] or not result['ProductType']:
        return False

    key_attrs = result['KeyAttributes']
    if any(v is None for v in key_attrs.values()):
        return False

    product_attrs = result['ProductSpecificAttributes']
    if any(v is None for v in product_attrs.values()):
        return False

    return True

if is_complete(result):
    print("Complete analysis - all attributes detected")
else:
    print("Incomplete analysis - some attributes missing")

    # List missing attributes
    missing = []
    if not result['Gender']:
        missing.append('Gender')
    if not result['ProductType']:
        missing.append('ProductType')

    for k, v in result['KeyAttributes'].items():
        if v is None:
            missing.append(f'KeyAttributes.{k}')

    for k, v in result['ProductSpecificAttributes'].items():
        if v is None:
            missing.append(f'ProductSpecific.{k}')

    print(f"Missing: {', '.join(missing)}")
```

### Example 5: Accessing Ontology

```python
from fashion_analyzer import FashionAnalyzer

analyzer = FashionAnalyzer()

# Get all possible colors
key_attrs = analyzer.get_key_attributes()
print("Available colors:", key_attrs['Color'])

# Get attributes for specific product type
topwear_attrs = analyzer.get_product_type_attributes('Topwear')
print("Topwear sleeve options:", topwear_attrs['SleeveLength'])

# Get attributes for dresses
dress_attrs = analyzer.get_product_type_attributes('Dresses')
print("Dress sleeve options:", dress_attrs['SleeveType'])

# List all product types
print("Product types:", analyzer.ontology['ProductType'])
```

---

## Integration Guide

### Web Application Integration

**Flask Example:**
```python
from flask import Flask, request, jsonify
from fashion_analyzer import FashionAnalyzer

app = Flask(__name__)
analyzer = FashionAnalyzer()

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    image_file = request.files['image']
    image_bytes = image_file.read()

    try:
        result = analyzer.analyze_image(image_bytes)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### Database Integration

**SQLAlchemy Example:**
```python
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fashion_analyzer import FashionAnalyzer

Base = declarative_base()

class FashionProduct(Base):
    __tablename__ = 'fashion_products'

    id = Column(Integer, primary_key=True)
    image_path = Column(String)
    analysis_result = Column(JSON)
    gender = Column(String)
    product_type = Column(String)
    color = Column(String)
    material = Column(String)

engine = create_engine('sqlite:///fashion.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

analyzer = FashionAnalyzer()

def analyze_and_store(image_path):
    with open(image_path, 'rb') as f:
        result = analyzer.analyze_image(f.read())

    product = FashionProduct(
        image_path=image_path,
        analysis_result=result,
        gender=result['Gender'],
        product_type=result['ProductType'],
        color=result['KeyAttributes']['Color'],
        material=result['KeyAttributes']['Material']
    )

    session = Session()
    session.add(product)
    session.commit()
    session.close()
```

### CLI Tool Integration

**argparse Example:**
```python
import argparse
from fashion_analyzer import FashionAnalyzer

def main():
    parser = argparse.ArgumentParser(description='Fashion Image Analyzer CLI')
    parser.add_argument('image', help='Path to fashion image')
    parser.add_argument('--format', choices=['json', 'csv'], default='json')
    parser.add_argument('--output', help='Output file path')

    args = parser.parse_args()

    analyzer = FashionAnalyzer()

    with open(args.image, 'rb') as f:
        result = analyzer.analyze_image(f.read())

    if args.format == 'json':
        output = analyzer.export_to_json(result)
    else:
        output = analyzer.export_to_csv_format(result)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
    else:
        print(output)

if __name__ == '__main__':
    main()
```

---

## Performance Considerations

### API Call Timing
- Average response time: 2-5 seconds
- Depends on: image size, API load, network speed
- Timeout recommendation: 10-15 seconds

### Rate Limiting
- OpenAI API has rate limits
- Implement backoff strategy for production
- Consider queueing for batch processing

### Caching Strategy
```python
import hashlib
import json
from pathlib import Path

class CachedFashionAnalyzer(FashionAnalyzer):
    def __init__(self, cache_dir='cache'):
        super().__init__()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def analyze_image(self, image_bytes):
        # Generate cache key from image hash
        image_hash = hashlib.md5(image_bytes).hexdigest()
        cache_file = self.cache_dir / f"{image_hash}.json"

        # Check cache
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)

        # Analyze and cache
        result = super().analyze_image(image_bytes)

        with open(cache_file, 'w') as f:
            json.dump(result, f)

        return result
```

---

## Version History

### Current Version: 1.0.0

**Recent Updates (2025-07-25):**
- Added Jumpsuits product category
- Expanded material options (Wool, Cashmere, Acrylic, Nylon)
- Fixed neckline detection with mandatory analysis
- Improved sleeve detection for dresses
- Enhanced prompt with detailed guidelines

**Previous Updates (2025-07-24):**
- Implemented new taxonomy structure
- Fixed sleeve type validation for dresses
- Added attribute normalization system
- Enhanced consistency rules

---

## Support and Resources

### Additional Documentation
- User Guide: `03_user_guide.md`
- Technical Architecture: `02_technical_architecture.md`
- Deployment Guide: `05_deployment_guide.md`

### OpenAI API Documentation
- Vision API: https://platform.openai.com/docs/guides/vision
- GPT-4o Model: https://platform.openai.com/docs/models/gpt-4o

### Community and Support
- GitHub Issues: [Repository link]
- Documentation: [Documentation link]
- API Support: OpenAI support portal
