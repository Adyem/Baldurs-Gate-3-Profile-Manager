import os
import shutil
import subprocess
from datetime import datetime

# -------- Configuration --------
# Location for the player's profiles.
PROFILE_ROOT = r"C:\Users\Adyem\AppData\Local\Larian Studios\Baldur's Gate 3\PlayerProfiles"

# Directory inside PROFILE_ROOT where saved profiles reside.
SAVED_PROFILES_DIR = os.path.join(PROFILE_ROOT, "SavedProfiles")

# Name of the active folder that the game reads.
ACTIVE_PROFILE_NAME = "Public"

# Name of the folder where crash backups are stored
CRASH_FOLDER = os.path.join(PROFILE_ROOT, "Crash")

# Path to the Baldur's Gate 3 executable (update this path as needed)
BG3_EXE_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Baldurs Gate 3\bin\bg3.exe"

# Define what exit code is considered “normal” (for example, 0)
NORMAL_EXIT_CODE = 0
# -------- End Configuration --------

def list_profiles(profiles_dir):
    """
    List all profile folders in the given profiles directory.
    """
    profiles = []
    for entry in os.listdir(profiles_dir):
        full_path = os.path.join(profiles_dir, entry)
        if os.path.isdir(full_path):
            profiles.append(entry)
    return profiles

def copy_profile(src, dst):
    """
    Copy the entire directory tree from src to dst.
    If dst exists, it will be removed first.
    """
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

def get_next_crash_folder(crash_root):
    """
    Determine the next crash folder name using a timestamp.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"crash_{timestamp}"
    return os.path.join(crash_root, folder_name)

def launch_game(exe_path):
    """
    Launch the game and wait for it to exit.
    Returns the game's exit code.
    """
    try:
        proc = subprocess.Popen([exe_path])
        proc.wait()
        return proc.returncode
    except Exception as e:
        print(f"Error launching game: {e}")
        return 1  # Nonzero exit code indicates an error

def main():
    # Ensure the crash folder exists:
    if not os.path.exists(CRASH_FOLDER):
        os.makedirs(CRASH_FOLDER)
    
    # Check if the saved profiles folder exists; if not, create it.
    first_launch = False
    if not os.path.exists(SAVED_PROFILES_DIR):
        os.makedirs(SAVED_PROFILES_DIR)
        first_launch = True
        print(f"Created the saved profiles directory: {SAVED_PROFILES_DIR}")
    
    active_profile_path = os.path.join(PROFILE_ROOT, ACTIVE_PROFILE_NAME)
    
    # List profiles from the SavedProfiles directory.
    profiles = list_profiles(SAVED_PROFILES_DIR)
    
    # If this is the first launch or no saved profiles exist, save current active profile as default.
    if first_launch or not profiles:
        default_profile = "Default"
        default_profile_path = os.path.join(SAVED_PROFILES_DIR, default_profile)
        print("No saved profiles found. Initializing the profile manager...")
        print(f"Saving the current active profile '{ACTIVE_PROFILE_NAME}' as '{default_profile}'.")
        copy_profile(active_profile_path, default_profile_path)
        profiles = [default_profile]
        print("Default profile created.")
    
    # If there's only one profile, we use it automatically.
    if len(profiles) == 1:
        selected_profile = profiles[0]
        print(f"Only one saved profile '{selected_profile}' found. Using it by default.")
    else:
        # If multiple profiles exist, list them for the user.
        print("Available profiles:")
        for idx, profile in enumerate(profiles, start=1):
            print(f"{idx}: {profile}")

        # Ask user to pick one
        try:
            choice = int(input("Select a profile by number: "))
            if choice < 1 or choice > len(profiles):
                print("Invalid selection.")
                return
        except ValueError:
            print("Invalid input.")
            return

        selected_profile = profiles[choice - 1]

    selected_profile_path = os.path.join(SAVED_PROFILES_DIR, selected_profile)
    print(f"Loading profile '{selected_profile}' into '{ACTIVE_PROFILE_NAME}'...")

    # Backup current Public folder if it exists
    if os.path.exists(active_profile_path):
        backup_public = os.path.join(PROFILE_ROOT, f"Public_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        print(f"Backing up existing '{ACTIVE_PROFILE_NAME}' to '{backup_public}'")
        copy_profile(active_profile_path, backup_public)

    # Replace the active ("Public") folder with the selected profile folder
    print("Copying selected profile to active profile folder...")
    copy_profile(selected_profile_path, active_profile_path)

    # Launch the game
    print("Launching the game...")
    exit_code = launch_game(BG3_EXE_PATH)
    print(f"Game exited with code {exit_code}.")

    # If the game did not exit normally, back up the active profile into the Crash folder.
    if exit_code != NORMAL_EXIT_CODE:
        crash_backup_folder = get_next_crash_folder(CRASH_FOLDER)
        print(f"Crash detected. Backing up active profile to crash folder: {crash_backup_folder}")
        copy_profile(active_profile_path, crash_backup_folder)

    # Save any changes (whether the game exited normally or crashed) back into the selected profile.
    print("Saving changes back to the selected profile...")
    copy_profile(active_profile_path, selected_profile_path)
    print("Profile saved. Exiting program.")

if __name__ == "__main__":
    main()
