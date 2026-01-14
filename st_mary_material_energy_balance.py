# Python material and energy balance for st mary sugar
from datetime import datetime
# from PyQt6.QtWidgets import QFileDialog
#from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication
import os
import sys
import time
import dearpygui.dearpygui as dpg
from stream_and_unit_classes import SteamStream, Evaporator, SugarStream, SteamTurbine


# test for github

def get_data_from_gui(data_dict, title="Data Entry"):
    """Opens a popup window to edit values in a dictionary."""
    dpg.create_context()
    dpg.set_global_font_scale(1.3)
    
    updated_data = data_dict.copy()
    input_tags = {}

    def submit_callback():
        try:
            for key, tag in input_tags.items():
                val = dpg.get_value(tag)
                updated_data[key] = float(val)
            dpg.stop_dearpygui()
        except ValueError:
            print("Invalid input detected. Please enter numbers.")

    with dpg.window(label=title, tag="Primary Window"):
        dpg.add_text("Please edit the values below:")
        dpg.add_separator()
        
        for key, value in data_dict.items():
            label_text = key.replace("_", " ").title()
            tag = f"input_{key}"
            input_tags[key] = tag
            dpg.add_input_text(label=label_text, default_value=str(value), tag=tag)

        dpg.add_separator()
        dpg.add_button(label="Submit", callback=submit_callback, width=150, height=40)

    dpg.create_viewport(title=title, width=600, height=700)
    dpg.setup_dearpygui()
    dpg.set_primary_window("Primary Window", True)
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
    return updated_data

def get_action_gui(title="Continue?"):
    """Opens a popup to ask the user what to do next."""
    dpg.create_context()
    dpg.set_global_font_scale(1.3)
    user_choice = {"value": ""}

    def set_choice(choice):
        user_choice["value"] = choice
        dpg.stop_dearpygui()

    with dpg.window(label=title, tag="Primary Window"):
        dpg.add_text("Select an action:")
        dpg.add_button(label="Continue to Next Section", callback=lambda: set_choice(""), width=-1, height=40)
        dpg.add_button(label="Re-enter Data", callback=lambda: set_choice("r"), width=-1, height=40)
        dpg.add_button(label="Quit Program", callback=lambda: set_choice("quit"), width=-1, height=40)

    dpg.create_viewport(title=title, width=400, height=300)
    dpg.setup_dearpygui()
    dpg.set_primary_window("Primary Window", True)
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
    return user_choice["value"]

def show_results_gui(data_dict, title="Results"):
    """Displays a dictionary of results in a popup window."""
    dpg.create_context()
    dpg.set_global_font_scale(1.3)
    
    with dpg.window(label=title, tag="Primary Window"):
        dpg.add_text(f"--- {title} ---")
        dpg.add_separator()
        
        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, scrollY=True):
            dpg.add_table_column(label="Field")
            dpg.add_table_column(label="Value")
            
            for key, value in data_dict.items():
                with dpg.table_row():
                    label_text = key.replace("_", " ").title()
                    if "percent" in key.lower():
                        label_text += " (%)"
                    
                    dpg.add_text(label_text)
                    if isinstance(value, (int, float)):
                        dpg.add_text(f"{value:,.2f}")
                    else:
                        dpg.add_text(str(value))

        dpg.add_separator()
        dpg.add_button(label="Continue", callback=lambda: dpg.stop_dearpygui(), width=150, height=40)

    dpg.create_viewport(title=title, width=600, height=700)
    dpg.setup_dearpygui()
    dpg.set_primary_window("Primary Window", True)
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

def show_error_gui(message, title="Error"):
    """Displays a modal error message."""
    dpg.create_context()
    dpg.set_global_font_scale(1.3)
    
    with dpg.window(label=title, modal=True, no_close=True, tag="ErrorWindow"):
        dpg.add_text(message, wrap=400)
        dpg.add_spacer(height=10)
        dpg.add_button(label="Acknowledge & Retry", width=-1, height=30, callback=lambda: dpg.stop_dearpygui())

    # Create a viewport if one doesn't exist
    dpg.create_viewport(title=title, width=450, height=180)
    dpg.setup_dearpygui()
    dpg.set_primary_window("ErrorWindow", True)
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

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
    "bagasse_percent_pol": 2.0,
    "bagasse_percent_moisture": 49.0,
    "bagasse_percent_ash": 4.0,
    "last_roll_purity": 75.0
}

answer = 'r'
while answer == 'r':
    # 1. Input Section: Update the mill_data dictionary
    mill_data = get_data_from_gui(mill_data, "Enter Mill Data")

    # Short-hand variables for easier calculation logic
    # Use .get() or direct access; we'll pull them into a local dict for the math
    d = mill_data
    
    try:
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
        
        results['mixed_juice_tons_pol_per_hour'] = results['cane_tons_pol_per_hour'] - results['bagasse_tons_pol_per_hour']
        results['mixed_juice_percent_pol'] = results['mixed_juice_tons_pol_per_hour'] / results['tons_mixed_juice_per_hour']
        results['mixed_juice_percent_brix'] = d['mixed_juice_purity'] * 100 / results['mixed_juice_percent_pol']
        results['extraction_percent_pol'] = (results['mixed_juice_tons_pol_per_hour'] / 
                                            results['cane_tons_pol_per_hour']) * 100

        display_data = {**mill_data, **results}
        show_results_gui(display_data, "Mill Balance Results")
            
    except ZeroDivisionError:
        print("\n!!! Error: Division by zero detected. Please check your inputs. Restarting section... !!!")
        time.sleep(2)
        continue
        
    # 4. Continue or Exit
    answer = get_action_gui("Mill Data Complete")
    if answer == 'quit':
        break

    mill_results = results

if answer == 'quit':
    sys.exit()


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
    clarifier_data = get_data_from_gui(clarifier_data, "Enter Clarifier Data")

    try:
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

        display_data = {**clarifier_data, **clarifier_results}
        show_results_gui(display_data, "Clarifier Balance Results")
            
    except ZeroDivisionError:
        print("\n!!! Error: Division by zero detected. Please check your inputs. Restarting section... !!!")
        time.sleep(2)
        continue
        
    # 4. Continue or Exit
    answer = get_action_gui("Clarifier Data Complete")
    if answer == 'quit':
        break

if answer == 'quit':
    sys.exit()

# Now onto the evaporation section, this is a simple balance that just gets tph syrup and tph evaporated

evaporation_data = {
    "syrup_brix": 65.0,
}

answer = 'r'
while answer == 'r':
    # 1. Input Section: Update the mill_data dictionary
    evaporation_data = get_data_from_gui(evaporation_data, "Enter Evaporation Data")

    try:
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

        evaporation_results['tons_brix_in_syrup_per_hour'] = (
            evaporation_results['tons_syrup_per_hour']
            * evaporation_data["syrup_brix"]
            / 100
        )

        display_data = {**evaporation_data, **evaporation_results}
        show_results_gui(display_data, "Evaporation Balance Results")
            
    except ZeroDivisionError:
        print("\n!!! Error: Division by zero detected. Please check your inputs. Restarting section... !!!")
        time.sleep(2)
        continue
        
    # 4. Continue or Exit
    answer = get_action_gui("Evaporation Data Complete")
    if answer == 'quit':
        break

if answer == 'quit':
    sys.exit()

# Now for crystallization
# This is a hybrid 4 boiling / 3 boiling double magma scheme

# Using birkett's slope for crystal yeild based on massecuite purity
dpg.create_context()
dpg.set_global_font_scale(1.3)
birkett_container = {"choice": "n"}

def set_birkett(val):
    birkett_container["choice"] = val
    dpg.stop_dearpygui()

with dpg.window(label="Crystal Yield", tag="Primary Window"):
    dpg.add_text("Do you want to use Birkett's prediction for crystal yield?")
    with dpg.group(horizontal=True):
        dpg.add_button(label="Yes", callback=lambda: set_birkett("y"), width=100, height=40)
        dpg.add_button(label="No", callback=lambda: set_birkett("n"), width=100, height=40)

dpg.create_viewport(title="Crystal Yield Method", width=450, height=200)
dpg.setup_dearpygui()
dpg.set_primary_window("Primary Window", True)
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

birkett_choice = birkett_container["choice"]

if birkett_choice == 'n':
    line_data = {"slope": 0.0, "intercept": 0.0}
    line_data = get_data_from_gui(line_data, "Enter Line Equation Parameters (y = mx + b)")
    slope = line_data["slope"]
    intercept = line_data["intercept"]

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

"""
gather input data for how to run the scheme
remember that crystal yeild % solids is (massecuite purity - molasses purity) / (100 - molasses purity)
cy / 100 = (massecuite purity - molasses purity) / (100 - molasses purity)
cy / 100 * (100 - molasses purity) = massecuite purity - molasses purity
cy / 100 * (100 - molasses purity) - massecuite purity = - molasses purity
cy * (1 - molasses purity / 100) - massecuite purity = - molasses purity
cy - cy * molasses purity / 100 - massecuite purity = - molasses purity
molasses purity - cy * molasses purity / 100 = massecuite purity - cy
molasses purity (1 - cy / 100) = massecuite purity - cy
molasses purity = (massecuite purity - cy) / (1 - cy / 100)
"""

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
    "a2_massecuite_percent_brix": 92.0,
    "a1_molasses_percent_brix": 75.0,
    "a2_molasses_percent_brix": 75.0,
    "b_magma_percent_brix": 92.0,
    "b_massecuite_percent_brix": 93.0,
    "b_molasses_percent_brix": 75.0,
    "grain_massecuite_percent_brix": 90.0,
    "c_magma_percent_brix": 93.0,
    "c_massecuite_percent_brix": 95.0,
    "c_molasses_percent_brix": 75.0,
    "remelt_percent_brix": evaporation_data["syrup_brix"],
    "a1_massecuite_steam_factor": 1.15,
    "a2_massecuite_steam_factor": 1.15,
    "b_massecuite_steam_factor": 1.15,
    "c_massecuite_steam_factor": 1.25,
    "grain_massecuite_steam_factor": 1.25,
    
    
    
}

# this will be a trial and error balance


answer = 'r'
while answer == 'r':
    # 1. Input Section: Update the mill_data dictionary
    pan_data = get_data_from_gui(pan_data, "Enter Pan Data")

    try:
        pan_results = {}

        pan_results['tons_brix_syrup_and_remelt_per_hour'] = (
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
                pan_results['tons_brix_syrup_and_remelt_per_hour']
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
                pan_results['tons_brix_syrup_and_remelt_per_hour']
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
                * pan_results['tons_brix_syrup_and_remelt_per_hour']
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

            pan_results['tons_brix_syrup_and_remelt_per_hour'] = (
                evaporation_results['tons_brix_in_syrup_per_hour'] 
                + pan_results['b_magma_tons_solids_remelted']
                + pan_results['c_magma_tons_solids_remelted']
            )

            pan_results['tons_syrup_and_remelt_per_hour'] = (
                pan_results['tons_brix_syrup_and_remelt_per_hour'] * 100 / evaporation_data["syrup_brix"]
            )

            pan_results['syrup_purity'] = (
                (evaporation_results['tons_brix_in_syrup_per_hour'] * clarifier_data['clarified_juice_purity']
                + pan_results['b_magma_tons_solids_remelted'] * pan_data['b_magma_purity']
                + pan_results['c_magma_tons_solids_remelted'] * pan_data['c_magma_purity'])
                / pan_results['tons_brix_syrup_and_remelt_per_hour']
            )

            # Calculate total material flows (tons/hr) based on solids and brix
            pan_results['tons_a1_massecuite_per_hour'] = pan_results['tons_brix_a1_massecuite'] * 100 / pan_data['a1_massecuite_percent_brix']
            pan_results['tons_a1_molasses_per_hour'] = pan_results['a1_molasses_tons_solids_per_hour'] * 100 / pan_data['a1_molasses_percent_brix']
            pan_results['tons_a1_sugar_per_hour'] = pan_results['a1_sugar_tons_solids_per_hour'] * 100 / pan_data['raw_sugar_brix']

            pan_results['tons_a2_massecuite_per_hour'] = pan_results['tons_brix_a2_massecuite'] * 100 / pan_data['a2_massecuite_percent_brix']
            pan_results['tons_a2_molasses_per_hour'] = pan_results['a2_molasses_tons_solids_per_hour'] * 100 / pan_data['a2_molasses_percent_brix']
            pan_results['tons_a2_sugar_per_hour'] = pan_results['a2_sugar_tons_solids_per_hour'] * 100 / pan_data['raw_sugar_brix']

            pan_results['tons_b_massecuite_per_hour'] = pan_results['tons_brix_b_massecuite'] * 100 / pan_data['b_massecuite_percent_brix']
            pan_results['tons_b_molasses_per_hour'] = pan_results['b_molasses_tons_solids_per_hour'] * 100 / pan_data['b_molasses_percent_brix']
            pan_results['tons_b_magma_per_hour'] = pan_results['b_magma_tons_solids_per_hour'] * 100 / pan_data['b_magma_percent_brix']

            pan_results['tons_grain_massecuite_per_hour'] = pan_results['tons_brix_grain_massecuite'] * 100 / pan_data['grain_massecuite_percent_brix']

            pan_results['tons_c_massecuite_per_hour'] = pan_results['tons_solids_c_massecuite'] * 100 / pan_data['c_massecuite_percent_brix']
            pan_results['tons_c_molasses_per_hour'] = pan_results['c_molasses_tons_solids_per_hour'] * 100 / pan_data['c_molasses_percent_brix']
            pan_results['tons_c_magma_per_hour'] = pan_results['c_magma_tons_solids_per_hour'] * 100 / pan_data['c_magma_percent_brix']

            # Water Evaporated Calculations
            # multipliers for using V1 or V2 instead of exhaust
            v1_multiplier = 0.98330
            v2_multiplier = 0.96906

            # A1
            tons_syrup_to_a1 = pan_results['tons_brix_syrup_to_a1_strikes'] * 100 / evaporation_data["syrup_brix"]
            tons_b_magma_to_a1 = pan_results['tons_brix_b_magma_to_a1_strikes'] * 100 / pan_data['b_magma_percent_brix']
            pan_results['tons_water_evap_a1'] = tons_syrup_to_a1 + tons_b_magma_to_a1 - pan_results['tons_a1_massecuite_per_hour']
            pan_results['tons_exhaust_steam_a1'] = pan_results['tons_water_evap_a1'] * pan_data['a1_massecuite_steam_factor']
            pan_results['tons_v1_steam_a1'] = pan_results['tons_exhaust_steam_a1'] * v1_multiplier
            pan_results['tons_v2_steam_a1'] = pan_results['tons_exhaust_steam_a1'] * v2_multiplier

            # A2
            tons_syrup_to_a2 = pan_results['tons_brix_syrup_to_a2_strikes'] * 100 / evaporation_data["syrup_brix"]
            tons_b_magma_to_a2 = pan_results['tons_brix_b_magma_to_a2_strikes'] * 100 / pan_data['b_magma_percent_brix']
            tons_a1_mol_to_a2 = pan_results['tons_brix_a1_molasses_for_a2_strikes'] * 100 / pan_data['a1_molasses_percent_brix']
            pan_results['tons_water_evap_a2'] = tons_syrup_to_a2 + tons_b_magma_to_a2 + tons_a1_mol_to_a2 - pan_results['tons_a2_massecuite_per_hour']
            pan_results['tons_exhaust_steam_a2'] = pan_results['tons_water_evap_a2'] * pan_data['a2_massecuite_steam_factor']
            pan_results['tons_v1_steam_a2'] = pan_results['tons_exhaust_steam_a2'] * v1_multiplier
            pan_results['tons_v2_steam_a2'] = pan_results['tons_exhaust_steam_a2'] * v2_multiplier

            # B
            tons_a1_mol_to_b = pan_results['tons_brix_a1_molasses_for_b_strikes'] * 100 / pan_data['a1_molasses_percent_brix']
            tons_a2_mol_to_b = pan_results['tons_brix_a2_molasses_for_b_strikes'] * 100 / pan_data['a2_molasses_percent_brix']
            tons_c_magma_to_b = pan_results['tons_brix_c_magma_for_b_strikes'] * 100 / pan_data['c_magma_percent_brix']
            pan_results['tons_water_evap_b'] = tons_a1_mol_to_b + tons_a2_mol_to_b + tons_c_magma_to_b - pan_results['tons_b_massecuite_per_hour']
            pan_results['tons_exhaust_steam_b'] = pan_results['tons_water_evap_b'] * pan_data['b_massecuite_steam_factor']
            pan_results['tons_v1_steam_b'] = pan_results['tons_exhaust_steam_b'] * v1_multiplier
            pan_results['tons_v2_steam_b'] = pan_results['tons_exhaust_steam_b'] * v2_multiplier

            # Grain
            tons_syrup_to_grain = pan_results['tons_brix_syrup_for_grain_strikes'] * 100 / evaporation_data["syrup_brix"]
            tons_a1_mol_to_grain = pan_results['tons_brix_a1_molasses_for_grain_strikes'] * 100 / pan_data['a1_molasses_percent_brix']
            tons_b_mol_to_grain = pan_results['tons_brix_b_molasses_for_grain_strikes'] * 100 / pan_data['b_molasses_percent_brix']
            pan_results['tons_water_evap_grain'] = tons_syrup_to_grain + tons_a1_mol_to_grain + tons_b_mol_to_grain - pan_results['tons_grain_massecuite_per_hour']
            pan_results['tons_exhaust_steam_grain'] = pan_results['tons_water_evap_grain'] * pan_data['grain_massecuite_steam_factor']
            pan_results['tons_v1_steam_grain'] = pan_results['tons_exhaust_steam_grain'] * v1_multiplier
            pan_results['tons_v2_steam_grain'] = pan_results['tons_exhaust_steam_grain'] * v2_multiplier

            # C
            tons_grain_to_c = pan_results['tons_grain_massecuite_per_hour']
            tons_b_mol_to_c = pan_results['tons_b_molasses_for_c_strikes'] * 100 / pan_data['b_molasses_percent_brix']
            pan_results['tons_water_evap_c'] = tons_grain_to_c + tons_b_mol_to_c - pan_results['tons_c_massecuite_per_hour']
            pan_results['tons_exhaust_steam_c'] = pan_results['tons_water_evap_c'] * pan_data['c_massecuite_steam_factor']
            pan_results['tons_v1_steam_c'] = pan_results['tons_exhaust_steam_c'] * v1_multiplier
            pan_results['tons_v2_steam_c'] = pan_results['tons_exhaust_steam_c'] * v2_multiplier

            
            iterations += 1
        
        # Organize outputs for display
        display_data = {}

        # 1. Overall Inputs/Outputs
        display_data["--- OVERALL BALANCE ---"] = ""
        display_data["Syrup Feed (Evap) (Tons/hr)"] = evaporation_results['tons_syrup_per_hour']
        display_data["Syrup + Remelt Feed (Tons/hr)"] = pan_results['tons_syrup_and_remelt_per_hour']
        display_data["Syrup Brix"] = evaporation_data["syrup_brix"]
        display_data["Syrup + Remelt Purity"] = pan_results['syrup_purity']
        
        total_sugar_tph = pan_results['tons_a1_sugar_per_hour'] + pan_results['tons_a2_sugar_per_hour']
        display_data["Total Raw Sugar (Tons/hr)"] = total_sugar_tph
        display_data["Raw Sugar Pol"] = pan_data['raw_sugar_pol']
        display_data["Raw Sugar Brix"] = pan_data['raw_sugar_brix']
        
        display_data["Final Molasses (Tons/hr)"] = pan_results['tons_c_molasses_per_hour']
        display_data["Final Molasses Brix"] = pan_data['c_molasses_percent_brix']
        display_data["Final Molasses Purity"] = pan_results['c_molasses_purity']

        # 2. A1 Station
        display_data["--- A1 STATION ---"] = ""
        display_data["A1 Massecuite (Tons/hr)"] = pan_results['tons_a1_massecuite_per_hour']
        display_data["A1 Massecuite Brix"] = pan_data['a1_massecuite_percent_brix']
        display_data["A1 Massecuite Purity"] = pan_results['a1_massecuite_purity']
        display_data["A1 Massecuite Crystal Yield"] = pan_results['a1_massecuite_crystal_yield_percent_solids']
        
        # Inputs
        syrup_to_a1_tph = pan_results['tons_brix_syrup_to_a1_strikes'] * 100 / evaporation_data["syrup_brix"]
        display_data["A1 Input: Syrup (Tons/hr)"] = syrup_to_a1_tph
        
        b_magma_to_a1_tph = pan_results['tons_brix_b_magma_to_a1_strikes'] * 100 / pan_data['b_magma_percent_brix']
        display_data["A1 Input: B Magma (Tons/hr)"] = b_magma_to_a1_tph
        
        # Outputs
        display_data["Output: A1 Sugar (Tons/hr)"] = pan_results['tons_a1_sugar_per_hour']
        display_data["Output: A1 Molasses (Tons/hr)"] = pan_results['tons_a1_molasses_per_hour']
        display_data["A1 Molasses Purity"] = pan_results['a1_molasses_purity']
        display_data["A1 Water Evaporated (Tons/hr)"] = pan_results['tons_water_evap_a1']
        display_data["A1 Exhaust Steam Required (Tons/hr)"] = pan_results['tons_exhaust_steam_a1']
        display_data["A1 V1 Steam Required (Tons/hr)"] = pan_results['tons_v1_steam_a1']
        display_data["A1 V2 Steam Required (Tons/hr)"] = pan_results['tons_v2_steam_a1']


        # 3. A2 Station
        display_data["--- A2 STATION ---"] = ""
        display_data["A2 Massecuite (Tons/hr)"] = pan_results['tons_a2_massecuite_per_hour']
        display_data["A2 Massecuite Brix"] = pan_data['a2_massecuite_percent_brix']
        display_data["A2 Massecuite Purity"] = pan_results['a2_massecuite_purity']
        display_data["A2 Massecuite Crystal Yield"] = pan_results['a2_massecuite_crystal_yield_percent_solids']
        
        # Inputs
        syrup_to_a2_tph = pan_results['tons_brix_syrup_to_a2_strikes'] * 100 / evaporation_data["syrup_brix"]
        display_data["A2 Input: Syrup (Tons/hr)"] = syrup_to_a2_tph
        
        b_magma_to_a2_tph = pan_results['tons_brix_b_magma_to_a2_strikes'] * 100 / pan_data['b_magma_percent_brix']
        display_data["A2 Input: B Magma (Tons/hr)"] = b_magma_to_a2_tph
        
        a1_mol_to_a2_tph = pan_results['tons_brix_a1_molasses_for_a2_strikes'] * 100 / pan_data['a1_molasses_percent_brix']
        display_data["A2 Input: A1 Molasses (Tons/hr)"] = a1_mol_to_a2_tph
        
        # Outputs
        display_data["Output: A2 Sugar (Tons/hr)"] = pan_results['tons_a2_sugar_per_hour']
        display_data["Output: A2 Molasses (Tons/hr)"] = pan_results['tons_a2_molasses_per_hour']
        display_data["A2 Molasses Purity"] = pan_results['a2_molasses_purity']
        display_data["A2 Water Evaporated (Tons/hr)"] = pan_results['tons_water_evap_a2']
        display_data["A2 Exhaust Steam Required (Tons/hr)"] = pan_results['tons_exhaust_steam_a2']
        display_data["A2 V1 Steam Required (Tons/hr)"] = pan_results['tons_v1_steam_a2']
        display_data["A2 V2 Steam Required (Tons/hr)"] = pan_results['tons_v2_steam_a2']

        # 4. B Station
        display_data["--- B STATION ---"] = ""
        display_data["B Massecuite (Tons/hr)"] = pan_results['tons_b_massecuite_per_hour']
        display_data["B Massecuite Brix"] = pan_data['b_massecuite_percent_brix']
        display_data["B Massecuite Purity"] = pan_results['b_massecuite_purity']
        display_data["B Massecuite Crystal Yield"] = pan_results['b_massecuite_crystal_yield_percent_solids']
        
        # Inputs
        a1_mol_to_b_tph = pan_results['tons_brix_a1_molasses_for_b_strikes'] * 100 / pan_data['a1_molasses_percent_brix']
        display_data["B Input: A1 Molasses (Tons/hr)"] = a1_mol_to_b_tph
        
        a2_mol_to_b_tph = pan_results['tons_brix_a2_molasses_for_b_strikes'] * 100 / pan_data['a2_molasses_percent_brix']
        display_data["B Input: A2 Molasses (Tons/hr)"] = a2_mol_to_b_tph
        
        c_magma_to_b_tph = pan_results['tons_brix_c_magma_for_b_strikes'] * 100 / pan_data['c_magma_percent_brix']
        display_data["B Input: C Magma (Tons/hr)"] = c_magma_to_b_tph
        
        # Outputs
        display_data["Output: B Magma (Tons/hr)"] = pan_results['tons_b_magma_per_hour']
        display_data["B Magma Purity"] = pan_data['b_magma_purity']
        display_data["Output: B Molasses (Tons/hr)"] = pan_results['tons_b_molasses_per_hour']
        display_data["B Molasses Purity"] = pan_results['b_molasses_purity']
        display_data["B Water Evaporated (Tons/hr)"] = pan_results['tons_water_evap_b']
        display_data["B Exhaust Steam Required (Tons/hr)"] = pan_results['tons_exhaust_steam_b']
        display_data["B V1 Steam Required (Tons/hr)"] = pan_results['tons_v1_steam_b']
        display_data["B V2 Steam Required (Tons/hr)"] = pan_results['tons_v2_steam_b']

        # 5. Grain Station
        display_data["--- GRAIN STATION ---"] = ""
        display_data["Grain Massecuite (Tons/hr)"] = pan_results['tons_grain_massecuite_per_hour']
        display_data["Grain Massecuite Brix"] = pan_data['grain_massecuite_percent_brix']
        display_data["Grain Massecuite Purity"] = pan_results['grain_massecuite_purity']
        
        # Inputs
        syrup_to_grain_tph = pan_results['tons_brix_syrup_for_grain_strikes'] * 100 / evaporation_data["syrup_brix"]
        display_data["Grain Input: Syrup (Tons/hr)"] = syrup_to_grain_tph
        
        a1_mol_to_grain_tph = pan_results['tons_brix_a1_molasses_for_grain_strikes'] * 100 / pan_data['a1_molasses_percent_brix']
        display_data["Grain Input: A1 Molasses (Tons/hr)"] = a1_mol_to_grain_tph
        
        b_mol_to_grain_tph = pan_results['tons_brix_b_molasses_for_grain_strikes'] * 100 / pan_data['b_molasses_percent_brix']
        display_data["Grain Input: B Molasses (Tons/hr)"] = b_mol_to_grain_tph
        display_data["Grain Water Evaporated (Tons/hr)"] = pan_results['tons_water_evap_grain']
        display_data["Grain Exhaust Steam Required (Tons/hr)"] = pan_results['tons_exhaust_steam_grain']
        display_data["Grain V1 Steam Required (Tons/hr)"] = pan_results['tons_v1_steam_grain']
        display_data["Grain V2 Steam Required (Tons/hr)"] = pan_results['tons_v2_steam_grain']

        # 6. C Station
        display_data["--- C STATION ---"] = ""
        display_data["C Massecuite (Tons/hr)"] = pan_results['tons_c_massecuite_per_hour']
        display_data["C Massecuite Brix"] = pan_data['c_massecuite_percent_brix']
        display_data["C Massecuite Purity"] = pan_results['c_massecuite_purity']
        
        # Inputs
        display_data["C Input: Grain Massecuite (Tons/hr)"] = pan_results['tons_grain_massecuite_per_hour']
        
        b_mol_to_c_tph = pan_results['tons_b_molasses_for_c_strikes'] * 100 / pan_data['b_molasses_percent_brix']
        display_data["C Input: B Molasses (Tons/hr)"] = b_mol_to_c_tph
        
        # Outputs
        display_data["Output: C Magma (Tons/hr)"] = pan_results['tons_c_magma_per_hour']
        display_data["C Magma Purity"] = pan_data['c_magma_purity']
        display_data["Output: C Molasses (Tons/hr)"] = pan_results['tons_c_molasses_per_hour']
        display_data["C Molasses Purity"] = pan_results['c_molasses_purity']
        display_data["C Water Evaporated (Tons/hr)"] = pan_results['tons_water_evap_c']
        display_data["C Exhaust Steam Required (Tons/hr)"] = pan_results['tons_exhaust_steam_c']
        display_data["C V1 Steam Required (Tons/hr)"] = pan_results['tons_v1_steam_c']
        display_data["C V2 Steam Required (Tons/hr)"] = pan_results['tons_v2_steam_c']

        show_results_gui(display_data, "Pan Balance Results")

    except ZeroDivisionError:
        show_error_gui(
            "A calculation error (division by zero) occurred. "
            "This often happens when purities are not balanced, leading to non-physical results (e.g., molasses purity >= massecuite purity). "
            "Please review your inputs before trying again.",
            "Pan Balance Calculation Error"
        )
        continue
        
    # 4. Continue or Exit
    answer = get_action_gui("Pan Data Complete")
    if answer == 'quit':
        break

if answer == 'quit':
    sys.exit()

# Final Summary
final_summary = {}
# Use try-except to safely check for and add results from each section
try:
    final_summary.update(mill_results)
except NameError:
    pass  # mill_results not defined, so skip
try:
    final_summary.update(clarifier_results)
except NameError:
    pass  # clarifier_results not defined, so skip
try:
    final_summary.update(evaporation_results)
except NameError:
    pass  # evaporation_results not defined, so skip
try:
    final_summary.update(pan_results)
except NameError:
    pass  # pan_results not defined, so skip

if final_summary:
    show_results_gui(final_summary, "Final Material Summary")

# Now moving onto the energy balance section
# We will start with steam available from the bagasse, we need working steam pressure from user

# user inputs here, convert to gui later...

live_steam_main_psig = 175 # psig
live_steam_deg_sh = 0 # degrees superheat in oF
print("Energy balance uses enthalpy of main steam")
live_steam_mills_psig = 170 # psig
live_steam_knives_psig = 165 # psig
live_steam_other_turbines_psig = 170 # psig, ID fans, FD fans, pumps, ect...

exhaust_steam_knives_psig = 16
exhaust_steam_mills_psig = 16
exhaust_steam_other_turbines_psig = 16
exhaust_steam_evaporators_psig = 14
exhaust_steam_pans_psig = 14

# now convert to absolute pressure
live_steam_main_psia = live_steam_main_psig + 14.696
live_steam_mills_psia = live_steam_mills_psig + 14.696
live_steam_knives_psia = live_steam_knives_psig + 14.696
live_steam_other_turbines_psia = live_steam_other_turbines_psig + 14.696
exhaust_steam_knives_psia = exhaust_steam_knives_psig + 14.696
exhaust_steam_mills_psia = exhaust_steam_mills_psig + 14.696
exhaust_steam_other_turbines_psia = exhaust_steam_other_turbines_psig + 14.696
exhaust_steam_evaporators_psia = exhaust_steam_evaporators_psig + 14.696
exhaust_steam_pans_psia = exhaust_steam_pans_psig + 14.696

# now we need steam availble from bagasse using Birkett's formula
live_steam_main = SteamStream('live_steam_main', 'ls_001', 0, live_steam_main_psia, live_steam_deg_sh)
ghv_bagasse = (
    .4299 
    * (19605 
        - 196.05 * mill_data['bagasse_percent_moisture'] 
        - 196.05 * mill_data['bagasse_percent_ash']
        - 31.14 * mill_results['bagasse_percent_brix'])
) # gross heating value bagasse in btu
avg_boiler_efficiency = 65 # user input, don't forget
btu_available_for_steam = ghv_bagasse * avg_boiler_efficiency / 100 * mill_results['tons_bagasse_per_hour'] * 2000
lbs_steam_available = btu_available_for_steam / live_steam_main.enthalpy
print(f"ghv bagasse {ghv_bagasse:,.2f}")
print(f"avg boiler efficiency {avg_boiler_efficiency:,.2f}")
print(f"btu available from bagasse {btu_available_for_steam:,.2f}")
print(f"live steam enthalpy {live_steam_main.enthalpy:,.2f}")

print(f"lbs steam availble {lbs_steam_available:,.2f}")

