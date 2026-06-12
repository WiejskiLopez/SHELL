Krok 1: Usuń uszkodzone środowisko
W terminalu (będąc w folderze SHELL), wykonaj:

PowerShell
# Usuń folder venv (Windows PowerShell)
Remove-Item -Recurse -Force venv
Krok 2: Utwórz nowe środowisko
PowerShell
# Utwórz czyste środowisko
python -m venv venv
Krok 3: Aktywuj i zainstaluj pakiety
PowerShell
# Aktywuj nowe środowisko
.\venv\Scripts\activate

# Zaktualizuj pip (bardzo ważne w nowszych wersjach Pythona)
python -m pip install --upgrade pip

# Zainstaluj potrzebne narzędzia do testów
pip install pytest pytest-asyncio

pip install sqlalchemy aiosqlite

pip install httpx

pip install fastapi uvicorn

pip install dependency-injector
.