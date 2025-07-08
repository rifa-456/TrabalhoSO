import art
import re
import inquirer
from inquirer import errors
from rich import get_console

def print_title():
    """Imprime um título estilizado da aplicação no console.

    Utiliza a biblioteca 'art' para gerar a arte ASCII e 'rich' para
    aplicar cores e estilos. A função imprime diretamente na saída padrão.
    """
    title_art = art.text2art("Sys Logger", font="small")
    console = get_console()
    console.print(f"[bold cyan]{title_art}[/bold cyan]")
    console.print("[bold yellow]Ferramenta de Logging de SysCalls[/bold yellow]", justify="center")
    console.print()

def pid_validation(_: any, current: str) -> bool:
    """Valida se a string fornecida contém apenas dígitos (0-9).

    Função de callback projetada para ser usada com a biblioteca 'inquirer'
    para validar a entrada de um Process ID (PID).

    Args:
        _ (any): Um argumento não utilizado, necessário para a assinatura da função de validação do inquirer.
        current (str): A string de entrada a ser validada.

    Returns:
        bool: Retorna True se a validação for bem-sucedida.

    Raises:
        inquirer.errors.ValidationError: Lançada se a string contiver
            qualquer caractere que não seja um dígito.
    """
    if not re.match(r"^[0-9]+$", current):
        raise inquirer.errors.ValidationError(
            "",
            reason="O PID deve ser composto apenas por números (0-9)"
        )
    return True