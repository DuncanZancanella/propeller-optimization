
# =======================================
# Bibliotecas
# =======================================

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.APC_Finder.apc_propeller_finder import *
from src.QPROP_wrapper.qprop_wrapper import *

# =======================================
# 1) Inicialização hélice
# =======================================
prop_code:str = "20x10E"

prop_APC = Geometry()
df_radial_data, df_general_data = prop_APC.read_data(prop_code)

prop_test = Propeller(
    code = prop_code, 

    N_blades = df_general_data['BLADES'].iloc[0],
    D_m = 2*(df_general_data['RADIUS'].iloc[0]),

    radial_dist_m  = df_radial_data['STATION (IN)'],
    chord_dist_m   = df_radial_data['CHORD (IN)'],  # corda/r em cada seção
    twist_dist_deg = df_radial_data['TWIST (DEG)'], # ângulo de torção em cada seção (°)
    sweep_dist_m = df_radial_data['SWEEP (IN)'],    # sweep/enflechamento sobre r
    zhigh_dist_m = df_radial_data["ZHIGH (IN)"],    # altura de cada seção

    n_sections = 40, # number of blade sections 
    mode='nonlinear', edge_factor=0.5
)

#plt.plot(prop.r_station_p_m, prop.chord_p_dist_m, 'x-', label='corda')
#plt.xlabel('Posição radial ')
#plt.ylabel('Corda ')
#plt.show()
#
#plt.plot(prop.r_station_p_m, prop.twist_p_dist_deg, 'x-', label='corda')
#plt.xlabel('Posição radial ')
#plt.ylabel('Torção ')
#plt.show()

# =======================================
# 2) Criação do arquivo input para qprop
# =======================================

output_file = 'simple_prop_test.txt'
aero = {
         "CL0": [0.5],
         "CL_a": [5.8],
         "CLmin": [-0.3],
         "CLmax": [1.2],
         "CD0": [0.028],
         "CD2u": [0.05],
         "CD2l": [0.02],
         "CLCD0": [0.5],
         "REref": [70000],
         "REexp": [-0.7],

        }
df_aero = pd.DataFrame(aero)

QPROP_wrapper.write_simple_prop_file(output_file, prop_test, df_aero)


# =======================================
# 3) Teste de single-point run
# =======================================

qprop = r"C:\Users\dunca\Desktop\UFSC\QPROP\qprop1.22\qprop.exe"
prop = r"C:\Users\dunca\Desktop\UFSC\Propeller_optimization\propeller-optimization\test_cases\write_simple_file\simple_prop_test.txt"
motor = r"C:\Users\dunca\Desktop\UFSC\Propeller_optimization\propeller-optimization\test_cases\write_simple_file\motor_file_test.txt"

qprop_runner = QPROP_wrapper(qprop, prop, motor)

qprop_runner.run_single_point('0, 25, 1', 4600)