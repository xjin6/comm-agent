# Changelog

## [0.1.0] - 2026-03-26

### Added
- Initial release
- Topic post scraping via s.weibo.com with cookie authentication
- Comment scraping via AJAX API with cursor-based pagination
- User profile scraping with in-memory caching
- Smart pagination: auto-detects page count from HTML
- Date segmentation (day → hour) to bypass 50-page search limit
- Incremental saving to prevent data loss on interruption
- CSV + JSON dual output with UTF-8 BOM for Excel compatibility
- Claude Code skill with step-by-step guided workflow
