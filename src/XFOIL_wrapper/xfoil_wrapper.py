import numpy as np
import matplotlib.pyplot as plt


import subprocess
import os
from pathlib import Path
import shutil
import pandas as pd


class XFOIL_wrapper():

    def __init__(self, xfoil_path:Path, airfoil_dat_path:Path):
        """
        To run XFOIL, the user must input:

        --- --- ---

        xfoil_path = directory to the xfoil.exe file in user desktop

        airfoil_dat_path = airfoil dat file with geometry. The order must follow: from the trailing edge (1, 0),
            follow across the upper surface to the leading edge (0, 0) and return to (1, 0) following the lower surface.

        """

        self.xfoil_path    = xfoil_path 
        self.airfoil_dat_path   = airfoil_dat_path             

    def aseq(self, alpha_start:float, alpha_end:float, alpha_step:float, reynolds:float, 
             iter:int = 1000, panels:int = 300, polar_file_output:Path = r'polar.txt'):
        """
        Angle of Attack Sequence: runs XFOIL for a given airfoil, reynolds number and alpha range, executes viscous analysis and creates 
            polar file to save the data. Creates an polar output file
        
        --- --- ---
        alpha_start 

        alpha_end

        alpha_step

        reynolds 

        iter = number of iteractions during the run

        panels = number of panels for analysis

        polar_file_output = name and path of the output file
        """

        # --- Defines airfoil dat file local path as the cwd
        working_dir = os.path.dirname(self.airfoil_dat_path)
        airfoil_path = os.path.basename(self.airfoil_dat_path)
  
        # --- List of XFOIL inputs in order 
        commands = [
            f'LOAD {airfoil_path}',
            'PANE',
            'ppar',
            'n',
            f'{panels}',
            '',
            '',
            'OPER',
            f'VISC {reynolds}',
            f'ITER {iter}',
            'PACC',
            'polar_temp.txt',           # temporary file is created, then deleted
            '',
            f'ASEQ {alpha_start} {alpha_end} {alpha_step}',
            'PACC',
            '',
            'QUIT'
        ]

        # --- Run
        df_output_polar = self._run_XFOIL(commands, working_dir, polar_file_output)

        return df_output_polar

    
    def _run_XFOIL(self, commands:list, working_dir:Path, polar_file_output:Path):
        """
        Recieves a list with strings containing the commands for the XFOIL run. The commands must be in the correct order
            as usually opening the xfoil.exe

        --- --- ---
        commands = list of xfoil commands, as strings, in order of the menu. 
            Example = ['LOAD NACA4412', 'PANE', 'OPER']
        
        """
        # --- run commands in working directory
        input_file = os.path.join(working_dir, 'input.in')
        with open(input_file, 'w') as f:
            f.write('\n'.join(commands))

        with open(input_file, 'r') as stdin_file:
            result = subprocess.run(
                [self.xfoil_path],
                stdin=stdin_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=working_dir
            )

        # --- creates a temporary output file (XFOIL needs an relative path)
        polar_path = os.path.join(working_dir, 'polar_temp.txt')
        if not os.path.exists(polar_path):
            print(result.stdout[-3000:])
            raise RuntimeError("polar.txt não foi gerado.")

        # --- copia para o destino final, se especificado
        if polar_file_output is not None:
            shutil.copy(polar_path, polar_file_output)
            os.remove(polar_path)

        # --- returns data as DataFrame
        df_output_polar = self._read_polar_file(polar_file_output)
        
        return df_output_polar
       
            
    def _read_polar_file(self, polar_file:Path) -> pd.DataFrame:
        """
        Read output polar XFOIL file, after a run analysis. Returns the data in a dataframe format.

        --- --- ---
        polar_file = Path of the output file

        """
        data = np.loadtxt(polar_file, skiprows=12, ndmin=2)
        
        return pd.DataFrame({
            'alpha': data[:, 0],
            'CL': data[:, 1],
            'CD': data[:, 2],
            'CDp': data[:, 3],
            'CM': data[:, 4],
            'Top_Xtr': data[:, 5],
            'Bot_Xtr': data[:, 6],
        })
    
    def inte(self, airfoil1, airfoil2, fraction_1to2, output_new_airfoil:Path):
        # --- Defines XFOIL path as the cwd
        working_dir = os.path.dirname(self.xfoil_path)

        airfoil1_name = Path(airfoil1).stem
        airfoil2_name = Path(airfoil2).stem

        shutil.copy(airfoil1, os.path.join(working_dir, Path(airfoil1).name))
        shutil.copy(airfoil2, os.path.join(working_dir, Path(airfoil2).name))

        commands = [
            f'LOAD {Path(airfoil1).name}',
            'INTE',
            'C'
            'F'
            f'{Path(airfoil2).name}',
            f'F {fraction_1to2}',
            '{airfoil1_name}_{airfoil2_name}_{fraction_1to2}',
            'PCOP',
            f'SAVE {airfoil1_name}_{airfoil2_name}_{fraction_1to2}.dat',
            'QUIT'
        ]
        ## --- Run
        df_output_polar = self._run_XFOIL(commands, working_dir, output_new_airfoil)

        return df_output_polar

    def _plot_polar(self, polar_file):
        """
        Recieves a polar.txt file and plots Cl-alpha and Cl-Cd
        """
        polar = np.loadtxt(polar_file, skiprows=12, ndmin=2)
        
        df_polar = pd.DataFrame({
            'alpha': polar[:, 0],
            'CL': polar[:, 1],
            'CD': polar[:, 2],
            'CDp': polar[:, 3],
            'CM': polar[:, 4],
            'Top_Xtr': polar[:, 5],
            'Bot_Xtr': polar[:, 6],
        })

        DARK  = '#0f0f0f'
        GRID  = '#2a2a2a'
        CYAN  = '#00d4ff'

        fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor=DARK)

        for ax in axes:
            ax.set_facecolor(DARK)
            ax.tick_params(colors='white')
            ax.grid(color=GRID, linewidth=0.8)

        # --- Cl x Alpha
        axes[0].plot(df_polar['alpha'], df_polar['CL'], color=CYAN, lw=2, marker='o', markersize=3)
        axes[0].set_xlabel('Alpha [deg]', color='white')
        axes[0].set_ylabel('Cl', color='white')
        axes[0].set_title('Cl x Alpha', color='white', fontweight='bold')

        # --- Cl x Cd (polar)
        axes[1].plot(df_polar['CD'], df_polar['CL'], color=CYAN, lw=2, marker='o', markersize=3)
        axes[1].set_xlabel('Cd', color='white')
        axes[1].set_ylabel('Cl', color='white')
        axes[1].set_title('Cl x Cd', color='white', fontweight='bold')

        plt.tight_layout()
        plt.show()


xfoil_path = r"C:\Users\dunca\Desktop\UFSC\Propeller_optimization\XFOIL\xfoil.exe"
airfoil_naca4412 = r'C:\Users\dunca\Desktop\UFSC\Propeller_optimization\propeller-optimization\src\Database\Airfoils_geometry\NACA4412.dat'
airfoil_e63 = r'C:\Users\dunca\Desktop\UFSC\Propeller_optimization\propeller-optimization\src\Database\Airfoils_geometry\E63.dat'

xfoil = XFOIL_wrapper(xfoil_path, airfoil_dat_path=airfoil_naca4412)
#xfoil.aseq(-15, 18, alpha_step=0.5, reynolds=60e3)

polar_output = r"C:\Users\dunca\Desktop\UFSC\Propeller_optimization\propeller-optimization\polar.txt"
xfoil._plot_polar(polar_output)
#xfoil.inte(airfoil_naca4412, airfoil_e63, fraction_1to2=0.5, output_new_airfoil=None)


