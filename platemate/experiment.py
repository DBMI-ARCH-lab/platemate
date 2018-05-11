import sys

from food.models import chiefs
from management.run import run

photoset = sys.argv[1]
mode = sys.argv[-1]

run(
    chief_module=chiefs.from_static,
    args={'photoset': photoset, 'sandbox': (mode != 'real')},
    operation=photoset,
)
