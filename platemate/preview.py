import sys

from food.models import chiefs
from management.run import run

run(
    chief_module=chiefs.preview,
    operation='preview',
)
