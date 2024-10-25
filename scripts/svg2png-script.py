# -*- coding: utf-8 -*-
import os
from pathlib import Path

import cairosvg

current_folder = Path(__file__).resolve().parent.parent

svg_folder_path = "/Users/pangan/Downloads/"
png_folder_path = current_folder / "source"


if not os.path.exists(png_folder_path):
    os.makedirs(png_folder_path)

for filename in os.listdir(svg_folder_path):
    if filename.endswith(".svg"):
        svg_file_path = os.path.join(svg_folder_path, filename)

        png_file_name = os.path.splitext(filename)[0] + ".png"
        png_file_path = os.path.join(png_folder_path, png_file_name)

        cairosvg.svg2png(url=svg_file_path, write_to=png_file_path, output_width=128, output_height=128)

        print(f"SVG file '{svg_file_path}' has been converted to PNG and saved as '{png_file_path}'.")

print("All SVG files have been converted to PNG.")
