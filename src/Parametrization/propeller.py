
# ==============================================================
# 0) Bibliotecas
# ==============================================================

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# --- parametrization functions
from scipy.interpolate import PchipInterpolator

# ==============================================================
# 1) Definição da hélice
# ==============================================================

class Propeller():

    def __init__(self, D_m:float, chord_dist_m:np.array = None, twist_dist_deg:np.array = None, 
                 sweep_dist_m:np.array = None, zhigh_dist_m:np.array = None, radial_dist_m:np.array = None, 
                 n_sections:int = None):
        """
        Classe para definir principais características de uma hélice.
        ---

        radial_dist_m = posições x em [m] para as distribuição de corda, torção, espessura, sweep e diedro na forma de lista [dist_chord, dist_twist, dist_thick, ...].
            Caso o array de posições x seja o mesmo para todas as distribuições, pode-se fazer [station_dist]

        chord_dist_m = distribuição de corda c(r) em [m]

        twist_dist_deg = distribuição de torção beta(r) em [deg]

        sweep_dist_m = distribuição de enflechamento a partir da distância do bordo de ataque do hub em [m]

        zhigh_dist_m = distribuição de diedro a partir da altura em relação ao centro do hub em [m]

        n_sections = número de seções para parametrização
        
        """
        # --- Propeller chracteristics
        self.D_m:float = D_m # Diâmetro [m]

        # --- Inputs
        self.radial_dist_m = radial_dist_m      # radial station for chord, twist and thick distributions
        self.chord_dist_m = chord_dist_m        # c(r): Distribuição radial de corda [m]
        self.twist_dist_deg = twist_dist_deg    # twist(r): Distribuição radial de torção em [deg]
        self.zhigh_dist_m = zhigh_dist_m        # LE_y/r: Distribuição radial de altura de cada seção a partir do bordo de ataque. Referencial: altura/espessura = y
        self.sweep_dist_m = sweep_dist_m        # LE_x/r: Distribuição de sweep a partir da distância do bordo de ataque. Referencial = x
        # --- Parametrization (executed below)
        self.n_sections = n_sections    # number of blade sections
        self.r_station_m = None         # same 'r' positions for chord, twist, thick, height and sweep
        self.chord_p_dist_m = None
        self.twist_p_dist_deg = None
        self.sweep_p_dist_m = None
        self.zhigh_p_dist_m = None
        

        # --- Tratamento das distribuições radiais r/R (vetor xi e r_station_m)
        if isinstance(radial_dist_m, list) and len(radial_dist_m) == 5:
            self.station_chord_m, self.station_twist_deg, self.station_thick_m, self.station_sweep_m, self.station_zhigh_m = radial_dist_m # posição radial dimensional em [m], pode ser array ou dataframe

            # faz com que distribuições r/R tenham mesmo array
            self.r_station_p_m, self.chord_p_dist_m, self.twist_p_dist_deg, self.sweep_p_dist_m, self.zhigh_p_dist_m  = self.parametrize(np.min(self.station_chord_m), np.max(self.station_chord_m) , 'PCHIP', self.n_sections) 
                    # cada distribuição tem um inicio/fim diferente, mas assume-se como referência o início e fim da corda
            
            self.xi = self.r_station_p_m/(np.max(self.station_chord_m)) # assume que ultima posição do station_chord é o valor do raio

        else:
            # O usuário só da como input um array de uma coluna para STATION
                # assume que as distribuições radiais de corda, torção e espessura possuem mesmo array 
            self.station_chord_m, self.station_twist_deg, self.station_thick_m, self.station_sweep_m, self.station_zhigh_m = radial_dist_m, radial_dist_m, radial_dist_m, radial_dist_m, radial_dist_m

            self.xi, self.chord_p_dist_m, self.twist_p_dist_deg, self.sweep_p_dist_m, self.zhigh_p_dist_m  = self.parametrize(np.min(self.radial_dist_m), np.max(self.radial_dist_m), 'PCHIP', self.n_sections)
            self.r_station_m = self.xi*(self.D_m/2)


    def parametrize(self, hub_station_m:float, tip_station_m:float, parametrization:str, DoF:float):
        """
        Retorna as posições radiais ('r') de cada distribuição conforme número de seções e método de parametrização dado.
        Faz com que todas as distribuições radiais da hélice possuam array de mesmo tamanho e distribuições radiais iguais,
            assumindo distribuição linear.

        --- --- ---
        hub_station_m = posição radial do fim do cubo, início da pá

        tip_station_m = posição radial da ponta da pá

        parametrization = string para indicar método de parametrização. Pode ser 'PCHIP'.

        DoF = número de graus de liberdade para parametrizar.

        --- --- ---
        A melhorar: - Considerar distância inicial do hub em porcentagem do raio.
                    - Considerar distribuição de espessura.
                    - Considerar distribuição não linear de pontos
        """
        #Raio dimensional r (Posição de cada seção de aerofólio)
        r_station_p_m = np.linspace(hub_station_m, tip_station_m, DoF + 1)

        if parametrization == 'PCHIP':
            chord_p = PchipInterpolator(self.station_chord_m, self.chord_dist_m, extrapolate=True)
            chord_p  = chord_p(r_station_p_m)
            chord_p = np.delete(chord_p, -1)

            twist_p = PchipInterpolator(self.station_twist_deg, self.twist_dist_deg, extrapolate=True)
            twist_p  = twist_p(r_station_p_m)
            twist_p = np.delete(twist_p, -1)

            if self.sweep_dist_m is None: sweep_p = None
            else:
                sweep_p = PchipInterpolator(self.station_sweep_m, self.sweep_dist_m, extrapolate=True)
                sweep_p = sweep_p(r_station_p_m)
                sweep_p = np.delete(sweep_p, -1)

            if self.zhigh_dist_m is None: zhigh_p = None
            else:
                zhigh_p = PchipInterpolator(self.station_zhigh_m , self.zhigh_dist_m, extrapolate=True)
                zhigh_p = zhigh_p(r_station_p_m)
                zhigh_p = np.delete(zhigh_p, -1)
        
        r_station_p_m = np.delete(r_station_p_m, -1)
        
        return r_station_p_m, chord_p, twist_p, sweep_p, zhigh_p