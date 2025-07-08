import select
import sys
from ptrace.debugger import PtraceDebugger
from ptrace.error import PtraceError
from loguru import logger
from src.utils.logger import setup_loggers
import tty


class SyscallTracer:
    """Comanda o rastreamento de chamadas de sistema (syscalls) para um processo.

    Esta classe utiliza a biblioteca 'python-ptrace'
    (uma biblioteca que faz o bind da biblioteca ptrace de C para python) para se anexar a um
    processo existente, interceptar suas chamadas de sistema e registrá-las de forma legível.

    Attributes:
        config (TracerConfig): Objeto `config` obrigatório que a biblioteca python-ptrace pede.
    """

    def __init__(self, config):
        """Inicializa o SyscallTracer.

        Args:
            config (TracerConfig): O objeto de configuração para o rastreador.
        """

        self.config = config

    def attach_and_trace(self, pid):
        """Anexa-se a um processo e inicia o rastreamento de syscalls.

        Este método gerencia todo o ciclo de vida do rastreamento: anexa-se ao
        PID, entra em um loop para esperar e processar eventos de syscall, e
        garante a limpeza e o desanexamento adequados no final.
        O rastreamento continua até que uma tecla seja pressionada no console.

        Args:
            pid (int): O ID do processo (PID) ao qual se anexar.
        """

        log_dir_path = setup_loggers(pid)
        debugger = PtraceDebugger()

        try:
            logger.info(f"Tentando se anexar ao processo: {pid}...")
            process = debugger.addProcess(pid, is_attached=False)
            logger.success(f"Axenado com sucesso ao processo de PID: {pid}. Escutando syscalls...")
            logger.info("Pressione qualquer tecla para parar de escutar.")
            logger.info("-" * 80)
            process.syscall()
            tty.setcbreak(sys.stdin.fileno())
            while True:
                if select.select([sys.stdin], [], [], 0)[0]:
                    sys.stdin.read(1)
                    logger.info("Tecla pressionada. Parando o rastreamento...")
                    logger.info(f"Os arquivos de log (estruturado e não estruturado) vão ser salvos em: {log_dir_path}")
                    break
                event = debugger.waitSyscall()
                if event:
                    self._handle_event(event)
                    event.process.syscall()

        except PtraceError as e:
            logger.error(f"Um erro de Ptrace ocorreu: {e}")

        except Exception:
            logger.exception("Um erro inesperado ocorreu.")

        finally:
            logger.info("-" * 80)
            logger.info("Limpando e desanexando-se do processo.")
            try:
                debugger.quit()
                logger.success("Debugger fechado e desanexado com sucesso.")
            except PtraceError as e:
                logger.error(f"Um erro inesperado de Ptrace ocorreu enquanto o debugger era fechado: {e}")

    def _handle_event(self, event):
        """Processa um único evento de syscall capturado pelo debugger.

        Esta função é chamada para cada evento (entrada ou saída de uma syscall).
        Ela extrai as informações relevantes, como nome da syscall, argumentos
        e valor de retorno, e as formata para registro no log.

        Args:
            event: O objeto de evento retornado por `debugger.waitSyscall()`.
        """

        process = event.process
        syscall_state = process.syscall_state

        if syscall_state.syscall:
            syscall = syscall_state.exit()
            if syscall:
                human_message = f"EXIT: {syscall.name} = {syscall.result_text}"
                logger.bind(
                    event_type="EXIT",
                    pid=process.pid,
                    syscall_name=syscall.name,
                    result_code=syscall.result,
                    result_text=syscall.result_text
                ).info(human_message)
            return

        else:
            syscall_state.enter(self.config)
            syscall = syscall_state.syscall
            if not syscall:
                return
            arg_texts = [arg.format() for arg in syscall.arguments]
            arg_values = [arg.value for arg in syscall.arguments]
            human_message = f"ENTER: PID={process.pid} | {syscall.name}({', '.join(arg_texts)})"
            logger.bind(
                event_type="ENTER",
                pid=process.pid,
                syscall_name=syscall.name,
                arguments=arg_values,
                arguments_text=arg_texts
            ).info(human_message)