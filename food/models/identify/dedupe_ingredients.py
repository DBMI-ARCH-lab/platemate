from food.models.common import *
from management.helpers import *
from management.qualifications import *
import management.models as base
from urllib import unquote
from django.core.exceptions import ObjectDoesNotExist

class Input(base.Input):
    ingredient_list = OneOf(IngredientList)

class Output(base.Output):
    ingredient_list = OneOf(IngredientList)

class Job(base.Job):
    selected_ingredients = OneOf(IngredientList)
    unselected_ingredients = OneOf(IngredientList)
    iteration = IntegerField(default=1)

class Response(base.Response):
    selected_ingredients = OneOf(IngredientList)
    unselected_ingredients = OneOf(IngredientList)

    # We assume here that client side validation has caught any attempt to submit zero selected
    # ingredients.
    def validate(self):
        # Parse out ingredient parameters coming from form into nice clean dictionary.
        # In the form we use a checkbox combined with a hidden input to ensure that each ingredient
        # appears in the submission even if the box is unchecked.
        # If Django handles this directly, it will return '0' if unchecked and '1' if checked,
        # as the checkbox overrides the hidden input.
        # Mechanical Turk, however, handles this differently. It returns '0' if unchecked and
        # '0|1' if checked, as it appears to combine both values instead of having one override the other.
        # So we check for value != '0' instead of value == '1' to determine whether checked.
        ingredient_params = {int(key[11:]): value != '0' for key, value in vars(self).items()
                             if key.startswith('ingredient_')}

        # Prepare lists
        box = self.to_job.selected_ingredients.box
        selected = IngredientList.objects.create(box=box)
        unselected = IngredientList.objects.create(box=box)

        # Sort ingredients into lists
        for food_id, sel in ingredient_params.items():
            # We need to include a box with the ingredients so that subsequent code
            # can access the submission. This is a big code smell but we're just dealing with it for now.
            # The box we set here may not be the same box the ingredient originally came from,
            # but that doesn't matter since we're no longer highlighting any of the boxes in the measure step.
            ingredient = Ingredient.objects.create(food=Food.get_food(food_id), box=box)
            if sel:
                selected.ingredients.add(ingredient)
            else:
                unselected.ingredients.add(ingredient)
        selected.save()
        unselected.save()
        self.selected_ingredients_id = selected.id
        self.unselected_ingredients_id = unselected.id
        self.save()

        return True

class Manager(base.Manager):

    num_iterations = 2

    ################
    # HIT SETTINGS #
    ################

    # Batching
    batch_size = 2
    max_wait = 5 * MINUTE

    # Payment
    reward = .10
    duplication = 1 # Job will be iterated twice, but only one at a time.

    # Advertising
    qualifications = [min_approval(98), min_completed(200), locale('US')]
    keywords = ['picture', 'identify', 'food', 'database', 'match']
    title = 'Remove duplicate entries in a list of ingredients'
    description = 'Remove duplicate entries in a list of ingredients for a photograph of a meal'

    #########
    # LOGIC #
    #########
    def work(self):
        for assignment in self.assigned:
            self.new_job(
                iteration=1,
                selected_ingredients=assignment.ingredient_list,
                unselected_ingredients=None,
                from_input=assignment,
            )

        for job in self.completed_jobs:
            response = job.valid_responses.all()[0]
            if job.iteration == self.num_iterations:
                self.finish(
                    ingredient_list=response.selected_ingredients,
                    from_job=job,
                )
            else:
                # Prevent turkers who worked on earlier steps from contributing to later steps
                forbidden_workers = list(job.forbidden_workers.all())
                forbidden_workers.append(response.assignment.worker)

                self.new_job(
                    iteration=job.iteration + 1,
                    selected_ingredients=response.selected_ingredients,
                    unselected_ingredients=response.unselected_ingredients,
                    forbidden_workers=forbidden_workers,
                    from_input=job.from_input,
                )
