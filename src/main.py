from cellsepi.__main__ import main
import os
os.environ["SCIKIT_IMAGE_NO_LAZY"] = "1"

if __name__ == "__main__":
    main()
