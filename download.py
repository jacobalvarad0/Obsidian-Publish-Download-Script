#!/usr/bin/env python3

import requests
import os
from tqdm import tqdm
import sys
import re
import json
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

FORBIDDEN_CHARS = r'[<>:"/\\|?*\n\r\t#]'
MAX_FILENAME_LEN = 100  # Windows max filename is 255, but keep some margin

def sanitize_path_component(component):
    # Remove or replace forbidden/problematic characters
    component = re.sub(FORBIDDEN_CHARS, '_', component)
    # Remove leading/trailing spaces and dots
    component = component.strip(' .')
    # Truncate to avoid path length issues
    return component[:MAX_FILENAME_LEN]

def log_error(error_message, error_folder="error_logs"):
    if not os.path.exists(error_folder):
        os.makedirs(error_folder)
    log_file = os.path.join(error_folder, "error_log.txt")
    with open(log_file, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {error_message}\n")

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

def safe_path_join(base_folder, parts):
    """
    Safely join path components, checking for file/folder conflicts.
    Returns None if a conflict is detected.
    """
    path = base_folder
    for i, part in enumerate(parts):
        path = os.path.join(path, part)
        if os.path.exists(path):
            if i < len(parts) - 1:
                # Should be a folder, but a file exists
                if os.path.isfile(path):
                    return None
            else:
                # Last part: if a folder exists but we want to write a file, that's a conflict
                if os.path.isdir(path):
                    return None
    return path

def download_one(args):
    i, host, uid, folder, no_photos, no_audio_video, no_documents = args
    if is_excluded(i, no_photos, no_audio_video, no_documents):
        return None

    try:
        resp = requests.get(f"https://{host}/access/{uid}/{i}", timeout=30)
        resp.raise_for_status()
    except Exception as e:
        log_error(f"Failed to download {i}: {e}")
        return None

    # Sanitize each path component
    safe_parts = [sanitize_path_component(part) for part in i.split('/')]
    safe_path = safe_path_join(folder, safe_parts)
    if safe_path is None:
        log_error(f"File/folder conflict detected for path: {os.path.join(folder, *safe_parts)}. Skipping.")
        return None

    parent_folder = os.path.dirname(os.path.abspath(safe_path))
    try:
        if not os.path.exists(parent_folder):
            os.makedirs(parent_folder)
        # If a directory exists at the file path, that's a conflict
        if os.path.isdir(safe_path):
            log_error(f"Cannot save file because a directory exists at {safe_path}. Skipping.")
            return None
        with open(safe_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1048576):
                f.write(chunk)
        return i
    except Exception as e:
        log_error(f"Failed to save {i}: {e}")
        return None

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} URL FOLDER [--no-photos] [--no-audio-video] [--no-documents] [--threads N]")
        sys.exit(1)

    url = sys.argv[1]
    folder = sys.argv[2]
    no_photos = '--no-photos' in sys.argv
    no_audio_video = '--no-audio-video' in sys.argv
    no_documents = '--no-documents' in sys.argv
    if '--threads' in sys.argv:
        threads_idx = sys.argv.index('--threads')
        try:
            num_threads = int(sys.argv[threads_idx + 1])
        except (IndexError, ValueError):
            num_threads = 8
    else:
        num_threads = 8  # Default

    try:
        main_page = requests.get(url, timeout=30).text
    except Exception as e:
        log_error(f"Failed to fetch main page: {e}")
        print(f"Failed to fetch main page: {e}")
        sys.exit(1)

    match_siteinfo = re.findall(r'window\.siteInfo\s*=\s*({[^}]+})', main_page)
    if len(match_siteinfo) == 0:
        log_error("Unable to extract siteInfo from the main page. Is this a valid Obsidian Publish site?")
        print("Unable to extract siteInfo from the main page. Is this a valid Obsidian Publish site?")
        sys.exit(1)

    try:
        siteinfo = json.loads(match_siteinfo[0])
        uid = siteinfo["uid"]
        host = siteinfo["host"]
    except Exception as e:
        log_error(f"Failed to parse siteInfo: {e}")
        print(f"Failed to parse siteInfo: {e}")
        sys.exit(1)

    try:
        cache_response = requests.get(f"https://{host}/cache/{uid}", timeout=30)
        if not cache_response.ok or not cache_response.text.strip():
            log_error(f"Error: Empty or invalid response from /cache/ endpoint. Status code: {cache_response.status_code} Response text: {cache_response.text}")
            print("Error: Empty or invalid response from /cache/ endpoint.")
            sys.exit(1)
        cache_data = cache_response.json()
    except Exception as e:
        log_error(f"Error: /cache/ endpoint did not return valid JSON or could not be reached. Exception: {e} Response text: {getattr(cache_response, 'text', '')}")
        print("Error: /cache/ endpoint did not return valid JSON or could not be reached.")
        sys.exit(1)

    file_list = list(cache_data.keys())
    if not file_list:
        log_error("No files found in the vault. Exiting.")
        print("No files found in the vault. Exiting.")
        sys.exit(1)

    download_args = [
        (i, host, uid, folder, no_photos, no_audio_video, no_documents)
        for i in file_list
    ]

    print(f"Starting download of {len(download_args)} files with {num_threads} threads...")

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(download_one, arg) for arg in download_args]
        for _ in tqdm(as_completed(futures), total=len(futures)):
            pass

    print("Download complete. Errors (if any) are logged in the error_logs/error_log.txt file.")

if __name__ == "__main__":
    main()
