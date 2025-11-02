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
        
        # Corridor walls (2 long walls)
        corridor_wall_lm_per_story = length * 2
        
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
        # We pass all interior-related inputs, the function will know which ones to use
        quantities = calculate_quantities(**inputs)
        
        # 3. Print the final report
        print_results(quantities)
        
        # 4. Export results to CSV
        export_to_csv(model_name, quantities)
        
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    
    input("\nPress Enter to exit.")

