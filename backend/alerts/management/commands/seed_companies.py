from django.core.management.base import BaseCommand
from alerts.models import Company
class Command(BaseCommand):
    help = 'Seed sample companies'
    def handle(self, *args, **options):
        Company.objects.update_or_create(ticker='AAPL', defaults={'name':'Apple Inc.'})
        Company.objects.update_or_create(ticker='TSLA', defaults={'name':'Tesla, Inc.'})
        self.stdout.write(self.style.SUCCESS('Seeded companies.'))
