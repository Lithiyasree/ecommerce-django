from django.contrib import admin
from .models import Category, Product, Cart, Wishlist

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(Wishlist)