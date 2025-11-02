import math
import csv

def get_numeric_input(prompt: str) -> float:
    """
    Prompts the user for numeric input and handles invalid entries.
    Allows zero and positive numbers.
    """
    while True:
        try:
            value_str = input(prompt)
            value_float = float(value_str)
            if value_float < 0:
                print("Input must be a non-negative number. Please try again.")
            else:
                return value_float
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_user_inputs() -> dict:
    """
    Gathers all necessary inputs from the user.
    """
    print("--- Building Dimensions ---")
    inputs = {}
    inputs['length'] = get_numeric_input("Enter building length N/S (m): ")
    inputs['width'] = get_numeric_input("Enter building width E/W (m): ")
    inputs['height_per_story'] = get_numeric_input("Enter average height per story (m): ")
    inputs['num_stories'] = int(get_numeric_input("Enter number of stories (levels): "))
    inputs['num_vertical_modules'] = int(get_numeric_input("Enter number of vertical circulation modules (stairs/elevators) (0, 1, 2...): "))

    print("\n--- Structural Inputs ---")
    inputs['col_spacing_length'] = get_numeric_input("Enter column spacing along the LENGTH (m): ")
    inputs['col_spacing_width'] = get_numeric_input("Enter column spacing along the WIDTH (m): ")

    print("\n--- Interior Inputs ---")
    inputs['partition_density_factor'] = get_numeric_input("Enter partition density factor (m/m²) (e.g., 0.1 for office, 0.3 for residential): ")

    print("\n--- Facade Inputs (WWR) ---")
    print("For Window-to-Wall Ratio (WWR), you can use a single average")
    print("or specify a different ratio for each orientation.")
    
    wwr_values = {}
    while True:
        mode = input("Use (S)imple WWR or by (O)rientation? [S/O]: ").strip().upper()
        if mode == 'S':
            wwr_values['general'] = get_numeric_input("Enter general WWR (e.g., 0.4 for 40%): ")
            break
        elif mode == 'O':
            print("\n** ASSUMPTION: 'Length' sides are East/West, 'Width' sides are North/South. **")
            wwr_values['north'] = get_numeric_input("Enter NORTH WWR (e.g., 0.3): ")
            wwr_values['south'] = get_numeric_input("Enter SOUTH WWR (e.g., 0.5): ")
            wwr_values['east'] = get_numeric_input("Enter EAST WWR (e.g., 0.4): ")
            wwr_values['west'] = get_numeric_input("Enter WEST WWR (e.g., 0.4): ")
            break
        else:
            print("Invalid choice. Please enter 'S' or 'O'.")
            
    inputs['wwr_mode'] = mode
    inputs['wwr_values'] = wwr_values
    
    return inputs

def calculate_quantities(
    length: float, 
    width: float, 
    height_per_story: float, 
    num_stories: int,
    num_vertical_modules: int,
    col_spacing_length: float,
    col_spacing_width: float,
    partition_density_factor: float,
    wwr_mode: str,
    wwr_values: dict
) -> dict:
    """
    Calculates all material quantities based on user inputs.
    """
    results = {}
    total_height = height_per_story * num_stories # Calculate total height

    # --- Area Calculations (m²) ---
    results['first_floor_area'] = length * width
    results['roof_area'] = length * width  # Assuming flat roof
    results['gross_floor_area'] = results['first_floor_area'] * num_stories
    if num_stories > 1:
        results['upper_levels_area'] = results['first_floor_area'] * (num_stories - 1)
    else:
        results['upper_levels_area'] = 0

    # --- Facade Area Calculations (m²) ---
    perimeter = 2 * (length + width)
    results['total_exterior_wall_area_gross'] = perimeter * total_height
    
    total_window_area = 0
    if wwr_mode == 'S':
        # Simple WWR calculation
        wwr = wwr_values['general']
        total_window_area = results['total_exterior_wall_area_gross'] * wwr
    else:
        # WWR by Orientation
        # Assumption: Length runs E/W, Width runs N/S
        north_wall_gross = length * total_height
        south_wall_gross = length * total_height
        east_wall_gross = width * total_height
        west_wall_gross = width * total_height
        
        total_window_area = (
            (north_wall_gross * wwr_values['north']) +
            (south_wall_gross * wwr_values['south']) +
            (east_wall_gross * wwr_values['east']) +
            (west_wall_gross * wwr_values['west'])
        )
    
    results['total_window_area'] = total_window_area
    results['total_exterior_wall_area_net'] = results['total_exterior_wall_area_gross'] - total_window_area

    # --- Vertical Circulation (m²) ---
    if num_vertical_modules > 0 and height_per_story > 0:
        # User formula: length_per_story = ((height_per_story / 0.17) * 0.30 * 2) + 4.8
        length_per_story_per_module = ((height_per_story / 0.17) * 0.30 * 2) + 4.8
        
        # User formula: total_sqm = length_per_story * height * num_levels
        # This is equivalent to: length_per_story * total_height
        total_area_per_module = length_per_story_per_module * total_height
        
        results['total_vertical_circulation_sqm'] = total_area_per_module * num_vertical_modules
    else:
        results['total_vertical_circulation_sqm'] = 0

    # --- Interior Wall Calculation (m²) ---
    # GFA * (linear m / m²) = total linear m
    total_linear_meters_interior = results['gross_floor_area'] * partition_density_factor
    # Total linear m * height = total m²
    # We use height_per_story because interior walls don't span the *entire* building height,
    # but rather the height of each story they are on.
    results['total_interior_wall_area'] = total_linear_meters_interior * height_per_story


    # --- Linear Meter Calculations (m) ---

    # Columns
    # We use floor + 1 to get the number of columns, including both ends
    num_cols_along_length = math.floor(length / col_spacing_length) + 1
    num_cols_along_width = math.floor(width / col_spacing_length) + 1
    total_columns = num_cols_along_length * num_cols_along_width
    
    results['total_columns_count'] = total_columns
    # Total column length is total columns * total building height
    results['total_column_linear_meters'] = total_columns * total_height

    # Beams
    # Beams run in a grid at each floor/roof level
    # 'num_stories' includes the roof level support
    
    # Beams running along the "length" axis
    beams_len_axis_total = num_cols_along_width * length
    
    # Beams running along the "width" axis
    beams_wid_axis_total = num_cols_along_length * width
    
    total_beam_lm_per_level = beams_len_axis_total + beams_wid_axis_total
    
    # A 1-story building has 1 level of beams (roof)
    # A 3-story building has 3 levels of beams (floor 2, floor 3, roof)
    results['total_beam_linear_meters'] = total_beam_lm_per_level * num_stories

    return results

def print_results(results: dict):
    """
    Prints a formatted report of the calculated quantities.
    """
    print("\n\n--- CALCULATION REPORT ---")
    print("==========================")
    
    print("\n--- AREAS (m²) ---")
    print(f"First Floor Area:       {results['first_floor_area']:,.2f} m²")
    print(f"Roof Area (Assumed):    {results['roof_area']:,.2f} m²")
    print(f"Upper Levels Area:      {results['upper_levels_area']:,.2f} m²")
    print(f"GROSS FLOOR AREA:       {results['gross_floor_area']:,.2f} m²")
    print("-" * 20)
    print(f"Gross Exterior Wall Area: {results['total_exterior_wall_area_gross']:,.2f} m²")
    print(f"Total Window Area:      {results['total_window_area']:,.2f} m²")
    print(f"NET EXTERIOR WALL AREA: {results['total_exterior_wall_area_net']:,.2f} m²")
    print(f"Vertical Circulation Area: {results['total_vertical_circulation_sqm']:,.2f} m²")
    print(f"Interior Wall Area (Est.): {results['total_interior_wall_area']:,.2f} m²")
    
    print("\n--- LINEAR METERS (m) ---")
    print(f"Total Columns:          {results['total_columns_count']} units")
    print(f"Total Column Length:    {results['total_column_linear_meters']:,.2f} m")
    print(f"Total Beam Length:      {results['total_beam_linear_meters']:,.2f} m")
    
    print("\n==========================")
    print("Calculation complete.")

def export_to_csv(model_name: str, results: dict):
    """
    Exports the calculation results to a CSV file.
    """
    filename = f"{model_name}.csv"
    
    # Define the data rows based on the results dictionary
    # We format numbers as strings here for consistent output
    data_rows = [
        # Header
        ['Quantity', 'Value', 'Unit'],
        
        # Areas
        ['--- AREAS ---', '', ''],
        ['First Floor Area', f"{results['first_floor_area']:.2f}", 'm²'],
        ['Roof Area (Assumed)', f"{results['roof_area']:.2f}", 'm²'],
        ['Upper Levels Area', f"{results['upper_levels_area']:.2f}", 'm²'],
        ['GROSS FLOOR AREA', f"{results['gross_floor_area']:.2f}", 'm²'],
        ['Gross Exterior Wall Area', f"{results['total_exterior_wall_area_gross']:.2f}", 'm²'],
        ['Total Window Area', f"{results['total_window_area']:.2f}", 'm²'],
        ['NET EXTERIOR WALL AREA', f"{results['total_exterior_wall_area_net']:.2f}", 'm²'],
        ['Vertical Circulation Area', f"{results['total_vertical_circulation_sqm']:.2f}", 'm²'],
        ['Interior Wall Area (Est.)', f"{results['total_interior_wall_area']:.2f}", 'm²'],

        # Linear Meters
        ['--- LINEAR METERS ---', '', ''],
        ['Total Columns', f"{results['total_columns_count']}", 'units'],
        ['Total Column Length', f"{results['total_column_linear_meters']:.2f}", 'm'],
        ['Total Beam Length', f"{results['total_beam_linear_meters']:.2f}", 'm'],
    ]
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(data_rows)
        print(f"\nSuccessfully exported results to {filename}")
    except IOError as e:
        print(f"\nError: Could not write to file {filename}. {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred during CSV export: {e}")

#
# --- NEW FUNCTION FOR BLENDER ---
#
def generate_blender_script(model_name: str, inputs: dict):
    """
    Generates a new Python script that can be run inside Blender
    to build a 3D model based on the user's inputs.
    
    Args:
        model_name (str): The base name for the output .py file.
        inputs (dict): The dictionary of user inputs from get_user_inputs().
    """
    print(f"\nGenerating Blender script...")
    
    # --- 1. Extract and Calculate Parameters ---
    
    # Get base inputs
    L = inputs['length']
    W = inputs['width']
    H_STORY = inputs['height_per_story']
    N_STORIES = inputs['num_stories']
    COL_SPACING_L = inputs['col_spacing_length']
    COL_SPACING_W = inputs['col_spacing_width']
    N_CORES = inputs['num_vertical_modules']
    PDF = inputs['partition_density_factor'] # Partition Density Factor
    
    # Calculate derived geometry values
    TOTAL_H = H_STORY * N_STORIES
    
    # Calculate column counts
    num_cols_x = math.floor(L / COL_SPACING_L) + 1 if COL_SPACING_L > 0 else 2
    num_cols_y = math.floor(W / COL_SPACING_W) + 1 if COL_SPACING_W > 0 else 2
    
    # Calculate exact spacing to ensure grid fits the dimensions
    x_spacing = L / (num_cols_x - 1) if num_cols_x > 1 else 0
    y_spacing = W / (num_cols_y - 1) if num_cols_y > 1 else 0
    
    x_start = -L / 2
    y_start = -W / 2
    
    # Get WWR values
    wwr_mode = inputs['wwr_mode']
    wwr_vals = inputs['wwr_values']
    
    if wwr_mode == 'S':
        wwr_n = wwr_s = wwr_e = wwr_w = wwr_vals['general']
    else:
        wwr_n = wwr_vals['north']
        wwr_s = wwr_vals['south']
        wwr_e = wwr_vals['east']
        wwr_w = wwr_vals['west']

    # --- 2. Define "Cosmetic" Parameters for 3D ---
    SLAB_THICKNESS = 0.3
    WALL_THICKNESS = 0.3
    COL_RADIUS = 0.25
    BEAM_HEIGHT = 0.4
    BEAM_WIDTH = 0.3
    CORE_DIM = 5.0 # Assume 5x5m for each vertical core
    PARTITION_THICKNESS = 0.15 # For internal walls

    # --- 3. Create the Blender Script String ---
    # This is a giant f-string that *is* the Python script
    # we will write to a new file.
    
    #
    # !! ERROR FIX !!
    # The docstrings """...""" inside this f-string were causing
    # the SyntaxError. They have been changed to '#' comments.
    #
    script_content = f"""
import bpy
import math

# ==========================================================
# === This script was auto-generated by your LCA tool ===
# === Model: {model_name}
# ==========================================================

# --- Parameters (Injected from your script) ---
L = {L}
W = {W}
H_STORY = {H_STORY}
N_STORIES = {N_STORIES}
TOTAL_H = {TOTAL_H}

NUM_COLS_X = {num_cols_x}
NUM_COLS_Y = {num_cols_y}
X_SPACING = {x_spacing}
Y_SPACING = {y_spacing}
X_START = {x_start}
Y_START = {y_start}

WWR_N = {wwr_n}
WWR_S = {wwr_s}
WWR_E = {wwr_e}
WWR_W = {wwr_w}

N_CORES = {N_CORES}
PDF = {PDF} # Partition Density Factor

# --- Cosmetic Parameters ---
SLAB_THICKNESS = {SLAB_THICKNESS}
WALL_THICKNESS = {WALL_THICKNESS}
COL_RADIUS = {COL_RADIUS}
BEAM_HEIGHT = {BEAM_HEIGHT}
BEAM_WIDTH = {BEAM_WIDTH}
CORE_DIM = {CORE_DIM}
PARTITION_THICKNESS = {PARTITION_THICKNESS}
    
# --- Helper Functions ---

def clear_scene():
    # Clear all mesh objects from the scene.
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()
    
    # Delete collections
    for collection in bpy.data.collections:
        if not collection.name == "Scene Collection":
            bpy.data.collections.remove(collection)

def create_collection(name):
    # Create a new collection and link it to the scene.
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    new_coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(new_coll)
    return new_coll

def add_to_collection(obj, coll):
    # Move an object to a collection.
    # Unlink from all other collections
    for c in obj.users_collection:
        c.objects.unlink(obj)
    # Link to the new collection
    coll.objects.link(obj)

def create_box(name, location, dimensions, coll):
    # Helper to create a simple box.
    bpy.ops.mesh.primitive_cube_add(size=1, location=location, enter_editmode=False)
    obj = bpy.context.active_object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    add_to_collection(obj, coll)
    return obj

def create_cylinder(name, location, radius, depth, coll):
    # Helper to create a simple cylinder.
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius, 
        depth=depth, 
        location=location,
        vertices=16
    )
    obj = bpy.context.active_object
    obj.name = name
    add_to_collection(obj, coll)
    return obj

def apply_boolean(target, cutter, operation='DIFFERENCE'):
    # Apply a boolean modifier.
    mod = target.modifiers.new(name=f"Bool_{{cutter.name}}", type='BOOLEAN')
    mod.object = cutter
    mod.operation = operation
    cutter.display_type = 'WIRE' # Make cutter visible but non-intrusive
    cutter.hide_render = True
    return mod

# --- Main Script ---

def build_model():
    print("Building parametric model in Blender...")
    
    # --- 1. Setup Collections ---
    coll_slabs = create_collection("Slabs")
    coll_cols = create_collection("Columns")
    coll_beams = create_collection("Beams")
    coll_facades = create_collection("Facades")
    coll_cores = create_collection("Cores")
    coll_partitions = create_collection("Internal_Partitions")
    coll_cutters = create_collection("Cutters (Hide Me)")

    # --- 2. Create Slabs ---
    # Loop N_STORIES + 1 to include ground floor and roof
    for i in range(N_STORIES + 1):
        z_pos = i * H_STORY
        # Center slab at (0, 0, z_pos)
        loc = (0, 0, z_pos - (SLAB_THICKNESS / 2.0))
        if i == 0:
            name = "Ground_Slab"
        elif i == N_STORIES:
            name = "Roof_Slab"
        else:
            name = f"Slab_L{{i}}"
        
        create_box(name, loc, (L, W, SLAB_THICKNESS), coll_slabs)

    # --- 3. Create Columns ---
    if NUM_COLS_X > 0 and NUM_COLS_Y > 0:
        for i in range(NUM_COLS_X):
            x = X_START + i * X_SPACING
            for j in range(NUM_COLS_Y):
                y = Y_START + j * Y_SPACING
                loc = (x, y, TOTAL_H / 2.0) # Center of the column
                name = f"Column_{{i}}_{{j}}"
                create_cylinder(name, loc, COL_RADIUS, TOTAL_H, coll_cols)

    # --- 4. Create Beams ---
    # Beams sit *under* the slabs (except ground floor)
    for k in range(N_STORIES):
        level = k + 1
        z_pos = (level * H_STORY) - SLAB_THICKNESS - (BEAM_HEIGHT / 2.0)
        
        # Beams along X-axis
        if NUM_COLS_Y > 0:
            for j in range(NUM_COLS_Y):
                y = Y_START + j * Y_SPACING
                loc = (0, y, z_pos)
                name = f"Beam_X_L{{level}}_{{j}}"
                create_box(name, loc, (L, BEAM_WIDTH, BEAM_HEIGHT), coll_beams)

        # Beams along Y-axis
        if NUM_COLS_X > 0:
            for i in range(NUM_COLS_X):
                x = X_START + i * X_SPACING
                loc = (x, 0, z_pos)
                name = f"Beam_Y_L{{level}}_{{i}}"
                create_box(name, loc, (BEAM_WIDTH, W, BEAM_HEIGHT), coll_beams)

    # --- 5. Create Facades (Walls and Windows) per Story ---
    
    # Loop for each story, from ground floor up
    for i in range(N_STORIES):
        # Calculate vertical position for this story's walls
        # Wall starts on top of slab (z = i * H_STORY)
        # Wall stops at bottom of beams for the *next* level up
        # (z = (i+1) * H_STORY - SLAB_THICKNESS - BEAM_HEIGHT)
        
        z_bottom = i * H_STORY
        z_top = (i + 1) * H_STORY - SLAB_THICKNESS - BEAM_HEIGHT
        
        # Ensure parameters are valid (e.g., story height > slab + beam)
        panel_height = z_top - z_bottom
        if panel_height <= 0:
            print(f"Skipping wall generation for level {{i}}, panel height is zero or negative.")
            continue
            
        # Z-location for the new centered wall panel
        z_center = z_bottom + (panel_height / 2.0)

        # Create the 4 wall panels for this story
        wall_n = create_box(f"Wall_North_L{{i}}", (0, W/2, z_center), (L, WALL_THICKNESS, panel_height), coll_facades)
        wall_s = create_box(f"Wall_South_L{{i}}", (0, -W/2, z_center), (L, WALL_THICKNESS, panel_height), coll_facades)
        wall_e = create_box(f"Wall_East_L{{i}}", (L/2, 0, z_center), (WALL_THICKNESS, W, panel_height), coll_facades)
        wall_w = create_box(f"Wall_West_L{{i}}", (-L/2, 0, z_center), (WALL_THICKNESS, W, panel_height), coll_facades)

        # --- Tweak 2: Create window cutouts per-bay ---
        
        # Define a "cosmetic" window height, e.g., 80% of the panel height
        window_height = panel_height * 0.8
        window_z_pos = z_center # Windows are vertically centered in the panel
        
        # North/South Facades (distributed along X-axis)
        bay_width_x = X_SPACING
        if bay_width_x > 0 and (NUM_COLS_X - 1) > 0:
            # North Windows
            if WWR_N > 0:
                # Use math.sqrt(WWR) to get a 1D ratio for the width
                window_width = bay_width_x * math.sqrt(WWR_N)
                window_width = min(window_width, bay_width_x * 0.9) # Add 10% margin
                
                for j in range(NUM_COLS_X - 1):
                    bay_center_x = (X_START + j * X_SPACING) + (bay_width_x / 2.0)
                    loc_n = (bay_center_x, W/2, window_z_pos)
                    cutter_n = create_box(f"Cutter_N_L{{i}}_B{{j}}", loc_n, (window_width, WALL_THICKNESS*2, window_height), coll_cutters)
                    apply_boolean(wall_n, cutter_n)

            # South Windows
            if WWR_S > 0:
                window_width = bay_width_x * math.sqrt(WWR_S)
                window_width = min(window_width, bay_width_x * 0.9)
                
                for j in range(NUM_COLS_X - 1):
                    bay_center_x = (X_START + j * X_SPACING) + (bay_width_x / 2.0)
                    loc_s = (bay_center_x, -W/2, window_z_pos)
                    cutter_s = create_box(f"Cutter_S_L{{i}}_B{{j}}", loc_s, (window_width, WALL_THICKNESS*2, window_height), coll_cutters)
                    apply_boolean(wall_s, cutter_s)

        # East/West Facades (distributed along Y-axis)
        bay_width_y = Y_SPACING
        if bay_width_y > 0 and (NUM_COLS_Y - 1) > 0:
            # East Windows
            if WWR_E > 0:
                window_width = bay_width_y * math.sqrt(WWR_E)
                window_width = min(window_width, bay_width_y * 0.9)

                for j in range(NUM_COLS_Y - 1):
                    bay_center_y = (Y_START + j * Y_SPACING) + (bay_width_y / 2.0)
                    loc_e = (L/2, bay_center_y, window_z_pos)
                    cutter_e = create_box(f"Cutter_E_L{{i}}_B{{j}}", loc_e, (WALL_THICKNESS*2, window_width, window_height), coll_cutters)
                    apply_boolean(wall_e, cutter_e)

            # West Windows
            if WWR_W > 0:
                window_width = bay_width_y * math.sqrt(WWR_W)
                window_width = min(window_width, bay_width_y * 0.9)

                for j in range(NUM_COLS_Y - 1):
                    bay_center_y = (Y_START + j * Y_SPACING) + (bay_width_y / 2.0)
                    loc_w = (-L/2, bay_center_y, window_z_pos)
                    cutter_w = create_box(f"Cutter_W_L{{i}}_B{{j}}", loc_w, (WALL_THICKNESS*2, window_width, window_height), coll_cutters)
                    apply_boolean(wall_w, cutter_w)

    # --- 6. Create Vertical Cores ---
    # Center the cores along the X-axis and place them adjacent to the North wall.
    
    # Calculate the total span of all cores (including 1m spacing)
    if N_CORES > 0:
        total_core_span = (N_CORES * CORE_DIM) + (N_CORES - 1) * 1.0
        
        # Calculate the X-coordinate for the center of the *first* core
        # This centers the whole block of cores at X=0
        current_core_x = -total_core_span / 2.0 + (CORE_DIM / 2.0)
        
        # Calculate the Y-coordinate, adjacent to the *inside* of the North wall
        # North wall is at +W/2. Its inner face is at (W/2) - WALL_THICKNESS
        # The core's center will be half its dimension south of that.
        core_y = (W / 2.0) - WALL_THICKNESS - (CORE_DIM / 2.0)
        
        for i in range(N_CORES):
            loc = (current_core_x, core_y, TOTAL_H / 2.0)
            name = f"Core_{{i+1}}"
            create_box(name, loc, (CORE_DIM, CORE_DIM, TOTAL_H), coll_cores)
            
            # Move the X-coordinate for the next core
            current_core_x += CORE_DIM + 1.0

    # --- 7. Create Internal Partitions (Representative) ---
    if PDF > 0:
        print(f"Generating partitions with density factor: {{PDF}}")
        
        for i in range(N_STORIES):
            # Partitions go from slab to slab (bottom of next slab)
            z_bottom = i * H_STORY
            z_top = (i + 1) * H_STORY
            
            # Stop partitions just under the slab above
            panel_height = z_top - z_bottom - SLAB_THICKNESS 
            z_center = z_bottom + (panel_height / 2.0)
            
            if panel_height <= 0:
                continue # Skip floor if height is invalid

            # Calculate total partition length needed for this floor
            # (L * W * PDF) = target m² area / panel_height = target m length
            target_length_per_floor = (L * W * PDF) / panel_height
            
            # Create one main E-W corridor
            corridor_y = 0 # Centered
            create_box(f"Corridor_L{{i}}", (0, corridor_y, z_center), (L, PARTITION_THICKNESS, panel_height), coll_partitions)
            
            length_created = L
            remaining_length = target_length_per_floor - length_created
            
            # Add perpendicular "office" walls
            num_bays_x = NUM_COLS_X - 1
            if remaining_length > 0 and num_bays_x > 0:
                
                # Get length of each perpendicular wall
                wall_length_per_bay = remaining_length / num_bays_x
                
                # Cap the wall length (e.g., can't be longer than half the building width)
                wall_length_per_bay = min(wall_length_per_bay, (W / 2.0) * 0.9)
                
                if wall_length_per_bay > 0.1: # Only create if they have meaningful length
                    for j in range(num_bays_x):
                        x_pos = X_START + (j * X_SPACING) + (X_SPACING / 2.0)
                        
                        # Create one wall north of corridor
                        y_pos_n = corridor_y + (wall_length_per_bay / 2.0)
                        create_box(f"Partition_N_L{{i}}_{{j}}", (x_pos, y_pos_n, z_center), (PARTITION_THICKNESS, wall_length_per_bay, panel_height), coll_partitions)
                        
                        # Create one wall south of corridor
                        y_pos_s = corridor_y - (wall_length_per_bay / 2.0)
                        create_box(f"Partition_S_L{{i}}_{{j}}", (x_pos, y_pos_s, z_center), (PARTITION_THICKNESS, wall_length_per_bay, panel_height), coll_partitions)

    print("Blender model generation complete.")


# --- Run the script ---
clear_scene()
build_model()
bpy.ops.object.select_all(action='DESELECT')

"""

    # --- 4. Write the String to a File ---
    filename = f"{model_name}_blender.py"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(script_content)
        print(f"\nSuccessfully generated Blender script: {filename}")
        print("To use it: Open Blender > Scripting tab > Open > Run Script")
    except IOError as e:
        print(f"\nError: Could not write to file {filename}. {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred during Blender script export: {e}")


if __name__ == "__main__":
    print("Welcome to the Construction Quantity Calculator!")
    print("This script will help you estimate areas (m²) and linear meters (m).")
    print("Please provide the following details in meters.\n")
    
    try:
        # 1. Get all inputs from the user
        inputs = get_user_inputs()
        
        # Get model name for export
        model_name = input("\nEnter a Model Name for CSV export (e.g., Building-A): ").strip()
        if not model_name:
            model_name = "construction_results" # Default name if left blank
        
        # 2. Perform calculations
        quantities = calculate_quantities(**inputs)
        
        # 3. Print the final report
        print_results(quantities)
        
        # 4. Export results to CSV
        export_to_csv(model_name, quantities)
        
        # 5. Generate Blender Script
        generate_blender_script(model_name, inputs)
        
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    
    input("\nPress Enter to exit.")

