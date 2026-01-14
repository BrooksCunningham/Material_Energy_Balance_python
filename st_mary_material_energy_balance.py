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
    "Grinding rate (tons/day)": 18000.0,
    "Lost time percent": 4.167,
    "Cane percent pol": 13.5,
    "Cane percent fiber": 13.0,
    "Imbibition water percent": 25.0,
    "Filter cake percent": 5.0,
    "Filter cake pol": 2.0,
    "Mixed juice purity": 88.0,
    "Mixed juice brix": 14.0,
    "Bagasse percent pol": 2.0,
    "Bagasse percent moisture": 49.0,
    "Bagasse percent ash": 4.0,
    "Last roll purity": 75.0
}

answer = 'r'
while answer == 'r':
    # 1. Input Section: Update the mill_data dictionary
    print("\n--- Enter Mill Data (Press Enter to keep current value) ---")
    for key, value in mill_data.items():
        user_input = input(f"{key} [{value:,.2f}]: ")
        if user_input.strip():
            mill_data[key] = float(user_input)
    
    time.sleep(0.5) # Stops execution for exactly 1 second
    termios.tcflush(sys.stdin, termios.TCIFLUSH) # Clear the input buffer

    # Short-hand variables for easier calculation logic
    # Use .get() or direct access; we'll pull them into a local dict for the math
    d = mill_data
    
    # 2. Calculation Section: Store results in a new dictionary
    results = {}
    

    # Time and Rates
    results['Hours lost'] = d["Lost time percent"] / 100 * 24
    results['Hours available'] = 24 - results['Hours lost']
    results['Tons cane per hour'] = d["Grinding rate (tons/day)"] / results['Hours available']
    
    # Cane Components
    results['Cane tons pol per hour'] = (d["Cane percent pol"] / 100) * results['Tons cane per hour']
    results['Cane tons fiber per hour'] = (d["Cane percent fiber"] / 100) * results['Tons cane per hour']
    
    # Process Streams
    results['Imbibition water tons per hour'] = (d["Imbibition water percent"] / 100) * results['Tons cane per hour']
    results['Filter cake tons per hour'] = (d["Filter cake percent"] / 100) * results['Tons cane per hour']
    results['Filter cake tons pol per hour'] = (results['Filter cake tons per hour'] * d["Filter cake pol"] / 100)
    
    # Bagasse Calculations
    results['Bagasse percent brix'] = d["Bagasse percent pol"] * 100 / d["Last roll purity"]
    results['Bagasse percent fiber'] = 100 - results['Bagasse percent brix'] - d["Bagasse percent moisture"]
    
    results['Bagasse tons fiber per hour'] = results['Cane tons fiber per hour']
    results['Tons bagasse per hour'] = results['Bagasse tons fiber per hour'] * 100 / results['Bagasse percent fiber']
    results['Bagasse tons pol per hour'] = (d["Bagasse percent pol"] / 100) * results['Tons bagasse per hour']
    results['Bagasse tons brix per hour'] = (results['Bagasse percent brix'] / 100) * results['Tons bagasse per hour']
    
    # Juice and Extraction
    results['Tons mixed juice per hour'] = (results['Tons cane per hour'] + 
                                            results['Imbibition water tons per hour'] - 
                                            results['Tons bagasse per hour'])
    
    mj_pol_pct = (d["Mixed juice purity"] / 100) * d["Mixed juice brix"]
    results['Mixed juice tons pol per hour'] = (mj_pol_pct / 100) * results['Tons mixed juice per hour']
    results['Mixed juice tons brix per hour'] = (d["Mixed juice brix"] / 100) * results['Tons mixed juice per hour']
    results['Extraction percent pol'] = (results['Mixed juice tons pol per hour'] / 
                                         results['Cane tons pol per hour']) * 100

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
    #"Mixed juice flow rate (tons/hr)": mill_results['Tons mixed juice per hour'],
    #"Filter cake flow rate (tons/hr)": mill_results['Filter cake tons per hour'],
    "Clarifier underflow percent cane": 20.0,
    "Mud Filter wash water percent cane": 5.0,
    "Flocculant flow rate (gpm)": 25.0,
    "Milk of Lime flow rate (gpm)": 25.0,
    "Clarified juice purity": 89.0,
    #"Clarified juice brix": 14.0,
    "Mixed Juice Temperature (F) to heaters": 90,
    "Mixed Juice Temperature (F) to clarifiers": 220,

}

answer = 'r'
while answer == 'r':
    # 1. Input Section: Update the mill_data dictionary
    print("\n--- Enter Clarifier Data (Press Enter to keep current value) ---")
    for key, value in clarifier_data.items():
        user_input = input(f"{key} [{value:,.2f}]: ")
        if user_input.strip():
            clarifier_data[key] = float(user_input)

    time.sleep(0.5) # Stops execution for exactly 1 second
    termios.tcflush(sys.stdin, termios.TCIFLUSH) # Clear the input buffer

    # getting outputs
    clarifier_results = {}

    clarifier_results['Tons Milk of Lime per hour'] = (
        (clarifier_data["Milk of Lime flow rate (gpm)"] * 9 * 60) / 2000
    )
    clarifier_results['Tons Flocculant per hour'] = (
        (clarifier_data["Flocculant flow rate (gpm)"] * 8.3 * 60) / 2000
    )

    clarifier_results['Filter wash water tons per hour'] = (
        clarifier_data["Mud Filter wash water percent cane"] / 100
    ) * mill_results['Tons cane per hour']

    clarifier_results['Tons Clarifier Underflow per hour'] = (
        (clarifier_data["Clarifier underflow percent cane"] / 100)
        * mill_results['Tons cane per hour']
    )

    clarifier_results['Filtrate juice flow rate (tons/hr)'] = (
        clarifier_results['Tons Clarifier Underflow per hour']
        + clarifier_results['Filter wash water tons per hour']
        - mill_results['Filter cake tons per hour']
    )

    clarifier_results['Mixed Juice with Filtrate flow rate (tons/hr)'] = (
        mill_results['Tons mixed juice per hour']
        + clarifier_results['Filter wash water tons per hour']
        + clarifier_results['Tons Milk of Lime per hour']
        + clarifier_results['Tons Flocculant per hour']
    )

    clarifier_results['Tons water in mixed juice flashed'] = (
        0.92 * clarifier_results['Mixed Juice with Filtrate flow rate (tons/hr)']
        * (clarifier_data["Mixed Juice Temperature (F) to clarifiers"] - 212)
        / 970
    )

    clarifier_results['Mixed Juice as Delivered to Clarifiers (tons/hr)'] = (
        clarifier_results['Mixed Juice with Filtrate flow rate (tons/hr)']
        - clarifier_results['Tons water in mixed juice flashed']
    )

    clarifier_results['Clarified juice flow rate (tons/hr)'] = (
        mill_results['Tons mixed juice per hour']
        - mill_results['Filter cake tons per hour']
        + clarifier_results['Filter wash water tons per hour']
        + clarifier_results['Tons Milk of Lime per hour']
        + clarifier_results['Tons Flocculant per hour']
        - clarifier_results['Tons water in mixed juice flashed']
    )

    clarifier_results['Clarified juice tons pol per hour'] = (
        mill_results['Mixed juice tons pol per hour']
        - mill_results['Filter cake tons pol per hour']
    )

    clarifier_results['Clarified juice tons brix per hour'] = (
        clarifier_results['Clarified juice tons pol per hour']
        * 100
        / clarifier_data["Clarified juice purity"]
    )

    clarifier_results['Clarified juice percent brix'] = (
        clarifier_results['Clarified juice tons brix per hour']
        / clarifier_results['Clarified juice flow rate (tons/hr)']
        *100
    )

    clarifier_results['Clarified juice percent pol'] = (
        clarifier_results['Clarified juice tons pol per hour']
        / clarifier_results['Clarified juice flow rate (tons/hr)']
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
    "Syrup Brix": 65.0,
}

answer = 'r'
while answer == 'r':
    # 1. Input Section: Update the mill_data dictionary
    print("\n--- Enter Evaporation Data (Press Enter to keep current value) ---")
    for key, value in evaporation_data.items():
        user_input = input(f"{key} [{value:,.2f}]: ")
        if user_input.strip():
            evaporation_data[key] = float(user_input)

    time.sleep(0.5) # Stops execution for exactly 1 second
    termios.tcflush(sys.stdin, termios.TCIFLUSH) # Clear the input buffer

    evaporation_results = {}

    evaporation_results['Tons syrup per hour'] = (
        clarifier_results['Clarified juice flow rate (tons/hr)']
        * clarifier_results['Clarified juice percent brix']
        / evaporation_data["Syrup Brix"]
    )

    evaporation_results['Tons evaporated per hour'] = (
        clarifier_results['Clarified juice flow rate (tons/hr)']
        - evaporation_results['Tons syrup per hour']
    )

    evaporation_results['Tons brix in syrup per hour'] = (
        evaporation_results['Tons syrup per hour']
        * evaporation_data["Syrup Brix"]
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
answer = input("\nDo you want to use Birkett's prediction for crystal yield? (y/n): ").lower()
if answer == 'n':
    print("The crystal yeild equation is a simple line on a xy graph, y = mx + b")
    slope = input("Enter the slope (m) of the line: ")
    intercept = input("Enter the intercept (b) of the line: ")

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
    if answer == 'n':
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
    "Raw Sugar Pol": 99.5,
    "Raw Sugar Brix": 99.7, 
    "B magma percent to A1 Strikes": 50.0,
    "B magma percent to A2 Strikes": 10.0,
    "B magma purity": 92.0,
    "Syrup percent to A2 Strikes": 25.0,
    "A1 molasses percent to A2 Strikes": 10.0,
    "A1 molasses percent to C Grain Strikes": 5.0,
    "C magma percent to B Strikes": 50.0,
    "C magma purity": 85.0,
    "B molasses percent to C Grain Strikes": 10.0,
    "Syrup percent to C Grain Strikes": 2.0,
    "A1 massecuite percent brix": 92.0,
    
}

# this will be a trial and error balance


answer = 'r'
while answer == 'r':
    # 1. Input Section: Update the mill_data dictionary
    print("\n--- Enter Pan Data (Press Enter to keep current value) ---")
    for key, value in pan_data.items():
        user_input = input(f"{key} [{value:,.2f}]: ")
        if user_input.strip():
            pan_data[key] = float(user_input)

    time.sleep(0.5) # Stops execution for exactly 1 second
    termios.tcflush(sys.stdin, termios.TCIFLUSH) # Clear the input buffer

    pan_results = {}

    pan_results['Tons syrup per hour'] = evaporation_results['Tons syrup per hour']
    pan_results['Tons brix in syrup per hour'] = (
        evaporation_results['Tons syrup per hour'] 
        * evaporation_data["Syrup Brix"] / 100
    )
    pan_results['Syrup purity'] = clarifier_data['Clarified juice purity']
    pan_results['Raw Sugar Purity'] = pan_data['Raw Sugar Pol'] / pan_data['Raw Sugar Brix'] * 100

    # set value of other data to zero for initial balance before trial error loop
    pan_results['B magma tons solids per hour'] = 0
    pan_results['B Molasses tons solids per hour'] = 0
    pan_results['A1 Molasses tons solids per hour'] = 0
    pan_results['A2 Molasses tons solids per hour'] = 0
    pan_results['C magma tons solids per hour'] = 0
    pan_results['Tons brix Grain massecuite'] = 0
    pan_results['C Molasses tons solids per hour'] = 0

    # Now for the loop
    iterations = 1
    while iterations < 100:

        # Begin with the A1 pans

        pan_results['Percent Syrup to A1 massecuite'] = (
            100
            - pan_data['Syrup percent to C Grain Strikes']
            - pan_data['Syrup percent to A2 Strikes']
        )

        pan_results['Tons brix syrup to A1 strikes'] = (
            pan_results['Tons brix in syrup per hour']
            * pan_results['Percent Syrup to A1 massecuite'] 
            / 100
        )

        pan_results['Tons brix B magma to A1 strikes'] = (
            pan_data['B magma percent to A1 Strikes']
            * pan_results['B magma tons solids per hour']
            /100
        )

        pan_results['Tons brix A1 massecuite'] = (
            pan_results['Tons brix syrup to A1 strikes']
            + pan_results['Tons brix B magma to A1 strikes']
        )

        pan_results['A1 Massecuite purity'] = (
            (pan_results['Tons brix syrup to A1 strikes'] * pan_results['Syrup purity']
            + pan_results['Tons brix B magma to A1 strikes'] * pan_data['B magma purity'])
            / pan_results['Tons brix A1 massecuite']
        )

        pan_results['A1 massecuite crystal yeild percent solids'] = (
            crystal_yield(pan_results['A1 Massecuite purity'])
        )

        pan_results['A1 Molasses Purity'] = (
            get_molasses_purity(
                pan_results['A1 massecuite crystal yeild percent solids'],
                pan_results['A1 Massecuite purity']
            )
        )

        s = pan_results['Raw Sugar Purity']
        j = pan_results['A1 Massecuite purity']
        m = pan_results['A1 Molasses Purity']
        j_tph = pan_results['Tons brix A1 massecuite']

        s_tph, m_tph = sjm_mid_flow_given(s, j, m, j_tph)

        pan_results['A1 Sugar tons solids per hour'] = s_tph
        pan_results['A1 Molasses tons solids per hour'] = m_tph

        # Now the A2 Pans
        pan_results['Tons brix A1 Molasses for A2 strikes'] = (
            pan_data['A1 molasses percent to A2 Strikes']
            * pan_results['A1 Molasses tons solids per hour']
            / 100
        )

        pan_results['Tons brix syrup to A2 strikes'] = (
            pan_results['Tons brix in syrup per hour']
            * pan_data['Syrup percent to A2 Strikes'] 
            / 100
        )

        pan_results['Tons brix B magma to A2 strikes'] = (
            pan_data['B magma percent to A2 Strikes']
            * pan_results['B magma tons solids per hour']
            / 100
        )

        pan_results['Tons brix A2 massecuite'] = (
            pan_results['Tons brix syrup to A2 strikes']
            + pan_results['Tons brix B magma to A2 strikes']
            + pan_results['Tons brix A1 Molasses for A2 strikes']
        )

        pan_results['A2 Massecuite purity'] = (
            (pan_results['Tons brix syrup to A2 strikes'] * pan_results['Syrup purity']
            + pan_results['Tons brix B magma to A2 strikes'] * pan_data['B magma purity']
            + pan_results['Tons brix A1 Molasses for A2 strikes'] * pan_results['A1 Molasses Purity'])
            / pan_results['Tons brix A2 massecuite']
        )

        pan_results['A2 massecuite crystal yeild percent solids'] = (
            crystal_yield(pan_results['A2 Massecuite purity'])
        )

        pan_results['A2 Molasses Purity'] = (
            get_molasses_purity(
                pan_results['A2 massecuite crystal yeild percent solids'],
                pan_results['A2 Massecuite purity']
            )
        )

        s = pan_results['Raw Sugar Purity']
        j = pan_results['A2 Massecuite purity']
        m = pan_results['A2 Molasses Purity']
        j_tph = pan_results['Tons brix A2 massecuite']

        s_tph, m_tph = sjm_mid_flow_given(s, j, m, j_tph)

        pan_results['A2 Sugar tons solids per hour'] = s_tph
        pan_results['A2 Molasses tons solids per hour'] = m_tph

        # Now the B Pans
        pan_results['Tons brix A1 Molasses for Grain Strikes'] = (
            pan_data['A1 molasses percent to C Grain Strikes']
            * pan_results['A1 Molasses tons solids per hour']
            / 100
        )

        pan_results['Tons brix A2 Molasses for B strikes'] = pan_results['A2 Molasses tons solids per hour']

        pan_results['Tons brix A1 Molasses for B strikes'] = (
            pan_results['A1 Molasses tons solids per hour']
            - pan_results['Tons brix A1 Molasses for A2 strikes']
            - pan_results['Tons brix A1 Molasses for Grain Strikes']
        )

        pan_results['Tons brix C magma for B strikes'] = (
            pan_data['C magma percent to B Strikes']
            * pan_results['C magma tons solids per hour']
            / 100
        )

        pan_results['Tons brix B massecuite'] = (
            pan_results['Tons brix A1 Molasses for B strikes']
            + pan_results['Tons brix A2 Molasses for B strikes']
            + pan_results['Tons brix C magma for B strikes']
        )

        pan_results['B Massecuite purity'] = (
            (pan_results['Tons brix A1 Molasses for B strikes'] * pan_results['A1 Molasses Purity']
            + pan_results['Tons brix A2 Molasses for B strikes'] * pan_results['A2 Molasses Purity']
            + pan_results['Tons brix C magma for B strikes'] * pan_data['C magma purity'])
            / pan_results['Tons brix B massecuite']
        )

        pan_results['B massecuite crystal yeild percent solids'] = (
            crystal_yield(pan_results['B Massecuite purity'])
        )

        pan_results['B Molasses Purity'] = (
            get_molasses_purity(
                pan_results['B massecuite crystal yeild percent solids'],
                pan_results['B Massecuite purity']
            )
        )

        s = pan_data['B magma purity']
        j = pan_results['B Massecuite purity']
        m = pan_results['B Molasses Purity']
        j_tph = pan_results['Tons brix B massecuite']

        s_tph, m_tph = sjm_mid_flow_given(s, j, m, j_tph)

        pan_results['B magma tons solids per hour'] = s_tph
        pan_results['B Molasses tons solids per hour'] = m_tph

        # Now the Grain Pans

        pan_results['Tons brix A1 Molasses for Grain Strikes'] = (
            pan_data['A1 molasses percent to C Grain Strikes']
            * pan_results['A1 Molasses tons solids per hour']
            / 100
        )

        pan_results['Tons brix B Molasses for Grain Strikes'] = (
            pan_data['B molasses percent to C Grain Strikes']
            * pan_results['B Molasses tons solids per hour']
            / 100
        )

        pan_results['Tons brix Syrup for Grain Strikes'] = (
            pan_data['Syrup percent to C Grain Strikes']
            * pan_results['Tons brix in syrup per hour']
            / 100
        )

        pan_results['Tons brix Grain massecuite'] = (
            pan_results['Tons brix A1 Molasses for Grain Strikes']
            + pan_results['Tons brix B Molasses for Grain Strikes']
            + pan_results['Tons brix Syrup for Grain Strikes']
        )

        pan_results['Grain Massecuite purity'] = (
            (pan_results['Tons brix A1 Molasses for Grain Strikes'] * pan_results['A1 Molasses Purity']
            + pan_results['Tons brix B Molasses for Grain Strikes'] * pan_results['B Molasses Purity']
            + pan_results['Tons brix Syrup for Grain Strikes'] * pan_results['Syrup purity'])
            / pan_results['Tons brix Grain massecuite']
        )

        # No crystal yeild for grain, no molasses either, but c massecuite yes

        pan_results['B molasses percent for C strikes'] = (
            100 - pan_data['B molasses percent to C Grain Strikes']
        )

        pan_results['Tons B Molasses for C strikes'] = (
            pan_results['B molasses percent for C strikes']
            * pan_results['B Molasses tons solids per hour']
            / 100
        )

        pan_results['Tons solids C massecuite'] = (
            pan_results['Tons B Molasses for C strikes']
            + pan_results['Tons brix Grain massecuite']
        )

        pan_results['C massecuite purity'] = (
            (pan_results['Tons B Molasses for C strikes'] * pan_results['B Molasses Purity']
            + pan_results['Tons brix Grain massecuite'] * pan_results['Grain Massecuite purity'])
            / pan_results['Tons solids C massecuite']
        )

        pan_results['C massecuite crystal yeild percent solids'] = (
            crystal_yield(pan_results['C massecuite purity'])
        )

        pan_results['C Molasses Purity'] = (
            get_molasses_purity(
                pan_results['C massecuite crystal yeild percent solids'],
                pan_results['C massecuite purity']
            )
        )

        s = pan_data['C magma purity']
        j = pan_results['C massecuite purity']
        m = pan_results['C Molasses Purity']
        j_tph = pan_results['Tons solids C massecuite']

        s_tph, m_tph = sjm_mid_flow_given(s, j, m, j_tph)

        pan_results['C magma tons solids per hour'] = s_tph
        pan_results['C Molasses tons solids per hour'] = m_tph

        pan_results['Percent c magma remelted'] = (
           100 - pan_data['C magma percent to B Strikes']
        )

        pan_results['Percent b magma remelted'] = (
            100 - pan_data['B magma percent to A1 Strikes'] - pan_data['B magma percent to A2 Strikes']
        )

        pan_results['B magma tons solids remelted'] = (
            pan_results['Percent b magma remelted'] / 100 * pan_results['B magma tons solids per hour']
        )

        pan_results['C magma tons solids remelted'] = (
            pan_results['Percent c magma remelted'] / 100 * pan_results['C magma tons solids per hour']
        )

        pan_results['Tons brix in syrup per hour'] = (
            evaporation_results['Tons brix in syrup per hour'] 
            + pan_results['B magma tons solids remelted']
            + pan_results['C magma tons solids remelted']
        )

        pan_results['Syrup purity'] = (
            (evaporation_results['Tons brix in syrup per hour'] * clarifier_data['Clarified juice purity']
            + pan_results['B magma tons solids remelted'] * pan_data['B magma purity']
            + pan_results['C magma tons solids remelted'] * pan_data['C magma purity'])
            / pan_results['Tons brix in syrup per hour']
        )

        
        iterations += 1
    # something is very wrong... need to figure out why... try tomorrow, just freaking use the other program...
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



# Now I want to export all inputs and outputs to a txt file
# Initialize the application (this is the missing piece)
#app = QApplication(sys.argv)

# 1. Setup Timing and Filename
#now = datetime.now()
#timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
#filename = f"material_energy_balance_{timestamp}.txt"

# 2. Get Directory from User
#folder_path = QFileDialog.getExistingDirectory(None, "Select folder to save file")
"""
if folder_path:
    
    full_path = os.path.join(folder_path, filename)
    
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write("========================================\n")
            f.write(f"MATERIAL BALANCE REPORT - {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("========================================\n\n")

            f.write("--- INPUTS ---\n")
            f.write(f"Grinding rate:                {grinding_rate:,.2f} tons per day\n")
            f.write(f"Lost time percent:            {lost_time_percent:.2f}%\n")
            f.write(f"Cane percent pol:             {cane_percent_pol:.2f}%\n")
            f.write(f"Cane percent fiber:           {cane_percent_fiber:.2f}%\n")
            f.write(f"Imbibition water percent:     {imbibition_water_percent:.2f}%\n")
            f.write(f"Filter cake percent:          {filter_cake_percent:.2f}%\n")
            f.write(f"Filter cake pol:              {filter_cake_pol:.2f}%\n")
            f.write(f"Mixed juice purity:           {mixed_juice_purity:.2f}%\n")
            f.write(f"Mixed juice brix:             {mixed_juice_brix:.2f}%\n")
            f.write(f"Bagasse percent pol:          {bagasse_percent_pol:.2f}%\n")
            f.write(f"Bagasse percent moisture:     {bagasse_percent_moisture:.2f}%\n")
            f.write(f"Bagasse percent ash:          {bagasse_percent_ash:.2f}%\n") # Corrected typo
            f.write(f"Last roll purity:             {last_roll_purity:.2f}%\n\n")

            f.write("--- OUTPUTS ---\n")
            f.write(f"Hours lost:                   {hours_lost:.2f}\n")
            f.write(f"Hours available:              {hours_available:.2f}\n")
            f.write(f"Tons cane per hour:           {tons_cane_per_hour:.2f}\n")
            f.write(f"Cane tons pol per hour:       {cane_tons_pol_per_hour:.2f}\n")
            f.write(f"Cane tons fiber per hour:     {cane_tons_fiber_per_hour:.2f}\n")
            f.write(f"Imbibition water TPH:         {imbibition_water_tons_per_hour:.2f}\n")
            f.write(f"Filter cake TPH:              {filter_cake_tons_per_hour:.2f}\n")
            f.write(f"Filter cake tons pol per hour:{filter_cake_tons_pol_per_hour:.2f}\n")
            f.write(f"Bagasse tons fiber per hour:  {bagasse_tons_fiber_per_hour:.2f}\n")
            f.write(f"Bagasse tons pol per hour:    {bagasse_tons_pol_per_hour:.2f}\n")
            f.write(f"Bagasse tons brix per hour:   {bagasse_tons_brix_per_hour:.2f}\n")
            f.write(f"Tons mixed juice per hour:    {tons_mixed_juice_per_hour:.2f}\n")
            f.write(f"Mixed juice tons pol per hour:{mixed_juice_tons_pol_per_hour:.2f}\n")
            f.write(f"Mixed juice tons brix per hr: {mixed_juice_tons_brix_per_hour:.2f}\n")
            f.write(f"Extraction percent pol:       {extraction_percent_pol:.2f}%\n")
            
        print(f"File successfully saved to: {full_path}")
        
    except Exception as e:
        print(f"An error occurred while saving: {e}")
else:
    print("No folder selected, file not saved")
"""
