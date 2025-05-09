# Alteryx Clone

A desktop application that provides ETL (Extract, Transform, Load) functionality similar to Alteryx, with a drag-and-drop interface for creating data workflows.

## Features

- Drag-and-drop workflow creation
- Support for common ETL operations:
  - Input: Read data from CSV files
  - Select: Choose or remove columns
  - Filter: Filter data based on conditions
  - Join: Combine data from multiple sources
  - Merge: Combine multiple files
  - Formula: Create new columns using formulas
  - Output: Save results to CSV files
- Save and load workflows
- Visual workflow representation
- Desktop application (no web server required)

## Installation

1. Ensure you have Python 3.8 or later installed
2. Clone this repository
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. Create a workflow:
   - Double-click tools from the left panel to add them to the canvas
   - Configure each tool by right-clicking and selecting "Configure"
   - Connect tools by selecting two tools in sequence
   - Save your workflow using File > Save Workflow

3. Run a workflow:
   - Load a saved workflow using File > Load Workflow
   - Click File > Run Workflow to execute the workflow

## Tool Configuration

### Input Tool
- Select a CSV file to read data from

### Select Tool
- Specify columns to keep or remove (comma-separated)

### Filter Tool
- Enter a filter condition (e.g., "column > 100")

### Join Tool
- Select the join type (inner, left, right, outer)
- Specify join columns

### Merge Tool
- Select multiple files to combine

### Formula Tool
- Enter a formula to create a new column
- Specify the new column name

### Output Tool
- Select the output file path for saving results

## Saving and Loading Workflows

- Workflows are saved in JSON format
- All tool configurations and connections are preserved
- Workflows can be shared between users

## Requirements

- Python 3.8+
- PyQt6
- pandas
- numpy

## License

MIT License 