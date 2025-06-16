#!/usr/bin/env python3

# Create a simple test image using PIL
from PIL import Image, ImageDraw, ImageFont
import os

# Create a simple test image
width, height = 400, 300
image = Image.new('RGB', (width, height), color='lightblue')
draw = ImageDraw.Draw(image)

# Add some text
try:
    # Try to use a default font
    font = ImageFont.load_default()
except:
    font = None

# Draw some shapes and text
draw.rectangle([50, 50, 350, 250], fill='white', outline='black', width=2)
draw.ellipse([100, 100, 200, 150], fill='red')
draw.ellipse([200, 120, 300, 170], fill='green')
draw.text((120, 200), "Test Image for File Manager", fill='black', font=font)

# Save the image
image.save('/Users/pascalhintermaier/Documents/neue UI /ordnungshub/test-sample-image.png')
print("Test image created: test-sample-image.png")