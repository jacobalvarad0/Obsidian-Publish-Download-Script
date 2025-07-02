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

def is_excluded(filename, no_photos, no_audio_video, no_documents):
    photo_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg'}
    audio_video_exts = {'.mp4', '.mp3', '.wav', '.avi', '.mov', '.flv', '.mkv', '.wmv', '.aac', '.ogg'}
    document_exts = {'.pdf', '.html', '.htm', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf'}

    ext = os.path.splitext(filename.lower())[1]
    if no_photos and ext in photo_exts:
        return True
    if no_audio_video and ext in audio_video_exts:
        return True
    if no_documents and ext in document_exts:
        return True
    return False

# --- Argument parsing ---
if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} URL FOLDER [--no-photos] [--no-audio-video] [--no-documents]")
    exit(1)

url = sys.argv[1]
folder = sys.argv[2]
no_photos = '--no-photos' in sys.argv
no_audio_video = '--no-audio-video' in sys.argv
no_documents = '--no-documents' in sys.argv

# --- Main logic ---
main_page = requests.get(url).text

match_siteinfo = re.findall(r'window\.siteInfo\s*=\s*({[^}]+})', main_page)
if len(match_siteinfo) == 0:
    print("Unable to extract siteInfo")
    exit(1)

siteinfo = json.loads(match_siteinfo[0])
uid = siteinfo["uid"]
host = siteinfo["host"]

cache_data = requests.get(f"https://{host}/cache/{uid}").json()

for i in tqdm(cache_data.keys()):
    if is_excluded(i, no_photos, no_audio_video, no_documents):
        continue

    resp = requests.get(f"https://{host}/access/{uid}/{i}")

    safe_parts = [sanitize_path_component(part) for part in i.split('/')]
    safe_path = os.path.join(folder, *safe_parts)
    parent_folder = os.path.dirname(os.path.abspath(safe_path))

    if not os.path.exists(parent_folder):
        os.makedirs(parent_folder)

    with open(safe_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1048576):
            f.write(chunk)
