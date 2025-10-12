import sys

#Basic: sys.argv
print("="*60)
print("Command Line Arguments Demo")
print("="*60)

print(f"\nScript name: {sys.argv[0]}")
print(f"Arguments: {sys.argv[1:]}")
print(f"Total arguments: {len(sys.argv) - 1}")

if len(sys.argv) > 1:
    print("\n Processing arguments: ")
    for i, arg in enumerate(sys.argv[1:], 1):
        print(f" Arg {i}: {arg}*")

else:
    print("\n No arguments provided!")
    print("Usage: python.py <arg1> <arg2> ...")


