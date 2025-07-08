import os
import subprocess
from typing import Optional

from rich import get_console

def run_dummy_process() -> Optional[int]:
    """Inicia um processo de teste ('dummy.py') e retorna seu PID.

    Esta função localiza e executa o script 'dummy.py' como um processo
    filho usando 'subprocess.Popen'.

    Returns:
        Optional[int]: O ID do processo (PID) recém-criado em caso de sucesso,
                       ou None se o arquivo 'dummy.py' não for encontrado.
    """
    console = get_console()
    try:
        dummy_path = os.path.join(os.getcwd(), 'src', 'utils', 'dummy.py')
        if not os.path.exists(dummy_path):
            raise FileNotFoundError
        process = subprocess.Popen(
            ['/usr/bin/python3', '-u', dummy_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process.pid
    except FileNotFoundError:
        console.print("\n[bold red][!] 'dummy.py' não encontrado. Verifique se o arquivo existe no caminho esperado.[/bold red]")
        return None


class TracerConfig:
    """Stores all configuration for the tracer."""
    def __init__(self):
        self.instr_pointer = False
        self.string_max_length = 256
        self.max_array_count = 20
        self.write_address = True
        self.show_pid = True
        self.show_name = True
        self.show_ret_val = True
        self.show_args = True
        self.write_argname = True
        self.write_types = True