import psutil
import os
import time

def clear_screen():
    """Clear Terminal"""
    os.system('clear')

def get_cpu_info():
    """Get CPU Usage"""
    return {
        'usage percent': psutil.cpu_percent(interval=1), #waits for one second then reports avg use
        'count': psutil.cpu_count(),
        'freq': psutil.cpu_freq().current if psutil.cpu_freq() else 0
    }

def get_memory_info():
    """Get memory usage"""
    mem = psutil.virtual_memory()
    return {
        'total': mem.total / (1024**3),
        'available': mem.available / (1024**3),
        'percent': mem.percent,
        'used': mem.used / (1024**3)
    }

def get_top_processes(n=5):
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

def display_stats():
    """Display all Stats""" 
    cpu = get_cpu_info()
    print("SYSTEM MONITOR")
    print(f"  Usage: {cpu['usage percent']}%")
    print(f"  Cores: {cpu['count']}")
    print(f"  Freq:  {cpu['freq']:.0f} MHz")         

    mem = get_memory_info()
    print(f" Total: {mem['total']:.2f} GB")
    print(f" Available: {mem['available']:.2f}")
    print(f" Used: {mem['percent']}%")
    
    processes = get_top_processes(5)
    for i, proc in enumerate(processes, 1):
        name = proc['name'][:20]
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
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n Bye!")

if __name__ == '__main__':
    main()