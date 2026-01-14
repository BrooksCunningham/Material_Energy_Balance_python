import numpy as np

# Example problem 1:
    # 3x + y = 9
    # x + 2y = 8

A = np.array([[3, 1], 
              [1, 2]]) # Left Hand Side
B = np.array([9, 8]) # Right Hand Side

solution = np.linalg.solve(A, B)

print(f"x = {solution[0]}, y = {solution[1]}")

# Now for evaporators..
# Overall balance m_Lo = m_Ls + m_Vt
# Component       Bo * m_Lo = Bs * m_Ls + 0
# given... Bo = 0.15, Bs = 0.65, m_Lo = 700 t/h
# rearrange... m_Ls + m_Vt = 700
#              0.65 * m_Ls + 0 = 105

A = np.array([[1, 1], 
              [0.65, 0]])
B = np.array([700, 105])
solution = np.linalg.solve(A, B)
print(f"Syrup = {solution[0]:.2f}, Total Evap = {solution[1]:.2f}")