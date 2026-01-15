from django.db import models


class Product(models.Model):
    """
    Product model representing items available for purchase.
    
    Fields:
    - name: Product name
    - price_cents: Price in cents (to avoid floating point issues)
    """
    name = models.CharField(max_length=255)
    price_cents = models.IntegerField()  # Price in cents
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return self.name


class Order(models.Model):
    """
    Order model representing a customer purchase.
    
    Fields:
    - session_id: Stripe checkout session ID (UNIQUE)
    - status: Order status (PENDING, PAID, FAILED)
    - total_cents: Total order amount in cents
    - created_at: Order creation timestamp
    """
    STATUS_PENDING = 'PENDING'
    STATUS_PAID = 'PAID'
    STATUS_FAILED = 'FAILED'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
    ]
    
    session_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    total_cents = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.id} - {self.status}"


class OrderItem(models.Model):
    """
    OrderItem model representing individual items in an order.
    
    Fields:
    - order: Foreign key to Order
    - product: Foreign key to Product
    - quantity: Quantity of the product ordered
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    
    class Meta:
        unique_together = ['order', 'product']
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
