# this code will return the specific gravity of sugar solutions given brix and temperature
standard_temp = 150 # in deg F, if no temperature is provided

def spec_grav(brix, temp=standard_temp):
    a = 1 + (brix * (brix + 200)) / 54000
    x = (temp - 32) / 1.8 - 20
    y = 160 - (temp - 32) / 1.8
    b = 1 - 0.036 * (x / y)
    sg = a * b
    return sg

# test below
#sgrav = spec_grav(80, 68)
#print(sgrav * 62.4)
# book value is 88.068, mine is 88.284, 0.25% error, only using to get volume flows, go with it
