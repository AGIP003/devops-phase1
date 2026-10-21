def two_sum (sum, target):
    seen = {}

    for i, value in enumerate(sum):
        complement = target - value
        
        if complement in seen:
            return (seen[complement], i)
        else:
            seen[value] = i
    
    
    
print(two_sum([2, 7, 11, 15], 9))  # [0, 1]
print(two_sum([3, 2, 4], 6))       # [1, 2]
print(two_sum([3, 3], 6))          # [0, 1]