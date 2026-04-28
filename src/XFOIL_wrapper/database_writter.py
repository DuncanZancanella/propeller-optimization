import numpy as np 
import os 
import matplotlib.pyplot as plt 
from xfoil_wrapper import XFoil
import pandas as pd 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "xfoil_database_single_perfil.csv")

def plot_polar(results, airfoil_name, Re, status, save_dir="plots"):
    '''
    Plota e salva os gráficos CL x alpha e CD x CL de uma polar.
 
    Parâmetros
    ----------
    results : dict
        Dicionário com arrays 'alpha', 'CL' e 'CD' retornado pelo XFoil.
    airfoil_name : str
        Nome do aerofólio (sem extensão), usado no título e no nome do arquivo.
    Re : float
        Número de Reynolds, usado no título e no nome do arquivo.
    status : str
        Classificação da polar ('good', 'suspect' ou 'bad'), exibida no título.
    save_dir : str, optional
        Pasta de destino dos arquivos PNG. Criada automaticamente se não existir.
        Default: 'plots'.
    '''

    os.makedirs(save_dir, exist_ok=True)

    alpha = results['alpha']
    CL    = results['CL']
    CD    = results['CD']

    fig, ax = plt.subplots(1, 2, figsize=(10,4))

    ax[0].plot(alpha, CL, marker='o')
    ax[0].set_xlabel("alpha [deg]")
    ax[0].set_ylabel("CL")
    ax[0].grid(True)

    ax[1].plot(CL, CD, marker='o')
    ax[1].set_xlabel("CL")
    ax[1].set_ylabel("CD")
    ax[1].grid(True)

    fig.suptitle(f"{airfoil_name} | Re={Re:.0f} | {status}")
    fig.tight_layout()

    filename = f"{save_dir}/{airfoil_name}_Re{int(Re)}.png"
    plt.savefig(filename, dpi=150)

    plt.show()

def classify_polar(results):
    '''
    Avalia a qualidade de uma polar aerodinâmica com base em critérios físicos
    e de regularidade numérica.
 
    Critérios aplicados (em ordem):
        1. Mínimo de 10 pontos de ângulo de ataque.
        2. CL dentro de [-3, 3] e CD dentro de [0, 1].
        3. CL crescente nos 5 primeiros pontos (monotonicidade).
        4. Pelo menos 5 pontos na região linear (-2 a 6 graus).
        5. RMSE do ajuste linear nessa região < 0.08.
        6. Menos de 4 inversões de sinal em dCL/dalpha.
 
    Parâmetros
    ----------
    results : dict
        Dicionário com arrays 'alpha', 'CL' e 'CD' retornado pelo XFoil.
 
    Retorna
    -------
    str
        'good'    — polar confiável.
        'suspect' — polar com pequenas irregularidades.
        'bad'     — polar inválida ou muito ruidosa.
    '''

    alpha, CL, CD = results['alpha'], results['CL'], results['CD']

    if len(alpha) < 10:
        return "bad"

    if np.any(np.abs(CL) > 3) or np.any(CD < 0) or np.any(CD > 1):
        return "bad"

    dCL = np.diff(CL)
    if not np.all(dCL[:5] > 0):
        return "bad"

    mask = (alpha >= -2) & (alpha <= 6)
    if np.sum(mask) < 5:
        return "bad"

    p = np.polyfit(alpha[mask], CL[mask], 1)
    CL_fit = np.polyval(p, alpha[mask])
    rmse = np.sqrt(np.mean((CL[mask] - CL_fit)**2))

    signs = np.sign(dCL)
    changes = np.sum(signs[1:] != signs[:-1])

    if rmse < 0.03 and changes < 2:
        return "good"
    elif rmse < 0.08 and changes < 4:
        return "suspect"
    else:
        return "bad"

def user_decision():
    '''
    Solicita ao usuário uma decisão interativa via terminal.
 
    Fica em loop até receber 'y' ou 'n'.
 
    Retorna
    -------
    bool
        True se o usuário digitou 'y', False se digitou 'n'.
    '''
    while True:
        decision = input("Adicionar ao banco? (y/n): ").strip().lower()
        if decision in ["y", "n"]:
            return decision == "y"

def update_database(airfoils, Res, alpha_start, alpha_end, alpha_step, db_path=DB_PATH):
    '''
    Executa o XFoil para cada combinação (airfoil, Re) e atualiza o banco CSV.
 
    Comportamento:
        - Se o banco ainda não existir, ele é criado do zero.
        - Combinações (airfoil, Re) já presentes no banco são puladas
          automaticamente, sem rodar o XFoil nem pedir confirmação.
        - Para cada nova combinação, plota a polar, exibe a classificação
          e pede confirmação interativa antes de salvar.
 
    Parâmetros
    ----------
    airfoils : list[str]
        Caminhos dos arquivos .dat relativos à pasta do projeto.
        Exemplo: ['airfoils/NACA0012.dat', 'airfoils/NACA4412.dat']
    Res : list[int | float]
        Valores de Reynolds a simular.
        Exemplo: [50000, 100000, 150000]
    db_path : str, optional
        Caminho completo do arquivo CSV do banco.
        Default: polar_database.csv na pasta do projeto.
    '''

    if os.path.exists(db_path):
        db = pd.read_csv(db_path)
        print(f"Banco carregado: {db_path}  ({len(db)} linhas)")
    else:
        db = pd.DataFrame(columns=["alpha", "CL", "CD", "Re", "airfoil"])
        print("Banco não encontrado. Criando um novo.")
 
    new_entries = []
 
    for airfoil in airfoils:
 
        xfoil        = XFoil(airfoil)
        airfoil_name = os.path.basename(airfoil).replace(".dat", "")
 
        for Re in Res:
 
            if ((db["airfoil"] == airfoil_name) & (db["Re"] == Re)).any():
                print(f"  [skip] {airfoil_name}  Re={Re} já está no banco")
                continue
 
            print(f"\nRodando {airfoil_name}  Re={Re}")
 
            try:
                results = xfoil.aseq(alpha_start=alpha_start, alpha_end=alpha_end,
                                     alpha_step=alpha_step, reynolds=Re)
            except Exception as e:
                print(f"  Falha no XFoil: {e}")
                continue
 
            status = classify_polar(results)
            plot_polar(results, airfoil_name, Re, status)
 
            if not user_decision():
                print("  Descartado")
                continue
 
            new_entries.append(pd.DataFrame({
                "alpha":   results["alpha"],
                "CL":      results["CL"],
                "CD":      results["CD"],
                "Re":      Re,
                "airfoil": airfoil_name,
            }))
 
    if new_entries:
        new_df = pd.concat(new_entries, ignore_index=True)
        db     = pd.concat([db, new_df], ignore_index=True)
        db.to_csv(db_path, index=False)
        print(f"\nBanco salvo: {db_path}  (+{len(new_df)} linhas, total {len(db)})")
    else:
        print("\nNenhuma entrada nova adicionada.")

def export_qprop(airfoil_name, Re, db_path=DB_PATH, output_path=None):
    '''
    Lê a polar de um aerofólio/Reynolds do banco e gera um arquivo de seção
    no formato QProp.
 
    O formato QProp para seção aerodinâmica é uma linha com 10 parâmetros:
        CL0  CL_a  CLmin  CLmax  CD0  CD2u  CD2l  CLCD0  REref  REexp
 
    Onde:
        CL0    — coeficiente de sustentação a alpha=0
        CL_a   — derivada dCL/dalpha [1/rad]
        CLmin  — CL mínimo da polar
        CLmax  — CL máximo da polar
        CD0    — arrasto mínimo (no ponto CLCD0)
        CD2u   — curvatura da parábola de CD para CL > CLCD0
        CD2l   — curvatura da parábola de CD para CL < CLCD0
        CLCD0  — CL no ponto de CD mínimo
        REref  — Reynolds de referência
        REexp  — expoente de escala de Reynolds (tipicamente -0.5)
 
    Parâmetros
    ----------
    airfoil_name : str
        Nome do aerofólio exatamente como está no banco (sem extensão e sem path).
        Exemplo: 'NACA0012'
    Re : int | float
        Número de Reynolds desejado. Deve existir no banco.
    db_path : str, optional
        Caminho do CSV do banco. Default: polar_database.csv na pasta do projeto.
    output_path : str, optional
        Caminho do arquivo de saída. Se None, salva como
        '<airfoil_name>_Re<Re>_qprop.txt' na pasta do projeto.
 
    Retorna
    -------
    dict
        Dicionário com os 10 parâmetros QProp ajustados.
 
    Raises
    ------
    FileNotFoundError
        Se o banco não existir.
    ValueError
        Se a combinação (airfoil_name, Re) não for encontrada no banco.
    '''

    from xfoil_wrapper import fit_qprop_parameters
 
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Banco não encontrado: {db_path}")
 
    db = pd.read_csv(db_path)
 
    mask = (db["airfoil"] == airfoil_name) & (db["Re"] == Re)
    if not mask.any():
        disponiveis = db.groupby("airfoil")["Re"].unique().apply(list).to_dict()
        raise ValueError(
            f"Combinação '{airfoil_name}' Re={Re} não encontrada.\n"
            f"Disponíveis no banco: {disponiveis}"
        )
 
    subset = db[mask].reset_index(drop=True)
 
    results = {
        "alpha": subset["alpha"].to_numpy(),
        "CL":    subset["CL"].to_numpy(),
        "CD":    subset["CD"].to_numpy(),
    }
 
    params = fit_qprop_parameters(results, reynolds=Re)
 
    qprop_line = (
        f"{params['CL0']:10.5f}  {params['CL_a']:10.5f}  "
        f"{params['CLmin']:10.5f}  {params['CLmax']:10.5f}  "
        f"{params['CD0']:10.6f}  {params['CD2u']:10.6f}  {params['CD2l']:10.6f}  "
        f"{params['CLCD0']:10.5f}  {params['REref']:.0f}  {params['REexp']:.2f}"
    )
 
    if output_path is None:
        output_path = os.path.join(BASE_DIR, f"{airfoil_name}_Re{int(Re)}_qprop.txt")
 
    with open(output_path, "w") as f:
        f.write(f"! QProp airfoil section — {airfoil_name}  Re={Re:.0f}\n")
        f.write("! CL0        CL_a        CLmin       CLmax       "
                "CD0         CD2u        CD2l        CLCD0       REref   REexp\n")
        f.write(qprop_line + "\n")
 
    print(f"Arquivo QProp salvo: {output_path}")
    print(f"\n{qprop_line}")
 
    return params


def update_database_by_polar(polar_file, db_path=DB_PATH):
    '''
    Executa o XFoil para cada combinação (airfoil, Re) e atualiza o banco CSV.
 
    Comportamento:
        - Se o banco ainda não existir, ele é criado do zero.
        - Combinações (airfoil, Re) já presentes no banco são puladas
          automaticamente, sem rodar o XFoil nem pedir confirmação.
        - Para cada nova combinação, plota a polar, exibe a classificação
          e pede confirmação interativa antes de salvar.
 
    Parâmetros
    ----------
    polar_file : str
        Caminhos do arquivo da polar .t
    db_path : str, optional
        Caminho completo do arquivo CSV do banco.
        Default: polar_database.csv na pasta do projeto.
    '''

    if os.path.exists(db_path):
        db = pd.read_csv(db_path)
        print(f"Banco carregado: {db_path}  ({len(db)} linhas)")
    else:
        db = pd.DataFrame(columns=["alpha", "CL", "CD", "Re", "airfoil"])
        print("Banco não encontrado. Criando um novo.")
 
    new_entries = []
 
    for airfoil in airfoils:
 
        xfoil        = XFoil(airfoil)
        airfoil_name = os.path.basename(airfoil).replace(".dat", "")
 
        for Re in Res:
 
            if ((db["airfoil"] == airfoil_name) & (db["Re"] == Re)).any():
                print(f"  [skip] {airfoil_name}  Re={Re} já está no banco")
                continue
 
            print(f"\nRodando {airfoil_name}  Re={Re}")
 
            try:
                results = xfoil.aseq(alpha_start=alpha_start, alpha_end=alpha_end,
                                     alpha_step=alpha_step, reynolds=Re)
            except Exception as e:
                print(f"  Falha no XFoil: {e}")
                continue
 
            status = classify_polar(results)
            plot_polar(results, airfoil_name, Re, status)
 
            if not user_decision():
                print("  Descartado")
                continue
 
            new_entries.append(pd.DataFrame({
                "alpha":   results["alpha"],
                "CL":      results["CL"],
                "CD":      results["CD"],
                "Re":      Re,
                "airfoil": airfoil_name,
            }))
 
    if new_entries:
        new_df = pd.concat(new_entries, ignore_index=True)
        db     = pd.concat([db, new_df], ignore_index=True)
        db.to_csv(db_path, index=False)
        print(f"\nBanco salvo: {db_path}  (+{len(new_df)} linhas, total {len(db)})")
    else:
        print("\nNenhuma entrada nova adicionada.")
#-------------------------------------------------------#
# Exemplo de uso

airfoils = [
    #'airfoils/NACA0012.dat',
    #'airfoils/NACA2412.dat',
    #'airfoils/NACA4412.dat'
    #'airfoils/ClarkY.dat'
    'airfoils/E63.dat'
    #'airfoils/s1223.dat'
    
    ]

#Re = [50000, 80000, 100000, 120000, 150000]
Re = [50000, 70000, 100000, 120000, 140000]
Re = [100000]
for airfoil in airfoils:
    update_database(
        airfoils    = [airfoil],
        Res         = Re,
        alpha_start = -5,
        alpha_end   = 8,
        alpha_step  = 0.5 )