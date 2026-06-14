#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""File Organizer Pro - Advanced file sorting tool with custom rules.

This module provides a professional-grade file organization utility that
automatically categorizes files based on their extensions. It supports
custom JSON rules, dry-run mode, recursive scanning, conflict resolution,
and comprehensive logging.

Typical usage example:
    python file_organizer.py ~/Downloads --recursive --dry-run
    python file_organizer.py . --config my_rules.json --log-file organize.log
"""

import argparse
import fnmatch
import json
import logging
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Final, TypeAlias

# Type aliases for better readability
CategoryMap: TypeAlias = Dict[str, List[str]]
ProcessStats: TypeAlias = Dict[str, int]

# ============================================================================
# Configuration and constants
# ============================================================================

DEFAULT_CATEGORIES: Final[CategoryMap] = {
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico'],
    'Documents': ['.pdf', '.docx', '.doc', '.txt', '.xlsx', '.xls', '.pptx', '.ppt',
                  '.md', '.rtf', '.odt', '.tex'],
    'Archives': ['.zip', '.rar', '.tar', '.gz', '.7z', '.bz2', '.xz'],
    'Audios': ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'],
    'Videos': ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm', '.wmv'],
    'Programs': ['.exe', '.msi', '.sh', '.bat', '.py', '.js', '.html', '.css',
                 '.json', '.xml', '.yml', '.yaml', '.ini', '.go', '.rs', '.c', '.cpp'],
    'Spreadsheets': ['.csv', '.xlsx', '.xls', '.ods'],
    'Others': []
}

CONFLICT_MODES: Final[Tuple[str, ...]] = ('rename', 'skip', 'overwrite')


@dataclass
class OrganizerConfig:
    """Immutable configuration container for file organizer."""
    base_path: Path
    categories: CategoryMap = field(default_factory=lambda: DEFAULT_CATEGORIES.copy())
    recursive: bool = False
    dry_run: bool = False
    move: bool = True  # False means copy
    ignore_patterns: List[str] = field(default_factory=list)
    conflict_mode: str = 'rename'
    verbose: bool = False
    log_file: Optional[Path] = None

    def __post_init__(self) -> None:
        self.base_path = Path(self.base_path).resolve()
        if self.conflict_mode not in CONFLICT_MODES:
            raise ValueError(f'conflict_mode must be one of {CONFLICT_MODES}')
        # Normalize ignore patterns to lower case for case-insensitive matching?
        # We'll keep as-is; fnmatch can handle case sensitivity based on OS.

# ============================================================================
# Logging setup
# ============================================================================

def _configure_logging(verbose: bool, log_file: Optional[Path]) -> None:
    """Set up logging with console and optional file output."""
    log_level = logging.DEBUG if verbose else logging.INFO
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding='utf-8'))

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers
    )


def _load_custom_categories(config_path: Path) -> CategoryMap:
    """Load category definitions from a JSON file.

    Expected JSON structure:
        {"categories": {"GroupName": [".ext1", ".ext2"], ...}}

    Returns:
        CategoryMap if file exists and contains valid data, otherwise raises.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        categories = data.get('categories')
        if not isinstance(categories, dict):
            raise ValueError('JSON must contain a "categories" dictionary')
        # Validate each category's extensions are lists of strings
        for cat, exts in categories.items():
            if not isinstance(exts, list) or not all(isinstance(e, str) for e in exts):
                raise ValueError(f'Extensions for "{cat}" must be list of strings')
        return categories
    except json.JSONDecodeError as e:
        raise ValueError(f'Invalid JSON in {config_path}: {e}')
    except Exception as e:
        raise ValueError(f'Failed to load config from {config_path}: {e}')


# ============================================================================
# Core logic
# ============================================================================

class FileOrganizer:
    """Main orchestrator for file sorting operations.

    This class handles scanning directories, categorizing files based on
    extension, and performing move/copy operations with conflict resolution.
    All operations respect dry-run mode and ignore patterns.
    """

    def __init__(self, config: OrganizerConfig) -> None:
        self._cfg = config
        self._stats: ProcessStats = {'processed': 0, 'moved': 0, 'skipped': 0, 'errors': 0}
        self._logger = logging.getLogger(self.__class__.__name__)

    def run(self) -> None:
        """Execute the organization process."""
        self._logger.info('Starting organization in: %s', self._cfg.base_path)
        if self._cfg.dry_run:
            self._logger.info('*** DRY-RUN MODE – no actual changes will be made ***')

        self._scan_and_process(self._cfg.base_path)
        self._print_summary()

    # ------------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------------

    def _should_ignore(self, file_path: Path) -> bool:
        """Check if a file matches any ignore pattern."""
        # Patterns can be like "*.tmp", "__pycache__", "temp*"
        str_path = str(file_path)
        for pattern in self._cfg.ignore_patterns:
            if fnmatch.fnmatch(str_path, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                return True
        return False

    def _get_target_category(self, extension: str) -> str:
        """Return category name based on file extension."""
        ext = extension.lower()
        for category, extensions in self._cfg.categories.items():
            if ext in extensions:
                return category
        return 'Others'

    def _resolve_conflict(self, dest_path: Path) -> Optional[Path]:
        """Handle existing file at destination according to conflict mode."""
        if not dest_path.exists():
            return dest_path

        mode = self._cfg.conflict_mode
        if mode == 'overwrite':
            if not self._cfg.dry_run:
                dest_path.unlink()
            return dest_path
        elif mode == 'skip':
            self._logger.debug('Skipping existing file: %s', dest_path.name)
            self._stats['skipped'] += 1
            return None
        elif mode == 'rename':
            # Generate unique name: filename_counter.ext
            counter = 1
            stem = dest_path.stem
            suffix = dest_path.suffix
            parent = dest_path.parent
            while True:
                new_name = f'{stem}_{counter}{suffix}'
                candidate = parent / new_name
                if not candidate.exists():
                    return candidate
                counter += 1
        else:
            # Should never happen due to validation in __post_init__
            raise RuntimeError(f'Unhandled conflict mode: {mode}')

    def _process_file(self, file_path: Path) -> bool:
        """Categorize and move/copy a single file."""
        if not file_path.is_file():
            return False

        if self._should_ignore(file_path):
            self._logger.debug('Ignored by pattern: %s', file_path.name)
            return False

        ext = file_path.suffix
        category = self._get_target_category(ext)
        dest_folder = self._cfg.base_path / category
        dest_path = dest_folder / file_path.name

        # Resolve naming conflicts
        dest_path = self._resolve_conflict(dest_path)
        if dest_path is None:
            return False

        # Perform actual operation
        if not self._cfg.dry_run:
            dest_folder.mkdir(parents=True, exist_ok=True)
            try:
                if self._cfg.move:
                    shutil.move(str(file_path), str(dest_path))
                    action = 'Moved'
                else:
                    shutil.copy2(str(file_path), str(dest_path))
                    action = 'Copied'
                self._logger.info('%s: %s → %s/', action, file_path.name, category)
                self._stats['moved'] += 1
            except OSError as e:
                self._logger.error('Failed to process %s: %s', file_path.name, e)
                self._stats['errors'] += 1
                return False
        else:
            self._logger.info('[DRY-RUN] Would move: %s → %s/', file_path.name, category)
            self._stats['moved'] += 1

        self._stats['processed'] += 1
        return True

    def _scan_and_process(self, current_dir: Path) -> None:
        """Recursively scan and process files (if recursive flag is set)."""
        try:
            for item in current_dir.iterdir():
                # Skip the output folders themselves to avoid infinite loops
                if item.is_dir() and item.name in self._cfg.categories:
                    self._logger.debug('Skipping category folder: %s', item.name)
                    continue

                if item.is_file():
                    self._process_file(item)
                elif item.is_dir() and self._cfg.recursive:
                    self._scan_and_process(item)
        except PermissionError:
            self._logger.warning('Permission denied: %s', current_dir)
        except Exception as e:
            self._logger.error('Unexpected error in %s: %s', current_dir, e)

    def _print_summary(self) -> None:
        """Output final statistics."""
        sep = '=' * 50
        summary = (
            f'\n{sep}\n'
            'Organization Summary:\n'
            f'  Files processed: {self._stats["processed"]}\n'
            f'  Files moved/copied: {self._stats["moved"]}\n'
            f'  Skipped (conflicts): {self._stats["skipped"]}\n'
            f'  Errors: {self._stats["errors"]}\n'
        )
        if self._cfg.dry_run:
            summary += '(Dry-run – no actual changes made.)\n'
        self._logger.info(summary)


# ============================================================================
# CLI argument parsing
# ============================================================================

def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Automatically organize files by extension or custom rules.',
        epilog='Examples:\n'
               '  %(prog)s ~/Downloads --recursive --dry-run\n'
               '  %(prog)s . --config my_rules.json --log-file organizer.log',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'path', nargs='?', default='.',
        help='Target directory to organize (default: current directory)'
    )
    parser.add_argument(
        '-r', '--recursive', action='store_true',
        help='Process subdirectories recursively'
    )
    parser.add_argument(
        '-n', '--dry-run', action='store_true',
        help='Preview actions without actually moving/copying files'
    )
    parser.add_argument(
        '-c', '--copy', action='store_true',
        help='Copy files instead of moving (default is move)'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '--log-file', type=str, metavar='FILE',
        help='Write logs to a file (e.g., organizer.log)'
    )
    parser.add_argument(
        '--config', type=str, metavar='JSON_FILE',
        help='JSON file with custom category definitions'
    )
    parser.add_argument(
        '--ignore', nargs='+', default=[], metavar='PATTERN',
        help='Glob patterns to ignore (e.g., "*.tmp" "__pycache__")'
    )
    parser.add_argument(
        '--conflict', choices=CONFLICT_MODES, default='rename',
        help='How to handle duplicate filenames (default: rename)'
    )
    return parser.parse_args()


# ============================================================================
# Main entry point
# ============================================================================

def main() -> None:
    args = _parse_arguments()

    # Initial logging (basic console)
    _configure_logging(verbose=args.verbose, log_file=Path(args.log_file) if args.log_file else None)

    base_path = Path(args.path)
    if not base_path.exists():
        logging.error('Path does not exist: %s', base_path)
        sys.exit(1)

    # Load custom categories if provided
    categories = DEFAULT_CATEGORIES.copy()
    if args.config:
        try:
            custom_cats = _load_custom_categories(Path(args.config))
            categories.update(custom_cats)  # Merge; custom overrides same keys
            logging.info('Loaded custom categories from %s', args.config)
        except ValueError as e:
            logging.error('Configuration error: %s', e)
            sys.exit(1)

    # Build configuration object
    try:
        config = OrganizerConfig(
            base_path=base_path,
            categories=categories,
            recursive=args.recursive,
            dry_run=args.dry_run,
            move=not args.copy,
            ignore_patterns=args.ignore,
            conflict_mode=args.conflict,
            verbose=args.verbose,
            log_file=Path(args.log_file) if args.log_file else None
        )
    except ValueError as e:
        logging.error('Invalid configuration: %s', e)
        sys.exit(1)

    # Run the organizer
    organizer = FileOrganizer(config)
    organizer.run()


if __name__ == '__main__':
    main()
