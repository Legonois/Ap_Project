import os
import time
# open a file, read it, and print it

# open the file
file = open("Test.txt", "r")

# read the file
data = file.read()

# print the file
print(data)

# close the file
file.close()

size = os.get_terminal_size()

print(size)

for i in range(0, size.lines):
    for j in range(0, size.columns):
        print("*", end="")
        
    print()

for i in range(100):
    print("\u2588", end=" ") 
    print(i)
    time.sleep(0.1)
    os.system('cls')

# Create Cursor Character in console
print("\u2588", end="")

# Clear entire console window and reset cursor to top left
for i in range(0, size.lines):
    os.system('cls')

print("\u2588", end=" ") 
