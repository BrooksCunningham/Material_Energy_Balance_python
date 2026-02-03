# GitHub Copilot Instructions

## Project Context
This is a Material and Energy Balance Calculator for Sugar Mills (cane sugar processing facilities). The application models multi-effect evaporator systems, steam turbines, juice heaters, and mill operations.

## Domain Knowledge

### Sugar Mill Process Flow
1. **Mill** - Crushes sugar cane to extract juice (mixed juice)
2. **Clarifier** - Removes impurities using lime and heat, produces clear juice
3. **Evaporators** - Multi-effect concentration from ~14% brix to ~65% brix syrup
4. **Vacuum Pans** - Further concentration and crystallization to produce sugar
5. **Centrifuges** - Separate sugar crystals from molasses

### Key Terminology
- **Brix**: Sugar content percentage by weight (°Bx)
- **Pol**: Sucrose content percentage
- **Purity**: Ratio of sucrose to total solids
- **TPH**: Tons per hour (mass flow rate)
- **BPE**: Boiling Point Elevation (increases with sugar concentration)
- **Calandria**: Heat exchanger section of an evaporator
- **Effect**: Individual evaporator stage in a multi-effect system
- **Massecuite**: Mixture of sugar crystals and molasses

### Units
- Mass flow: tons per hour (tph) or pounds per hour (lb/hr)
- Temperature: Fahrenheit (°F)
- Pressure: psia (absolute) or psig (gauge) or inches of Hg vacuum
- Area: square feet (ft²)
- Brix: percentage (%)
- Heat transfer coefficient: BTU/(hr·ft²·°F)

## Code Structure

### Core Classes (`stream_and_unit_classes.py`)

#### SugarStream
Represents sugar-bearing streams (juice, syrup, molasses).
```python
SugarStream(name, tag, mass_flow_tph, brix, purity, temperature_deg_F, pressure_psia, liquid_level)
```

#### SteamStream
Steam properties using IAPWS97 standard.
```python
SteamStream(name, tag, pressure_psia, temperature_deg_F, mass_flow_lb_hr)
```

#### Evaporator
Multi-effect evaporator calculations.
```python
Evaporator(name, tag, heating_steam, juice_in, surface_area_sqft)
```

#### SteamTurbine
Steam turbine performance modeling.
```python
SteamTurbine(name, inlet_steam, exhaust_pressure_psia, efficiency)
```

### Main Calculation Engine (`st_mary_material_energy_balance.py`)
Entry point: `run_full_balance(inputs, csv_path=None)`
- Mill balance
- Clarifier balance
- Evaporator balance
- Pan balance
- Returns results dictionary and exports to CSV

## Coding Conventions

### Naming Conventions
- Stream tags: Lowercase with underscores (e.g., `j_005`, `sy_001`, `st_101`)
  - `j_` prefix for juice streams
  - `sy_` prefix for syrup streams
  - `st_` prefix for steam streams
  - `m_` prefix for molasses streams
- Variables: Snake_case (e.g., `mass_flow_tph`, `juice_brix`)
- Constants: UPPER_CASE (e.g., `STEAM_SOURCES`)

### Property Access
- Use `.mass_flow_tph` for ton per hour
- Use `.lb_per_hr` for pounds per hour
- Use `.brix` for concentration (%)
- Use `.temperature_deg_F` for temperature
- Use `.pressure_psia` for pressure
- Use `.enthalpy_btu_lb` for steam enthalpy

### Thermodynamic Calculations
- Always use IAPWS97 for steam properties: `from iapws import IAPWS97`
- Steam object: `IAPWS97(P=pressure_MPa, T=temperature_K)` or `IAPWS97(P=pressure_MPa, x=quality)`
- Convert units: psia to MPa: `psia * 0.00689476`, °F to K: `(degF - 32) * 5/9 + 273.15`

### Energy Balance
- Heat duty: `Q = m * h_in - m * h_out` (BTU/hr)
- Evaporation: `evap = (heat_in - sensible_heat_change) / latent_heat`
- Material balance: `mass_in = mass_out + evaporation`

### BPE Calculation
Two components:
1. Brix-based: `BPE1 = 4.266667 * brix / (100 - brix)`
2. Level/temperature correction: Use `calculate_bpe2(liquid_level, brix, vapor_temp)`
3. Total: `BPE = BPE1 + BPE2`

## Common Patterns

### Creating a new stream
```python
juice = SugarStream(
    name='clear juice',
    tag='j_005',
    mass_flow_tph=350,
    brix=14,
    purity=88,
    temperature_deg_F=225,
    pressure_psia=14.696,
    liquid_level=2
)
```

### Steam property lookup
```python
steam = IAPWS97(P=pressure_MPa, T=temperature_K)
enthalpy = steam.h * 0.42992  # Convert kJ/kg to BTU/lb
```

### Evaporator setup
```python
evap = Evaporator(
    name='Effect 1',
    tag='evap_1',
    heating_steam=steam_stream,
    juice_in=juice_stream,
    surface_area_sqft=72000
)
```

## Testing & Validation

### Expected Ranges
- First effect calandria: ~15 psig
- Last effect: 25-26 inches Hg vacuum
- Juice temperature rise: 10-15°F per effect
- Evaporation rate: 60-70% of heating steam flow
- U-values: 150-300 BTU/(hr·ft²·°F) depending on effect

### Validation Checks
- Material balance closure: `sum(inputs) ≈ sum(outputs)`
- Energy balance closure: Within 5% typically
- Pressure cascade: Each effect should have lower pressure than previous
- U-ratios: Should be approximately equal across effect sets

## Known Issues
- Evaporator loop balances each set correctly but doesn't rebalance juice flow based on U-ratio optimization
- Manual iteration may be required for optimal distribution

## When Suggesting Code
1. Use consistent units (prefer tph for mass flow)
2. Always include proper BPE calculations for evaporators
3. Use IAPWS97 for steam properties
4. Maintain material and energy balance closure
5. Include validation checks for physical feasibility
6. Document assumptions for sugar mill engineers
7. Consider operational constraints (pressure ranges, temperature limits)
