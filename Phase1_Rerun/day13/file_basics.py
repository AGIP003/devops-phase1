with open('sample.txt', 'w') as f:
    f.write("Hello, World!\n")
    f.write("Python is awesome!\n")
    f.write("File I/O is important.\n")

print("="*60)
print("METHOD 1: Read entire file as string")
print("="*60)

with open('sample.txt', 'r') as file:
    content = file.read() # Reads entire file
    print(content)

 

print("\n" + "="*60)
print("METHOD 2: Read line by line")
print("="*60)

with open("sample.txt", "r") as f:
    for line in f:
        print(f"line: {line.strip()}")
file.close()

print("\n" + "="*60)
print("METHOD 3: Read into list of lines")
print("="*60)

with open('sample.txt', 'r') as f:
    liness = f.readlines() #Returns list
    print(f"Total lines: {len(liness)}")
    for i, line in enumerate(liness, 1):
        print(f"{i}. {line.strip()}")


with open('sample.txt', 'r') as f:
    content = f.read()
    print(content)


print("="*60)
print("WRITE MODE ('w') - Overwrites file")
print("="*60) 


with open('output.txt', 'w') as f:
    f.write("First line\n")
    f.write("Second line\n")

print("File written")

print("\n" + "="*60)
print("APPEND MODE ('a') - Adds to end")
print("="*60)

with open('output.txt', 'a') as f:
    f.write("Third line (appended)\n")
    f.write("Fourth line (appended)\n")

print("Lines appended!")

print("\n" + "="*60)
print("Reading back the file:")
print("="*60)

with open('output.txt', 'r') as f:
    content = f.read()
    print(content)
