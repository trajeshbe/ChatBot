# Fashion Image Tagger - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [User Interface Overview](#user-interface-overview)
3. [Step-by-Step Usage](#step-by-step-usage)
4. [Understanding Results](#understanding-results)
5. [Exporting Data](#exporting-data)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Frequently Asked Questions](#frequently-asked-questions)

---

## Getting Started

### System Requirements
Before using the Fashion Image Tagger, ensure you have:
- A modern web browser (Chrome, Firefox, Safari, or Edge)
- Internet connection
- Fashion product images in JPG, JPEG, PNG, or WEBP format

### Accessing the Application
The Fashion Image Tagger is a web-based application that runs in your browser. Simply navigate to the application URL provided by your administrator or deployment platform.

### What to Expect
The Fashion Image Tagger will:
- Analyze your fashion product images using AI
- Extract detailed attributes like color, pattern, material, and style
- Provide product-specific details (sleeve length, neckline, fit, etc.)
- Allow you to export results in JSON or CSV format

---

## User Interface Overview

The application interface is divided into several key sections:

### 1. Header Section
```
👗 Fashion Image Tagger
Automatically extract structured fashion attributes from apparel photos using AI vision analysis
```
This section provides the application title and brief description.

### 2. Upload and Analyze Section (Top Row)

**Left Column - Upload Image**
- File uploader control
- Supports JPG, JPEG, PNG, WEBP formats
- Drag-and-drop or click to browse

**Right Column - Analyze Button**
- Appears only when an image is uploaded
- Click to start AI analysis
- Shows loading spinner during processing

### 3. Results Section (Bottom Row)

**Left Column - Image Preview**
- Displays thumbnail of uploaded image (300px width)
- Shows "No image uploaded" when empty

**Right Column - Analysis Results**
- **Basic Info**: Gender and product type
- **Key Attributes**: Color, pattern, material, style
- **Product Details**: Product-specific attributes
- **Export Buttons**: JSON and CSV download options
- **View Full Details**: Expandable section with complete JSON

### 4. Information Section (Footer)
Explains how the system works with three key points:
- AI Vision Analysis
- Structured Ontology
- Structured Output

---

## Step-by-Step Usage

### Step 1: Upload an Image

1. Locate the **Upload Image** section on the left side
2. Click on **"Choose a fashion product image..."** or drag an image into the upload area
3. Select your fashion product image from your computer
4. The image preview will appear in the bottom-left section

**Supported Formats:**
- JPG / JPEG
- PNG
- WEBP

**Image Requirements:**
- Single fashion product (not outfit compositions)
- Clear, well-lit photograph
- Product should be the main focus
- Recommended: White or neutral background
- Minimum resolution: 640x480 pixels
- Maximum file size: Typically 5-10 MB

### Step 2: Analyze the Image

1. After uploading, the **Analyze** button will become active in the right column
2. Click the **"🔍 Analyze Image"** button
3. Wait for the analysis to complete (typically 2-5 seconds)
4. A success message will appear: **"✅ Analysis completed successfully!"**
5. Results will automatically display in the bottom-right section

**During Analysis:**
- A loading spinner appears with message "Analyzing fashion attributes..."
- The application is communicating with AI vision model
- Do not close the browser during this process

### Step 3: Review Results

Once analysis is complete, results appear in the **Analysis Results** section with:

**Basic Info Section:**
- Gender classification (Man/Woman/Boy/Girl/Unisex)
- Product type (Topwear/Bottomwear/Dresses/etc.)

**Key Attributes Section:**
- Color (e.g., Blue, Burgundy, Navy)
- Pattern (e.g., Solid, Striped, Printed)
- Material (e.g., Cotton, Denim, Silk)
- Style (e.g., Casual, Formal, Party)

**Product Details Section:**
Varies by product type. Examples:
- **Topwear**: SleeveLength, Neckline, Fit
- **Dresses**: DressLength, SleeveType
- **Footwear**: HeelType, ToeStyle, ClosureType

### Step 4: Export Results (Optional)

Choose your preferred export format:

**JSON Export:**
1. Click the **"JSON"** button in the Export section
2. File downloads as `fashion_tags.json`
3. Structured, hierarchical format
4. Ideal for API integration or programming

**CSV Export:**
1. Click the **"CSV"** button in the Export section
2. File downloads as `fashion_tags.csv`
3. Flattened, spreadsheet-friendly format
4. Ideal for Excel or data analysis tools

---

## Understanding Results

### Gender Classification

The system identifies the target demographic for the fashion item:

| Value | Description | Examples |
|-------|-------------|----------|
| Man | Masculine cuts, men's styles | Men's shirts, trousers, suits |
| Woman | Feminine cuts, women's styles | Women's dresses, blouses, skirts |
| Boy | Child-sized masculine items | Boys' t-shirts, shorts |
| Girl | Child-sized feminine items | Girls' dresses, skirts |
| Unisex | Gender-neutral designs | Plain t-shirts, hoodies, sneakers |

### Product Type Categories

The system classifies items into seven main categories:

| Product Type | Description | Examples |
|--------------|-------------|----------|
| Topwear | Upper body garments | T-shirts, shirts, blouses, sweaters |
| Bottomwear | Lower body garments | Jeans, pants, skirts, shorts |
| Dresses | One-piece garments | Maxi dress, cocktail dress, sundress |
| Jumpsuits | One-piece with legs | Rompers, overalls, jumpsuits |
| Footwear | Shoes and boots | Sneakers, heels, sandals, boots |
| Outerwear | Layering garments | Coats, jackets, blazers |
| Accessories | Fashion accessories | Bags, belts, hats, scarves |

### Key Attributes Explained

#### Color (28 Options)
The system identifies specific color shades:

**Basic Colors:**
- Red, Blue, Green, Yellow, Pink, Purple, Orange, Brown, Grey, Black, White

**Specific Shades:**
- Burgundy (deep red), Navy (dark blue), Forest Green (dark green)
- Mustard (dark yellow), Magenta (bright purple), Coral (pink-orange)
- Tan (light brown), Charcoal (dark grey), Beige, Cream (off-white)
- Teal (blue-green), Turquoise (bright blue-green), Maroon (dark red-brown)
- Olive (yellow-green), Gold, Silver

**Multicolor:**
- Used when 3 or more distinct colors are present

#### Pattern (5 Options)

| Pattern | Description | Visual Characteristics |
|---------|-------------|----------------------|
| Solid | Single uniform color | No visible patterns or designs |
| Striped | Parallel lines | Horizontal, vertical, or diagonal lines |
| Printed | Graphics or designs | Logos, images, complex patterns |
| Checked | Grid patterns | Squares, plaids, gingham |
| Floral | Botanical motifs | Flowers, leaves, botanical designs |

#### Material (11 Options)

| Material | Type | Common In | Characteristics |
|----------|------|-----------|----------------|
| Cotton | Natural | T-shirts, casual wear | Breathable, matte finish |
| Denim | Cotton variant | Jeans, jackets | Thick, diagonal weave |
| Polyester | Synthetic | Athletic wear, dresses | Shiny, wrinkle-resistant |
| Leather | Animal hide | Jackets, shoes | Smooth or textured surface |
| Silk | Natural | Formal dresses, blouses | Luxurious, natural sheen |
| Linen | Natural | Summer wear | Textured, casual appearance |
| Rayon | Synthetic | Dresses, blouses | Drapes well, semi-shiny |
| Wool | Natural | Sweaters, coats | Textured, often knitted |
| Cashmere | Wool variant | Luxury sweaters | Soft, fine texture |
| Acrylic | Synthetic | Sweaters, athletic | Wool-like, lightweight |
| Nylon | Synthetic | Athletic, outerwear | Smooth, stretchy |

#### Style (5 Options)

| Style | When Used | Occasions | Examples |
|-------|-----------|-----------|----------|
| Casual | Everyday wear | Daily activities | Jeans & t-shirt, sneakers |
| Formal | Business/dressy | Work, formal events | Suits, dress shirts, heels |
| Party | Festive occasions | Celebrations, nights out | Cocktail dresses, statement pieces |
| Sports | Athletic activities | Exercise, sports | Athletic wear, running shoes |
| Ethnic | Traditional styles | Cultural events | Traditional garments |

### Product-Specific Attributes

These vary based on the product type identified.

#### For Topwear

**SleeveLength:**
- **Sleeveless**: No sleeves (tank tops, vests)
- **Short**: Above elbow (t-shirts, polo shirts)
- **3/4th**: Between elbow and wrist
- **Full**: To wrist (long sleeves)

**Neckline:**
- **Round Neck**: Circular opening (crew neck)
- **V-Neck**: V-shaped dip in front
- **Polo**: Collar with button opening
- **Boat Neck**: Wide horizontal opening
- **Collared**: Formal collar structure

**Fit:**
- **Slim**: Close-fitting, tailored
- **Regular**: Standard, comfortable fit
- **Oversized**: Loose, relaxed fit

#### For Bottomwear

**Length:**
- **Short**: Above knee (shorts)
- **Ankle**: Ends at ankle (ankle pants)
- **Full**: Full length (standard pants)

**Fit:**
- **Slim**: Close-fitting, tapered
- **Straight**: Consistent width
- **Relaxed**: Comfortable, loose
- **Flared**: Widens at bottom

**WaistRise:**
- **Low Rise**: Below natural waist
- **Mid Rise**: At natural waist
- **High Rise**: Above natural waist

#### For Dresses

**DressLength:**
- **Mini**: Above knee
- **Knee Length**: At or just below knee
- **Midi**: Between knee and ankle
- **Maxi**: Full length, to floor

**SleeveType:**
- **Sleeveless**: No sleeves
- **Short**: Standard short sleeves
- **3/4th**: Three-quarter sleeves
- **Full**: Long sleeves to wrist
- **Cap**: Very short, covers shoulder
- **Puff**: Gathered, voluminous short sleeves
- **Bell**: Flared sleeves widening at wrist

#### For Jumpsuits

**SleeveType:** Sleeveless, Short, 3/4th, Full

**Neckline:**
- **Round Neck**: Circular opening
- **V-Neck**: V-shaped opening
- **Halter**: Straps tied around neck
- **Strapless**: Tube-style, no straps
- **Overall**: Dungaree-style with shoulder straps
- **Square Neck**: Straight horizontal neckline

**Length:** Short, Ankle, Full

**Fit:** Slim, Regular, Wide Leg

#### For Footwear

**HeelType:**
- **Flat**: No heel elevation
- **Block**: Thick, square heel
- **Wedge**: Triangular solid heel
- **Stiletto**: Thin, high heel

**ToeStyle:**
- **Round**: Rounded toe box
- **Pointed**: Pointed toe
- **Open**: Open-toe design
- **Square**: Square toe box

**ClosureType:**
- **Slip-On**: No fasteners
- **Laces**: Laced shoes
- **Buckle**: Buckle closure
- **Velcro**: Hook-and-loop fastener

#### For Outerwear

**ClosureType:**
- **Buttoned**: Button closure
- **Zipped**: Zipper closure
- **Open Front**: No closure

**CollarStyle:**
- **Lapel**: Folded collar (suit style)
- **Mandarin**: Stand-up collar
- **Shawl**: Rounded lapel
- **Hooded**: Hood attached

### Null Values

When an attribute shows as "Not detected" or null:
- The AI could not determine the value with confidence
- The attribute may not be visible in the image
- The item may not have that specific feature
- Better image quality or angle may improve detection

---

## Exporting Data

### JSON Format

**Structure:**
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

**Best For:**
- API integration
- Database imports
- Programming and automation
- Preserving hierarchical structure

**How to Use:**
1. Click "JSON" button
2. File downloads to your computer
3. Open in text editor or JSON viewer
4. Import into your application or database

### CSV Format

**Structure:**
```csv
Gender,ProductType,KeyAttributes_Color,KeyAttributes_Pattern,KeyAttributes_Material,KeyAttributes_Style,ProductSpecific_DressLength,ProductSpecific_SleeveType
Woman,Dresses,Navy,Solid,Cotton,Casual,Midi,Short
```

**Best For:**
- Spreadsheet analysis (Excel, Google Sheets)
- Data aggregation
- Bulk import to inventory systems
- Simple data manipulation

**How to Use:**
1. Click "CSV" button
2. File downloads to your computer
3. Open in Excel, Google Sheets, or text editor
4. Each attribute becomes a separate column

### Batch Export Workflow

For analyzing multiple images:
1. Upload and analyze first image
2. Export results (JSON or CSV)
3. Rename downloaded file (e.g., `product_001.json`)
4. Upload next image
5. Repeat process
6. Combine CSV files or JSON objects as needed

---

## Best Practices

### Image Quality Guidelines

**✅ Do:**
- Use high-resolution images (minimum 640x480)
- Ensure good lighting (natural or studio lighting)
- Position product as main subject
- Use neutral or white backgrounds when possible
- Photograph item flat or on mannequin
- Capture full product (not cropped)
- Use front-facing views

**❌ Don't:**
- Use blurry or pixelated images
- Upload images with poor lighting
- Include multiple products in one image
- Use heavily filtered or edited photos
- Crop out important product details
- Use extreme angles
- Include busy or distracting backgrounds

### Image Type Recommendations

| Product Type | Best Image Angle | Notes |
|--------------|-----------------|-------|
| Topwear | Front view, flat lay | Show neckline and sleeve clearly |
| Bottomwear | Front view | Show full length and waist |
| Dresses | Front view, on model/mannequin | Show full length and details |
| Footwear | Side view | Show heel and toe clearly |
| Outerwear | Front view | Show collar and closure type |
| Accessories | Clear product shot | Minimize background |

### Maximizing Accuracy

1. **Single Product Focus**: Upload images with one product at a time
2. **Clear Details**: Ensure fabric texture and colors are visible
3. **Standard Angles**: Use conventional product photography angles
4. **Minimal Editing**: Avoid heavy filters that alter colors
5. **Complete Views**: Show entire product, not partial views

### Common Issues to Avoid

| Issue | Impact | Solution |
|-------|--------|----------|
| Low resolution | Reduced detail detection | Use images >1000px width |
| Poor lighting | Incorrect color detection | Use well-lit photos |
| Multiple items | Confused analysis | Upload single product only |
| Extreme cropping | Missing attributes | Show complete product |
| Heavy filtering | Color/material errors | Use natural, unfiltered images |

---

## Troubleshooting

### Common Problems and Solutions

#### "Failed to initialize Fashion Analyzer"
**Cause:** Missing configuration or API key issue
**Solution:** Contact your administrator to verify OpenAI API key is configured

#### "Analysis failed" Error
**Cause:** Network issue, API timeout, or invalid image
**Solutions:**
- Check internet connection
- Try uploading a different image
- Ensure image is in supported format (JPG, PNG, WEBP)
- Verify image file is not corrupted
- Refresh the page and try again

#### Image Won't Upload
**Causes and Solutions:**
- File too large → Resize image to <5MB
- Unsupported format → Convert to JPG or PNG
- Browser issue → Try different browser or clear cache

#### Results Show Many "Not detected" Values
**Causes and Solutions:**
- Image quality too low → Use higher resolution image
- Product not clearly visible → Improve lighting or angle
- Product type unusual → System may not recognize specialty items
- Partial product view → Upload image showing complete product

#### Export Buttons Don't Work
**Causes and Solutions:**
- No analysis performed yet → Analyze an image first
- Browser blocking downloads → Check browser download settings
- Session expired → Refresh page and re-analyze

#### Wrong Attributes Detected
**Causes and Solutions:**
- Poor image quality → Use clearer, better-lit images
- Unusual product design → System trained on common styles
- Color distortion → Ensure natural color representation
- Try different product angle or lighting

### Browser Compatibility

**Recommended Browsers:**
- Google Chrome (latest version)
- Mozilla Firefox (latest version)
- Safari (latest version)
- Microsoft Edge (latest version)

**Not Supported:**
- Internet Explorer
- Very old browser versions

### Performance Issues

**Slow Analysis:**
- Normal processing: 2-5 seconds
- If longer: Check internet speed
- Try during off-peak hours
- Contact administrator if persistent

**Page Loading Slowly:**
- Clear browser cache
- Close unnecessary browser tabs
- Check internet connection
- Try incognito/private browsing mode

---

## Frequently Asked Questions

### General Questions

**Q: How accurate is the Fashion Image Tagger?**
A: Accuracy depends on image quality and product type. For clear, well-photographed standard fashion items, accuracy typically exceeds 85-90%. Unusual or specialty items may have lower accuracy.

**Q: Can I analyze multiple images at once?**
A: Currently, the system processes one image at a time. Upload and analyze images sequentially.

**Q: How long does analysis take?**
A: Typically 2-5 seconds per image, depending on internet speed and API response time.

**Q: Are my images stored or saved?**
A: No, images are only processed temporarily and not stored on servers. Once you close the browser, all data is cleared.

**Q: What happens to my data?**
A: Images are sent to OpenAI's API for analysis and then discarded. No permanent storage occurs.

### Technical Questions

**Q: What image formats are supported?**
A: JPG, JPEG, PNG, and WEBP formats are supported.

**Q: What's the maximum file size?**
A: While there's no hard limit, images under 5-10 MB work best for optimal performance.

**Q: Can I use this offline?**
A: No, the application requires internet connection to communicate with AI vision services.

**Q: Does this work on mobile devices?**
A: Yes, the web interface is accessible on mobile browsers, though desktop use is recommended for better experience.

### Results and Export Questions

**Q: What does "null" or "Not detected" mean?**
A: The AI could not determine that attribute with confidence. This may occur if the feature is not visible or the image quality is insufficient.

**Q: Can I edit the results before exporting?**
A: Currently, results cannot be edited within the application. Export the data and edit in your preferred tool.

**Q: What's the difference between JSON and CSV export?**
A: JSON preserves the hierarchical structure and is better for programming. CSV is flat and better for spreadsheets.

**Q: Can I import results into my e-commerce platform?**
A: Yes, use the JSON export format for most API integrations. Consult your platform's documentation for import procedures.

### Usage Questions

**Q: Can I analyze outfits with multiple items?**
A: No, the system is designed for single product analysis. Analyze each item separately.

**Q: Will it work for jewelry or small accessories?**
A: The system can analyze accessories, but detection may be limited. Large, clearly visible accessories work best.

**Q: Can I analyze vintage or unusual fashion items?**
A: Yes, but accuracy may vary for highly unusual or specialty items. The system is trained on contemporary fashion.

**Q: Does it work for children's clothing?**
A: Yes, the system includes "Boy" and "Girl" gender classifications for children's fashion.

### Cost and Access Questions

**Q: Is there a usage limit?**
A: This depends on your deployment configuration. Contact your administrator for details on usage limits.

**Q: How much does each analysis cost?**
A: Costs vary based on OpenAI API pricing (approximately $0.01-0.03 per image). Check with your administrator.

---

## Getting Help

### Support Resources

**For Technical Issues:**
- Contact your system administrator
- Check that internet connection is stable
- Try different browser or clear cache
- Provide specific error messages when reporting issues

**For Questions About Results:**
- Review this user guide's "Understanding Results" section
- Consider image quality improvements
- Try analyzing with different product angle
- Compare with similar successful analyses

**For Feature Requests:**
- Document your use case and requirements
- Contact your administrator or product team
- Provide examples of desired functionality

---

## Conclusion

The Fashion Image Tagger is a powerful tool for automating fashion product attribute extraction. By following the best practices outlined in this guide, you can achieve highly accurate results that streamline your fashion cataloging workflow.

**Key Takeaways:**
- Use high-quality, well-lit product images
- Upload one product at a time
- Review results for completeness
- Export in your preferred format (JSON or CSV)
- Contact support if issues persist

Happy tagging!
