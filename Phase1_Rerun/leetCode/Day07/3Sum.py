#In Two Sum, we found two numbers that add up to a target.
#In 3Sum, we need to find three numbers that add up to zero.

#We now have three positions:
#- i: the fixed number.
#- left: starts immediately after i.
#- right: starts at the end.

def three_sum(nums):
    nums.sort()
    result = []

    for i in range(len(nums) - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        
        left = i + 1
        right = len(nums) - 1
        # Check whether this fixed value
        # duplicates the previous fixed value

        # Initialize left and right

        # We'll add the two-pointer search next
        while left < right:
            current_sum = nums[i] + nums[left] + nums[right]

            if current_sum < 0:
                left += 1
            elif current_sum > 0:
                right -= 1
            else:
                result.append([nums[i], nums[left], nums[right]])

                left += 1
                right -= 1
            while left < right and nums[left] == nums[left + 1]:
                left += 1
            
            while left < right and nums[right] == nums[right - 1]:
                right -= 1


    return result
print(three_sum([-1, 0, 1, 2, -1, -4]))
print(three_sum([-2,0,1,1,2]))