import sys
import traceback
from gui import main

if __name__ == "__main__":
    try:
        print("Starting Smart To-Do List application...")
        main()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        print("Traceback:")
        traceback.print_exc()
        sys.exit(1)