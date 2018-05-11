import glob
import os

from django.conf import settings

import management.models as base
from food.models import identify, measure, tag
from food.models.common import *

class Output(base.Output):
    photo = OneOf(Photo)
    box = OneOf(Box)
    ingredient_list = OneOf(IngredientList)

class Manager(base.Manager):

    def setup(self):
        self.hire(identify.describe, 'describe')

    def work(self):
        pass
