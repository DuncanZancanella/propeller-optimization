# ==============================================================
# 0) Bibliotecas
# ==============================================================

import sys
import os
from pathlib import Path

# ==============================================================
# 1) Chamar projeto "APC-Propeller-Finder"
# ==============================================================

# --- Importar bibioteca APC-Propeller-Finder (definir diretório)

SRC = Path(r"C:\Users\dunca\Desktop\UFSC\APC - Propeller data\src") # diretório no PC

sys.path.insert(0, str(SRC))