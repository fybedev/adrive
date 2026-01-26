import shutil
import subprocess
import os
import sys
import zipfile
from rich.progress import Progress
from rich.console import Console
import requests
from .. import prompt
from time import sleep

console = Console()

def check_dependencies():
    """Check if required dependencies are installed."""
    required_tools = ["git", "curl", "tar", "wget"]
    missing_tools = [tool for tool in required_tools if shutil.which(tool) is None]
    
    if missing_tools:
        print("The following required tools are missing:")
        for tool in missing_tools:
            print(f"- {tool}")
            if tool == "wget":
                if prompt.prompt_yes_no("Would you like to install 'wget' using brew?"):
                    subprocess.run(['brew', 'install', 'wget'])
                    print("'wget' has been installed.")
                else:
                    print("Please install 'wget' manually to proceed.")
                    exit(1)
        exit(1)
    else:
        print("All required tools are installed.")

def check_python_dependencies():
    """Check if required Python packages are installed."""
    try:
        import requests
    except ImportError:
        print("requests library is required. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'requests'])
        print("requests has been installed.")

def detect_installation() -> bool:
    """Detect if LightDB is already installed."""
    installation_path = "lightdb"
    if os.path.exists(installation_path):
        return True
    else:
        return False
    
def install_lightdb():
    check_dependencies()
    check_python_dependencies()
    print("Starting LightDB installation...")
    installation_path = "lightdb"
    url = "https://fybe.dev/ldb/ldb.zip"
    zip_path = "lightdb.zip"
    
    with Progress() as progress:
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        if total_size > 0:
            task = progress.add_task("Downloading LightDB...", total=total_size)
            downloaded = 0
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    sleep(0.3)
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress.update(task, completed=downloaded)
        else:
            task = progress.add_task("Downloading LightDB...", total=None)
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        files = zip_ref.namelist()
        total_files = len(files)
        with Progress() as progress:
            task = progress.add_task("Unzipping LightDB...", total=total_files)
            for file in files:
                sleep(0.3)
                zip_ref.extract(file, installation_path)
                progress.update(task, advance=1)
    
    os.remove(zip_path)
    with console.status("[bold cyan]Verifying LightDB installation...", spinner="dots"):
        sleep(0.3)
        if os.path.exists(installation_path) and len(os.listdir(installation_path)) > 0:
            console.print("[green]✓ LightDB directory verified[/green]")
        else:
            console.print("[red]✗ Installation verification failed[/red]")
    
    with console.status("[bold cyan]Checking LightDB modules: [bold magenta]base", spinner="dots"):
        sleep(0.5)
        if os.path.exists(installation_path + '/__init__.py'):
            console.print("[green]✓ Module verified: [/green][bold magenta]base[/bold magenta]")
        else:
            console.print("[red]✗ Module verification failed[/red]")
    
    with console.status("[bold cyan]Checking LightDB modules: [bold magenta]dbconnect", spinner="dots"):
        sleep(0.5)
        if os.path.exists(installation_path + '/dbconnect.py'):
            console.print("[green]✓ Module verified: [/green][bold magenta]dbconnect[/bold magenta]")
        else:
            console.print("[red]✗ Module verification failed:[/red] [bold cyan underline]dbconnect[/bold cyan underline]")
    console.print('\n[bold green]LightDB has been successfully installed![/bold green]')
