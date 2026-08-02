# This Python file uses the following encoding: utf-8

from django.core.management.base import BaseCommand

from aula.apps.incidencies.helpers import preescriu


class Command(BaseCommand):
    help = "Caduca les incidències i faltes greus velles"

    preescriu()

    def handle(self, *args, **options):
        self.stdout.write("Tasca finalitzada satisfactoriament")
