import sys
from lib.db import del_claim

def main():
    # Check if there are command line arguments (excluding the script name)
    try:
        numbers = [int(arg) for arg in sys.argv[1:]]
    except:
        print("Please provide a list of integer claim ids to delete.")
        return
        
    ok = input("Will delete claims {}, proceed?".format(numbers))
    if ok.lower() != 'y':
        return

    for x in numbers:
        del_claim(x)

if __name__ == "__main__":
    main()
