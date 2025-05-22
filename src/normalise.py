
import os
from PIL import Image

# Input and output folders
input_folder = '../data/logos/pngs'
output_folder = '../data/logos/normalised'

# Target size for all output images
target_size = (256, 256)

# Rare background color (used to detect background easily if needed later)
bg_color = (255, 0, 255)

# Create the output directory if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Process each PNG file in the input directory
for filename in os.listdir(input_folder):
    if filename.lower().endswith('.png'):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        with Image.open(input_path) as img:
            # Ensure the image is in RGBA mode to support transparency
            img = img.convert('RGBA')

            # Resize the image while maintaining aspect ratio
            img.thumbnail(target_size, Image.Resampling.LANCZOS)

            # Create a new image with the target size and background color
            background = Image.new('RGB', target_size, bg_color)

            # Center the resized image on the background
            x = (target_size[0] - img.width) // 2
            y = (target_size[1] - img.height) // 2
            background.paste(img, (x, y), img)

            # Save the final image
            background.save(output_path, 'PNG')

print("All images resized and centered on background.")