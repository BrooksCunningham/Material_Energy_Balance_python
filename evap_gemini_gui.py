

# for a quadruple effect, no vapor bleeds
# use as a template

data = initial_balance(
    num_effects=4, 
    exh_press_psia=34.7, 
    last_eff_psia=1.92, 
    juice_in_tph=100, 
    juice_brix=12, 
    syrup_brix=60, 
    v1_bleed=(8959+3895+28108)/2000,
    v2_bleed=22120/2000,
    v3_bleed=0,
    effect_1_surface=7750,
    effect_2_surface=6250,
    effect_3_surface=3125,
    effect_4_surface=3125,
    effect_5_surface=0
    )

# setting up initial brix profile and streams
clear_juice = SugarStream('clear juice', 'j_005', data['juice_in_tph'], data['juice_brix'], 88, 225, data['vapor_press_effect_1'], 2)
conc_juice_1 = SugarStream('conc_1', 'j_006', data['conc_1_mass_flow'], data['conc_1_brix'], 88, 225, data['vapor_press_effect_1'], 2)
conc_juice_2 = SugarStream('conc 2', 'j_007', data['conc_2_mass_flow'], data['conc_2_brix'], 88, 225, data['vapor_press_effect_2'], 2)
conc_juice_3 = SugarStream('conc 3', 'j_008', data['conc_3_mass_flow'], data['conc_3_brix'], 88, 225, data['vapor_press_effect_3'], 2)
conc_juice_4 = SugarStream('conc 4', 'j_009', data['conc_4_mass_flow'], data['conc_4_brix'], 88, 225, data['vapor_press_effect_4'], 2)
syrup = SugarStream('syrup', 'sy_001', data['syrup_out_tph'], data['syrup_brix'], 88, 140, data['vapor_press_effect_4'], 2)

# setting up evaporators
effect_1 = Evaporator('effect 1', 'ev_001', data['surf_area_effect_1'], data['vapor_press_effect_1'], 20000)
effect_2 = Evaporator('effect 2', 'ev_002', data['surf_area_effect_2'], data['vapor_press_effect_2'], 20000)
effect_3 = Evaporator('effect 3', 'ev_003', data['surf_area_effect_3'], data['vapor_press_effect_3'], 20000)
effect_4 = Evaporator('effect 4', 'ev_004', data['surf_area_effect_4'], data['vapor_press_effect_4'], 20000)

# initial exhaust in
exhaust = SteamStream('exhaust', 'exh_001', data['exhaust_estim_tph'], data['exhaust_press_psia'], 0)
print('initial exhaust')
print(exhaust.mass_flow_tph)
print('\n')

#v1 = SteamStream("V1", 'v_001', )

# begin iterations...
iteration = 1
while iteration < 100:
    # first effect
    effect_1.heat_duty(steam_in_tph=exhaust.mass_flow_tph, steam_latent_heat=exhaust.latent_heat)
    effect_1.heat_for_evaporation(clear_juice.mass_flow_tph, clear_juice.temp, conc_juice_1.boil_temp_liq, clear_juice.cp)
    effect_1.tons_evaporated(conc_juice_1.latent_heat)
    effect_1.tons_conc_out(clear_juice.mass_flow_tph)
    effect_1.tons_vap_to_next_eff(data['v1_bleed'])
    conc_juice_1.evaporate(effect_1.conc_out_tph, effect_1.vapor_pressure)
    
    # second effect
    effect_2.heat_duty(steam_in_tph=effect_1.vap_to_next_eff_tph, steam_latent_heat=conc_juice_1.latent_heat)
    effect_2.heat_for_evaporation(conc_juice_1.mass_flow_tph, conc_juice_1.boil_temp_liq, conc_juice_2.boil_temp_liq, conc_juice_1.cp)
    effect_2.tons_evaporated(conc_juice_2.latent_heat)
    effect_2.tons_conc_out(conc_juice_1.mass_flow_tph)
    effect_2.tons_vap_to_next_eff(data['v2_bleed'])
    conc_juice_2.evaporate(effect_2.conc_out_tph, effect_2.vapor_pressure)

    # third effect
    effect_3.heat_duty(steam_in_tph=effect_2.vap_to_next_eff_tph, steam_latent_heat=conc_juice_2.latent_heat)
    effect_3.heat_for_evaporation(conc_juice_2.mass_flow_tph, conc_juice_2.boil_temp_liq, conc_juice_3.boil_temp_liq, conc_juice_2.cp)
    effect_3.tons_evaporated(conc_juice_3.latent_heat)
    effect_3.tons_conc_out(conc_juice_2.mass_flow_tph)
    effect_3.tons_vap_to_next_eff(data['v3_bleed'])
    conc_juice_3.evaporate(effect_3.conc_out_tph, effect_3.vapor_pressure)

    # fourth effect
    effect_4.heat_duty(steam_in_tph=effect_3.vap_to_next_eff_tph, steam_latent_heat=conc_juice_3.latent_heat)
    effect_4.heat_for_evaporation(conc_juice_3.mass_flow_tph, conc_juice_3.boil_temp_liq, conc_juice_4.boil_temp_liq, conc_juice_3.cp)
    effect_4.tons_evaporated(conc_juice_4.latent_heat)
    effect_4.tons_conc_out(conc_juice_3.mass_flow_tph)
    conc_juice_4.evaporate(effect_4.conc_out_tph, effect_4.vapor_pressure)
    
    # adjust exhaust
    evaporation_calc = clear_juice.mass_flow_tph - conc_juice_4.mass_flow_tph
    difference = evaporation_calc - data['total_evaporation']
    adjustment = difference / 10
    exhaust_tph = exhaust.mass_flow_tph - adjustment
    exhaust.change_flow(exhaust_tph)

    # adjust pressure profile
    effect_1.dessin_u(conc_juice_1.brix, exhaust.sat_temp, conc_juice_1.latent_heat)
    effect_1.u_calc(conc_juice_1.boil_temp_liq, exhaust.sat_temp)
    ratio_effect_1 = effect_1.heat_trans_coef / effect_1.dessin_coefficient

    effect_2.dessin_u(conc_juice_2.brix, conc_juice_1.sat_temp, conc_juice_2.latent_heat)
    effect_2.u_calc(conc_juice_2.boil_temp_liq, conc_juice_1.sat_temp)
    ratio_effect_2 = effect_2.heat_trans_coef / effect_2.dessin_coefficient

    effect_3.dessin_u(conc_juice_3.brix, conc_juice_2.sat_temp, conc_juice_3.latent_heat)
    effect_3.u_calc(conc_juice_3.boil_temp_liq, conc_juice_2.sat_temp)
    ratio_effect_3 = effect_3.heat_trans_coef / effect_3.dessin_coefficient

    effect_4.dessin_u(conc_juice_4.brix, conc_juice_3.sat_temp, conc_juice_4.latent_heat)
    effect_4.u_calc(conc_juice_4.boil_temp_liq, conc_juice_3.sat_temp)
    ratio_effect_4 = effect_4.heat_trans_coef / effect_4.dessin_coefficient
    
    average_u_ratio = (
        (ratio_effect_1
        + ratio_effect_2
        + ratio_effect_3
        + ratio_effect_4)
        / data['num_effects']
    )
   
    press_effect_1 = effect_1.vapor_pressure * ((average_u_ratio / ratio_effect_1) ** 0.1)
    press_effect_2 = effect_2.vapor_pressure * ((average_u_ratio / ratio_effect_2) ** 0.1)
    press_effect_3 = effect_3.vapor_pressure * ((average_u_ratio / ratio_effect_3) ** 0.1)
    # press_effect_4 = effect_4.vapor_pressure * ((average_u_ratio / ratio_effect_4) ** 0.1)

    effect_1.adjust_pressure(press_effect_1)
    effect_2.adjust_pressure(press_effect_2)
    effect_3.adjust_pressure(press_effect_3)
    # effect_4.adjust_pressure(press_effect_4) turn on for quintuple

    # move iteration along
    iteration += 1

exhaust.display_propterties()
clear_juice.display_propterties()
effect_1.display_properties()
conc_juice_1.display_propterties()
effect_2.display_properties()
conc_juice_2.display_propterties()
effect_3.display_properties()
conc_juice_3.display_propterties()
effect_4.display_properties()
conc_juice_4.display_propterties()
syrup.display_propterties()
