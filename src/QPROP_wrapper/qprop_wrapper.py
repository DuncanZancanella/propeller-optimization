import os
import subprocess

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from Parametrization.propeller import *


class QPROP_wrapper():

    def __init__(self, qprop_path, propfile_path, motorfile_path):
        """
        To run qprop, it is recommended to use all input files in one folder.
        If the user wants to change atmospheric data, include a file "qcon.def" following the format in README.file

        --- --- ---
        qprop_path = original qprop.exe path

        propfile = propeller input file path

        motorfile = motor input file path
        """

        self.qprop_path = qprop_path
        self.propfile_path = propfile_path
        self.motorfile_path = motorfile_path

    def run_single_point(self, velocity_mps, rpm, 
                         Volt_V = 0, dBeta_deg = 0, Thrust_N = 0, Torque_Nm = 0, Amps_A = 0, Pele_W = 0,
                         output_file_name = "qprop_singlepoint_output.txt") -> None:
        """
        Executes QPROP via single-point run and writes an output file.

        Can execute a multi-point run replacing the float variables for a string in the format 'Var_init,Var_end,var_step'
            or 'Var_init, Var_end/number_var'

        In case velocity_mps and rpm are not specific, qprop can be run to find these parameters for a given thrust or torque, 
            specific inside extra_input.
        --- --- ---

        velocity_mps = input desired true airspeed velocity in [m/s]

        rpm = operational rpm point

        output_file_name = name of the output file to save data

        --- --- ---
        extra data (optional)
            
            Volt = motor input voltage [V]

            dBeta = change in propeller twist [deg]

            Thrust = thrust [N]

            Torque = [Nm]

            Amps = motor current [A]

            Pele = electrical motor supplied [W]
        
            if some of the parameters are defined as '0', it will be tagged as unspecified. 
            In case of a zero paratemeter value, input is in the format '0.0'.
        """
        
        # --- qprop will run as in the input path
        #working_dir = os.path.dirname(self.propfile_path)
        
        # --- get filename
        prop_name_path = os.path.basename(self.propfile_path)
        motor_name_path = os.path.basename(self.motorfile_path)

        import shutil
        working_dir = os.path.dirname(self.qprop_path)

        # --- caminhos destino (dentro da pasta do qprop)
        prop_dest = os.path.join(working_dir, prop_name_path)
        motor_dest = os.path.join(working_dir, motor_name_path)

        # --- copia arquivos
        shutil.copy(self.propfile_path, prop_dest)
        shutil.copy(self.motorfile_path, motor_dest)

        # --- o qprop é executado na própria pasta, então faz-se uma copia dos arquivos motor/prop no local dele

        with open(output_file_name, 'w') as f:
                subprocess.run(
                    [self.qprop_path, prop_name_path, motor_name_path, str(velocity_mps), str(rpm), 
                    str(Volt_V), str(dBeta_deg), str(Thrust_N), str(Torque_Nm), str(Amps_A), str(Pele_W)],
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=working_dir  
            )

    def read_single_point_output(self, velocity_input:str, rpm_input:str, output_file_name:str) -> pd.DataFrame:
        """
        Reads QPROP output file after single point analysis and save data in dataframe.

        --- --- ---
        velocity_input:str = string used for velocity input in run_single_point

        rpm_input:str = string used for rpm input in run_single_point

        output_file_name = name of the qprop output file for reading

        --- --- ---
        OUTPUT

        df = dataframe with performance output data

        df_local_properties = dataframe with local blade section properties

        """
        # --- Guarantee that they are strings
        velocity_input = str(velocity_input)
        rpm_input = str(rpm_input)
        
        # - Verify if it has ",", for giving qprop the command for array input
        velocity_array_condition:bool = "," in velocity_input
        rpm_array_condition:bool = "," in rpm_input

        # - Condition 1: (one fixed value and one array as input) OR (two arrays as input)
        if velocity_array_condition or rpm_array_condition:
            df = pd.read_csv(output_file_name, sep='\s+', header=None, comment='#')

            df.columns = ['V(m/s)', 'rpm', 'Dbeta', 
                          'T(N)','Q(N-m)','Pshaft(W)',
                          'Volts','Amps','effmot',
                          'effprop','adv','CT','CP',
                          'DV(m/s)','eff',
                          'Pelec','Pprop',
                          'cl_avg','cd_avg']
            
            df_local_properties = None

        # - Condition 2: fixed velocity and fixed rpm as inputs (outputs blade local properties)
        if not velocity_array_condition and not rpm_array_condition:

            # -- Read sectional local blade properties
            df_local_properties = pd.read_csv(output_file_name, sep='\s+', comment='#')

            df_local_properties.columns = ['radius', 'chord', 'beta',
                           'Cl', 'Cd', 'Re', 'Mach', 
                           'effi', 'effp', 'Wa(m/s)', 
                           'Aswirl', 'adv_wake']


            # -- Read output performance data
            # - find line where the data starts
            with open(output_file_name, 'r') as f:
                for i, line in enumerate(f):
                    if "V(m/s)" in line:
                        header_line = i
                        break
                    
            # - read header + data line below
            df = pd.read_csv(
                output_file_name,
                sep=r'\s+',
                skiprows=header_line,
                nrows=2,
                header=0
            )
            # - extract data
            df = df.iloc[[0]]
            
            # - remove '#'
            df = df.replace('#', '', regex=True).apply(pd.to_numeric)
            df = df.drop(columns=['#'])
            
        return df, df_local_properties
    
        
    @staticmethod
    def write_simple_prop_file(output_file_name, prop:Propeller, aerodynamic_coef:pd.DataFrame):
        """
            Gera o arquivo de hélice simples para input do QPROP.
            A parametrização da hélice é feita no objeto prop, definindo geometria de entrada e 
                número de seções para parametrização.

            Limitações:
                - coeficientes aerodinâmicos únicos, portanto representa hélice de aerofólio fixo

            --- --- ---
            output_file_name = nome do arquivo

            prop = objeto propeller, inicializado anteriormente

            aerodynamic_coef = DataFrame de coeficientes aerodinâmicos de entrada
        
        """

        header_parts = [
            f"Simple propeller input file: {prop.code}",
            f" {prop.N_blades}      {prop.D_m/2}    ! Nblades       [R]",
            "",
            f" {aerodynamic_coef["CL0"].iloc[0]}    {aerodynamic_coef["CL_a"].iloc[0]}  ! CL0     CL_a",
            f" {aerodynamic_coef["CLmin"].iloc[0]}  {aerodynamic_coef["CLmax"].iloc[0]} ! CLmin   CLmax",
            "",
            f" {aerodynamic_coef["CD0"].iloc[0]}    {aerodynamic_coef["CD2u"].iloc[0]}  {aerodynamic_coef["CD2l"].iloc[0]}  {aerodynamic_coef["CLCD0"].iloc[0]} ! CD0   CD2u    CD2l    CLCD0",
            f" {aerodynamic_coef["REref"].iloc[0]}  {aerodynamic_coef["REexp"].iloc[0]} ! REref REexp",
            "",
            " 0.0254  0.0254  1.0  ! Rfac   Cfac   Bfac", # assumindo entrada em polegadas
            " 0.0     0.0     0.0  ! Radd   Cadd   Badd",
            "",
            "# r        chord       beta"
            ]
        header = "\n".join(header_parts)
        with open(output_file_name, "w") as f:
            f.write(header)
            for r_i, chord_i, beta_i in zip(prop.r_station_p_m, prop.chord_p_dist_m, prop.twist_p_dist_deg):
                f.write(
                    f"\n {r_i:.2f}      {chord_i:.2f}       {beta_i:.2f}    " 
                    )
            
            #print(f"Qprop propeller input file '{output_file}' created suscessfuly from {input_file} file")
 
