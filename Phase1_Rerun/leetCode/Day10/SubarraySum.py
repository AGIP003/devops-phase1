#Why initialize min_length to infinity?
#Because we're looking for a minimum. 
#  Every real window length will be smaller than infinity.

def min_subarray_len(target, nums):
    left = 0
    current_sum = 0
    min_length = float("inf")

    for right in range(len(nums)):
        # Expand the window by including nums[right]
        current_sum += nums[right]

        # While the window reaches the target:
        while current_sum >= target:
            window_length =  right - left + 1

            if window_length < min_length:
                min_length = window_length

            current_sum -= nums[left]
            left += 1
        #   Record its length if it's smaller
        #   Remove the leftmost number from the sum
        #   Advance left

    if min_length == float("inf"):
        return 0

    return min_length
    # Handle the case where no window qualified

print(min_subarray_len(7, [2, 3, 1, 2, 4, 3]))  # 2

print(min_subarray_len(4, [1, 4, 4]))           # 1

print(min_subarray_len(11, [1, 1, 1, 1]))       # 0

print(min_subarray_len(8, [2, 3, 5, 1, 1]))     # 2

print(min_subarray_len(5, [5]))                 # 1

print(min_subarray_len(7, []))                  # 0