import os
from pathlib import Path
import cairosvg

def convert_svg_to_png(input_dir: str, output_dir: str, scale: float = 1.0, output_size: tuple[int, int] = None):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for svg_file in input_path.glob("*.svg"):
        png_filename = output_path / (svg_file.stem + ".png")

        try:
            if output_size:
                cairosvg.svg2png(
                    url=str(svg_file),
                    write_to=str(png_filename),
                    output_width=output_size[0],
                    output_height=output_size[1]
                )
            else:
                cairosvg.svg2png(
                    url=str(svg_file),
                    write_to=str(png_filename),
                    scale=scale
                )
            print(f"✔️ Converted: {svg_file.name} → {png_filename.name}")
        except Exception as e:
            print(f"❌ Failed to convert {svg_file.name}: {e}")

# Exemplu de utilizare:
if __name__ == "__main__":
    convert_svg_to_png(
        input_dir="../data/logos/svgs",     # folder cu SVG-uri
        output_dir="../data/logos/pngs",   # folder de ieșire PNG-uri
        scale=2.0                   # poți schimba sau înlocui cu output_size=(256, 256)
    )
