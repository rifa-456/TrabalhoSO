import os
import sys
import argparse
from datetime import datetime
from ptrace.debugger import PtraceDebugger, ProcessExit, ProcessSignal
import os
import signal
import subprocess
import time

# This options class MUST contain the attributes the library's
# automatic formatting functions will look for.
class SyscallOptions:
    def __init__(self):
        # Max length of a string read from the child's memory.
        self.string_max_length = 256
        # Max number of elements to read from an array (e.g., for execve).
        self.max_array_count = 20
        # These were the original flags.
        self.write_argname = True
        self.write_types = True
        self.write_address = True
        self.instr_pointer = False
        self.replace_socketcall = False

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

        process.syscall()
        while True:
            try:
                event = debugger.waitSyscall()
                process_event = event.process

                if process_event.syscall_state.syscall:
                    # EXIT: The syscall object exists from the entry.
                    syscall = process_event.syscall_state.exit()

                    if syscall:
                        result = syscall.result_text
                        print(f"SYSCALL EXIT: {syscall.name} = {result}")
                else:
                    # ENTER: No syscall object exists yet.
                    options = SyscallOptions()
                    process_event.syscall_state.enter(options)
                    syscall = process_event.syscall_state.syscall

                    if syscall:
                        # --- THE FINAL FIX ---
                        # We must explicitly call .format() on each argument.
                        # This tells the library to do the expensive work of
                        # reading memory and dereferencing pointers. It will now
                        # work because our options object is complete.
                        for arg in syscall.arguments:
                            print(arg.format())
                        # --- END OF FIX ---

                        print(f"SYSCALL ENTER: {syscall.name}")

            except ProcessExit as e:
                print(f"\n[*] Process {e.pid} exited with code {e.exit_code}.")
                break
            except ProcessSignal as e:
                e.display()
            except Exception as e:
                print(f"\n[!] An unexpected error occurred: {e}")
                break

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
    args = parser.parse_args()
    if os.geteuid() != 0:
        print("[!] This script must be run as root to use ptrace.")
        sys.exit(1)
    if args.pid:
        pid = args.pid
    else:
        print("[!] You must provide either a PID (-p) or use --test flag")
        sys.exit(1)
    attach_and_trace(pid)