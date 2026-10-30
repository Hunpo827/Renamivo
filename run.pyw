import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from renamer.app import main
sys.exit(main())
