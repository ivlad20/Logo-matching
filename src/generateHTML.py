import os
import json
import shutil

# Paths to input/output directories and files
json_path = '../data/logos/groups.json'
input_images_folder = '../data/logos/pngs'
output_site_folder = './output_site'
images_output_folder = os.path.join(output_site_folder, 'images')

# Create the output folders if they do not already exist
os.makedirs(images_output_folder, exist_ok=True)

# Load the JSON file containing the image groups
with open(json_path, 'r', encoding='utf-8') as f:
    groups = json.load(f)

# Copy all unique images from the input folder to the site output folder
copied = set()
for group in groups.values():
    for img in group["images"]:
        if img not in copied:
            src = os.path.join(input_images_folder, img)
            dst = os.path.join(images_output_folder, img)
            shutil.copy2(src, dst)
            copied.add(img)

# Begin building the HTML content
html_parts = [
    "<!DOCTYPE html>",
    "<html lang='en'>",
    "<head>",
    "  <meta charset='UTF-8'>",
    "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
    "  <title>Grouped Logos</title>",
    "  <style>",
    "    body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }",
    "    h2 { border-bottom: 1px solid #ccc; padding-bottom: 5px; }",
    "    .group { margin-bottom: 40px; }",
    "    .images { display: flex; flex-wrap: wrap; gap: 10px; }",
    "    .images img {",
    "      height: 100px;",
    "      border: 1px solid #ccc;",
    "      padding: 4px;",
    "      background-color: #d3d3d3;",
    "      transition: transform 0.2s ease;",
    "    }",
    "    .images img:hover {",
    "      ",
    "      ",
    "      ",
    "    }",
    "  </style>",
    "</head>",
    "<body>",
    "  <h1>Grouped Logos</h1>"
]

# Add each group and its images to the HTML
for group_name, group_data in groups.items():
    html_parts.append(f"<div class='group'>")
    html_parts.append(f"  <h2>{group_name} (Based on: {group_data['based_on']})</h2>")
    html_parts.append(f"  <div class='images'>")
    for img_name in group_data["images"]:
        html_parts.append(f"    <img src='images/{img_name}' alt='{img_name}'>")
    html_parts.append(f"  </div>")
    html_parts.append(f"</div>")

# Close the HTML tags
html_parts.append("</body></html>")

# Write the HTML content to a file in the output site folder
with open(os.path.join(output_site_folder, 'index.html'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(html_parts))

# Confirmation message
print("Website generated in folder:", output_site_folder)