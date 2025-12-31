# Fashion Image Tagger

You are an AI assistant specialized in the **Fashion Image Tagger** prototype, an AI-powered web application that automatically extracts structured fashion attributes from apparel photographs.

## Project Overview

The Fashion Image Tagger uses OpenAI's GPT-4o Vision model to analyze fashion images and classify them according to a comprehensive fashion ontology. It provides automated product tagging with 7 product types, 28 colors, 11 materials, and product-specific attributes.

**Location**: `/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/fashion_tagging/`

## Core Capabilities

### Fashion Ontology

**Product Categories** (7):
- Topwear (shirts, blouses, t-shirts, sweaters)
- Bottomwear (pants, jeans, shorts, skirts)
- Dresses (casual, formal, maxi, midi)
- Jumpsuits (one-piece garments)
- Footwear (shoes, boots, sandals, sneakers)
- Outerwear (jackets, coats)
- Accessories (bags, hats, scarves, jewelry)

**Universal Attributes**:
- **Gender**: Man, Woman, Boy, Girl, Unisex (5 options)
- **Color**: 28 specific shades (Red, Blue, Black, White, Navy, etc.)
- **Pattern**: Solid, Striped, Printed, Checked, Floral (5 options)
- **Material**: Cotton, Denim, Silk, Wool, Leather, etc. (11 options)
- **Style**: Casual, Formal, Party, Sports, Ethnic (5 options)

**Product-Specific Attributes** (2-4 per product type):
- Topwear: SleeveLength, Neckline, Fit
- Dresses: DressLength, SleeveType
- Footwear: HeelType, ToeStyle, ClosureType

### Key Features

- Automated attribute extraction from images
- Comprehensive taxonomy (100+ attribute combinations)
- Multiple export formats (JSON, CSV)
- User-friendly Streamlit interface
- High accuracy AI analysis
- No technical knowledge required

## Technology Stack

```
Language: Python 3.11+
Framework: Streamlit 1.47.0+
AI Model: OpenAI GPT-4o Vision
Image Processing: Pillow (PIL)
Configuration: python-dotenv
Data Format: JSON (fashion_ontology.json)
```

## Architecture

### Component Structure

```
app.py                    # Main Streamlit application
fashion_analyzer.py       # AI analysis engine
fashion_ontology.json     # Fashion taxonomy definition
.env                      # API key configuration
pyproject.toml           # Dependencies
```

### Processing Flow

```
Image Upload (JPG, PNG)
  ↓
Image Validation & Processing
  ↓
GPT-4o Vision Analysis
  ↓
Attribute Extraction (Ontology-based)
  ↓
Data Validation & Normalization
  ↓
Results Display
  ↓
Export (JSON/CSV)
```

## Common Implementation Tasks

### 1. Running the Application

```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/fashion_tagging/

# Set API key
export OPENAI_API_KEY="your-api-key"

# Install dependencies
pip install streamlit openai pillow python-dotenv

# Run application
streamlit run app.py
```

### 2. Analyzing a Fashion Image

```python
from fashion_analyzer import FashionAnalyzer

# Initialize analyzer
analyzer = FashionAnalyzer()

# Analyze image
with open('dress_image.jpg', 'rb') as f:
    image_bytes = f.read()
    result = analyzer.analyze_image(image_bytes)

# Result structure:
{
    "Gender": "Woman",
    "ProductType": "Dresses",
    "Color": "Navy Blue",
    "Pattern": "Solid",
    "Material": "Cotton",
    "Style": "Casual",
    "DressLength": "Midi",
    "SleeveType": "Short Sleeve"
}
```

### 3. Exporting Results

```python
# Export as JSON
json_output = analyzer.export_to_json(result)
with open('product_tags.json', 'w') as f:
    f.write(json_output)

# Export as CSV
csv_output = analyzer.export_to_csv_format(result)
with open('product_tags.csv', 'w') as f:
    f.write(csv_output)

# CSV format:
# Gender,ProductType,Color,Pattern,Material,Style,DressLength,SleeveType
# Woman,Dresses,Navy Blue,Solid,Cotton,Casual,Midi,Short Sleeve
```

### 4. Customizing the Fashion Ontology

Edit `fashion_ontology.json`:

```json
{
  "Gender": ["Man", "Woman", "Boy", "Girl", "Unisex"],
  "ProductType": [
    "Topwear",
    "Bottomwear",
    "Dresses",
    "Jumpsuits",
    "Footwear",
    "Outerwear",
    "Accessories"
  ],
  "Color": [
    "Red", "Blue", "Navy Blue", "Black", "White",
    "Grey", "Beige", "Brown", "Green", "Yellow",
    "Pink", "Purple", "Orange", "Multi-Color", ...
  ],
  "ProductAttributes": {
    "Topwear": {
      "SleeveLength": ["Sleeveless", "Short Sleeve", "3/4 Sleeve", "Long Sleeve"],
      "Neckline": ["Round Neck", "V-Neck", "Collar", "Boat Neck", "High Neck"],
      "Fit": ["Regular", "Slim", "Loose", "Oversized"]
    },
    "Dresses": {
      "DressLength": ["Mini", "Knee-Length", "Midi", "Maxi"],
      "SleeveType": ["Sleeveless", "Short Sleeve", "3/4 Sleeve", "Long Sleeve"]
    }
  }
}
```

### 5. Adding a New Product Type

```python
# 1. Update fashion_ontology.json
"ProductType": [..., "NewCategory"],
"ProductAttributes": {
  "NewCategory": {
    "Attribute1": ["Option1", "Option2"],
    "Attribute2": ["Option1", "Option2"]
  }
}

# 2. Update AI prompt in fashion_analyzer.py
prompt = f"""
...
For {product_type}:
- Attribute1: {options}
- Attribute2: {options}
"""

# 3. Update validation logic
def validate_result(result):
    if result['ProductType'] == 'NewCategory':
        assert 'Attribute1' in result
        assert 'Attribute2' in result
```

## AI Analysis Process

### Prompt Engineering

```python
def build_analysis_prompt(image_path):
    """Build GPT-4o Vision prompt"""

    prompt = """
    Analyze this fashion/apparel image and extract the following attributes:

    1. Gender: Man, Woman, Boy, Girl, or Unisex
    2. ProductType: Topwear, Bottomwear, Dresses, Jumpsuits, Footwear, Outerwear, or Accessories
    3. Color: Primary color (e.g., Red, Navy Blue, Black, White)
    4. Pattern: Solid, Striped, Printed, Checked, or Floral
    5. Material: Best guess (Cotton, Denim, Silk, Wool, Leather, etc.)
    6. Style: Casual, Formal, Party, Sports, or Ethnic

    For the identified ProductType, also specify:
    - For Topwear: SleeveLength, Neckline, Fit
    - For Dresses: DressLength, SleeveType
    - For Footwear: HeelType, ToeStyle, ClosureType
    [... other product types ...]

    Return ONLY a JSON object with these exact field names.
    Use "N/A" if an attribute cannot be determined.
    """

    return prompt
```

### Response Validation

```python
def validate_and_normalize(result):
    """Validate AI response against ontology"""

    ontology = load_ontology()

    # Validate Gender
    if result['Gender'] not in ontology['Gender']:
        result['Gender'] = 'Unisex'  # Default

    # Validate ProductType
    if result['ProductType'] not in ontology['ProductType']:
        result['ProductType'] = 'Unknown'

    # Validate Color
    if result['Color'] not in ontology['Color']:
        # Find closest match
        result['Color'] = find_closest_color(result['Color'], ontology['Color'])

    # Validate product-specific attributes
    if result['ProductType'] in ontology['ProductAttributes']:
        required_attrs = ontology['ProductAttributes'][result['ProductType']]

        for attr, valid_values in required_attrs.items():
            if attr in result and result[attr] not in valid_values:
                result[attr] = valid_values[0]  # Use first valid option

    return result
```

## Best Practices

### Image Quality

1. **Resolution**: Minimum 500x500 pixels
2. **Clarity**: Clear, well-lit product images
3. **Background**: Plain backgrounds work best
4. **Framing**: Full product visible in frame
5. **Angle**: Front-facing or standard product shots

### Accuracy Optimization

1. **Image Quality**: Higher quality = better accuracy
2. **Ontology Precision**: Well-defined attribute options
3. **Prompt Clarity**: Detailed, specific instructions
4. **Validation**: Always review AI outputs
5. **Feedback Loop**: Refine based on results

### Batch Processing

```python
import os

def batch_analyze_images(image_dir):
    """Analyze multiple fashion images"""

    analyzer = FashionAnalyzer()
    results = []

    for filename in os.listdir(image_dir):
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            filepath = os.path.join(image_dir, filename)

            with open(filepath, 'rb') as f:
                result = analyzer.analyze_image(f.read())
                result['filename'] = filename
                results.append(result)

    # Export all results
    import pandas as pd
    df = pd.DataFrame(results)
    df.to_csv('batch_analysis_results.csv', index=False)

    return results
```

## Use Cases

### E-Commerce Product Cataloging

```python
# Automated product tagging pipeline
def catalog_product(product_image):
    """Tag product for e-commerce catalog"""

    analyzer = FashionAnalyzer()
    tags = analyzer.analyze_image(product_image)

    # Generate product metadata
    metadata = {
        'title': f"{tags['Gender']} {tags['ProductType']} - {tags['Color']}",
        'category': tags['ProductType'],
        'tags': [tags['Color'], tags['Style'], tags['Material']],
        'attributes': tags
    }

    return metadata
```

### Quality Assurance

```python
def verify_manual_tags(image, manual_tags):
    """Verify manually entered tags against AI analysis"""

    analyzer = FashionAnalyzer()
    ai_tags = analyzer.analyze_image(image)

    discrepancies = []

    for key in manual_tags:
        if key in ai_tags and manual_tags[key] != ai_tags[key]:
            discrepancies.append({
                'attribute': key,
                'manual': manual_tags[key],
                'ai': ai_tags[key]
            })

    return {
        'match': len(discrepancies) == 0,
        'discrepancies': discrepancies
    }
```

## Business Value

### Time and Cost Savings

- **Manual Tagging**: 2-3 minutes per product
- **Automated Tagging**: 3-5 seconds per product
- **Time Savings**: 95%+
- **Accuracy**: 85-90% (with review)

### Scalability

- Process thousands of products daily
- Consistent tagging standards
- Reduced human error
- Faster catalog updates

## Documentation References

**Comprehensive Documentation**: `/documentation/` folder
- `README.md`: Documentation index
- `01_overview.md`: System overview
- `02_technical_architecture.md`: Architecture
- `03_user_guide.md`: User guide
- `04_api_reference.md`: API documentation
- `05_deployment_guide.md`: Deployment

**Project Status**: Production-ready
**Last Updated**: December 2025
