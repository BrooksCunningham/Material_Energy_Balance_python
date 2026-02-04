# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Material and Energy Balance Calculator for cane sugar mills. Models multi-effect evaporator systems, steam turbines, juice heaters, and mill operations. Originally developed for St. Mary Sugar Cooperative.

## Running the Application

### Browser-Based Calculator (No Server Required)
The `evaporator_calculator.html` is a standalone client-side application. Open directly in a browser:
```bash
# Windows
start evaporator_calculator.html

# macOS
open evaporator_calculator.html

# Linux
xdg-open evaporator_calculator.html
```

### Python Applications
```bash
# Install dependencies
pip install -r requirements.txt

# Main calculation engine (programmatic)
python -c "from st_mary_material_energy_balance import run_full_balance; results = run_full_balance(inputs_dict, 'output.csv')"

# Standalone evaporator simulator
python Evap_program.py

# Desktop GUI (DearPyGUI)
python evap_gemini_gui.py

# Streamlit web interface
streamlit run streamlit_inputs.py
```

## Testing with Chrome DevTools MCP

Use the Chrome DevTools MCP tools to test the browser-based calculator:

### Opening and Navigating
```
# Open the calculator in Chrome
mcp__chrome-devtools__new_page with url: "file:///path/to/evaporator_calculator.html"

# Take a snapshot to see current page state
mcp__chrome-devtools__take_snapshot
```

### Testing Form Inputs
```
# Fill input fields using their element IDs
mcp__chrome-devtools__fill with uid for input, value for data

# Key input element IDs:
# - juiceFlow: Juice flow rate (lb/hr)
# - juiceBrix: Juice brix (%)
# - syrupBrix: Target syrup brix (%)
# - juiceTemp: Juice inlet temperature (°F)
# - numEffects: Number of effects (select)
# - exhaustPress: Exhaust pressure (psig)
# - lastEffVac: Last effect vacuum (inches Hg)
# - tubeLevel: Tube liquid level (ft)
# - area1-area5: Effect surface areas (ft²)
# - bleed1-bleed4: Vapor bleeds (lb/hr)
# - dessinK: Dessin coefficient
```

### Running Calculations and Verifying Results
```
# Click the Calculate button
mcp__chrome-devtools__click with uid for "Calculate Balance" button

# Take snapshot to verify results displayed
mcp__chrome-devtools__take_snapshot

# Check console for JavaScript errors
mcp__chrome-devtools__list_console_messages
```

### Validation Workflow
1. `take_snapshot` - Get element UIDs from the page
2. `fill` - Enter test values in input fields
3. `click` - Click "Calculate Balance" button
4. `take_snapshot` - Verify results section appears with expected values
5. `list_console_messages` - Check for any JavaScript errors

### Expected Results to Verify
- Summary box displays: Exhaust Steam, Total Evaporation, Syrup Output, Avg U-Ratio
- Status shows green "Sufficient heating surface" when U-ratio ≤ 1
- Status shows red warning when U-ratio > 1
- Mass Balance, Thermal Properties, Heat Transfer, and Pressure Profile tabs populate with data

## Architecture

### Core Modules
- **stream_and_unit_classes.py** - Domain classes: `SugarStream`, `SteamStream`, `Evaporator`, `SteamTurbine`, and BPE calculation helpers
- **st_mary_material_energy_balance.py** - Main engine with `run_full_balance(inputs, csv_path)` orchestrating mill → clarifier → evaporator → pan balance phases

### Domain Modules
- **pan_balance.py** - Vacuum pan crystallization (massecuite, molasses, sugar)
- **turbine.py** - Steam turbine isentropic expansion and HP calculations
- **Juice_Heater.py** - Juice heater design (LMTD, heat duty, surface area)
- **Mill_Settings.py** - Mill roller geometry and mechanical specifications
- **Evap_program.py** - Standalone multi-effect evaporator simulator

## Unit System (Mixed English)

- Mass flow: tons per hour (tph), pounds per hour (lb/hr)
- Temperature: Fahrenheit (°F)
- Pressure: psia (absolute), psig (gauge), inches Hg vacuum
- Area: square feet (ft²)
- Heat duty: BTU/hr

## Coding Conventions

### Stream Naming
- `j_XXX` - juice streams
- `sy_XXX` - syrup streams
- `st_XXX` - steam streams
- `m_XXX` - molasses streams

### Property Access
```python
# SugarStream
stream.mass_flow_tph, stream.lb_per_hr
stream.brix, stream.purity
stream.temperature_deg_F, stream.pressure_psia
stream.latent_heat, stream.boil_temp_liq
stream.tons_solids, stream.tons_pol

# SteamStream
stream.enthalpy_btu_lb, stream.pressure_psia
stream.quality, stream.saturation_temperature
```

### IAPWS97 Steam Properties
```python
from iapws import IAPWS97

# Unit conversions
psia_to_mpa = psia * 0.00689476
degF_to_K = (degF - 32) * 5/9 + 273.15
btu_lb_to_kj_kg = btu_lb * 2.326

# Steam state lookup
steam = IAPWS97(P=pressure_MPa, T=temperature_K)
steam = IAPWS97(P=pressure_MPa, x=1)  # x=1 for saturated vapor
enthalpy = steam.h * 0.42992  # kJ/kg to BTU/lb
```

### BPE (Boiling Point Elevation) Calculation
Two-component system:
1. Brix-based: `BPE1 = 4.266667 * brix / (100 - brix)`
2. Level/temperature correction: `calculate_bpe2(liquid_level, brix, vapor_temp)`
3. Total: `boil_temp_liq = BPE_total + sat_temp`

## Expected Operating Ranges

- First effect calandria: ~15 psig
- Last effect: 25-26 inches Hg vacuum
- Juice temperature rise: 10-15°F per effect
- Evaporation rate: 60-70% of heating steam flow
- U-values: 150-300 BTU/(hr·ft²·°F)
- Energy balance closure: within 5%

## Known Limitations

- Evaporator loop doesn't automatically rebalance juice flow based on U-ratio optimization
- Manual iteration may be required for uniform heat transfer coefficients across effect sets
- File `Linear_algrebra.py` has a typo in the filename
