# Changelog

All notable changes to this project will be documented in this file.

## [2026-01-18]
### Added
- Created virtual environment setup logic.
- Added `requirements.txt` with `requests`, `beautifulsoup4`, and `python-dotenv`.
- Create `README.md` with project setup and usage instructions.
- Added support for `.env` file to manage secrets securely.
- Added `config.py` for centralized configuration management.

### Fixed
- Fixed execution environment issues by switching to absolute paths for `venv` scripts.
- Refactored `index.py` to use `config.py` instead of direct env access for better maintainability.

### Removed
- Removed `telegram_bot_data.py` (secrets now in `.env`).
