the files 'st_mary_material_energy_balance.py' and 'stream_and_unit_classes.py' are the two files you need to run the material and energy balance. the neccesary imports are listed at the very top of the code on the'st_mary_material_energy_balance.py' file. 
IAPWS97 library for steam, there is a javascript for it
Brooks.. I need to convert this to a htnml file, the issue I am having is with the evaporation loop, It balances each set correctly, but it does not rebalance the juice flow to each set of evaporators based on the U ratio (within the code). Let claude have a whack at it
The out puts for the evaporators should show a tabular dataset of evaporator outputs, what you should look for is the U ratio being equal across all sets. You should also ensure that the last effect is somewhere around 25 - 26" (user specified), the first effect calandria should be around 15 psig (user specified). Each effect should drop in pressure from the previous effect.

goodluck. 
