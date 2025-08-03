# IQiyi Scrapers Package

Organized package untuk semua fungsi scraping IQiyi di AniFlix.

## Struktur Folder

```
iqiyi_scrapers/
├── __init__.py                   # Package entry point
├── README.md                     # Dokumentasi ini
├── extractors/                   # Core extraction modules
│   ├── __init__.py
│   ├── enhanced_iqiyi_extractor.py    # Main extraction engine (mainx.py method)
│   ├── iqiyi_dash_extractor.py        # DASH URL processing
│   └── iqiyi_play_extractor.py        # Play URL to M3U8 conversion
├── scrapers/                     # Scraping strategies
│   ├── __init__.py
│   ├── enhanced_iqiyi_scraper.py       # Main scraper with error handling
│   ├── iqiyi_scraper.py               # Core scraper functions
│   ├── iqiyi_m3u8_scraper.py          # M3U8 extraction from DASH
│   ├── iqiyi_direct_scraper.py        # Direct URL scraping
│   └── iqiyi_fallback_scraper.py      # Simplified fallback method
├── utils/                        # Helper scripts
│   ├── __init__.py
│   ├── simple_episode_scraper.py      # Basic episode info extraction
│   ├── create_episodes_from_basic.py  # Database insertion
│   ├── get_all_22_episodes.py         # Bulk episode extraction
│   └── migrate_to_iqiyi_play_url.py   # Migration script
└── legacy/                       # Deprecated implementations
    ├── __init__.py
    └── iqiyi_alternative.py           # Alternative scraper method
```

## Usage

### Basic Import
```python
from iqiyi_scrapers import scrape_iqiyi_episode, scrape_iqiyi_playlist, IQiyiM3U8Scraper
```

### Advanced Import
```python
from iqiyi_scrapers.extractors.enhanced_iqiyi_extractor import EnhancedIQiyiExtractor
from iqiyi_scrapers.scrapers.iqiyi_scraper import IQiyiScraper
```

## Description

### Extractors
- **Enhanced IQiyi Extractor**: Core extraction engine menggunakan advanced methods
- **DASH Extractor**: Specialized untuk memproses DASH URLs
- **Play Extractor**: Konversi langsung play URL ke M3U8

### Scrapers  
- **Enhanced Scraper**: Main scraping engine dengan error handling
- **Core Scraper**: Fungsi scraping utama (scrape_iqiyi_episode, scrape_iqiyi_playlist)
- **M3U8 Scraper**: Ekstraksi M3U8 dari DASH URLs
- **Direct Scraper**: Scraping langsung dari play pages
- **Fallback Scraper**: Method sederhana untuk reliability

### Utils
- **Simple Episode Scraper**: Ekstraksi basic episode info tanpa M3U8
- **Create Episodes**: Insert episodes ke database dari scraping results
- **Migration Scripts**: Update database schema

### Legacy
- **Alternative Scraper**: Backup implementations untuk referensi

## Notes

- Semua import statements di project sudah diupdate untuk menggunakan struktur baru
- Package ini sepenuhnya backward compatible dengan kode yang ada
- Struktur ini memudahkan maintenance dan development future features