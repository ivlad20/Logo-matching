import os
from pathlib import Path
import cairosvg


def convert_svg_to_png(input_dir: str, output_dir: str, scale: float = 2.0, fallback_size=(256, 256)):
    # Convert the input and output paths to Path objects
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Create the output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    # Iterate over all SVG files in the input directory
    for svg_file in input_path.glob("*.svg"):
        png_filename = output_path / (svg_file.stem + ".png")

        try:
            # Attempt to convert SVG to PNG with the specified scale
            cairosvg.svg2png(
                url=str(svg_file),
                write_to=str(png_filename),
                scale=scale
            )
            print(f"Converted: {svg_file.name} → {png_filename.name}")
        except Exception as e:
            # Handle the case where SVG size is undefined
            if "SVG size is undefined" in str(e):
                try:
                    # Retry conversion by setting a fallback output size
                    cairosvg.svg2png(
                        url=str(svg_file),
                        write_to=str(png_filename),
                        output_width=fallback_size[0],
                        output_height=fallback_size[1]
                    )
                    print(f"Converted with fallback size: {svg_file.name} → {png_filename.name}")
                except Exception as inner_e:
                    print(f"Failed to convert {svg_file.name} even with fallback size: {inner_e}")
            else:
                print(f"Failed to convert {svg_file.name}: {e}")


# Entry point of the script
if __name__ == "__main__":
    convert_svg_to_png(
        input_dir="../data/logos/svgs",
        output_dir="../data/logos/pngs",
        scale=2.0,
        fallback_size=(256, 256)
    )
