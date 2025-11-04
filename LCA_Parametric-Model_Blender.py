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
    print("Choose a method to estimate interior partitions:")
    print(" (F) Factor: Simple density factor (e.g., 0.3 m/m²).")
    print(" (L) Layout: Bottom-up estimate based on building use and a central corridor.")
    
    # Initialize all interior inputs to 0 or None
    inputs['partition_density_factor'] = 0
    inputs['building_use'] = None
    inputs['corridor_width'] = 0
    inputs['bathroom_perimeter'] = 0

    while True:
        mode = input("Choose partition method [F/L]: ").strip().upper()
        if mode == 'F':
            inputs['partition_mode'] = 'F'
            inputs['partition_density_factor'] = get_numeric_input("  Enter partition density factor (m/m²) (e.g., 0.1 for office, 0.3 for residential): ")
            break
        elif mode == 'L':
            inputs['partition_mode'] = 'L'
            print("\n  --- Layout Method Inputs ---")
            while True:
                use = input("  Enter Building Use (R)esidential, (C)ommercial, (O)ffice: ").strip().upper()
                if use in ['R', 'C', 'O']:
                    inputs['building_use'] = use
                    break
                else:
                    print("  Invalid input. Please enter 'R', 'C', or 'O'.")
            while True:
                pos = input("Enter Corridor Position (M=Middle, N=North, S=South) [M/N/S]: ").strip().upper()
                if pos in ['M', 'N', 'S']:
                    inputs['corridor_position'] = pos
                    break
                else:
                    print("Invalid choice. Please enter 'M', 'N', or 'S'.")
            inputs['corridor_width'] = get_numeric_input("  Enter average corridor width (m) (e.g., 2): ")
            inputs['bathroom_perimeter'] = get_numeric_input("  Enter avg. bathroom module perimeter (m) (e.g., 10 for 2.5x2.5m): ")
            break
        else:
            print("Invalid choice. Please enter 'F' or 'L'.")
            

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
    partition_mode: str,
    partition_density_factor: float,
    building_use: str,
    corridor_width: float,
    corridor_position: str,
    bathroom_perimeter: float,
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
    total_linear_meters_interior = 0
    total_units = 0

    if partition_mode == 'F':
        # GFA * (linear m / m²) = total linear m
        total_linear_meters_interior = results['gross_floor_area'] * partition_density_factor
        results['total_units'] = 0 # Factor method doesn't calculate units

    elif partition_mode == 'L':
        # Bottom-up calculation per story
        
        # 1. Define constants based on use
        avg_unit_size = 71.5 # Default (Residential)
        bathrooms_per_unit = 1
        if building_use == 'C':
            avg_unit_size = 50
            bathrooms_per_unit = 2
        elif building_use == 'O':
            avg_unit_size = 80
            bathrooms_per_unit = 2
            
        # 2. Calculate areas and units per story
        area_per_story = results['first_floor_area']
        corridor_area_per_story = length * corridor_width
        net_usable_area_per_story = area_per_story - corridor_area_per_story
        
        if net_usable_area_per_story < 0: net_usable_area_per_story = 0
        if avg_unit_size == 0: avg_unit_size = 1 # Avoid division by zero
        
        units_per_story = math.floor(net_usable_area_per_story / avg_unit_size)
        total_units = units_per_story * num_stories
        results['total_units'] = total_units
        
        # 3. Calculate linear meters of walls per story
        
        # Corridor walls (calculate linear meters of corridor walls per story)
        if corridor_position == 'M':
    	    # Double loaded = 2 corridor walls
            corridor_wall_lm_per_story = length * 2
        else:
            # Single loaded = 1 corridor wall
            corridor_wall_lm_per_story = length * 1
        
        # Bathroom walls
        bathroom_wall_lm_per_story = units_per_story * bathrooms_per_unit * bathroom_perimeter
        
        # Unit demising walls (walls separating units)
        # Proxy: Each unit needs one wall of its average depth
        # Avg depth = (building width - corridor width) / 2
        avg_unit_depth = (width - corridor_width) / 2
        if avg_unit_depth < 0: avg_unit_depth = 0
        demising_wall_lm_per_story = units_per_story * avg_unit_depth
        
        # 4. Sum all interior walls
        total_lm_per_story = corridor_wall_lm_per_story + bathroom_wall_lm_per_story + demising_wall_lm_per_story
        total_linear_meters_interior = total_lm_per_story * num_stories

    # 5. Calculate final interior wall area (m²)
    # We use height_per_story because interior walls span one floor
    results['total_interior_wall_area'] = total_linear_meters_interior * height_per_story


    # --- Linear Meter Calculations (m) ---

    # Columns
    # We use floor + 1 to get the number of columns, including both ends
    if col_spacing_length == 0: col_spacing_length = 1 # Avoid zero division
    if col_spacing_width == 0: col_spacing_width = 1 # Avoid zero division
    num_cols_along_length = math.floor(length / col_spacing_length) + 1
    num_cols_along_width = math.floor(width / col_spacing_width) + 1
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
    
    print("\n--- LINEAR METERS (m) & UNITS ---")
    print(f"Total Columns:          {results['total_columns_count']} units")
    print(f"Total Column Length:    {results['total_column_linear_meters']:,.2f} m")
    print(f"Total Beam Length:      {results['total_beam_linear_meters']:,.2f} m")
    print(f"Estimated Total Units:  {results['total_units']} units")
    
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

        # Linear Meters & Units
        ['--- LINEAR METERS & UNITS ---', '', ''],
        ['Total Columns', f"{results['total_columns_count']}", 'units'],
        ['Total Column Length', f"{results['total_column_linear_meters']:.2f}", 'm'],
        ['Total Beam Length', f"{results['total_beam_linear_meters']:.2f}", 'm'],
        ['Estimated Total Units', f"{results['total_units']}", 'units'],
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
# --- BLENDER SCRIPT FUNCTION ---
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
    BUILDING_USE = inputs['building_use']
    CORRIDOR_POS = inputs['corridor_position'] # NEW
    CORRIDOR_WIDTH = inputs['corridor_width']
    
    # Calculate derived geometry values
    TOTAL_H = H_STORY * N_STORIES
    
    num_cols_x = math.floor(L / COL_SPACING_L) + 1 if COL_SPACING_L > 0 else 2
    num_cols_y = math.floor(W / COL_SPACING_W) + 1 if COL_SPACING_W > 0 else 2
    
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
BUILDING_USE = "{BUILDING_USE}"
CORRIDOR_POS = "{CORRIDOR_POS}" # NEW
CORRIDOR_WIDTH = {CORRIDOR_WIDTH}

# --- Cosmetic Parameters ---
SLAB_THICKNESS = {SLAB_THICKNESS}
WALL_THICKNESS = {WALL_THICKNESS}
COL_RADIUS = {COL_RADIUS}
BEAM_HEIGHT = {BEAM_HEIGHT}
BEAM_WIDTH = {BEAM_WIDTH}
CORE_DIM = {CORE_DIM}
PARTITION_THICKNESS = {PARTITION_THICKNESS}
BATH_MODULE_DIM = 2.0 # 2x2m bathroom
    
# --- Helper Functions ---

def clear_scene():
    # Clear all mesh objects from the scene.
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()
    
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
    for c in obj.users_collection:
        c.objects.unlink(obj)
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
    cutter.display_type = 'WIRE' 
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
    for i in range(N_STORIES + 1):
        z_pos = i * H_STORY
        loc = (0, 0, z_pos - (SLAB_THICKNESS / 2.0))
        name = f"Slab_L{{i}}"
        if i == 0: name = "Ground_Slab"
        if i == N_STORIES: name = "Roof_Slab"
        create_box(name, loc, (L, W, SLAB_THICKNESS), coll_slabs)

    # --- 3. Create Columns ---
    if NUM_COLS_X > 0 and NUM_COLS_Y > 0:
        for i in range(NUM_COLS_X):
            x = X_START + i * X_SPACING
            for j in range(NUM_COLS_Y):
                y = Y_START + j * Y_SPACING
                loc = (x, y, TOTAL_H / 2.0)
                name = f"Column_{{i}}_{{j}}"
                create_cylinder(name, loc, COL_RADIUS, TOTAL_H, coll_cols)

    # --- 4. Create Beams ---
    for k in range(N_STORIES):
        level = k + 1
        z_pos = (level * H_STORY) - SLAB_THICKNESS - (BEAM_HEIGHT / 2.0)
        
        if NUM_COLS_Y > 0:
            for j in range(NUM_COLS_Y):
                y = Y_START + j * Y_SPACING
                loc = (0, y, z_pos)
                name = f"Beam_X_L{{level}}_{{j}}"
                create_box(name, loc, (L, BEAM_WIDTH, BEAM_HEIGHT), coll_beams)

        if NUM_COLS_X > 0:
            for i in range(NUM_COLS_X):
                x = X_START + i * X_SPACING
                loc = (x, 0, z_pos)
                name = f"Beam_Y_L{{level}}_{{j}}"
                create_box(name, loc, (BEAM_WIDTH, W, BEAM_HEIGHT), coll_beams)

    # --- 5. Create Facades (Walls and Windows) per Story ---
    for i in range(N_STORIES):
        z_bottom = i * H_STORY
        z_top = (i + 1) * H_STORY - SLAB_THICKNESS - BEAM_HEIGHT
        
        panel_height = z_top - z_bottom
        if panel_height <= 0:
            print(f"Skipping wall generation for level {{i}}, panel height is zero or negative.")
            continue
            
        z_center = z_bottom + (panel_height / 2.0)

        wall_n = create_box(f"Wall_North_L{{i}}", (0, W/2, z_center), (L, WALL_THICKNESS, panel_height), coll_facades)
        wall_s = create_box(f"Wall_South_L{{i}}", (0, -W/2, z_center), (L, WALL_THICKNESS, panel_height), coll_facades)
        wall_e = create_box(f"Wall_East_L{{i}}", (L/2, 0, z_center), (WALL_THICKNESS, W, panel_height), coll_facades)
        wall_w = create_box(f"Wall_West_L{{i}}", (-L/2, 0, z_center), (WALL_THICKNESS, W, panel_height), coll_facades)

        window_height = panel_height * 0.8
        window_z_pos = z_center 
        
        bay_width_x = X_SPACING
        if bay_width_x > 0 and (NUM_COLS_X - 1) > 0:
            if WWR_N > 0:
                window_width = bay_width_x * math.sqrt(WWR_N)
                window_width = min(window_width, bay_width_x * 0.9) 
                
                for j in range(NUM_COLS_X - 1):
                    bay_center_x = (X_START + j * X_SPACING) + (bay_width_x / 2.0)
                    loc_n = (bay_center_x, W/2, window_z_pos)
                    cutter_n = create_box(f"Cutter_N_L{{i}}_B{{j}}", loc_n, (window_width, WALL_THICKNESS*2, window_height), coll_cutters)
                    apply_boolean(wall_n, cutter_n)

            if WWR_S > 0:
                window_width = bay_width_x * math.sqrt(WWR_S)
                window_width = min(window_width, bay_width_x * 0.9)
                
                for j in range(NUM_COLS_X - 1):
                    bay_center_x = (X_START + j * X_SPACING) + (bay_width_x / 2.0)
                    loc_s = (bay_center_x, -W/2, window_z_pos)
                    cutter_s = create_box(f"Cutter_S_L{{i}}_B{{j}}", loc_s, (window_width, WALL_THICKNESS*2, window_height), coll_cutters)
                    apply_boolean(wall_s, cutter_s)

        bay_width_y = Y_SPACING
        if bay_width_y > 0 and (NUM_COLS_Y - 1) > 0:
            if WWR_E > 0:
                window_width = bay_width_y * math.sqrt(WWR_E)
                window_width = min(window_width, bay_width_y * 0.9)

                for j in range(NUM_COLS_Y - 1):
                    bay_center_y = (Y_START + j * Y_SPACING) + (bay_width_y / 2.0)
                    loc_e = (L/2, bay_center_y, window_z_pos)
                    cutter_e = create_box(f"Cutter_E_L{{i}}_B{{j}}", loc_e, (WALL_THICKNESS*2, window_width, window_height), coll_cutters)
                    apply_boolean(wall_e, cutter_e)

            if WWR_W > 0:
                window_width = bay_width_y * math.sqrt(WWR_W)
                window_width = min(window_width, bay_width_y * 0.9)

                for j in range(NUM_COLS_Y - 1):
                    bay_center_y = (Y_START + j * Y_SPACING) + (bay_width_y / 2.0)
                    loc_w = (-L/2, bay_center_y, window_z_pos)
                    cutter_w = create_box(f"Cutter_W_L{{i}}_B{{j}}", loc_w, (WALL_THICKNESS*2, window_width, window_height), coll_cutters)
                    apply_boolean(wall_w, cutter_w)

    # --- 6. Create Vertical Cores ---
    if N_CORES > 0:
        total_core_span = (N_CORES * CORE_DIM) + (N_CORES - 1) * 1.0
        current_core_x = -total_core_span / 2.0 + (CORE_DIM / 2.0)
        
        # Core Y position depends on corridor
        if CORRIDOR_POS == 'S':
            # Place adjacent to South facade
            core_y = (-W / 2.0) + WALL_THICKNESS + (CORE_DIM / 2.0)
        else:
            # Place adjacent to North facade (for 'M' and 'N' layouts)
            core_y = (W / 2.0) - WALL_THICKNESS - (CORE_DIM / 2.0)

        for i in range(N_CORES):
            loc = (current_core_x, core_y, TOTAL_H / 2.0)
            name = f"Core_{{i+1}}"
            create_box(name, loc, (CORE_DIM, CORE_DIM, TOTAL_H), coll_cores)
            current_core_x += CORE_DIM + 1.0

    # --- 7. Create Internal Partitions (New Logic) ---
    if CORRIDOR_WIDTH > 0:
        print(f"Generating internal partitions for {{BUILDING_USE}} use ({{CORRIDOR_POS}} layout).")
        
        # Define parameters based on building use
        unit_size_map = {{'R': 71.5, 'C': 50, 'O': 80}}
        bathrooms_per_unit_map = {{'R': 1, 'C': 2, 'O': 2}}
        
        unit_size = unit_size_map.get(BUILDING_USE, 71.5)
        baths_per_unit = bathrooms_per_unit_map.get(BUILDING_USE, 1)

        # Calculate unit layout
        rentable_area_per_floor = (L * W) - (L * CORRIDOR_WIDTH)
        if rentable_area_per_floor < 0: rentable_area_per_floor = 0
        
        num_units_per_floor = math.floor(rentable_area_per_floor / unit_size) if unit_size > 0 else 0
        
        for i in range(N_STORIES):
            # Partitions go from slab to bottom of next slab
            z_bottom = i * H_STORY
            panel_height = H_STORY - SLAB_THICKNESS 
            z_center = z_bottom + (panel_height / 2.0)
            
            if panel_height <= 0:
                continue # Skip floor if height is invalid

            # --- Branching layout logic ---
            
            if CORRIDOR_POS == 'M':
                # --- Double-Loaded Corridor (Center) ---
                corridor_y_n = CORRIDOR_WIDTH / 2.0
                corridor_y_s = -CORRIDOR_WIDTH / 2.0
                
                create_box(f"Corridor_N_L{{i}}", (0, corridor_y_n, z_center), (L, PARTITION_THICKNESS, panel_height), coll_partitions)
                create_box(f"Corridor_S_L{{i}}", (0, corridor_y_s, z_center), (L, PARTITION_THICKNESS, panel_height), coll_partitions)

                num_units_per_side = math.floor(num_units_per_floor / 2)
                unit_depth = (W - CORRIDOR_WIDTH) / 2.0 - PARTITION_THICKNESS
                unit_width = L / num_units_per_side if num_units_per_side > 0 else 0

                if unit_width > 0:
                    # Create the demising walls (between units)
                    for j in range(1, num_units_per_side): # Loop from 1 to N-1
                        x_pos = X_START + j * unit_width
                        
                        # North side demising wall
                        y_pos_n = corridor_y_n + (unit_depth / 2.0)
                        create_box(f"Partition_N_L{{i}}_{{j}}", (x_pos, y_pos_n, z_center), (PARTITION_THICKNESS, unit_depth, panel_height), coll_partitions)
                        
                        # South side demising wall
                        y_pos_s = corridor_y_s - (unit_depth / 2.0)
                        create_box(f"Partition_S_L{{i}}_{{j}}", (x_pos, y_pos_s, z_center), (PARTITION_THICKNESS, unit_depth, panel_height), coll_partitions)

                    # Create bathroom modules
                    for j in range(num_units_per_side):
                        unit_start_x = X_START + j * unit_width
                        bath_x = unit_start_x + (BATH_MODULE_DIM / 2.0) + PARTITION_THICKNESS
                        
                        # North side bathrooms
                        bath_y_n = corridor_y_n + (BATH_MODULE_DIM / 2.0) + PARTITION_THICKNESS
                        create_box(f"Bath_N_L{{i}}_{{j}}_1", (bath_x, bath_y_n, z_center), (BATH_MODULE_DIM, BATH_MODULE_DIM, panel_height), coll_partitions)
                        if baths_per_unit == 2:
                            bath_x_2 = bath_x + BATH_MODULE_DIM + 0.1
                            create_box(f"Bath_N_L{{i}}_{{j}}_2", (bath_x_2, bath_y_n, z_center), (BATH_MODULE_DIM, BATH_MODULE_DIM, panel_height), coll_partitions)

                        # South side bathrooms
                        bath_y_s = corridor_y_s - (BATH_MODULE_DIM / 2.0) - PARTITION_THICKNESS
                        create_box(f"Bath_S_L{{i}}_{{j}}_1", (bath_x, bath_y_s, z_center), (BATH_MODULE_DIM, BATH_MODULE_DIM, panel_height), coll_partitions)
                        if baths_per_unit == 2:
                            bath_x_2 = bath_x + BATH_MODULE_DIM + 0.1
                            create_box(f"Bath_S_L{{i}}_{{j}}_2", (bath_x_2, bath_y_s, z_center), (BATH_MODULE_DIM, BATH_MODULE_DIM, panel_height), coll_partitions)

            else:
                # --- Single-Loaded Corridor (North or South) ---
                num_units_on_side = num_units_per_floor
                # Depth from partition wall to *inside* of facade wall
                unit_depth = W - CORRIDOR_WIDTH - WALL_THICKNESS - PARTITION_THICKNESS 
                unit_width = L / num_units_on_side if num_units_on_side > 0 else 0
                
                corridor_partition_y = 0
                unit_y_pos = 0
                bath_y = 0
                
                if CORRIDOR_POS == 'N':
                    # Corridor at North, units face South
                    # The ONE partition wall is south of the corridor
                    corridor_partition_y = (W / 2.0) - WALL_THICKNESS - CORRIDOR_WIDTH
                    # Units are south of that
                    unit_y_pos = corridor_partition_y - (unit_depth / 2.0)
                    # Bathrooms are just south of the partition
                    bath_y = corridor_partition_y - (BATH_MODULE_DIM / 2.0) - PARTITION_THICKNESS
                
                elif CORRIDOR_POS == 'S':
                    # Corridor at South, units face North
                    # The ONE partition wall is north of the corridor
                    corridor_partition_y = (-W / 2.0) + WALL_THICKNESS + CORRIDOR_WIDTH
                    # Units are north of that
                    unit_y_pos = corridor_partition_y + (unit_depth / 2.0)
                    # Bathrooms are just north of the partition
                    bath_y = corridor_partition_y + (BATH_MODULE_DIM / 2.0) + PARTITION_THICKNESS

                # Create the *one* corridor wall
                create_box(f"Corridor_Wall_L{{i}}", (0, corridor_partition_y, z_center), (L, PARTITION_THICKNESS, panel_height), coll_partitions)

                if unit_width > 0 and unit_depth > 0:
                    # Create demising walls (one side only)
                    for j in range(1, num_units_on_side): # Loop from 1 to N-1
                        x_pos = X_START + j * unit_width
                        create_box(f"Partition_L{{i}}_{{j}}", (x_pos, unit_y_pos, z_center), (PARTITION_THICKNESS, unit_depth, panel_height), coll_partitions)
                    
                    # Create bathrooms (one side only)
                    for j in range(num_units_on_side):
                        unit_start_x = X_START + j * unit_width
                        bath_x = unit_start_x + (BATH_MODULE_DIM / 2.0) + PARTITION_THICKNESS
                        
                        create_box(f"Bath_L{{i}}_{{j}}_1", (bath_x, bath_y, z_center), (BATH_MODULE_DIM, BATH_MODULE_DIM, panel_height), coll_partitions)
                        if baths_per_unit == 2:
                            bath_x_2 = bath_x + BATH_MODULE_DIM + 0.1
                            create_box(f"Bath_L{{i}}_{{j}}_2", (bath_x_2, bath_y, z_center), (BATH_MODULE_DIM, BATH_MODULE_DIM, panel_height), coll_partitions)

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
        model_name = input("\nEnter a Model Name for CSV/Blender export (e.g., Building-A): ").strip()
        if not model_name:
            model_name = "construction_model" # Default name if left blank
        
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
