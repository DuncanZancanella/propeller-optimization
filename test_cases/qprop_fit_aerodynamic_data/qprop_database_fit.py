# =======================================
# Bibliotecas
# =======================================

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.QPROP_wrapper.qprop_wrapper import *

# ------ Save fits in PDF and create csv

df_database_xfoil = pd.read_csv(r'C:\Users\dunca\Desktop\UFSC\Propeller_optimization\propeller-optimization\src\Database\xfoil_database_single_perfil.csv')
airfoils = df_database_xfoil['airfoil'].unique()

from matplotlib.backends.backend_pdf import PdfPages

DARK = '#0f0f0f'
GRID = '#2a2a2a'
CYAN = '#00d4ff'
ORANGE = '#ff6b35'

pdf_path = 'qprop_aerodynamic_database.pdf'


with PdfPages(pdf_path) as pdf:
    for af in airfoils:
        df = df_database_xfoil[df_database_xfoil['airfoil'] == af]
        Re_array = df['Re'].unique()

        for Re in Re_array:
            filter_ = (df_database_xfoil['Re'] == Re) & (df_database_xfoil['airfoil'] == af)
            df_ = df_database_xfoil[filter_]
            fitted = QPROP_wrapper.fit_parameters(df_polar_xfoil=df_, reynolds=Re)

            # --- update dataframe
            for key in fitted.keys():
                if key not in df_database_xfoil.columns:
                    df_database_xfoil[key] = np.nan
            for key, value in fitted.items():
                df_database_xfoil.loc[filter_, key] = value

            alpha = df_['alpha'].values

            def CL(alpha_deg, f):
                return f['CL0'] + alpha_deg * (f['CL_a'] * np.pi / 180)

            def CD(alpha_deg, f, re):
                Cl = CL(alpha_deg, f)
                CD2 = np.where(Cl > f['CLCD0'], f['CD2u'], f['CD2l'])
                return (f['CD0'] + CD2 * (Cl - f['CLCD0'])**2) * (re / f['REref'])**f['REexp']

            # --- 2 subplots
            fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor=DARK)
            fig.suptitle(f'Airfoil: {af}  |  Re = {Re:.0f}', color='white', fontsize=13, fontweight='bold')

            for ax in axes:
                ax.set_facecolor(DARK)
                ax.tick_params(colors='white')
                ax.xaxis.label.set_color('white')
                ax.yaxis.label.set_color('white')
                ax.title.set_color('white')
                for spine in ax.spines.values():
                    spine.set_edgecolor(GRID)
                ax.grid(color=GRID, linewidth=0.8)

            # --- CL x alpha
            axes[0].plot(alpha, df_['CL'].values,  color=CYAN,   lw=2,   label='XFOIL')
            axes[0].plot(alpha, CL(alpha, fitted),  color=ORANGE, lw=1.5, linestyle='--', label='QPROP fit')
            axes[0].set_xlabel('Alpha [deg]')
            axes[0].set_ylabel('Cl')
            axes[0].set_title('Cl x Alpha')
            axes[0].legend(facecolor='#1a1a1a', labelcolor='white')

            # --- CL x CD
            axes[1].plot(df_['CD'].values,    df_['CL'].values,  color=CYAN,   lw=2,   label='XFOIL')
            axes[1].plot(CD(alpha, fitted, Re), CL(alpha, fitted), color=ORANGE, lw=1.5, linestyle='--', label='QPROP fit')
            axes[1].set_xlabel('Cd')
            axes[1].set_ylabel('Cl')
            axes[1].set_title('Cl x Cd (polar)')
            axes[1].legend(facecolor='#1a1a1a', labelcolor='white')

            plt.tight_layout()
            param_text = (
                f"CL0 = {fitted['CL0']:.4f}\n"
                f"CL_a = {fitted['CL_a']:.4f}\n"
                f"CLmin = {fitted['CLmin']:.4f}\n"
                f"CLmax = {fitted['CLmax']:.4f}\n"
                f"CD0 = {fitted['CD0']:.6f}\n"
                f"CD2u = {fitted['CD2u']:.4f}\n"
                f"CD2l = {fitted['CD2l']:.4f}\n"
                f"CLCD0 = {fitted['CLCD0']:.4f}\n"
                f"REref = {fitted['REref']:.0f}\n"
                f"REexp = {fitted['REexp']:.2f}"
            )
            axes[1].text(
                0.97, 0.5, param_text,
                transform=axes[1].transAxes,
                fontsize=8, verticalalignment='center', horizontalalignment='right',
                color='white', fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#1a1a1a', edgecolor=GRID, alpha=0.9)
            )
            pdf.savefig(fig, facecolor=DARK)
            plt.close(fig)



df_database_xfoil.to_csv('qprop_aerodynamic_database.csv', index=False)
