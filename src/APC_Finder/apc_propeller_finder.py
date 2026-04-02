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

SRC = Path(r"/home/duncan/Desktop/26.1/projects/APC-Propeller-Finder/src") # diretório no PC

sys.path.insert(0, str(SRC))

from Objects.Geometry import *