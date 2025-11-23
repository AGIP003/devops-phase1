import psutil
import os
import time
#import argparse
#
#parser = argparse.ArgumentParser(description="System Monitor CLI")
#parser.add_argument("--save", action="store_true", help="Save snapshot to JSON file")
#args = parser.parse_args()


def clear_screen():
    """Clear Terminal"""
    os.system('clear')

def get_cpu_info():
    """Get CPU Usage"""
    return {
        'usage percent': psutil.cpu_percent(interval=2), #waits for one second then reports avg use
        'count': psutil.cpu_count(),
        'freq': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
        'stats': psutil.cpu_stats()
    }

def get_memory_info():
    """Get memory usage"""
    mem = psutil.virtual_memory()
    return {
        'total': mem.total / (1024**3),
        'available': mem.available / (1024**3),
        'percent': mem.percent,
        'used': mem.used / (1024**3),
        'free': mem.free / (1024**3)
    }

def get_top_processes(n=10):
    """Get top N processes by CPU"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    #Sort by CPU
    processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
    return processes[:n]

def get_disk_usage(path = '/'):
    """Get disk usage using psutil.
    
    Returns dict with:
    - total: Total disk space in bytes
    - used: Used space in bytes
    - free: Free space in bytes
    - percent: Usage percentage
    
    Learned: disk_usage() takes a path ('/' for root)
    """
    
    disk = psutil.disk_usage(path)
    return {
        'total': disk.total / (1024**3),
        'used': disk.used / (1024**3),
        'free': disk.free / (1024**3),
        'percent': disk.percent
    }



def display_stats():
    """Display all Stats""" 
    cpu = get_cpu_info()
    print("SYSTEM MONITOR")
    print("CPU USAGE")
    print(f"  Usage: {cpu['usage percent']}%")
    print(f"  Cores: {cpu['count']}")
    print(f"  Freq:  {cpu['freq']:.0f} MHz")    
    print(f" Stats: {cpu['stats']}")     

    mem = get_memory_info()
    print("MEMORY INFORMATION")
    print(f" Total: {mem['total']:.2f} GB")
    print(f" Available: {mem['available']:.2f}")
    print(f" Used: {mem['percent']}%")
    print(f" Used(non-percent): {mem['used']:.2f} GB")
    print(f" Free: {mem["free"]:.2f} GB")

    dsk = get_disk_usage()
    print("DISK USAGE")
    print(f" Total: {dsk['total']:.2f} GB")
    print(f" Used(non-percent): {dsk['used']:.2f} GB")
    print(f" Free: {dsk['free']:.2f} GB")
    print(f" Used: {dsk['percent']}%")
    
    
    processes = get_top_processes(10)
    for i, proc in enumerate(processes, 1):
        name = (proc['name'] or "Unkown")[:20]
        cpu_pct = proc['cpu_percent'] or 0
        print(f" {i}. {name:<20} {cpu_pct:>5.1f}%")

    print(f"\n{'='*50}")
    print("Press Ctrl+c to exit")



def main():
    """Main Loop"""
    try:
        while True:
            clear_screen()
            display_stats()
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n Bye!")

if __name__ == '__main__':
    main()

