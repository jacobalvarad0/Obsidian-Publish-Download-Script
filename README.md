# Obsidian-Publish-Download-Script

A simple Python script to download an entire [Obsidian Publish](https://obsidian.md/publish) site with or without photo assets.

## Requirements

- [tqdm](https://pypi.org/project/tqdm/)
- [requests](https://pypi.org/project/requests/)

## Example

```
python download.py https://help.obsidian.md/ vault_name
python download.py https://help.obsidian.md/ vault_name --no-photos
```

To download the Obsidian Help site to a folder called "vault_name".

## Licensing

This software is licensed under the MIT License. See `LICENSE`.
