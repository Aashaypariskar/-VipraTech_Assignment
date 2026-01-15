from django.core.management.base import BaseCommand

from core.models import Product


class Command(BaseCommand):
    """
    Management command to seed the database with initial products.
    
    This command creates exactly 3 sample products for testing purposes.
    """
    help = 'Seed the database with initial products'
    
    def handle(self, *args, **options):
        """
        Execute the command to create sample products.
        
        Flow:
        1. Check if products already exist
        2. Create exactly 3 products with sample data
        3. Display confirmation message
        
        TODO: Implement logic to insert exactly 3 products
        """
        # TODO: Delete existing products or check if they exist
        # TODO: Create Product 1
        # TODO: Create Product 2
        # TODO: Create Product 3
        # TODO: Print success message with product count
        pass
