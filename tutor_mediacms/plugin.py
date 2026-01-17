import os
import pkg_resources
from tutor import hooks

# Configuration
config = {
    # Add any default configuration variables here
    "defaults": {
        "MEDIACMS_BASE_URL": "https://deic.mediacms.io",
    }
}

hooks.Filters.CONFIG_DEFAULTS.add_items(
    [
        ("MEDIACMS_BASE_URL", config["defaults"]["MEDIACMS_BASE_URL"]),
    ]
)

# 1. Inject the XBlock source code into the build context
# We assume the source code is located in a 'mediacms_xblock' folder within this package.
# We will write it to openedx/requirements/mediacms-xblock in the Tutor env.

def get_xblock_patches():
    """
    Reads all files in the bundled 'mediacms_xblock' directory
    and returns a list of (filename, content) patches.
    """
    patches = []
    # Identify where the xblock source is relative to this plugin file
    # If installed as a package, we use pkg_resources or __file__
    # Because we moved 'mediacms_xblock' to be a sibling of 'tutor_mediacms',
    # we need to go up one level.
    # Structure:
    # tutor-mediacms/
    #   tutor_mediacms/
    #      plugin.py
    #   mediacms_xblock/
    #      ...
    
    # However, if we want this to work when pip installed, 'mediacms_xblock' should likely be 
    # included as package data INSIDE 'tutor_mediacms' or specified in MANIFEST.in.
    # For this specific local setup, we'll traverse up.
    
    request_dir = os.path.join(os.path.dirname(__file__), "..", "mediacms_xblock")
    request_dir = os.path.abspath(request_dir)
    
    if not os.path.exists(request_dir):
        return []

    for root, dirs, files in os.walk(request_dir):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, request_dir)
            
            # Read content
            try:
                with open(full_path, "r", encoding="utf-8") as f_obj:
                    content = f_obj.read()
            except UnicodeDecodeError:
                # Skip binary files for the simple text patcher if possible, 
                # or handle them? ENV_PATCHES usually expects strings.
                # If we have binary (images), this might fail.
                # For now, skip binaries or warn.
                continue

            # Target path in build env
            target_path = f"openedx/requirements/mediacms-xblock/{rel_path}"
            patches.append((target_path, content))
            
    return patches

# Register the patches
hooks.Filters.ENV_PATCHES.add_items(get_xblock_patches())

# 2. Add the requirement to install it
# We use ENV_TEMPLATE_VARIABLES to append to the existing list safeley
@hooks.Filters.ENV_TEMPLATE_VARIABLES.add()
def _add_mediacms_requirements(env_vars):
    # env_vars is a list of (key, value) tuples
    new_req = "-e ./requirements/mediacms-xblock"
    found = False
    
    # Try to find existing requirement list and append to it
    for key, value in env_vars:
        if key == "OPENEDX_EXTRA_PIP_REQUIREMENTS":
            if isinstance(value, list):
                value.append(new_req)
            found = True
            break
            
    # If not found, add it
    if not found:
        env_vars.append(("OPENEDX_EXTRA_PIP_REQUIREMENTS", [new_req]))
        
    return env_vars
