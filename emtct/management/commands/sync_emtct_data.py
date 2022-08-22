from django.core.management import BaseCommand
from emtct.models import RapidPro


class Command(BaseCommand):
    def handle(self, *args, **options):
        RapidPro.sync_rapidpro()
        self.stdout.write(self.style.SUCCESS('Successfully synced data'))