
# ==============================
# 0) Bibiotecas
# ==============================
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.XFOIL_wrapper.xfoil_wrapper import XFOIL_wrapper

# --- Bibliotecas ---------------------------
import pandas as pd
from matplotlib import pyplot as plt
import glob


# ==============================
# 1) Análises
# ==============================
analises = [
            #1, # RODAR XFOIL, salvar em pdf plot e polar em .txt
            #2  # analisar dispersão dos dados (todos os alphas foram preenchidos?), scatter
            3, # heatmap de convergencia
            ]


#xfoil_path = r"C:\Users\dunca\Desktop\UFSC\Propeller_optimization\XFOIL\xfoil.exe"
xfoil_path = r'/usr/bin/xfoil'
airfoil_naca4412 = r'/home/duncan/Desktop/26.1/projects/propeller-optimization/src/Database/Airfoils_geometry/NACA4412.dat'
airfoil_e63 = r'/home/duncan/Desktop/26.1/projects/propeller-optimization/src/Database/Airfoils_geometry/E63.dat'



if 1 in analises:
    xfoil = XFOIL_wrapper(xfoil_path, airfoil_dat_path=airfoil_naca4412)
    xfoil.aseq(-16, 25, alpha_step=0.5, reynolds=80e3, 
            panels=300, iter=10000, 
            # N = 9
            vacc=0.0)

    polar_output = r'/home/duncan/Desktop/26.1/projects/propeller-optimization/polar.txt'

    files = [
        #r'/home/duncan/Desktop/26.1/projects/propeller-optimization/low_reynolds_test/polar_100e3.txt',
        r'/home/duncan/Desktop/26.1/projects/propeller-optimization/low_reynolds_test/polar_150e3.txt',
        #r'/home/duncan/Desktop/26.1/projects/propeller-optimization/low_reynolds_test/polar_200e3.txt',
        #r'/home/duncan/Desktop/26.1/projects/propeller-optimization/low_reynolds_test/polar_250e3.txt',
        r'/home/duncan/Desktop/26.1/projects/propeller-optimization/low_reynolds_test/polar_400e3_RODAR_ALPHA.txt',
        #r'/home/duncan/Desktop/26.1/projects/propeller-optimization/low_reynolds_test/polar_350e3.txt',
        #r'/home/duncan/Desktop/26.1/projects/propeller-optimization/low_reynolds_test/polar_450e3.txt',
        #r'/home/duncan/Desktop/26.1/projects/propeller-optimization/low_reynolds_test/polar_500e3_verificar.txt',

    ]

    xfoil._save_polar_pdf([polar_output])
 

if 2 in analises:

    xfoil_path = r'/usr/bin/xfoil'
    airfoil_naca4412 = r'/home/duncan/Desktop/26.1/projects/propeller-optimization/src/Database/Airfoils_geometry/NACA4412.dat'
    xfoil = XFOIL_wrapper(xfoil_path, airfoil_naca4412)


    
    
    # ── 1. Leitura dos arquivos ───────────────────────────────────────────────────
 
    POLAR_GLOB = r"/home/duncan/Desktop/26.1/projects/propeller-optimization/low_reynolds_test/*.txt"          
    
    files = sorted(glob.glob(POLAR_GLOB))
    if not files:
        raise FileNotFoundError(f"Nenhum arquivo encontrado em: {POLAR_GLOB}")
    
    frames = []
    for f in files:
        re_val = xfoil._extract_reynolds_from_polar(f)
        df = xfoil._read_polar_file(Path(f))
        df["Reynolds"] = re_val
        frames.append(df)
    
    df_all = pd.concat(frames, ignore_index=True)
    
    # ── 2. Filtragem ──────────────────────────────────────────────────────────────
    
    ALPHA_MIN, ALPHA_MAX = -16, 25
    
    df = df_all[
        df_all["alpha"].between(ALPHA_MIN, ALPHA_MAX) &
        df_all["CL"].notna() &
        df_all["Reynolds"].notna()
    ].copy()
    
    # ── 3. Gráfico ────────────────────────────────────────────────────────────────
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    sc = ax.scatter(
        df["alpha"],
        df["Reynolds"],
        c=df["CL"],
        cmap="RdBu_r",
        s=40,
        alpha=0.85,
        edgecolors="none",
        zorder=3,
    )
    
    cbar = fig.colorbar(sc, ax=ax, pad=0.015)
    cbar.set_label("$C_L$  [-]", fontsize=11)
    
    ax.set_xlabel(r"$\alpha$  [°]", fontsize=11)
    ax.set_ylabel("Reynolds  [-]", fontsize=11)
    ax.set_title("Convergência XFOIL — $C_L$ por $\\alpha$ e Re", fontsize=12)
    
    ax.set_xlim(ALPHA_MIN - 1, ALPHA_MAX + 1)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.2e}"))
    
    ax.axvline(0, color="gray", lw=0.6, ls="--", zorder=2)
    ax.grid(True, which="both", ls=":", lw=0.4, alpha=0.5)
    
    plt.tight_layout()
    plt.savefig("xfoil_scatter_CL.png", dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Pontos plotados: {len(df)} | Arquivos lidos: {len(files)}")





if 3 in analises:
    def plot_xfoil_convergence_heatmap(
        df_all,
        alpha_min=-16,
        alpha_max=25,
        alpha_step=0.5,
        value_column="CL",
    ):
        """
        Heatmap de convergência XFOIL em grade regular (alpha x Reynolds)

        --- --- ---
        value_column = 'CL' ou 'CD', escolher qual parâmetro analisar
        
        """

        import numpy as np
        import pandas as pd
        from matplotlib import pyplot as plt

        if value_column == 'CD': value_column_plot = r'$C_d$'
        elif value_column == 'CL': value_column_plot = r'$C_l$'

        # ------------------------------------------------------------------
        # 1) Filtra intervalo de alpha
        # ------------------------------------------------------------------
        df = df_all[
            df_all["alpha"].between(alpha_min, alpha_max)
        ].copy()

        # ------------------------------------------------------------------
        # 2) Grade regular esperada
        # ------------------------------------------------------------------
        alpha_grid = np.round(
            np.arange(alpha_min, alpha_max + alpha_step, alpha_step),
            3
        )

        reynolds_grid = np.sort(df["Reynolds"].unique())

        full_grid = pd.MultiIndex.from_product(
            [reynolds_grid, alpha_grid],
            names=["Reynolds", "alpha"]
        ).to_frame(index=False)

        # ------------------------------------------------------------------
        # 3) Junta com os dados reais
        # ------------------------------------------------------------------
        merged = full_grid.merge(
            df[["Reynolds", "alpha", value_column]],
            on=["Reynolds", "alpha"],
            how="left"
        )

        # convergiu = possui valor
        merged["converged"] = merged[value_column].notna().astype(int)

        # ------------------------------------------------------------------
        # 4) Pivot para matriz 2D
        # ------------------------------------------------------------------
        merged["alpha"] = merged["alpha"].round(3)

        heatmap_conv = merged.pivot_table(
            index="Reynolds",
            columns="alpha",
            values="converged",
            aggfunc="max"
        )

        heatmap_cl = merged.pivot_table(
            index="Reynolds",
            columns="alpha",
            values=value_column,
            aggfunc="mean"
        )

        # ------------------------------------------------------------------
        # 5) Plot binário (convergência)
        # ------------------------------------------------------------------

        fig, ax = plt.subplots(figsize=(12, 5))

        im = ax.imshow(
            heatmap_conv,
            aspect="auto",
            origin="lower",
        )

        cbar = fig.colorbar(im, ax=ax, pad=0.015)
        cbar.set_label("Convergência")

        ax.set_xlabel(r"$\alpha$ [deg]")
        ax.set_ylabel("Reynolds")

        ax.set_title("Mapa de convergência XFOIL")


        ax.set_yticks(np.arange(len(reynolds_grid)))
        ax.set_yticklabels([f"{Re/1e3:.0f}k" for Re in reynolds_grid])

        # linhas horizontais separando Reynolds
        for y in np.arange(-0.5, len(reynolds_grid), 1):
            ax.axhline(y, color="k", lw=0.4, alpha=0.3)

        # ------------------------------------------------------------------
        # 6) Plot contínuo de CL
        # ------------------------------------------------------------------

        fig, ax = plt.subplots(figsize=(14, 5))

        im = ax.imshow(
            heatmap_cl,
            aspect="auto",
            origin="lower",
            cmap='plasma'
        )

        cbar = fig.colorbar(im, ax=ax, pad=0.015)
        cbar.set_label(f"{value_column_plot}")

        ax.set_xlabel(r"$\alpha$ [deg]")
        ax.set_ylabel("Reynolds")

        ax.set_title(r"Mapa de Convergência XFOIL - NACA4412")
        alpha_ticks = np.arange(alpha_grid.min(), alpha_grid.max() + 0.5, 0.5)

        # converte alpha físico -> índice da imagem
        x_subpositions = np.interp(
            alpha_ticks,
            alpha_grid,
            np.arange(len(alpha_grid))
        )

        for x in x_subpositions:
            ax.axvline(x, color="k", lw=0.2, alpha=0.12)

        alpha_ticks = np.arange(alpha_grid.min(), alpha_grid.max() + 1, 1)

        x_positions = np.interp(
            alpha_ticks,
            alpha_grid,
            np.arange(len(alpha_grid))
        )

        ax.set_xticks(x_positions)
        ax.set_xticklabels([f"{a:.0f}" for a in alpha_ticks])

        # ticks igualmente espaçados
        #ax.set_xticks(np.arange(len(alpha_grid)))
        #ax.set_xticklabels(alpha_grid)

        ax.set_yticks(np.arange(len(reynolds_grid)))
        ax.set_yticklabels([f"{Re/1e3:.0f}k" for Re in reynolds_grid])

        # linhas horizontais separando Reynolds
        for y in np.arange(-0.5, len(reynolds_grid), 1):
            ax.axhline(y, color="k", lw=0.4, alpha=0.3)

        plt.tight_layout()

        tendency_lines = True
        if tendency_lines == True:
            # ----------------------------------------------------------
            # linha de tendência do CL máximo
            # ----------------------------------------------------------

            # máximo CL para cada Reynolds
            cl_max = heatmap_cl.max(axis=1)

            # posição x do CL máximo
            alpha_cl_max = heatmap_cl.idxmax(axis=1)

            # converte alpha -> índice da imagem
            x_trend = np.interp(
                alpha_cl_max.values,
                alpha_grid,
                np.arange(len(alpha_grid))
            )

            # posições y (cada Reynolds igualmente espaçado)
            y_trend = np.arange(len(reynolds_grid))

            # plota linha
            ax.plot(
                x_trend,
                y_trend,
                color="black",
                lw=2,
                marker="o",
                ms=4,
                label=f"{value_column_plot}"+r"$_{,max}$"
            )

            # ----------------------------------------------------------
            # linha de tendência do CL mínimo
            # ----------------------------------------------------------

            # mínimo CL para cada Reynolds
            cl_min = heatmap_cl.min(axis=1)

            # posição x do CL mínimo
            alpha_cl_min = heatmap_cl.idxmin(axis=1)

            # converte alpha -> índice da imagem
            x_trend_min = np.interp(
                alpha_cl_min.values,
                alpha_grid,
                np.arange(len(alpha_grid))
            )

            # posições y
            y_trend_min = np.arange(len(reynolds_grid))

            # plota linha
            ax.plot(
                x_trend_min,
                y_trend_min,
                color="black",
                lw=2,
                marker="s",
                ms=4,
                label=f"{value_column_plot}"+r"$_{,min}$"
            )


            # ----------------------------------------------------------
            # linha de tendência para CL = 0
            # ----------------------------------------------------------
            if value_column == 'CL':
                alpha_cl0 = []

                for _, row in heatmap_cl.iterrows():

                    # remove NaNs
                    valid = row.dropna()

                    if len(valid) < 2:
                        alpha_cl0.append(np.nan)
                        continue

                    cl_values = valid.values
                    alpha_values = valid.index.values.astype(float)

                    # procura mudança de sinal
                    sign_change = np.where(np.diff(np.sign(cl_values)) != 0)[0]

                    if len(sign_change) == 0:
                        alpha_cl0.append(np.nan)
                        continue

                    i = sign_change[0]

                    # interpolação linear
                    alpha0 = np.interp(
                        0,
                        [cl_values[i], cl_values[i+1]],
                        [alpha_values[i], alpha_values[i+1]]
                    )

                    alpha_cl0.append(alpha0)

                # converte alpha -> índice da imagem
                x_trend_cl0 = np.interp(
                    alpha_cl0,
                    alpha_grid,
                    np.arange(len(alpha_grid))
                )

                # posições y
                y_trend_cl0 = np.arange(len(reynolds_grid))

                # plota linha
                ax.plot(
                    x_trend_cl0,
                    y_trend_cl0,
                    color="black",
                    lw=2,
                    marker="^",
                    ms=4,
                    label=f"{value_column_plot}"+r"$ = 0$"
                )


        ax.legend()


        plt.savefig("convergence_xfoil_heatmap.png", dpi=150, bbox_inches="tight")
        plt.show()

    xfoil_path = r'/usr/bin/xfoil'
    airfoil_naca4412 = r'/home/duncan/Desktop/26.1/projects/propeller-optimization/src/Database/Airfoils_geometry/NACA4412.dat'
    xfoil = XFOIL_wrapper(xfoil_path, airfoil_naca4412)

    # ── 1. Leitura dos arquivos ───────────────────────────────────────────────────
 
    POLAR_GLOB = r"/home/duncan/Desktop/26.1/projects/propeller-optimization/low_reynolds_test/*.txt"          

    files = sorted(glob.glob(POLAR_GLOB))
    if not files:
        raise FileNotFoundError(f"Nenhum arquivo encontrado em: {POLAR_GLOB}")
    
    frames = []
    for f in files:
        re_val = xfoil._extract_reynolds_from_polar(f)
        df = xfoil._read_polar_file(Path(f))
        df["Reynolds"] = re_val
        frames.append(df)
    
    df_all = pd.concat(frames, ignore_index=True)
    plot_xfoil_convergence_heatmap(df_all)



