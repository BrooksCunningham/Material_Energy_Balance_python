import dearpygui.dearpygui as dpg
import sys
from io import StringIO
import json
from datetime import datetime
import os
import pandas as pd
import math
from stream_and_unit_classes import SteamStream, Evaporator, SugarStream, SteamTurbine, initial_balance, calculate_bpe1, calculate_bpe2
from iapws import IAPWS97

# --- Constants & Helpers ---

STEAM_SOURCES = ["Exhaust", "Pre-Evap"]
for s in range(1, 5):
    for v in range(1, 4):
        STEAM_SOURCES.append(f"S{s} V{v}")

def crystal_yield(massecuite_purity, use_birkett=False, slope=0, intercept=0):
    if not use_birkett:
        m = float(slope)
        y_intercept = float(intercept)
    else:
        m = 0.7609
        y_intercept = -11.693
    return m * massecuite_purity + y_intercept

def get_molasses_purity(cy, p_ma):
    return (p_ma - cy) / (1 - cy / 100)

def sjm_mid_flow_given(s, j, m, j_tph):
    if s == m: return 0, j_tph # Avoid div by zero
    s_tph = (j - m) / (s - m) * j_tph
    m_tph = j_tph - s_tph
    return s_tph, m_tph

# --- Main Calculation Logic ---

def run_full_balance(inputs, csv_path=None):
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    try:
        # ==========================================
        # 1. MILL BALANCE
        # ==========================================
        print("="*80)
        print("MILL & CLARIFIER BALANCE")
        print("="*80)
        
        mill_res = {}
        mill_res['hours_lost'] = inputs["lost_time_percent"] / 100 * 24
        mill_res['hours_available'] = 24 - mill_res['hours_lost']
        mill_res['tons_cane_per_hour'] = inputs["grinding_rate_tons_day"] / mill_res['hours_available']
        
        mill_res['cane_tons_pol_per_hour'] = (inputs["cane_percent_pol"] / 100) * mill_res['tons_cane_per_hour']
        mill_res['cane_tons_fiber_per_hour'] = (inputs["cane_percent_fiber"] / 100) * mill_res['tons_cane_per_hour']
        
        mill_res['imbibition_water_tons_per_hour'] = (inputs["imbibition_water_percent"] / 100) * mill_res['tons_cane_per_hour']
        mill_res['filter_cake_tons_per_hour'] = (inputs["filter_cake_percent"] / 100) * mill_res['tons_cane_per_hour']
        mill_res['filter_cake_tons_pol_per_hour'] = (mill_res['filter_cake_tons_per_hour'] * inputs["filter_cake_pol"] / 100)
        
        mill_res['bagasse_percent_brix'] = inputs["bagasse_percent_pol"] * 100 / inputs["last_roll_purity"]
        mill_res['bagasse_percent_fiber'] = 100 - mill_res['bagasse_percent_brix'] - inputs["bagasse_percent_moisture"]
        
        mill_res['bagasse_tons_fiber_per_hour'] = mill_res['cane_tons_fiber_per_hour']
        mill_res['tons_bagasse_per_hour'] = mill_res['bagasse_tons_fiber_per_hour'] * 100 / mill_res['bagasse_percent_fiber']
        mill_res['bagasse_tons_pol_per_hour'] = (inputs["bagasse_percent_pol"] / 100) * mill_res['tons_bagasse_per_hour']
        
        mill_res['tons_mixed_juice_per_hour'] = (mill_res['tons_cane_per_hour'] + 
                                                mill_res['imbibition_water_tons_per_hour'] - 
                                                mill_res['tons_bagasse_per_hour'])
        
        # Calculate MJ Brix/Pol
        mill_res['mixed_juice_tons_pol_per_hour'] = mill_res['cane_tons_pol_per_hour'] - mill_res['bagasse_tons_pol_per_hour']
        mill_res['mixed_juice_percent_pol'] = mill_res['mixed_juice_tons_pol_per_hour'] / mill_res['tons_mixed_juice_per_hour'] * 100
        mill_res['mixed_juice_percent_brix'] = mill_res['mixed_juice_percent_pol'] / (inputs["mixed_juice_purity"] / 100)
        mill_res['mixed_juice_tons_brix_per_hour'] = mill_res['tons_mixed_juice_per_hour'] * mill_res['mixed_juice_percent_brix'] / 100

        mill_summary = pd.DataFrame([
            {'Stream': 'Cane', 'Flow (TPH)': mill_res['tons_cane_per_hour'], 'Pol %': inputs["cane_percent_pol"], 'Fiber %': inputs["cane_percent_fiber"], 'Moisture %': 100 - inputs["cane_percent_pol"]/0.85 - inputs["cane_percent_fiber"], 
             'Tons Pol': mill_res['cane_tons_pol_per_hour'], 'Tons Fiber': mill_res['cane_tons_fiber_per_hour'], 'Tons Brix': mill_res['tons_cane_per_hour'] * (inputs["cane_percent_pol"]/0.85)/100},
            {'Stream': 'Imbibition', 'Flow (TPH)': mill_res['imbibition_water_tons_per_hour'], 'Pol %': 0, 'Fiber %': 0, 'Moisture %': 100, 'Tons Pol': 0, 'Tons Fiber': 0, 'Tons Brix': 0},
            {'Stream': 'Mixed Juice', 'Flow (TPH)': mill_res['tons_mixed_juice_per_hour'], 'Pol %': mill_res['mixed_juice_percent_pol'], 'Fiber %': 0, 'Moisture %': 100 - mill_res['mixed_juice_percent_brix'],
             'Tons Pol': mill_res['mixed_juice_tons_pol_per_hour'], 'Tons Fiber': 0, 'Tons Brix': mill_res['mixed_juice_tons_brix_per_hour']},
            {'Stream': 'Bagasse', 'Flow (TPH)': mill_res['tons_bagasse_per_hour'], 'Pol %': inputs["bagasse_percent_pol"], 'Fiber %': mill_res['bagasse_percent_fiber'], 'Moisture %': inputs["bagasse_percent_moisture"],
             'Tons Pol': mill_res['bagasse_tons_pol_per_hour'], 'Tons Fiber': mill_res['bagasse_tons_fiber_per_hour'], 'Tons Brix': mill_res['tons_bagasse_per_hour'] * mill_res['bagasse_percent_brix'] / 100},
            {'Stream': 'Filter Cake', 'Flow (TPH)': mill_res['filter_cake_tons_per_hour'], 'Pol %': inputs["filter_cake_pol"], 'Fiber %': 0, 'Moisture %': 75,
             'Tons Pol': mill_res['filter_cake_tons_pol_per_hour'], 'Tons Fiber': 0, 'Tons Brix': mill_res['filter_cake_tons_pol_per_hour'] / 0.85}
        ])
        print(mill_summary.to_string(index=False, float_format=lambda x: "{:,.2f}".format(x)))
        print("-" * 80)

        # ==========================================
        # 2. CLARIFIER BALANCE
        # ==========================================
        clar_res = {}
        clar_res['tons_milk_of_lime_per_hour'] = (inputs["milk_of_lime_flow_rate_gpm"] * 9 * 60) / 2000
        clar_res['tons_flocculant_per_hour'] = (inputs["flocculant_flow_rate_gpm"] * 8.3 * 60) / 2000
        clar_res['filter_wash_water_tons_per_hour'] = (inputs["mud_filter_wash_water_percent_cane"] / 100) * mill_res['tons_cane_per_hour']
        
        # Flow entering heaters (MJ + Filtrate + Additives)
        # Note: Filtrate is recycled, so we calculate the combined stream
        clar_res['mixed_juice_with_filtrate_flow_rate_tons_hr'] = (
            mill_res['tons_mixed_juice_per_hour']
            + clar_res['filter_wash_water_tons_per_hour']
            + clar_res['tons_milk_of_lime_per_hour']
            + clar_res['tons_flocculant_per_hour']
        )

        # Determine Flash Temp from Heater Settings
        # If secondary heaters are on, use sec_out_temp, else prim_out_temp
        heater_out_temp = inputs['sec_out_temp'] if inputs['sec_htrs_on'] else inputs['prim_out_temp']
        
        clar_res['tons_water_in_mixed_juice_flashed'] = (
            0.92 * clar_res['mixed_juice_with_filtrate_flow_rate_tons_hr']
            * (heater_out_temp - 212)
            / 970
        )
        if clar_res['tons_water_in_mixed_juice_flashed'] < 0: clar_res['tons_water_in_mixed_juice_flashed'] = 0

        clar_res['clarified_juice_flow_rate_tons_hr'] = (
            clar_res['mixed_juice_with_filtrate_flow_rate_tons_hr']
            - mill_res['filter_cake_tons_per_hour']
            - clar_res['tons_water_in_mixed_juice_flashed']
        )
        
        # Pol/Brix Tracking
        clar_res['clarified_juice_tons_pol_per_hour'] = mill_res['mixed_juice_tons_pol_per_hour'] - mill_res['filter_cake_tons_pol_per_hour']
        clar_res['clarified_juice_tons_brix_per_hour'] = clar_res['clarified_juice_tons_pol_per_hour'] * 100 / inputs["clarified_juice_purity"]
        clar_res['clarified_juice_percent_brix'] = clar_res['clarified_juice_tons_brix_per_hour'] / clar_res['clarified_juice_flow_rate_tons_hr'] * 100

        # MJ + Filtrate Brix approx (diluted by filtrate/wash)
        mj_filt_brix_est = (mill_res['tons_mixed_juice_per_hour'] * mill_res['mixed_juice_percent_brix']) / clar_res['mixed_juice_with_filtrate_flow_rate_tons_hr']

        clar_summary = pd.DataFrame([
            {'Stream': 'MJ + Filtrate', 'Flow (TPH)': clar_res['mixed_juice_with_filtrate_flow_rate_tons_hr'], 'Temp (F)': inputs['mj_temp'], 'Brix': mj_filt_brix_est, 'Purity': inputs['mixed_juice_purity'], 'Tons Brix': clar_res['mixed_juice_with_filtrate_flow_rate_tons_hr']*mj_filt_brix_est/100, 'Tons Pol': clar_res['mixed_juice_with_filtrate_flow_rate_tons_hr']*mj_filt_brix_est/100*inputs['mixed_juice_purity']/100},
            {'Stream': 'Flash Steam', 'Flow (TPH)': clar_res['tons_water_in_mixed_juice_flashed'], 'Temp (F)': 212.0, 'Brix': 0.0, 'Purity': 0.0, 'Tons Brix': 0, 'Tons Pol': 0},
            {'Stream': 'Clarified Juice', 'Flow (TPH)': clar_res['clarified_juice_flow_rate_tons_hr'], 'Temp (F)': 212.0, 'Brix': clar_res['clarified_juice_percent_brix'], 'Purity': inputs["clarified_juice_purity"], 'Tons Brix': clar_res['clarified_juice_tons_brix_per_hour'], 'Tons Pol': clar_res['clarified_juice_tons_pol_per_hour']}
        ])
        print(clar_summary.to_string(index=False, float_format=lambda x: "{:,.2f}".format(x)))


        # ==========================================
        # 3. EVAPORATION MASS BALANCE
        # ==========================================
        evap_res = {}
        evap_res['tons_syrup_per_hour'] = (
            clar_res['clarified_juice_flow_rate_tons_hr']
            * clar_res['clarified_juice_percent_brix']
            / inputs["syrup_brix"]
        )
        evap_res['tons_brix_in_syrup_per_hour'] = evap_res['tons_syrup_per_hour'] * inputs["syrup_brix"] / 100

        # ==========================================
        # 4. PAN MATERIAL BALANCE
        # ==========================================
        print("\n" + "="*80)
        print("PAN MATERIAL BALANCE")
        print("="*80)
        
        pan_res = {}
        pan_res['tons_brix_syrup_and_remelt_per_hour'] = evap_res['tons_brix_in_syrup_per_hour'] # Initial
        pan_res['syrup_purity'] = inputs['clarified_juice_purity']
        pan_res['raw_sugar_purity'] = inputs['raw_sugar_pol'] / inputs['raw_sugar_brix'] * 100
        
        # Initialize loop variables
        pan_res['b_magma_tons_solids_per_hour'] = 0
        pan_res['c_magma_tons_solids_per_hour'] = 0
        pan_res['a1_molasses_tons_solids_per_hour'] = 0
        pan_res['a2_molasses_tons_solids_per_hour'] = 0
        pan_res['b_molasses_tons_solids_per_hour'] = 0
        
        for _ in range(100): # Convergence loop
            # --- A1 ---
            pct_syrup_a1 = 100 - inputs['syrup_percent_to_c_grain_strikes'] - inputs['syrup_percent_to_a2_strikes']
            ts_syrup_a1 = pan_res['tons_brix_syrup_and_remelt_per_hour'] * pct_syrup_a1 / 100
            ts_b_mag_a1 = inputs['b_magma_percent_to_a1_strikes'] * pan_res['b_magma_tons_solids_per_hour'] / 100
            
            ts_a1_mas = ts_syrup_a1 + ts_b_mag_a1
            purity_a1_mas = (ts_syrup_a1 * pan_res['syrup_purity'] + ts_b_mag_a1 * inputs['b_magma_purity']) / ts_a1_mas
            
            cy_a1 = crystal_yield(purity_a1_mas, inputs['use_birkett'], inputs['cy_slope'], inputs['cy_intercept'])
            pur_a1_mol = get_molasses_purity(cy_a1, purity_a1_mas)
            
            ts_a1_sug, ts_a1_mol = sjm_mid_flow_given(pan_res['raw_sugar_purity'], purity_a1_mas, pur_a1_mol, ts_a1_mas)
            pan_res['a1_molasses_tons_solids_per_hour'] = ts_a1_mol

            # --- A2 ---
            ts_a1_mol_a2 = inputs['a1_molasses_percent_to_a2_strikes'] * ts_a1_mol / 100
            ts_syrup_a2 = pan_res['tons_brix_syrup_and_remelt_per_hour'] * inputs['syrup_percent_to_a2_strikes'] / 100
            ts_b_mag_a2 = inputs['b_magma_percent_to_a2_strikes'] * pan_res['b_magma_tons_solids_per_hour'] / 100
            
            ts_a2_mas = ts_syrup_a2 + ts_b_mag_a2 + ts_a1_mol_a2
            purity_a2_mas = (ts_syrup_a2 * pan_res['syrup_purity'] + ts_b_mag_a2 * inputs['b_magma_purity'] + ts_a1_mol_a2 * pur_a1_mol) / ts_a2_mas
            
            cy_a2 = crystal_yield(purity_a2_mas, inputs['use_birkett'], inputs['cy_slope'], inputs['cy_intercept'])
            pur_a2_mol = get_molasses_purity(cy_a2, purity_a2_mas)
            
            ts_a2_sug, ts_a2_mol = sjm_mid_flow_given(pan_res['raw_sugar_purity'], purity_a2_mas, pur_a2_mol, ts_a2_mas)
            pan_res['a2_molasses_tons_solids_per_hour'] = ts_a2_mol

            # --- B ---
            ts_a1_mol_grain = inputs['a1_molasses_percent_to_c_grain_strikes'] * ts_a1_mol / 100
            ts_a1_mol_b = ts_a1_mol - ts_a1_mol_a2 - ts_a1_mol_grain
            ts_a2_mol_b = ts_a2_mol
            ts_c_mag_b = inputs['c_magma_percent_to_b_strikes'] * pan_res['c_magma_tons_solids_per_hour'] / 100
            
            ts_b_mas = ts_a1_mol_b + ts_a2_mol_b + ts_c_mag_b
            purity_b_mas = (ts_a1_mol_b * pur_a1_mol + ts_a2_mol_b * pur_a2_mol + ts_c_mag_b * inputs['c_magma_purity']) / ts_b_mas
            
            cy_b = crystal_yield(purity_b_mas, inputs['use_birkett'], inputs['cy_slope'], inputs['cy_intercept'])
            pur_b_mol = get_molasses_purity(cy_b, purity_b_mas)
            
            ts_b_mag, ts_b_mol = sjm_mid_flow_given(inputs['b_magma_purity'], purity_b_mas, pur_b_mol, ts_b_mas)
            pan_res['b_magma_tons_solids_per_hour'] = ts_b_mag
            pan_res['b_molasses_tons_solids_per_hour'] = ts_b_mol

            # --- Grain ---
            ts_syrup_gr = inputs['syrup_percent_to_c_grain_strikes'] * pan_res['tons_brix_syrup_and_remelt_per_hour'] / 100
            ts_b_mol_gr = inputs['b_molasses_percent_to_c_grain_strikes'] * ts_b_mol / 100
            
            ts_gr_mas = ts_a1_mol_grain + ts_b_mol_gr + ts_syrup_gr
            purity_gr_mas = (ts_a1_mol_grain * pur_a1_mol + ts_b_mol_gr * pur_b_mol + ts_syrup_gr * pan_res['syrup_purity']) / ts_gr_mas

            # --- C ---
            ts_b_mol_c = (100 - inputs['b_molasses_percent_to_c_grain_strikes']) * ts_b_mol / 100
            ts_c_mas = ts_b_mol_c + ts_gr_mas
            purity_c_mas = (ts_b_mol_c * pur_b_mol + ts_gr_mas * purity_gr_mas) / ts_c_mas
            
            cy_c = crystal_yield(purity_c_mas, inputs['use_birkett'], inputs['cy_slope'], inputs['cy_intercept'])
            pur_c_mol = get_molasses_purity(cy_c, purity_c_mas)
            
            ts_c_mag, ts_c_mol = sjm_mid_flow_given(inputs['c_magma_purity'], purity_c_mas, pur_c_mol, ts_c_mas)
            pan_res['c_magma_tons_solids_per_hour'] = ts_c_mag

            # --- Remelt & Recalc Syrup ---
            pct_b_remelt = 100 - inputs['b_magma_percent_to_a1_strikes'] - inputs['b_magma_percent_to_a2_strikes']
            ts_b_remelt = pct_b_remelt / 100 * ts_b_mag
            
            pct_c_remelt = 100 - inputs['c_magma_percent_to_b_strikes']
            ts_c_remelt = pct_c_remelt / 100 * ts_c_mag
            
            pan_res['tons_brix_syrup_and_remelt_per_hour'] = evap_res['tons_brix_in_syrup_per_hour'] + ts_b_remelt + ts_c_remelt
            pan_res['syrup_purity'] = (evap_res['tons_brix_in_syrup_per_hour'] * inputs['clarified_juice_purity'] + 
                                       ts_b_remelt * inputs['b_magma_purity'] + 
                                       ts_c_remelt * inputs['c_magma_purity']) / pan_res['tons_brix_syrup_and_remelt_per_hour']
            
            ts_sugar = ts_a1_sug + ts_a2_sug

        # --- Calculate Steam Demands (TPH) ---
        # A1
        tph_a1_mas = ts_a1_mas * 100 / inputs['a1_massecuite_percent_brix']
        tph_syrup_a1 = ts_syrup_a1 * 100 / inputs['syrup_brix']
        tph_b_mag_a1 = ts_b_mag_a1 * 100 / inputs['b_magma_percent_brix']
        evap_a1 = tph_syrup_a1 + tph_b_mag_a1 - tph_a1_mas
        steam_a1 = evap_a1 * inputs['a1_massecuite_steam_factor']
        
        # A2
        tph_a2_mas = ts_a2_mas * 100 / inputs['a2_massecuite_percent_brix']
        tph_syrup_a2 = ts_syrup_a2 * 100 / inputs['syrup_brix']
        tph_b_mag_a2 = ts_b_mag_a2 * 100 / inputs['b_magma_percent_brix']
        tph_a1_mol_a2 = ts_a1_mol_a2 * 100 / inputs['a1_molasses_percent_brix']
        evap_a2 = tph_syrup_a2 + tph_b_mag_a2 + tph_a1_mol_a2 - tph_a2_mas
        steam_a2 = evap_a2 * inputs['a2_massecuite_steam_factor']
        
        # B
        tph_b_mas = ts_b_mas * 100 / inputs['b_massecuite_percent_brix']
        tph_a1_mol_b = ts_a1_mol_b * 100 / inputs['a1_molasses_percent_brix']
        tph_a2_mol_b = ts_a2_mol_b * 100 / inputs['a2_molasses_percent_brix']
        tph_c_mag_b = ts_c_mag_b * 100 / inputs['c_magma_percent_brix']
        evap_b = tph_a1_mol_b + tph_a2_mol_b + tph_c_mag_b - tph_b_mas
        steam_b = evap_b * inputs['b_massecuite_steam_factor']
        
        # Grain
        tph_gr_mas = ts_gr_mas * 100 / inputs['grain_massecuite_percent_brix']
        tph_syrup_gr = ts_syrup_gr * 100 / inputs['syrup_brix']
        tph_a1_mol_gr = ts_a1_mol_grain * 100 / inputs['a1_molasses_percent_brix']
        tph_b_mol_gr = ts_b_mol_gr * 100 / inputs['b_molasses_percent_brix']
        evap_gr = tph_syrup_gr + tph_a1_mol_gr + tph_b_mol_gr - tph_gr_mas
        steam_gr = evap_gr * inputs['grain_massecuite_steam_factor']
        
        # C
        tph_c_mas = ts_c_mas * 100 / inputs['c_massecuite_percent_brix']
        tph_b_mol_c = ts_b_mol_c * 100 / inputs['b_molasses_percent_brix']
        evap_c = tph_gr_mas + tph_b_mol_c - tph_c_mas
        steam_c = evap_c * inputs['c_massecuite_steam_factor']

        # Store calculated steam demands (Base Exhaust Equivalent)
        pan_steam_demands = {
            'A1': steam_a1,
            'A2': steam_a2,
            'B': steam_b,
            'C': steam_c,
            'Grain': steam_gr
        }
        
        # Helper for summary row
        def get_row(name, ts, brix, purity, temp=150):
            if brix <= 0: return {'Stream': name, 'TPH': 0.0, 'Brix': 0.0, 'Purity': 0.0, 'Tons Brix': 0.0, 'Tons Pol': 0.0, 'CuFt/Hr': 0.0}
            tph = ts * 100 / brix
            s = SugarStream('temp', 'tag', tph, brix, purity, temp)
            return {'Stream': name, 'TPH': tph, 'Brix': brix, 'Purity': purity, 'Tons Brix': ts, 'Tons Pol': ts*purity/100, 'CuFt/Hr': s.vol_cuft_hr}

        summary_rows = []
        summary_rows.append(get_row('Syrup', evap_res['tons_brix_in_syrup_per_hour'], inputs['syrup_brix'], inputs['clarified_juice_purity']))
        summary_rows.append(get_row('A1 Massecuite', ts_a1_mas, inputs['a1_massecuite_percent_brix'], purity_a1_mas))
        summary_rows.append(get_row('A1 Molasses', ts_a1_mol, inputs['a1_molasses_percent_brix'], pur_a1_mol))
        summary_rows.append(get_row('A2 Massecuite', ts_a2_mas, inputs['a2_massecuite_percent_brix'], purity_a2_mas))
        summary_rows.append(get_row('A2 Molasses', ts_a2_mol, inputs['a2_molasses_percent_brix'], pur_a2_mol))
        summary_rows.append(get_row('B Massecuite', ts_b_mas, inputs['b_massecuite_percent_brix'], purity_b_mas))
        summary_rows.append(get_row('B Molasses', ts_b_mol, inputs['b_molasses_percent_brix'], pur_b_mol))
        summary_rows.append(get_row('C Massecuite', ts_c_mas, inputs['c_massecuite_percent_brix'], purity_c_mas))
        summary_rows.append(get_row('Final Molasses', ts_c_mol, inputs['c_molasses_percent_brix'], pur_c_mol))
        summary_rows.append(get_row('Grain Massecuite', ts_gr_mas, inputs['grain_massecuite_percent_brix'], purity_gr_mas))
        summary_rows.append(get_row('B Magma', pan_res['b_magma_tons_solids_per_hour'], inputs['b_magma_percent_brix'], inputs['b_magma_purity']))
        summary_rows.append(get_row('C Magma', pan_res['c_magma_tons_solids_per_hour'], inputs['c_magma_percent_brix'], inputs['c_magma_purity']))
        summary_rows.append(get_row('B Remelt', ts_b_remelt, inputs['b_magma_percent_brix'], inputs['b_magma_purity']))
        summary_rows.append(get_row('C Remelt', ts_c_remelt, inputs['c_magma_percent_brix'], inputs['c_magma_purity']))
        summary_rows.append(get_row('Total Sugar', ts_sugar, inputs['raw_sugar_brix'], inputs['raw_sugar_pol']/inputs['raw_sugar_brix']*100))

        pan_mat_summary = pd.DataFrame(summary_rows)
        print(pan_mat_summary.to_string(index=False, float_format=lambda x: "{:,.2f}".format(x)))

        # ==========================================
        # 5. ENERGY BALANCE
        # ==========================================
        print("\n" + "="*80)
        print("ENERGY BALANCE")
        print("="*80)

        # --- Steam Generation ---
        live_steam_main_psia = inputs['live_steam_main_psig'] + 14.696
        exhaust_steam_evaporators_psia = inputs['exhaust_steam_evaporators_psig'] + 14.696
        
        live_steam_main = SteamStream('live_steam_main', 'ls_001', 0, live_steam_main_psia, inputs['live_steam_deg_sh'])
        
        # Bagasse GHV
        ghv_bagasse = (.4299 * (19605 - 196.05 * inputs['bagasse_percent_moisture'] - 196.05 * inputs['bagasse_percent_ash'] - 31.14 * mill_res['bagasse_percent_brix']))
        btu_available = ghv_bagasse * 65 / 100 * mill_res['tons_bagasse_per_hour'] * 2000 # 65% eff hardcoded for now
        
        # BFW
        bfw_temp = inputs['boiler_feed_water_temp']
        bfw_k = (bfw_temp - 32) * 5/9 + 273.15
        bfw = IAPWS97(T=bfw_k, x=0)
        bfw_h = bfw.h * 0.429923
        
        heat_to_steam = live_steam_main.enthalpy - bfw_h
        lbs_steam_avail = btu_available / heat_to_steam
        
        # Steam Losses
        steam_loss_tph = (lbs_steam_avail / 2000) * inputs['steam_loss_percent'] / 100
        net_steam_avail_tph = (lbs_steam_avail / 2000) - steam_loss_tph
        
        print("BOILER SUMMARY")
        print(f"Bagasse Moisture:           {inputs['bagasse_percent_moisture']:.2f} %")
        print(f"Bagasse Ash:                {inputs['bagasse_percent_ash']:.2f} %")
        print(f"Bagasse Brix:               {mill_res['bagasse_percent_brix']:.2f} %")
        print(f"GHV Bagasse:                {ghv_bagasse:.0f} BTU/lb")
        print(f"Boiler Efficiency:          65.0 %")
        print(f"Live Steam Pressure:        {live_steam_main_psia-14.696:.0f} psig")
        print(f"Live Steam Temp:            {live_steam_main.temp:.1f} F")
        print(f"BFW Temp:                   {bfw_temp:.1f} F")
        print("-" * 40)
        print(f"Gross Steam Gen: {lbs_steam_avail:,.0f} lb/hr ({lbs_steam_avail/2000:.2f} TPH)")
        print(f"Steam Losses ({inputs['steam_loss_percent']}%): {steam_loss_tph:.2f} TPH")
        print(f"Net Steam Avail: {net_steam_avail_tph:.2f} TPH")

        # --- Turbines ---
        # (Simplified aggregation of turbine inputs)
        # Calculate total steam demand and exhaust available
        # Using the logic from energy_balance_testing.py
        
        # Helper to calc turbine
        def calc_turbine(hp, eff, p_in, p_out, h_in, s_in):
            # Ideal
            p_out_mpa = p_out * 0.00689476
            s_ideal = IAPWS97(P=p_out_mpa, s=s_in)
            h_ideal = s_ideal.h * 0.429923
            d_h_ideal = h_in - h_ideal
            
            # Actual
            d_h_actual = d_h_ideal * eff
            ssr = 2544 / d_h_actual
            steam_req = hp * ssr
            
            h_out_actual = h_in - d_h_actual
            exh_qual = IAPWS97(P=p_out_mpa, h=h_out_actual/0.429923).x
            return steam_req, steam_req * exh_qual

        # Live Steam Props
        ls_mpa = live_steam_main_psia * 0.00689476
        ls_obj = IAPWS97(P=ls_mpa, x=1) if inputs['live_steam_deg_sh'] == 0 else IAPWS97(P=ls_mpa, T=(live_steam_main.temp-32)*5/9+273.15)
        h_in = ls_obj.h * 0.429923
        s_in = ls_obj.s
        
        # Dataframes for reporting
        turb_rows = []
        
        # Cane Prep
        for i in range(len(inputs['ck_trb_hp_tf'])):
            hp_load = inputs['ck_trb_hp_tf'][i] * mill_res['cane_tons_fiber_per_hour']
            if hp_load > 0:
                req, avail = calc_turbine(hp_load, inputs['ck_trb_eff'][i], live_steam_main_psia, 30.7, h_in, s_in) # 30.7 = 16psig
                turb_rows.append({
                    'Group': 'Cane Prep', 'ID': i+1, 'HP': hp_load, 'Eff': inputs['ck_trb_eff'][i],
                    'Steam (lb/hr)': req, 'Exhaust (lb/hr)': avail, 'SSR': req/hp_load
                })
        
        # Mills
        for i in range(len(inputs['mill_trb_hp_tf'])):
            hp_load = inputs['mill_trb_hp_tf'][i] * mill_res['cane_tons_fiber_per_hour']
            if hp_load > 0:
                req, avail = calc_turbine(hp_load, inputs['mill_trb_eff'][i], live_steam_main_psia, 30.7, h_in, s_in)
                turb_rows.append({
                    'Group': 'Mill', 'ID': i+1, 'HP': hp_load, 'Eff': inputs['mill_trb_eff'][i],
                    'Steam (lb/hr)': req, 'Exhaust (lb/hr)': avail, 'SSR': req/hp_load
                })
                
        # Other
        for i in range(len(inputs['other_trb_hp'])):
            hp_load = inputs['other_trb_hp'][i]
            if hp_load > 0:
                req, avail = calc_turbine(hp_load, inputs['other_trb_eff'][i], live_steam_main_psia, 30.7, h_in, s_in)
                name = inputs['other_trb_names'][i] if i < len(inputs['other_trb_names']) else f"Other {i+1}"
                turb_rows.append({
                    'Group': name, 'ID': i+1, 'HP': hp_load, 'Eff': inputs['other_trb_eff'][i],
                    'Steam (lb/hr)': req, 'Exhaust (lb/hr)': avail, 'SSR': req/hp_load
                })

        df_turb = pd.DataFrame(turb_rows)
        total_ls_demand = df_turb['Steam (lb/hr)'].sum()
        total_exh_avail = df_turb['Exhaust (lb/hr)'].sum()
        
        print("\nSTEAM TURBINE SUMMARY")
        print(df_turb.to_string(index=False, float_format=lambda x: "{:,.1f}".format(x)))
        print("-" * 80)
        print(f"Total Turbine Steam Demand: {total_ls_demand:,.0f} lb/hr")
        print(f"Total Turbine Exhaust Avail: {total_exh_avail:,.0f} lb/hr")

        # Steam Jets
        steam_jets_tph = inputs['steam_jets_lb_hr'] / 2000
        print(f"Steam Jets Demand: {steam_jets_tph:.2f} TPH")
        total_ls_demand += inputs['steam_jets_lb_hr']

        # --- Process Steam Demands ---
        
        steam_demands = {'exhaust': 0.0, 'pre': 0.0, 'sets': [[0.0]*3 for _ in range(4)]}
        
        # Track actual flows for bleed breakdown and condensate
        actual_steam_flows = {'heaters': [], 'pans': {}, 'cj': None}
        
        def add_demand(source, flow_tph):
            if source == 'Exhaust': steam_demands['exhaust'] += flow_tph
            elif source == 'Pre-Evap': steam_demands['pre'] += flow_tph
            elif source.startswith('S'):
                parts = source.split()
                s_idx = int(parts[0][1:]) - 1
                v_idx = int(parts[1][1:]) - 1
                if 0 <= s_idx < 4 and 0 <= v_idx < 3:
                    steam_demands['sets'][s_idx][v_idx] += flow_tph

        # Deaerator
        da_temp = inputs['deaerator_inlet_temp']
        da_k = (da_temp - 32) * 5/9 + 273.15
        da_h = IAPWS97(T=da_k, x=0).h * 0.429923
        
        exh_evap_obj = IAPWS97(P=exhaust_steam_evaporators_psia * 0.00689476, x=1)
        exh_hfg = 0.429923 * (exh_evap_obj.h - IAPWS97(P=exhaust_steam_evaporators_psia * 0.00689476, x=0).h)
        
        da_load = total_ls_demand * (bfw_h - da_h)
        da_steam = da_load / exh_hfg / 2000
        add_demand('Exhaust', da_steam)
        da_exhaust_demand_tph = da_steam

        # Heaters
        # Flow is mixed_juice_with_filtrate_flow_rate_tons_hr
        # MJ Temp is inputs['mj_temp']
        mj_flow = clar_res['mixed_juice_with_filtrate_flow_rate_tons_hr']
        mj_cp = 0.92 # Approx
        
        # Calculate MJ Brix for heater calc (approx)
        # Using mill_res['mixed_juice_percent_brix'] but diluted by filtrate
        mj_filt_brix = (mill_res['tons_mixed_juice_per_hour'] * mill_res['mixed_juice_percent_brix']) / mj_flow

        q_prim = 0
        q_sec = 0
        
        if inputs['heater_config'] == "Series":
            q_prim = mj_flow * 2000 * mj_cp * (inputs['prim_out_temp'] - inputs['mj_temp'])
            if inputs['sec_htrs_on']:
                q_sec = mj_flow * 2000 * mj_cp * (inputs['sec_out_temp'] - inputs['prim_out_temp'])
        else:
            split = inputs['parallel_split'] / 100
            q_prim = (mj_flow * split) * 2000 * mj_cp * (inputs['prim_out_temp'] - inputs['mj_temp'])
            if inputs['sec_htrs_on']:
                q_sec = (mj_flow * (1-split)) * 2000 * mj_cp * (inputs['prim_out_temp'] - inputs['mj_temp'])
        
        stm_prim = q_prim / exh_hfg / 2000
        stm_sec = q_sec / exh_hfg / 2000
        
        exh_for_prim = stm_prim if inputs['steam_for_prim'] == 'Exhaust' else 0
        exh_for_sec = stm_sec if (inputs['sec_htrs_on'] and inputs['steam_for_sec'] == 'Exhaust') else 0

        # Multipliers for V1/V2/V3 usage
        v1_mult = 0.98330
        v2_mult = 0.96906
        v3_mult = 0.95500
        
        def get_equiv_flow(base_flow, source):
            if source == 'Exhaust': return base_flow
            if 'V1' in source or 'Pre' in source: return base_flow * v1_mult
            if 'V2' in source: return base_flow * v2_mult
            if 'V3' in source: return base_flow * v3_mult
            return base_flow

        act_prim = get_equiv_flow(stm_prim, inputs['steam_for_prim'])
        add_demand(inputs['steam_for_prim'], act_prim)
        actual_steam_flows['heaters'].append({'Unit': 'Primary Heaters', 'Source': inputs['steam_for_prim'], 'Flow': act_prim})
        
        if inputs['sec_htrs_on']:
            act_sec = get_equiv_flow(stm_sec, inputs['steam_for_sec'])
            add_demand(inputs['steam_for_sec'], act_sec)
            actual_steam_flows['heaters'].append({'Unit': 'Secondary Heaters', 'Source': inputs['steam_for_sec'], 'Flow': act_sec})
            
        print("\nHEATER SUMMARY")
        htr_data = [
            {'Unit': 'Primary', 'Flow TPH': mj_flow if inputs['heater_config']=='Series' else mj_flow*split, 'Temp In': inputs['mj_temp'], 'Temp Out': inputs['prim_out_temp'], 'Source': inputs['steam_for_prim'], 'Steam TPH': stm_prim},
        ]
        if inputs['sec_htrs_on']:
            htr_data.append({'Unit': 'Secondary', 'Flow TPH': mj_flow if inputs['heater_config']=='Series' else mj_flow*(1-split), 'Temp In': inputs['prim_out_temp'] if inputs['heater_config']=='Series' else inputs['mj_temp'], 'Temp Out': inputs['sec_out_temp'] if inputs['heater_config']=='Series' else inputs['prim_out_temp'], 'Source': inputs['steam_for_sec'], 'Steam TPH': stm_sec})

        # CJ Heater
        exh_for_cj = 0
        if inputs['cj_htr_enable']:
            q_cj = clar_res['clarified_juice_flow_rate_tons_hr'] * 2000 * 0.92 * (inputs['cj_out_temp'] - inputs['cj_in_temp'])
            stm_cj = q_cj / exh_hfg / 2000
            act_cj = get_equiv_flow(stm_cj, inputs['cj_htr_steam'])
            add_demand(inputs['cj_htr_steam'], act_cj)
            actual_steam_flows['cj'] = {'Unit': 'CJ Heater', 'Source': inputs['cj_htr_steam'], 'Flow': act_cj}
            if inputs['cj_htr_steam'] == 'Exhaust': exh_for_cj = stm_cj
            htr_data.append({'Unit': 'CJ Heater', 'Flow TPH': clar_res['clarified_juice_flow_rate_tons_hr'], 'Temp In': inputs['cj_in_temp'], 'Temp Out': inputs['cj_out_temp'], 'Source': inputs['cj_htr_steam'], 'Steam TPH': stm_cj})

        print(pd.DataFrame(htr_data).to_string(index=False, float_format=lambda x: "{:,.2f}".format(x)))

        # Pans
        pan_exhaust_demand = 0
        pan_exh_breakdown = {}
        for station, source in inputs['pan_config'].items():
            base_flow = pan_steam_demands[station] # This is already TPH Exhaust Equivalent
            actual_flow = get_equiv_flow(base_flow, source)
            add_demand(source, actual_flow)
            actual_steam_flows['pans'][station] = {'Source': source, 'Flow': actual_flow}
            if source == 'Exhaust':
                pan_exhaust_demand += actual_flow
                pan_exh_breakdown[station] = actual_flow
            else:
                pan_exh_breakdown[station] = 0

        print("\nPAN STEAM SUMMARY")
        pan_stm_data = []
        for k, v in pan_steam_demands.items():
            src = inputs['pan_config'][k]
            pan_stm_data.append({'Station': k, 'Steam Demand (Exh Eq) TPH': v, 'Source': src, 'Actual Steam TPH': get_equiv_flow(v, src)})
        print(pd.DataFrame(pan_stm_data).to_string(index=False, float_format=lambda x: "{:,.2f}".format(x)))

        # Evaporators
        # Logic from energy_balance_testing.py adapted
        juice_to_mee = clar_res['clarified_juice_flow_rate_tons_hr']
        juice_brix = clar_res['clarified_juice_percent_brix']
        
        # Create Objects for Evap Logic
        mj_and_filt_obj = SugarStream('mj', 'tag', mj_flow, mj_filt_brix, 85, inputs['mj_temp'])
        exh_evaps_obj = IAPWS97(P=exhaust_steam_evaporators_psia * 0.00689476, x=1)
        
        # Pre-Evaporator Logic (Iterative)
        pre_evaps_input = inputs['pre_evaps']
        active_pre_evaps = [i for i, p in enumerate(pre_evaps_input) if p['enable']]
        total_pre_hs = sum(pre_evaps_input[i]['hs'] for i in active_pre_evaps)
        
        # Pre-Evap
        pre_evap_vap = steam_demands['pre']
        pre_evap_exh = 0
        pre_evap_cond_temp = 0
        pre_evap_results = []
        last_effect_vapors = [] # Store (flow_tph, pressure_psia) for injection water calc
        mee_feed_temp = inputs['cj_out_temp']
        
        if active_pre_evaps and pre_evap_vap > 0:
            # Iterative Solver for Pre-Evap
            v1_est_psia = 24
            exh_temp_f = (exh_evaps_obj.T - 273.15) * 9/5 + 32
            
            total_juice_in = juice_to_mee
            total_juice_out = total_juice_in - pre_evap_vap
            global_out_brix = (total_juice_in * juice_brix) / total_juice_out
            
            for _ in range(3):
                v1_est_sat = IAPWS97(P=v1_est_psia * 0.00689476, x=1)
                v1_est_hfg = 0.429923 * (v1_est_sat.h - IAPWS97(P=v1_est_psia * 0.00689476, x=0).h)
                v1_sat_temp_f = (v1_est_sat.T - 273.15) * 9/5 + 32
                
                u_avg = (100 - global_out_brix) * (exh_temp_f - 130) * v1_est_hfg / 20000
                if u_avg < 10: u_avg = 10
                
                pe_bpe_brix = calculate_bpe1(global_out_brix)
                pe_bpe_head = calculate_bpe2(2, global_out_brix, v1_sat_temp_f)
                pe_bpe = pe_bpe_brix + pe_bpe_head
                
                F_lb = total_juice_in * 2000
                V_lb = pre_evap_vap * 2000
                UA = u_avg * total_pre_hs
                
                numerator = UA*exh_temp_f - UA*pe_bpe - V_lb*v1_est_hfg - F_lb*mj_and_filt_obj.cp*(pe_bpe - mee_feed_temp)
                denominator = F_lb*mj_and_filt_obj.cp + UA
                v1_sat_temp_f = numerator / denominator
                
                try:
                    v1_sat_temp_k = (v1_sat_temp_f - 32) * 5/9 + 273.15
                    if v1_sat_temp_k > 273.15:
                        v1_new = IAPWS97(T=v1_sat_temp_k, x=1)
                        v1_est_psia = v1_new.P / 0.00689476
                except: pass
            
            pe_boil_temp = v1_sat_temp_f + pe_bpe
            total_heat_load = V_lb*v1_est_hfg + F_lb*mj_and_filt_obj.cp*(pe_boil_temp - mee_feed_temp)
            pre_evap_exh = (total_heat_load / exh_hfg) / 2000
            
            pre_evap_cond_temp = exh_temp_f # Condensate temp is steam temp
            add_demand('Exhaust', pre_evap_exh)
            juice_to_mee -= pre_evap_vap
            juice_brix = global_out_brix
            mee_feed_temp = pe_boil_temp
            
            for idx in active_pre_evaps:
                hs = pre_evaps_input[idx]['hs']
                ratio = hs / total_pre_hs
                pre_evap_results.append({
                    'Vessel': f"Pre-Evap {idx+1}", 'Juice In': total_juice_in*ratio, 'Juice Out': total_juice_out*ratio,
                    'Brix In': clar_res['clarified_juice_percent_brix'], 'Brix Out': global_out_brix, 'HS': hs,
                    'Temp In': inputs['cj_out_temp'], 'Temp Out': pe_boil_temp,
                    'Steam P': exhaust_steam_evaporators_psia, 'Steam TPH': pre_evap_exh*ratio, 'Vapor T': v1_sat_temp_f, 'U': u_avg,
                    'BPE Brix': pe_bpe_brix, 'BPE Head': pe_bpe_head, 'BPE Total': pe_bpe, 'Vapor P': v1_est_psia,
                    'Evap TPH': (total_juice_in - total_juice_out)*ratio
                })

        # MEE Sets
        sets_input = inputs['sets']
        active_sets = [i for i, s in enumerate(sets_input) if s['enable']]
        total_hs = sum(sum(sets_input[i]['hs']) for i in active_sets)
        
        # Initial Juice Distribution
        set_juice_split = {}
        for idx in active_sets:
            set_hs = sum(sets_input[idx]['hs'])
            set_juice_split[idx] = set_hs / total_hs
            
        mee_exh_total = 0
        sets_results = []
        condensate_streams = [] # List to store condensate info
        
        # Helper to get bleed breakdown for a specific vapor source (e.g. "S1 V1")
        def get_bleed_breakdown(vapor_name):
            bd = {}
            # Heaters
            for h in actual_steam_flows['heaters']:
                if h['Source'] == vapor_name:
                    bd[f"To {h['Unit']}"] = h['Flow']
            # CJ
            if actual_steam_flows['cj'] and actual_steam_flows['cj']['Source'] == vapor_name:
                bd["To CJ Heater"] = actual_steam_flows['cj']['Flow']
            # Pans
            for station, data in actual_steam_flows['pans'].items():
                if data['Source'] == vapor_name:
                    bd[f"To {station} Pan"] = data['Flow']
            return bd
        
        for idx in active_sets:
            s_data = sets_input[idx]
            j_in = juice_to_mee * set_juice_split[idx]
            bleeds = steam_demands['sets'][idx]
            
            # --- Iterative Solver (Ported from energy_balance_testing.py) ---
            
            data = initial_balance(
                num_effects=s_data['num_effects'], exh_press_psia=exhaust_steam_evaporators_psia,
                last_eff_psia=(29.92 - inputs['last_eff_vac']) * 0.491154,
                juice_in_tph=j_in, juice_brix=juice_brix, syrup_brix=inputs['syrup_brix'],
                v1_bleed=bleeds[0], v2_bleed=bleeds[1], v3_bleed=bleeds[2],
                effect_1_surface=s_data['hs'][0], effect_2_surface=s_data['hs'][1],
                effect_3_surface=s_data['hs'][2], effect_4_surface=s_data['hs'][3], effect_5_surface=s_data['hs'][4]
            )
            
            # Create Objects
            clear_juice = SugarStream('cj', 'tag', data['juice_in_tph'], data['juice_brix'], 88, mee_feed_temp, data['vapor_press_effect_1'], 2)
            exhaust_stm = SteamStream('exh', 'tag', data['exhaust_estim_tph'], data['exhaust_press_psia'], 0)
            effects = []
            concs = []
            for e in range(s_data['num_effects']):
                effects.append(Evaporator(f'E{e+1}', 'tag', s_data['hs'][e], data[f'vapor_press_effect_{e+1}'], 20000))
                concs.append(SugarStream(f'C{e+1}', 'tag', data[f'conc_{e+1}_mass_flow'], data[f'conc_{e+1}_brix'], 88, 225, data[f'vapor_press_effect_{e+1}'], 2))
            
            # Convergence Loop
            for _ in range(100): # Increased to 100 for better convergence
                steam_source = exhaust_stm
                set_u_ratios = []
                
                for e in range(s_data['num_effects']):
                    eff = effects[e]
                    conc = concs[e]
                    feed = clear_juice if e == 0 else concs[e-1]
                    
                    eff.heat_duty(steam_in_tph=steam_source.mass_flow_tph, steam_latent_heat=steam_source.latent_heat)
                    eff.heat_for_evaporation(feed.mass_flow_tph, feed.temp, conc.boil_temp_liq, feed.cp)
                    eff.tons_evaporated(conc.latent_heat)
                    eff.tons_conc_out(feed.mass_flow_tph)
                    
                    # Calculate U
                    current_steam_temp = exhaust_stm.sat_temp if e == 0 else concs[e-1].sat_temp
                    eff.u_calc(conc.boil_temp_liq, current_steam_temp)
                    
                    # Dessin U
                    eff.dessin_u(conc.brix, current_steam_temp, conc.latent_heat)
                    
                    # Ratio for Pressure Adjustment
                    if eff.dessin_coefficient > 0:
                        ratio = eff.heat_trans_coef / eff.dessin_coefficient
                    else: ratio = 1.0
                    set_u_ratios.append(max(0.1, ratio))

                    bleed = bleeds[e] if e < 3 else 0
                    eff.tons_vap_to_next_eff(bleed)
                    conc.evaporate(eff.conc_out_tph, eff.vapor_pressure)
                    
                    # Next effect steam source is this effect's vapor (after bleed)
                    steam_source = type('obj', (object,), {'mass_flow_tph': eff.vap_to_next_eff_tph, 'latent_heat': conc.latent_heat})

                # Adjust Exhaust to close mass balance
                final_conc = concs[-1]
                evap_calc = clear_juice.mass_flow_tph - final_conc.mass_flow_tph
                target_evap = clear_juice.mass_flow_tph - (clear_juice.mass_flow_tph * clear_juice.brix / inputs['syrup_brix'])
                diff = evap_calc - target_evap
                
                # If calculated evap is too low, we need more steam -> increase exhaust
                # diff = calc - target. If diff < 0, we need more.
                exhaust_stm.change_flow(exhaust_stm.mass_flow_tph - diff/5)
                if exhaust_stm.mass_flow_tph < 0.1: exhaust_stm.change_flow(0.1)
                
                # Adjust Pressures (Dessin Method)
                avg_u_ratio = sum(set_u_ratios) / len(set_u_ratios)
                for e in range(s_data['num_effects'] - 1):
                    new_p = effects[e].vapor_pressure * ((avg_u_ratio / set_u_ratios[e]) ** 0.1)
                    effects[e].adjust_pressure(max(0.5, new_p))

            # --- Collect Results for Display ---
            for e in range(s_data['num_effects']):
                eff = effects[e]
                conc = concs[e]
                feed = clear_juice if e == 0 else concs[e-1]
                
                # Determine Steam Source Info
                if e == 0:
                    stm_flow = exhaust_stm.mass_flow_tph
                    stm_temp = exhaust_stm.sat_temp
                    stm_src_name = "Exhaust"
                else:
                    stm_flow = effects[e-1].vap_to_next_eff_tph
                    stm_temp = concs[e-1].sat_temp
                    stm_src_name = f"S{idx+1} V{e}" # V1 enters E2
                
                # Bleed Breakdown
                vapor_name = f"S{idx+1} V{e+1}"
                bleed_bd = get_bleed_breakdown(vapor_name)
                
                # Add to Condensate List
                condensate_streams.append({
                    'Unit': f"Set {idx+1} E{e+1}",
                    'Source': stm_src_name,
                    'Flow': stm_flow,
                    'Temp': stm_temp
                })

                sets_results.append({
                    'Vessel': f"Set {idx+1} E{e+1}", 'Juice In': feed.mass_flow_tph, 'Juice Out': conc.mass_flow_tph,
                    'Brix In': feed.brix, 'Brix Out': conc.brix, 'HS': eff.heating_surface_sqft,
                    'Temp In': feed.temp, 'Temp Out': conc.boil_temp_liq,
                    'Steam P': effects[e-1].vapor_pressure if e>0 else exhaust_steam_evaporators_psia,
                    'Steam TPH': stm_flow,
                    'Vapor T': conc.sat_temp, 
                    'U Calc': eff.heat_trans_coef,
                    'U Dessin': eff.dessin_coefficient,
                    'U Ratio': eff.heat_trans_coef / eff.dessin_coefficient if eff.dessin_coefficient else 0,
                    'Total Bleed': eff.vapor_bleed,
                    'Bleed Breakdown': bleed_bd,
                    'BPE Brix': conc.bpe_brx, 'BPE Head': conc.bpe_head, 'BPE Total': conc.bpe_total, 'Vapor P': eff.vapor_pressure,
                    'Evap TPH': eff.tons_evap
                })
            
            mee_exh_total += exhaust_stm.mass_flow_tph
            add_demand('Exhaust', exhaust_stm.mass_flow_tph)
            
            # Store last effect vapor for injection water calc
            last_effect_vapors.append({'flow': effects[-1].tons_evap, 'p': effects[-1].vapor_pressure})

        # Print Evap Summary
        print("\nEVAPORATOR SUMMARY")
        all_evap_res = pre_evap_results + sets_results
        if all_evap_res:
            # Transpose Logic
            # Columns: Vessel Names
            # Rows: Properties
            
            vessels = [r['Vessel'] for r in all_evap_res]
            data_dict = {}
            
            # Define rows order
            keys_config = [
                ('HS', 'HS (ft²)'),
                ('Juice In', 'Juice In (TPH)'),
                ('Juice Out', 'Juice Out (TPH)'),
                ('Brix In', 'Brix In'),
                ('Brix Out', 'Brix Out'),
                ('Temp In', 'Temp In (°F)'),
                ('Temp Out', 'Temp Out (°F)'),
                ('Steam P', 'Steam P In'),
                ('Steam TPH', 'Steam In (TPH)'),
                ('Steam lb/hr', 'Steam In (lb/hr)'),
                ('Evap TPH', 'Evap (TPH)'),
                ('Evap lb/hr', 'Evap (lb/hr)'),
                ('Vapor P', 'Vapor P Out'),
                ('Vapor T', 'Vapor T (°F)'),
                ('BPE Brix', 'BPE Brix (°F)'),
                ('BPE Head', 'BPE Head (°F)'),
                ('BPE Total', 'BPE Total (°F)'),
                ('U Calc', 'U Calc'),
                ('U Dessin', 'U Dessin'),
                ('U Ratio', 'U Ratio'),
                ('Total Bleed', 'Total Bleed (TPH)')
            ]
            
            for k, label in keys_config:
                row_vals = []
                for r in all_evap_res:
                    val = r.get(k, 0)
                    if k == 'Steam lb/hr':
                        val = r.get('Steam TPH', 0) * 2000
                        val = f"{val:,.0f}"
                    elif k == 'Evap lb/hr':
                        val = r.get('Evap TPH', 0) * 2000
                        val = f"{val:,.0f}"
                    elif k in ['Steam P', 'Vapor P']:
                        val = f"{val-14.696:.1f} psig" if val>14.696 else f"{(14.696-val)*2.036:.1f} \"Hg"
                    elif isinstance(val, float):
                        val = f"{val:,.1f}"
                    row_vals.append(val)
                data_dict[label] = row_vals
            
            # Add Bleed Breakdown Rows dynamically
            # Collect all unique bleed destinations
            all_destinations = set()
            for r in all_evap_res:
                if 'Bleed Breakdown' in r:
                    all_destinations.update(r['Bleed Breakdown'].keys())
            
            for dest in sorted(all_destinations):
                row_vals = []
                for r in all_evap_res:
                    bd = r.get('Bleed Breakdown', {})
                    val = bd.get(dest, 0)
                    row_vals.append(f"{val:,.1f}" if val > 0 else "-")
                data_dict[dest] = row_vals

            df_transposed = pd.DataFrame(data_dict, index=vessels).T
            print(df_transposed.to_string())

        # Final Balance
        print("\n" + "="*80)
        print("EXHAUST STEAM BALANCE")
        print("="*80)
        
        def print_exh_row(label, tph):
            print(f"{label:<30} {tph:10.2f} TPH  ({tph*2000:12,.0f} lb/hr)")

        print_exh_row("MEE Exhaust Demand:", mee_exh_total)
        if pre_evap_exh > 0:
            print_exh_row("Pre-Evap Exhaust Demand:", pre_evap_exh)
        
        print("-" * 60)
        print_exh_row("Primary Heaters:", exh_for_prim)
        print_exh_row("Secondary Heaters:", exh_for_sec)
        print_exh_row("Clarified Juice Heater:", exh_for_cj)
        print("-" * 60)
        for station in ['A1', 'A2', 'B', 'C', 'Grain']:
            print_exh_row(f"{station} Pan Exhaust:", pan_exh_breakdown.get(station, 0))
        print("-" * 60)
        print_exh_row("Deaerator Exhaust Demand:", da_exhaust_demand_tph)
        print("-" * 60)
        print_exh_row("Total Exhaust Required:", steam_demands['exhaust'])
        print_exh_row("Total Exhaust Available:", total_exh_avail/2000)
        
        balance = (total_exh_avail/2000) - steam_demands['exhaust'] - steam_loss_tph
        if balance >= 0: print(f"SURPLUS: {balance:.2f} TPH")
        else: print(f"DEFICIT: {abs(balance):.2f} TPH")

        # ==========================================
        # 6. INJECTION WATER & CONDENSATE
        # ==========================================
        print("\n" + "="*80)
        print("CONDENSER & WATER BALANCE")
        print("="*80)
        
        # Injection Water
        inj_in = inputs['injection_water_temp_in']
        inj_out = inputs['injection_water_temp_out']
        dt_inj = inj_out - inj_in
        if dt_inj <= 0: dt_inj = 1 # Prevent div/0
        
        def calc_inj_water(vap_tph, vac_hg):
            if vap_tph <= 0: return 0
            p_psia = (29.92 - vac_hg) * 0.491154
            if p_psia <= 0: p_psia = 0.1
            sat = IAPWS97(P=p_psia*0.00689476, x=1)
            h_g = sat.h * 0.429923
            h_f = IAPWS97(P=p_psia*0.00689476, x=0).h * 0.429923
            h_fg = h_g - h_f
            # Water req = Q / (cp * dt)
            # Q = m * h_fg
            return (vap_tph * 2000 * h_fg) / (1.0 * dt_inj) / 2000 # TPH

        # Pan Injection
        pan_inj_total = 0
        print(f"{'Station':<20} {'Vapor (TPH)':<15} {'Vac (\"Hg)':<15} {'Inj Water (TPH)':<15} {'GPM':<15}")
        print("-" * 80)
        
        pan_vapors = [
            ('A1', evap_a1, inputs['pan_vac_a1']), ('A2', evap_a2, inputs['pan_vac_a2']),
            ('B', evap_b, inputs['pan_vac_b']), ('C', evap_c, inputs['pan_vac_c']),
            ('Grain', evap_gr, inputs['pan_vac_gr'])
        ]
        for name, vap, vac in pan_vapors:
            w = calc_inj_water(vap, vac)
            pan_inj_total += w
            print(f"{name:<20} {vap:<15.2f} {vac:<15.1f} {w:<15.2f} {w*2000/8.33/60:<15.0f}")
            
        # Evap Injection
        evap_inj_total = 0
        for i, eff in enumerate(last_effect_vapors):
            # Convert P to Vac
            vac = (14.696 - eff['p']) * 2.036
            w = calc_inj_water(eff['flow'], vac)
            evap_inj_total += w
            print(f"{'Evap Set '+str(i+1):<20} {eff['flow']:<15.2f} {vac:<15.1f} {w:<15.2f} {w*2000/8.33/60:<15.0f}")
            
        total_inj = pan_inj_total + evap_inj_total
        print("-" * 80)
        print(f"TOTAL INJECTION WATER: {total_inj:,.2f} TPH ({total_inj*2000/8.33/60:,.0f} GPM)")
        
        # ==========================================
        # 7. CONDENSATE BALANCE (DETAILED)
        # ==========================================
        print("\n" + "="*80)
        print("CONDENSATE AVAILABLE")
        print("="*80)
        
        # Collect all condensate streams
        # 1. Heaters
        for h in actual_steam_flows['heaters']:
            # Need temp of source. 
            # If Exhaust: exh_evaps_obj.T
            # If Vapors: Need to find that vapor's temp.
            # Approximation: If Exhaust -> Exh Temp. If Vx -> Approx Temp.
            # Better: Look up temp based on source name.
            # For now, using Exh Temp for Exhaust, and approximation for others if not easily linked.
            # Actually, we can assume saturation temp of the pressure.
            # Let's use a helper if possible, or just list what we have.
            # For simplicity in this view, I will use the Exh Temp for Exhaust, and 212 for others if unknown, 
            # but ideally we link to the Evap result.
            
            # Quick lookup for Vapor Temps from Evap Results
            # Map "S1 V1" -> Temp
            vap_temps = {}
            for r in sets_results:
                # r['Vessel'] is "Set 1 E1". Vapor is "S1 V1"
                parts = r['Vessel'].split() # ['Set', '1', 'E1']
                s_num = parts[1]
                e_num = parts[2][1:]
                vap_temps[f"S{s_num} V{e_num}"] = r['Vapor T']
            
            src = h['Source']
            temp = (exh_evaps_obj.T - 273.15)*9/5+32
            if src in vap_temps: temp = vap_temps[src]
            elif src == 'Pre-Evap': temp = pre_evap_results[0]['Vapor T'] if pre_evap_results else 212
            
            condensate_streams.append({'Unit': h['Unit'], 'Source': src, 'Flow': h['Flow'], 'Temp': temp})
            
        # 2. CJ Heater
        if actual_steam_flows['cj']:
            h = actual_steam_flows['cj']
            src = h['Source']
            temp = (exh_evaps_obj.T - 273.15)*9/5+32
            if src in vap_temps: temp = vap_temps[src]
            elif src == 'Pre-Evap': temp = pre_evap_results[0]['Vapor T'] if pre_evap_results else 212
            condensate_streams.append({'Unit': h['Unit'], 'Source': src, 'Flow': h['Flow'], 'Temp': temp})
            
        # 3. Pans
        for station, data in actual_steam_flows['pans'].items():
            src = data['Source']
            temp = (exh_evaps_obj.T - 273.15)*9/5+32
            if src in vap_temps: temp = vap_temps[src]
            elif src == 'Pre-Evap': temp = pre_evap_results[0]['Vapor T'] if pre_evap_results else 212
            condensate_streams.append({'Unit': f"{station} Pan", 'Source': src, 'Flow': data['Flow'], 'Temp': temp})
            
        # 4. Deaerator
        condensate_streams.append({'Unit': 'Deaerator', 'Source': 'Exhaust', 'Flow': da_exhaust_demand_tph, 'Temp': (exh_evaps_obj.T - 273.15)*9/5+32})
        
        # 5. Pre-Evaporator (Steam Side)
        if pre_evap_exh > 0:
             condensate_streams.append({'Unit': 'Pre-Evaporator', 'Source': 'Exhaust', 'Flow': pre_evap_exh, 'Temp': pre_evap_cond_temp})

        # Print Table
        print(f"{'Unit':<25} {'Source':<15} {'Flow (TPH)':<15} {'(lb/hr)':<15} {'(GPM)':<10} {'Temp (F)':<10}")
        print("-" * 95)
        total_cond_avail = 0
        for c in condensate_streams:
            f = c['Flow']
            total_cond_avail += f
            print(f"{c['Unit']:<25} {c['Source']:<15} {f:<15.2f} {f*2000:<15.0f} {f*2000/8.33/60:<10.0f} {c['Temp']:<10.1f}")
            
        print("-" * 95)
        bfw_req = lbs_steam_avail / 2000
        print(f"Total Condensate Available: {total_cond_avail:.2f} TPH")
        print(f"Boiler Feed Water Required: {bfw_req:.2f} TPH")
        print(f"Balance:                    {total_cond_avail - bfw_req:.2f} TPH")

        # --- Save CSV ---
        if csv_path:
            with open(csv_path, 'w') as f:
                f.write(mystdout.getvalue())
            print(f"Saved to {csv_path}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    sys.stdout = old_stdout
    return mystdout.getvalue()

# --- GUI ---

def run_gui():
    dpg.create_context()
    dpg.create_viewport(title='St. Mary Material & Energy Balance', width=1600, height=900)
    dpg.set_global_font_scale(1.3)

    def get_inputs():
        # Collect all inputs from DPG
        data = {
            # Mill
            "grinding_rate_tons_day": dpg.get_value("i_grind"),
            "lost_time_percent": dpg.get_value("i_lost_time"),
            "cane_percent_pol": dpg.get_value("i_cane_pol"),
            "cane_percent_fiber": dpg.get_value("i_cane_fib"),
            "imbibition_water_percent": dpg.get_value("i_imb"),
            "filter_cake_percent": dpg.get_value("i_cake_pct"),
            "filter_cake_pol": dpg.get_value("i_cake_pol"),
            "mixed_juice_purity": dpg.get_value("i_mj_pur"),
            "bagasse_percent_pol": dpg.get_value("i_bag_pol"),
            "bagasse_percent_moisture": dpg.get_value("i_bag_moist"),
            "bagasse_percent_ash": dpg.get_value("i_bag_ash"),
            "last_roll_purity": dpg.get_value("i_last_roll"),
            
            # Clarifier
            "milk_of_lime_flow_rate_gpm": dpg.get_value("i_lime"),
            "flocculant_flow_rate_gpm": dpg.get_value("i_floc"),
            "mud_filter_wash_water_percent_cane": dpg.get_value("i_mud_wash"),
            "clarified_juice_purity": dpg.get_value("i_cj_pur"),
            
            # Evap/Pan Mat
            "syrup_brix": dpg.get_value("i_syr_brix"),
            "raw_sugar_pol": dpg.get_value("i_sugar_pol"),
            "raw_sugar_brix": dpg.get_value("i_sugar_brix"),
            "use_birkett": dpg.get_value("i_use_birkett"),
            "cy_slope": dpg.get_value("i_cy_slope"),
            "cy_intercept": dpg.get_value("i_cy_int"),
            
            # Pan Config (Purities/Flows)
            "b_magma_percent_to_a1_strikes": dpg.get_value("i_b_to_a1"),
            "b_magma_percent_to_a2_strikes": dpg.get_value("i_b_to_a2"),
            "b_magma_purity": dpg.get_value("i_b_mag_pur"),
            "syrup_percent_to_a2_strikes": dpg.get_value("i_syr_to_a2"),
            "a1_molasses_percent_to_a2_strikes": dpg.get_value("i_a1_to_a2"),
            "a1_molasses_percent_to_c_grain_strikes": dpg.get_value("i_a1_to_gr"),
            "c_magma_percent_to_b_strikes": dpg.get_value("i_c_to_b"),
            "c_magma_purity": dpg.get_value("i_c_mag_pur"),
            "b_molasses_percent_to_c_grain_strikes": dpg.get_value("i_b_to_gr"),
            "syrup_percent_to_c_grain_strikes": dpg.get_value("i_syr_to_gr"),
            
            # Pan Brix/Factors
            "a1_massecuite_percent_brix": dpg.get_value("i_a1_brix"),
            "a2_massecuite_percent_brix": dpg.get_value("i_a2_brix"),
            "b_massecuite_percent_brix": dpg.get_value("i_b_brix"),
            "grain_massecuite_percent_brix": dpg.get_value("i_gr_brix"),
            "c_massecuite_percent_brix": dpg.get_value("i_c_brix"),
            "a1_molasses_percent_brix": dpg.get_value("i_a1_mol_brix"),
            "a2_molasses_percent_brix": dpg.get_value("i_a2_mol_brix"),
            "b_molasses_percent_brix": dpg.get_value("i_b_mol_brix"),
            "c_molasses_percent_brix": dpg.get_value("i_c_mol_brix"),
            "b_magma_percent_brix": dpg.get_value("i_b_mag_brix"),
            "c_magma_percent_brix": dpg.get_value("i_c_mag_brix"),
            
            "a1_massecuite_steam_factor": dpg.get_value("i_a1_fac"),
            "a2_massecuite_steam_factor": dpg.get_value("i_a2_fac"),
            "b_massecuite_steam_factor": dpg.get_value("i_b_fac"),
            "c_massecuite_steam_factor": dpg.get_value("i_c_fac"),
            "grain_massecuite_steam_factor": dpg.get_value("i_gr_fac"),
            
            # Energy - General
            "live_steam_main_psig": dpg.get_value("i_ls_p"),
            "live_steam_deg_sh": dpg.get_value("i_ls_sh"),
            "exhaust_steam_evaporators_psig": dpg.get_value("i_ex_p"),
            "boiler_feed_water_temp": dpg.get_value("i_bfw_t"),
            "deaerator_inlet_temp": dpg.get_value("i_da_t"),
            "bagasse_tph": 0, # Calculated in Mill
            "steam_jets_lb_hr": dpg.get_value("i_jets"),
            "steam_loss_percent": dpg.get_value("i_stm_loss"),
            
            # Injection Water
            "injection_water_temp_in": dpg.get_value("i_inj_in"),
            "injection_water_temp_out": dpg.get_value("i_inj_out"),
            "pan_vac_a1": dpg.get_value("i_vac_a1"),
            "pan_vac_a2": dpg.get_value("i_vac_a2"),
            "pan_vac_b": dpg.get_value("i_vac_b"),
            "pan_vac_c": dpg.get_value("i_vac_c"),
            "pan_vac_gr": dpg.get_value("i_vac_gr"),
            
            # Energy - Process
            "mj_temp": dpg.get_value("i_mj_temp"),
            "heater_config": dpg.get_value("i_htr_cfg"),
            "sec_htrs_on": dpg.get_value("i_sec_on"),
            "steam_for_prim": dpg.get_value("i_stm_prim"),
            "steam_for_sec": dpg.get_value("i_stm_sec"),
            "prim_out_temp": dpg.get_value("i_prim_t"),
            "sec_out_temp": dpg.get_value("i_sec_t"),
            "parallel_split": dpg.get_value("i_par_split"),
            "cj_htr_enable": dpg.get_value("i_cj_on"),
            "cj_htr_steam": dpg.get_value("i_cj_stm"),
            "cj_in_temp": dpg.get_value("i_cj_in"),
            "cj_out_temp": dpg.get_value("i_cj_out"),
            
            'pre_evaps': [
                {'enable': dpg.get_value(f"i_pre_{i}_en"), 'hs': dpg.get_value(f"i_pre_{i}_hs")}
                for i in range(3)
            ],
            
            "pan_config": {
                'A1': dpg.get_value("i_pan_a1_src"),
                'A2': dpg.get_value("i_pan_a2_src"),
                'B': dpg.get_value("i_pan_b_src"),
                'C': dpg.get_value("i_pan_c_src"),
                'Grain': dpg.get_value("i_pan_gr_src")
            },
            
            "last_eff_vac": dpg.get_value("i_vac"),
            
            # Sets
            'sets': [
                {
                    'enable': dpg.get_value(f"i_set_{i}_en"),
                    'num_effects': int(dpg.get_value(f"i_set_{i}_num")),
                    'hs': [dpg.get_value(f"i_set_{i}_e{j+1}") for j in range(5)]
                } for i in range(4)
            ],
            
            # Turbines
            'ck_trb_hp_tf': [dpg.get_value(f"i_ck_hp_{i}") for i in range(6)],
            'ck_trb_eff': [dpg.get_value(f"i_ck_eff_{i}") for i in range(6)],
            'mill_trb_hp_tf': [dpg.get_value(f"i_mill_hp_{i}") for i in range(7)],
            'mill_trb_eff': [dpg.get_value(f"i_mill_eff_{i}") for i in range(7)],
            'other_trb_names': [dpg.get_value(f"i_other_name_{i}") for i in range(18)],
            'other_trb_hp': [dpg.get_value(f"i_other_hp_{i}") for i in range(18)],
            'other_trb_eff': [dpg.get_value(f"i_other_eff_{i}") for i in range(18)],
            
            "filename": dpg.get_value("i_filename")
        }
        return data

    def cb_run(sender, app_data):
        inputs = get_inputs()
        res = run_full_balance(inputs)
        dpg.set_value("output_text", res)

    def cb_save(sender, app_data):
        inputs = get_inputs()
        name = inputs['filename']
        ts = datetime.now().strftime("%m%d%Y%H%M%S")
        path = f"material_energy_balance_{name}_{ts}.csv"
        res = run_full_balance(inputs, csv_path=path)
        dpg.set_value("output_text", res)
        
    def cb_save_inputs(sender, app_data):
        inputs = get_inputs()
        with open("full_balance_inputs.json", "w") as f:
            json.dump(inputs, f, indent=4)
            
    def cb_load_inputs(sender, app_data):
        if os.path.exists("full_balance_inputs.json"):
            with open("full_balance_inputs.json", "r") as f:
                data = json.load(f)
            # Map back to DPG items (simplified loop)
            # Note: This requires mapping keys back to tags. 
            # For brevity, assuming tags match keys or manual mapping needed.
            # Implementing manual mapping for key fields:
            dpg.set_value("i_grind", data.get("grinding_rate_tons_day", 18000))
            # ... (Add all fields here in real app) ...
            print("Inputs loaded (partial implementation)")

    with dpg.window(label="Main", width=1580, height=880):
        with dpg.group(horizontal=True):
            dpg.add_button(label="RUN BALANCE", callback=cb_run, width=150, height=50)
            dpg.add_button(label="SAVE RESULTS", callback=cb_save, width=150, height=50)
            dpg.add_input_text(label="File Name", tag="i_filename", default_value="run1", width=200)
            dpg.add_button(label="Save Inputs", callback=cb_save_inputs)
            dpg.add_button(label="Load Inputs", callback=cb_load_inputs)

        with dpg.tab_bar():
            # --- TAB 1: Mill & Clarifier ---
            with dpg.tab(label="Mill & Clarifier"):
                dpg.add_text("Mill Settings")
                dpg.add_input_float(label="Grinding Rate (Tons/Day)", tag="i_grind", default_value=18000)
                dpg.add_input_float(label="Lost Time %", tag="i_lost_time", default_value=4.17)
                dpg.add_input_float(label="Cane Pol %", tag="i_cane_pol", default_value=13.5)
                dpg.add_input_float(label="Cane Fiber %", tag="i_cane_fib", default_value=13.0)
                dpg.add_input_float(label="Imbibition %", tag="i_imb", default_value=25.0)
                dpg.add_input_float(label="Bagasse Pol %", tag="i_bag_pol", default_value=2.0)
                dpg.add_input_float(label="Bagasse Moisture %", tag="i_bag_moist", default_value=49.0)
                dpg.add_input_float(label="Bagasse Ash %", tag="i_bag_ash", default_value=4.0)
                dpg.add_input_float(label="Last Roll Purity", tag="i_last_roll", default_value=75.0)
                dpg.add_input_float(label="Filter Cake % Cane", tag="i_cake_pct", default_value=5.0)
                dpg.add_input_float(label="Filter Cake Pol", tag="i_cake_pol", default_value=2.0)
                dpg.add_input_float(label="Mixed Juice Purity", tag="i_mj_pur", default_value=88.0)
                
                dpg.add_separator()
                dpg.add_text("Clarifier Settings")
                dpg.add_input_float(label="Lime Flow (GPM)", tag="i_lime", default_value=25.0)
                dpg.add_input_float(label="Flocculant Flow (GPM)", tag="i_floc", default_value=25.0)
                dpg.add_input_float(label="Mud Wash % Cane", tag="i_mud_wash", default_value=5.0)
                dpg.add_input_float(label="Clarified Juice Purity", tag="i_cj_pur", default_value=89.0)

            # --- TAB 2: Evap & Pan Material ---
            with dpg.tab(label="Evap & Pan (Mat Bal)"):
                dpg.add_text("General")
                dpg.add_input_float(label="Syrup Brix", tag="i_syr_brix", default_value=65.0)
                dpg.add_input_float(label="Sugar Pol", tag="i_sugar_pol", default_value=99.5)
                dpg.add_input_float(label="Sugar Brix", tag="i_sugar_brix", default_value=99.7)
                
                dpg.add_checkbox(label="Use Birkett Crystal Yield", tag="i_use_birkett", default_value=False)
                dpg.add_input_float(label="CY Slope", tag="i_cy_slope", default_value=0.76)
                dpg.add_input_float(label="CY Intercept", tag="i_cy_int", default_value=-11.7)
                
                dpg.add_separator()
                dpg.add_text("Pan Configuration (%)")
                dpg.add_input_float(label="B Mag -> A1", tag="i_b_to_a1", default_value=50, width=200)
                dpg.add_input_float(label="B Mag -> A2", tag="i_b_to_a2", default_value=10, width=200)
                dpg.add_input_float(label="Syrup -> A2", tag="i_syr_to_a2", default_value=25, width=200)
                dpg.add_input_float(label="A1 Mol -> A2", tag="i_a1_to_a2", default_value=10, width=200)
                dpg.add_input_float(label="A1 Mol -> Grain", tag="i_a1_to_gr", default_value=5, width=200)
                dpg.add_input_float(label="C Mag -> B", tag="i_c_to_b", default_value=50, width=200)
                dpg.add_input_float(label="B Mol -> Grain", tag="i_b_to_gr", default_value=10, width=200)
                dpg.add_input_float(label="Syrup -> Grain", tag="i_syr_to_gr", default_value=2, width=200)

                dpg.add_separator()
                dpg.add_text("Purities & Brix")
                dpg.add_input_float(label="B Magma Purity", tag="i_b_mag_pur", default_value=92.0)
                dpg.add_input_float(label="C Magma Purity", tag="i_c_mag_pur", default_value=85.0)
                
                with dpg.table(header_row=True):
                    dpg.add_table_column(label="Stream")
                    dpg.add_table_column(label="Brix")
                    dpg.add_table_column(label="Steam Factor")
                    
                    with dpg.table_row():
                        dpg.add_text("A1 Massecuite")
                        dpg.add_input_float(tag="i_a1_brix", default_value=92.0, width=200)
                        dpg.add_input_float(tag="i_a1_fac", default_value=1.15, width=200)
                    with dpg.table_row():
                        dpg.add_text("A2 Massecuite")
                        dpg.add_input_float(tag="i_a2_brix", default_value=92.0, width=200)
                        dpg.add_input_float(tag="i_a2_fac", default_value=1.15, width=200)
                    with dpg.table_row():
                        dpg.add_text("B Massecuite")
                        dpg.add_input_float(tag="i_b_brix", default_value=93.0, width=200)
                        dpg.add_input_float(tag="i_b_fac", default_value=1.15, width=200)
                    with dpg.table_row():
                        dpg.add_text("C Massecuite")
                        dpg.add_input_float(tag="i_c_brix", default_value=95.0, width=200)
                        dpg.add_input_float(tag="i_c_fac", default_value=1.25, width=200)
                    with dpg.table_row():
                        dpg.add_text("Grain")
                        dpg.add_input_float(tag="i_gr_brix", default_value=90.0, width=200)
                        dpg.add_input_float(tag="i_gr_fac", default_value=1.25, width=200)

                dpg.add_text("Molasses/Magma Brix")
                dpg.add_input_float(label="A1 Mol", tag="i_a1_mol_brix", default_value=75, width=200)
                dpg.add_input_float(label="A2 Mol", tag="i_a2_mol_brix", default_value=75, width=200)
                dpg.add_input_float(label="B Mol", tag="i_b_mol_brix", default_value=75, width=200)
                dpg.add_input_float(label="C Mol", tag="i_c_mol_brix", default_value=75, width=200)
                dpg.add_input_float(label="B Mag", tag="i_b_mag_brix", default_value=92, width=200)
                dpg.add_input_float(label="C Mag", tag="i_c_mag_brix", default_value=93, width=200)

            # --- TAB 3: Energy (Process) ---
            with dpg.tab(label="Energy (Process)"):
                dpg.add_text("Steam Generation")
                dpg.add_input_float(label="Live Steam Psig", tag="i_ls_p", default_value=175)
                dpg.add_input_float(label="Superheat F", tag="i_ls_sh", default_value=0)
                dpg.add_input_float(label="Exhaust Psig", tag="i_ex_p", default_value=14)
                dpg.add_input_float(label="BFW Temp F", tag="i_bfw_t", default_value=235)
                dpg.add_input_float(label="Deaerator Temp F", tag="i_da_t", default_value=212)
                dpg.add_input_float(label="Steam Jets (lb/hr)", tag="i_jets", default_value=2000)
                dpg.add_input_float(label="Steam Loss %", tag="i_stm_loss", default_value=3.0)
                
                dpg.add_separator()
                dpg.add_text("Condenser & Water")
                dpg.add_input_float(label="Inj Water In F", tag="i_inj_in", default_value=85)
                dpg.add_input_float(label="Inj Water Out F", tag="i_inj_out", default_value=120)
                dpg.add_input_float(label="A1 Pan Vac \"Hg", tag="i_vac_a1", default_value=25)
                dpg.add_input_float(label="A2 Pan Vac \"Hg", tag="i_vac_a2", default_value=25)
                dpg.add_input_float(label="B Pan Vac \"Hg", tag="i_vac_b", default_value=25)
                dpg.add_input_float(label="C Pan Vac \"Hg", tag="i_vac_c", default_value=25)
                dpg.add_input_float(label="Grain Pan Vac \"Hg", tag="i_vac_gr", default_value=25)
                
                dpg.add_separator()
                dpg.add_text("Heaters")
                dpg.add_input_float(label="MJ Inlet Temp F", tag="i_mj_temp", default_value=90)
                dpg.add_combo(label="Config", tag="i_htr_cfg", items=["Series", "Parallel"], default_value="Series")
                dpg.add_checkbox(label="Sec Heaters On", tag="i_sec_on", default_value=True)
                dpg.add_combo(label="Prim Steam", tag="i_stm_prim", items=STEAM_SOURCES, default_value="S1 V2")
                dpg.add_combo(label="Sec Steam", tag="i_stm_sec", items=STEAM_SOURCES, default_value="S1 V1")
                dpg.add_input_float(label="Prim Out Temp", tag="i_prim_t", default_value=200)
                dpg.add_input_float(label="Sec Out Temp", tag="i_sec_t", default_value=220)
                dpg.add_input_float(label="Parallel Split %", tag="i_par_split", default_value=50)
                
                dpg.add_checkbox(label="CJ Heater On", tag="i_cj_on", default_value=True)
                dpg.add_combo(label="CJ Steam", tag="i_cj_stm", items=STEAM_SOURCES, default_value="Exhaust")
                dpg.add_input_float(label="CJ In Temp", tag="i_cj_in", default_value=200)
                dpg.add_input_float(label="CJ Out Temp", tag="i_cj_out", default_value=215)
                
                dpg.add_separator()
                dpg.add_text("Pre-Evaporators")
                for i in range(3):
                    with dpg.group(horizontal=True):
                        dpg.add_checkbox(label=f"Pre {i+1}", tag=f"i_pre_{i}_en", default_value=(i==0))
                        dpg.add_input_float(tag=f"i_pre_{i}_hs", default_value=35000, width=100)
                
                dpg.add_separator()
                dpg.add_text("Pan Steam Sources")
                dpg.add_combo(label="A1 Source", tag="i_pan_a1_src", items=STEAM_SOURCES, default_value="S1 V1")
                dpg.add_combo(label="A2 Source", tag="i_pan_a2_src", items=STEAM_SOURCES, default_value="S1 V1")
                dpg.add_combo(label="B Source", tag="i_pan_b_src", items=STEAM_SOURCES, default_value="S1 V1")
                dpg.add_combo(label="C Source", tag="i_pan_c_src", items=STEAM_SOURCES, default_value="S1 V2")
                dpg.add_combo(label="Grain Source", tag="i_pan_gr_src", items=STEAM_SOURCES, default_value="S1 V2")
                
                dpg.add_separator()
                dpg.add_text("Evaporator Config")
                dpg.add_input_float(label="Last Eff Vac \"Hg", tag="i_vac", default_value=25)
                for i in range(4):
                    if dpg.collapsing_header(label=f"Set {i+1}", default_open=(i==0)):
                        dpg.add_checkbox(label="Enable", tag=f"i_set_{i}_en", default_value=(i==0))
                        dpg.add_combo(label="Num Effects", tag=f"i_set_{i}_num", items=["3", "4", "5"], default_value="4")
                        dpg.add_input_float(label="E1 HS", tag=f"i_set_{i}_e1", default_value=37000)
                        dpg.add_input_float(label="E2 HS", tag=f"i_set_{i}_e2", default_value=37000)
                        dpg.add_input_float(label="E3 HS", tag=f"i_set_{i}_e3", default_value=37000)
                        dpg.add_input_float(label="E4 HS", tag=f"i_set_{i}_e4", default_value=37000)
                        dpg.add_input_float(label="E5 HS", tag=f"i_set_{i}_e5", default_value=37000)

            # --- TAB 4: Energy (Turbines) ---
            with dpg.tab(label="Energy (Turbines)"):
                dpg.add_text("Cane Prep")
                with dpg.table(header_row=True):
                    dpg.add_table_column(label="Unit")
                    dpg.add_table_column(label="HP/TF")
                    dpg.add_table_column(label="Efficiency")
                    for i in range(6):
                        with dpg.table_row():
                            dpg.add_text(f"CP {i+1}")
                            dpg.add_input_float(tag=f"i_ck_hp_{i}", default_value=16 if i < 5 else 0, width=150)
                            dpg.add_input_float(tag=f"i_ck_eff_{i}", default_value=0.5, width=150)
                
                dpg.add_text("Mills")
                with dpg.table(header_row=True):
                    dpg.add_table_column(label="Unit")
                    dpg.add_table_column(label="HP/TF")
                    dpg.add_table_column(label="Efficiency")
                    for i in range(7):
                        with dpg.table_row():
                            dpg.add_text(f"Mill {i+1}")
                            dpg.add_input_float(tag=f"i_mill_hp_{i}", default_value=18 if i < 6 else 0, width=150)
                            dpg.add_input_float(tag=f"i_mill_eff_{i}", default_value=0.5, width=150)
                
                dpg.add_text("Other (Total HP)")
                with dpg.table(header_row=True):
                    dpg.add_table_column(label="Name")
                    dpg.add_table_column(label="Total HP")
                    dpg.add_table_column(label="Efficiency")
                    for i in range(18):
                        with dpg.table_row():
                            dpg.add_input_text(tag=f"i_other_name_{i}", default_value=f"Other {i+1}", width=150)
                            dpg.add_input_float(tag=f"i_other_hp_{i}", default_value=100 if i < 13 else 0, width=150)
                            dpg.add_input_float(tag=f"i_other_eff_{i}", default_value=0.5, width=150)

            # --- TAB 5: Results ---
            with dpg.tab(label="Results"):
                dpg.add_input_text(tag="output_text", multiline=True, width=1550, height=750, readonly=True)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    run_gui()
