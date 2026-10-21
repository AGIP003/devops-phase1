def two_sum(nums, target):
    seen = {}

    for i, num in enumerate(nums):
        complement = target - num

        if complement in seen:
            return [seen[complement], i]

        seen[num] = i #{3:0, 2:1} {3:0, }


print(two_sum([3, 2, 4], 6))
print(two_sum([3, 3], 6))
print(two_sum([5, 8, 1, 9], 10))