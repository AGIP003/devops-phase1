#anagram signature → list of words
#The signature is a representation that should be identical,
#  for all words belonging to the same anagram group
#Hint: You need sorted(), join(), an empty list [], and append()

words = ["eat", "tea", "bat", "ate"]
groups = {}

for word in words:
    # 1. Generate a sorted string key
    key = "".join(sorted(word))

    # 2. Initialize an empty list if key is new
    if key not in groups:
        groups[key] = []

    groups[key].append(word)

#print(groups)

#print(list(groups.values()))

def group_anagrams(strs):
    groups = {}

    for word in strs:
        key = "".join(sorted(word))

        if key not in groups:
            groups[key] = []
        
        groups[key].append(word)
    
    return list(groups.values())

print(group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]))

print(group_anagrams([""]))

print(group_anagrams(["a"]))
print(group_anagrams(["ab", "ba", "abc", "cab"]))