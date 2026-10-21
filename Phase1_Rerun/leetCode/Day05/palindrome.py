# A palindrome is a sequence that reads the same forwards and backwards.
#.lower() converts uppercase letters to lowercase.
#.isalnum() checks whether a character is a letter or number
#[::-1] creates a reversed copy of the string.

print("!".isalnum())
print("7".isalnum())
print(" ".isalnum())


def is_palindrome(s):
    cleaned = ""

    for char in s:
        # Check whether the character is alphanumeric
        if char.isalnum():
        # If valid, convert to lowercase
        # and add it to cleaned
            cleaned += char.lower()
        
    if cleaned == cleaned[::-1]:
        return True
    
    return False

print(is_palindrome("racecar"))   # True
print(is_palindrome("Race, car!"))# True
print(is_palindrome("race a car"))# False
print(is_palindrome("abca"))      # False
print(is_palindrome(""))         # True

def is_it_palindrome(s):
    # Compare cleaned with its reverse
    left = 0
    right = len(s) - 1

    while left < right:
        while left < right and not s[left].isalnum():
            left += 1
        
        while left < right and not s[right].isalnum():
            right -= 1

        if s[left].lower() != s[right].lower():
            return False

        left += 1
        right -= 1
        
    return True

print(is_it_palindrome("racecar"))   # True
print(is_it_palindrome("Race, car!"))# True
print(is_it_palindrome("race a car"))# False
print(is_it_palindrome("abca"))      # False
print(is_it_palindrome(""))         # True

    # Return the result
