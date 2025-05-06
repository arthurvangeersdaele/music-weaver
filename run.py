import subprocess
import sys
import importlib.util
import os


paths = []

def install_if_missing(package):
    global paths
    # Check if the package is already installed
    if importlib.util.find_spec(package) is None:
        print(f"Installing missing package: {package}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    else:
        print(f"Package '{package}' is already installed.")
    
    # Get the file paths of the installed package
    package_spec = importlib.util.find_spec(package)
    if package_spec is not None:
        # If the package is found, return the file path(s)
        # Package location is typically in 'origin' attribute of spec
        if package_spec.origin:
            paths.append(package_spec.origin)
        # Check if 'submodule_search_locations' is available
        if hasattr(package_spec, 'submodule_search_locations') and package_spec.submodule_search_locations:
            for location in package_spec.submodule_search_locations:
                paths.append(location)
        return 1
    return 0

def get_scripts_directory(package_path):
    """
    Given a package path, this function returns the corresponding Scripts directory
    where executables like streamlit are usually located.
    """
    # Ensure the package path is valid
    if not os.path.exists(package_path):
        raise ValueError(f"The provided path does not exist: {package_path}")

    # Step 1: Get the base Python installation directory
    site_packages_dir = os.path.dirname(package_path)
    python_base_dir = os.path.dirname(site_packages_dir)  # Go one level up to find Python install directory

    # Step 2: Build the path to the Scripts directory (where executables are typically located)
    scripts_dir = os.path.join(python_base_dir, 'Scripts')
    
    # Step 3: Check if the scripts directory exists
    if os.path.isdir(scripts_dir):
        return scripts_dir
    else:
        raise FileNotFoundError(f"Scripts directory not found: {scripts_dir}")


# Check and install required packages
install_if_missing("streamlit")
install_if_missing("sounddevice")
install_if_missing("pandas")
install_if_missing("PIL")
install_if_missing("numpy")
install_if_missing("time")

# For each package path, try to add the corresponding Scripts directory to PATH
for package_path in paths:
    try:
        # Get the Scripts directory where the executable is typically located
        scripts_dir = get_scripts_directory(package_path)
        
        # Add to PATH if not already added
        if scripts_dir not in os.environ["PATH"]:
            os.environ["PATH"] += os.pathsep + scripts_dir
            print(f"Added {scripts_dir} to PATH")
        else:
            print(f"{scripts_dir} is already in PATH")
    
    except Exception as e:
        print(f"Error adding path for {package_path}: {e}")

# Optionally, print the updated PATH to verify
print("\nUpdated PATH:")
print(os.environ["PATH"])

# Run the Streamlit script using subprocess
if __name__ == "__main__":
    # We're not running under Streamlit yet, so we can launch the new process
    subprocess.run(["streamlit", "run", "browser_app.py"])  # Avoid recursive calls