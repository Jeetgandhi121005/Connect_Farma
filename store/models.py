# store/models.py
from django.db import models
from django.contrib.auth.models import User

# Model to extend the built-in User for Consumers
class Consumer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_no = models.CharField(max_length=15)
    # Add other consumer-specific fields here

    def __str__(self):
        return self.user.username

# Model to extend the built-in User for Farmers
class Farmer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    kisan_id = models.CharField(max_length=20, unique=True)
    contact_no = models.CharField(max_length=15)
    pincode = models.CharField(max_length=10)
    village_name = models.CharField(max_length=100)
    # Add other farmer-specific fields here
# --- ADD THESE LINES ---
    PAYOUT_STATUS_CHOICES = [
        ('none', 'None'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
    ]
    payout_status = models.CharField(max_length=20, choices=PAYOUT_STATUS_CHOICES, default='none')
    # ---------------------

    def __str__(self):
        return self.user.username
    




class Product(models.Model):
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    UNIT_CHOICES = [
        ('kg', 'kg'),
        ('dozen', 'dozen'),
        ('piece', 'piece'),
        ('litre', 'litre'),
        ('bunch', 'bunch'),
    ]
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='kg')
    stock = models.PositiveIntegerField(default=0)
    
    image_path = models.CharField(max_length=255, blank=True, null=True)
    
    CATEGORY_CHOICES = [
        ('vegetables', 'Vegetables'),
        ('fruits', 'Fruits'),
        ('dairy', 'Dairy'),
        ('grains', 'Grains & Pulses'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='vegetables')

    # --- ADD THIS LINE ---
    is_approved = models.BooleanField(default=False)
    # ---------------------

    def __str__(self):
        return self.name

# ... (Order and OrderItem models) ...

# ... (Order and OrderItem models stay the same) ...# Models for the Ordering System
class Order(models.Model):
    consumer = models.ForeignKey(Consumer, on_delete=models.SET_NULL, null=True)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Shipping info from checkout.html
    full_name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    address = models.TextField()
    pincode = models.CharField(max_length=10)
    
    payment_method = models.CharField(max_length=50, default='Cash On Delivery')
    is_delivered = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.id} by {self.consumer.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Price at the time of order
    is_paid_out = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

# Create your models here.
