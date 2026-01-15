from django.db import models


class Product(models.Model):
    """
    Product model representing items available for purchase.
    
    Fields:
    - name: Product name
    - description: Detailed description of the product
    - price: Price in cents (to avoid floating point issues)
    - quantity: Available quantity in stock
    """
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.IntegerField()  # Price in cents
    quantity = models.IntegerField()
    
    def __str__(self):
        return self.name


class Order(models.Model):
    """
    Order model representing a customer purchase.
    
    Fields:
    - stripe_session_id: Stripe checkout session ID
    - status: Order status (pending, completed, cancelled)
    - created_at: Order creation timestamp
    """
    stripe_session_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Order {self.id} - {self.status}"


class OrderItem(models.Model):
    """
    OrderItem model representing individual items in an order.
    
    Fields:
    - order: Foreign key to Order
    - product: Foreign key to Product
    - quantity: Quantity of the product ordered
    - price: Price of the product at time of order (in cents)
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    price = models.IntegerField()  # Price in cents at time of order
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
