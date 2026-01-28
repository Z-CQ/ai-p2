from prints import err_print, warn_print, ok_print, get_input
from converter import convert, STEAM_EXEC, PORTAL_DIR

try:
    from google import genai
    from google.genai.interactions import GenerationConfigParam
    HAS_GENAI = True
except ImportError:
    genai = None
    GenerationConfigParam = None
    warn_print("Google GenAI library not found. AI features will be disabled.")
    HAS_GENAI = False

import os
import json
import sys
import subprocess
import shutil
import configparser

# Load config
parser = configparser.ConfigParser()
parser.read('config.ini')

# Used to optimize the map. Not required, but important for optimization.
COMPILE_VIS = parser.getboolean('General', 'compile_vis', fallback=True)

# Compile with lighting?
COMPILE_RAD = parser.getboolean('General', 'compile_rad', fallback=True)

# AI Settings
AI_KEY = parser.get('AI', 'key', fallback=None)
AI_MODEL = parser.get('AI', 'model', fallback="gemini-3-flash-preview")
MAX_TOKENS = parser.getint('AI', 'max_tokens', fallback=4096)

if AI_KEY is None:
    warn_print("No API key found for Google GenAI. AI features will be disabled.")
    HAS_GENAI = False

"""
Verifies Steam exists at the specified location
"""
def verifySteam():
    """Ensures the Steam executable exists"""
    if not os.path.exists(STEAM_EXEC):
        err_print("steam.exe not found. Terminating.")
        sys.exit(1)

    if not os.path.isfile(STEAM_EXEC):
        err_print("STEAM_EXEC was found, but isn't a file. Terminating.")
        sys.exit(1)

    if not STEAM_EXEC.lower().endswith(".exe"):
        err_print("STEAM_EXEC was not found, but isn't an executable. Terminating.")
        sys.exit(1)

    ok_print("Found Steam.")


def verifyPortal():
    """Ensures Portal 2 exists at the given directory"""
    if not os.path.exists(PORTAL_DIR):
        err_print("Portal 2 not found. Terminating.")
        sys.exit(1)

    # Ensures there's an actual executable in the Portal 2 directory
    if not os.path.exists(os.path.join(PORTAL_DIR, "portal2.exe")):
        err_print("Portal 2 directory exists, but the executable could not found. Terminating.")
        sys.exit(1)

    ok_print("Found Portal 2.")


def getOptions() -> tuple[bool, bool, bool]:
    """Set options for map generation."""

    # Launch on compile?
    launch = False if get_input("Launch Portal 2 on map build? [Y/n] ").lower() in ["n", "no"] else True

    # Surround the map in a nodraw bounding box? (Recommended)
    bb = False if get_input("Surround the map with a nodraw bounding box? (Recommended) [Y/n] ").lower() in ["n", "no"] else True

    # Use A.I to generate the map?
    if HAS_GENAI:
        useAI = False if get_input("Generate the map by A.I? [Y/n] ").lower() in ["n", "no"] else True
    else:
        warn_print("Google GenAI library not found. Defaulting to user-made JSON maps. You can install the library with 'pip install google-genai' in a terminal.")
        useAI = False

    return launch, bb, useAI


def assignJSONMap() -> str:
    """Prompt the user for a JSON file and return the path after validation."""    
    while True:

        jmap = get_input("JSON file to generate P2 map from: ")

        if not os.path.exists(jmap):
            err_print("File does not exist.")
            continue

        if not os.path.isfile(jmap):
            err_print("Input is not a file.")
            continue

        if not jmap.lower().endswith(".json"):
            err_print("Passed file is not a JSON file.")
            continue

        break

    ok_print("Found.")
    return jmap

def open_json(path: str) -> dict:
    """Open and parse a JSON file, returning the data as a dictionary."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            jsonData = json.load(f)
        return jsonData
    except json.JSONDecodeError:
        err_print("JSON data was invalid.")
        sys.exit(2)
    except Exception as e:
        err_print("Exception occurred: {0}".format(e))
        sys.exit(3)

    return jsonData


def generate_map_with_ai(prompt: str) -> str:
    """Generate a Portal 2 map using Google GenAI based on the provided prompt and return the path to the file."""

    # Last catch for GenAI library
    if not HAS_GENAI or genai is None or GenerationConfigParam is None:
        err_print("Google GenAI library not found. Cannot generate map with A.I.")
        sys.exit(1)

    # Create a client
    client = genai.Client(api_key=AI_KEY)

    # See if we can read the base prompt, which is required so the AI knows what's what
    try:
        base = open("message.txt", "r", encoding="utf-8").read()
        prompt = base.replace("{user_request}", prompt)
    except Exception as e:
        err_print("Failed to read message.txt.")
        sys.exit(7)

    # ai assisted in making this schema
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["name", "level", "entities"],
        "properties": {
            "name": {"type": "string"},
            "level": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {"anyOf": [{"type": "null"}, {"type": "string"}]}
            }
            },
            "entities": {
            "type": "object",
            "minProperties": 1
        }
        }
    }


    # Create a response
    res = client.models.generate_content(
        model=AI_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": schema,
            "temperature": 0.1,
            "max_output_tokens": MAX_TOKENS,
        }
    )

    raw = res.text

    # Ensure that there IS a response
    if raw is None:
        err_print("No response from A.I.")
        sys.exit(9)

    # log it
    print("\n\nA.I Response:\n{0}\n\n".format(raw))

    # write it to _last_raw.txt for debugging
    with open("maps/_last_raw.txt", "w", encoding="utf-8") as f:
        f.write(raw)

    data = json.loads(raw)

    os.makedirs("maps", exist_ok=True)
    path = os.path.join("maps", f"{data['name']}.json")

    # Write the JSON to a file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # return the path
    return path


def main():
    verifySteam()
    verifyPortal()
    
    launch, bb, useAI = getOptions()

    if not useAI:
        rawFile = assignJSONMap()
    else:
        maps_dir = os.path.join(os.path.dirname(__file__), "maps")
        if not os.path.exists(maps_dir):
            warn_print("Output folder \"maps\" does not exist. Creating . . .")
            os.mkdir(maps_dir)

        prompt = get_input("Enter a prompt for the A.I to generate a Portal 2 map from: ")
        ok_print("Generating JSON map from A.I . . .")
        rawFile = generate_map_with_ai(prompt)
        ok_print(f"Generated JSON map at {rawFile}")


    jsonData = open_json(rawFile)
    
    file_path, maps_dir, map_name = convert(jsonData, bb)
    ok_print("Map generated from JSON.")

    if launch:
        ok_print("Compiling map . . .")
        ok_print("Generating BSP . . .")

        """
        Hammer compiles and runs maps like this:

        CD into PORTAL_DIR/bin
        vbsp.exe -game ../portal2 <mapfile.vmf>

        Then, if VIS is enabled, while still CD'd into PORTAL_DIR/bin:
        vis.exe -game ../portal2 <mapfile>

        Then, if RAD is enabled, while still CD'd into PORTAL_DIR/bin:
        rad.exe -game ../portal2 <mapfile>

        Then finally, run steam.exe with Portal as the applaunch arg, the game arg as ../portal2, and +map as the map name without extension.
        We can effectively recreate this process with subprocess calls.
        """

        print("File path: {0}".format(file_path))

        # Define paths to executables
        bin_dir = os.path.join(PORTAL_DIR, "bin")
        vbsp_exe = os.path.join(bin_dir, "vbsp.exe")
        vis_exe = os.path.join(bin_dir, "vvis.exe")
        rad_exe = os.path.join(bin_dir, "vrad.exe")

        # Run vbsp to get the initial map file
        subprocess.run(
            [vbsp_exe, "-game", os.path.join(PORTAL_DIR, "portal2"), file_path],
            check=True
        )
        ok_print("Map compiled successfully.")

        # Compile VIS if enabled (highly recommended)
        if COMPILE_VIS:
            subprocess.run(
            [vis_exe, "-game", os.path.join(PORTAL_DIR, "portal2"), file_path],
            check=True
            )
            ok_print("Map vis compiled successfully.")

        # Compile RAD if enabled
        if COMPILE_RAD:
            subprocess.run(
            [rad_exe, "-game", os.path.join(PORTAL_DIR, "portal2"), file_path],
            check=True
            )
            ok_print("Map rad compiled successfully.")

        # Copy the output BSP from sdk_content/maps/ to Portal 2/portal2/maps
        src_bsp = os.path.join(maps_dir, "{0}.bsp".format(map_name))
        dst_bsp = os.path.join(PORTAL_DIR, "portal2", "maps", "{0}.bsp".format(map_name))
        os.makedirs(os.path.dirname(dst_bsp), exist_ok=True)
        shutil.copy2(src_bsp, dst_bsp)
        ok_print("Map copied to Portal 2 maps directory.")


        ok_print("Launching Portal 2 . . .")

        # Run Portal 2 with the map
        subprocess.run([
            STEAM_EXEC,
            "-applaunch",
            "620",
            "-game",
            os.path.join(PORTAL_DIR, "portal2"),
            "+map",
            os.path.splitext(os.path.basename(file_path))[0],
        ], check=True)

        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("")
        err_print("Process interrupted by user. Exiting.")
        sys.exit(10)