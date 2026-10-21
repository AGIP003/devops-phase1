#Two strings are anagrams if they contain exactly the same characters,
 #with exactly the same frequencies, but potentially in a different order.

frequency = {}
word = "abb"

for char in word:
    if char in frequency:
        frequency[char] += 1
        print("Already encountered:", char)
    else:
        frequency[char] = 1
        print("First encounter:", char)

print(frequency)


def is_anagram(s, t):
    # 1. Check if lengths are different
    if len(s) != len(t):
        return False
        
    freq_s = {}
    freq_t = {}

    # 2. Count characters in s
    for char in s:
        if char in freq_s:
            freq_s[char] += 1
        else:
            freq_s[char] = 1

    # 3. Count characters in t
    for char in t:
        if char in freq_t:
            freq_t[char] += 1
        else:
            freq_t[char] = 1

    # 4. Compare the dictionaries
    if freq_s == freq_t:
        return True
    return False

print(is_anagram("anagram", "nagaram"))  # True
print(is_anagram("rat", "car"))          # False
print(is_anagram("aab", "abb"))          # False
print(is_anagram("", ""))              # True
print(is_anagram("ab", "a"))            # False

#single string implementation

def is_anagram(s, t):
    if len(s) != len(t):
        return False

    frequency = {}

    for char in s:
        # Count how often each character appears
        if char in frequency:
            frequency[char] += 1
        else:
            frequency[char] = 1
        # Use if/else, just like your banana exercise
    
    for char in t:
        if char not in frequency:
            return False

        frequency[char] -= 1
        
    if frequency[char] == 0:
        return True
    else:
        return False