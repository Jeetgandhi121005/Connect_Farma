# store/admin.py
from django.contrib import admin
from .models import Consumer, Farmer, Product, Order, OrderItem

# --- Product Approval Action ---
@admin.action(description='Approve selected products')
def approve_products(modeladmin, request, queryset):
    queryset.update(is_approved=True)
    
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'farmer', 'price', 'stock', 'is_approved')
    list_filter = ('is_approved', 'category', 'farmer')
    search_fields = ('name', 'farmer__user__username')
    actions = [approve_products]

# --- NEW: Farmer Payout Approval Action ---
@admin.action(description='Approve payout request for selected farmers')
def approve_payout(modeladmin, request, queryset):
    queryset.update(payout_status='approved')

class FarmerAdmin(admin.ModelAdmin):
    list_display = ('user', 'kisan_id', 'contact_no', 'payout_status') # Add payout_status
    list_filter = ('payout_status',) # Add filter
    search_fields = ('user__username', 'kisan_id')
    actions = [approve_payout] # Add the action

# Register your models here
admin.site.register(Consumer)
admin.site.register(Farmer, FarmerAdmin) # Register Farmer with our new custom class
admin.site.register(Product, ProductAdmin)
admin.site.register(Order)
admin.site.register(OrderItem)