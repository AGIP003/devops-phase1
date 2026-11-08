#Brute Force
def max_profit(prices):
    max_profit = 0
    n = len(prices)

    for i in range(n):

        # Start j AFTER i so we sell later
        for j in range(i + 1, n):

            # Calculate profit for buying
            # at i and selling at j
            profit = prices[j] - prices[i]

            # Update max_profit only if
            # this profit is better
            if profit > max_profit:
                max_profit = profit
            
    return max_profit
    # Return the best profit found

print(max_profit([7, 1, 5, 3, 6, 4]))  # 5
print(max_profit([7, 6, 4, 3, 1]))     # 0
print(max_profit([8, 3, 6, 2, 9, 4]))  # 7
print(max_profit([5]))                 # 0

#DSA
# O(n) time: One traversal.
# O(1) auxiliary space: No growing list or dictionary.
def max_profit_optimized(prices):

    # Assume prices is nonempty.
    if not prices:
        return 0
    # Initialize the minimum using the first price.
    min_price = prices[0]

    # No profit discovered yet
    max_profit = 0

    # Traverse the remaining prices
    for price in prices:

        # Calculate profit if we sell today
        profit = price - min_price

        # Update max_profit if we've found
        # a better selling opportunity
        if profit > max_profit:
            max_profit = profit

        # Update min_price if today's
        # price is cheaper
        if price < min_price:
            min_price = price
        

    return max_profit

print(max_profit_optimized([7, 1, 5, 3, 6, 4]))  # 5
print(max_profit_optimized([7, 6, 4, 3, 1]))     # 0
print(max_profit_optimized([1, 3, 6, 2, 9, 4]))  # 7
print(max_profit_optimized([5]))                 # 0