# Logo-matching
Logo Similarity Grouping – Veridion Challenge
Task
Group websites based on the similarity of their logos.

Problem and Motivation
Logos are a crucial part of a brand’s identity. This project aims to extract logos from thousands of websites and group them based on visual similarity, without using traditional ML clustering algorithms (e.g., KMeans, DBSCAN).

Initial Thought Process
My initial idea was to group logos solely by average color, inspired by visual processing techniques learned during university courses. This seemed simple, fast, and scalable.

However, after analyzing the dataset (~3400 domains), I realized that:

Many logos share dominant background colors.

The most distinctive feature of logos is often text (brand name, initials, etc.).

So I decided to combine:

OCR (Optical Character Recognition) to extract text,

and average color as a fallback when no text was detected.

Solution Architecture
1. Logo Extraction (extract_logos.py)
This was by far the most complex component.

Major challenges encountered:

Websites vary drastically in structure.

Logos often don’t have obvious tags (logo, brand), but their parent elements do.

Some websites don’t load images in headless Selenium.

Logos were sometimes mistakenly extracted from cookie banners, payment badges (Visa, Mastercard), or social media.

Many domains were offline or only supported HTTP.

Some sites blocked requests unless proper HTTP headers were sent.

Solution highlights:

Selenium-based scraping with a scoring system to evaluate image relevance.

Multiple complementary methods:

XPath DOM search,

CSS background-image extraction,

inline SVG handling,

analysis of network requests.

2. SVG to PNG Conversion (convertToPNG.py)
All SVGs were converted to PNG using cairosvg, including fallback for undefined SVG sizes.

3. Normalization (normalise.py)
All logos were resized to 256×256 px.

Each image was centered on a fixed background (magenta) for uniformity.

4. Grouping by Text or Color (compare.py)
Used pytesseract to extract text via OCR.

If OCR failed, fallback was to group by average RGB color.

Grouping was done based on identical text or similar color values.

5. HTML Visualization (generateHTML.py)
A static HTML page was generated to visualize logo groups.

Each group was labeled by its similarity method (text or color-based).

Results
Successfully extracted logos for over 97% of the websites.

Groupings were consistent and meaningful in most cases.

Clear similarities emerged when logos shared textual or visual elements.

Limitations and Observations
Some incorrect extractions occurred (e.g., cookie banners, Visa logos).

Low-resolution logos couldn’t be reliably processed via OCR or color analysis.

Stylized or distorted fonts significantly reduced OCR accuracy.

Some websites displayed language-specific logos (e.g., localized text), which caused the same brand to be split into separate groups.

Logos from the same company with slight color tone variations were rarely grouped together due to strict RGB tolerance.

Multiple logos from the same website were sometimes separated due to resolution or visual noise.

Advanced Observations & Future Improvements
Multithreading can drastically improve scraping speed.

Introduce more robust similarity checks:

perceptual hashing (e.g., phash),

structural similarity (SSIM),

visual embeddings from pretrained models.

Enhance scraping logic to avoid false positives from headers or non-logo elements.

Consider site language to adjust OCR or use language-specific models.

Implement adaptive tolerance thresholds based on image resolution and format.

Use geometric comparison of shapes (e.g., for SVGs) when OCR and color both fail.

Directory structure:

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

Run order:

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

Conclusion
This project demonstrated the real-world complexity of a seemingly simple task: extracting and grouping logos. Scraping real websites requires dynamic heuristics and lots of exception handling. Combining OCR and color analysis offered a practical and scalable approach to logo clustering without any ML.

With further improvements, this solution can evolve into a scalable, accurate, and production-ready system capable of processing millions of logos.
