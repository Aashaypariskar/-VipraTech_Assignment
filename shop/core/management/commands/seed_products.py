from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Product, OrderItem


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
        1. Upsert the 3 fixed products deterministically by name
        2. Delete any extra products only if they are unreferenced
        3. Display confirmation message
        """
        desired = [
            ('Laptop', 99999),   # $999.99
            ('Mouse', 2999),     # $29.99
            ('Keyboard', 7999),  # $79.99
        ]
        desired_names = [name for (name, _) in desired]

        with transaction.atomic():
            created = 0
            updated = 0
            for name, price_cents in desired:
                obj, was_created = Product.objects.update_or_create(
                    name=name,
                    defaults={'price_cents': price_cents},
                )
                created += 1 if was_created else 0
                updated += 0 if was_created else 1

            # Keep DB tidy without breaking existing orders:
            # delete products not in our fixed set only if unreferenced.
            referenced_ids = OrderItem.objects.values_list('product_id', flat=True).distinct()
            deleted, _ = (
                Product.objects
                .exclude(name__in=desired_names)
                .exclude(id__in=referenced_ids)
                .delete()
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Products seeded. created={created}, updated={updated}, deleted_extra_unreferenced={deleted}'
            )
        )
