# Obsidian-Publish-Download-Script

A simple Python script to download an entire [Obsidian Publish](https://obsidian.md/publish) site with or without photo, video or document assests. 

Supports parallel downloads with configurable number of threads. 

Logs errors and conflicts to a dedicated error log file.

## Requirements

- [tqdm](https://pypi.org/project/tqdm/)
- [requests](https://pypi.org/project/requests/)

```
pip install requests tqdm
```
## Usage
```
<URL>: The URL of the Obsidian Publish site to download.

<FOLDER>: The local folder to save the downloaded vault.

--no-photos: Optional flag to skip downloading image files.

--no-audio-video: Optional flag to skip downloading audio and video files.

--no-documents: Optional flag to skip downloading document files (PDF, DOCX, etc).

--threads N: Optional flag to set the number of parallel download threads (default is 8).
```
## Example

```
python download.py <URL> <FOLDER> [--no-photos] [--no-audio-video] [--no-documents] [--threads N]
```

## Licensing

This software is licensed under the MIT License. See `LICENSE`.
