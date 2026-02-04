from geometry_reader import read_apc_geometry
from xfoil_wrapper import XFoil, fit_qprop_parameters 
import numpy as np
from scipy.interpolate import PchipInterpolator
from tabulate import tabulate

def generate_qprop_input(input_file, output_file, rpm, thrust = 0, vel = 0, n_ctrl=10, n_interp=30, mode="nonuniform"):

    """
    Creates a QProp propeller input file by selecting points from a geometry file,
    then interpolating a curve using PCHIP to obtain the radius, chord and twist distribution.
    The airfoil data for each section of the propeller is obtained with XFoil    
        
    Parameters
    ----------
    input_file: str
        Path to geometry file
    
    output_file: str
        Path to QProp geometry file

    rpm: int
        Rotational Speed

    thrust: double
        Thrust 

    vel: double
        Speed

    n_ctrl : int
        Number of control points that shall be selected from the geometry file
    
    n_interp : int
        Number of interpolated points that shall be written on the QProp input file
    
    mode : str
        Chooses whether the selected points in the geometry file are picked 
        uniformly ("uniform") or non-uniformly ("nonuniform").
    """
    
    radius, chord, twist, airfoils, thickness_ratio = read_apc_geometry(input_file, n_ctrl, mode=mode)
    
    xp = np.array(radius , dtype = np.float64)
    xi = np.linspace(xp[0], xp[-1], n_interp)

    yp_chord = np.array(chord, dtype = np.float64)
    yp_twist= np.array(twist, dtype = np.float64)

    interp_chord = PchipInterpolator(xp, yp_chord)
    interp_twist = PchipInterpolator(xp, yp_twist)
    interp_thickRatio = PchipInterpolator(xp, thickness_ratio)

    yi_chord = interp_chord(xi)
    yi_twist = interp_twist(xi)
    yi_thickness_ratio = interp_thickRatio(xi)

    n = rpm / 60
    D = 2*radius[-1]/39.37
    adv_ratio  = vel / ( n * D )
    V = n * D * adv_ratio

    xfoil = XFoil(f'airfoils/{airfoils[0][1]}', f'airfoils/{airfoils[1][1]}')
    trans1 = airfoils[0][0]  
    trans2 = airfoils[1][0]

    CL0 = []
    CL_a = []
    CL_min = []
    CL_max = []
    CD0 = []
    CD2u = []
    CD2l = []
    CLCD0 = []
    REref = []
    REexp = []

    rows = []

    for i in range(n_interp):
        ri = xi[i]
        if (ri < trans1 ): frac = 0
        elif (ri > trans2 ): frac = 1
        else:  frac = (ri - trans1) / (trans2 - trans1)
        
        Vt = 2*np.pi*n*(ri/39.37)
        gamma = np.arctan(V / Vt)
        alpha_eff = yi_twist[i] - gamma
        reynolds = 1.225 / 1.78e-5 * (yi_chord[i]/39.37) * np.sqrt(V**2 + Vt**2)
        reynolds = max(reynolds, 20000)

        rows.append([
            f"{ri:.2f}",
            f"{yi_chord[i]:.2f}",
            f"{yi_twist[i]:.2f}",
            f"{alpha_eff:.1f}",
            f"{gamma:.1f}",
            f"{reynolds:.0f}",
            f"{frac:.2f}"
        ])
        headers = ["Radius", "Chord", "Twist", "Alpha_eff", "Gamma", "Re", "Interp"]

        results = xfoil.inte(frac, yi_thickness_ratio[i], alpha_start=-8, alpha_end=8, alpha_step=0.5, reynolds = reynolds)
        data = fit_qprop_parameters(results, reynolds = reynolds, reexp=-0.5)
        CL0.append(data['CL0'])
        CL_a.append(data['CL_a'])
        CL_min.append(data['CLmin'])
        CL_max.append(data['CLmax'])
        CD0.append(data['CD0'])
        CD2u.append(data['CD2u'])
        CD2l.append(data['CD2l'])
        CLCD0.append(data['CLCD0'])
        REref.append(data['REref'])  
        REexp.append(data['REexp'])   

    print(tabulate(rows, headers=headers, tablefmt="pretty"))

    header_parts = [
    f"{input_file}",
    " 2           ! Nblades",
    "",
    f" {CL0[0]:.2f}    {CL_a[0]:.1f}   ! CL0     CL_a",
    f" {CL_min[0]:.1f} {CL_max[0]:.1f} ! CLmin   CLmax",
    "",
    f" {CD0[0]:.3f}  {CD2u[0]:.3f}  {CLCD0[0]:.2f}   ! CD0    CD2    CLCD0",
    " 70000  -0.7          ! REref  REexp",
    "",
    " 0.0254  0.0254  1.0  ! Rfac   Cfac   Bfac",
    " 0.0     0.0     0.0  ! Radd   Cadd   Badd",
    "",
    "# r  chord  beta  CL0  CL_a  CLmin CLmax  CD0   CD2u   CD2l   CLCD0  REref  REexp"
    ]

    header = "\n".join(header_parts)
    with open(output_file, "w") as f:
        f.write(header)
        for ri, ci, bi, CL0i, CL_ai, CL_mini, CL_maxi, CDOi, CD2ui, CD2li, CLCD0i, RErefi, REexpi in zip(xi, yi_chord, yi_twist, CL0, CL_a, CL_min, CL_max, CD0, CD2u, CD2l, CLCD0, REref, REexp):
            f.write(
                f"\n {ri:.2f}  {ci:.2f}  {bi:.2f}  {CL0i:.2f}  {CL_ai:.2f}  {CL_mini:.2f}  {CL_maxi:.2f}  "
                f"{CDOi:.3f}  {CD2ui:.3f}  {CD2li:.3f}  {CLCD0i:.2f}  {RErefi:.2f}  {REexpi:.2f}" )
    print(f"Qprop propeller input file '{output_file}' created suscessfuly from {input_file} file")
'''
    TEST RUNS
'''

#generate_qprop_input("APC/10x45MR-PERF.PE0", "apc_prop",vel=10, rpm = 10000, thrust = 1)