import dearpygui.dearpygui as dpg
import math
import time

# --- PHYSICS & CALCULATION ENGINE ---
def solve_evaporator():
    try:
        # 1. Get Inputs from GUI [cite: 1]
        m_L0 = dpg.get_value("in_m_L0")
        bx_0 = dpg.get_value("in_bx_0")
        bx_N = dpg.get_value("in_bx_N")
        P_exh = dpg.get_value("in_P_exh")
        P_N_in_hg = dpg.get_value("in_P_N")
        T_L0 = dpg.get_value("in_T_L0")
        N = int(dpg.get_value("in_N"))
        K = dpg.get_value("in_K")
        Lvl = dpg.get_value("in_Lvl")
        
        # Bleeds and Areas [cite: 2, 3]
        blds = [dpg.get_value(f"in_bld_{i}") for i in range(1, 5)]
        areas = [dpg.get_value(f"in_A_{i}") for i in range(1, 6)]

        # 2. Material Balance [cite: 4]
        m_LN = m_L0 * (bx_0 / bx_N)
        m_Vt = m_L0 - m_LN
        
        # Shortcut factors [cite: 5, 6]
        X = (m_Vt - blds[0] - blds[1]*2 - blds[2]*3 - blds[3]*4) / N
        Exh = X + sum(blds)
        
        # Pressure conversions [cite: 7]
        P_exh_psia = P_exh + 14.7
        P_N_psia = (29.92 - P_N_in_hg) * 0.491154
        P_drop = (P_exh_psia - P_N_psia) / N
        
        # Iteration variables [cite: 10]
        P_vals = [P_exh_psia - (i * P_drop) for i in range(N + 1)]

        # --- Helper Formulas ---
        def calculate_T(P): # [cite: 13, 14, 15]
            x = math.log10(P) + 10
            exponent = (0.0000219687002497959 * x**6 - 0.00135518069051674 * x**5 +
                        0.0327789523048858 * x**4 - 0.377600406306301 * x**3 +
                        1.85343522575917 * x**2 - 19.9759078567689)
            return 10 ** exponent

        def calculate_LH(T): # [cite: 18]
            return -0.00000152231563 * T**3 + 0.000504774867 * T**2 - 0.634291695987 * T + 1096.29

        def get_cp(bx): # [cite: 11]
            return -0.005656 * bx + 0.9964

        def calculate_bpe(bx, T_Vap): # [cite: 20, 21, 23, 25]
            bpe1 = 4.266667 * bx / (100 - bx)
            brix_poly = (0.99991 + 0.0038008*bx + 0.000012662*(bx**2) + 0.00000009596*(bx**3))
            temp_poly = (5.314 - 0.07135*T_Vap + 0.00033908*(T_Vap**2) - 0.00000055728*(T_Vap**3))
            bpe2 = max(1, Lvl * 6 * brix_poly * temp_poly)
            return bpe1 + bpe2

        # Final Calculations for first effect as demonstration [cite: 32, 73, 75]
        T_0 = calculate_T(P_vals[0])
        lh_exh = calculate_LH(T_0)
        bx_1 = bx_0 * (m_L0 / (m_L0 - Exh)) # Simplification for display
        U_dessin = (100 - bx_1) * (T_0 - 130) * calculate_LH(calculate_T(P_vals[1])) / K
        
        # 3. Update GUI Outputs [cite: 85, 90]
        dpg.set_value("out_m_LN", f"{m_LN:,.0f} lb/hr")
        dpg.set_value("out_m_Vt", f"{m_Vt:,.0f} lb/hr")
        dpg.set_value("out_T0", f"{T_0:,.2f} °F")
        dpg.set_value("out_LH", f"{lh_exh:,.2f} BTU/lb")
        
        # Simple capacity check for warning [cite: 90]
        if m_Vt < (m_L0 * 0.8): # Example threshold
            dpg.set_value("out_status", "STATION OK")
            dpg.configure_item("out_status", color=[0, 255, 0])
        else:
            dpg.set_value("out_status", "WARNING: CHECK SURFACE AREA")
            dpg.configure_item("out_status", color=[255, 0, 0])

    except Exception as e:
        dpg.set_value("out_status", f"Error: {str(e)}")

# --- GUI LAYOUT ---
dpg.create_context()

# Value Registry for hidden/internal variables [Replaces add_hidden_value]
with dpg.value_registry():
    dpg.add_float_value(tag="in_T_L0", default_value=225.0) # [cite: 1]
    dpg.add_float_value(tag="in_K", default_value=20000.0)   # 
    dpg.add_float_value(tag="in_Lvl", default_value=2.0)    # [cite: 1]
    for i in range(1, 6):
        # Default areas from St Mary's Normal Operations 
        default_a = [72000, 48000, 46000, 46000, 5900]
        dpg.add_float_value(tag=f"in_A_{i}", default_value=default_a[i-1])

with dpg.window(label="Evaporator Design Tool", width=800, height=650):
    with dpg.group(horizontal=True):
        # LEFT COLUMN: INPUTS
        with dpg.child_window(width=350, label="Inputs"):
            dpg.add_text("Primary Process Data", color=[100, 200, 255])
            dpg.add_input_float(label="Juice Flow (lb/hr)", default_value=1450000, tag="in_m_L0", format="%.0f") # [cite: 1]
            dpg.add_input_float(label="Inlet Brix", default_value=14, tag="in_bx_0") # [cite: 1]
            dpg.add_input_float(label="Final Brix", default_value=65, tag="in_bx_N") # [cite: 1]
            dpg.add_input_float(label="Exhaust (psig)", default_value=14, tag="in_P_exh") # [cite: 1]
            dpg.add_input_float(label="Vacuum (in Hg)", default_value=25, tag="in_P_N") # [cite: 1]
            dpg.add_input_int(label="No. Effects", default_value=4, tag="in_N") # [cite: 1]
            
            dpg.add_spacer(height=10)
            dpg.add_text("Vapor Bleeds (lb/hr)", color=[100, 200, 255]) # [cite: 3]
            dpg.add_input_float(label="Bleed 1", default_value=174000, tag="in_bld_1")
            dpg.add_input_float(label="Bleed 2", default_value=0, tag="in_bld_2")
            dpg.add_input_float(label="Bleed 3", default_value=0, tag="in_bld_3")
            dpg.add_input_float(label="Bleed 4", default_value=0, tag="in_bld_4")
            
            dpg.add_spacer(height=10)
            dpg.add_button(label="RUN SIMULATION", callback=solve_evaporator, width=-1, height=40)

        # RIGHT COLUMN: OUTPUTS
        with dpg.child_window(width=420, label="Results"):
            dpg.add_text("Operational Results", color=[255, 200, 100])
            with dpg.group(horizontal=True):
                dpg.add_text("System Status:")
                dpg.add_text("Idle", tag="out_status")
            
            dpg.add_separator()
            
            # Formatted Output Display
            labels = [
                ("Syrup Flow:", "out_m_LN"),
                ("Total Evap:", "out_m_Vt"),
                ("Exh Temp:", "out_T0"),
                ("Latent Heat:", "out_LH")
            ]
            
            for label, tag in labels:
                with dpg.group(horizontal=True):
                    dpg.add_text(label, bullet=True)
                    dpg.add_text("---", tag=tag)

dpg.create_viewport(title='Sugar Factory Evaporator Solver', width=850, height=700)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()