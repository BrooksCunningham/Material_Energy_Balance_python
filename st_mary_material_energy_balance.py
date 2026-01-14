# Python material and energy balance for st mary sugar
from datetime import datetime
# from PyQt6.QtWidgets import QFileDialog
#from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication
import os
import sys
import time
import termios
# test for github


# Mill floor material balance, loop function to ensure user likes data before moving on
# input data
# Get input data
# Initial values stored in a dictionary for easy iteration
mill_data = {
    "grinding_rate_tons_day": 18000.0,
    "lost_time_percent": 4.167,
    "cane_percent_pol": 13.5,
    "cane_percent_fiber": 13.0,
    "imbibition_water_percent": 25.0,
    "filter_cake_percent": 5.0,
    "filter_cake_pol": 2.0,
    "mixed_juice_purity": 88.0,
    "mixed_juice_brix": 14.0,
    "bagasse_percent_pol": 2.0,
    "bagasse_percent_moisture": 49.0,
    "bagasse_percent_ash": 4.0,
    "last_roll_purity": 75.0
}

answer = 'r'
while answer == 'r':
    # 1. Input Section: Update the mill_data dictionary
    print("\n--- Enter Mill Data (Press Enter to keep current value) ---")
    for key, value in mill_data.items():
        while True:
            user_input = input(f"{key} [{value:,.2f}]: ")
            if user_input.strip():
                try:
                    mill_data[key] = float(user_input)
                    break
                except ValueError:
                    print("Invalid input. Please enter a number.")
            else:
                break
    
    time.sleep(0.5) # Stops execution for exactly 1 second
    termios.tcflush(sys.stdin, termios.TCIFLUSH) # Clear the input buffer

    # Short-hand variables for easier calculation logic
    # Use .get() or direct access; we'll pull them into a local dict for the math
    d = mill_data
    
    # 2. Calculation Section: Store results in a new dictionary
    results = {}
    

    # Time and Rates
    results['hours_lost'] = d["lost_time_percent"] / 100 * 24
    results['hours_available'] = 24 - results['hours_lost']
    results['tons_cane_per_hour'] = d["grinding_rate_tons_day"] / results['hours_available']
    
    # Cane Components
    results['cane_tons_pol_per_hour'] = (d["cane_percent_pol"] / 100) * results['tons_cane_per_hour']
    results['cane_tons_fiber_per_hour'] = (d["cane_percent_fiber"] / 100) * results['tons_cane_per_hour']
    
    # Process Streams
    results['imbibition_water_tons_per_hour'] = (d["imbibition_water_percent"] / 100) * results['tons_cane_per_hour']
    results['filter_cake_tons_per_hour'] = (d["filter_cake_percent"] / 100) * results['tons_cane_per_hour']
    results['filter_cake_tons_pol_per_hour'] = (results['filter_cake_tons_per_hour'] * d["filter_cake_pol"] / 100)
    
    # Bagasse Calculations
    results['bagasse_percent_brix'] = d["bagasse_percent_pol"] * 100 / d["last_roll_purity"]
    results['bagasse_percent_fiber'] = 100 - results['bagasse_percent_brix'] - d["bagasse_percent_moisture"]
    
    results['bagasse_tons_fiber_per_hour'] = results['cane_tons_fiber_per_hour']
    results['tons_bagasse_per_hour'] = results['bagasse_tons_fiber_per_hour'] * 100 / results['bagasse_percent_fiber']
    results['bagasse_tons_pol_per_hour'] = (d["bagasse_percent_pol"] / 100) * results['tons_bagasse_per_hour']
    results['bagasse_tons_brix_per_hour'] = (results['bagasse_percent_brix'] / 100) * results['tons_bagasse_per_hour']
    
    # Juice and Extraction
    results['tons_mixed_juice_per_hour'] = (results['tons_cane_per_hour'] + 
                                            results['imbibition_water_tons_per_hour'] - 
                                            results['tons_bagasse_per_hour'])
    
    mj_pol_pct = (d["mixed_juice_purity"] / 100) * d["mixed_juice_brix"]
    results['mixed_juice_tons_pol_per_hour'] = (mj_pol_pct / 100) * results['tons_mixed_juice_per_hour']
    results['mixed_juice_tons_brix_per_hour'] = (d["mixed_juice_brix"] / 100) * results['tons_mixed_juice_per_hour']
    results['extraction_percent_pol'] = (results['mixed_juice_tons_pol_per_hour'] / 
                                         results['cane_tons_pol_per_hour']) * 100

    # 3. Output Summary: Loop through both dictionaries
    print(f"\n{'FIELD':<40}{'VALUE':>15}")
    print("-" * 55)
    
    # Print Inputs
    for key, value in mill_data.items():
        print(f"{key:<40}{value:>15,.2f}")
    
    print("-" * 55)
    
    # Print Calculations
    for key, value in results.items():
        # Add a % sign to the labels that need it
        label = f"{key}%" if "percent" in key.lower() else key
        print(f"{label:<40}{value:>15,.2f}")
        
    # 4. Continue or Exit
    answer = input("\nHit Enter to continue, 'r' to re-enter, or 'quit' to exit: ").lower()
    if answer == 'quit':
        break

    mill_results = results


# Now moving on to mud filters and clarifiers
# Initial values as a dictionary
clarifier_data = {
    #"mixed_juice_flow_rate_tons_hr": mill_results['tons_mixed_juice_per_hour'],
    #"filter_cake_flow_rate_tons_hr": mill_results['filter_cake_tons_per_hour'],
    "clarifier_underflow_percent_cane": 20.0,
    "mud_filter_wash_water_percent_cane": 5.0,
    "flocculant_flow_rate_gpm": 25.0,
    "milk_of_lime_flow_rate_gpm": 25.0,
    "clarified_juice_purity": 89.0,
    #"clarified_juice_brix": 14.0,
    "mixed_juice_temp_f_to_heaters": 90,
    "mixed_juice_temp_f_to_clarifiers": 220,

}

answer = 'r'
while answer == 'r':
    # 1. Input Section: Update the mill_data dictionary
    print("\n--- Enter Clarifier Data (Press Enter to keep current value) ---")
    for key, value in clarifier_data.items():
        while True:
            user_input = input(f"{key} [{value:,.2f}]: ")
            if user_input.strip():
                try:
                    clarifier_data[key] = float(user_input)
                    break
                except ValueError:
                    print("Invalid input. Please enter a number.")
            else:
                break

    time.sleep(0.5) # Stops execution for exactly 1 second
    termios.tcflush(sys.stdin, termios.TCIFLUSH) # Clear the input buffer

    # getting outputs
    clarifier_results = {}

    clarifier_results['tons_milk_of_lime_per_hour'] = (
        (clarifier_data["milk_of_lime_flow_rate_gpm"] * 9 * 60) / 2000
    )
    clarifier_results['tons_flocculant_per_hour'] = (
        (clarifier_data["flocculant_flow_rate_gpm"] * 8.3 * 60) / 2000
    )

    clarifier_results['filter_wash_water_tons_per_hour'] = (
        clarifier_data["mud_filter_wash_water_percent_cane"] / 100
    ) * mill_results['tons_cane_per_hour']

    clarifier_results['tons_clarifier_underflow_per_hour'] = (
        (clarifier_data["clarifier_underflow_percent_cane"] / 100)
        * mill_results['tons_cane_per_hour']
    )

    clarifier_results['filtrate_juice_flow_rate_tons_hr'] = (
        clarifier_results['tons_clarifier_underflow_per_hour']
        + clarifier_results['filter_wash_water_tons_per_hour']
        - mill_results['filter_cake_tons_per_hour']
    )

    clarifier_results['mixed_juice_with_filtrate_flow_rate_tons_hr'] = (
        mill_results['tons_mixed_juice_per_hour']
        + clarifier_results['filter_wash_water_tons_per_hour']
        + clarifier_results['tons_milk_of_lime_per_hour']
        + clarifier_results['tons_flocculant_per_hour']
    )

    clarifier_results['tons_water_in_mixed_juice_flashed'] = (
        0.92 * clarifier_results['mixed_juice_with_filtrate_flow_rate_tons_hr']
        * (clarifier_data["mixed_juice_temp_f_to_clarifiers"] - 212)
        / 970
    )

    clarifier_results['mixed_juice_as_delivered_to_clarifiers_tons_hr'] = (
        clarifier_results['mixed_juice_with_filtrate_flow_rate_tons_hr']
        - clarifier_results['tons_water_in_mixed_juice_flashed']
    )

    clarifier_results['clarified_juice_flow_rate_tons_hr'] = (
        mill_results['tons_mixed_juice_per_hour']
        - mill_results['filter_cake_tons_per_hour']
        + clarifier_results['filter_wash_water_tons_per_hour']
        + clarifier_results['tons_milk_of_lime_per_hour']
        + clarifier_results['tons_flocculant_per_hour']
        - clarifier_results['tons_water_in_mixed_juice_flashed']
    )

    clarifier_results['clarified_juice_tons_pol_per_hour'] = (
        mill_results['mixed_juice_tons_pol_per_hour']
        - mill_results['filter_cake_tons_pol_per_hour']
    )

    clarifier_results['clarified_juice_tons_brix_per_hour'] = (
        clarifier_results['clarified_juice_tons_pol_per_hour']
        * 100
        / clarifier_data["clarified_juice_purity"]
    )

    clarifier_results['clarified_juice_percent_brix'] = (
        clarifier_results['clarified_juice_tons_brix_per_hour']
        / clarifier_results['clarified_juice_flow_rate_tons_hr']
        *100
    )

    clarifier_results['clarified_juice_percent_pol'] = (
        clarifier_results['clarified_juice_tons_pol_per_hour']
        / clarifier_results['clarified_juice_flow_rate_tons_hr']
        *100
    )

    # 3. Output Summary: Loop through both dictionaries
    print(f"\n{'FIELD':<40}{'VALUE':>15}")
    print("-" * 55)
    
    # Print Inputs
    for key, value in clarifier_data.items():
        print(f"{key:<40}{value:>15,.2f}")
    
    print("-" * 55)
    
    # Print Calculations
    for key, value in clarifier_results.items():
        # Add a % sign to the labels that need it
        label = f"{key}%" if "percent" in key.lower() else key
        print(f"{label:<55}{value:>15,.2f}")
        
    # 4. Continue or Exit
    answer = input("\nHit Enter to continue, 'r' to re-enter, or 'quit' to exit: ").lower()
    if answer == 'quit':
        break

# Now onto the evaporation section, this is a simple balance that just gets tph syrup and tph evaporated

evaporation_data = {
    "syrup_brix": 65.0,
}

answer = 'r'
while answer == 'r':
    # 1. Input Section: Update the mill_data dictionary
    print("\n--- Enter Evaporation Data (Press Enter to keep current value) ---")
    for key, value in evaporation_data.items():
        while True:
            user_input = input(f"{key} [{value:,.2f}]: ")
            if user_input.strip():
                try:
                    evaporation_data[key] = float(user_input)
                    break
                except ValueError:
                    print("Invalid input. Please enter a number.")
            else:
                break

    time.sleep(0.5) # Stops execution for exactly 1 second
    termios.tcflush(sys.stdin, termios.TCIFLUSH) # Clear the input buffer

    evaporation_results = {}

    evaporation_results['tons_syrup_per_hour'] = (
        clarifier_results['clarified_juice_flow_rate_tons_hr']
        * clarifier_results['clarified_juice_percent_brix']
        / evaporation_data["syrup_brix"]
    )

    evaporation_results['tons_evaporated_per_hour'] = (
        clarifier_results['clarified_juice_flow_rate_tons_hr']
        - evaporation_results['tons_syrup_per_hour']
    )

    evaporation_results['tons_brix_in_syruer_hour'] = (
        evaporation_results['tons_syrup_per_hour']
        * evaporation_data["syrup_brix"]
        / 100
    )

        # 3. Output Summary: Loop through both dictionaries
    print(f"\n{'FIELD':<40}{'VALUE':>15}")
    print("-" * 55)
    
    # Print Inputs
    for key, value in evaporation_data.items():
        print(f"{key:<40}{value:>15,.2f}")
    
    print("-" * 55)
    
    # Print Calculations
    for key, value in evaporation_results.items():
        # Add a % sign to the labels that need it
        label = f"{key}%" if "percent" in key.lower() else key
        print(f"{label:<40}{value:>15,.2f}")
        
    # 4. Continue or Exit
    answer = input("\nHit Enter to continue, 'r' to re-enter, or 'quit' to exit: ").lower()
    if answer == 'quit':
        break

# Now for crystallization
# This is a hybrid 4 boiling / 3 boiling double magma scheme

# Using birkett's slope for crystal yeild based on massecuite purity
while True:
    birkett_choice = input("\nDo you want to use Birkett's prediction for crystal yield? (y/n): ").lower()
    if birkett_choice in ['y', 'n']:
        break
    print("Invalid input. Please enter 'y' or 'n'.")

if birkett_choice == 'n':
    print("The crystal yeild equation is a simple line on a xy graph, y = mx + b")
    while True:
        try:
            slope = float(input("Enter the slope (m) of the line: "))
            break
        except ValueError:
            print("Invalid input. Please enter a number.")
    while True:
        try:
            intercept = float(input("Enter the intercept (b) of the line: "))
            break
        except ValueError:
            print("Invalid input. Please enter a number.")

def crystal_yield(massecuite_purity):
    """
    Calculate the crystal yield percent solids using birkett's slope.

    Parameters
    ----------
    massecuite_purity : float
        The massecuite purity in percent.

    Returns
    -------
    float
        The crystal yield percent solids.
    """
    if birkett_choice == 'n':
        m = float(slope)
        y_intercept = float(intercept)
    else:
        m = 0.7609 # m = birkett's slope
        y_intercept = -11.693

    x = massecuite_purity
    # y = m * x + y_intercept is the equation of the line
    y = m * x + y_intercept
    return y # returns crystal yield percent solids

# gather input data for how to run the scheme
# remember that crystal yeild % solids is (massecuite purity - molasses purity) / (100 - molasses purity)
# cy / 100 = (massecuite purity - molasses purity) / (100 - molasses purity)
# cy / 100 * (100 - molasses purity) = massecuite purity - molasses purity
# cy / 100 * (100 - molasses purity) - massecuite purity = - molasses purity
# cy * (1 - molasses purity / 100) - massecuite purity = - molasses purity
# cy - cy * molasses purity / 100 - massecuite purity = - molasses purity
# molasses purity - cy * molasses purity / 100 = massecuite purity - cy
# molasses purity (1 - cy / 100) = massecuite purity - cy
# molasses purity = (massecuite purity - cy) / (1 - cy / 100)

def get_molasses_purity(crystal_yield, massecuite_purity):
    """calculates molasses purity based on crystal yield and massecuite purity"""
    cy = crystal_yield
    p_ma = massecuite_purity
    p_mol = (p_ma - cy) / (1 - cy / 100)
    return p_mol

def sjm_mid_flow_given(s, j, m, j_tph):
    """ returns solids flows of high and low purity flow given mid purity flow"""
    s_tph = (j - m) / (s - m) * j_tph
    m_tph = j_tph - s_tph
    return s_tph, m_tph

    

pan_data = {
    "raw_sugar_pol": 99.5,
    "raw_sugar_brix": 99.7, 
    "b_magma_percent_to_a1_strikes": 50.0,
    "b_magma_percent_to_a2_strikes": 10.0,
    "b_magma_purity": 92.0,
    "syrup_percent_to_a2_strikes": 25.0,
    "a1_molasses_percent_to_a2_strikes": 10.0,
    "a1_molasses_percent_to_c_grain_strikes": 5.0,
    "c_magma_percent_to_b_strikes": 50.0,
    "c_magma_purity": 85.0,
    "b_molasses_percent_to_c_grain_strikes": 10.0,
    "syrup_percent_to_c_grain_strikes": 2.0,
    "a1_massecuite_percent_brix": 92.0,
    
}

# this will be a trial and error balance


answer = 'r'
while answer == 'r':
    # 1. Input Section: Update the mill_data dictionary
    print("\n--- Enter Pan Data (Press Enter to keep current value) ---")
    for key, value in pan_data.items():
        while True:
            user_input = input(f"{key} [{value:,.2f}]: ")
            if user_input.strip():
                try:
                    pan_data[key] = float(user_input)
                    break
                except ValueError:
                    print("Invalid input. Please enter a number.")
            else:
                break

    time.sleep(0.5) # Stops execution for exactly 1 second
    termios.tcflush(sys.stdin, termios.TCIFLUSH) # Clear the input buffer

    pan_results = {}

    pan_results['tons_syrup_per_hour'] = evaporation_results['tons_syrup_per_hour']
    pan_results['tons_brix_in_syrup_per_hour'] = (
        evaporation_results['tons_syrup_per_hour'] 
        * evaporation_data["syrup_brix"] / 100
    )
    pan_results['syrup_purity'] = clarifier_data['clarified_juice_purity']
    pan_results['raw_sugar_purity'] = pan_data['raw_sugar_pol'] / pan_data['raw_sugar_brix'] * 100

    # set value of other data to zero for initial balance before trial error loop
    pan_results['b_magma_tons_solids_per_hour'] = 0
    pan_results['b_molasses_tons_solids_per_hour'] = 0
    pan_results['a1_molasses_tons_solids_per_hour'] = 0
    pan_results['a2_molasses_tons_solids_per_hour'] = 0
    pan_results['c_magma_tons_solids_per_hour'] = 0
    pan_results['tons_brix_grain_massecuite'] = 0
    pan_results['c_molasses_tons_solids_per_hour'] = 0

    # Now for the loop
    iterations = 1
    while iterations < 100:

        # Begin with the A1 pans

        pan_results['percent_syrup_to_a1_massecuite'] = (
            100
            - pan_data['syrup_percent_to_c_grain_strikes']
            - pan_data['syrup_percent_to_a2_strikes']
        )

        pan_results['tons_brix_syrup_to_a1_strikes'] = (
            pan_results['tons_brix_in_syrup_per_hour']
            * pan_results['percent_syrup_to_a1_massecuite'] 
            / 100
        )

        pan_results['tons_brix_b_magma_to_a1_strikes'] = (
            pan_data['b_magma_percent_to_a1_strikes']
            * pan_results['b_magma_tons_solids_per_hour']
            /100
        )

        pan_results['tons_brix_a1_massecuite'] = (
            pan_results['tons_brix_syrup_to_a1_strikes']
            + pan_results['tons_brix_b_magma_to_a1_strikes']
        )

        pan_results['a1_massecuite_purity'] = (
            (pan_results['tons_brix_syrup_to_a1_strikes'] * pan_results['syrup_purity']
            + pan_results['tons_brix_b_magma_to_a1_strikes'] * pan_data['b_magma_purity'])
            / pan_results['tons_brix_a1_massecuite']
        )

        pan_results['a1_massecuite_crystal_yield_percent_solids'] = (
            crystal_yield(pan_results['a1_massecuite_purity'])
        )

        pan_results['a1_molasses_purity'] = (
            get_molasses_purity(
                pan_results['a1_massecuite_crystal_yield_percent_solids'],
                pan_results['a1_massecuite_purity']
            )
        )

        s = pan_results['raw_sugar_purity']
        j = pan_results['a1_massecuite_purity']
        m = pan_results['a1_molasses_purity']
        j_tph = pan_results['tons_brix_a1_massecuite']

        s_tph, m_tph = sjm_mid_flow_given(s, j, m, j_tph)

        pan_results['a1_sugar_tons_solids_per_hour'] = s_tph
        pan_results['a1_molasses_tons_solids_per_hour'] = m_tph

        # Now the A2 Pans
        pan_results['tons_brix_a1_molasses_for_a2_strikes'] = (
            pan_data['a1_molasses_percent_to_a2_strikes']
            * pan_results['a1_molasses_tons_solids_per_hour']
            / 100
        )

        pan_results['tons_brix_syrup_to_a2_strikes'] = (
            pan_results['tons_brix_in_syrup_per_hour']
            * pan_data['syrup_percent_to_a2_strikes'] 
            / 100
        )

        pan_results['tons_brix_b_magma_to_a2_strikes'] = (
            pan_data['b_magma_percent_to_a2_strikes']
            * pan_results['b_magma_tons_solids_per_hour']
            / 100
        )

        pan_results['tons_brix_a2_massecuite'] = (
            pan_results['tons_brix_syrup_to_a2_strikes']
            + pan_results['tons_brix_b_magma_to_a2_strikes']
            + pan_results['tons_brix_a1_molasses_for_a2_strikes']
        )

        pan_results['a2_massecuite_purity'] = (
            (pan_results['tons_brix_syrup_to_a2_strikes'] * pan_results['syrup_purity']
            + pan_results['tons_brix_b_magma_to_a2_strikes'] * pan_data['b_magma_purity']
            + pan_results['tons_brix_a1_molasses_for_a2_strikes'] * pan_results['a1_molasses_purity'])
            / pan_results['tons_brix_a2_massecuite']
        )

        pan_results['a2_massecuite_crystal_yield_percent_solids'] = (
            crystal_yield(pan_results['a2_massecuite_purity'])
        )

        pan_results['a2_molasses_purity'] = (
            get_molasses_purity(
                pan_results['a2_massecuite_crystal_yield_percent_solids'],
                pan_results['a2_massecuite_purity']
            )
        )

        s = pan_results['raw_sugar_purity']
        j = pan_results['a2_massecuite_purity']
        m = pan_results['a2_molasses_purity']
        j_tph = pan_results['tons_brix_a2_massecuite']

        s_tph, m_tph = sjm_mid_flow_given(s, j, m, j_tph)

        pan_results['a2_sugar_tons_solids_per_hour'] = s_tph
        pan_results['a2_molasses_tons_solids_per_hour'] = m_tph

        # Now the B Pans
        pan_results['tons_brix_a1_molasses_for_grain_strikes'] = (
            pan_data['a1_molasses_percent_to_c_grain_strikes']
            * pan_results['a1_molasses_tons_solids_per_hour']
            / 100
        )

        pan_results['tons_brix_a2_molasses_for_b_strikes'] = pan_results['a2_molasses_tons_solids_per_hour']

        pan_results['tons_brix_a1_molasses_for_b_strikes'] = (
            pan_results['a1_molasses_tons_solids_per_hour']
            - pan_results['tons_brix_a1_molasses_for_a2_strikes']
            - pan_results['tons_brix_a1_molasses_for_grain_strikes']
        )

        pan_results['tons_brix_c_magma_for_b_strikes'] = (
            pan_data['c_magma_percent_to_b_strikes']
            * pan_results['c_magma_tons_solids_per_hour']
            / 100
        )

        pan_results['tons_brix_b_massecuite'] = (
            pan_results['tons_brix_a1_molasses_for_b_strikes']
            + pan_results['tons_brix_a2_molasses_for_b_strikes']
            + pan_results['tons_brix_c_magma_for_b_strikes']
        )

        pan_results['b_massecuite_purity'] = (
            (pan_results['tons_brix_a1_molasses_for_b_strikes'] * pan_results['a1_molasses_purity']
            + pan_results['tons_brix_a2_molasses_for_b_strikes'] * pan_results['a2_molasses_purity']
            + pan_results['tons_brix_c_magma_for_b_strikes'] * pan_data['c_magma_purity'])
            / pan_results['tons_brix_b_massecuite']
        )

        pan_results['b_massecuite_crystal_yield_percent_solids'] = (
            crystal_yield(pan_results['b_massecuite_purity'])
        )

        pan_results['b_molasses_purity'] = (
            get_molasses_purity(
                pan_results['b_massecuite_crystal_yield_percent_solids'],
                pan_results['b_massecuite_purity']
            )
        )

        s = pan_data['b_magma_purity']
        j = pan_results['b_massecuite_purity']
        m = pan_results['b_molasses_purity']
        j_tph = pan_results['tons_brix_b_massecuite']

        s_tph, m_tph = sjm_mid_flow_given(s, j, m, j_tph)

        pan_results['b_magma_tons_solids_per_hour'] = s_tph
        pan_results['b_molasses_tons_solids_per_hour'] = m_tph

        # Now the Grain Pans

        pan_results['tons_brix_a1_molasses_for_grain_strikes'] = (
            pan_data['a1_molasses_percent_to_c_grain_strikes']
            * pan_results['a1_molasses_tons_solids_per_hour']
            / 100
        )

        pan_results['tons_brix_b_molasses_for_grain_strikes'] = (
            pan_data['b_molasses_percent_to_c_grain_strikes']
            * pan_results['b_molasses_tons_solids_per_hour']
            / 100
        )

        pan_results['tons_brix_syrup_for_grain_strikes'] = (
            pan_data['syrup_percent_to_c_grain_strikes']
            * pan_results['tons_brix_in_syrup_per_hour']
            / 100
        )

        pan_results['tons_brix_grain_massecuite'] = (
            pan_results['tons_brix_a1_molasses_for_grain_strikes']
            + pan_results['tons_brix_b_molasses_for_grain_strikes']
            + pan_results['tons_brix_syrup_for_grain_strikes']
        )

        pan_results['grain_massecuite_purity'] = (
            (pan_results['tons_brix_a1_molasses_for_grain_strikes'] * pan_results['a1_molasses_purity']
            + pan_results['tons_brix_b_molasses_for_grain_strikes'] * pan_results['b_molasses_purity']
            + pan_results['tons_brix_syrup_for_grain_strikes'] * pan_results['syrup_purity'])
            / pan_results['tons_brix_grain_massecuite']
        )

        # No crystal yeild for grain, no molasses either, but c massecuite yes

        pan_results['b_molasses_percent_for_c_strikes'] = (
            100 - pan_data['b_molasses_percent_to_c_grain_strikes']
        )

        pan_results['tons_b_molasses_for_c_strikes'] = (
            pan_results['b_molasses_percent_for_c_strikes']
            * pan_results['b_molasses_tons_solids_per_hour']
            / 100
        )

        pan_results['tons_solids_c_massecuite'] = (
            pan_results['tons_b_molasses_for_c_strikes']
            + pan_results['tons_brix_grain_massecuite']
        )

        pan_results['c_massecuite_purity'] = (
            (pan_results['tons_b_molasses_for_c_strikes'] * pan_results['b_molasses_purity']
            + pan_results['tons_brix_grain_massecuite'] * pan_results['grain_massecuite_purity'])
            / pan_results['tons_solids_c_massecuite']
        )

        pan_results['c_massecuite_crystal_yield_percent_solids'] = (
            crystal_yield(pan_results['c_massecuite_purity'])
        )

        pan_results['c_molasses_purity'] = (
            get_molasses_purity(
                pan_results['c_massecuite_crystal_yield_percent_solids'],
                pan_results['c_massecuite_purity']
            )
        )

        s = pan_data['c_magma_purity']
        j = pan_results['c_massecuite_purity']
        m = pan_results['c_molasses_purity']
        j_tph = pan_results['tons_solids_c_massecuite']

        s_tph, m_tph = sjm_mid_flow_given(s, j, m, j_tph)

        pan_results['c_magma_tons_solids_per_hour'] = s_tph
        pan_results['c_molasses_tons_solids_per_hour'] = m_tph

        pan_results['percent_c_magma_remelted'] = (
           100 - pan_data['c_magma_percent_to_b_strikes']
        )

        pan_results['percent_b_magma_remelted'] = (
            100 - pan_data['b_magma_percent_to_a1_strikes'] - pan_data['b_magma_percent_to_a2_strikes']
        )

        pan_results['b_magma_tons_solids_remelted'] = (
            pan_results['percent_b_magma_remelted'] / 100 * pan_results['b_magma_tons_solids_per_hour']
        )

        pan_results['c_magma_tons_solids_remelted'] = (
            pan_results['percent_c_magma_remelted'] / 100 * pan_results['c_magma_tons_solids_per_hour']
        )

        pan_results['tons_brix_in_syrup_per_hour'] = (
            evaporation_results['tons_brix_in_syrup_per_hour'] 
            + pan_results['b_magma_tons_solids_remelted']
            + pan_results['c_magma_tons_solids_remelted']
        )

        pan_results['syrup_purity'] = (
            (evaporation_results['tons_brix_in_syrup_per_hour'] * clarifier_data['clarified_juice_purity']
            + pan_results['b_magma_tons_solids_remelted'] * pan_data['b_magma_purity']
            + pan_results['c_magma_tons_solids_remelted'] * pan_data['c_magma_purity'])
            / pan_results['tons_brix_in_syrup_per_hour']
        )
        
        iterations += 1
            # 3. Output Summary: Loop through both dictionaries
    print(f"\n{'FIELD':<50}{'VALUE':>15}")
    print("-" * 55)
    
    # Print Inputs
    for key, value in pan_data.items():
        print(f"{key:<50}{value:>15,.2f}")
    
    print("-" * 55)
    
    # Print Calculations
    for key, value in pan_results.items():
        # Add a % sign to the labels that need it
        label = f"{key}%" if "percent" in key.lower() else key
        print(f"{label:<50}{value:>15,.2f}")
        
    # 4. Continue or Exit
    answer = input("\nHit Enter to continue, 'r' to re-enter, or 'quit' to exit: ").lower()
    if answer == 'quit':
        break
