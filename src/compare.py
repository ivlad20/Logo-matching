import os
import json
import pytesseract
import re
import shutil
from PIL import Image
import numpy as np
from collections import defaultdict

# Configurare
input_folder = '../data/logos/normalised'
output_base_folder = '../data/logos/grouped_by_text_or_color'
output_json_path = '../data/logos/groups.json'
COLOR_TOLERANCE = 1  # Toleranță culoare (0 = strict, >0 = mai permisiv)

# Structură pentru grupuri
text_groups = defaultdict(list)

# === Funcții OCR și procesare imagine ===

def clean_ocr_text(text):
    text = text.strip().lower()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def prepare_for_ocr(img):
    gray = img.convert('L')  # grayscale
    resized = gray.resize((img.width * 2, img.height * 2))  # upscale
    threshold = resized.point(lambda p: 255 if p > 180 else 0)  # binarizare dură
    return threshold

def get_average_rgb_ignore_magenta(image):
    arr = np.array(image.convert('RGB')).reshape(-1, 3)
    non_magenta = arr[~np.all(arr == [255, 0, 255], axis=1)]
    if len(non_magenta) == 0:
        return None
    avg = tuple(np.mean(non_magenta, axis=0).astype(int))
    return avg

def quantize_rgb(rgb, tolerance):
    return tuple((c // tolerance) * tolerance for c in rgb)

# === Procesare imagini ===

for filename in os.listdir(input_folder):
    if filename.lower().endswith('.png'):
        path = os.path.join(input_folder, filename)

        with Image.open(path) as img:
            ocr_ready = prepare_for_ocr(img)
            text = pytesseract.image_to_string(
                ocr_ready,
                lang='eng',
                config='--psm 6 --oem 3 -c preserve_interword_spaces=1'
            )
            text = clean_ocr_text(text)

            if text:
                text_groups[text].append(filename)
            else:
                avg_rgb = get_average_rgb_ignore_magenta(img)
                if avg_rgb is None:
                    group_key = "magenta_bg"
                else:
                    quantized_rgb = quantize_rgb(avg_rgb, COLOR_TOLERANCE)
                    group_key = f"color_{quantized_rgb[0]}_{quantized_rgb[1]}_{quantized_rgb[2]}"
                text_groups[group_key].append(filename)

# === Salvare grupuri + copiere imagini + JSON ===

sorted_groups = sorted(text_groups.items(), key=lambda x: len(x[1]), reverse=True)
os.makedirs(output_base_folder, exist_ok=True)

json_output = {}
for idx, (group_name, files) in enumerate(sorted_groups, 1):
    group_key = f"group_{idx:03}"
    group_folder = os.path.join(output_base_folder, group_key)
    os.makedirs(group_folder, exist_ok=True)

    # Copiere imagini în folderul de grup
    for f in files:
        src = os.path.join(input_folder, f)
        dst = os.path.join(group_folder, f)
        shutil.copy2(src, dst)

    # Scriere în JSON
    json_output[group_key] = {
        "based_on": group_name,
        "images": files
    }

# Scriere JSON final
os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
with open(output_json_path, 'w', encoding='utf-8') as f:
    json.dump(json_output, f, indent=2, ensure_ascii=False)

print(f"\n✅ Gruparea a fost salvată în: {output_json_path}")
print(f"🧠 OCR agresiv activat | 🎨 Toleranță culoare: {COLOR_TOLERANCE} | 🎯 Ignorare magenta: ON")
