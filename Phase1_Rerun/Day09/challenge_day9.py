#A script that:
#Takes a list of numbers (with duplicates)
#Removes duplicates using a set
#Sorts the unique numbers back into a list
#prinsts results

nums = [5, 2, 2, 3, 5, 7, 1]
dupes_sorted = sorted(set(nums))
print(dupes_sorted)

captains = {}
captains["Enterprise"] = "Picard"
captains["Voyager"] = "Janeway"
captains["Defiant"] = "Sisko"

if  "Discovery" not in captains:
    captains["Discovery"] = "Unknown"

print(captains)   

for ship, captain in captains.items():
    print(f"The {ship} is captained by {captain}")
