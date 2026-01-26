from .installer import install_lightdb, detect_installation
from .prompt import prompt_yes_no

def verify_args(args):
    if not args:
        raise ValueError("No arguments provided.")
    
def run_cli(args):
    print("=== LightDB CLI ===")
    if args[0] == "install":
        if detect_installation():
            print("LightDB is already installed in the current working directory, exiting.")
            exit(0)
        if prompt_yes_no("This command will install LightDB in the current working directory. Do you want to continue?"):
            install_lightdb()
    else:
        print(f"Unknown command: {args[0]}")