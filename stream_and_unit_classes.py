from iapws import IAPWS97

 # Boiling point elevation
def calculate_bpe1(bx):
    bpe1 = 4.266667*bx / (100 - bx)
    return bpe1

def calculate_bpe2(Lvl, brix, T_Vap):
    
        # Polynomial for Brix (C64)
    brix_poly = (
        0.99991 + 
        0.0038008 * brix + 
        0.000012662 * (brix ** 2) + 
        0.00000009596 * (brix ** 3)
    )
    
    # Polynomial for Vapor Temperature (C57)
    temp_poly = (
        5.314 - 
        0.07135 * T_Vap + 
        0.00033908 * (T_Vap ** 2) - 
        0.00000055728 * (T_Vap ** 3)
    )
    
    # Combine terms (0.5 * 12 = 6)
    calculation = Lvl * 6 * brix_poly * temp_poly
    
    # IF(calculation < 1, 1, calculation) logic
    return max(1, calculation)

# Example Usage:
#result = calculate_bpe2(Lvl=2, brix=60, T_Vap=124)
#print(result)

def calculate_bpe(bpe1, bpe2):
    bpe = bpe1 + bpe2
    return bpe


class SugarStream:
    """A class to get all parameters for a sugar stream
    like juice, syrup, clearjuice, concentrate, molasses, ect..."""
    def __init__(self, name, tag='none', mass_flow_tph=0, brix=0, purity=88,
                 temperature_deg_F=90, pressure_psia=14.696, liquid_level=0):
        """Getting initial stream properties"""
        self.name = name
        self.tag = tag
        self.mass_flow_tph = mass_flow_tph
        self.lb_per_hr = self.mass_flow_tph * 2000
        self.brix = brix
        self.purity = purity
        self.temp = temperature_deg_F   # default to 90 deg F
        self.press = pressure_psia     # default to 14.696 psia
        self.cp = 0.9964 - 0.005656 * self.brix
        self.spec_grav = (
            (62.2511 
            + 0.24081 * self.brix 
            + 0.0007902404 * self.brix**2
            + 0.00000423954  * self.brix**3
            - 0.00000001657193 * self.brix**4)
            / 62.4
            ) # specific gravity for 68 deg F
        self.tons_solids = self.mass_flow_tph * self.brix / 100
        self.tons_pol = self.tons_solids * self.purity / 100
        self.pol_perc = self.tons_pol / self.mass_flow_tph * 100
        self.vol_cuft_hr = self.mass_flow_tph * 2000 / (self.spec_grav * 62.4)
        self.gpm = self.vol_cuft_hr * 0.1246753247
        self.psig = self.press - 14.696
        self.inches_vac_hg = 29.921368857 - (self.press * 2.0360212886)
        self.liquid_level = liquid_level # in feet, for evaporator calculations

        """getting steam properties"""
        self.megapascal = self.press * 0.00689476
        self.kelvin = (self.temp - 32) * 5 / 9 + 273.15
        sat_steam = IAPWS97(P=self.megapascal, x=1)
        sat_liquid = IAPWS97(P=self.megapascal, x=0)
        latent_heat = sat_steam.h - sat_liquid.h
        sat_temp = sat_steam.T
        self.latent_heat = latent_heat * 0.429923 # btu / lb
        self.sat_temp = (sat_temp - 273.15) * 9 / 5 + 32

        """now for boiling point elevation"""
        self.bpe_brx = calculate_bpe1(self.brix)
        self.bpe_head = calculate_bpe2(self.liquid_level, self.brix, self.sat_temp)
        self.bpe_total = calculate_bpe(self.bpe_brx, self.bpe_head)
        self.boil_temp_liq = self.bpe_total + self.sat_temp

    def evaporate(self, new_mass_flow, new_press):
        """recalculates all neccesary properties from evaporation"""
        self.mass_flow_tph = new_mass_flow
        self.lb_per_hr = self.mass_flow_tph * 2000
        self.brix = self.tons_solids / self.mass_flow_tph * 100
        self.press = new_press
        self.cp = 0.9964 - 0.005656 * self.brix
        self.spec_grav = (
            (62.2511 
            + 0.24081 * self.brix 
            + 0.0007902404 * self.brix**2
            + 0.00000423954  * self.brix**3
            - 0.00000001657193 * self.brix**4)
            / 62.4
            ) # specific gravity for 68 deg F
        self.pol_perc = self.tons_pol / self.mass_flow_tph * 100
        self.vol_cuft_hr = self.mass_flow_tph * 2000 / (self.spec_grav * 62.4)
        self.gpm = self.vol_cuft_hr * 0.1246753247
        self.psig = self.press - 14.696
        self.inches_vac_hg = 29.921368857 - (self.press * 2.0360212886)

        """getting steam properties"""
        self.megapascal = self.press * 0.00689476
        self.kelvin = (self.temp - 32) * 5 / 9 + 273.15
        sat_steam = IAPWS97(P=self.megapascal, x=1)
        sat_liquid = IAPWS97(P=self.megapascal, x=0)
        latent_heat = sat_steam.h - sat_liquid.h
        sat_temp = sat_steam.T
        self.latent_heat = latent_heat * 0.429923 # btu / lb
        self.sat_temp = (sat_temp - 273.15) * 9 / 5 + 32

        """now for boiling point elevation"""
        self.bpe_brx = calculate_bpe1(self.brix)
        self.bpe_head = calculate_bpe2(self.liquid_level, self.brix, self.sat_temp)
        self.bpe_total = calculate_bpe(self.bpe_brx, self.bpe_head)
        self.boil_temp_liq = self.bpe_total + self.sat_temp
        self.temp = self.boil_temp_liq # avoid confusion, these will be same during evaporation

    def display_propterties(self):
        """displays all the stream properties"""
        print(f"Stream name:                    {self.name.title()}")
        print(f"Stream tag:                     {self.tag}")
        print(f"mass flow tph:                  {self.mass_flow_tph:,.3f}")
        print(f"mass flow lb/hr:                {self.lb_per_hr:,.1f}")
        print(f"Brix %:                         {self.brix:.2f}")
        print(f"Pol %:                          {self.pol_perc:.2f}")
        print(f"Purity:                         {self.purity:.2f}")
        print(f"Tons solids per hour:           {self.tons_solids:.3f}")
        print(f"Tons pol per hour:              {self.tons_pol:.3f}")
        print(f"Temperature:                    {self.temp:.2f}\u1d52F")
        print(f"Saturation Temp Water:          {self.sat_temp:.2f}\u1d52F")
        print(f"Liquid Level:                   {self.liquid_level}")
        print(f"bpe brix:                       {self.bpe_brx:.1f}")
        print(f"bpe head:                       {self.bpe_head:.1f}")
        print(f"bpe total:                      {self.bpe_total:.1f}")
        print(f"liquid boiling temp:            {self.boil_temp_liq:.1f}")
        print(f"Pressure psia:                  {self.press:.2f}")
        print(f'         psig:                  {self.psig:.2f}')
        print(f'         "Hg vac:               {self.inches_vac_hg:.2f}')
        print(f"Specific Gravity at 68 deg F:   {self.spec_grav:.4f}")
        print(f"Volumetric flow cu ft / hr:     {self.vol_cuft_hr:,.2f} ")
        print(f"Gallons per minute:             {self.gpm:,.2f}")
        print(f"cp BTU/(lb * deg F):            {self.cp:.3f} ")
        print(f"Latent heat btu/lb:             {self.latent_heat:.2f}")
        print('\n')

class SteamStream:
    """this class defines a steam flow stream"""
    def __init__(self, name, tag, flow_tph, pressure_psia, deg_superheat=0):
        """initiating properties, assumes no superheat unless value inputted"""
        self.name = name
        self.tag = tag
        self.mass_flow_tph = flow_tph
        self.lbs_per_hr = self.mass_flow_tph * 2000
        self.pressure_psia = pressure_psia
        self.megapascal = self.pressure_psia * 0.00689476
        sat_steam = IAPWS97(P=self.megapascal, x=1)
        sat_liquid = IAPWS97(P=self.megapascal, x=0)
        latent_heat = sat_steam.h - sat_liquid.h
        sat_temp = sat_steam.T
        self.latent_heat = latent_heat * 0.429923 # btu / lb
        self.sat_temp = (sat_temp - 273.15) * 9 / 5 + 32
        self.deg_superheat = deg_superheat
        if self.deg_superheat > 0:
            self.temp = self.sat_temp + self.deg_superheat
            self.t_kelvin = (self.temp - 32) * 5 / 9 + 273.15
            sh_steam = IAPWS97(P=self.megapascal, T=self.t_kelvin)
            enthalpy_metric = sh_steam.h
            entropy_metric = sh_steam.s
        else:
            self.temp = self.sat_temp
            self.t_kelvin = (self.temp - 32) * 5 / 9 + 273.15
            sh_steam = IAPWS97(P=self.megapascal, x=1)
            enthalpy_metric = sh_steam.h
            entropy_metric = sh_steam.s
        self.enthalpy = enthalpy_metric * 0.429923 # btu / lb
        self.entropy = entropy_metric * 0.2388458966 # btu / (lb R)
    
    def change_flow(self, new_flow_tph):
        self.mass_flow_tph = new_flow_tph
        self.lbs_per_hr = self.mass_flow_tph * 2000
    
    def display_propterties(self):
        """displays all the properties"""
        print(f"Name: {self.name}")
        print(f"stream tag: {self.tag}")
        print(f"Mass Flow (TPH):        {self.mass_flow_tph:,.2f}")
        print(f"Mass Flow (lb/hr):      {self.lbs_per_hr:,.2f}")
        print(f"Pressure (psia):        {self.pressure_psia:,.2f}")
        #print(f"Pressure (MPa):         {self.megapascal:,.2f}")
        print(f"Latent Heat (BTU/lb):   {self.latent_heat:,.2f}")
        print(f"Saturation Temp (°F):   {self.sat_temp:,.2f}")
        print(f"Superheat (°F):         {self.deg_superheat:,.2f}")
        print(f"Steam Temp (°F):        {self.temp:,.2f}")
        #print(f"Steam Temp (K):         {self.t_kelvin:,.2f}")
        print(f"Enthalpy (BTU/lb):      {self.enthalpy:,.2f}")
        print(f"Entropy (BTU/lb·R):     {self.entropy:,.2f}")
        print('\n')


class Evaporator:
    """This class will get all parameters for a robert evaporator,
    this will work on other evaporator styles, but intended for robert"""

    def __init__(self, name, unit_tag, heating_surface_sqft, vapor_pressure, dessin_constant):
        """Initialize the properties of the evaporator"""
        self.name = name
        self.tag = unit_tag
        self.heating_surface_sqft = heating_surface_sqft
        self.vapor_pressure = vapor_pressure
        self.dessin_constant = dessin_constant

    def heat_duty(self, steam_in_tph, steam_latent_heat):
        """calculates heat transferred from steam to juice"""
        self.heat_xfered = steam_in_tph * 2000 * steam_latent_heat
        
    def dessin_u(self, brix_out, steam_temp, vapor_latent_heat):
        """calculates dessin heat transfer coefficient"""
        self.dessin_coefficient = (
            (100 - brix_out) 
            * (steam_temp - 130) 
            * vapor_latent_heat 
            / self.dessin_constant
            )

    def u_calc(self, temp_juice, temp_steam):
        """calculates actual heat transfer coefficient"""
        self.heat_trans_coef = (
            self.heat_xfered 
            / self.heating_surface_sqft 
            / (temp_steam - temp_juice)
            )

    def heat_for_evaporation(self, juice_in_tph, juice_temp_in, conc_out_temp, juice_in_cp):
        """Calculates heat available for evaporation"""
        q_dot_steam = self.heat_xfered
        m_dot = juice_in_tph * 2000
        cp = juice_in_cp
        del_t = conc_out_temp - juice_temp_in
        q_dot_sensible = m_dot * cp * del_t
        self.heat_for_evap = (
            q_dot_steam 
            - q_dot_sensible
        ) # btus

    def tons_evaporated(self, vapor_latent_heat):
        """calculates the tons water evaporated"""
        self.tons_evap = (
            self.heat_for_evap 
            / vapor_latent_heat
            / 2000
        )

    def tons_conc_out(self, juice_in_tph):
        """calculates outlet flow rate"""
        self.conc_out_tph = (
            juice_in_tph
            - self.tons_evap
        )

    def tons_vap_to_next_eff(self, vapor_bleed_tph):
        """calculates the vapors fed to next effect"""
        self.vapor_bleed = vapor_bleed_tph
        self.vap_to_next_eff_tph = self.tons_evap - self.vapor_bleed
    
    def adjust_pressure(self, new_pressure):
        """changes evaporator vapor pressure"""
        self.vapor_pressure = new_pressure
    
    def display_properties(self):
        """displays all evaporator properties"""
        print(f"Name:                      {self.name}")
        print(f"Tag:                       {self.tag}")
        print(f"Heating Surface (sq ft):   {self.heating_surface_sqft:,.2f}")
        print(f"Vapor Pressure:            {self.vapor_pressure:,.2f}")
        print(f"Dessin Constant:           {self.dessin_constant:,.2f}")

        if hasattr(self, "heat_xfered"):
            print(f"Heat Transferred (BTU):    {self.heat_xfered:,.2f}")

        if hasattr(self, "dessin_coefficient"):
            print(f"Dessin U Coefficient:     {self.dessin_coefficient:,.2f}")

        if hasattr(self, "heat_trans_coef"):
            print(f"Actual U (BTU/hr·ft²·°F):  {self.heat_trans_coef:,.2f}")

        if hasattr(self, "heat_for_evap"):
            print(f"Heat for Evap (BTU):       {self.heat_for_evap:,.2f}")

        if hasattr(self, "tons_evap"):
            print(f"Tons Evaporated (TPH):    {self.tons_evap:,.3f}")

        if hasattr(self, "conc_out_tph"):
            print(f"Concentrated Out (TPH):   {self.conc_out_tph:,.3f}")

        if hasattr(self, "vapor_bleed"):
            print(f"Vapor Bleed (TPH):        {self.vapor_bleed:,.3f}")

        if hasattr(self, "vap_to_next_eff_tph"):
            print(f"Vapor to Next Eff (TPH):  {self.vap_to_next_eff_tph:,.3f}")
        
        print('\n')

from iapws import IAPWS97


class SteamTurbine:
    """
    Steam Turbine performance model using IAPWS97

    All INPUTS and OUTPUTS are in ENGLISH UNITS
    Internally converts to SI units for IAPWS97
    """

    def __init__(
        self,
        inlet_pressure_psia,
        inlet_temperature_F,
        exhaust_pressure_psia,
        isentropic_efficiency,
        horsepower
    ):
        self.P1_psia = inlet_pressure_psia
        self.T1_F = inlet_temperature_F
        self.P2_psia = exhaust_pressure_psia
        self.eta_is = isentropic_efficiency
        self.hp = horsepower

        self._calculate()

    # -----------------------------
    # Unit Conversions
    # -----------------------------
    @staticmethod
    def psia_to_mpa(p_psia):
        return p_psia * 0.00689476

    @staticmethod
    def F_to_K(T_F):
        return (T_F - 32) * 5 / 9 + 273.15

    @staticmethod
    def kJkg_to_BTUlb(h):
        return h * 0.429922614

    @staticmethod
    def BTUlb_to_kJkg(h):
        return h / 0.429922614

    # -----------------------------
    # Main Calculation
    # -----------------------------
    def _calculate(self):
        # ---- Inlet State ----
        P1 = self.psia_to_mpa(self.P1_psia)
        T1 = self.F_to_K(self.T1_F)

        self.state1 = IAPWS97(P=P1, T=T1)

        h1 = self.state1.h      # kJ/kg
        s1 = self.state1.s      # kJ/kg-K

        # ---- Isentropic Exhaust ----
        P2 = self.psia_to_mpa(self.P2_psia)
        self.state2s = IAPWS97(P=P2, s=s1)
        h2s = self.state2s.h

        # ---- Actual Exhaust ----
        h2 = h1 - self.eta_is * (h1 - h2s)
        self.state2 = IAPWS97(P=P2, h=h2)

        # ---- Convert Properties to English Units ----
        self.h1_BTUlb = self.kJkg_to_BTUlb(h1)
        self.h2_BTUlb = self.kJkg_to_BTUlb(h2)
        self.delta_h_BTUlb = self.h1_BTUlb - self.h2_BTUlb

        # ---- Power & Steam Rate ----
        # 1 hp = 2545 BTU/hr
        self.specific_steam_rate = 2545 / self.delta_h_BTUlb  # lb/hp-hr
        self.steam_flow_lbh = self.specific_steam_rate * self.hp

    # -----------------------------
    # Results Dictionary
    # -----------------------------
    def results(self):
        return {
            "Inlet Pressure (psia)": self.P1_psia,
            "Inlet Temperature (F)": self.T1_F,
            "Inlet Enthalpy (BTU/lb)": self.h1_BTUlb,
            "Inlet Entropy (BTU/lb-R)": self.state1.s * 0.238845897,

            "Exhaust Pressure (psia)": self.P2_psia,
            "Exhaust Quality": getattr(self.state2, "x", None),
            "Exhaust Enthalpy (BTU/lb)": self.h2_BTUlb,

            "Isentropic Efficiency": self.eta_is,
            "Enthalpy Drop (BTU/lb)": self.delta_h_BTUlb,

            "Specific Steam Rate (lb/hp-hr)": self.specific_steam_rate,
            "Steam Required (lb/hr)": self.steam_flow_lbh,
            "Horsepower": self.hp,
        }


# testing below

# get inital steam inlet flow and pressure profile
"""
def initial_balance(
    num_effects = 4,
    exh_press_psia = 30,
    last_eff_psia = 2.2,
    juice_in_tph = 500,
    juice_brix = 14,
    syrup_brix = 65,
    v1_bleed = 0,
    v2_bleed = 0,
    v3_bleed = 0,
    effect_1_surface = 25000,
    effect_2_surface = 25000,
    effect_3_surface = 25000,
    effect_4_surface = 25000,
): """
"""Calculates initial values for the trial and error balance"""

"""  tons_solids = juice_brix * juice_in_tph / 100
    syrup_out_tph = juice_brix / syrup_brix * juice_in_tph
    total_evaporation = juice_in_tph - syrup_out_tph
    x_factor = (total_evaporation - v1_bleed - v2_bleed * 2 - v3_bleed * 3) / num_effects
    exhaust_estim_tph = x_factor + v1_bleed + v2_bleed + v3_bleed
    p_drop_per_effect = (exh_press_psia - last_eff_psia) / num_effects
    vapor_press_effect_1 = exh_press_psia - p_drop_per_effect
    vapor_press_effect_2 = vapor_press_effect_1 - p_drop_per_effect
    vapor_press_effect_3 = vapor_press_effect_2 - p_drop_per_effect
    vapor_press_effect_4 = vapor_press_effect_3 - p_drop_per_effect
    vapor_press_effect_5 = vapor_press_effect_4 - p_drop_per_effect
    effect_1_evaporation = exhaust_estim_tph
    effect_2_evaporation = effect_1_evaporation - v1_bleed
    effect_3_evaporation = effect_2_evaporation - v2_bleed
    effect_4_evaporation = effect_3_evaporation - v3_bleed
    effect_5_evaporation = effect_4_evaporation
    conc_1_mass_flow = juice_in_tph - effect_1_evaporation
    conc_2_mass_flow = conc_1_mass_flow - effect_2_evaporation
    conc_3_mass_flow = conc_2_mass_flow - effect_3_evaporation
    conc_4_mass_flow = conc_3_mass_flow - effect_4_evaporation
    conc_5_mass_flow = conc_4_mass_flow - effect_5_evaporation
    conc_1_brix = tons_solids / conc_1_mass_flow * 100
    conc_2_brix = tons_solids / conc_2_mass_flow * 100
    conc_3_brix = tons_solids / conc_3_mass_flow * 100
    conc_4_brix = tons_solids / conc_4_mass_flow * 100
    conc_5_brix = tons_solids / conc_5_mass_flow * 100
"""

# Gemini shortcut method below
def initial_balance(
    num_effects = 4,
    exh_press_psia = 30,
    last_eff_psia = 2.2,
    juice_in_tph = 500,
    juice_brix = 14,
    syrup_brix = 65,
    v1_bleed = 0,
    v2_bleed = 0,
    v3_bleed = 0,
    effect_1_surface = 25000,
    effect_2_surface = 25000,
    effect_3_surface = 25000,
    effect_4_surface = 25000,
    effect_5_surface = 25000,
):
    """Calculates initial values for the trial and error balance and returns a dictionary."""
    
    results = {}

    # Mass Balance Calculations
    results['juice_in_tph'] = juice_in_tph
    results['juice_brix'] = juice_brix
    results['tons_solids'] = juice_brix * juice_in_tph / 100
    results['syrup_brix'] = syrup_brix
    results['syrup_out_tph'] = juice_brix / syrup_brix * juice_in_tph
    results['total_evaporation'] = juice_in_tph - results['syrup_out_tph']
    
    # Steam and Vapor Estimations
    results['num_effects'] = num_effects
    results['v1_bleed'] = v1_bleed
    results['v2_bleed'] = v2_bleed
    results['v3_bleed'] = v3_bleed
    results['x_factor'] = (results['total_evaporation'] - v1_bleed - v2_bleed * 2 - v3_bleed * 3) / num_effects
    results['exhaust_estim_tph'] = results['x_factor'] + v1_bleed + v2_bleed + v3_bleed
    
    # Pressure Profile
    results['exhaust_press_psia'] = exh_press_psia
    results['last_effect_press_psia'] = last_eff_psia
    results['p_drop_per_effect'] = (exh_press_psia - last_eff_psia) / num_effects
    results['vapor_press_effect_1'] = exh_press_psia - results['p_drop_per_effect']
    if num_effects >= 2:
        results['vapor_press_effect_2'] = results['vapor_press_effect_1'] - results['p_drop_per_effect']
    if num_effects >= 3:
        results['vapor_press_effect_3'] = results['vapor_press_effect_2'] - results['p_drop_per_effect']
    if num_effects >= 4:
        results['vapor_press_effect_4'] = results['vapor_press_effect_3'] - results['p_drop_per_effect']
    if num_effects >= 5:
        results['vapor_press_effect_5'] = results['vapor_press_effect_4'] - results['p_drop_per_effect']
    
    # Evaporation per Effect
    results['effect_1_evaporation'] = results['exhaust_estim_tph']
    if num_effects >= 2:
        results['effect_2_evaporation'] = results['effect_1_evaporation'] - v1_bleed
    if num_effects >= 3:
        results['effect_3_evaporation'] = results['effect_2_evaporation'] - v2_bleed
    if num_effects >= 4:
        results['effect_4_evaporation'] = results['effect_3_evaporation'] - v3_bleed
    if num_effects >= 5:
        results['effect_5_evaporation'] = results['effect_4_evaporation']
    
    # Mass Flow Profile
    results['conc_1_mass_flow'] = juice_in_tph - results['effect_1_evaporation']
    if num_effects >= 2:
        results['conc_2_mass_flow'] = results['conc_1_mass_flow'] - results['effect_2_evaporation']
    if num_effects >= 3:
        results['conc_3_mass_flow'] = results['conc_2_mass_flow'] - results['effect_3_evaporation']
    if num_effects >= 4:
        results['conc_4_mass_flow'] = results['conc_3_mass_flow'] - results['effect_4_evaporation']
    if num_effects >= 5:
        results['conc_5_mass_flow'] = results['conc_4_mass_flow'] - results['effect_5_evaporation']
    
    # Brix Profile with Division Guard
    # We check if the key exists (num_effects check) AND if flow is > 0
    if 'conc_1_mass_flow' in results and results['conc_1_mass_flow'] > 0:
        results['conc_1_brix'] = results['tons_solids'] / results['conc_1_mass_flow'] * 100
        
    if 'conc_2_mass_flow' in results and results['conc_2_mass_flow'] > 0:
        results['conc_2_brix'] = results['tons_solids'] / results['conc_2_mass_flow'] * 100
        
    if 'conc_3_mass_flow' in results and results['conc_3_mass_flow'] > 0:
        results['conc_3_brix'] = results['tons_solids'] / results['conc_3_mass_flow'] * 100
        
    if 'conc_4_mass_flow' in results and results['conc_4_mass_flow'] > 0:
        results['conc_4_brix'] = results['tons_solids'] / results['conc_4_mass_flow'] * 100
        
    if 'conc_5_mass_flow' in results and results['conc_5_mass_flow'] > 0:
        results['conc_5_brix'] = results['tons_solids'] / results['conc_5_mass_flow'] * 100

    # Evaporator heating surfaces
    results['surf_area_effect_1'] = effect_1_surface
    results['surf_area_effect_2'] = effect_2_surface
    results['surf_area_effect_3'] = effect_3_surface
    results['surf_area_effect_4'] = effect_4_surface
    results['surf_area_effect_5'] = effect_5_surface

    return results
