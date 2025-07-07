import os
import sys
import argparse
from datetime import datetime
from ptrace.debugger import PtraceDebugger, ProcessExit, ProcessSignal

def attach_and_trace(pid):
    """
    Attaches to an existing process by its PID and logs its syscalls.
    """
    print(f"[*] Attempting to attach to PID: {pid}\n")

    debugger = PtraceDebugger()
    try:
        # Attach to the existing process.
        # is_attached=True is crucial for attaching, not creating.
        process = debugger.addProcess(pid, is_attached=True)
        print(f"[*] Successfully attached to PID: {pid}. Tracing syscalls...")
        print("-" * 60)

        # Main loop to capture syscalls
        while True:
            # Wait for the next syscall event from the process
            try:
                event = debugger.waitSyscall()
            except ProcessExit as e:
                print(f"\n[*] Process {e.pid} exited with code {e.exit_code}.")
                break
            except Exception as e:
                print(f"\n[!] An unexpected error occurred: {e}")
                break

            # A syscall event was captured
            syscall = event.syscall

            if syscall:
                # 'is_enter' is True when the syscall is first made
                if syscall.is_enter:
                    timestamp = datetime.now().isoformat()
                    syscall_name = syscall.name
                    arguments = syscall.arguments

                    # Format arguments for clear display
                    formatted_args = ", ".join(map(str, arguments))

                    # Print without a newline to keep entry and exit on the same line
                    print(f"[{timestamp}] PID: {pid} | {syscall_name}({formatted_args})", end='', flush=True)

                # 'is_enter' is False when the syscall returns
                else:
                    return_value = syscall.result
                    print(f" = {return_value}")

            # Allow the traced process to continue to the next syscall
            process.syscall()

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
        required=True,
        help="The Process ID (PID) of the program to attach to."
    )
    args = parser.parse_args()

    # 2. Check for root privileges, which are required for ptrace
    if os.geteuid() != 0:
        print("[!] This script must be run as root to use ptrace.")
        sys.exit(1)

    # 3. Call the main tracing function
    attach_and_trace(args.pid)