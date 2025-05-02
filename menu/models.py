from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse

class Restaurant(AbstractUser):
    name = models.CharField(max_length=200)
    pan_number = models.CharField(max_length=10, unique=True)
    logo = models.ImageField(upload_to='restaurant_logos/', blank=True, null=True)
    
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('menu:restaurant_menu', kwargs={'restaurant_id': self.id})

class MenuCategory(models.Model):
    name = models.CharField(max_length=100)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='categories')
    order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = 'Menu Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"

class MenuItem(models.Model):
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    photo = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    order = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('menu:restaurant_menu', kwargs={'restaurant_id': self.category.restaurant.id})
