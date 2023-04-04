import ScrollRenderer
import os
import asyncio
import pyEdit

def main():
    
    pyEdit = pyEdit()

    pyEdit.run()

if __name__ == "__main__":
    main()

    # wait for user to press enter
    print("Press enter to exit")
    input()