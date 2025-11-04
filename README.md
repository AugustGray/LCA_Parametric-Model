# Parametric Construction Quantity Calculator for LCA

## Overview

This is a simple Python script designed to quickly estimate building material quantities for conceptual design and Life Cycle Assessment (LCA).

Based on a few key parametric inputs (like building dimensions, story height, and column spacing), this tool calculates:

- Gross Floor Area (GFA) and other building areas.

- Square meters (m²) of exterior walls, windows, interior partitions, and vertical circulation shafts.

- Linear meters (m) of structural columns and beams.

The primary goal is to provide a rapid, high-level quantity takeoff that can be fed into an LCA model during the earliest stages of design, before detailed drawings are available.

## Features

* **Parametric Inputs:** Quickly model different building sizes and configurations.

* **Material Quantities:** Calculates key quantities for:

	* Floors & Roof (m²)

	* Exterior Walls (m²)

	* Windows (m²)

	* Interior Partitions (m²)

	* Vertical Circulation (Stairs/Elevators) (m²)

	* Structural Columns (m)

	* Structural Beams (m)

* **Flexible WWR:** Supports both a single, simple Window-to-Wall Ratio (WWR) and a detailed WWR by orientation (N, S, E, W).

* **CSV Export:** Automatically exports all calculated results to a .csv file, named according to the "Model Name" you provide.

* **Blender Python Script:** Automatically creates a python script to build a model based on all inputs. To use it: Open Blender > Script tab > Open > Run Script.

## How to Use

**Prerequisites**

- You must have Python 3 installed on your system.

**Running the Script**

1. Save the script as construction_calculator.py.

2. Open your terminal or command prompt.

3. Navigate to the directory where you saved the file.

4. Run the script using the following command: (This script will create only a report of material quantities on an .csv file)

```
python LCA_Parametric-Model.py
```
or run: (This will create the report of materials + a python script for blender)
```
python LCA_Parametric-Model_Blender.py
```

5. The script will guide you through all the required inputs one by one.

6. Once all inputs are provided, it will print a formatted report to the console and create a .csv file in the same directory.

## Input Definitions

The script will prompt you for the following information:

**Building Dimensions**

- **Building Length (m):** The total length of the building.

- **Building Width (m):** The total width of the building.

- **Average Height per Story (m):** The typical floor-to-floor height.

- **Number of Stories (levels):** The total number of floors, including the ground floor.

- **Vertical Circulation Modules:** The number of stair/elevator shafts in the building.

**Structural Inputs**

- **Column Spacing (Length) (m):** The typical distance between columns along the building's length.

- **Column Spacing (Width) (m):** The typical distance between columns along the building's width.

**Interior Inputs**

- **Partition Density Factor (m/m²):** An estimation factor for interior walls. This is the average linear meters of partition per square meter of GFA.

Example: 0.1 (open-plan office) to 0.3 (residential) or 0.5 (hotel).

**Facade Inputs (WWR)**

- You will be asked to choose (S)imple or by (O)rientation.

- **Simple:** A single Window-to-Wall Ratio (e.g., 0.4) applied to the entire building.

- **Orientation:** Separate WWRs for the North, South, East, and West facades.

**Export**

- **Model Name:** The name for your project (e.g., Building-A). This will be used as the filename for the output (Building-A.csv).

## Output

The script generates two outputs:

1. **Console Report:** A summary of all calculated areas (m²) and linear meters (m) printed directly to your terminal.

2. **CSV File:** A file named <Your-Model-Name>.csv containing all the results, formatted for use in spreadsheets (like Excel or Google Sheets) or for import into other analysis software.
