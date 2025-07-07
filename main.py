import os
import sys
import argparse
from datetime import datetime
from ptrace.debugger import PtraceDebugger, ProcessExit, ProcessSignal
import os
import signal
import subprocess
import time


def run_dummy_process():
    """Launch a dummy process and return its PID"""
    process = subprocess.Popen(['python3', 'dummy.py'],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    # Give it time to start
    time.sleep(1)
    output = process.stdout.readline().decode().strip()
    pid = int(output.split(':')[1].strip())
    print(f"Started dummy process with PID: {pid}")
    return pid

def is_process_running(pid):
    """Check if the process with given PID is running"""
    try:
        os.kill(pid, 0)  # Signal 0 doesn't kill the process but checks if it exists
        return True
    except OSError:
        return False


def attach_and_trace(pid):
    """
    Attaches to an existing process by its PID and logs its syscalls.
    """
    if not is_process_running(pid):
        print(f"[!] Process {pid} does not exist. Please check the PID.")
        return

    print(f"[*] Attempting to attach to PID: {pid}\n")

    debugger = PtraceDebugger()
    try:
        process = debugger.addProcess(pid, is_attached=False)
        print(f"[*] Successfully attached to PID: {pid}. Tracing syscalls...")
        print("-" * 60)

        # Track whether we're entering or exiting a syscall
        in_syscall = False

        process.syscall()
        while True:
            try:
                event = debugger.waitSyscall()
                process_event = event.process

                # Toggle between syscall entry and exit
                if in_syscall:
                    # Exiting syscall
                    syscall = process_event.syscall_state.syscall
                    result = process_event.syscall_state.result
                    print(f"SYSCALL EXIT: {syscall.name} = {result}")
                    in_syscall = False
                else:
                    # Entering syscall
                    syscall = process_event.syscall_state.syscall

                    # Get arguments from registers instead of trying to use arguments attribute
                    arg_values = []
                    for reg in process_event.syscall_state.registers:
                        if reg.startswith('arg'):  # arg0, arg1, etc.
                            arg_values.append(process_event.syscall_state.registers[reg])

                    arg_str = ", ".join(str(arg) for arg in arg_values)
                    print(f"SYSCALL ENTER: {syscall.name}({arg_str})")
                    in_syscall = True

            except ProcessExit as e:
                print(f"\n[*] Process {e.pid} exited with code {e.exit_code}.")
                break
            except ProcessSignal as e:
                e.display()  # Use the display method from ProcessSignal
                # Continue tracing after signal
            except Exception as e:
                print(f"\n[!] An unexpected error occurred: {e}")
                break

            # Allow the traced process to continue to the next syscall
            process_event.syscall()

    except Exception as e:
        print(f"[!] Failed to attach or trace PID {pid}. Error: {e}")
        print("[!] Ensure the PID exists and you have the necessary permissions (run with sudo).")
    finally:
        print("-" * 60)
        print("\n[*] Detaching from all processes and quitting.")
        debugger.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A Python syscall logger using ptrace to attach to a running process.",
        epilog="Example: sudo python3 syscall_tracer.py -p 1234"
    )
    parser.add_argument(
        "-p", "--pid",
        type=int,
        help="The Process ID (PID) of the program to attach to."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a test dummy process and trace it"
    )
    args = parser.parse_args()
    if os.geteuid() != 0:
        print("[!] This script must be run as root to use ptrace.")
        sys.exit(1)
    if args.test:
        pid = run_dummy_process()
    elif args.pid:
        pid = args.pid
    else:
        print("[!] You must provide either a PID (-p) or use --test flag")
        sys.exit(1)
    attach_and_trace(pid)