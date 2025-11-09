# store/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .models import Farmer, Consumer, Product, Order, OrderItem
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json 
from django.db import transaction
from datetime import datetime, timedelta
from decimal import Decimal
from django.conf import settings 
# --- Import Q for searching ---
from django.db.models import Q 

# --- Main/Shared Views ---

def index_view(request):
    return render(request, 'index.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('index')

def about_us_view(request):
    return render(request, 'about_us.html')

def reviews_view(request):
    return render(request, 'reviews.html')

# --- Consumer Views ---

def consumer_signup_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('fullName')
        email = request.POST.get('email')
        contact_number = request.POST.get('contactNumber')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')

        if password != confirm_password:
            messages.error(request, 'Error: Passwords do not match.')
            return redirect('consumer_signup')
            
        if User.objects.filter(username=email).exists():
            messages.error(request, 'Error: This Email is already registered.')
            return redirect('consumer_signup')
        
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name
        )
        
        new_consumer = Consumer.objects.create(
            user=user,
            contact_no=contact_number
        )
        
        login(request, user)
        messages.success(request, f'Signup Successful! Welcome, {full_name}.')
        return redirect('consumer_home')
    
    return render(request, 'consumer_signup.html')

def consumer_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('consumerUsername') 
        password = request.POST.get('consumerPassword')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if hasattr(user, 'consumer'): # Check if they are a consumer
                login(request, user)
                return redirect('consumer_home')
            else:
                messages.error(request, 'This account is not a consumer account.')
                return redirect('consumer_login')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('consumer_login')
            
    return render(request, 'consumer_login.html')


# --- MODIFIED consumer_home_view ---
# (Removed the backend search filtering logic)
@login_required(login_url='consumer_login')
def consumer_home_view(request):
    if not hasattr(request.user, 'consumer'):
        messages.error(request, 'This page is for consumers only. Please log in as a consumer.')
        logout(request)
        return redirect('consumer_login')

    # Start with all available products
    products = Product.objects.filter(stock__gt=0, price__gt=0) 
    
    # --- Get the search query, but DO NOT filter the 'products' list ---
    query = request.GET.get('q')
    
    context = {
        'vegetables': products.filter(category='vegetables'),
        'fruits': products.filter(category='fruits'),
        'dairy': products.filter(category='dairy'),
        'grains': products.filter(category='grains'),
        
        # --- Pass the query to the template for highlighting ---
        'search_query': query 
    }
    return render(request, 'consumer_home.html', context)


# --- Farmer Views ---

def farmer_signup_view(request):
    if request.method == 'POST':
        kisan_id = request.POST.get('kisanId')
        full_name = request.POST.get('fullName')
        email = request.POST.get('email')
        contact_number = request.POST.get('contactNumber')
        pin_code = request.POST.get('pinCode')
        farm_location = request.POST.get('farmLocation')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')

        if password != confirm_password:
            messages.error(request, 'Error: Passwords do not match.')
            return redirect('farmer_signup')

        if User.objects.filter(username=email).exists():
            messages.error(request, 'Error: This Email is already registered.')
            return redirect('farmer_signup')
            
        if Farmer.objects.filter(kisan_id=kisan_id).exists():
            messages.error(request, 'Error: This Kisan ID is already registered.')
            return redirect('farmer_signup')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name
        )
        
        new_farmer = Farmer.objects.create(
            user=user,
            kisan_id=kisan_id,
            contact_no=contact_number,
            pincode=pin_code,
            village_name=farm_location
        )

        login(request, user)
        messages.success(request, f'Signup Successful! Welcome, {full_name}.')
        return redirect('farmer_dashboard')
    else:
        return render(request, 'farmer_signup.html')

def farmer_login_view(request):
    if request.method == 'POST':
        kisan_id = request.POST.get('farmerUsername')
        password = request.POST.get('farmerPassword')

        try:
            farmer_profile = Farmer.objects.get(kisan_id=kisan_id)
            user = authenticate(request, username=farmer_profile.user.username, password=password)
            
            if user is not None:
                if hasattr(user, 'farmer'): # Check if they are a farmer
                    login(request, user)
                    messages.success(request, 'Welcome back!')
                    return redirect('farmer_dashboard')
                else:
                    messages.error(request, 'This is not a farmer account.')
                    return redirect('farmer_login')
            else:
                messages.error(request, 'Invalid Kisan ID or Password.')
                return redirect('farmer_login')
                
        except Farmer.DoesNotExist:
            messages.error(request, 'Invalid Kisan ID or Password.')
            return redirect('farmer_login')
    else:
        return render(request, 'farmer_login.html')

@login_required(login_url='farmer_login')
def farmer_dashboard_view(request):
    if not hasattr(request.user, 'farmer'):
        messages.error(request, 'This page is for farmers only.')
        logout(request)
        return redirect('farmer_login')

    farmer = request.user.farmer
    products = Product.objects.filter(farmer=farmer)
    farmer_order_items = OrderItem.objects.filter(product__farmer=farmer)
    
    # Fixed for SQLite
    pending_order_ids = farmer_order_items.filter(order__is_delivered=False).values_list('order__id', flat=True)
    pending_orders = len(set(pending_order_ids))
    
    total_earnings = sum(item.price * item.quantity for item in farmer_order_items.filter(order__is_delivered=True))

    context = {
        'live_products_count': products.filter(stock__gt=0, price__gt=0).count(),
        'low_stock_products': products.filter(stock__gt=0, stock__lte=5),
        'pending_orders_count': pending_orders,
        'total_earnings': total_earnings,
    }
    return render(request, 'farmer_dashboard.html', context)

@login_required(login_url='farmer_login')
def farmer_products_view(request):
    if not hasattr(request.user, 'farmer'):
        messages.error(request, 'This page is for farmers only.')
        logout(request)
        return redirect('farmer_login')
    
    products = Product.objects.filter(farmer=request.user.farmer).order_by('name')
    context = {'products': products}
    return render(request, 'farmer_products.html', context)


# This is the logic to auto-assign images
PRODUCT_IMAGE_MAP = {
    # Vegetables
    "Tomatoes": "Products/vegetables/tomatoes.jpg",
    "Onions": "Products/vegetables/onions.jpg",
    "Potatoes": "Products/vegetables/potatoes.jpg",
    "Cabbage": "Products/vegetables/cabbage.jpg",
    "Spinach": "Products/vegetables/spinach.jpg",
    "Carrots": "Products/vegetables/carrots.jpg",
    "Capsicum": "Products/vegetables/capsicum.jpg",
    "Cauliflower": "Products/vegetables/cauliflower.jpg",
    "Broccoli": "Products/vegetables/broccoli.jpg",
    "Cucumber": "Products/vegetables/cucumber.jpg",
    "Brinjal": "Products/vegetables/brinjal.jpg",
    "Garlic": "Products/vegetables/garlic.jpg",
    "Ginger": "Products/vegetables/ginger.jpg",
    "Green Chilli": "Products/vegetables/green_chilli.jpg",
    "Lemon": "Products/vegetables/lemon.jpg",
    # Fruits
    "Bananas": "Products/fruits/bananas.jpg",
    "Apples": "Products/fruits/apples.jpg",
    "Grapes": "Products/fruits/grapes.jpg",
    "Mangoes": "Products/fruits/mangoes.jpg",
    "Oranges": "Products/fruits/oranges.jpg",
    "Pineapple": "Products/fruits/pineapple.jpg",
    "Pomegranate": "Products/fruits/pomegranate.jpg",
    "Kiwi": "Products/fruits/kiwi.jpg",
    "Papaya": "Products/fruits/papaya.jpg",
    "Watermelon": "Products/fruits/watermelon.jpg",
    "Coconut": "Products/fruits/coconut.jpg",
    "Muskmelon": "Products/fruits/muskmelon.jpg",
    "Strawberry": "Products/fruits/strawberry.jpg",
    "Litchi": "Products/fruits/litchi.jpg",
    "Cherries": "Products/fruits/cherries.jpg",
    # Grains & Pulses
    "Wheat (gehu)": "Products/grains/wheat.jpg",
    "Basmati rice": "Products/grains/rice.jpg",
    "Toor dal (arhar)": "Products/grains/arhar.jpg",
    "Moong dal (yellow)": "Products/grains/moong (yellow).jpg",
    "Urad dal (split)": "Products/grains/split.jpg",
    "Chana dal": "Products/grains/chana dal.jpg",
    "Kidney beans (rajma)": "Products/grains/kidneybeans.jpg",
    "Chickpeas (chhole)": "Products/grains/chickpeas.jpg",
    "Oats": "Products/grains/oats.jpg",
    "Barley": "Products/grains/barley.jpg",
    "Rye": "Products/grains/rye.jpg",
    "Teff": "Products/grains/teff.jpg",
    "Sorghum (jowar)": "Products/grains/sorghum.jpg",
    "Millet (bajra)": "Products/grains/millet.jpg",
    "Buckwheat": "Products/grains/buckwheat.jpg",
    # Dairy
    "Milk": "Products/dairy/milk.jpg",
    "Paneer": "Products/dairy/paneer.jpg",
    "Ghee": "Products/dairy/ghee.jpg",
    "Curd": "Products/dairy/curd.jpg",
    "Butter": "Products/dairy/butter.jpg",
    "Cheese Slice": "Products/dairy/cheese slice.jpg",
    "Fresh Cream": "Products/dairy/cream.jpg",
    "Lassi": "Products/dairy/lassi.jpg",
    "Chaas (Buttermilk)": "Products/dairy/buttermilk.jpg",
    "Bread": "Products/dairy/bread.jpg",
    "Cheese Spread": "Products/dairy/cheese spread.jpg",
    "Diced Cheese": "Products/dairy/diced cheese.jpg",
    "Condensed Milk": "Products/dairy/condensed milk.jpg",
    "Ice Cream": "Products/dairy/ice cream.jpg",
    "Flavored Milk (Pack of 5)": "Products/dairy/flavoured milk.jpg",
}


@login_required(login_url='farmer_login')
def farmer_add_product_view(request):
    if not hasattr(request.user, 'farmer'):
        messages.error(request, 'This page is for farmers only.')
        logout(request)
        return redirect('farmer_login')

    farmer = request.user.farmer

    if request.method == 'POST':
        selected_products = request.POST.getlist('product')
        
        if not selected_products:
            messages.error(request, 'Please select at least one product to add.')
            return redirect('farmer_add_product')

        existing_products = Product.objects.filter(farmer=farmer).values_list('name', flat=True)
        
        new_products_added = 0
        products_to_create = []

        for product_name in selected_products:
            if product_name not in existing_products:
                category = 'vegetables' # default
                if product_name in ['Bananas', 'Apples', 'Grapes', 'Mangoes', 'Oranges', 'Pineapple', 'Pomegranate', 'Kiwi', 'Papaya', 'Watermelon', 'Coconut', 'Muskmelon', 'Strawberry', 'Litchi', 'Cherries']:
                    category = 'fruits'
                elif product_name in ['Wheat (gehu)', 'Basmati rice', 'Toor dal (arhar)', 'Moong dal (yellow)', 'Urad dal (split)', 'Chana dal', 'Kidney beans (rajma)', 'Chickpeas (chhole)', 'Oats', 'Barley', 'Rye', 'Teff', 'Sorghum (jowar)', 'Millet (bajra)', 'Buckwheat']:
                    category = 'grains'
                elif product_name in ['Milk', 'Paneer', 'Ghee', 'Curd', 'Butter', 'Cheese Slice', 'Fresh Cream', 'Lassi', 'Chaas (Buttermilk)', 'Bread', 'Cheese Spread', 'Diced Cheese', 'Condensed Milk', 'Ice Cream', 'Flavored Milk (Pack of 5)']:
                    category = 'dairy'

                image_path = PRODUCT_IMAGE_MAP.get(product_name, 'Images/logo.png') # Default image

                products_to_create.append(
                    Product(
                        farmer=farmer, 
                        name=product_name, 
                        category=category, 
                        price=0, 
                        stock=0, 
                        unit='kg',
                        image_path=image_path
                    )
                )
                new_products_added += 1
        
        if products_to_create:
            Product.objects.bulk_create(products_to_create)
            messages.success(request, f'Success! {new_products_added} new products added. Please set their price and stock.')
        else:
            messages.info(request, 'All selected products were already in your inventory.')

        return redirect('farmer_products')

    return render(request, 'farmer_add_product.html')


@login_required(login_url='farmer_login')
def update_product_view(request, product_id):
    if not hasattr(request.user, 'farmer'):
        messages.error(request, 'This page is for farmers only.')
        logout(request)
        return redirect('farmer_login')
        
    try:
        product = Product.objects.get(id=product_id, farmer=request.user.farmer)
    except Product.DoesNotExist:
        messages.error(request, 'Product not found.')
        return redirect('farmer_products')

    if request.method == 'POST':
        product.price = request.POST.get('price')
        product.unit = request.POST.get('unit')
        product.stock = request.POST.get('stock')
        
        product.save()
        messages.success(request, f'{product.name} updated successfully!')
        return redirect('farmer_products')
    
    return redirect('farmer_products')

@login_required(login_url='farmer_login')
def delete_product_view(request, product_id):
    if not hasattr(request.user, 'farmer'):
        messages.error(request, 'This page is for farmers only.')
        logout(request)
        return redirect('farmer_login')
        
    try:
        product = Product.objects.get(id=product_id, farmer=request.user.farmer)
        product_name = product.name
        product.delete()
        messages.success(request, f'{product_name} has been deleted.')
    except Product.DoesNotExist:
        messages.error(request, 'Product not found.')

    return redirect('farmer_products')

@login_required(login_url='farmer_login')
def farmer_orders_view(request):
    if not hasattr(request.user, 'farmer'):
        messages.error(request, 'This page is for farmers only.')
        logout(request)
        return redirect('farmer_login')
    
    order_items = OrderItem.objects.filter(product__farmer=request.user.farmer).order_by('-order__order_date')
    context = {
        'order_items': order_items
    }
    return render(request, 'farmer_orders.html', context)

# store/views.py
from django.shortcuts import render, redirect
# ... (all your other imports) ...
from decimal import Decimal # Make sure Decimal is imported at the top

# ... (all your other views) ...

# NEW UPDATED VIEW
@login_required(login_url='farmer_login')
def farmer_payments_view(request):
    if not hasattr(request.user, 'farmer'):
        messages.error(request, 'This page is for farmers only.')
        logout(request)
        return redirect('farmer_login')

    farmer = request.user.farmer # Get the farmer object

    # Get all COMPLETED but NOT YET PAID OUT order items for this farmer
    order_items = OrderItem.objects.filter(
        product__farmer=farmer, 
        order__is_delivered=True,
        is_paid_out=False  # --- Only show unpaid items ---
    ).order_by('order__order_date') # Show oldest first

    payment_data = []
    commission_rate = Decimal('0.15') # 15% commission
    total_unpaid_amount = Decimal('0.00') # This is what the farmer is owed

    for item in order_items:
        total_amount = item.price * item.quantity
        our_commission = total_amount * commission_rate
        farmer_amount = total_amount - our_commission
        total_unpaid_amount += farmer_amount # Sum up the farmer's total due

        payment_data.append({
            'item': item,
            'total_amount': total_amount,
            'our_commission': our_commission,
            'farmer_amount': farmer_amount,
        })

    context = {
        'payment_data': payment_data,
        'total_unpaid_amount': total_unpaid_amount, # Pass the total
        'farmer_status': farmer.payout_status, # Pass the status
        'has_unpaid_items': order_items.exists() # Pass if there's anything to pay
    }
    return render(request, 'farmer_py.html', context)

# ... (rest of your views.py) ...

# --- Cart & Checkout Views ---

@login_required(login_url='consumer_login')
def update_cart_view(request):
    if not hasattr(request.user, 'consumer'):
        return JsonResponse({'status': 'error', 'message': 'Not a consumer account'}, status=403)

    if request.method == 'POST' and request.user.is_authenticated:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        quantity = int(data.get('quantity'))
        cart = request.session.get('cart', {})

        if quantity > 0:
            cart[product_id] = quantity
        elif product_id in cart:
            del cart[product_id]
        
        request.session['cart'] = cart
        total_items = sum(cart.values())
        return JsonResponse({'status': 'success', 'total_items': total_items})
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required(login_url='consumer_login')
def cart_view(request):
    if not hasattr(request.user, 'consumer'):
        messages.error(request, 'This page is for consumers only. Please log in as a consumer.')
        logout(request)
        return redirect('consumer_login')

    cart = request.session.get('cart', {})
    cart_items = []
    total_subtotal = 0
    total_items_count = 0

    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            item_total = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'item_total': item_total,
            })
            total_subtotal += item_total
            total_items_count += quantity
        except Product.DoesNotExist:
            if product_id in request.session['cart']:
                del request.session['cart'][product_id]
                request.session.modified = True

    context = {
        'cart_items': cart_items,
        'total_subtotal': total_subtotal,
        'total_items_count': total_items_count,
    }
    return render(request, 'cart.html', context)

@login_required(login_url='consumer_login')
def checkout_view(request):
    if not hasattr(request.user, 'consumer'):
        messages.error(request, 'This page is for consumers only. Please log in as a consumer.')
        logout(request)
        return redirect('consumer_login')

    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart_view')
        
    if request.method == 'POST':
        try:
            with transaction.atomic():
                full_name = request.POST.get('user-full-name')
                mobile = request.POST.get('user-mobile')
                address = request.POST.get('user-address')
                pincode = request.POST.get('user-pincode')
                payment_method = request.POST.get('payment-method-new')

                total_subtotal = 0
                items_to_create = []
                
                for product_id, quantity in cart.items():
                    product = Product.objects.get(id=product_id)
                    if product.stock < quantity:
                        raise Exception(f'Not enough stock for {product.name}')
                    
                    total_subtotal += product.price * quantity
                    items_to_create.append({
                        'product': product,
                        'quantity': quantity,
                        'price': product.price
                    })

                new_order = Order.objects.create(
                    consumer=request.user.consumer,
                    total_amount=total_subtotal,
                    full_name=full_name,
                    mobile=mobile,
                    address=address,
                    pincode=pincode,
                    payment_method=payment_method
                )

                for item in items_to_create:
                    OrderItem.objects.create(
                        order=new_order,
                        product=item['product'],
                        quantity=item['quantity'],
                        price=item['price']
                    )
                    item['product'].stock -= item['quantity']
                    item['product'].save()
            
            del request.session['cart']
            return redirect('order_confirmation', order_id=new_order.id)

        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
            return redirect('checkout_view')
    
    return render(request, 'checkout.html')

@login_required(login_url='consumer_login')
def order_confirmation_view(request, order_id):
    if not hasattr(request.user, 'consumer'):
        messages.error(request, 'This page is for consumers only. Please log in as a consumer.')
        logout(request)
        return redirect('consumer_login')

    try:
        order = Order.objects.get(id=order_id, consumer=request.user.consumer)
        delivery_fee = Decimal('30.00')
        grand_total = order.total_amount + delivery_fee
        
        expected_delivery_date = (datetime.now() + timedelta(days=1)).strftime('%A, %d %B %Y')

        context = {
            'order': order,
            'delivery_fee': delivery_fee,
            'grand_total': grand_total,
            'expected_delivery_date': expected_delivery_date
        }
        return render(request, 'order_confirmation.html', context)
        
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('consumer_home')
    
# --- ADD THIS NEW VIEW ---

@login_required(login_url='farmer_login')
def complete_order_view(request, order_id):
    # Ensure the user is a farmer
    if not hasattr(request.user, 'farmer'):
        messages.error(request, 'This action is for farmers only.')
        return redirect('farmer_login')
    
    if request.method == 'POST':
        try:
            # Find the order
            order_to_complete = Order.objects.get(id=order_id)
            
            # **Security Check:** Ensure the logged-in farmer has at least one item in this order
            # This prevents a farmer from marking another farmer's order as complete
            if not OrderItem.objects.filter(order=order_to_complete, product__farmer=request.user.farmer).exists():
                messages.error(request, 'You do not have permission to modify this order.')
                return redirect('farmer_orders')

            # Update the status
            order_to_complete.is_delivered = True
            order_to_complete.save()
            
            messages.success(request, f'Order {order_to_complete.id} has been marked as completed.')
        
        except Order.DoesNotExist:
            messages.error(request, 'Order not found.')
        
        # Redirect back to the orders page
        return redirect('farmer_orders')
    
    # If not POST, just redirect
    return redirect('farmer_orders')    
@login_required(login_url='farmer_login')
def request_payout_view(request):
    if request.method == 'POST':
        farmer = request.user.farmer
        # Only allow request if status is 'none' and they have items
        if farmer.payout_status == 'none' and OrderItem.objects.filter(product__farmer=farmer, order__is_delivered=True, is_paid_out=False).exists():
            farmer.payout_status = 'requested'
            farmer.save()
            messages.success(request, 'Payout request submitted to admin.')
        else:
            messages.error(request, 'Could not submit payout request.')
    return redirect('farmer_payments')


@login_required(login_url='farmer_login')
def collect_payment_view(request):
    farmer = request.user.farmer

    # Security check: Only farmers with 'approved' status can be here
    if farmer.payout_status != 'approved':
        messages.error(request, 'Your payout has not been approved by admin.')
        return redirect('farmer_payments')

    # Get all items that will be paid out
    items_to_be_paid = OrderItem.objects.filter(
        product__farmer=farmer, 
        order__is_delivered=True,
        is_paid_out=False
    )

    # Calculate total
    total_payout = Decimal('0.00')
    commission_rate = Decimal('0.15')
    for item in items_to_be_paid:
        total_amount = item.price * item.quantity
        farmer_amount = total_amount - (total_amount * commission_rate)
        total_payout += farmer_amount

    if not items_to_be_paid.exists() or total_payout == 0:
        messages.error(request, 'No pending payments found.')
        farmer.payout_status = 'none' # Reset status
        farmer.save()
        return redirect('farmer_payments')

    if request.method == 'POST':
        # Get bank details from form
        bank_name = request.POST.get('bank_name')
        account_holder = request.POST.get('account_holder')
        account_number = request.POST.get('account_number')
        ifsc_code = request.POST.get('ifsc_code')

        # Simple validation
        if not all([bank_name, account_holder, account_number, ifsc_code]):
            messages.error(request, 'Please fill out all bank details.')
            return redirect('collect_payment')

        # --- CRITICAL TRANSACTION ---
        # This is where you would process the payment in a real app
        # For this project, we just simulate success.

        try:
            with transaction.atomic():
                # 1. Mark all items as paid
                items_to_be_paid.update(is_paid_out=True)

                # 2. Reset farmer's payout status
                farmer.payout_status = 'none'
                farmer.save()

            # 3. Show success
            messages.success(request, f'Payment of ₹{total_payout:.2f} was successful! The amount will be credited to your account shortly.')
            return redirect('farmer_payments') # Redirect to payment page

        except Exception as e:
            messages.error(request, f'An error occurred: {e}. Please contact admin.')
            return redirect('collect_payment')

    # GET request: Show the form
    context = {
        'total_payout': total_payout
    }
    return render(request, 'collect_payment.html', context)