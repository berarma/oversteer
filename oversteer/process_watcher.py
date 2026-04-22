import logging
import os

logger = logging.getLogger(__name__)


def get_running_processes():
    """Return a set of process names from /proc."""
    processes = set()
    try:
        for pid in os.listdir('/proc'):
            if not pid.isdigit():
                continue
            try:
                comm_path = os.path.join('/proc', pid, 'comm')
                with open(comm_path, 'r') as f:
                    name = f.read().strip()
                    if name:
                        processes.add(name)
                # Also resolve exe symlink for Wine/Proton games
                exe_path = os.path.join('/proc', pid, 'exe')
                try:
                    exe = os.path.realpath(exe_path)
                    basename = os.path.basename(exe)
                    if basename and basename not in ('', 'None'):
                        processes.add(basename)
                except (OSError, FileNotFoundError):
                    pass
            except (OSError, FileNotFoundError, PermissionError):
                continue
    except OSError:
        pass
    return processes


def detect_game(processes, profile_processes_map):
    """
    Given a set of running process names and a dict of
    {profile_name: [process_names]}, return the matching profile name
    or None.
    """
    for profile_name, proc_list in profile_processes_map.items():
        for proc in proc_list:
            # Case-insensitive match, handle both .exe and native names
            proc_lower = proc.lower()
            for running in processes:
                if running.lower() == proc_lower:
                    return profile_name
                # Partial match for Wine/Proton paths like "steamapps/common/AMS2"
                if proc_lower.replace('.exe', '') in running.lower():
                    return profile_name
    return None
