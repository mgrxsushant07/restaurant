from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views

app_name = 'menu'

urlpatterns = [
    path('', views.RestaurantListView.as_view(), name='restaurant_list'),
    path('restaurant/<int:restaurant_id>/', views.RestaurantMenuView.as_view(), name='restaurant_menu'),
    path('restaurant/edit/', views.RestaurantUpdateView.as_view(), name='edit_restaurant'),
    path('category/<int:category_id>/items/', views.MenuItemListView.as_view(), name='menu_items'),
    
    # Authentication URLs
    path('login/', views.RestaurantLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='menu:restaurant_list'
    ), name='logout'),
    path('register/', views.RestaurantRegistrationView.as_view(), name='register'),
    
    # CRUD operations
    path('category/add/', views.MenuCategoryCreateView.as_view(), name='add_category'),
    path('category/<int:pk>/edit/', views.MenuCategoryUpdateView.as_view(), name='edit_category'),
    path('item/add/', views.MenuItemCreateView.as_view(), name='add_item'),
    path('item/<int:pk>/edit/', views.MenuItemUpdateView.as_view(), name='edit_item'),
    path('item/<int:pk>/delete/', views.MenuItemDeleteView.as_view(), name='delete_item'),
]