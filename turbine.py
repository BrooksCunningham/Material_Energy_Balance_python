from iapws import iapws97

# Conversion constants
PSIA_TO_MPA = 0.00689476
MPA_TO_PSIA = 1 / PSIA_TO_MPA
KJ_KG_TO_BTU_LB = 1 / 2.326
KJKGK_TO_BTULBR = 1 / 2.326
M3KG_TO_FT3LB = 16.0185

def get_steam_state(p_psia, t_f=None, x=None, s_btu=None, h_btu=None):
    """
    Helper to get IAPWS97 object and return a dictionary of English properties.
    Expects Pressure in PSIA and one other property.
    """
    p_mpa = p_psia * PSIA_TO_MPA
    
    if x is not None:
        steam = iapws97.IAPWS97(P=p_mpa, x=x)
    elif t_f is not None:
        t_k = (t_f - 32) * 5/9 + 273.15
        steam = iapws97.IAPWS97(P=p_mpa, T=t_k)
    elif s_btu is not None:
        s_si = s_btu * 2.326
        steam = iapws97.IAPWS97(P=p_mpa, s=s_si)
    elif h_btu is not None:
        h_si = h_btu * 2.326
        steam = iapws97.IAPWS97(P=p_mpa, h=h_si)
    
    return {
        "P": p_psia,
        "T": (steam.T - 273.15) * 9/5 + 32,
        "h": steam.h * KJ_KG_TO_BTU_LB,
        "s": steam.s * KJKGK_TO_BTULBR,
        "v": steam.v * M3KG_TO_FT3LB,
        "u": steam.u * KJ_KG_TO_BTU_LB,
        "x": steam.x,
        "phase": steam.phase
    }

def main():
    print("=" * 60)
    print("STEAM TURBINE CALCULATOR (Full Properties)")
    print("=" * 60)
    
    # Inputs
    p_live_psig = float(input("\nLive Steam Pressure (psig): "))
    p_live = p_live_psig + 14.696
    
    use_sat = input("Use saturation temperature? (y/n): ").lower() == 'y'
    if use_sat:
        inlet = get_steam_state(p_live, x=1) # Assuming saturated vapor
    else:
        t_live = float(input("Live Steam Temperature (°F): "))
        inlet = get_steam_state(p_live, t_f=t_live)
    
    p_exh_psig = float(input("Exhaust Steam Pressure (psig): "))
    p_exh = p_exh_psig + 14.696
    eta = float(input("Turbine Isentropic Efficiency (0-1): "))
    hp_target = float(input("Turbine Power Output (HP): "))
    
    # 1. Isentropic Expansion (Constant Entropy)
    isentropic_exit = get_steam_state(p_exh, s_btu=inlet['s'])
    
    # 2. Actual Expansion (Efficiency)
    h_actual_exit = inlet['h'] - eta * (inlet['h'] - isentropic_exit['h'])
    actual_exit = get_steam_state(p_exh, h_btu=h_actual_exit)
    
    # 3. Flow Calculations
    btu_per_hp_hr = 2544.43
    steam_flow = (hp_target * btu_per_hp_hr) / (inlet['h'] - actual_exit['h'])
    
    # Output Table
    def print_props(label, data):
        print(f"\n--- {label} ---")
        print(f"{'Property':<20} | {'Value':<10} | {'Unit'}")
        print("-" * 45)
        print(f"{'Pressure':<20} | {data['P']:<10.2f} | psia")
        print(f"{'Temperature':<20} | {data['T']:<10.2f} | °F")
        print(f"{'Enthalpy':<20} | {data['h']:<10.2f} | Btu/lb")
        print(f"{'Entropy':<20} | {data['s']:<10.4f} | Btu/lb·R")
        print(f"{'Specific Volume':<20} | {data['v']:<10.4f} | ft³/lb")
        print(f"{'Internal Energy':<20} | {data['u']:<10.2f} | Btu/lb")
        print(f"{'Quality (x)':<20} | {data['x'] if data['x'] is not None else 1.0:<10.4f} | -")

    print_props("INLET PROPERTIES", inlet)
    print_props("EXHAUST PROPERTIES (ACTUAL)", actual_exit)
    
    print("\n" + "=" * 60)
    print(f"REQUIRED STEAM FLOW: {steam_flow:.2f} lbs/hr")
    print(f"SPECIFIC STEAM RATE: {steam_flow/hp_target:.4f} lb/HP-hr")
    print("=" * 60)

if __name__ == "__main__":
    main()