#!/usr/bin/env python3

import requests
import os
from tqdm import tqdm
import sys
import re
import json

def sanitize_path_component(component):
    # Replace forbidden characters with underscore
    return re.sub(r'[<>:"/\\|?*]', '_', component)

def is_photo(filename):
    # Common image extensions (add more as needed)
    return filename.lower().endswith((
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp', '.tiff', '.ico'
    ))

if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} URL FOLDER [--no-photos]")
    exit(1)

# Option handling
exclude_photos = '--no-photos' in sys.argv
if exclude_photos:
    sys.argv.remove('--no-photos')

main_page = requests.get(sys.argv[1]).text

match_siteinfo = re.findall(r'window\.siteInfo\s*=\s*({[^}]+})', main_page)
if len(match_siteinfo) == 0:
    print("Unable to extract siteInfo")
    exit(1)

siteinfo = json.loads(match_siteinfo[0])
uid = siteinfo["uid"]
host = siteinfo["host"]

cache_data = requests.get(f"https://{host}/cache/{uid}").json()

for i in tqdm(cache_data.keys()):
    # Skip photo files if the option is enabled
    if exclude_photos and is_photo(i):
        continue

    resp = requests.get(f"https://{host}/access/{uid}/{i}")

    # Split the path, sanitize each part, and re-join
    safe_parts = [sanitize_path_component(part) for part in i.split('/')]
    safe_path = os.path.join(sys.argv[2], *safe_parts)
    parent_folder = os.path.dirname(os.path.abspath(safe_path))

    if not os.path.exists(parent_folder):
        os.makedirs(parent_folder)

    with open(safe_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1048576):
            f.write(chunk)
