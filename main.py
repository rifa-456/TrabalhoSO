from rich import get_console

from src.ui.menu import MainMenu
from src.ui.utils import print_title


def main():
    """Função principal que controla o início do programa.

    Esta função serve como o entry point do script.

    Returns:
        None: A função não retorna nenhum valor.
    """
    console = get_console()
    try:
        main_menu = MainMenu()
        main_menu.show()
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        console.print("\n[bold green]Obrigado por utilizar nosso programa![/bold green]")


if __name__ == "__main__":
    main()
