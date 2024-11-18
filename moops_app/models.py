from django.db import models
from django.contrib.auth.models import User

from django.utils.text import slugify



class ProductType(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class ProductOrder(models.Model):
    
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.heading} - {self.order}"
    





class Ingredient(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='ingredients/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Concerns(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='ingredients/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    STATUS_CHOICES = (
        ('In stock', 'In stock'),
        ('Limited stock', 'Limited stock'),
        ('Out of stock', 'Out of stock'),
    )
    
    product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    heading = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    video = models.FileField(upload_to='products_videos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    quantity = models.IntegerField(default=0)  # Added default value
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='In stock')
    ingredients = models.ManyToManyField('Ingredient', blank=True)
    concerns = models.ManyToManyField('Concerns', blank=True)
    # display_order = models.OneToOneField(ProductOrder, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.heading

    def save(self, *args, **kwargs):
        if self.quantity == 0:
            self.status = 'Out of stock'
        elif self.quantity < 5:
            self.status = 'Limited stock'
        else:
            self.status = 'In stock'
        
        self.slug = slugify(self.heading)
        super(Product, self).save(*args, **kwargs)






class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products_images/')


class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE ,null=True)
    phone_number = models.CharField(max_length=20)


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        """Calculate the total price for this cart item."""
        return (self.product.discount_price or self.product.original_price) * self.quantity

    def update_quantity_and_total(self):
        """Update the quantity and ensure the total is recalculated."""
        if self.quantity < 1:
            self.quantity = 1
        self.save()

    def save(self, *args, **kwargs):
        # Ensure quantity is always at least 1
        if self.quantity < 1:
            self.quantity = 1
        super().save(*args, **kwargs)




class Blog(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=100)
    content = models.TextField()
    image = models.ImageField(upload_to='blog_images/')
    pub_date = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Blog, self).save(*args, **kwargs)



class SwiperSlide(models.Model):
    image = models.ImageField(upload_to='swiper_slides/')  # Image for the slide
    button_text = models.CharField(max_length=100, default='Button')  # Button text
    button_url = models.URLField(max_length=200, default='#')  # Button link
    
    def __str__(self):
        return self.button_text  # Return a descriptive text
    

class ClientLogo(models.Model):
    image = models.ImageField(upload_to='client_logos/')  # Image upload location
    alt_text = models.CharField(max_length=255, default='Client Logo')  # Alt text for accessibility

    def __str__(self):
        return self.alt_text



class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class HeroSection(models.Model):
    heading = models.CharField(max_length=200)
    paragraph = models.TextField()
    background_image = models.ImageField(upload_to='hero_images/')

    def __str__(self):
        return self.heading
    
class Jumbotron(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    background_image = models.ImageField(upload_to='jumbotron_images/')

    def __str__(self):
        return self.title



class Mobile_slider(models.Model):
    image = models.ImageField(upload_to='swiper_slides/')  # Image for the slide
    button_text = models.CharField(max_length=100, default='Button')  # Button text
    button_url = models.URLField(max_length=200, default='#')  # Button link
    
    def __str__(self):
        return self.button_text  # Return a descriptive text
    
class Video(models.Model):
    product = models.ForeignKey(Product, related_name='videos', on_delete=models.CASCADE)
    video_file = models.FileField(upload_to='product_videos/')



class Order(models.Model):

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=100)
    address = models.TextField()
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')  # Add this line
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.heading} (Order {self.order.id})"




class IngredientCategory(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='ingredient_category_images/', blank=True, null=True)

    def __str__(self):
        return self.name


class Ingredients(models.Model):
    category = models.ForeignKey(IngredientCategory, on_delete=models.CASCADE)
    product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE, default=1)  # Set an appropriate default ID
    categorys = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    measurement = models.CharField(max_length=50)  # e.g., '100g', '50ml'
    image = models.ImageField(upload_to='ingredient_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.measurement})"
    


class CustomizedProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)  # User-defined name for the customized product
    ingredients = models.ManyToManyField(Ingredients, blank=True)
    product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE,default=1)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Customized by {self.user.username}: {self.name}"



class CustomizedCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    customized_product = models.ForeignKey(CustomizedProduct, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def update_total_price(self):
        self.total_price = self.customized_product.total_price * self.quantity
        self.save()

    def __str__(self):
        return f"Cart of {self.user.username} - {self.customized_product.name}"



class CustomizedOrder(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    address = models.TextField()
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class CustomizedOrderItem(models.Model):
    order = models.ForeignKey(CustomizedOrder, related_name='items', on_delete=models.CASCADE)
    customized_product = models.ForeignKey(CustomizedProduct, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.customized_product.name} (Order {self.order.id})"




class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contact from {self.name} ({self.email})"




class TimelineEvent(models.Model):
    year = models.CharField(max_length=4, unique=True)  # Store the year as a string
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='timeline_images/')  # Image upload path

    def __str__(self):
        return f"{self.year} - {self.title}"
    


class Section(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='section_images/')
    order = models.PositiveIntegerField(default=1)  # To control the display order

    class Meta:
        ordering = ['order']  # Ensure sections are displayed in the correct order

    def __str__(self):
        return self.title



class WhyMilkFeature(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    icon = models.ImageField(upload_to='why_milk_icons/', blank=True, null=True)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title




class WorkWithUs(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    contact_email = models.EmailField()
    image = models.ImageField(upload_to='work_with_us/', blank=True, null=True)

    def __str__(self):
        return self.title
