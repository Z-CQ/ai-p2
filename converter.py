from prints import ok_print, warn_print, err_print
from world import Solid, Entity, Door, FloorButton, PedestalButton, CubeDropper, Fizzler, ObservationRoom, STEP, NODRAW, TRIGGER, ORIGIN_X, ORIGIN_Y, ORIGIN_Z
import sys
import os
import configparser

# Load configuration
parser = configparser.ConfigParser()
parser.read('config.ini')

STEAM_EXEC = parser.get('General', 'steam_path', fallback="C:\\Program Files (x86)\\Steam\\steam.exe") # Points to the Steam executable
PORTAL_DIR = parser.get('General', 'portal_path', fallback="C:\\Program Files (x86)\\Steam\\steamapps\\common\\Portal 2") # Points to the root Portal 2 directory

"""
A VMF file is structured as such:
versioninfo { }
visgroups { }
viewsettings { }
world { }
entity { }
cameras { }
cordons { }

entity { } exists multiple times, one for each entity, while solid geometry is thrown in solid { } blocks in world { }
cameras { } only needs to contain "activecamera" "-1" and so it will not receive its own variable
cordons { } is similar, in that it only contains "active" "0" and will also not receive its own variable


Listed below is the collection of headers used in VMF files, which will be used to piece together the final VMF file. Feel free to configure if necessary.
Lists will be appended to, not overridden, so if you would like persistent entities or pieces of geometry for whatever reason, this is where to do it.
"""

# Not necessarily important to a VMF file compiling and running.
VERS_INF = """
    "editorversion" "400"
    "editorbuild" "3325"
    "mapversion" "1"
    "formatversion" "100"
    "prefab" "0"
"""

# Empty in the typical Portal 2 hammer map, so it's empty here.
VIS_GROUPS = """"""

# Settings used for the Hammer editor. Included in case you want to edit the map further yourself.
VIEW_SETTINGS = """
    "bSnapToGrid" "1"
    "bShowGrid" "1"
    "bShowLogicalGrid" "0"
    "nGridSpacing" "16"
    "bShow3DGrid" "0"
"""

# Config and brushes for the world itself.
WORLD = """
    "id" "1"
    "mapversion" "1"
    "classname" "worldspawn"
    "detailmaterial" "detail/detailsprites"
	"detailvbsp" "detail.vbsp"
	"maxblobcount" "250"
	"maxpropscreenwidth" "-1"
	"skyname" "sky_black_nofog"
	"paintinmap" "0"
"""

# List of entities to include in the final VMF file.
ENTITIES = []

def validateData(data: dict) -> tuple[str, list, None|dict]:
    """
    Verify data contains what's necessary to piece together the map.\n
    Returns the level name, the world geometry data, and the entities.
    """

    if not "name" in data:
        # Give the user the option to override the default "out.vmf" file or cancel
        warn_print("Optional key \"name\" not found in the data. Default to \"out\"? (this will override existing \"out.vmf\" if it exists) [Y\\n] ", last="")
        act = input()
        if act.lower() == "n" or act.lower() == "no":
            warn_print("Refused to override. Terminating.")
            sys.exit(4)

        # Default to "out.vmf"
        name = "out"
    else:
        ok_print("Found level name.")
        name = data["name"]
    
    if not "level" in data:
        err_print("Required key \"level\" not found in the data. Terminating.")
        sys.exit(4)
    elif not isinstance(data["level"], list): # Ensure the level points to a list
        err_print("Required key \"level\" was found, but isn't a list. Terminating.")
        sys.exit(5)
    elif not all(isinstance(l, list) for l in data["level"]): # Ensure that the list is 2D
        err_print("Required key \"level\" was found, but is a 1-dimensional list. Terminating.")
        sys.exit(5)
    else:
        ok_print("Found geometry information.")

    if not "entities" in data:
        warn_print("Optional key \"entities\" not found in the data. Skipping.")
        entities = None
    else:
        ok_print("Found entity information.")
        entities = data["entities"]

    return name, data["level"], entities


def convert(data: dict, bounding_box: bool) -> tuple[str, str, str]:
    """Generates a .vmf file into the maps folder and compiles it. Returns the VMF file path."""
    map_name, world, ent = validateData(data)

    maps_dir = os.path.join(PORTAL_DIR, "sdk_content", "maps")
    if not os.path.exists(maps_dir):
        warn_print("Output folder \"Portal 2\\sdk_content\\maps\" does not exist. Creating . . .")
        os.mkdir(maps_dir)

    with open(os.path.join(maps_dir, "{0}.vmf".format(map_name)), "w+") as f:

        solids: list[Solid] = []
        entities: list[Entity] = []

        vmf = """
versioninfo
{{
{0}
}}
visgroups
{{
{1}
}}
viewsettings
{{
{2}
}}
world
{{
{3}
}}
entity
{{
    "id" "2"
    "classname" "func_instance"
    "targetname" "pti_ents"
    "file" "instances/p2editor/global_pti_ents.vmf"
    "fixup_style" "0"
    "origin" "0 0 -3500"
}}
entity
{{
	"id" "3"
	"classname" "func_instance"
	"file" "instances/p2editor/arrival_departure_transition_ents.vmf"
	"fixup_style" "3"
	"replace01" "$arrival_video ???"
	"replace02" "$departure_video ???"
	"origin" "-2500 -2500 -5500"
	editor
	{{
		"color" "255 255 255"
		"visgroupshown" "1"
		"visgroupautoshown" "1"
		"logicalpos" "[0 0]"
	}}
}}
entity
{{
	"id" "4"
	"classname" "func_instance"
	"file" "instances/p2editor/elevator_entrance.vmf"
	"fixup_style" "0"
	"origin" "-2000 2000 -5500"
	"replace01" "$no_player_start 0"
	editor
	{{
		"color" "255 255 255"
		"visgroupshown" "1"
		"visgroupautoshown" "1"
		"logicalpos" "[0 0]"
	}}
}}
entity
{{
	"id" "5"
	"classname" "func_instance"
	"file" "instances/p2editor/elevator_exit.vmf"
	"fixup_style" "0"
	"origin" "-2000 -2000 -6500"
	editor
	{{
		"color" "255 255 255"
		"visgroupshown" "1"
		"visgroupautoshown" "1"
		"logicalpos" "[0 0]"
	}}
}}
{4}
{5}
cameras
{{
	"activecamera" "-1"
}}
cordons
{{
	"active" "0"
}}
        """

        EXIT_TRIGGER = """
entity
{{
    "id" "{0}"
    "classname" "trigger_once"
    "targetname" "end_trigger"
    "origin" "{1}"
    connections {{ 
        "OnTrigger" "pti_ents\x1binstance:@relay_pti_level_end;Trigger\x1b0\x1b-1" 
    }} 
    {2} 
}}
"""

        # declare a string which will hold information on the exit trigger
        exit_raw = ""

        prop_dirs = {
            "south": (0, 90, 0),
            "north": (0, 270, 0),
            "west": (0, 180, 0),
            "east": (0, 0, 0)
        }

        # Iterate over each tile and generate geometry or an entity according to the tile
        for y, row in enumerate(world):
            for x, tile in enumerate(row):
                
                # It's solid geometry
                if tile == "W" or tile == "PW":

                    portalable = True if tile == "PW" else False

                    ok_print("Found tile at {0},{1}. Portalable: {2}. Generating a wall...".format(x, y, portalable))
                    solid = Solid(portalable, x, y, height=STEP * 3)
                    solids.append(solid)

                else:
                    # Generate the ceiling and floor of the chamber
                    ok_print("No wall found at {0},{1}. Generating a floor...".format(x, y))
                    solid = Solid(False, x, y, z0=-STEP)
                    solids.append(solid)

                    if tile is None or not str(tile).startswith("CD"):
                        ok_print("Generating the ceiling...")
                        solid_c = Solid(False, x, y, z0=STEP * 3)
                        solids.append(solid_c)


                    # Generate an entity
                    if not tile is None:
                        tile = str(tile)
                        if tile == "EN":
                            starting_door = Door([x, y, 0], [0, 0, 0], "EN", 1)
                            frame, _ = starting_door.resolve_position(world)

                            # Copy frame origin to avoid messing with the door's and update it since its 64 units lower than the door
                            frame.origin = [frame.origin[0], frame.origin[1], frame.origin[2] + 64]
                            entities.append(starting_door)
                            entities.append(frame)

                            # Generate a shorter chunk to place above the door
                            sd_top = Solid(False, x, y, z0=STEP, height=STEP * 2)
                            solids.append(sd_top)
                        elif tile == "EX":
                            exit_door = Door([x, y, 0], [0, 0, 0], "EX", 0, start_closed=True)
                            exit_frame, (ox, oy) = exit_door.resolve_position(world)

                            # Trigger one and a half tile deeper into the hallway than the door's inside tile
                            # This is an ideal range. Closer would end the level too soon, further would risk the player reaching the restart level trigger packed into the p2editor exit door instance
                            TRIG_DEPTH_TILES = -1.5
                            tx = exit_door.origin[0] + ox * TRIG_DEPTH_TILES
                            ty = exit_door.origin[1] + oy * TRIG_DEPTH_TILES

                            # World origin string for entity
                            trigger_x = ORIGIN_X + tx * STEP + STEP // 2
                            trigger_y = ORIGIN_Y + ty * STEP + STEP // 2
                            trigger_z = ORIGIN_Z + (-STEP + 64)
                            exit_origin = f"{trigger_x} {trigger_y} {trigger_z}"

                            # Make the trigger using our Solid class
                            trigger_solid = Solid(portalable=False, x=tx, y=ty, material_override=TRIGGER)

                            # Make our trigger entity
                            exit_raw = EXIT_TRIGGER.format(Solid.nextID, exit_origin, trigger_solid.convert())
                            Solid.nextID += 1


                            # Copy frame origin to avoid messing with the door's and update it since its 64 units lower than the door
                            exit_frame.origin = [exit_frame.origin[0], exit_frame.origin[1], exit_frame.origin[2] + 64]
                            entities.append(exit_door)
                            entities.append(exit_frame)

                            # Generate a shorter chunk to place above the door
                            sd_top = Solid(False, x, y, z0=STEP, height=STEP * 2)
                            solids.append(sd_top)
                        elif tile.startswith("FB"):

                            floor_button = FloorButton([x, y, 0], [0, 0, 0], tile)
                            entities.append(floor_button)
                        
                        elif tile.startswith("PB"):

                            pedestal_button = PedestalButton([x, y, 0], [0, 0, 0], tile)
                            entities.append(pedestal_button)

                        elif tile.startswith("CB"):
                            loose_cube = Entity("prop_weighted_cube", [x, y, 32], [0, 0, 0], tile)
                            entities.append(loose_cube)

                        elif tile.startswith("CD"):
                            cube_dropper = CubeDropper([x, y, STEP * 6 + (STEP // 2)], [0, 0, 0], tile)
                            entities.append(cube_dropper)

                        elif tile.startswith("FZ"):
                            fizzler = Fizzler([x, y, 0], tile)
                            entities.append(fizzler)

                        elif tile.startswith("T"):
                            turret = Entity("npc_portal_turret_floor", [x, y, 0], [0, 0, 0], tile)
                            turret.extras = "    \"AllowShootThroughPortals\" \"1\"\n    \"DamageForce\" \"1\""
                            entities.append(turret)

                        elif tile.startswith("OR"):
                            observation_room = ObservationRoom([x, y, STEP * 2 - (STEP // 2)], [0, 0, 0], tile)
                            observation_room.resolve_position(world)

                            or_bottom = Solid(False, x, y)
                            or_top = Solid(False, x, y, z0=STEP * 2)

                            entities.append(observation_room)
                            solids.append(or_bottom)
                            solids.append(or_top)




        if len(solids) <= 0:
            err_print("No geometry saved. Terminating.")
            sys.exit(6)

    

        if bounding_box:
            # no draw boundaries to prevent leaks, since we don't have the best manual control with this
            ok_print("Generating nodraw boundaries.")
            BUFFER = 16

            h = len(world)
            w = max(len(row) for row in world) if h else 0

            min_x = -BUFFER
            max_x = w - 1 + BUFFER
            min_y = -BUFFER
            max_y = h - 1 + BUFFER

            BOUND_Z0 = -STEP * 5
            BOUND_H  = STEP * 17

            # Top + bottom rows of the bounding box
            for x in range(min_x, max_x + 1):
                solids.append(Solid(False, x, min_y, z0=BOUND_Z0, height=BOUND_H, material_override=NODRAW))
                solids.append(Solid(False, x, max_y, z0=BOUND_Z0, height=BOUND_H, material_override=NODRAW))

            # Left + right columns of the bounding box
            for y in range(min_y + 1, max_y):
                solids.append(Solid(False, min_x, y, z0=BOUND_Z0, height=BOUND_H, material_override=NODRAW))
                solids.append(Solid(False, max_x, y, z0=BOUND_Z0, height=BOUND_H, material_override=NODRAW))

            # Fill boundary floor + ceiling across the whole buffered area
            BOUND_FLOOR_Z0 = -STEP * 6
            BOUND_CEIL_Z0  = STEP * 11

            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    # boundary floor
                    solids.append(Solid(
                        False, x, y,
                        z0=BOUND_FLOOR_Z0,
                        height=STEP,
                        material_override=NODRAW
                    ))

                    # boundary ceiling
                    solids.append(Solid(
                        False, x, y,
                        z0=BOUND_CEIL_Z0,
                        height=STEP,
                        material_override=NODRAW
                    ))
        else:
            warn_print("No bounding box generated.")


        DEFAULT_BINDINGS = {
            ("FloorButton", "Door"):            ("pressed", "enable", "released", "disable"),
            ("PedestalButton", "Door"):         ("pressed", "enable", "released", "disable"),
            ("PedestalButton", "CubeDropper"):  ("pressed", "trigger", None, None),
            ("FloorButton", "Fizzler"):         ("pressed", "deactivate", "released", "activate"),
            ("FloorButton", "CubeDropper"):     ("pressed", "trigger", None, None),
            ("PedestalButton", "Fizzler"):      ("pressed", "deactivate", "released", "activate")
        }

        def bind(src: Entity, dst: Entity):

            # Get the ports for src and dst
            key = (src.__class__.__name__, dst.__class__.__name__)
            rule = DEFAULT_BINDINGS.get(key)

            # No rule? Skip
            if not rule:
                warn_print(f"No bind rule for {key}")
                return

            # Unpack the response
            p_on, r_on, p_off, r_off = rule

            # Compile outputs for on/off ports and append to src.outputs
            for out in src.compile_link(p_on, dst, r_on):
                src.add_output(*out)

            if p_off and r_off:
                for out in src.compile_link(p_off, dst, r_off):
                    src.add_output(*out)

            # Tell the destination it received a connection
            dst.on_connected(src)


        # Parse necessary entity information (connections, autodrop, autorespawn, stuff like that)
        if ent is None:
            warn_print("Skipping entity parsing...")
        else:
            ok_print("Parsing entity data...")
            
            entity_by_name = {e.target_name: e for e in entities}

            # Iterate through all entity information
            for name, info in ent.items():
                src = entity_by_name.get(name)
                if not src:
                    warn_print(f"{name} not spawned; skipping.")
                    continue

                if "conn" in info:
                    for target_name in info["conn"]:
                        dst = entity_by_name.get(target_name)
                        if not dst:
                            warn_print(f"{name} conn target {target_name} not found; skipping.")
                            continue

                        bind(src, dst)
                if "delay" in info:
                    src.extras += "\n    \"Delay\" \"{0}\"\n    \"istimer\" \"1\"".format(info["delay"])
                if "facing" in info and info["facing"] in prop_dirs:
                    src.angles = list(src.angles)
                    src.angles[1] = prop_dirs[info["facing"]][1]


        all_solids = "".join([s.convert() for s in solids])
        wrld = WORLD + all_solids

        all_ents = "".join([e.convert() for e in entities])
        vmf = vmf.format(VERS_INF, VIS_GROUPS, VIEW_SETTINGS, wrld, exit_raw, all_ents)

        f.write(vmf)

        f.close()

        return os.path.join(maps_dir, "{0}.vmf".format(map_name)), maps_dir, map_name