# Obsidian-Publish-Download-Script

A simple Python script to download an entire [Obsidian Publish](https://obsidian.md/publish) site with or without photo assets.

## Requirements

- [tqdm](https://pypi.org/project/tqdm/)
- [requests](https://pypi.org/project/requests/)

## Example

```
python download.py <URL> <FOLDER> [--no-photos] [--no-audio-video] [--no-documents] [--threads N]
```

To download the Obsidian Help site to a folder called "vault_name".

## Licensing

This software is licensed under the MIT License. See `LICENSE`.
