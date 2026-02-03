# Material and Energy Balance Calculator for Sugar Mills

A comprehensive Python-based simulation tool for material and energy balance calculations in cane sugar processing facilities. This application models multi-effect evaporator systems, steam turbines, juice heaters, and mill operations to optimize sugar production efficiency.

## 🎯 Overview

This tool is designed for sugar mill engineers and operators to:
- Calculate material flows through the entire sugar production process
- Perform energy balance analysis for multi-effect evaporator systems
- Optimize steam consumption and energy recovery
- Analyze turbine performance and steam distribution
- Model juice heating and concentration processes

Originally developed for St. Mary Sugar Cooperative operations, this calculator helps optimize plant efficiency and troubleshoot operational issues.

## ✨ Key Features

### Material Balance
- **Mill Operations**: Fiber content, pol extraction, and crushing capacity analysis
- **Clarifier Balance**: Lime/flocculant dosing and mud filtration calculations
- **Juice Flow Tracking**: Monitor brix concentration and purity through the process
- **Pan Crystallization**: Vacuum pan material balance for sugar crystallization

### Energy Balance
- **Multi-Effect Evaporators**: Support for triple and quadruple effect systems
- **Vapor Bleed Optimization**: Calculate optimal vapor extraction points
- **Boiling Point Elevation (BPE)**: Accurate modeling based on brix and liquid level
- **Heat Transfer Analysis**: U-value calculations for evaporator performance
- **Steam System**: Complete steam distribution and consumption analysis

### Thermodynamic Properties
- **IAPWS97 Standard**: Industry-standard steam and water properties
- **CoolProp Integration**: Accurate thermodynamic calculations
- **Pressure-Temperature Profiles**: Maintain proper pressure cascades across effects

### User Interfaces
- **DearPyGUI Desktop App**: Interactive desktop interface for evaporator calculations
- **Streamlit Web App**: Browser-based data entry and visualization
- **CSV Export**: Export detailed results for further analysis

## 📋 Requirements

### Python Version
- Python 3.7 or higher

### Dependencies

```bash
# Core thermodynamic libraries
iapws           # Steam and water properties (IAPWS97 standard)
CoolProp        # Thermodynamic property database

# Data processing
pandas          # Data manipulation and CSV export
numpy           # Numerical calculations

# GUI frameworks
dearpygui       # Desktop GUI interface
streamlit       # Web-based interface

# Standard library (included with Python)
math
sys
json
datetime
```

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/BrooksCunningham/Material_Energy_Balance_python.git
   cd Material_Energy_Balance_python
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install required packages**
   ```bash
   pip install iapws pandas numpy CoolProp dearpygui streamlit
   ```

## 💻 Usage

### Main Calculation Engine

The primary calculation is performed using the `st_mary_material_energy_balance.py` script with the `stream_and_unit_classes.py` module:

```python
from st_mary_material_energy_balance import run_full_balance

# Define your input parameters
inputs = {
    'cane_tph': 350,
    'fiber_pct': 14.5,
    'pol_pct': 13.5,
    'juice_brix': 14,
    'syrup_brix': 65,
    # ... additional parameters
}

# Run the complete balance
results = run_full_balance(inputs, csv_path='output.csv')
```

### Standalone Evaporator Simulator

```python
# Run the evaporator program
python Evap_program.py
```

This script calculates:
- Multi-effect evaporator performance
- Steam consumption optimization
- Pressure profiles across effects
- Vapor bleed quantities

### Desktop GUI Application

```python
python evap_gemini_gui.py
```

Launches an interactive GUI for:
- Entering evaporator parameters
- Visualizing results
- Adjusting operating conditions in real-time

### Streamlit Web Interface

```bash
streamlit run streamlit_inputs.py
```

Opens a browser-based interface for data entry and visualization.

### Juice Heater Design

```python
python Juice_Heater.py
```

Calculate juice heater specifications and performance.

## 📁 Project Structure

```
Material_Energy_Balance_python/
│
├── stream_and_unit_classes.py      # Core classes (SugarStream, SteamStream, Evaporator, etc.)
├── st_mary_material_energy_balance.py  # Main calculation engine
├── Evap_program.py                 # Standalone evaporator simulator
├── evap_gemini_gui.py              # DearPyGUI desktop interface
├── streamlit_inputs.py             # Streamlit web interface
├── Juice_Heater.py                 # Juice heater design calculator
├── turbine.py                      # Steam turbine calculations
├── Mill_Settings.py                # Mill roller and mechanical specs
├── pan_balance.py                  # Pan crystallization balance
├── energy_balance_testing.py       # Testing and validation scripts
├── Linear_algrebra.py              # Mathematical utilities
├── specific_gravity_brix.py        # Brix-specific gravity conversions
└── README.md                       # This file
```

### Core Classes

#### `SugarStream`
Represents juice, syrup, molasses, or any sugar-bearing stream with properties:
- Mass flow rate (tph)
- Brix concentration (%)
- Purity (%)
- Temperature (°F)
- Pressure (psia)

#### `SteamStream`
Steam properties using IAPWS97:
- Pressure and temperature
- Enthalpy and entropy
- Quality (for wet steam)

#### `Evaporator`
Multi-effect evaporator unit with:
- Surface area (ft²)
- Heat transfer coefficient (U-value)
- Vapor generation
- Boiling point elevation

#### `SteamTurbine`
Turbine performance modeling:
- Isentropic expansion
- Work output
- Steam flow rates

## 🔧 Configuration

Key parameters for evaporator calculations (from `Evap_program.py`):

```python
# Input Data
m_L0 = 1450000      # Juice flow in lb/hr
bx_0 = 14           # Juice brix (%)
bx_N = 65           # Final syrup brix (%)
P_exh = 14          # Exhaust pressure (psig)
P_N = 25            # Last effect pressure (inches Hg vacuum)
Lvl = 2             # Tube liquid level (ft)
T_L0 = 225          # Juice inlet temperature (°F)
N = 4               # Number of effects

# Evaporator surface areas (ft²)
A_1d = 72000        # Effect 1
A_2d = 48000        # Effect 2
A_3d = 46000        # Effect 3
A_4d = 46000        # Effect 4
```

## 🎓 Technical Background

### Boiling Point Elevation (BPE)

The calculator uses two methods for BPE calculation:

1. **Brix-based BPE** (Dühring's rule):
   ```
   BPE₁ = 4.266667 × brix / (100 - brix)
   ```

2. **Level and temperature correction**:
   Uses polynomial correlations for brix and vapor temperature effects

### Multi-Effect Evaporation

The simulation iterates to find equilibrium conditions where:
- Heat transfer balances across all effects
- U-values (overall heat transfer coefficients) are consistent
- Pressure cascade is maintained (decreasing pressure from effect 1 to N)
- Mass flow rates satisfy material balance constraints

### Expected Operating Ranges

- **First Effect Calandria**: ~15 psig
- **Last Effect**: 25-26 inches Hg vacuum (user-specified)
- **Pressure Drop**: Each effect should show decreasing pressure
- **U-Ratio**: Should be approximately equal across all effect sets

## ⚠️ Known Issues

### Evaporator Loop Balance
The evaporation loop currently balances each effect set correctly but does not automatically rebalance juice flow distribution based on U-ratio optimization. Manual iteration may be required to achieve uniform heat transfer coefficients across all sets.

### Validation Checklist
When reviewing evaporator outputs:
- ✓ Verify U-ratios are approximately equal across all sets
- ✓ Confirm last effect pressure matches target (25-26" Hg)
- ✓ Check first effect calandria pressure (~15 psig)
- ✓ Ensure pressure decreases progressively through effects

## 📊 Output Formats

### Console Output
Detailed text-based results showing:
- Mill balance calculations
- Clarifier flows and chemical dosing
- Evaporator performance by effect
- Steam consumption summary

### CSV Export
Structured data export for:
- Stream properties (flow, brix, temperature, pressure)
- Energy balance results
- Equipment performance metrics

### GUI Display
Interactive tables and visualizations:
- Real-time parameter adjustment
- Graphical representation of results
- Comparative analysis tools

## 🤝 Contributing

This project is actively used for sugar mill operations. Contributions that improve accuracy, add features, or fix known issues are welcome.

### Development Guidelines
1. Maintain consistency with IAPWS97 standards for steam properties
2. Follow existing class structures in `stream_and_unit_classes.py`
3. Test calculations against known mill operating data
4. Document any changes to calculation methods
5. Preserve backward compatibility with existing input formats

## 📧 Contact

For questions about sugar mill applications or calculation methodologies, please open an issue on GitHub.

## 🙏 Acknowledgments

- Originally developed for St. Mary Sugar Cooperative
- Based on standard sugar engineering practices and thermodynamic principles
- Uses IAPWS97 industrial formulation for steam properties

---

**Note**: This tool is designed for engineering analysis and optimization. Always verify critical calculations with actual plant data and consult with experienced sugar mill engineers before making operational changes.
