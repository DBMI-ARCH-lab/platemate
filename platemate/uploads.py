import sys

from food.models import chiefs
from management.run import run

# Example usage: "python uploads.py sandbox"
operation = sys.argv[1]
mode = sys.argv[-1]

run(
    chief_module=chiefs.from_uploads,
    args={'sandbox': (mode != 'real')},
    operation=operation
)
