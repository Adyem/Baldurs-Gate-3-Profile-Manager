from pathlib import Path
import logging
import shutil
import os
import configuration

def ensure_directories_exist(directories):
    """
    Given an iterable of Path objects, create each one (and parents)
    if it doesn’t already exist. Returns a list of the paths that
    were actually created.
    """
    created = []
    for path in directories:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create {path!r}: {e}")
        else:
            if path.exists() and path not in created:
                created.append(path)
                logger.info(f"Ensured directory: {path}")
    return created


def initialize_current_profile(data_dir: Path, default_profile: str = "default_profile"):
    """
    Ensure that a file named 'current_profile' exists in the specified data directory.
    If it does not exist, create it and write `default_profile` as its sole content
    (no trailing newline).
    Returns True if the file was created, False if it already existed.
    """
    file_path = Path(data_dir) / "current_profile"
    if file_path.exists():
        logger.info(f"current_profile already exists at {file_path}")
        return False
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('w', newline='') as f:
            f.write(default_profile)
    except Exception as e:
        logger.error(f"Failed to create current_profile at {file_path}: {e}")
        raise
    else:
        logger.info(f"Created current_profile at {file_path}")
        return True


def initialize_saved_profiles(profile_root: Path = None,
                               saved_profiles_dir: Path = None,
                               active_profile_name: str = None,
                               default_dir_name: str = "default_profile"):
    """
    On first run, copy the active profile from PROFILE_ROOT to a new folder
    named `default_dir_name` inside SAVED_PROFILES_DIR.
    Returns True if copied, False if already exists or source missing.
    """
    root = Path(profile_root) if profile_root is not None else Path(configuration.PROFILE_ROOT)
    saved_dir = Path(saved_profiles_dir) if saved_profiles_dir is not None else Path(configuration.SAVED_PROFILES_DIR)
    active_name = active_profile_name if active_profile_name is not None else configuration.ACTIVE_PROFILE_NAME
    dest = saved_dir / default_dir_name

    if dest.exists():
        logger.info(f"Default profile already initialized at {dest}")
        return False
    src = root / active_name
    if not src.exists():
        logger.error(f"Active profile source not found at {src}")
        return False
    try:
        shutil.copytree(src, dest)
    except Exception as e:
        logger.error(f"Failed to copy profile from {src} to {dest}: {e}")
        raise
    else:
        logger.info(f"Copied default profile from {src} to {dest}")
        return True


def check_and_make_dirs(base_path: Path = None):
    """
    Ensure that the folders 'temp', 'saved profiles', 'crashes', and 'data'
    exist under base_path (or CWD if none given), then initialize
    current_profile and saved profiles.
    Returns a list of directories that were actually created.
    """
    base = Path(base_path) if base_path is not None else Path.cwd()
    dirs = [
        Path(configuration.TEMP_FOLDER),
        Path(configuration.SAVED_PROFILES_DIR),
        Path(configuration.CRASH_FOLDER),
        Path(configuration.DATA_FOLDER),
    ]
    created_dirs = ensure_directories_exist(dirs)
    initialize_current_profile(data_dir=base / "data")
    initialize_saved_profiles()

    return created_dirs
