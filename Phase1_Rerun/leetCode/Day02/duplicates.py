seen = set()  # Empty set
seen = {}     # Empty dictionary

numbers = [4, 2, 9, 4]
seen = set()

seen.add(numbers[0])
seen.add(numbers[1])
seen.add(numbers[2])
seen.add(numbers[3])

print(len(seen))
print(4 in seen)
print(7 in seen)

#Brute force
def contains_duplicate(nums):
    n = len(nums)

    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] == nums[j]:
                return True

    return False

print(contains_duplicate([1, 2, 3, 1]))
print(contains_duplicate([1, 2, 3, 2]))
print(contains_duplicate([5, 5]))
print(contains_duplicate([7]))           # False
print(contains_duplicate([])) 

#dsa
def contain_duplicate(nums):
    seen = set()

    for value in nums:
        if value in seen:
            return True
        
        seen.add(value)
    
    return False

print(contain_duplicate([1, 2, 3, 1]))
print(contain_duplicate([1, 2, 3, 2, 3, 4, 2, 5, 4]))
print(contain_duplicate([5, 5]))
print(contain_duplicate([7]))           # False
print(contain_duplicate([])) 