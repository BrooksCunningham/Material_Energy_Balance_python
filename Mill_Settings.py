import math

# The first thing we need is the data for the capacity
tcpd = 17000  # tons of cane per day
cfib_per = 14.0  # Cane % Fiber

# For all mill calcs
tfph = tcpd * cfib_per / 100 / 24 # Tons of fiber per hour
pfpm = tfph * 2000 / 60 # Lbs of fiber per minute

# Now we need the data for each individual mill

# Roller Geometry
groove_depth_list = [2.5, 2.063, 2, 1.9375, 1.9375, 1.9375]
pitch_list = [2.5, 2, 2, 2, 2, 2] # Roller Pitch in inches
length_list = [7.5, 7, 7, 7, 7, 7.5] # Roller length in inches
top_roll_dia_list = [49.5, 48.0, 49.5, 49.5, 49.5, 49.5] # Top Roller Diameter in inches
cane_roll_dia_list  = [48.5, 48.25, 47.25, 47.5, 49.5, 49.5] # Cane Roller Diameters
bag_roll_dia_list  = [49.5, 48.75, 48.0, 50.0, 50.0, 50.0]  # Bagasse Roller Diameters
four_roll_dia_list  = [39.0, 37.0, 38.0, 39.0, 39.5, 39.0]  # Fourth Roller Diameters


# Mill Speed and HP demand
rpm_list = [5.13, 5.1, 4.3, 4.3, 4.3, 4.3 ] # Roller RPM
hp_fib_list = [18, 18, 18, 18, 18, 18] # This is the horse power demand per ton of fiber per hour

# Material composition upon compression
fib_fill_list = [66, 87, 105, 116, 130, 130]  # Fiber Fill in lbs / cu ft

# Moisture and Fiber Data Lists
moist_a_list = [67, 60, 55, 47, 46, 46]      # First moisture values
moist_b_list = [60, 56, 48, 41, 36, 36]      # Second moisture values

fib_a_list = [33, 40, 45, 47, 51, 51]        # First fiber values
fib_b_list = [36, 44, 52, 56.5, 63, 63]      # Second fiber values

# Density Data List
rho_m_list = [66, 66, 65, 64, 61, 61]        # Moisture Density (lbs/cu ft)


# Mill floats and opening ratios
float_list  = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]     # Top roll float (inches)
cane_rat_list  = [2.1, 2.0, 1.9, 1.8, 1.75, 1.7]   # Cane Roll Ratio
four_rat_list  = [4.5, 5, 5.5, 5, 4.85, 4.75]      # 4th Roller Ratio
chute_rat_list = [14, 13, 12, 11, 10, 9]           # Chute to Bagasse ratio






# Now comes the calculations

# Getting basic numbers for settings..


# Now I will define several functions to call later on

# Blanket Load lbs/fiber/sq ft
def blanket_load(pfpm, rpm, roll_leng):
    BL = pfpm / (math.pi * rpm * 3.83 * roll_leng)

    return BL

blanket_loads = []

for i in range(6):
    a = pfpm
    r = rpm_list[i]
    l = length_list[i]
    result = blanket_load(a, r, l)
    blanket_loads.append(round(result, 2))


# Roller surface speed in ft / minute
def roll_spd(diam, rpm):
    
    RS = diam * rpm * math.pi / 12

    return RS

# Roller speeds
top_roller_speeds = []

for i in range(6):
    diam = top_roll_dia_list[i]
    rpm = rpm_list[i]
    results = roll_spd(diam, rpm)
    top_roller_speeds.append(round(results, 2))

cane_roller_speeds = []
for i in range(6):
    diam = cane_roll_dia_list[i]
    rpm = rpm_list[i]
    results = roll_spd(diam, rpm)
    cane_roller_speeds.append(round(results, 2))

bag_roller_speeds = []
for i in range(6):
    diam = bag_roll_dia_list[i]
    rpm = rpm_list[i]
    results = roll_spd(diam, rpm)
    bag_roller_speeds.append(round(results, 2))

# Fourth Roll Speed is different, you have to include 20/15 in the calc
def fourth_roll_spd(diam, rpm):
    frs = diam * rpm * math.pi / 12 * 20 / 15
    return frs
four_roller_speeds = []
for i in range(6):
    diam = four_roll_dia_list[i]
    rpm = rpm_list[i]
    results = fourth_roll_spd(diam, rpm)
    four_roller_speeds.append(round(results, 2))



# Moisture to Fiber compression
def comp(moist, fib):
    
    comp = moist / fib

    return comp

compressA = []
for i in range(6):
    moist = moist_a_list[i]
    fib = fib_a_list[i]
    results = comp(moist, fib)
    compressA.append(round(results,2))


compressB = []
for i in range(6):
    moist = moist_b_list[i]
    fib = fib_b_list[i]
    results = comp(moist, fib)
    compressB.append(round(results, 2))


# Hey gemini, look what I did here below...
# Fiber Density Under Compression
def fib_dens_comp(fib_fill):

    FDC = 20 / fib_fill

    return FDC

fib_dens = []
for i in range(6):
    fib_fill = fib_fill_list[i]
    results = fib_dens_comp(fib_fill)
    fib_dens.append(round(results, 3))

# Hey Gemini, now finish the pattern here on down

# Moisture in Blanket   
def mois_in_blkt(rho_moist, comp):

    MIB = 20 / rho_moist * comp

    return MIB


# Mill O Factor
def O_fact(fib_dens_comp, mois_in_blkt):

    O = fib_dens_comp + mois_in_blkt

    return O

# Now to get dynamic mill settings in inches
def bag_roll_dyn(tons_fib_hour, roll_len, roll_spd, O_fac):

    BRD = tons_fib_hour * 24 / (roll_len * roll_spd * 0.1 * 12) * O_fac

    return BRD  # Bagass dynamic setting

def set_dyn(bag_roll_dyn, roll_ratio):

    SD = bag_roll_dyn * roll_ratio

    return SD  # Cane Roll or Fourth roll dynamic setting based on their ratio



# Now the static setting
def static_set(dynamic_set, float):

    SS = dynamic_set - float

    return SS

# Now the dynamic working Centers
def dy_work_cent(top_roll_dia, roll_dia, groove_depth, float, static_set):
    DWC = top_roll_dia / 2 + roll_dia / 2 + static_set + float - groove_depth
    return DWC

# Now the static working centers
def st_work_cent(dy_work_cent, float):
    SWC = dy_work_cent - float
    return SWC

# Enscribed Volume
def en_vol(dyn_set, roll_spd):
    EV = dyn_set * roll_spd
    return EV # cu ft per minute

# Max top roll speed
def max_top_spd(top_roll_dia):
    MTS = (top_roll_dia / 12 * 108) / (top_roll_dia / 12 + 2.4)
    return MTS

# Feed Chute Opening
def feed_open(feed_cht_rat, bag_set_dyn):
    FO = feed_cht_rat * bag_set_dyn
    return FO

# Theoretical Horse Power Required
def hp_req(tfph):
    HP = tfph * 18
    return HP

# Escribed Volume
def escr_vol(roll_dia, grv_depth, rpm, roll_leng, dyn_set):
    ESV = (roll_dia - grv_depth)*(math.pi() * rpm) / 12 * roll_leng * (dyn_set / 12)
    return ESV

# Compaction
def compact(pfpm, escrib_vol):
    compact = pfpm / escrib_vol
    return compact




# Lists to store the final results
mib_list = []
o_fact_list = []
bag_dyn_list = []
cane_dyn_list = []
four_dyn_list = []
bag_static_list = []
cane_static_list = []
chute_opening_list = []

for i in range(6):
    # 1. Calculate Moisture in Blanket
    mib = mois_in_blkt(rho_m_list[i], compressB[i])
    mib_list.append(round(mib, 4))
    
    # 2. Calculate Mill O Factor
    o_f = O_fact(fib_dens[i], mib)
    o_fact_list.append(round(o_f, 4))
    
    # 3. Calculate Dynamic Bagasse Roll Setting
    # Using tfph (tons fiber per hour) and top roll surface speed
    b_dyn = bag_roll_dyn(tfph, length_list[i], top_roller_speeds[i], o_f)
    bag_dyn_list.append(round(b_dyn, 3))
    
    # 4. Calculate Cane and 4th Roll Dynamic Settings using ratios
    c_dyn = set_dyn(b_dyn, cane_rat_list[i])
    cane_dyn_list.append(round(c_dyn, 3))
    
    f_dyn = set_dyn(b_dyn, four_rat_list[i])
    four_dyn_list.append(round(f_dyn, 3))
    
    # 5. Calculate Static Settings (Setting - Float)
    b_stat = static_set(b_dyn, float_list[i])
    bag_static_list.append(round(b_stat, 3))
    
    c_stat = static_set(c_dyn, float_list[i])
    cane_static_list.append(round(c_stat, 3))
    
    # 6. Feed Chute Opening
    f_open = feed_open(chute_rat_list[i], b_dyn)
    chute_opening_list.append(round(f_open, 2))

# Calculate Power Requirement (Total Tandem)
total_hp = hp_req(tfph)

# Lists for the missing metrics
escr_vol_list = []

for i in range(6):
    # 1. Calculate Escribed Volume (cu ft / min)
    # Using your formula: (Roll Dia - Grv Depth) * (pi * RPM) / 12 * Length * (Dyn Set / 12)
    # Note: We use the Bagasse Dynamic Setting for the final discharge volume
    esv = (top_roll_dia_list[i] - groove_depth_list[i]) * (math.pi * rpm_list[i]) / 12 * length_list[i] * (bag_dyn_list[i] / 12)
    escr_vol_list.append(round(esv, 2))
    
    

# Lists for Roller-Specific Escribed Volumes (cu ft / min)
esv_cane_list = []
esv_bag_list = []
esv_fourth_list = []
mill_hp_list = []
tp_esv_list = []
compac_cane_list = []
compac_bag_list = []
compac_tp_list = []

for i in range(6):
    # 1. ESV Cane Roller
    # Formula: (Cane_Dia - Grv) * pi * RPM / 12 * Length * (Cane_Dyn_Set / 12)
    esv_c = (top_roll_dia_list[i] - groove_depth_list[i]) * (math.pi * rpm_list[i]) / 12 * length_list[i] * (cane_dyn_list[i] / 12)
    esv_cane_list.append(round(esv_c, 2))
    compac_cane = pfpm / esv_cane_list[i] 
    compac_cane_list.append(round(compac_cane,2))
    
    # 2. ESV Bagasse Roller
    esv_b = (top_roll_dia_list[i] - groove_depth_list[i]) * (math.pi * rpm_list[i]) / 12 * length_list[i] * (bag_dyn_list[i] / 12)
    esv_bag_list.append(round(esv_b, 2))
    compac_bag = pfpm / esv_bag_list[i] 
    compac_bag_list.append(round(compac_bag,2))

    # 3. ESV Fourth Roller (Uses specific 4th roll speed)
    # Using your fourth_roll_spd logic implicitly:
    esv_f = (four_roll_dia_list[i] - groove_depth_list[i]) * (math.pi * rpm_list[i] * 20/15) / 12 * length_list[i] * (four_dyn_list[i] / 12)
    esv_fourth_list.append(round(esv_f, 2))

    # 3.5 Turn Plate Escribed Volume
    tp_esv = (cane_dyn_list[i] * 1.75 / 12 * (top_roller_speeds[i] * length_list[i]))
    tp_esv_list.append(round(tp_esv,2))
    compac_tp = pfpm / tp_esv_list[i] 
    compac_tp_list.append(round(compac_tp,2))
    
    # 4. Horsepower Per Mill
    # Based on your hp_req function (tfph * 18), but applied per mill unit
    m_hp = tfph * hp_fib_list[i] # Assuming equal distribution or specific tfph load
    mill_hp_list.append(round(m_hp, 2))




# ---------------------------------------------------------
# EXPORTING EVERYTHING TO EXCEL
# ---------------------------------------------------------

import pandas as pd

# Consolidating every list into the final Export Dictionary
final_export_data = {
    "Mill No.": [f"M{i+1}" for i in range(6)],
    "Tons Cane Per Day": [tcpd]*6,
    "Cane % Fiber": [cfib_per]*6,
    "Tons Fiber Per Hour": [tfph]*6,
    "Lbs Fiber Per Minute": [pfpm]*6,
    # Geometry
    "Top Roll Dia (in)": top_roll_dia_list,
    "Cane Roll Dia (in)": cane_roll_dia_list,
    "Bagasse Roll Dia (in)": bag_roll_dia_list,
    "4th Roll Dia (in)": four_roll_dia_list,
    "Groove Depth (in)": groove_depth_list,
    "Pitch (in)": pitch_list,
    "Length (ft)": length_list,
    "RPM": rpm_list,
    # Speeds
    "Top Speed (fpm)": top_roller_speeds,
    "Cane Speed (fpm)": cane_roller_speeds,
    "Bagasse Speed (fpm)": bag_roller_speeds,
    "4th Speed (fpm)": four_roller_speeds,
    # Composition
    "Moisture A": moist_a_list,
    "Fiber A": fib_a_list,
    "Moisture B": moist_b_list,
    "Fiber B": fib_b_list,
    "Fiber Fill (lb/cuft)": fib_fill_list,
    "Moisture Density (lb/cuft)": rho_m_list,
    # Settings & Ratios
    "Top Float (in)": float_list,
    "Cane Ratio": cane_rat_list,
    "4th Ratio": four_rat_list,
    "Chute Ratio": chute_rat_list,
    "O-Factor": o_fact_list,
    "Bagasse Dyn Set (in)": bag_dyn_list,
    "Cane Dyn Set (in)": cane_dyn_list,
    "4th Dyn Set (in)": four_dyn_list,
    "Bagasse Static Set (in)": bag_static_list,
    "Cane Static Set (in)": cane_static_list,
    "Chute Opening (in)": chute_opening_list,
    "HP req per tfph": hp_fib_list,
    "HP Required": mill_hp_list,
    # Volume & Power
    "Escribed Volume Cane (cfm)": esv_cane_list,
    "Cane Compaction lbs / cu ft": compac_cane_list,
    "Escribed Volume Bagasse (cfm)": esv_bag_list,
    "Bagasse Compaction lb / cu ft": compac_bag_list,
    "Escribed Volume Turn Plate": tp_esv_list,
    "Turnplate Compaction lb / cu ft": compac_tp_list,
    "Escribed Volume 4th Roll (cfm)": esv_fourth_list,
    
    
}

df = pd.DataFrame(final_export_data)
df_transpose = df.T.reset_index()
        
df_transpose.to_excel("Mill_Settings.xlsx", index=False)
