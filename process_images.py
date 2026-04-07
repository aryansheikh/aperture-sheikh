from PIL import Image, ImageDraw, ImageFont
import os

# --- CONFIG ---
INPUT_DIR = "raw"
OUTPUT_DIR = "images"
WATERMARK_TEXT = "© ApertureSheikh"
QUALITY = 82
MAX_WIDTH = 2400  # pixels — enough for large screens, not bloated

os.makedirs(OUTPUT_DIR, exist_ok=True)

supported = (".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG")
files = [f for f in os.listdir(INPUT_DIR) if f.endswith(supported)]

print(f"Found {len(files)} images to process...")

for filename in files:
    input_path = os.path.join(INPUT_DIR, filename)
    output_filename = os.path.splitext(filename)[0] + ".webp"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    with Image.open(input_path) as img:
        # Convert to RGB (in case of PNG with transparency)
        img = img.convert("RGB")

        # Resize if wider than MAX_WIDTH, keep aspect ratio
        if img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / img.width
            new_size = (MAX_WIDTH, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        # --- WATERMARK ---
        draw = ImageDraw.Draw(img)

        # Font size relative to image width
        font_size = max(20, int(img.width * 0.018))

        try:
            # Try to use a system font
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Get text size
        bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Position: bottom right with padding
        padding = int(img.width * 0.02)
        x = img.width - text_width - padding
        y = img.height - text_height - padding

        # Draw subtle shadow then text
        draw.text((x + 1, y + 1), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 128))
        draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 180))

        # Save as WebP
        img.save(output_path, "WEBP", quality=QUALITY)
        original_size = os.path.getsize(input_path) / 1024 / 1024
        output_size = os.path.getsize(output_path) / 1024 / 1024
        print(f"✓ {filename} → {output_filename} ({original_size:.1f}MB → {output_size:.2f}MB)")

print("\nDone! All images saved to /images")
