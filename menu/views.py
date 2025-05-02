from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Restaurant, MenuCategory, MenuItem
from django.contrib.auth.forms import UserCreationForm
from django import forms
import qrcode
import io
import base64
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import update_session_auth_hash

class RestaurantRegistrationForm(UserCreationForm):
    name = forms.CharField(max_length=200, required=True)
    pan_number = forms.CharField(max_length=10, required=True)
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = Restaurant
        fields = ('username', 'name', 'pan_number', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.name = self.cleaned_data['name']
        user.pan_number = self.cleaned_data['pan_number']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class RestaurantLoginView(LoginView):
    template_name = 'menu/login.html'
    
    def get_success_url(self):
        messages.success(self.request, 'Successfully logged in!')
        return reverse_lazy('menu:restaurant_menu', kwargs={'restaurant_id': self.request.user.id})

class RestaurantRegistrationView(CreateView):
    model = Restaurant
    form_class = RestaurantRegistrationForm
    template_name = 'menu/register.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Registration successful! Please log in.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('menu:login')

class RestaurantListView(ListView):
    model = Restaurant
    template_name = 'menu/restaurant_list.html'
    context_object_name = 'restaurants'

    def get_queryset(self):
        # If user is authenticated, only show their own restaurant
        if self.request.user.is_authenticated:
            return Restaurant.objects.filter(id=self.request.user.id)
            
        # Otherwise show all restaurants for public view
        queryset = Restaurant.objects.all()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

class RestaurantMenuView(DetailView):
    model = Restaurant
    template_name = 'menu/restaurant_menu.html'
    context_object_name = 'restaurant'
    pk_url_kwarg = 'restaurant_id'

    def dispatch(self, request, *args, **kwargs):
        # Get the restaurant object
        self.object = self.get_object()
        
        # If user is logged in and trying to access another restaurant's menu
        if request.user.is_authenticated and request.user.id != self.object.id:
            messages.warning(request, "You can only view your own restaurant's menu.")
            return redirect('menu:restaurant_menu', restaurant_id=request.user.id)
            
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = MenuCategory.objects.filter(restaurant=self.object)
        
        # Generate QR code for the menu URL
        current_site = get_current_site(self.request)
        menu_url = f'http://{current_site.domain}{self.object.get_absolute_url()}'
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(menu_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_image = base64.b64encode(buffer.getvalue()).decode()
        context['qr_code'] = qr_image
        context['menu_url'] = menu_url
        
        return context

class MenuCategoryCreateView(LoginRequiredMixin, CreateView):
    model = MenuCategory
    fields = ['name']
    template_name = 'menu/category_form.html'
    
    def form_valid(self, form):
        form.instance.restaurant = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Category added successfully!')
        return response
    
    def get_success_url(self):
        return reverse_lazy('menu:restaurant_menu', kwargs={'restaurant_id': self.request.user.id})

class MenuItemCreateView(LoginRequiredMixin, CreateView):
    model = MenuItem
    fields = ['name', 'description', 'price', 'photo', 'category']
    template_name = 'menu/item_form.html'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['category'].queryset = MenuCategory.objects.filter(restaurant=self.request.user)
        return form
    
    def form_valid(self, form):
        if form.instance.category.restaurant != self.request.user:
            messages.error(self.request, 'Invalid category selected.')
            return self.form_invalid(form)
        response = super().form_valid(form)
        messages.success(self.request, 'Menu item added successfully!')
        return response
    
    def get_success_url(self):
        return reverse_lazy('menu:restaurant_menu', kwargs={'restaurant_id': self.request.user.id})

class MenuItemUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = MenuItem
    fields = ['name', 'description', 'price', 'photo', 'category', 'order', 'is_available']
    template_name = 'menu/item_form.html'
    
    def test_func(self):
        item = self.get_object()
        return item.category.restaurant == self.request.user
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['category'].queryset = MenuCategory.objects.filter(restaurant=self.request.user)
        return form
    
    def form_valid(self, form):
        if form.instance.category.restaurant != self.request.user:
            messages.error(self.request, 'Invalid category selected.')
            return self.form_invalid(form)
        messages.success(self.request, 'Menu item updated successfully!')
        return super().form_valid(form)

class MenuItemDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = MenuItem
    template_name = 'menu/menuitem_confirm_delete.html'
    
    def test_func(self):
        item = self.get_object()
        return item.category.restaurant == self.request.user
    
    def get_success_url(self):
        messages.success(self.request, 'Menu item deleted successfully!')
        return reverse_lazy('menu:restaurant_menu', kwargs={'restaurant_id': self.request.user.id})

class MenuCategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = MenuCategory
    fields = ['name', 'order']
    template_name = 'menu/category_form.html'
    
    def test_func(self):
        category = self.get_object()
        return category.restaurant == self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('menu:restaurant_menu', kwargs={'restaurant_id': self.request.user.id})

class MenuItemListView(ListView):
    model = MenuItem
    template_name = 'menu/menu_items.html'
    context_object_name = 'items'

    def dispatch(self, request, *args, **kwargs):
        # Get the category first
        self.category = get_object_or_404(MenuCategory, id=self.kwargs['category_id'])
        
        # If user is logged in and trying to access another restaurant's items
        if request.user.is_authenticated and request.user != self.category.restaurant:
            messages.warning(request, "You can only view items from your own restaurant's menu.")
            return redirect('menu:restaurant_menu', restaurant_id=request.user.id)
            
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return MenuItem.objects.filter(category=self.category)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context

class RestaurantUpdateForm(forms.ModelForm):
    current_password = forms.CharField(widget=forms.PasswordInput(), required=False)
    new_password = forms.CharField(widget=forms.PasswordInput(), required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = Restaurant
        fields = ['name', 'email', 'pan_number', 'logo']

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and not current_password:
            raise forms.ValidationError('Current password is required to set a new password')
        
        if new_password != confirm_password:
            raise forms.ValidationError('New passwords do not match')

        return cleaned_data

class RestaurantUpdateView(LoginRequiredMixin, UpdateView):
    model = Restaurant
    form_class = RestaurantUpdateForm
    template_name = 'menu/restaurant_form.html'
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        # Check if password change is requested
        current_password = form.cleaned_data.get('current_password')
        new_password = form.cleaned_data.get('new_password')
        
        if current_password and new_password:
            # Verify current password
            if not self.request.user.check_password(current_password):
                form.add_error('current_password', 'Current password is incorrect')
                return self.form_invalid(form)
            
            # Set new password
            self.request.user.set_password(new_password)
            password_changed = True
        else:
            password_changed = False

        response = super().form_valid(form)
        
        if password_changed:
            # Update session to prevent logout
            update_session_auth_hash(self.request, self.request.user)
            messages.success(self.request, 'Password updated successfully!')
        
        messages.success(self.request, 'Restaurant profile updated successfully!')
        return response
    
    def get_success_url(self):
        return reverse_lazy('menu:restaurant_menu', kwargs={'restaurant_id': self.request.user.id})
