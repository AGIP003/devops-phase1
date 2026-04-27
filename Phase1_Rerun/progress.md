#Project Progress
## PROJECT 1 - System Monitor
- The idea is to: - ├─ Read data from system
                    ├─ Display in real-time
                    └─ Export snapshots


## Week 1: MVP 
- [x] Basic CPU/Memory display
- [x] Top processes
- [x] Fixed None name bug
- [x] Real-time updates
- [x] Disk usage 
- [x] Network stats
- [x] Color output
- [ ] File export 
- [x] CLI arguments (argparse)
- [x] Save to JSON file
- [ ] Config file (YAML/JSON)
- [x] Network uplad/download
- [ ] Historical data (track over time)
- [ ] Alert if CPU > 90%


## Bugs Found & Fixed:
1. Process name = None → Fixed with defensive check
2. When calling the function dont forget the brackets

## Things I Learned:
1. psutil returns None for some process names
2. Always check for None before slicing strings
3. disk usage and memory info one needs to break them down in dicts to standardize and make it presentable
4. Download speed is calculated through bytes
5. Packets - how many messages
6. Bytes - how much data
7. For the download speed one needs to call the psutil.net_io_counters() twice with a time interval between so as to accurately measure the difference and get the upload and download speed.
8. Fore.RED sets text color to red.
   Back.GREEN sets background color to green.
   Style.DIM lowers the text intensity (dim effect).
   Style.RESET_ALL resets everything (color + style).
   After resetting, the last line prints normally.


## PROJECT 2: Finance Tracker
- The idea is to: - ├─ Accept user input
                    ├─ Validate data
                    ├─ Store persistently
                    ├─ Query & filter
                    └─ Generate reports


# Finance Tracker - Progress

## ✅ Phase 1: Core CRUD 
- [x] Add transaction ⏳ START HERE
- [x] List transactions
- [x] Show balance
- [x] Delete transaction
- [x] Input validation working
- [x] JSON storage working
- [x] Git committed

## 🚧 Phase 2: Queries & Reports
- [x] Filter by category
- [x] Filter by date range
- [x] Monthly summary
- [x] Category breakdown
- [ ] Export to CSV

## 🔮 Phase 3: Advanced
- [ ] Multiple accounts
- [ ] Budgets & alerts
- [ ] Recurring transactions
- [ ] Charts (ASCII)

---
