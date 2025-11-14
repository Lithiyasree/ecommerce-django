# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.models import User
# from django.contrib import messages
# from .models import Category, Product, Cart, Wishlist

# def home(request):
#     categories = Category.objects.all()
#     products = Product.objects.all()
#     return render(request, 'home.html', {'categories': categories, 'products': products})

# def product_detail(request, id):
#     product = get_object_or_404(Product, id=id)
#     return render(request, 'product_detail.html', {'product': product})

# def add_to_cart(request, id):
#     if not request.user.is_authenticated:
#         return redirect('login')
#     product = Product.objects.get(id=id)
#     Cart.objects.get_or_create(user=request.user, product=product)
#     messages.success(request, 'Product added to cart!')
#     return redirect('home')

# def view_cart(request):
#     if not request.user.is_authenticated:
#         return redirect('login')
#     cart_items = Cart.objects.filter(user=request.user)
#     return render(request, 'cart.html', {'cart_items': cart_items})

# def add_to_wishlist(request, id):
#     if not request.user.is_authenticated:
#         return redirect('login')
#     product = Product.objects.get(id=id)
#     Wishlist.objects.get_or_create(user=request.user, product=product)
#     messages.success(request, 'Product added to wishlist!')
#     return redirect('home')

# def view_wishlist(request):
#     if not request.user.is_authenticated:
#         return redirect('login')
#     wishlist_items = Wishlist.objects.filter(user=request.user)
#     return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})

# def user_login(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(username=username, password=password)
#         if user:
#             login(request, user)
#             return redirect('home')
#         else:
#             messages.error(request, 'Invalid credentials')
#     return render(request, 'login.html')

# def user_register(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         User.objects.create_user(username=username, password=password)
#         messages.success(request, 'Registration successful!')
#         return redirect('login')
#     return render(request, 'register.html')

# def user_logout(request):
#     logout(request)
#     return redirect('login')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Category, Product, Cart, Wishlist


def _counts_for_user(request):
    """Helper to return cart_count and wishlist_count for navbar/context."""
    if request.user.is_authenticated:
        cart_count = Cart.objects.filter(user=request.user).count()
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
    else:
        cart_count = 0
        wishlist_count = 0
    return {'cart_count': cart_count, 'wishlist_count': wishlist_count}


def home(request):
    """
    Home page - shows categories and products.
    Use ?category=<id> to filter products by category.
    """
    categories = Category.objects.all()
    category_id = request.GET.get('category')  # optional query param

    if category_id:
        products = Product.objects.filter(category_id=category_id)
        try:
            selected_category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            selected_category = None
    else:
        products = Product.objects.all()
        selected_category = None

    context = {
        'categories': categories,
        'products': products,
        'selected_category': selected_category,
    }
    context.update(_counts_for_user(request))
    return render(request, 'home.html', context)


def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    context = {'product': product}
    context.update(_counts_for_user(request))
    return render(request, 'product_detail.html', context)


############################################## CART VIEWS #######################################################

@login_required(login_url='login')
def add_to_cart(request, id):
    product = get_object_or_404(Product, id=id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        # If already in cart, increment quantity
        cart_item.quantity += 1
        cart_item.save()
        messages.info(request, f"Incremented quantity for {product.name} in your cart.")
    else:
        messages.success(request, f"Added {product.name} to your cart.")
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required(login_url='login')
def view_cart(request):

    if not request.user.is_authenticated:
        messages.warning(request, "Please login to access your cart.")
        return redirect('login')

    cart_items = Cart.objects.filter(user=request.user).select_related('product')

    # Add total for each item
    for item in cart_items:
        item.total = item.product.price * item.quantity

    # Compute grand total
    grand_total = sum(item.total for item in cart_items)

    context = {
        'cart_items': cart_items,
        'grand_total': grand_total
    }

    context.update(_counts_for_user(request))

    return render(request, 'cart.html', context)


@login_required(login_url='login')
def remove_from_cart(request, id):
    """
    id here is cart item id (primary key of Cart model).
    If you prefer to remove by product id, change accordingly.
    """
    item = get_object_or_404(Cart, id=id, user=request.user)
    item.delete()
    messages.success(request, "Removed item from cart.")
    return redirect('cart')


@login_required(login_url='login')
def update_cart_quantity(request, id):
    """
    Optional: POST endpoint to update quantity for a cart item.
    Expect 'quantity' in POST data.
    """
    item = get_object_or_404(Cart, id=id, user=request.user)
    if request.method == 'POST':
        try:
            qty = int(request.POST.get('quantity', 1))
            if qty < 1:
                item.delete()
                messages.info(request, "Item removed from cart because quantity was set to 0.")
            else:
                item.quantity = qty
                item.save()
                messages.success(request, "Cart updated.")
        except ValueError:
            messages.error(request, "Invalid quantity.")
    return redirect('cart')


@login_required(login_url='login')
def increase_quantity(request, item_id):
    item = get_object_or_404(Cart, id=item_id, user=request.user)
    item.quantity += 1
    item.save()
    return redirect('cart')

@login_required(login_url='login')
def decrease_quantity(request, item_id):
    item = get_object_or_404(Cart, id=item_id, user=request.user)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    return redirect('cart')


############################################### WISHLIST VIEWS ####################################################### 

@login_required(login_url='login')
def add_to_wishlist(request, id):
    product = get_object_or_404(Product, id=id)
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request, f"Added {product.name} to wishlist.")
    else:
        messages.info(request, f"{product.name} is already in your wishlist.")
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required(login_url='login')
def view_wishlist(request):

    if not request.user.is_authenticated:
        messages.warning(request, "Please login to access your cart.")
        return redirect('login')

    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    context = {'wishlist_items': wishlist_items}
    context.update(_counts_for_user(request))
    return render(request, 'wishlist.html', context)


@login_required(login_url='login')
def remove_from_wishlist(request, id):
    item = get_object_or_404(Wishlist, id=id, user=request.user)
    item.delete()
    messages.success(request, "Removed from wishlist.")
    return redirect('wishlist')


############################################# AUTHENTICATION VIEWS #######################################################

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            # Redirect to next param if present
            next_url = request.GET.get('next') or request.POST.get('next')
            return redirect(next_url or 'home')
        else:
            messages.error(request, "Invalid username or password.")
    context = {}
    context.update(_counts_for_user(request))
    return render(request, 'login.html', context)


def user_register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        if not username or not password:
            messages.error(request, "Username and password are required.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('register')

        User.objects.create_user(username=username, password=password)
        messages.success(request, "Registration successful. Please log in.")
        return redirect('login')

    context = {}
    context.update(_counts_for_user(request))
    return render(request, 'register.html', context)


@login_required
def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')
