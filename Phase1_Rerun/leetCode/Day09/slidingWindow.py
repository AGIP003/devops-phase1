
def length_of_longest_substring(s):
    seen = set()
    left = 0
    longest = 0

    for right in range(len(s)):
        while s[right] in seen:
            seen.remove(s[left])
            left += 1
        
        seen.add(s[right])

        window_length = right - left + 1

        if window_length > longest:
            longest = window_length
        # If s[right] already exists in seen:
        # Keep removing s[left] and advancing left
        # until the duplicate is gone

        # Add s[right] to seen

        # Calculate current window length
        # and update longest

    return longest

print(length_of_longest_substring("abcabcbb"))  # 3
print(length_of_longest_substring("bbbbb"))     # 1
print(length_of_longest_substring("pwwkew"))    # 3
print(length_of_longest_substring("abba"))      # 2
print(length_of_longest_substring(""))          # 0
print(length_of_longest_substring("dvdf"))      # 3