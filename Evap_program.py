import math
import numpy as np
import time
start_time = time.time()

# Input Data
m_L0 = 1450000   # m_L0 = Juice flow in lb / hr
bx_0, bx_N = 14, 65  # bx_0 = juice brix, bx_N = final syrup brix

P_exh = 14 #psig
P_N = 25 # "inches of Hg"

Lvl = 2 # ft of tube liquid level

T_L0 = 225 #°F Juice Inlet Temperature

N = 4  # N = number of effects

# Now define the Desired Area of each effect
A_1d, A_2d, A_3d, A_4d, A_5d = 72000, 48000, 46000, 46000, 5900 # ft²

    # St Mary's Evaporators... Normal Operations Effect 1 = 72000, Effect 2 = 48000, Effect 3 = 46000, Effect 4 = 46000
         # Wash Pre3.. Effect 1 = 37000, Effect 2 = 48000, Effect 3 = 46000, Effect 4 = 46000
         # Wash Pre1.. Effect 1 = 47000, Effect 2 = 48000, Effect 3 = 46000, Effect 4 = 46000
         # Wash Big Set (set 1)... Effect 1 = 72000, Effect 2 = 23000, Effect 3 = 21000, Effect 4 = 21000

    # Note that for a triple, A_4d and A_5d are not used, for a quad A_5d is not used


# Now we need to include vapor bleeds
bld_1, bld_2, bld_3, bld_4 = 174000, 0, 0, 0
    # Note that for a triple, bld_3 and bld_4 are not used, for a quad bld_4 is not used

# Define the Dessin Coefficient
K = 20000 # 20000 is good for design purposes, 16000 for very clean evaporators




# m_LN = Syrup Flow in lb / hr
m_LN = m_L0 * (bx_0 / bx_N)

# Now to calculate the total water evaporated
m_Vt = m_L0 - m_LN


# Now solve for the X factor
X = (m_Vt - bld_1 - bld_2 * 2 - bld_3 * 3 - bld_4 * 4) / N
Exh_est = X + bld_1 + bld_2 + bld_3 + bld_4
Exh = Exh_est

# Now we need the brix in each effect, this is done first by calculating the flow out of each effect by a basic material balance
m_L1 = m_L0 - Exh
bx_1 = bx_0 * (m_L0 / m_L1)







m_L2 = m_L1 - (Exh - bld_1)
bx_2 = bx_1 * (m_L1 / m_L2)


m_L3 = m_L2 - (Exh - bld_1 - bld_2)
bx_3 = bx_2 * (m_L2 / m_L3) 
if N > 3:
    m_L4 = m_L3 - (Exh - bld_1 - bld_2 - bld_3)
    bx_4 = bx_3 * (m_L3 / m_L4)
    if N > 4:
        m_L5 = m_L4 - (Exh - bld_1 - bld_2 - bld_3 - bld_4)
        bx_5 = bx_4 * (m_L4 / m_L5)

# Now we need to calculate the estimated steam savings for vapor bleeds
Exh_Sav = bld_1 / N + bld_2 * 2 / N + bld_3 * 3 / N + bld_4 * 4 / N

# Now comes the fun part, the trial and error method   
# First assume an equal pressure drop across each effect
# convert both numbers to psia
P_exh_psia = P_exh + 14.7
P_N_psia = (29.92 - P_N) * 0.491154
# Calculate the pressure drop across each effect
P_drop = (P_exh_psia - P_N_psia) / N    
# Calculate the pressure at the start of each effect
P_0 = P_exh_psia
P_1 = P_0 - P_drop
P_2 = P_1 - P_drop
P_3 = P_2 - P_drop
P_4 = P_3 - P_drop
P_5 = P_4 - P_drop





print("This is the input data for the program")

print(f"Exhaust Pressure in psig: {P_exh}")
print(f"Last effect vacuum in inches of Hg: {P_N}")

print(f"Number of effects: {N}")


print(f"juice flow in lb / hr: {m_L0:,.0f}")

print(f"juice brix: {bx_0}")
print(f"final syrup brix: {bx_N}")

print(f"vapor bleed 1 in lb / hr: {bld_1:,.0f}")
print(f"vapor bleed 2 in lb / hr: {bld_2:,.0f}") 
if N > 3:
    print(f"vapor bleed 3 in lb / hr: {bld_3:,.0f}")
    if N > 4:
     print(f"vapor bleed 4 in lb / hr: {bld_4:,.0f}")

print("----------------------------------------------------")
print("This is the shortcut method calculations to use for the trial and error portion")
print(f"syrup flow in lb / hr: {m_LN:,.0f}")
print(f"Total water evaporated in lb / hr: {m_Vt:,.0f}")
print(f"X factor: {X:,.0f}")
print(f"Exhaust in lb / hr: {Exh:,.0f}")
print(f"juice flow out of effect 1 in lb / hr: {m_L1:,.0f}")
print(f"juice brix out of effect 1: {bx_1:,.2f}")
print(f"juice flow out of effect 2 in lb / hr: {m_L2:,.0f}")
print(f"juice brix out of effect 2: {bx_2:,.2f}")
print(f"juice flow out of effect 3 in lb / hr: {m_L3:,.0f}")
print(f"juice brix out of effect 3: {bx_3:,.2f}")
if N > 3:
    print(f"juice flow out of effect 4 in lb / hr: {m_L4:,.0f}")
    print(f"juice brix out of effect 4: {bx_4:,.2f}")
    if N > 4:
        print(f"juice flow out of effect 5 in lb / hr: {m_L5:,.0f}")
        print(f"juice brix out of effect 5: {bx_5:,.2f}")

print(f"Steam savings from vapor bleeds in lb / hr: {Exh_Sav:,.0f}")

print(f"Exhaust pressure in psia: {P_exh_psia:,.2f}")
print(f"Last effect vacuum in psia: {P_N_psia:,.2f}")


print(f"Exhaust Pressure in psia: {P_0:,.2f}")
print(f"Pressure at the start of effect 1 in psia: {P_1:,.2f}")
print(f"Pressure at the start of effect 2 in psia: {P_2:,.2f}")
print(f"Pressure at the start of effect 3 in psia: {P_3:,.2f}")
if N > 3:

    print(f"Pressure at the start of effect 4 in psia: {P_4:,.2f}")
    if N > 4:
        print(f"Pressure at the start of effect 5 in psia: {P_5:,.2f}")

print("----------------------------------------------------")

print(f"Starting Trial and Error for Target Evap in lb/hr: {m_Vt:,.0f} \n")


#Now we need the specific heat of each liquid at each effect


tolerance = 1.0  # Stop when difference is less than 1 lb/hr
max_iterations = 5  # Maximum number of iterations
iteration = 0

while iteration < max_iterations:
    # this is done with this equation cp_i = -0.005656 * bx_i + 0.9964

        cp_0 = -0.005656 * bx_0 + 0.9964
        cp_1 = -0.005656 * bx_1 + 0.9964
        cp_2 = -0.005656 * bx_2 + 0.9964    
        cp_3 = -0.005656 * bx_3 + 0.9964
        if N > 3:
            cp_4 = -0.005656 * bx_4 + 0.9964
            if N > 4:
                cp_5 = -0.005656 * bx_5 + 0.9964
            
        # Now we need to use some methods to obtain the vapor temperature at each effect
        # We will use a formula to find the temperature of the vapor at each effect
        # We will use the pressure at the start of each effect to find the temperature of the vapor at each effect
        def calculate_T(P):
            # Calculate the repeating base term
            x = math.log10(P) + 10
            
            # Calculate the exponent (polynomial)
            exponent = (
                0.0000219687002497959 * x**6 +
                -0.00135518069051674 * x**5 +
                0.0327789523048858 * x**4 +
                -0.377600406306301 * x**3 +
                1.85343522575917 * x**2 +
                0 * x + # This term is zero as per your formula
                -19.9759078567689
            )
            
            # Calculate final T
            T = 10 ** exponent
            return T

        # Example usage:
        #p_value = 34.7 # Replace with your actual P value
        #result = calculate_T(p_value)
        #print(f"T = {result}")
        # for each effect
        T_0 = calculate_T(P_0)
        T_1 = calculate_T(P_1)  
        T_2 = calculate_T(P_2)
        T_3 = calculate_T(P_3)
        if N > 3:
            T_4 = calculate_T(P_4)
            if N > 4:
                T_5 = calculate_T(P_5)  
        # Now we need the latent heat of vaporization at each effect
        # We will use the temperature at each effect to find the latent heat of vaporization at each effect
        def calculate_LH(T):
        
            
            # Calculate the polynomial
            LH = -0.00000152231563 * T**3 + .000504774867 * T**2 - 0.634291695987 * T + 1096.29

        
            return LH
        # Example usage:
        #T_value = 347.7 # Replace with your actual T value
        calculate_LH(T_0)
        calculate_LH(T_1)
        calculate_LH(T_2)   
        calculate_LH(T_3)
        if N > 3:
            calculate_LH(T_4)
            if N > 4:
                calculate_LH(T_5)

    
        # Now we need the boiling point elevation at each effect from brix and then from head
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

        #Now to actually calculate the boiling point elevation for each effect
        bpe_0 = calculate_bpe1(bx_0) + calculate_bpe2(Lvl, bx_0, T_0)
        bpe_1 = calculate_bpe1(bx_1) + calculate_bpe2(Lvl, bx_1, T_1)
        bpe_2 = calculate_bpe1(bx_2) + calculate_bpe2(Lvl, bx_2, T_2)   
        bpe_3 = calculate_bpe1(bx_3) + calculate_bpe2(Lvl, bx_3, T_3)
        if N > 3:
            bpe_4 = calculate_bpe1(bx_4) + calculate_bpe2(Lvl, bx_4, T_4)
            if N > 4:
                bpe_5 = calculate_bpe1(bx_5) + calculate_bpe2(Lvl, bx_5, T_5)
        

        # Now we need to calculate the boiling point of the liquid at each effect
        def calculate_bp(T, bpe):
            bp = T + bpe
            return bp
        bp_1 = calculate_bp(T_1, bpe_1)
        bp_2 = calculate_bp(T_2, bpe_2)
        bp_3 = calculate_bp(T_3, bpe_3)
        if N > 3:
            bp_4 = calculate_bp(T_4, bpe_4)
            if N > 4:
                bp_5 = calculate_bp(T_5, bpe_5)
        # Now we will determine the evaporation in each effect doing a heat and mass balance and compare the calculated evaporation to the 
        # actual evaporation
        def calculate_evaporation(m_L, cp, T_in, T_out, LH_cal, LH_bod, steam_in):
            # Calculate the heat entering from the steam
            Q_steam = steam_in * LH_cal
            # Calculate the heat entering or leaving from sensible heat
            Q_sensible = m_L * cp * (T_out - T_in)
            # Take the difference between the two
            Q_total = Q_steam - Q_sensible
            # Calculate the evaporation from the latent heat of vaporization
            m_V = Q_total / LH_bod
            
            return m_V
        # Example usage:
        #m_L = 200000
        #cp = 0.91 
        #T_in = 225
        #T_out = 238
        #LH_cal = 940
        #LH_bod = 970
        #m_V = calculate_evaporation(m_L, cp, T_in, T_out, LH_cal, LH_bod)
        #print(f"Evaporation: {m_V:,.2f} lb/hr")
        # Now to actually calculate the evaporation for each effect
        steam_in = Exh
        m_V5 = 0
        m_V4 = 0
        m_V1 = calculate_evaporation(m_L0, cp_1, T_L0, bp_1, calculate_LH(T_0), calculate_LH(T_1), steam_in)
        Q_1 = steam_in * calculate_LH(T_0)
        m_L1 = m_L0 - m_V1
        steam_in = m_V1 - bld_1
        m_V2 = calculate_evaporation(m_L1, cp_2, bp_1, bp_2, calculate_LH(T_1), calculate_LH(T_2), steam_in)
        Q_2 = steam_in * calculate_LH(T_1)
        m_L2 = m_L1 - m_V2
        steam_in = m_V2 - bld_2
        m_V3 = calculate_evaporation(m_L2, cp_3, bp_2, bp_3, calculate_LH(T_2), calculate_LH(T_3), steam_in)
        Q_3 = steam_in * calculate_LH(T_2)
        m_L3 = m_L2 - m_V3
        steam_in = m_V3 - bld_3
        if N > 3:
            m_V4 = calculate_evaporation(m_L3, cp_4, bp_3, bp_4, calculate_LH(T_3), calculate_LH(T_4), steam_in)
            Q_4 = steam_in * calculate_LH(T_3)
            m_L4 = m_L3 - m_V4
            steam_in = m_V4 - bld_4
            if N > 4:
                m_V5 = calculate_evaporation(m_L4, cp_5, bp_4, bp_5, calculate_LH(T_4), calculate_LH(T_5), steam_in)
                m_L5 = m_L4 - m_V5
                Q_5 = steam_in * calculate_LH(T_4)
            
        m_Vt_calc = m_V1 + m_V2 + m_V3 + m_V4 + m_V5
        evap_diff = m_Vt_calc - m_Vt

        # Now we need to adjust the inlet steam (Exh) until we get a difference of 0
    # This is done by trial and error, but we can use a loop to automate the process
        Exh = Exh - evap_diff / 10

        iteration += 1



    #Now We will calculate the Dessin heat transfer coefficients for each effect
def calc_dessin(brx, T_cal, LH_vap, K):
        # Calculate the Dessin heat transfer coefficient
        U = (100-brx) * (T_cal - 130) * LH_vap / K
        return U    
U_1 = calc_dessin(bx_1, T_0, calculate_LH(T_1), K)
U_2 = calc_dessin(bx_2, T_1, calculate_LH(T_2), K)
U_3 = calc_dessin(bx_3, T_2, calculate_LH(T_3), K)
if N > 3:
        U_4 = calc_dessin(bx_4, T_3, calculate_LH(T_4), K)
        if N > 4:
            U_5 = calc_dessin(bx_5, T_4, calculate_LH(T_5), K)
# Now the heat transfer calculations solving U calc 
# Q = U * A * ΔT_lm, Un_calc = Q / (A * ΔT_lm)
def U_calc(Q, A, delta_T_lm):
        U_c = Q / (A * delta_T_lm)
        return U_c
U_1_calc = U_calc(Q_1, A_1d, (T_0 - bp_1))
U_2_calc = U_calc(Q_2, A_2d, (T_1 - bp_2))
U_3_calc = U_calc(Q_3, A_3d, (T_2 - bp_3))
if N > 3:
        U_4_calc = U_calc(Q_4, A_4d, (T_3 - bp_4))
        if N > 4:
            U_5_calc = U_calc(Q_5, A_5d, (T_4 - bp_5))
# Now we need to ratio the U calc to the Dessin U
def U_ratio(U_calc, U_dessin):
        U_r = U_calc / U_dessin
        return U_r
U_1_ratio = U_ratio(U_1_calc, U_1)
U_2_ratio = U_ratio(U_2_calc, U_2)
U_3_ratio = U_ratio(U_3_calc, U_3)
if N > 3:
        U_4_ratio = U_ratio(U_4_calc, U_4)
        if N > 4:
            U_5_ratio = U_ratio(U_5_calc, U_5)
# Now we need the average U ratio
def average_U_ratio(ratios):
        avg = sum(ratios) / len(ratios)
        return avg
if N == 3:
    ratios = [U_1_ratio, U_2_ratio, U_3_ratio]
elif N == 4:
    ratios = [U_1_ratio, U_2_ratio, U_3_ratio, U_4_ratio]
elif N == 5:
    ratios = [U_1_ratio, U_2_ratio, U_3_ratio, U_4_ratio, U_5_ratio]
avg_U_ratio = average_U_ratio(ratios)

# Now we compare these areas to the desired areas
# Now to Do this whole method several times until the U ratios are all close equal


interation_master = 0
max_master_iterations = 65

while interation_master < max_master_iterations:

    iteration = 0
    max_iterations = 5 


    while iteration < max_iterations:
        # this is done with this equation cp_i = -0.005656 * bx_i + 0.9964

            cp_0 = -0.005656 * bx_0 + 0.9964
            cp_1 = -0.005656 * bx_1 + 0.9964
            cp_2 = -0.005656 * bx_2 + 0.9964    
            cp_3 = -0.005656 * bx_3 + 0.9964
            if N > 3:
                cp_4 = -0.005656 * bx_4 + 0.9964
                if N > 4:
                    cp_5 = -0.005656 * bx_5 + 0.9964
                
            # Now we need to use some methods to obtain the vapor temperature at each effect
            # We will use a formula to find the temperature of the vapor at each effect
            # We will use the pressure at the start of each effect to find the temperature of the vapor at each effect
            def calculate_T(P):
                # Calculate the repeating base term
                x = math.log10(P) + 10
                
                # Calculate the exponent (polynomial)
                exponent = (
                    0.0000219687002497959 * x**6 +
                    -0.00135518069051674 * x**5 +
                    0.0327789523048858 * x**4 +
                    -0.377600406306301 * x**3 +
                    1.85343522575917 * x**2 +
                    0 * x + # This term is zero as per your formula
                    -19.9759078567689
                )
                
                # Calculate final T
                T = 10 ** exponent
                return T

            # Example usage:
            #p_value = 34.7 # Replace with your actual P value
            #result = calculate_T(p_value)
            #print(f"T = {result}")
            # for each effect
            T_0 = calculate_T(P_0)
            T_1 = calculate_T(P_1)  
            T_2 = calculate_T(P_2)
            T_3 = calculate_T(P_3)
            if N > 3:
                T_4 = calculate_T(P_4)
                if N > 4:
                    T_5 = calculate_T(P_5)  
            # Now we need the latent heat of vaporization at each effect
            # We will use the temperature at each effect to find the latent heat of vaporization at each effect
            def calculate_LH(T):
            
                
                # Calculate the polynomial
                LH = -0.00000152231563 * T**3 + .000504774867 * T**2 - 0.634291695987 * T + 1096.29

            
                return LH
            # Example usage:
            #T_value = 347.7 # Replace with your actual T value
            calculate_LH(T_0)
            calculate_LH(T_1)
            calculate_LH(T_2)   
            calculate_LH(T_3)
            if N > 3:
                calculate_LH(T_4)
                if N > 4:
                    calculate_LH(T_5)

        
            # Now we need the boiling point elevation at each effect from brix and then from head
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

            #Now to actually calculate the boiling point elevation for each effect
            bpe_0 = calculate_bpe1(bx_0) + calculate_bpe2(Lvl, bx_0, T_0)
            bpe_1 = calculate_bpe1(bx_1) + calculate_bpe2(Lvl, bx_1, T_1)
            bpe_2 = calculate_bpe1(bx_2) + calculate_bpe2(Lvl, bx_2, T_2)   
            bpe_3 = calculate_bpe1(bx_3) + calculate_bpe2(Lvl, bx_3, T_3)
            if N > 3:
                bpe_4 = calculate_bpe1(bx_4) + calculate_bpe2(Lvl, bx_4, T_4)
                if N > 4:
                    bpe_5 = calculate_bpe1(bx_5) + calculate_bpe2(Lvl, bx_5, T_5)
            

            # Now we need to calculate the boiling point of the liquid at each effect
            def calculate_bp(T, bpe):
                bp = T + bpe
                return bp
            bp_1 = calculate_bp(T_1, bpe_1)
            bp_2 = calculate_bp(T_2, bpe_2)
            bp_3 = calculate_bp(T_3, bpe_3)
            if N > 3:
                bp_4 = calculate_bp(T_4, bpe_4)
                if N > 4:
                    bp_5 = calculate_bp(T_5, bpe_5)
            # Now we will determine the evaporation in each effect doing a heat and mass balance and compare the calculated evaporation to the 
            # actual evaporation
            def calculate_evaporation(m_L, cp, T_in, T_out, LH_cal, LH_bod, steam_in):
                # Calculate the heat entering from the steam
                Q_steam = steam_in * LH_cal
                # Calculate the heat entering or leaving from sensible heat
                Q_sensible = m_L * cp * (T_out - T_in)
                # Take the difference between the two
                Q_total = Q_steam - Q_sensible
                # Calculate the evaporation from the latent heat of vaporization
                m_V = Q_total / LH_bod
                
                return m_V
            # Example usage:
            #m_L = 200000
            #cp = 0.91 
            #T_in = 225
            #T_out = 238
            #LH_cal = 940
            #LH_bod = 970
            #m_V = calculate_evaporation(m_L, cp, T_in, T_out, LH_cal, LH_bod)
            #print(f"Evaporation: {m_V:,.2f} lb/hr")
            # Now to actually calculate the evaporation for each effect
            steam_in = Exh
            m_V5 = 0
            m_V4 = 0
            m_V1 = calculate_evaporation(m_L0, cp_1, T_L0, bp_1, calculate_LH(T_0), calculate_LH(T_1), steam_in)
            Q_1 = steam_in * calculate_LH(T_0)
            m_L1 = m_L0 - m_V1
            steam_in = m_V1 - bld_1
            m_V2 = calculate_evaporation(m_L1, cp_2, bp_1, bp_2, calculate_LH(T_1), calculate_LH(T_2), steam_in)
            Q_2 = steam_in * calculate_LH(T_1)
            m_L2 = m_L1 - m_V2
            steam_in = m_V2 - bld_2
            m_V3 = calculate_evaporation(m_L2, cp_3, bp_2, bp_3, calculate_LH(T_2), calculate_LH(T_3), steam_in)
            Q_3 = steam_in * calculate_LH(T_2)
            m_L3 = m_L2 - m_V3
            steam_in = m_V3 - bld_3
            if N > 3:
                m_V4 = calculate_evaporation(m_L3, cp_4, bp_3, bp_4, calculate_LH(T_3), calculate_LH(T_4), steam_in)
                Q_4 = steam_in * calculate_LH(T_3)
                m_L4 = m_L3 - m_V4
                steam_in = m_V4 - bld_4
                if N > 4:
                    m_V5 = calculate_evaporation(m_L4, cp_5, bp_4, bp_5, calculate_LH(T_4), calculate_LH(T_5), steam_in)
                    m_L5 = m_L4 - m_V5
                    Q_5 = steam_in * calculate_LH(T_4)
                
            m_Vt_calc = m_V1 + m_V2 + m_V3 + m_V4 + m_V5
            evap_diff = m_Vt_calc - m_Vt

            # Now we need to adjust the inlet steam (Exh) until we get a difference of 0
        # This is done by trial and error, but we can use a loop to automate the process
            Exh = Exh - evap_diff / 10

            iteration += 1



        #Now We will calculate the Dessin heat transfer coefficients for each effect
    def calc_dessin(brx, T_cal, LH_vap, K):
            # Calculate the Dessin heat transfer coefficient
            U = (100-brx) * (T_cal - 130) * LH_vap / K
            return U    
    U_1 = calc_dessin(bx_1, T_0, calculate_LH(T_1), K)
    U_2 = calc_dessin(bx_2, T_1, calculate_LH(T_2), K)
    U_3 = calc_dessin(bx_3, T_2, calculate_LH(T_3), K)
    if N > 3:
            U_4 = calc_dessin(bx_4, T_3, calculate_LH(T_4), K)
            if N > 4:
                U_5 = calc_dessin(bx_5, T_4, calculate_LH(T_5), K)
    # Now the heat transfer calculations solving U calc 
    # Q = U * A * ΔT_lm, Un_calc = Q / (A * ΔT_lm)
    def U_calc(Q, A, delta_T_lm):
            U_c = Q / (A * delta_T_lm)
            return U_c
    U_1_calc = U_calc(Q_1, A_1d, (T_0 - bp_1))
    U_2_calc = U_calc(Q_2, A_2d, (T_1 - bp_2))
    U_3_calc = U_calc(Q_3, A_3d, (T_2 - bp_3))
    if N > 3:
            U_4_calc = U_calc(Q_4, A_4d, (T_3 - bp_4))
            if N > 4:
                U_5_calc = U_calc(Q_5, A_5d, (T_4 - bp_5))
    # Now we need to ratio the U calc to the Dessin U
    def U_ratio(U_calc, U_dessin):
            U_r = U_calc / U_dessin
            return U_r
    U_1_ratio = U_ratio(U_1_calc, U_1)
    U_2_ratio = U_ratio(U_2_calc, U_2)
    U_3_ratio = U_ratio(U_3_calc, U_3)
    if N > 3:
            U_4_ratio = U_ratio(U_4_calc, U_4)
            if N > 4:
                U_5_ratio = U_ratio(U_5_calc, U_5)
    # Now we need the average U ratio
    def average_U_ratio(ratios):
            avg = sum(ratios) / len(ratios)
            return avg
    if N == 3:
        ratios = [U_1_ratio, U_2_ratio, U_3_ratio]
    elif N == 4:
        ratios = [U_1_ratio, U_2_ratio, U_3_ratio, U_4_ratio]
    elif N == 5:
        ratios = [U_1_ratio, U_2_ratio, U_3_ratio, U_4_ratio, U_5_ratio]
    avg_U_ratio = average_U_ratio(ratios)

    P_1 = P_1 * (avg_U_ratio / U_1_ratio)**0.1
    P_2 = P_2 * (avg_U_ratio / U_2_ratio)**0.1
    if N > 3:
        P_3 = P_3 * (avg_U_ratio / U_3_ratio)**0.1
        if N > 4:
            P_4 = P_4 * (avg_U_ratio / U_4_ratio)**0.1
    interation_master += 1

# Print Section

print(f"Specific heat of juice Initial: {cp_0:,.4f}")
print(f"Specific heat of juice at effect 1: {cp_1:,.4f}")
print(f"Specific heat of juice at effect 2: {cp_2:,.4f}")
print(f"Specific heat of juice at effect 3: {cp_3:,.4f}")
if N > 3:
            print(f"Specific heat of juice at effect 4: {cp_4:,.4f}")
            if N > 4:
                print(f"Specific heat of juice at effect 5: {cp_5:,.4f}")  
print(f"Estimated Exhaust in lb / hr: {Exh_est:,.0f}")
print(f"Final Exhaust in lb / hr: {Exh:,.0f}")

print(f"Temperature of the Exhaust in °F: {T_0:,.2f}")
print(f"Temperature of the vapor at effect 1 in °F: {T_1:,.2f}")
print(f"Temperature of the vapor at effect 2 in °F: {T_2:,.2f}")
print(f"Temperature of the vapor at effect 3 in °F: {T_3:,.2f}")
if N > 3:
            print(f"Temperature of the vapor at effect 4 in °F: {T_4:,.2f}")
            if N > 4:
                print(f"Temperature of the vapor at effect 5 in °F: {T_5:,.2f}")
print(f"Latent heat of vaporization Exhaust in BTU/lb: {calculate_LH(T_0):,.2f} ")
print(f"Latent heat of vaporization at effect 1 in BTU/lb: {calculate_LH(T_1):,.2f} ")
print(f"Latent heat of vaporization at effect 2 in BTU/lb: {calculate_LH(T_2):,.2f} ")
print(f"Latent heat of vaporization at effect 3 in BTU/lb: {calculate_LH(T_3):,.2f} ")
if N > 3:
            print(f"Latent heat of vaporization at effect 4 in BTU/lb: {calculate_LH(T_4):,.2f} ")
            if N > 4:
                print(f"Latent heat of vaporization at effect 5 in BTU/lb: {calculate_LH(T_5):,.2f} ")
print(f"Boiling point elevation at effect 1 in °F: {bpe_1:,.2f}")
print(f"Boiling point elevation at effect 2 in °F: {bpe_2:,.2f}")
print(f"Boiling point elevation at effect 3 in °F: {bpe_3:,.2f}")
if N > 3:
            print(f"Boiling point elevation at effect 4 in °F: {bpe_4:,.2f}")
            if N > 4:
                print(f"Boiling point elevation at effect 5 in °F: {bpe_5:,.2f}")
print(f"Boiling point at effect 1 in °F: {bp_1:,.2f}")
print(f"Boiling point at effect 2 in °F: {bp_2:,.2f}")
print(f"Boiling point at effect 3 in °F: {bp_3:,.2f}")
if N > 3:
            print(f"Boiling point at effect 4 in °F: {bp_4:,.2f}")
            if N > 4:
                print(f"Boiling point at effect 5 in °F: {bp_5:,.2f}")
print(f"Evaporation at effect 1 in lb/hr: {m_V1:,.0f} ")
print(f"Evaporation at effect 2 in lb/hr: {m_V2:,.0f} ")
print(f"Evaporation at effect 3 in lb/hr: {m_V3:,.0f} ")
if N > 3:
            print(f"Evaporation at effect 4 in lb/hr: {m_V4:,.0f} ")
            if N > 4:
                print(f"Evaporation at effect 5 in lb/hr: {m_V5:,.0f} ")
print(f"Evaporation difference in lb/hr: {evap_diff:,.5f} ")
print(f"Total calculated evaporation in lb/hr: {m_Vt_calc:,.0f} ")
print(f"Total actual evaporation in lb/hr: {m_Vt:,.0f} ")

print(f"Dessin heat transfer coefficient at effect 1 in BTU/hr-ft²-°F: {U_1:,.2f}")
print(f"Dessin heat transfer coefficient at effect 2 in BTU/hr-ft²-°F: {U_2:,.2f}")
print(f"Dessin heat transfer coefficient at effect 3 in BTU/hr-ft²-°F: {U_3:,.2f}")
if N > 3:
        print(f"Dessin heat transfer coefficient at effect 4 in BTU/hr-ft²-°F: {U_4:,.2f}")
        if N > 4:
            print(f"Dessin heat transfer coefficient at effect 5 in BTU/hr-ft²-°F: {U_5:,.2f}")
print(f"Calculated heat transfer coefficient at effect 1 in BTU/hr-ft²-°F: {U_1_calc:,.2f} ")
print(f"Calculated heat transfer coefficient at effect 2 in BTU/hr-ft²-°F: {U_2_calc:,.2f}")
print(f"Calculated heat transfer coefficient at effect 3 in BTU/hr-ft²-°F: {U_3_calc:,.2f}")
if N > 3:
        print(f"Calculated heat transfer coefficient at effect 4 in BTU/hr-ft²-°F: {U_4_calc:,.2f}")
        if N > 4:
            print(f"Calculated heat transfer coefficient at effect 5 in BTU/hr-ft²-°F: {U_5_calc:,.2f}")
print(f"U ratio at effect 1: {U_1_ratio:,.4f}")
print(f"U ratio at effect 2: {U_2_ratio:,.4f}")
print(f"U ratio at effect 3: {U_3_ratio:,.4f}")
if N > 3:
        print(f"U ratio at effect 4: {U_4_ratio:,.4f}")
        if N > 4:
            print(f"U ratio at effect 5: {U_5_ratio:,.4f}")

print(f"Average U ratio: {avg_U_ratio:,.4f}")

# Now I want the pressure of each effect, if psia > 14.7, then units are in psig,
#  if psia <= 14.7, then units are in vacuum "inches of Hg"
def convert_pressure(P):
    if P > 14.7:
        P_conv = P - 14.7
        unit = "psig"
    else:
        P_conv = 29.92 - P / 0.491154 
        unit = "inches of Hg"
    return P_conv, unit
P_1_conv, unit_1 = convert_pressure(P_1)
P_2_conv, unit_2 = convert_pressure(P_2)
P_3_conv, unit_3 = convert_pressure(P_3)
if N > 3:
        P_4_conv, unit_4 = convert_pressure(P_4)
        if N > 4:
            P_5_conv, unit_5 = convert_pressure(P_5)
print(f"Vapor Pressure effect 1 in {unit_1}: {P_1_conv:,.2f} ")
print(f"Vapor Pressure effect 2 in {unit_2}: {P_2_conv:,.2f} ")
print(f"Vapor Pressure effect 3 in {unit_3}: {P_3_conv:,.2f} ")
if N > 3:
        print(f"Vapor Pressure effect 4 in {unit_4}: {P_4_conv:,.2f} ")
        if N > 4:
            print(f"Vapor Pressure effect 5 in {unit_5}: {P_5_conv:,.2f} ")
if avg_U_ratio <= 1:
     print(f"The Evaporator Station has enough heating surface for the given conditions.")
else: 

     print(f"!!! Warning!!! The Evaporator Station DOES NOT have enough heating surface for the given conditions.")

end_time = time.time()
elapsed_time = end_time - start_time
print(f"Time to Solve in seconds: {elapsed_time:,.4f} ")
