#Big O describes how the amount of computational work or memory,
#   required by an algorithm grows as its input gets larger.
#As the number of elements increases, the number of iterations increases proportionally.
#   That's called linear time complexity, written as O(n).
# Auxiliary space tells us how much additional memory it needs as the input grows, excluding the input array itself.

def contains_duplicate(nums):
    seen = set()

    for value in nums:
        if value in seen:
            return True
        else:    
            seen.add(value)
    return False

print(contains_duplicate([1, 2, 3, 1]))  # True
print(contains_duplicate([1, 2, 3, 4]))  # False
print(contains_duplicate([5, 5]))        # True
print(contains_duplicate([]))            # False