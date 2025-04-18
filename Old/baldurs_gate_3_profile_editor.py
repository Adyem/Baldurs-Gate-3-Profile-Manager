import os
import shutil
import subprocess
import time
from datetime import datetime
import psutil  # requires: pip install psutil

# -------- Configuration --------
# Location for the player's profiles.
PROFILE_ROOT = r"C:\Users\Adyem\AppData\Local\Larian Studios\Baldur's Gate 3\PlayerProfiles"

# Directory inside PROFILE_ROOT where saved profiles reside.
SAVED_PROFILES_DIR = os.path.join(PROFILE_ROOT, "SavedProfiles")

# Name of the active folder that the game reads.
ACTIVE_PROFILE_NAME = "Public"

# Name of the folder where crash backups are stored.
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
    if os.path.exists(profiles_dir):
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

def is_game_running(exe_path):
    """
    Check if any process is running that has the given executable path.
    """
    for proc in psutil.process_iter(['exe']):
        try:
            if proc.info['exe'] and os.path.normcase(proc.info['exe']) == os.path.normcase(exe_path):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def launch_game(exe_path):
    """
    Launch the game and wait for the actual game process to exit.
    This function uses psutil to poll for the BG3 executable;
    it waits until no process with the executable remains.
    """
    try:
        # Start the launcher process.
        proc = subprocess.Popen([exe_path])
        print("Launcher process started. Waiting for the game to launch...")
        time.sleep(5)  # Allow time for the launcher to spawn the actual game processes.

        # Poll until no processes with BG3_EXE_PATH are found.
        # (This assumes the actual game uses the same executable path.)
        while is_game_running(exe_path):
            print("Game process detected... waiting for it to exit.")
            time.sleep(5)  # Poll every 5 seconds.

        # Optionally, capture an exit code; here we assume normal termination.
        return NORMAL_EXIT_CODE
    except Exception as e:
        print(f"Error launching game: {e}")
        return 1  # Nonzero exit code indicates an error

def copy_profile_option():
    """
    Implements the 'copy a profile' option.
    Lists available profiles, asks for the profile to copy from, and the new profile name.
    Prevents using the reserved name 'NoProfile'.
    """
    profiles = list_profiles(SAVED_PROFILES_DIR)
    if not profiles:
        print("No saved profiles available to copy from.")
        return

    print("Available profiles to copy from:")
    for idx, profile in enumerate(profiles, start=1):
        folder_path = os.path.join(SAVED_PROFILES_DIR, profile)
        print(f"{idx}: {profile} (located in {folder_path})")

    try:
        src_choice = int(input("Select a profile to copy from by number: "))
        if src_choice < 1 or src_choice > len(profiles):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input.")
        return

    source_profile = profiles[src_choice - 1]
    new_profile_name = input("Enter the new profile name: ").strip()
    
    # Prevent the reserved name "NoProfile" from being used.
    if new_profile_name.lower() == "noprofile":
        print("Invalid profile name. 'NoProfile' is reserved and cannot be used.")
        return

    if not new_profile_name:
        print("New profile name cannot be empty.")
        return

    new_profile_path = os.path.join(SAVED_PROFILES_DIR, new_profile_name)
    if os.path.exists(new_profile_path):
        print(f"A profile with the name '{new_profile_name}' already exists. Aborting copy.")
        return

    source_profile_path = os.path.join(SAVED_PROFILES_DIR, source_profile)
    copy_profile(source_profile_path, new_profile_path)
    print(f"Profile '{source_profile}' copied successfully to '{new_profile_name}'.")

def launch_game_with_profile():
    """
    Lists all saved profiles and asks the user to choose one to load.
    The player can also type "NoProfile" to launch the game with the currently active profile.
    Once a profile is chosen, it is loaded into the active folder and the game is launched.
    After the game exits, if launched via a profile selection (i.e. not NoProfile),
    changes are saved back, and if the game crashed, the active profile is backed up.
    """
    profiles = list_profiles(SAVED_PROFILES_DIR)
    print("Available profiles from:", SAVED_PROFILES_DIR)
    if profiles:
        for idx, profile in enumerate(profiles, start=1):
            folder_path = os.path.join(SAVED_PROFILES_DIR, profile)
            print(f"{idx}: {profile} (located in {folder_path})")
    else:
        print("No saved profiles found.")

    print("\nEnter the number corresponding to the profile you want to load,")
    print("or type 'NoProfile' to launch the game with the currently active profile.")
    
    choice = input("Your selection: ").strip()

    use_profile = None  # This will hold the name of the saved profile to load.
    if choice.lower() == "noprofile":
        use_profile = None
    else:
        try:
            profile_index = int(choice)
            if 1 <= profile_index <= len(profiles):
                use_profile = profiles[profile_index - 1]
            else:
                print("Invalid selection number.")
                return
        except ValueError:
            print("Invalid input. Please enter a number or 'NoProfile'.")
            return

    active_profile_path = os.path.join(PROFILE_ROOT, ACTIVE_PROFILE_NAME)
    
    if use_profile is not None:
        selected_profile_path = os.path.join(SAVED_PROFILES_DIR, use_profile)
        print(f"\nLoading profile '{use_profile}' from:")
        print(f"    {selected_profile_path}")
        print(f"into the active profile folder:")
        print(f"    {active_profile_path}")
        
        # Backup the current active profile if it exists.
        if os.path.exists(active_profile_path):
            backup_public = os.path.join(PROFILE_ROOT, f"{ACTIVE_PROFILE_NAME}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            print(f"Backing up current active profile to: {backup_public}")
            copy_profile(active_profile_path, backup_public)
        
        # Copy the selected profile into the active profile folder.
        print("Copying selected profile into active profile folder...")
        copy_profile(selected_profile_path, active_profile_path)
    else:
        print("\nLaunching game with the current active profile. No profile is loaded or changed.")

    # Launch the game and wait for it to exit.
    print("\nLaunching Baldur's Gate 3...")
    exit_code = launch_game(BG3_EXE_PATH)
    print(f"Game exited with code {exit_code}.")

    # If the game did not exit normally, back up the current active profile into the Crash folder.
    if exit_code != NORMAL_EXIT_CODE:
        crash_backup_folder = get_next_crash_folder(CRASH_FOLDER)
        print(f"Game crash detected. Backing up active profile to crash folder: {crash_backup_folder}")
        copy_profile(active_profile_path, crash_backup_folder)
    
    # If a profile was loaded (i.e. not NoProfile), save any changes back to the saved profile.
    if use_profile is not None:
        print("Saving changes back to the saved profile...")
        copy_profile(active_profile_path, selected_profile_path)
        print(f"Profile '{use_profile}' has been updated with changes from the game.")

def main():
    # Ensure the crash folder exists.
    if not os.path.exists(CRASH_FOLDER):
        os.makedirs(CRASH_FOLDER)
    
    # Ensure the saved profiles folder exists.
    if not os.path.exists(SAVED_PROFILES_DIR):
        os.makedirs(SAVED_PROFILES_DIR)
        print(f"Created the saved profiles directory: {SAVED_PROFILES_DIR}")
    
    while True:
        print("\nMain Menu:")
        print("1: Load a profile into the game and launch")
        print("2: Copy an existing profile to create a new one")
        print("3: Exit")
        
        choice = input("Enter 1, 2, or 3: ").strip()
        
        if choice == "1":
            launch_game_with_profile()
            # Optionally pause here to see logs before exit.
            input("Press Enter to exit the launcher...")
            break
        elif choice == "2":
            copy_profile_option()
            launch_now = input("Do you want to launch the game now with a selected profile? (y/n): ").strip().lower()
            if launch_now == "y":
                launch_game_with_profile()
                input("Press Enter to exit the launcher...")
                break
            else:
                print("Returning to the main menu...")
        elif choice == "3":
            print("Exiting the program.")
            break
        else:
            print("Invalid selection. Please try again.")

if __name__ == "__main__":
    main()
