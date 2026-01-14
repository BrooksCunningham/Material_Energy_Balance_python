# This program is meant to do the material balance for the pan floor
# This balance assumes double magma, top off A strikes with separated A and ToA molasses tanks
import numpy as np
import pandas as pd
import specific_gravity_brix as sg

# Get inputs
# Overall Balance Data
tons_syrup_per_hour = 150 # 150 is around 700 tons cane per hour
syrup_in_purity = 88.77
syrup_brix = 66.37
final_molasses_purity = 36.68
final_molasses_brix = 79.79
raw_sugar_purity = 99.61
raw_sugar_brix = 99.93

# Information for A1 Strikes
a1_molasses_purity = 75.44
a1_molasses_brix = 76.05
a1_massecuite_brix = 93.16

# Information for A2 Strikes
a2_molasses_purity = 74.26
a2_molasses_brix = 79.00
a2_massecuite_purity = 88.28
a2_massecuite_brix = 93.58


# Information for B strikes
b_magma_purity = 90.89
b_magma_brix = 93.5
b_magma_perc_to_a1 = 40
b_magma_perc_to_a2 = 20
b_massecuite_purity = 76.0 
b_massecuite_brix = 94.75
b_molasses_purity = 55.53
b_molasses_brix = 74.46
b_mas_feed_perc_a1_mol = 80 
    # specifies the % of A1 molasses in feed to make b massecuite
    # So if this value = 80, then the molasses blend is 80% A1 molasses
perc_b_mag_to_a2 = 20 # how much b magma sent to A2 strikes
perc_b_mag_to_a1 = 40 # how much b magma sent to A1 strikes
# remainder goes to syrup to be redissolved

# Information for C strikes
c_magma_purity = 81.59
c_magma_brix = 94.6
c_massecuite_purity = 57.01
c_massecuite_brix = 96.00

# Information for Grain II Strikes
grain_ii_purity = 61.46
grain_ii_brix = 89.90

# Information for Grain I strikes
grain_i_purity = 70.56
grain_i_brix = 89.74
syrup_a1_blend_to_grain_i_ratio = 0.67 
    # The blend (syrup + A1 molasses) solids ratio to total ratio, usually 2/3 (0.67)

# Pan factors for evaporation, multiplier for req exhaust steam, accounts for wash water, bleed, ect...
a_factor = 1.15
b_factor = 1.15
c_factor = 1.25
grain_factor = 1.25

# multipliers for using V1 or V2 instead of exhaust
v1_multiplier = 0.98330
v2_multiplier = 0.96906

# define functions
def stream_dict(name, solids_flow, brix, purity, temp=150):
    """ Creates dictionary of flow stream"""
    tons_per_hour = solids_flow * 100 / brix
    tons_pol = solids_flow * purity / 100
    sgrav = sg.spec_grav(brix, temp)
    pol = tons_pol / tons_per_hour * 100
    volume = tons_per_hour * 2000 / (62.4 * sgrav)
    stream_info = {
        "stream_name": name.title(),
        "flowrate_tph": tons_per_hour,
        "tons_solids": solids_flow,
        "tons_pol": tons_pol,
        "purity": purity,
        "brix": brix,
        "pol": pol,
        "sg": sgrav,
        "temp_F": temp,
        "cu_ft_per_hr": volume
    }
    return stream_info

def evaporated(stream_info_leaving, *stream_info_entering):
    entering = sum(stream['flowrate_tph'] for stream in stream_info_entering)
    leaving = stream_info_leaving['flowrate_tph']
    evaporation = entering - leaving
    return evaporation

def steam_req(name, evaporation, factor):
    """Creates a dictionary for steam required"""
    exh_req = evaporation * factor
    v1_req = exh_req * v1_multiplier
    v2_req = exh_req * v2_multiplier
    steam_info = {
        'steam_supplied_to': name.title(),
        'evaporated_tph': evaporation,
        'steam_factor': factor,
        'exhaust_req_tph': exh_req,
        'v1_req_tph': v1_req,
        'v2_req_tph': v2_req,
    }
    return steam_info
    

def display_stream(stream_info):
    """Displays Stream Information with good formatting"""
    results = stream_info
    print(f"{'PROPERTY':<20} | {'VALUE':<10}")
    print("-" * 35)

    for key, value in results.items():
        # format if numeric, otherwise print as is
        display_val = f"{value:.3f}" if isinstance(value, (int, float)) else value
        print(f"{key:<20} | {display_val:<10}")

def display_flows(name, flowrate, brix, purity, temp=150):
    print(f"{name}")
    print(f"Total Flow in tons / hr: {flowrate:,.3f}")
    solids_flow = flowrate * brix / 100
    print(f"Solids tons / hr: {solids_flow:,.3f}")
    pol_flow = solids_flow * purity / 100
    print(f"Pol tons / hr: {pol_flow:.3f}")
    sgrav = sg.spec_grav(brix, temp)
    print(f'Specific Gravity: {sgrav}')
    

def sjm(high_purity, mid_purity, low_purity): # solids ratio balance via cobenze
    low_purity_solids_ratio = high_purity - mid_purity
    high_purity_solids_ratio = mid_purity - low_purity
    total_solids_ratio = high_purity - low_purity
    return high_purity_solids_ratio, total_solids_ratio, low_purity_solids_ratio

def sjm_mid_flow(mid_purity_flow, high_purity, mid_purity, low_purity):  
    """Returns the high and low purity solids flows given 
       mid purity flow and the high, mid, and low purities """
    low_purity_solids_ratio = high_purity - mid_purity                   
    high_purity_solids_ratio = mid_purity - low_purity
    total_solids_ratio = high_purity - low_purity
    high_purity_flow = high_purity_solids_ratio / total_solids_ratio * mid_purity_flow
    low_purity_flow = low_purity_solids_ratio / total_solids_ratio * mid_purity_flow 
    return high_purity_flow, low_purity_flow

def sjm_low_flow(low_purity_flow, high_purity, mid_purity, low_purity):  
    """Returns the mid and high purity solids flow given
       low purity flow and the high, mid, and low purities"""
    low_purity_solids_ratio = high_purity - mid_purity                    
    high_purity_solids_ratio = mid_purity - low_purity
    total_solids_ratio = high_purity - low_purity
    high_purity_flow = high_purity_solids_ratio / low_purity_solids_ratio * low_purity_flow
    mid_purity_flow = total_solids_ratio / low_purity_solids_ratio * low_purity_flow
    return high_purity_flow, mid_purity_flow

def sjm_high_flow(high_purity_flow, high_purity, mid_purity, low_purity):  
    """Returns the mid and low purity solids flow given high purity flow
       and the high, mid, and low purities"""
    low_purity_solids_ratio = high_purity - mid_purity                      
    high_purity_solids_ratio = mid_purity - low_purity
    total_solids_ratio = high_purity - low_purity
    mid_purity_flow = total_solids_ratio / high_purity_solids_ratio * high_purity_flow
    low_purity_flow = low_purity_solids_ratio / high_purity_solids_ratio * high_purity_flow
    return mid_purity_flow, low_purity_flow

def hi_blend_to_strike(
        high_blend_purity, low_blend_purity, strike_solids, 
        low_purity_solids, strike_purity, low_purity):
    # meaning high purity in SJM (so 'S') is a blend you are solving for
    # Example below for clarity
    # Syrup + A1 Mol = grain I - b mol 
    # pur (syrup) + pur (A1 mol) = pur (grain i) - pur (b mol)
    # linear algebra array
    # [1,                  1]
    # [pur syrup, pur A1 mol] A matrix
    #[grain i - b mol, pur(grain i) - pur(b mol)]
    A = np.array([[1, 1], 
              [high_blend_purity, low_blend_purity]]) # Left Hand Side
    B = np.array([
        strike_solids - low_purity_solids, 
        strike_purity * strike_solids - low_purity * low_purity_solids]) # Right Hand Side
    solution = np.linalg.solve(A, B)
    ts_high_blend = solution[0]
    ts_low_blend = solution[1]
    return ts_high_blend, ts_low_blend

def low_blend_to_strike(
        high_blend_purity, low_blend_purity, strike_solids, 
        high_purity_solids, strike_purity, high_purity
        ):
    # meaning low purity in SJM (so 'M') is a blend you are solving for
    # Example below for clarity
    # Syrup + A1 Mol = A2 mas - b mag 
    # pur (syrup) + pur (A1 mol) = pur (A2 mas) - pur (b mag)
    # linear algebra array
    # [1,                  1]
    # [pur syrup, pur A1 mol] A matrix
    #[A2 mas - b mag, pur(A2 mas) - pur(b mag)]
    A = np.array([[1, 1], 
              [high_blend_purity, low_blend_purity]]) # Left Hand Side
    B = np.array([
        strike_solids - high_purity_solids, 
        strike_purity * strike_solids - high_purity * high_purity_solids
        ]) # Right Hand Side
    solution = np.linalg.solve(A, B)
    ts_high_blend = solution[0]
    ts_low_blend = solution[1]
    return ts_high_blend, ts_low_blend

def display_solids(solids_flow_name, solids_flowrate): # print the solids flowrate
    print(f"{solids_flow_name} tons solids per hour: {solids_flowrate:.2f}")

# ts_ means tons solids

# Overall Solids Balance
ts_syrup = tons_syrup_per_hour * syrup_brix / 100
ts_sugar, ts_final_molasses = sjm_mid_flow(
    ts_syrup, raw_sugar_purity, syrup_in_purity, final_molasses_purity
    )

display_solids('Syrup', ts_syrup)
display_solids('Sugar', ts_sugar)
display_solids('Final Molasses', ts_final_molasses)

# Solids flow on C massecuite
ts_c_magma, ts_c_massecuite = sjm_low_flow(
    ts_final_molasses, c_magma_purity, c_massecuite_purity, final_molasses_purity
    )


# Solids Flow on B Molasses and Grain II to C Massecuite
ts_grain_ii, ts_b_mol_to_c_massecuite = sjm_mid_flow(
    ts_c_massecuite, grain_ii_purity, c_massecuite_purity, b_molasses_purity
    )


# Solids Flow on Grain I and B molasses to Grain II
ts_grain_i, ts_b_molasses_to_grain_ii = sjm_mid_flow(
    ts_grain_ii, grain_i_purity, grain_ii_purity, b_molasses_purity
    )

# Starting here we need to do a while loop to account for the b and c magma being remelted
syrup_purity = syrup_in_purity # data to start the loop
ts_syrup_old = ts_syrup # storing number for iterations
 
iteration = 1
while iteration < 40:    
    # Solids flow on B molasses, A1 molasses, and Syrup to Grain I
    ts_b_mol_to_grain_i = (
        (1 - syrup_a1_blend_to_grain_i_ratio) 
        * ts_grain_i
        )
    ts_syrup_grain_i, ts_a1_mol_grain_i = hi_blend_to_strike(
        syrup_purity, a1_molasses_purity, ts_grain_i, 
        ts_b_mol_to_grain_i, grain_i_purity, b_molasses_purity
        )


    # Solids flow B Massecuite Balance, b magma and b massecuite
    ts_c_magma_to_b_mas = ts_c_magma + 1 # to initialize while loop
    a1_a2_blend_purity = 99 # starting value to begin loop

    while (ts_c_magma_to_b_mas >= ts_c_magma 
        or b_massecuite_purity <= a1_a2_blend_purity):
        
        ts_b_mol_total = (
            ts_b_mol_to_c_massecuite 
            + ts_b_mol_to_grain_i 
            + ts_b_molasses_to_grain_ii)

        ts_b_magma, ts_b_massecuite = sjm_low_flow(
            ts_b_mol_total, b_magma_purity, 
            b_massecuite_purity, b_molasses_purity
            )

        # Solids flow for A2 and A1 molasses for B Massecuite
        b_mas_feed_perc_a2_mol = 100 - b_mas_feed_perc_a1_mol

        a1_a2_blend_purity = (
            (b_mas_feed_perc_a1_mol * a1_molasses_purity 
            + b_mas_feed_perc_a2_mol * a2_molasses_purity)
            / 100
            )

        ts_c_magma_to_b_mas, ts_a1a2_blend = sjm_mid_flow(
            ts_b_massecuite, c_magma_purity, 
            b_massecuite_purity, a1_a2_blend_purity
            )

        if ts_c_magma_to_b_mas >= ts_c_magma:
            print("Warning!!! B massecuite requires more C Magma than what is "
                "available!!! Please adjust purities")
            current_pur = b_massecuite_purity
            b_massecuite_purity = float(input(f"Your current purity is {current_pur}, "
                                        "you should lower the purity: "))

        if b_massecuite_purity <= a1_a2_blend_purity:
            print("WARNING!!! Your B Massecuite Purity is lower than the blend purity!!!")
            b_massecuite_purity = float(input(f"B massecuite purity {b_massecuite_purity} "
                                            f" A1 A2 molasses blend purity {a1_a2_blend_purity}"
                                            " , please increase your B massecuite purity: "))

    ts_a1_mol_to_b_mas = ts_a1a2_blend * b_mas_feed_perc_a1_mol / 100

    # A2 massecuite solids flowrate, assumes A2 sugar purity = raw sugar purity
    ts_a2_mol_tot = ts_a1a2_blend * b_mas_feed_perc_a2_mol / 100
    ts_a2_sugar, ts_a2_mas = sjm_low_flow(
        ts_a2_mol_tot, raw_sugar_purity, a2_massecuite_purity, a2_molasses_purity
    )


    # Syrup, A1 Molasses, and B Magma to the A2 Strikes
    ts_b_magma_to_a2 = ts_b_magma * b_magma_perc_to_a2 / 100
    ts_a1_syrup_blend = ts_a2_mas - ts_b_magma_to_a2
    ts_syrup_to_a2_mas, ts_a1_mol_to_a2_mas = low_blend_to_strike(
        syrup_purity, a1_molasses_purity, ts_a2_mas, 
        ts_b_magma_to_a2, a2_massecuite_purity, b_magma_purity
    )

    # All Remaining Material goes to A1 Strikes, A1 purity is calculated
    # this is just the rest of the syrup and b magma
    # remelt will be handled via a while loop
    ts_syrup_for_a1_mas = ts_syrup - ts_syrup_to_a2_mas - ts_syrup_grain_i
    ts_b_magma_to_a1 = ts_b_magma * b_magma_perc_to_a1 / 100
    ts_a1_massecuite = ts_b_magma_to_a1 + ts_syrup_for_a1_mas
    ts_a1_mol_total = ts_a1_mol_to_a2_mas + ts_a1_mol_grain_i + ts_a1_mol_to_b_mas
    ts_a1_sugar = ts_sugar - ts_a2_sugar
    a1_massecuite_purity = (
        (ts_syrup_for_a1_mas * syrup_purity + ts_b_magma_to_a1 * b_magma_purity)
        / ts_a1_massecuite
    )

    # adding remelt into the syrup
    ts_c_mag_remelt = ts_c_magma - ts_c_magma_to_b_mas
    ts_b_mag_remelt = ts_b_magma - ts_b_magma_to_a1 - ts_b_magma_to_a2

    ts_syrup = ts_syrup_old + ts_c_mag_remelt + ts_b_mag_remelt
    syrup_purity_prev = syrup_purity
    syrup_purity = (
        (syrup_purity * ts_syrup_old
        + c_magma_purity * ts_c_mag_remelt
        + b_magma_purity * ts_b_mag_remelt)
        / ts_syrup
        )
    iteration += 1
ts_syrup_and_remelt = ts_syrup

# Initialize stream list
sugar_stream_collection = []
def add_sug_stream(*sugar_stream_name):
    sugar_stream_collection.extend(sugar_stream_name)

steam_collection = []
def add_steam_stream(*steam_stream_name):
    steam_collection.extend(steam_stream_name)


# overall balance information
syrup_entering = stream_dict("syrup entering pan floor", ts_syrup_old, syrup_brix, syrup_in_purity)
raw_sugar = stream_dict("Total Raw Sugar", ts_sugar, raw_sugar_brix, raw_sugar_purity)
final_molasses = stream_dict("Final Molasses", ts_final_molasses, final_molasses_brix, final_molasses_purity)
add_sug_stream(syrup_entering, raw_sugar, final_molasses)
# storing syrup as delivered to pans
syrup_and_remelt = stream_dict('syrup and remelt blend', ts_syrup_and_remelt, syrup_brix, syrup_purity)
add_sug_stream(syrup_and_remelt)
# will call syrup and remelt 'sar' from now on

# A1 Strikes
# entering
sar_to_a1_strikes = stream_dict("syrup remelt blend to a1 strikes", ts_syrup_for_a1_mas, syrup_brix, syrup_purity)
b_mag_a1_strikes = stream_dict("b magma for a1 strikes", ts_b_magma_to_a1, b_magma_brix, b_magma_purity)
# leaving
a1_massecuite = stream_dict('a massecuite', ts_a1_massecuite, a1_massecuite_brix, a1_massecuite_purity)
a1_evaporated = evaporated(a1_massecuite, sar_to_a1_strikes, b_mag_a1_strikes)
a1_steam_req = steam_req('A1 Strikes', a1_evaporated, a_factor)
a1_molasses = stream_dict('A1 Molasses', ts_a1_mol_total, a1_molasses_brix, a1_molasses_purity)
a1_sugar = stream_dict('A1 Sugar', ts_a1_sugar, raw_sugar_brix, raw_sugar_purity)
add_sug_stream(sar_to_a1_strikes, b_mag_a1_strikes, a1_massecuite, a1_molasses, a1_sugar)
add_steam_stream(a1_steam_req)

# A2 Strikes
# entering
sar_to_a2_strikes = stream_dict("syrup remelt blend to a2 strikes", ts_syrup_to_a2_mas, syrup_brix, syrup_purity)
a1_mol_to_a2_strikes = stream_dict("a1 molasses to a2 strikes", ts_a1_mol_to_a2_mas, a1_molasses_brix, a1_molasses_purity)
b_mag_a2_strikes = stream_dict("b magma for a2 strikes", ts_b_magma_to_a2, b_magma_brix, b_magma_purity)
# leaving
a2_massecuite = stream_dict('a2 massecuite', ts_a2_mas, a2_massecuite_brix, a2_massecuite_purity)
a2_evaporated = evaporated(a2_massecuite, sar_to_a2_strikes, a1_mol_to_a2_strikes, b_mag_a2_strikes)
a2_steam_req = steam_req("a2 strikes", a2_evaporated, a_factor)
a2_molasses = stream_dict('a2 molasses', ts_a2_mol_tot, a2_molasses_brix, a2_molasses_purity)
a2_sugar = stream_dict('a2 sugar', ts_a2_sugar, raw_sugar_brix, raw_sugar_purity)
add_sug_stream(sar_to_a2_strikes, a1_mol_to_a2_strikes, b_mag_a2_strikes, a2_massecuite, a2_molasses, a2_sugar)
add_steam_stream(a2_steam_req)

# B Strikes
# entering
a1_mol_b_strikes = stream_dict("a1 molasses for b strikes", ts_a1_mol_to_b_mas, a1_molasses_brix, a1_molasses_purity)
a2_mol_b_strikes = stream_dict('a2 molasses for b strikes', ts_a2_mol_tot, a2_molasses_brix, a2_molasses_purity)
c_magma_b_strikes = stream_dict('c magma for b strikes', ts_c_magma_to_b_mas, c_magma_brix, c_magma_purity)
# leaving
b_massecuite = stream_dict('b massecuite', ts_b_massecuite, b_massecuite_brix, b_massecuite_purity)
b_evaporated = evaporated(b_massecuite, a1_mol_b_strikes, a2_mol_b_strikes, c_magma_b_strikes)
b_steam_req = steam_req('b strikes', b_evaporated, b_factor)
b_magma = stream_dict('b magma', ts_b_magma, b_magma_brix, b_magma_purity)
b_molasses = stream_dict('b molasses', ts_b_mol_total, b_molasses_brix, b_molasses_purity)
add_sug_stream(a1_mol_b_strikes, a2_mol_b_strikes, c_magma_b_strikes, b_massecuite, b_magma, b_molasses)
add_steam_stream(b_steam_req)

# Grain I
# entering
syrup_grain_i = stream_dict('syrup for grain i', ts_syrup_grain_i, grain_i_brix, grain_i_purity)
a1_mol_grain_i = stream_dict('a1 molasses for grain i', ts_a1_mol_grain_i, a1_molasses_brix, a1_molasses_purity)
b_mol_grain_i = stream_dict('b molasses for grain i', ts_b_mol_to_grain_i, b_molasses_brix, b_molasses_purity)
# leaving
grain_i = stream_dict('grain i', ts_grain_i, grain_i_brix, grain_i_purity)
grain_i_evaporated = evaporated(grain_i, syrup_grain_i, a1_mol_grain_i, b_mol_grain_i)
grain_i_steam_req = steam_req('grain i', grain_i_evaporated, grain_factor)
add_sug_stream(syrup_grain_i, a1_mol_grain_i, b_mol_grain_i, grain_i)
add_steam_stream(grain_i_steam_req)

# Grain II
# entering
# grain i
b_molasses_grain_ii = stream_dict('b molasses for grain ii', ts_b_molasses_to_grain_ii, b_molasses_brix, b_molasses_purity)
# leaving
grain_ii = stream_dict('grain ii', ts_grain_ii, grain_ii_brix, grain_ii_purity)
grain_ii_evaporated = evaporated(grain_ii, b_molasses_grain_ii, grain_i)
grain_ii_steam_req = steam_req('grain ii', grain_ii_evaporated, grain_factor)
add_sug_stream(b_molasses_grain_ii, grain_ii)
add_steam_stream(grain_ii_steam_req)

# C Strikes
# entering
grain_ii = stream_dict('grain ii', ts_grain_ii, grain_ii_brix, grain_ii_purity)
b_molasses_c_strikes = stream_dict('b molasses to c strikes', ts_b_mol_to_c_massecuite, b_molasses_brix, b_molasses_purity)
# leaving
c_massecuite = stream_dict('c massecuite', ts_c_massecuite, c_massecuite_brix, c_massecuite_purity)
c_evaporated = evaporated(c_massecuite, grain_ii, b_molasses_c_strikes)
c_steam_req = steam_req('c strikes', c_evaporated, c_factor)
c_magma = stream_dict('c magma', ts_c_magma, c_magma_brix, c_magma_purity)
c_molasses = final_molasses
add_sug_stream(b_molasses_c_strikes, c_massecuite, c_magma)
add_steam_stream(c_steam_req)

# Remelt account
b_magma_remelt = stream_dict('b magma to remelt', ts_b_mag_remelt, b_magma_brix, b_magma_purity)
c_magma_remelt = stream_dict('c magma to remelt', ts_c_mag_remelt, c_magma_brix, c_magma_purity)
add_sug_stream(b_magma_remelt, c_magma_remelt)

df_sugar = pd.DataFrame(sugar_stream_collection)
df_steam = pd.DataFrame(steam_collection)

print(df_sugar)
print(df_steam)

# export frames to excel
with pd.ExcelWriter("Material_Balance_pan_floor.xlsx", engine="openpyxl") as writer:
    # Write the first table at the very top (row 0)
    df_sugar.to_excel(writer, sheet_name="Balance", index=False)
    
    # Write the second table starting 2 rows after the first one ends
    # len(df_in) + 2 gives you a small gap between tables
    df_steam.to_excel(writer, sheet_name="Balance", index=False, startrow=len(df_sugar) + 2)