import math
import pandas as pd
import CoolProp.CoolProp as CP

# This is a Juice Heater Calculator for St mary sugar cooperative's heater set up

# Get inputs
grnd_rate = 18000 # Tons of Cane Per Day
mj_perc_cane = 120 # Mixed Juice % Cane, usually around 120
T_in = 90  # Inlet Juice Temperature
T_out = 216 # Outlet Juice Temperature
cp = 0.92  # specific heat capacity, usually 0.92
U = 230  # Heat Transfer Coefficient 
p_steam = 6 # heating steam pressure in psig.. Exhaust usually 13-15, V1 usually 6-7, V2 usually 0-2
SG = 1.04 # specific gravity usually 1.04
# Data is listed as follows [H1, H2, H3, H4, H5, H6]
htr_number_list = [1, 2, 3, 4, 5, 6]
jhtr_tub_leng_list = [20, 20, 20, 20, 20, 20] # Juice Heater Tube Length in ft
tub_OD_list = [1.75, 1.75, 1.75, 1.75, 1.75, 1.75] # Tube OD in inches
tub_per_pass_list = [18, 18, 28, 18, 18, 28] # Tubes Per Pass
tub_thic_list = [0.063, 0.063, 0.063, 0.063, 0.063, 0.063] # Tube Thickness in inches
num_of_pass_list = [20, 20, 20, 20, 20, 20] # Number of Passes
# Now we need to select which heaters are in use.. True = online, False = offline
            #   H1    H2    H3    H4    H5     H6
in_use_list = [True, True, True, True, False, False]

# Getting steam temperature from pressure
p_psig = p_steam
p_pa = (p_psig +14.696) * 6894.76 # convert to Pascals abs
temp_k = CP.PropsSI('T', 'P', p_pa, 'Q', 1, 'Water')
temp_f = (temp_k - 273.15) *9/5 + 32
print(f"Steam Temp: {temp_f:.2f} deg F")
T_stm = temp_f  # Heating steam temperature in deg F.. Exhaust usually 255, V1 about 230, V2 around 212

# Creating a Table
df = pd.DataFrame({
    'Heater_Number': htr_number_list,
    'Length': jhtr_tub_leng_list,
    'OD': tub_OD_list,
    'TPP': tub_per_pass_list,
    'Thickness': tub_thic_list,
    'Passes': num_of_pass_list,
    'In_Use': in_use_list
})

df['Internal_ID'] = df['OD'] - (2 * df['Thickness'])
df['Total_Tubes'] = df['TPP'] * df['Passes']
df['SA_sqft'] = df['OD'] * math.pi / 12 * df['Length'] * df['Total_Tubes']
df['Xs_area'] = df['Internal_ID']**2 / 4 * math.pi * df['TPP'] / 144
print(df.round({"SA_sqft":1}))

df['In_Use'] = in_use_list
active_heater = df[df['In_Use'] == True]
total_sa = active_heater['SA_sqft'].sum()
m_juic = grnd_rate / 24 * 2000 * mj_perc_cane / 100  # Juice Flow in lbs / hr
A_xs = active_heater['Xs_area'].sum()

Q = m_juic * cp * (T_out - T_in)  # The heat duty in BTU / hr
del_T1 = (T_stm - T_in)
del_T2 = (T_stm - T_out)
LMTD = (del_T1 - del_T2) / (math.log(del_T1 / del_T2))
A_req = Q / (U * LMTD)
gpm = m_juic / 8.3 / 60 / SG
cfps = gpm / 448.83 # cubic feet per sec
vel = cfps / A_xs # Juice velocity in feet per second

print(f"GPM: {gpm:.1f}")
print(f"Juice Velocity in ft / sec: {vel:.2f}")
print(f"LMTD: {LMTD:.1f}")
print(f"Total Heating Surface Required: {A_req:.1f} sqft")
print(f"Total Avtive Surface Area: {total_sa:.1f} sqft")
print(active_heater)
