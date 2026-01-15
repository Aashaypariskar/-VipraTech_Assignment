from django.core.management.base import BaseCommand

from core.models import Product


class Command(BaseCommand):
    """
    Management command to seed the database with initial products.
    
    This command creates exactly 3 sample products for testing purposes.
    Products are created with price in cents for currency safety.
    """
    help = 'Seed the database with initial products'
    
    def handle(self, *args, **options):
        """
        Execute the command to create sample products.
        
        Flow:
        1. Clear existing products
        2. Create exactly 3 products with sample data
        3. Display confirmation message
        """
        Product.objects.all().delete()
        
        products = [
            Product(name='Laptop', price_cents=99999),  # $999.99
            Product(name='Mouse', price_cents=2999),    # $29.99
            Product(name='Keyboard', price_cents=7999), # $79.99
        ]
        
        Product.objects.bulk_create(products)
        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(products)} products'))
