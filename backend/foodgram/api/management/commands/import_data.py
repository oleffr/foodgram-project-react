import os
import json
import logging

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s, %(levelname)s, %(message)s',
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        logger.info('Импорт начался')
        try:
            with open(
                    os.path.join(os.path.dirname(__file__), 'ingredients.json'),
                    'r',
                    encoding='utf-8') as file:
                data = json.load(file)
                Ingredient.objects.bulk_create(Ingredient(**line
                                                          ) for line in data)
            logger.info(f'Данные загружены')
        except Exception as error:
            logger.error(error)
