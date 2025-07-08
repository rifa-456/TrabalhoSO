import inquirer
import psutil
from rich import get_console
from .utils import pid_validation, print_title
from ..core.tracer import SyscallTracer
from ..utils.process_helpers import run_dummy_process, TracerConfig


class MainMenu:
    """Gerencia o fluxo da interface de usuário principal usando 'inquirer'.

    Esta classe é responsável por exibir os menus, coletar a entrada do
    usuário e iniciar o processo de rastreamento de syscalls com base
    nas escolhas feitas.

    Attributes:
        config (TracerConfig): Objeto de configuração para o tracer.
        console (Console): Instância do console 'rich' para impressão estilizada.
    """
    def __init__(self):
        """Inicializa a classe MainMenu."""
        self.config = TracerConfig()
        self.console = get_console()

    def show(self):
        """Exibe o menu principal em um loop contínuo.

        Apresenta as opções "Escutar Processo" ou "Sair",
        e direciona o fluxo do programa com base na seleção do usuário.
        O loop termina quando o usuário escolhe sair.
        """
        while True:
            print_title()
            main_menu_question = [
                inquirer.List(
                    "choice",
                    message="Escolha uma opção abaixo",
                    choices=[
                        ("Escutar Processo", "e"),
                        ("Sair", "s")
                    ],
                )
            ]
            answer = inquirer.prompt(main_menu_question)
            choice = answer.get('choice')
            if choice == 's':
                break
            elif choice == 'e':
                self._show_listen_menu()

    def _show_listen_menu(self):
        """Exibe o submenu para selecionar um processo a ser rastreado.

        Oferece ao usuário as opções de digitar um PID manualmente, iniciar um
        processo de teste para rastreamento ou voltar ao menu anterior. Após obter
        um PID válido, instancia e executa o `SyscallTracer`.
        """
        pid_to_trace = None
        listen_menu_question = [
            inquirer.List(
                "choice",
                message="Escolha a opção desejada: ",
                choices=[
                    ("Digitar PID manualmente", "p"),
                    ("Escutar um processo teste", "t"),
                    ("Voltar para o menu inicial", "v")
                ],
            )
        ]
        answer = inquirer.prompt(listen_menu_question)
        choice = answer.get('choice')

        if choice == 'v':
            return

        if choice == 'p':
            pid_question = [
                inquirer.Text(
                    "pid",
                    message="Digite o PID do processo que deseja escutar",
                    validate=pid_validation,
                ),
            ]
            pid_answer = inquirer.prompt(pid_question)
            pid_to_trace = int(pid_answer['pid'])

        elif choice == 't':
            self.console.print("[cyan]Iniciando processo de teste...[/cyan]")
            pid_to_trace = run_dummy_process()
            if pid_to_trace:
                self.console.print(f"[bold green]Processo de teste iniciado com PID: {pid_to_trace}[/bold green]")

        if psutil.pid_exists(pid_to_trace):
            tracer = SyscallTracer(self.config)
            tracer.attach_and_trace(pid_to_trace)
            self.console.input("\n[yellow]Rastreamento finalizado. Pressione Enter para voltar ao menu...[/yellow]")
        else:
            self.console.print(f"[bold red]Não foi possível encontrar um processo com PID {pid_to_trace}.[/bold red]")