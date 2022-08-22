from django.core.management import BaseCommand
from emtct.models import UgandaEMRExport


class Command(BaseCommand):
    def handle(self, *args, **options):
        UgandaEMRExport.sync_data()
        self.stdout.write(self.style.SUCCESS('Successfully synced data'))