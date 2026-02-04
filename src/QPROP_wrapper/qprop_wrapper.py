import os
import subprocess

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

        In case velocity_mps and rpm is not specific, qprop can be run to find these parameters for a given thrust or torque, 
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

# test case
qprop = r"C:\Users\dunca\Desktop\UFSC\QPROP\qprop1.22\qprop.exe"
prop = r"C:\Users\dunca\Desktop\UFSC\Propeller_optimization\propeller-optimization\test_cases\run_qprop\CAM6x3F.txt"
motor = r"C:\Users\dunca\Desktop\UFSC\Propeller_optimization\propeller-optimization\test_cases\run_qprop\Speed-400-3321.txt"

qprop_runner = QPROP_wrapper(qprop, prop, motor)

qprop_runner.run_single_point(0, 4000)