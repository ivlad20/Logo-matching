
# Logo Similarity Grouping – Veridion Challenge

## Task

Group websites based on the similarity of their logos.

## Problem and Motivation

Logos are a crucial part of a brand’s identity. This project aims to extract logos from thousands of websites and group them based on visual similarity, **without using traditional ML clustering algorithms** (e.g., KMeans, DBSCAN).

## Initial Thought Process

The initial idea was to group logos by **average color**, inspired by university coursework in visual processing. While simple and elegant, this method proved insufficient when applied to a dataset of ~3400 domains:

- Many logos share dominant color tones.
- Text in logos provides stronger brand distinction.

I therefore combined:
- **OCR** for extracting text from logos.
- **Average color** as a fallback when no text is detected.

## Solution Architecture

### 1. Logo Extraction (`extract_logos.py`)

This was the most complex part of the project.

**Challenges:**
- Highly inconsistent HTML structures.
- Logos lacked specific tags, but parent elements often had identifiers like `logo` or `brand`.
- Some sites didn't render images in headless mode.
- Incorrect logo matches from cookie banners, social icons, payment badges.
- HTTP-only domains, offline sites, and anti-scraping headers.

**Approach:**
- Used Selenium with a scoring system based on URL patterns, alt/class attributes, and DOM context.
- Combined several methods: DOM search, CSS background-image detection, inline SVG, and network request analysis.

### 2. SVG to PNG Conversion (`convertToPNG.py`)

Converted all SVG logos to PNG using `cairosvg`, with fallbacks for undefined SVG sizes.

### 3. Normalization (`normalise.py`)

- Resized all logos to 256x256 px.
- Centered logos on a magenta background for uniformity.

### 4. Grouping by Text or Color (`compare.py`)

- Used `pytesseract` for OCR text extraction.
- If no text was detected, fallback to grouping by average RGB color.
- Group naming was based on extracted text or representative color.

### 5. HTML Visualization (`generateHTML.py`)

Generated a clean HTML page to browse grouped logos with metadata on grouping basis (text or color).

## Results

- Over **97%** of websites had logos successfully extracted.
- Grouping showed clear patterns based on text or color similarity.
- Logos from the same brand were generally clustered well—if resolution and text visibility allowed.

## Limitations and Observations

- Some logos from the same website were treated as different due to low resolution or minor color variance.
- Low-resolution images impaired both OCR and color detection accuracy.
- Stylized or custom fonts caused OCR to fail.
- Language-specific branding in logos (site localized versions) confused grouping logic.
- Slight hue changes between logos of the same brand led to split groups.
- Some false positives from headers or third-party images.

## Advanced Observations & Future Improvements

- Implement **multithreading** for large-scale scraping.
- Add more robust similarity checks: perceptual hashing (phash), SSIM, or vision embeddings.
- Improve parent-based heuristics to avoid header noise.
- Use webpage language context to adjust OCR expectations.
- Introduce adaptive RGB similarity thresholds.
- Consider geometric vector comparison for SVGs.

## Example Groups

```
Group 001 (7 images) – based on: 'veridion'
Group 003 (4 images) – based on: color_0_0_0
Group 010 (1 image) – based on: '__empty__'
```

## Directory Structure

```
├── extract_logos.py
├── convertToPNG.py
├── normalise.py
├── compare.py
├── generateHTML.py
├── data/
│   └── logos/
│       ├── pngs/
│       ├── svgs/
│       ├── normalised/
│       ├── grouped_by_text_or_color/
│       └── groups.json
```

## How to Run

```bash
# Step 1: Extract logos from websites
python extract_logos.py

# Step 2: Convert SVG logos to PNG
python convertToPNG.py

# Step 3: Resize and normalize all logos
python normalise.py

# Step 4: Group logos based on text or color
python compare.py

# Step 5: Generate a static website to visualize results
python generateHTML.py
```

## Conclusion

This project highlighted the real-world challenges of automating logo extraction and visual grouping. A mix of visual heuristics, OCR, and color analysis proved effective without ML. With further enhancements—scalability, smarter comparison techniques, and better extraction—this pipeline can scale to millions of records.
