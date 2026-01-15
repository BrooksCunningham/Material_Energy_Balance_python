from stream_and_unit_classes import SteamStream, Evaporator, SugarStream, SteamTurbine
from iapws import IAPWS97
import pandas as pd

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
# for testing we will use these numbers for bagasse...
mill_data = {}
mill_results = {}

mill_data['bagasse_percent_moisture'] = 49.0
mill_data['bagasse_percent_ash'] = 4.0
mill_results['bagasse_percent_brix'] = 3.0
mill_results['tons_bagasse_per_hour'] = 204

live_steam_main = SteamStream('live_steam_main', 'ls_001', 0, live_steam_main_psia, live_steam_deg_sh)
ghv_bagasse = (
    .4299 
    * (19605 
        - 196.05 * mill_data['bagasse_percent_moisture'] 
        - 196.05 * mill_data['bagasse_percent_ash']
        - 31.14 * mill_results['bagasse_percent_brix'])
) # gross heating value bagasse in btu
avg_boiler_efficiency = 65 # user input, don't forget
btu_per_lb_bagasse = ghv_bagasse * avg_boiler_efficiency / 100
btu_available_for_steam = ghv_bagasse * avg_boiler_efficiency / 100 * mill_results['tons_bagasse_per_hour'] * 2000
live_steam_enthalpy = live_steam_main.enthalpy
boiler_feed_water_temp = 235 # deg F, user input
boiler_feed_water_temp_kelvin = (boiler_feed_water_temp - 32) * 5 / 9 + 273
boiler_feed_water = IAPWS97(T=boiler_feed_water_temp_kelvin, x=0)
boiler_feed_water_enthalpy = boiler_feed_water.h * 0.429923 # btu / lb
heat_required_to_make_a_lb_of_steam = live_steam_enthalpy - boiler_feed_water_enthalpy
lbs_steam_available = btu_available_for_steam / heat_required_to_make_a_lb_of_steam
print(f"ghv bagasse {ghv_bagasse:,.2f}")
print(f"avg boiler efficiency {avg_boiler_efficiency:,.2f}")
print(f"btu per lb bagasse {btu_per_lb_bagasse:,.2f}")
print(f"btu available from bagasse {btu_available_for_steam:,.2f}")
print(f"live steam enthalpy {live_steam_main.enthalpy:,.2f}")
print(f"boiler feed water enthalpy {boiler_feed_water_enthalpy:,.2f}")
print(f"heat required to make a lb of steam {heat_required_to_make_a_lb_of_steam:,.2f}")
print(f"lbs steam availble {lbs_steam_available:,.2f}")

# Steam turbine questionaire
# cane preparation steam turbines
""" 
key to keep code concise
trb = turbine
ck = cane knife
cs = cane shredder
ml = mill
id = ID fan
fd = fd fan
pm = pump
ls = live steam
ex = exhaust steam
h = enthalpy
hp = horsepower
tf = tons fiber per hour
ef = issentropic efficiecy
ms = main steam
"""
# these will be user inputs
ck_trb_name_list = ['ck_trb_1', 'ck_trb_2', 'ck_trb_3', 'cs_trb_1', 'cs_trb_2']
ck_trb_hp_tf_list = [16, 16, 16, 20, 20] # horse power per ton fiber per hour
ck_trb_ef_list = [0.5, 0.5, 0.5, 0.5, 0.5] # issentropic efficiency
ck_tf_to_trb_list = [100, 100, 100, 0, 0] # tons fiber per hour to turbine

df_cane_prep = pd.DataFrame({
    'Turbine Name': ck_trb_name_list,
    'HP/Ton Fiber/hr': ck_trb_hp_tf_list,
    'Issentropic Efficiency': ck_trb_ef_list,
    'Tons Fiber/Hr': ck_tf_to_trb_list
})

df_cane_prep['Horse Power Demand'] = df_cane_prep['HP/Ton Fiber/hr'] * df_cane_prep['Tons Fiber/Hr']

#df_cane_prep['']

ls_mn_deg_sh = 0 # prompt user to ask for degrees of super heat
if ls_mn_deg_sh > 0:
    ls_mn_sat = IAPWS97(P=live_steam_main_psia * 0.00689476, x=1)
    ls_mn_sat_temp = ls_mn_sat.T
    ls_mn_temp = ls_mn_sat_temp + ((ls_mn_deg_sh - 32) * 5 / 9 + 273.15)
    ls_mn = IAPWS97(P=live_steam_main_psia * 0.00689476, T=ls_mn_temp)
else:
    ls_mn = IAPWS97(P=live_steam_main_psia * 0.00689476, x=1)

    
ls_ck = IAPWS97(P=live_steam_knives_psia * 0.00689476, h=ls_mn.h)
ex_ck_ideal = IAPWS97(P=exhaust_steam_knives_psia * 0.00689476, s=ls_ck.s)
delta_h_ideal = ls_ck.h - ex_ck_ideal.h # kj/kg
delta_h_ideal_btus = delta_h_ideal * 0.429923 # btu/lb
delta_h_ideal_hp = delta_h_ideal_btus / 2544 # hp for 1 lb steam per hour
ideal_specific_steam_rate = 2544 / delta_h_ideal_btus # lb/hp-hr
print(f"live steam knives enthalpy {ls_ck.h:,.2f}")
print(f"exhaust steam knives enthalpy {ex_ck_ideal.h:,.2f}")
print(f"delta_h_ideal {delta_h_ideal:,.2f}")
print(f"delta_h_ideal_btus {delta_h_ideal_btus:,.2f}")
print(f"delta_h_ideal_hp {delta_h_ideal_hp:,.4f}")
print(f"ideal specific steam rate {ideal_specific_steam_rate:,.2f}")
# note that 1 hp equals 2544 btu / hr
# 1 kj / kg = 0.429923 btu / lb

df_cane_prep['Specific Steam Rate lb/(hr*hp)'] = (
    ideal_specific_steam_rate 
    / df_cane_prep['Issentropic Efficiency']
)

df_cane_prep['Steam Required lb/hr'] = df_cane_prep['Horse Power Demand'] * df_cane_prep['Specific Steam Rate lb/(hr*hp)']
df_cane_prep['Exhaust Steam Enthalpy btu/lb'] = (
    0.429923 * (ls_ck.h - (delta_h_ideal * df_cane_prep['Issentropic Efficiency']))
)

def get_quality(h_btu):
    h_kjkg = h_btu / 0.429923
    p_mpa = exhaust_steam_knives_psia * 0.00689476
    state = IAPWS97(P=p_mpa, h=h_kjkg)
    return state.x

df_cane_prep['Exhaust Quality'] = df_cane_prep['Exhaust Steam Enthalpy btu/lb'].apply(get_quality)
df_cane_prep['Exhaust available lb/hr at x=1'] = df_cane_prep['Exhaust Quality'] * df_cane_prep['Steam Required lb/hr']
df_cane_prep_filter = df_cane_prep.drop(columns=['Exhaust Steam Enthalpy btu/lb'])
print(df_cane_prep)

# Mill Turbines Data, user inputs
mill_trb_name_list = ['Mill 1', 'Mill 2', 'Mill 3', 'Mill 4', 'Mill 5', 'Mill 6']
mill_trb_hp_tf_list = [18, 16, 16, 16, 16, 18]
mill_trb_ef_list = [0.5] * 6
mill_tf_to_trb_list = [100] * 6 # Assuming 100 tons fiber/hr for testing

df_mill_turbines = pd.DataFrame({
    'Turbine Name': mill_trb_name_list,
    'HP/Ton Fiber/hr': mill_trb_hp_tf_list,
    'Issentropic Efficiency': mill_trb_ef_list,
    'Tons Fiber/Hr': mill_tf_to_trb_list
})

df_mill_turbines['Horse Power Demand'] = df_mill_turbines['HP/Ton Fiber/hr'] * df_mill_turbines['Tons Fiber/Hr']

# Steam calculations for Mills
ls_mills = IAPWS97(P=live_steam_mills_psia * 0.00689476, h=ls_mn.h)
ex_mills_ideal = IAPWS97(P=exhaust_steam_mills_psia * 0.00689476, s=ls_mills.s)
delta_h_ideal_mills = ls_mills.h - ex_mills_ideal.h # kj/kg
delta_h_ideal_mills_btus = delta_h_ideal_mills * 0.429923 # btu/lb
ideal_ssr_mills = 2544 / delta_h_ideal_mills_btus # lb/hp-hr

print(f"live steam mills enthalpy {ls_mills.h:,.2f}")
print(f"exhaust steam mills enthalpy {ex_mills_ideal.h:,.2f}")
print(f"delta_h_ideal_mills_btus {delta_h_ideal_mills_btus:,.2f}")
print(f"ideal specific steam rate mills {ideal_ssr_mills:,.2f}")

df_mill_turbines['Specific Steam Rate lb/(hr*hp)'] = (
    ideal_ssr_mills 
    / df_mill_turbines['Issentropic Efficiency']
)

df_mill_turbines['Steam Required lb/hr'] = df_mill_turbines['Horse Power Demand'] * df_mill_turbines['Specific Steam Rate lb/(hr*hp)']
df_mill_turbines['Exhaust Steam Enthalpy btu/lb'] = (
    0.429923 * (ls_mills.h - (delta_h_ideal_mills * df_mill_turbines['Issentropic Efficiency']))
)

def get_quality_mills(h_btu):
    h_kjkg = h_btu / 0.429923
    p_mpa = exhaust_steam_mills_psia * 0.00689476
    state = IAPWS97(P=p_mpa, h=h_kjkg)
    return state.x

df_mill_turbines['Exhaust Quality'] = df_mill_turbines['Exhaust Steam Enthalpy btu/lb'].apply(get_quality_mills)
df_mill_turbines['Exhaust available lb/hr at x=1'] = df_mill_turbines['Exhaust Quality'] * df_mill_turbines['Steam Required lb/hr']
df_mill_turbines_filter = df_mill_turbines.drop(columns=['Exhaust Steam Enthalpy btu/lb'])
print(df_mill_turbines_filter)

# id, fd, pump turbines, will be user inputs later
other_trb_list = [
 'id_fan_123_trb',
 'id_fan_4_trb', 
 'id_fan_5_trb', 
 'id_fan_6_trb', 
 'id_fan_7_trb', 
 'id_fan_8_trb', 
 'fd_fan_7_trb', 
 'fd_fan_8_trb',
 'bfw_pm_1_trb',
 'bfw_pm_2_trb',
 'bfw_pm_3_trb',
 'jc_pm_1_trb',
 'jc_pm_2_trb'
 ]

other_trb_hp_list = [
    750,
    235,
    400,
    795,
    1200,
    1300,
    233,
    350,
    400,
    400,
    400,
    400,
    0
]

other_trb_ef_list = [
    0.5,
    0.5,
    0.5,
    0.5,
    0.5,
    0.5,
    0.4,
    0.4,
    0.4,
    0.4,
    0.4,
    0.4,
    0.4
]

df_other_turbines = pd.DataFrame({
    'Turbine Name': other_trb_list,
    'Horse Power Demand': other_trb_hp_list,
    'Issentropic Efficiency': other_trb_ef_list
})

ls_other = IAPWS97(P=live_steam_other_turbines_psia * 0.00689476, h=ls_mn.h)
ex_other_ideal = IAPWS97(P=exhaust_steam_other_turbines_psia * 0.00689476, s=ls_other.s)
delta_h_ideal_other = ls_other.h - ex_other_ideal.h # kj/kg
delta_h_ideal_other_btus = delta_h_ideal_other * 0.429923 # btu/lb
ideal_ssr_other = 2544 / delta_h_ideal_other_btus # lb/hp-hr
df_other_turbines['Specific Steam Rate lb/(hr*hp)'] = (
    ideal_ssr_other 
    / df_other_turbines['Issentropic Efficiency']
)
df_other_turbines['Steam Required lb/hr'] = df_other_turbines['Horse Power Demand'] * df_other_turbines['Specific Steam Rate lb/(hr*hp)']
def get_exhaust_quality(iss_eff):
    h_ex_kjkg = ls_other.h - (delta_h_ideal_other * iss_eff)
    p_mpa = exhaust_steam_other_turbines_psia * 0.00689476
    return IAPWS97(P=p_mpa, h=h_ex_kjkg).x

df_other_turbines['Exhaust Quality'] = df_other_turbines['Issentropic Efficiency'].apply(get_exhaust_quality)
df_other_turbines['Exhaust available lb/hr at x=1'] = df_other_turbines['Exhaust Quality'] * df_other_turbines['Steam Required lb/hr']

print(df_other_turbines)

ls_req_cane_prep = df_cane_prep['Steam Required lb/hr'].sum()
ls_req_mills = df_mill_turbines['Steam Required lb/hr'].sum()
ls_req_other = df_other_turbines['Steam Required lb/hr'].sum()
ls_req_equip = ls_req_cane_prep + ls_req_mills + ls_req_other

ex_available_from_trb = (
    df_cane_prep_filter['Exhaust available lb/hr at x=1'].sum() 
    + df_mill_turbines_filter['Exhaust available lb/hr at x=1'].sum() 
    + df_other_turbines['Exhaust available lb/hr at x=1'].sum()
)

print(f"ls_req_cane_prep {ls_req_cane_prep:,.2f}")
print(f"ls_req_mills {ls_req_mills:,.2f}")
print(f"ls_req_other {ls_req_other:,.2f}")
print(f"ls_req_total_equip {ls_req_equip:,.2f}")
print(f"ex_available_from_trb {ex_available_from_trb:,.2f}")

# exhaust steam energy balance
