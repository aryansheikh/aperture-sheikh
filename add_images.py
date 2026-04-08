import os
import re

IMAGES_DIR = "images"
INDEX_FILE = "index.html"
CATEGORIES = ["birds", "wildlife", "landscape"]

# --- Read index.html ---
with open(INDEX_FILE, "r", encoding="utf-8") as f:
    html = f.read()

# --- Find all images already referenced in index.html ---
existing = set(re.findall(r'src="images/([^"]+)"', html))

# --- Find all processed images in images/ dir ---
all_images = [f for f in os.listdir(IMAGES_DIR) if f.endswith(".webp")]

# --- Find new ones ---
new_images = [f for f in all_images if f not in existing]

if not new_images:
    print("No new images found. All images are already in index.html.")
    exit()

print(f"\nFound {len(new_images)} new image(s):\n")

entries = []

for filename in sorted(new_images):
    print(f"  {filename}")

    # Title
    default_title = os.path.splitext(filename)[0].replace("-", " ").replace("_", " ")
    title = input(f"  Title [{default_title}]: ").strip()
    if not title:
        title = default_title

    # Category
    print(f"  Category: ", end="")
    for i, cat in enumerate(CATEGORIES):
        print(f"{i+1}) {cat}  ", end="")
    cat_input = input("\n  Choice [1]: ").strip()
    try:
        cat_index = int(cat_input) - 1
        if cat_index < 0 or cat_index >= len(CATEGORIES):
            cat_index = 0
    except ValueError:
        cat_index = 0
    category = CATEGORIES[cat_index]
    cat_display = category.capitalize()

    entry = f'''    <div class="gallery-item" data-category="{category}" data-title="{title}">
      <img src="images/{filename}" alt="{title}" loading="lazy">
      <div class="gallery-item-overlay"><div class="gallery-item-meta"><span class="gallery-item-cat">{cat_display}</span><span class="gallery-item-title">{title}</span></div></div>
    </div>'''

    entries.append((category, entry))
    print(f"  Added: {title} ({category})\n")

# --- Insert entries into the correct category section in index.html ---
# Find insertion point: just before </div>\n</section> that closes the gallery grid
# We insert grouped by category, after the last item of that category

for category, entry in entries:
    # Find the last occurrence of data-category="{category}" and insert after its closing </div>
    pattern = rf'((?:.*?data-category="{category}".*?</div>\s*</div>\s*</div>)(?!.*data-category="{category}"))'
    match = list(re.finditer(
        rf'(<div class="gallery-item" data-category="{category}".*?</div>\s*</div>\s*</div>)',
        html, re.DOTALL
    ))

    if match:
        last_match = match[-1]
        insert_pos = last_match.end()
        html = html[:insert_pos] + "\n" + entry + html[insert_pos:]
    else:
        # Category doesn't exist yet, insert before closing gallery-grid div
        insert_marker = "  </div>\n</section>"
        insert_pos = html.rfind(insert_marker)
        if insert_pos != -1:
            html = html[:insert_pos] + entry + "\n\n" + html[insert_pos:]
        else:
            print(f"  Warning: Could not find insertion point for {filename}. Add it manually.")

# --- Write updated index.html ---
with open(INDEX_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nDone! {len(entries)} image(s) added to {INDEX_FILE}.")
print("Review index.html, then run:")
print("  git add images/ metadata.json index.html")
print('  git commit -m "Add new photos"')
print("  git push")
