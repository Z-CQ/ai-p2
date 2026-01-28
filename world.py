from prints import warn_print, ok_print, err_print

WALKABLE_TYPES = [
    "FB",   # floor button
    "PB",   # pedestal button
    "CD",   # cube dropper
    "CB",   # loose cube
    "FZ",   # fizzler volume
    "T"     # turret
]

def is_walkable(tile: str | None) -> bool:
    """Is the tile we're looking at walkable?"""
    if tile is None:
        return True
    return any(tile.startswith(t) for t in WALKABLE_TYPES)



STEP = 128
"""How big is one tile? By default, 128 is used in the P2 editor."""

ORIGIN_X = -STEP
ORIGIN_Y = 0
ORIGIN_Z = 0

SOLID_DETAILS = """
    solid
    {{
        "id" "{0}"
        side
        {{
{1}
        }}
        side
        {{
{2}
        }}
        side
        {{
{3}
        }}
        side
        {{
{4}
        }}
        side
        {{
{5}
        }}
        side
        {{
{6}
        }}
        editor
        {{
            "color" "0 0 0"
            "visgroupshown" "1"
            "visgroupautoshown" "1"
        }}
    }}
"""
"""Used by Solid class to fill out information used in the final VMF file."""


SIDE_DETAILS = """
            "id" "{0}"
            "plane" "({1}) ({2}) ({3})"
            "material" "{4}"
            "uaxis" "[{5} 0] 0.25"
            "vaxis" "[{6} 0] 0.25"
            "rotation" "0"
            "lightmapscale" "16"
            "smoothing_groups" "0"
"""
"""Used by Side class to fill out information used in the final VMF file."""


ENTITY_DETAILS = """
entity
{{
    "id" "{0}"
    "classname" "{1}"
    "targetname" "{2}"
    "angles" "{3}"
    "origin" "{4}"
{5}
{6}
"""


BLACK_FLOOR = "metal/black_floor_metal_001c"
BLACK_WALL = "metal/black_wall_metal_002c"
WHITE_FLOOR = "tile/white_floor_tile002a"
WHITE_WALL = "tile/white_wall_tile003a"

NODRAW = "tools/toolsnodraw"
TRIGGER = "tools/toolstrigger"


class Side:
    """Represents a side of a solid in VMF."""

    def __init__(self, id: int, material: str, vert1: list[int], vert2: list[int], vert3: list[int], uaxis: list[int], vaxis: list[int]):
        self.id = id
        self.material = material
        self.vert1 = vert1
        self.vert2 = vert2
        self.vert3 = vert3
        self.uaxis = uaxis
        self.vaxis = vaxis


    def convert(self) -> str:
        """Converts the side's information into a readable VMF format."""

        vert1coords = " ".join([str(x) for x in self.vert1])
        vert2coords = " ".join([str(x) for x in self.vert2])
        vert3coords = " ".join([str(x) for x in self.vert3])

        ucoords = " ".join([str(x) for x in self.uaxis])
        vcoords = " ".join([str(x) for x in self.vaxis])

        return SIDE_DETAILS.format(self.id, vert1coords, vert2coords, vert3coords, self.material, ucoords, vcoords)

class Solid:
    """Represents a solid in VMF."""

    nextID = 7
    """The next ID for the next Solid instantiated."""

    def __init__(self, portalable: bool, x: int|float, y: int|float, z0: int = 0, height: int = STEP, material_override = None):
        self.id = Solid.nextID
        Solid.nextID += 1

        self.portalable = portalable
        self.x = x
        self.y = y
        self.z0 = z0
        self.height = height
        self.mat_override = material_override

        self.sides: list[Side] = []
        self._populate_sides()

    def _populate_sides(self):
        """
        Generate all sides to create a cube based on x, y, and z0 coords.\n
        AI assisted in helping make the function because no one wants to do cubes these days
        """

        # Determine what the material should be
        if self.mat_override is None:
            floor_mat = WHITE_FLOOR if self.portalable else BLACK_FLOOR
            wall_mat  = WHITE_WALL  if self.portalable else BLACK_WALL
        else:
            floor_mat = wall_mat = self.mat_override

        # Calculate all vertex coords
        x0 = ORIGIN_X + self.x * STEP
        x1 = ORIGIN_X + (self.x + 1) * STEP
        y0 = ORIGIN_Y + self.y * STEP
        y1 = ORIGIN_Y + (self.y + 1) * STEP
        z0 = ORIGIN_Z + self.z0
        z1 = ORIGIN_Z + self.z0 + self.height

        # Helper to generate a side
        def add(material, p1, p2, p3, u, v):
            self.sides.append(Side(
                id=Solid.nextID, material=material,
                vert1=list(p1), vert2=list(p2), vert3=list(p3),
                uaxis=list(u), vaxis=list(v)
            ))
            Solid.nextID += 1

        # Match Hammer axis signs
        FLOOR_U = (1, 0, 0)
        FLOOR_V = (0, -1, 0) 

        WALL_V  = (0, 0, -1)

        # Top (z=z1)
        add(floor_mat,
            (x0, y1, z1), (x1, y1, z1), (x1, y0, z1),
            FLOOR_U, FLOOR_V)

        # Bottom (z=z0)
        add(floor_mat,
            (x0, y0, z0), (x1, y0, z0), (x1, y1, z0),
            FLOOR_U, FLOOR_V)

        # West (x=x0)
        add(wall_mat,
            (x0, y1, z1), (x0, y0, z1), (x0, y0, z0),
            (0, 1, 0), WALL_V)

        # East (x=x1)
        add(wall_mat,
            (x1, y1, z0), (x1, y0, z0), (x1, y0, z1),
            (0, 1, 0), WALL_V)

        # South (y=y1)
        add(wall_mat,
            (x1, y1, z1), (x0, y1, z1), (x0, y1, z0),
            (1, 0, 0), WALL_V)

        # North (y=y0)
        add(wall_mat,
            (x1, y0, z0), (x0, y0, z0), (x0, y0, z1),
            (1, 0, 0), WALL_V)



    def convert(self) -> str:
        """Converts the side's information into a readable VMF format."""

        return SOLID_DETAILS.format(self.id, self.sides[0].convert(), self.sides[1].convert(), self.sides[2].convert(), self.sides[3].convert(), self.sides[4].convert(), self.sides[5].convert())
    

class Entity:
    """Bare class of an Entity represented for VMF."""

    def __init__(self, class_name: str, origin: list[int], angles: list[float], target_name: str):
        self.id = Solid.nextID
        Solid.nextID += 1

        self.class_name = class_name
        self.origin = origin
        self.angles = angles
        self.target_name = target_name

        self.outputs: list[str] = []
        self.conns = 0

        self.extras = ""

    def connect_to(self, other: "Entity"):
        # default: entity doesn't emit connections
        warn_print(f"{self.target_name} can't connect to things (no connect_to override).")

    def add_output(self, event: str, target: str, action: str, params: str = "", delay: float = 0.0, times: int = -1):
        # "Event" "target,input,params,delay,times"
        self.outputs.append(f'"{event}" "{target}\x1b{action}\x1b{params}\x1b{delay}\x1b{times}"')

    def _outputs_block(self) -> str:
        if not self.outputs:
            return ""
        return "\n    connections\n    {\n        " + "\n        ".join(self.outputs) + "\n    }\n"

    def compile_link(self, emit_port: str, target: "Entity", recv_port: str) -> list[tuple]:
        """Returns a list of connections to be made from this entity to the target entity."""
        raise NotImplementedError
    
    def compile_input(self, recv_port: str) -> str:
        """Returns a string representing what the entity needs to do when receiving input."""
        raise NotImplementedError
    
    def on_connected(self, sender: "Entity") -> None:
        pass

    
    def convert(self):
        """Converts the entity's information into a readable VMF format."""

        tx, ty, z = self.origin

        x = ORIGIN_X + tx * STEP + STEP // 2
        y = ORIGIN_Y + ty * STEP + STEP // 2
        z = ORIGIN_Z + z

        angles = " ".join(str(a) for a in self.angles)
        origin = f"{x} {y} {z}"

        return ENTITY_DETAILS.format(self.id, self.class_name, self.target_name, angles, origin, self.extras, self._outputs_block()) +"\n}"
    

class Instance(Entity):
    """Empty func_instance class."""

    def __init__(self, origin: list[int], angles: list[float], target_name: str, instance_class: str):
        super().__init__("func_instance", origin, angles, target_name)

        self.instance_class = instance_class
        self.fixup = "0"


    def convert(self):
        self.extras = "\n    \"file\" \"{0}\"\n    \"fixup_style\" \"{1}\"".format(self.instance_class, self.fixup)
        return super().convert()

class Receivable(Entity):
    def compile_input(self, recv_port: str) -> str:
        raise NotImplementedError

class FloorButton(Instance):
    def __init__(self, origin: list[int], angles: list[float], target_name: str):
        super().__init__(origin, angles, target_name, "instances/buttons/floor_button_black_intact.vmf")

    def compile_link(self, emit_port: str, target: Entity, recv_port: str):
        if emit_port == "pressed":
            return [("instance:button;OnPressed", target.target_name, target.compile_input(recv_port), "", 0, -1)]
        if emit_port == "released":
            return [("instance:button;OnUnpressed", target.target_name, target.compile_input(recv_port), "", 0, -1)]
        return []
    
class PedestalButton(Entity):
    def __init__(self, origin, angles, target_name):
        super().__init__("prop_button", origin, angles, target_name)

    def compile_link(self, emit_port: str, target: Entity, recv_port: str) -> list[tuple]:
        if emit_port == "pressed":
            return [("OnPressed", target.target_name, target.compile_input(recv_port), "", 0, -1)]
        if emit_port == "released":
            return [("OnButtonReset", target.target_name, target.compile_input(recv_port), "", 0, -1)]
        return []


class Door(Instance, Receivable):
    """Door class represented for VMF."""
    
    door_data_temp = """
    "replace01" "$connectioncount {0}"
    "replace02" "$start_open {1}"
    "replace03" "$no_player_start {2}"
"""

    DIRS = (
        (1, 0, 180),
        (-1, 0, 0),
        (0, 1, 270),
        (0, -1, 90),
    )

    def __init__(self, origin: list[int], angles: list[float], target_name: str, type: int, start_closed: bool = False, no_player_start: bool = False):
        angles = list(angles)
        
        # P2editor doors require the pitch to be -90 to be flat. Why? i dunno 
        angles[0] = -90 if type == 0 or type == 1 else 0

        instance_class = "instances/p2editor/door_exit_1.vmf" if type == 0 else "instances/p2editor/door_entrance_1.vmf" if type == 1 else "instances/door/portal_entry_door_black.vmf"
        super().__init__(origin, angles, target_name, instance_class)

        self.type = type
        self.start_closed = start_closed
        self.no_player_start = no_player_start
    
    def resolve_position(self, world: list[list]):
        """Adjust origin/angles so the door is placed on the inside tile and faces into the chamber."""

        dx, dy, dz = self.origin
        height = len(world)

        def get(x, y) -> str:
            if y < 0 or y >= height:
                return "W"
            row = world[y]
            if x < 0 or x >= len(row):
                return "W"
            return row[x]
        
        for ox, oy, yaw in Door.DIRS:
            if is_walkable(get(dx + ox, dy + oy)):
                # assign the origin and angle
                self.origin = [dx + ox, dy + oy, dz]
                self.angles[1] = float(yaw)

                doorframe = Entity("func_instance", self.origin, self.angles, "doorframe")
                doorframe.extras = "\n    \"file\" \"instances/p2editor/door_frame_black.vmf\""

                return doorframe, (ox, oy)
            
        raise ValueError(f"Door {self.target_name} at ({dx},{dy}) has no adjacent walkable tile")

    def compile_input(self, recv_port: str) -> str:
        if recv_port == "enable":
            return "instance:counter;Add"
        if recv_port == "disable":
            return "instance:counter;Subtract"
        raise ValueError(recv_port)
    
    def on_connected(self, sender: Entity):
        self.conns += 1
            

    def convert(self):
        base = super().convert()
        added = "\n    " + Door.door_data_temp.format(self.conns, "0" if self.start_closed else "1", "1" if self.no_player_start else "0")
        return base.replace("}", added + "\n}")
    
class CubeDropper(Instance, Receivable):
    def __init__(self, origin: list[int], angles: list[float], target_name: str):
        super().__init__(origin, angles, target_name, "instances/gameplay/cube_dropper_multiple_normal.vmf")

    def compile_input(self, recv_port: str) -> str:
        if recv_port == "trigger":
            return "instance:cube_dropper;Trigger"
        raise ValueError(recv_port)
  
class Fizzler(Receivable):

    fizzler_brush = """
    "spawnflags" "4105"
    {0}
"""

    def __init__(self, origin: list[int], target_name: str):
        super().__init__("trigger_portal_cleanser", origin, [0, 0, 0], target_name)

        brush = Solid(False, origin[0], origin[1], height = STEP * 3, material_override="EFFECTS/FIZZLER")
        self.extras = "    \"visible\" \"1\"\n" + Fizzler.fizzler_brush.format(brush.convert())

    def compile_input(self, recv_port: str) -> str:
        if recv_port == "deactivate":
            return "Disable"
        if recv_port == "activate":
            return "Enable"
        raise ValueError(recv_port)
    
    def convert(self):
        return super().convert()
    

class ObservationRoom(Instance):
    """Observation Room class represented for VMF."""

    DIRS = (
        (1, 0, 180),
        (-1, 0, 0),
        (0, 1, 270),
        (0, -1, 90),
    )

    def __init__(self, origin: list[int], angles: list[float], target_name: str):
        angles = list(angles)
        
        # P2editor observation rooms, like doors, are flipped
        angles[0] = -90

        instance_class = "instances/p2editor/observation_room_128x128_1.vmf"
        super().__init__(origin, angles, target_name, instance_class)
    
    def resolve_position(self, world: list[list]):
        """Adjust origin/angles so the observation room is placed on the inside tile and faces into the chamber."""

        dx, dy, dz = self.origin
        height = len(world)

        def get(x, y) -> str:
            if y < 0 or y >= height:
                return "W"
            row = world[y]
            if x < 0 or x >= len(row):
                return "W"
            return row[x]
        
        for ox, oy, yaw in ObservationRoom.DIRS:
            if is_walkable(get(dx + ox, dy + oy)):
                # assign the origin and angle
                self.origin = [dx + ox, dy + oy, dz]
                self.angles[1] = float(yaw)
                return
            
        raise ValueError(f"Observation Room {self.target_name} at ({dx},{dy}) has no adjacent walkable tile")