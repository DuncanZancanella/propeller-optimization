
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
prop_code:str = "10x45MR"

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

#prop_performance = Performance()
#df_performance_data = prop_performance.read_data("10x45E")
#prop_performance.performance_map(df_radial_data, rpm_min=4000, rpm_max=8000, eta_range=[0.7])

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

output_file = 'simple_prop_test.txt' # aqui é interessante especificar uma pasa para output, de modo a sempre ter um padrão fixo de rotinas
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

# --- Definir diretórios
qprop = r"/home/duncan/Desktop/26.1/projects/Qprop/bin/qprop"
prop = r"/home/duncan/Desktop/26.1/projects/propeller-optimization/simple_prop_test.txt"
motor = r"/home/duncan/Desktop/26.1/projects/propeller-optimization/test_cases/write_simple_file/motor_draconis_1300KV.txt"

qprop_runner = QPROP_wrapper(qprop, prop, motor)

# --- Definir inputs
velocity_input = '0.0, 10, 1'
rpm_input = '8000'

# --- rodar análise
qprop_runner.run_single_point(velocity_input, rpm_input, Volt_V=14.8, output_file_name=r'/home/duncan/Desktop/26.1/projects/propeller-optimization/test_cases/write_simple_file/qprop_singlepoint_output.txt')

# --- ler outputs da análise
df, df_local_properties = qprop_runner.read_single_point_output(velocity_input, rpm_input, output_file_name=r'/home/duncan/Desktop/26.1/projects/propeller-optimization/test_cases/write_simple_file/qprop_singlepoint_output.txt')

