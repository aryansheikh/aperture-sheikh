from PIL import Image, ImageDraw, ImageFont
import piexif
import json
import os

# --- CONFIG ---
INPUT_DIR = "raw"
OUTPUT_DIR = "images"
WATERMARK_TEXT = "© ApertureSheikh"
QUALITY = 82
MAX_WIDTH = 2400

os.makedirs(OUTPUT_DIR, exist_ok=True)

supported = (".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG")
files = [f for f in os.listdir(INPUT_DIR) if f.endswith(supported)]

print(f"Found {len(files)} images to process...\n")

metadata = {}


def get_str(exif_dict, ifd, tag):
    try:
        val = exif_dict[ifd][tag]
        if isinstance(val, bytes):
            return val.decode("utf-8", errors="ignore").strip("\x00").strip()
        return str(val).strip()
    except Exception:
        return None


def rational_to_float(val):
    try:
        if isinstance(val, tuple) and val[1] != 0:
            return val[0] / val[1]
        return float(val)
    except Exception:
        return None


for filename in files:
    input_path = os.path.join(INPUT_DIR, filename)
    output_filename = os.path.splitext(filename)[0] + ".webp"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    with Image.open(input_path) as img:
        img = img.convert("RGB")

        # --- EXIF HANDLING ---
        exif_data = {}
        clean_exif_bytes = None

        try:
            raw_exif = img.info.get("exif", b"")
            if raw_exif:
                exif_dict = piexif.load(raw_exif)
                photo = exif_dict.get("Exif", {})

                # Extract what we want to display
                make  = get_str(exif_dict, "0th", piexif.ImageIFD.Make)
                model = get_str(exif_dict, "0th", piexif.ImageIFD.Model)
                lens  = get_str(exif_dict, "Exif", piexif.ExifIFD.LensModel)

                focal    = rational_to_float(photo.get(piexif.ExifIFD.FocalLength))
                aperture = rational_to_float(photo.get(piexif.ExifIFD.FNumber))
                iso      = photo.get(piexif.ExifIFD.ISOSpeedRatings)

                shutter = None
                shutter_raw = photo.get(piexif.ExifIFD.ExposureTime)
                if shutter_raw and isinstance(shutter_raw, tuple):
                    n, d = shutter_raw
                    shutter = f"1/{d}s" if n == 1 else f"{n}/{d}s"

                exif_data = {k: v for k, v in {
                    "camera":       f"{make} {model}".strip() if (make or model) else None,
                    "lens":         lens,
                    "focal_length": f"{int(focal)}mm"         if focal     else None,
                    "aperture":     f"f/{aperture:.1f}"        if aperture  else None,
                    "shutter":      shutter,
                    "iso":          f"ISO {iso}"               if iso       else None,
                }.items() if v}

                # Strip GPS, keep everything else
                exif_dict["GPS"] = {}
                clean_exif_bytes = piexif.dump(exif_dict)

        except Exception as e:
            print(f"  ⚠  EXIF error for {filename}: {e}")

        # --- RESIZE ---
        if img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / img.width
            img = img.resize((MAX_WIDTH, int(img.height * ratio)), Image.LANCZOS)

        # --- WATERMARK ---
        draw = ImageDraw.Draw(img)
        font_size = max(20, int(img.width * 0.018))
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        bbox    = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
        tw, th  = bbox[2] - bbox[0], bbox[3] - bbox[1]
        padding = int(img.width * 0.02)
        x = img.width  - tw - padding
        y = img.height - th - padding

        draw.text((x + 1, y + 1), WATERMARK_TEXT, font=font, fill=(0,   0,   0,   128))
        draw.text((x,     y    ), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 180))

        # --- SAVE ---
        save_kwargs = {"quality": QUALITY}
        if clean_exif_bytes:
            save_kwargs["exif"] = clean_exif_bytes

        img.save(output_path, "WEBP", **save_kwargs)

        orig_mb = os.path.getsize(input_path)  / 1024 / 1024
        out_mb  = os.path.getsize(output_path) / 1024 / 1024
        exif_summary = " | ".join(exif_data.values()) if exif_data else "no EXIF"
        print(f"✓  {filename} → {output_filename}  ({orig_mb:.1f}MB → {out_mb:.2f}MB)  [{exif_summary}]")

        metadata[output_filename] = exif_data

# --- WRITE METADATA JSON ---
with open("metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"\nDone! metadata.json written with {len(metadata)} entries.")
