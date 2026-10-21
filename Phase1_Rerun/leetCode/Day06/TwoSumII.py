
def two_sum_ii(numbers, target):
    left = 0
    right = len(numbers) - 1

    while left < right:
        # 1. Calculate the current sum
        current_sum = numbers[left] + numbers[right]

        # 2. If the sum matches target:
        if current_sum == target:
            return [left + 1, right + 1]
        #    Return one-based positions

        # 3. If the sum is too small:
        elif current_sum < target:
            left += 1
        #    Move left forward
        else:
            right -= 1
   