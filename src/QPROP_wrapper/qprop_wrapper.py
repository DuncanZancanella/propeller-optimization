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
        working_dir = os.path.dirname(self.propfile_path)
        
        # --- get filename
        p_name = os.path.basename(self.propfile_path)
        m_name = os.path.basename(self.motorfile_path)
        
        with open(output_file_name, 'w') as f:
                subprocess.run(
                    [self.qprop_path, p_name, m_name, str(velocity_mps), str(rpm), 
                    str(Volt_V), str(dBeta_deg), str(Thrust_N), str(Torque_Nm), str(Amps_A), str(Pele_W)],
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=working_dir  
            )
        
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
 
