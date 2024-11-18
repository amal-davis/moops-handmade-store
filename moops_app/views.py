import json
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.models import User,auth
from django.urls import reverse
from .models import *
from django.shortcuts import get_object_or_404,redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.mail import send_mail
from django.utils.text import slugify
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.contrib.auth import logout  # Correct import
from django.views.decorators.http import require_POST
from django.db.models import Avg
from django.template import Library
from django.contrib.auth.decorators import user_passes_test
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction











# Create your views here.


def index(request):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    blogs = Blog.objects.all()
    reversed_order = reversed(list(blogs))
    ingredient = Ingredient.objects.all()
    concerns = Concerns.objects.all()  # Retrieve all ingredients
    slides = SwiperSlide.objects.all()
    mobile_slides = Mobile_slider.objects.all()
    logos = ClientLogo.objects.all()
    hero = HeroSection.objects.first()
    jumbotron = Jumbotron.objects.first()
    videos = Video.objects.all()
    user = request.user.id
    carts = Cart.objects.filter(user=user)
    total_quantity = sum(cart.quantity for cart in carts) 
    # Generate slug for each category
    for category in categories:
        category.slug = slugify(category.name)

    # Get ordered products
    product_orders = ProductOrder.objects.all()
    ordered_products = [product_order.product for product_order in product_orders]

    # Fetch all products and order them based on the display_order
    all_products = Product.objects.all().order_by('id')
    products = [product for product in all_products if product in ordered_products]
    for product in products:
        product.reviews = Review.objects.filter(product=product)
        product.average_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        product.stars_representation = stars(product.average_rating)
        product.slug = slugify(product.heading)

    # Fetch the latest 4 regular products
    regular_products = Product.objects.exclude(id__in=[product.id for product in ordered_products]).order_by('-created_at')[:4]
    for product in regular_products:
        product.reviews = Review.objects.filter(product=product)
        product.average_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        product.stars_representation = stars(product.average_rating)
        product.slug = slugify(product.heading)

    context = {
        'product_types': product_types,
        'cart_quantity':total_quantity,
        'categories': categories,
        'products': products,
        'regular_products': regular_products,
        'blogs': reversed_order,
        'ingredient':ingredient,
        'slides':slides,
        'logos':logos,
        'concerns':concerns,
        'hero':hero,
        'jumbotron':jumbotron,
        'mobile_slides':mobile_slides,
        'videos':videos
    }

    return render(request, 'index.html', context)


register = Library()

@register.filter(name='stars')
def stars(average_rating):
    full_stars = int(average_rating)  # Full stars
    half_star = 1 if (average_rating - full_stars) >= 0.5 else 0  # Half star if the decimal part is >= 0.5
    empty_stars = 5 - (full_stars + half_star)  # Remaining empty stars to make 5

    return {
        'full_stars': range(full_stars),
        'half_star': half_star,
        'empty_stars': range(empty_stars)
    }


def product_detail(request, slug):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    product = get_object_or_404(Product, slug=slug)
    reviews = Review.objects.filter(product=product)
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    stars_representation = stars(average_rating)

    return render(request, 'product_details.html', {'product': product,'reviews': reviews, 'average_rating': average_rating,'stars_representation':stars_representation,'product_types':product_types,'categories':categories})



@login_required(login_url='signin')
def product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if rating and comment:
            Review.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment
            )
            product_slug = slugify(product.heading)  # Ensure this matches how slugs are generated/saved in the Product model
            return redirect('product_detail', slug=product_slug)

    return render(request, 'product_details.html', {'product': product})


def all_products(request):
    # Fetch all products ordered by creation date in descending order
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    products = Product.objects.all().order_by('-created_at')

    # Add reviews, average rating, and stars representation to each product
    for product in products:
        product.reviews = Review.objects.filter(product=product)
        product.average_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        product.stars_representation = stars(product.average_rating)
        product.slug = slugify(product.heading)

    # Handle sorting by price
    price_order = request.GET.get('price_order', 'low_to_high')
    if price_order == 'low_to_high':
        products = products.order_by('discount_price')
    elif price_order == 'high_to_low':
        products = products.order_by('-discount_price')

    # Pagination setup
    items_per_page = 20  # Set the number of items per page
    paginator = Paginator(products, items_per_page)
    page_number = request.GET.get('page', 1)  # Get the current page from the request
    page_obj = paginator.get_page(page_number)

    return render(request, 'products.html', {
        'products': page_obj,  # Pass the paginated products
        'price_order': price_order,
        'product_types': product_types,
        'categories': categories
    })




@login_required(login_url='signin')
def admin_page(request):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request,'admin.html',{'product_types':product_types,'categories':categories})

def login_page(request):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request,'login.html',{'product_types':product_types,'categories':categories})

def signup_page(request):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render (request,'sign_in.html',{'product_types':product_types,'categories':categories})

def contact_page(request):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request,'contact_us.html',{'product_types':product_types,'categories':categories})


@login_required(login_url='signin')
def cart_page(request):
    carts = Cart.objects.filter(user=request.user).order_by('-id')
    total_price = 0
    subtotal = 0  # Initialize subtotal here
    for cart in carts:
        cart.subtotal = cart.product.discount_price * cart.quantity
        total_price += cart.subtotal
        subtotal += cart.subtotal
    return render(request, 'cart.html', {'carts': carts, 'total_price': total_price,'subtotal':subtotal})


def wishlist(request):
    return render(request,'wish_list.html')



@login_required(login_url='signin')
def remove_from_cart(request, pk):
    cart = Cart.objects.filter(id=pk, user=request.user).first()
    if cart:
        cart.delete()
    return redirect('cart_page')
    

@login_required(login_url='signin')
def update_cart(request,pk):
    cart = Cart.objects.filter(id=pk, user=request.user).first()
    if cart and request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart.quantity = quantity
        cart.save()
    return redirect('cart_page')




@login_required(login_url='signin')
def update_cart_quantity(request):
    if request.method == 'POST':
        cart_id = request.POST.get('cart_id')
        quantity = int(request.POST.get('quantity', 1))

        try:
            cart_item = Cart.objects.get(id=cart_id, user=request.user)
            cart_item.quantity = quantity
            cart_item.save()

            # Return the updated total price for this item
            return JsonResponse({'total_price': cart_item.total_price}, status=200)
        except Cart.DoesNotExist:
            return JsonResponse({'error': 'Cart item not found'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)




def add_product_type(request):
    if request.method == 'POST':
        product_type_name = request.POST.get('product_type_name')
        product_type_image = request.FILES.get('product_type_image')  # Get the uploaded image
        
        if product_type_name:
            # Create a new ProductType with the provided name and image
            ProductType.objects.create(
                name=product_type_name,
                image=product_type_image
            )
        
        return redirect('add_product_type')
    
    product_type = ProductType.objects.all()
    
    categories = Category.objects.all()
    return render(request, 'add_product_type.html', {'product_type': product_type,'categories':categories})



def edit_product_type(request, edit_type):
    product_type = get_object_or_404(ProductType, id=edit_type)

    if request.method == 'POST':
        product_type_name = request.POST.get('product_type_name')
        product_type_image = request.FILES.get('product_type_image')

        if product_type_name:
            product_type.name = product_type_name
        
        if product_type_image:
            product_type.image = product_type_image
        
        product_type.save()  # Save changes to the product type
        
        return redirect('add_product_type')  # Redirect to the list page
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request, 'edit_product_type.html', {'product_type': product_type,'product_types':product_types,'categories':categories})


def delete_product_type(request, delet_product_type):
    product_type = get_object_or_404(ProductType, id=delet_product_type)
    
    product_type.delete()  # Delete the product type
    
    return redirect('add_product_type')  # Redirect to the list page



def product_type_page(request, product_typese):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()

    # Fetch the product type by ID
    product_type = get_object_or_404(ProductType, id=product_typese)
    
    # Filter products by the selected product type
    products = Product.objects.filter(product_type=product_type).order_by('-created_at')
    
    # Add reviews, average rating, and stars representation to each product
    for product in products:
        product.reviews = Review.objects.filter(product=product)
        product.average_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        product.stars_representation = stars(product.average_rating)
        product.slug = slugify(product.heading)

    # Pagination setup
    items_per_page = 20  # Adjust the number of items per page as needed
    paginator = Paginator(products, items_per_page)
    page_number = request.GET.get('page', 1)  # Get the current page from the request
    page_obj = paginator.get_page(page_number)

    return render(request, 'product_type_page.html', {
        'product_type': product_type,
        'products': page_obj,
        'product_types': product_types,
        'categories': categories
    })

def add_category(request):
    if request.method == 'POST':
        product_type_id = request.POST.get('product_type')
        category_name = request.POST.get('category_name')
        if product_type_id and category_name:
            Category.objects.create(product_type_id=product_type_id, name=category_name)
        return redirect('add_category')
    
    product_types = ProductType.objects.all()
    categories = Category.objects.all()

    return render(request, 'add_category.html', {'product_types': product_types, 'categories': categories})


def category_view(request, category_id):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    reversed_order = reversed(list(products))
    for product in products:
        product.reviews = Review.objects.filter(product=product)
        product.average_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        product.stars_representation = stars(product.average_rating)
        product.slug = slugify(product.heading)
    return render(request, 'category_template.html', {'category': category,'products':reversed_order,'product_types':product_types,'categories':categories})


def add_product(request):
    if request.method == 'POST':
        product_type_id = request.POST.get('product_type')
        category_id = request.POST.get('category')
        heading = request.POST.get('heading')
        description = request.POST.get('description')
        original_price = request.POST.get('original_price')
        discount_price = request.POST.get('discount_price')
        video = request.FILES.get('video')
        quantity = int(request.POST['quantity'])

        # Create product instance first without many-to-many fields
        product = Product.objects.create(
            product_type_id=product_type_id,
            category_id=category_id,
            heading=heading,
            description=description,
            original_price=original_price,
            discount_price=discount_price,
            video=video,
            quantity=quantity,
        )

        # Then set many-to-many fields
        ingredients_ids = request.POST.getlist('ingredients')
        concerns_ids = request.POST.getlist('concerns')
        product.ingredients.set(ingredients_ids)
        product.concerns.set(concerns_ids)

        # Handle multiple images
        images = request.FILES.getlist('images')
        for image in images:
            ProductImage.objects.create(product=product, image=image)

        # Refresh your context data if needed
        products = Product.objects.all()
        reversed_order = reversed(list(products))
        product_types = ProductType.objects.all()
        categories = Category.objects.all()
        ingredient = Ingredient.objects.all()
        concern = Concerns.objects.all()

        return render(request, 'add_product.html', {
            'product_types': product_types,
            'categories': categories,
            'products': reversed_order,
            'ingredient': ingredient,
            'concern': concern
        })
    else:
        # Initial rendering of the form
        product_types = ProductType.objects.all()
        categories = Category.objects.all()
        products = Product.objects.all()
        reversed_order = reversed(list(products))
        ingredient = Ingredient.objects.all()
        concern = Concerns.objects.all()
        return render(request, 'add_product.html', {
            'product_types': product_types,
            'categories': categories,
            'products': reversed_order,
            'ingredient': ingredient,
            'concern': concern
        })


def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)  # Get the product by ID

    if request.method == 'POST':  # Handle form submission for updating the product
        # Update other fields
        product.product_type_id = request.POST.get('product_type', product.product_type_id)
        product.category_id = request.POST.get('category', product.category_id)
        product.heading = request.POST.get('heading', product.heading)
        product.description = request.POST.get('description', product.description)
        product.original_price = float(request.POST.get('original_price', product.original_price))
        product.discount_price = float(request.POST.get('discount_price', product.discount_price))
        product.quantity = int(request.POST.get('quantity', product.quantity))
        product.concerns_id = request.POST.get('concerns', product.concerns_id)
        product.Ingredeints_id = request.POST.get('ingredients', product.Ingredeints_id)

        # Check if a new video is provided
        new_video = request.FILES.get('video')
        if new_video:
            product.video = new_video  # Replace only if a new video is uploaded
        # If no new video is provided, do nothing (retain the existing video)

        product.save()  # Save changes to the product

        # Handle new images if updated
        new_images = request.FILES.getlist('images')  # Get the list of new images
        for image in new_images:
            ProductImage.objects.create(product=product, image=image)  # Add new images

        # Redirect to the product detail or other relevant page after successful update
        return redirect('add_product')

    # Provide context data for rendering the edit form
    context = {
        'product': product,
        'product_types': ProductType.objects.all(),
        'categories': Category.objects.all(),
        'ingredients': Ingredient.objects.all(),
        'concerns': Concerns.objects.all(),
    }

    return render(request, 'edit_product.html', context)


def p_delete_form(request,pk):
    edit=Product.objects.get(id=pk)
    edit.delete()
    return redirect('add_product')


def usercreate(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        password = request.POST['password']
        cpassword = request.POST['confirm_password']
        email = request.POST['email']
        phone_no = request.POST['phone']

        # Validate password using Django's password_validation module
        try:
            password_validation.validate_password(password)
        except ValidationError as e:
            messages.error(request, "\n".join(e.messages))
            return redirect('signup_page')

        if password == cpassword:
            # Check if the username is already taken
            if User.objects.filter(username=username).exists():
                messages.info(request, 'This username is already taken. Please choose a different one.')
                return redirect('signup_page')
            else:
                # Create the user and profile
                user = User.objects.create_user(
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    password=password,
                    email=email
                )
                user.save()

                user_profile = UserProfile.objects.create(
                    user=user,
                    phone_number=phone_no
                )
                user_profile.save()
                print('Succeed....')
        else:
            messages.info(request, 'Password does not match!!!!!')
            print('Password is not matching')
            return redirect('signup_page')

        return redirect('login_page')
    else:
        return render(request, 'sign_in.html')
    

def signin(request):
    if request.method == 'POST':
        # Get the username (or email) and password from the request, with default values to avoid KeyError
        username = request.POST.get('username', '')  # Assuming 'username' is the email
        password = request.POST.get('password', '')

        # Authenticate the user with the provided credentials
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # User authenticated successfully
            login(request, user)  # Log in the user

            # Redirect based on user type
            if user.is_staff:
                return redirect('admin_page')  # Redirect admin users to the admin page
            else:
                return redirect('index')  # Redirect regular users to the index page
        else:
            # Authentication failed, show an error message
            messages.error(request, 'Invalid credentials. Please try again.')
            # Render the login page with the error message
            return render(request, 'login.html', context={'error': 'Invalid credentials'})

    # If not a POST request, render the login page
    return render(request, 'login.html')


def logout(request):
	auth.logout(request)
	return redirect('index')



@login_required(login_url='signin')  # Ensure this URL is correct
def add_to_cart(request, pk):
    product = Product.objects.get(id=pk)  # Simplified from filter().first() to get()

    if product:
        try:
            cart = Cart.objects.get(user=request.user, product=product)
            cart.quantity += 1
            cart.save()
        except Cart.DoesNotExist:
            cart = Cart(user=request.user, product=product)
            cart.save()

    return redirect('cart_page')


def add_blogs(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        content = request.POST.get('content')
        image = request.FILES.get('image')

        blog = Blog(title=title, author=author, content=content, image=image)
        blog.save()

        return redirect('add_blogs')
    blogs = Blog.objects.all()
    reversed_order = reversed(list(blogs))
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request,'add_blog.html',{'blogs':reversed_order,'product_types':product_types,'categories':categories})



def edit_blog(request, blog_id):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    blog = get_object_or_404(Blog, id=blog_id)
    if request.method == 'POST':
        blog.title = request.POST.get('title')
        blog.author = request.POST.get('author')
        blog.content = request.POST.get('content')
        blog.image = request.FILES.get('image', blog.image)  # Use existing image if new one isn't uploaded

        blog.save()
        return redirect('add_blogs')  # Redirect to the blog detail view or any other suitable view

    return render(request, 'edit_blogs.html', {'blog': blog,'product_types':product_types,'categories':categories})


def delete_blogs(request, delet_blogs):
    product_type = get_object_or_404(Blog, id=delet_blogs)
    
    product_type.delete()  # Delete the product type
    
    return redirect('add_blogs')  # Redirect to the list page


def blog_detail(request, slug):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    blog = get_object_or_404(Blog, slug=slug)
    context = {
        'blog': blog,
        'product_types':product_types,
        'categories':categories
    }
    return render(request, 'blog_details.html', context)


def manage_product_order(request):
    products = Product.objects.all()
    product_orders = ProductOrder.objects.all()
    product_types = ProductType.objects.all()
    categories = Category.objects.all()

    if request.method == 'POST':
        product_id = request.POST.get('product')
        order = request.POST.get('order')
        
        # Check if product_order already exists
        existing_product_order = ProductOrder.objects.filter(product_id=product_id).first()

        if existing_product_order:
            existing_product_order.order = order
            existing_product_order.save()
        else:
            ProductOrder.objects.create(product_id=product_id, order=order)

        return redirect('manage_product_order')

    context = {
        'products': products,
        'product_orders': product_orders,
        'product_types':product_types,
        'categories':categories

    }

    return render(request, 'manage_product_order.html', context)



def add_ingredient(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')

        # Create the ingredient with name and image
        Ingredient.objects.create(name=name, image=image)
        
        return redirect('add_ingredient')  # Redirect after successful addition
    
    ingredients = Ingredient.objects.all()  # Retrieve all ingredients
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request, 'add_ingredient.html',{'ingredients':ingredients,'product_types':product_types,'categories':categories})  # Render form for adding



def delete_ingredient(request, ingredints):
    ingredient = get_object_or_404(Ingredient, id=ingredints)
    ingredient.delete()  # Delete the ingredient
    
    return redirect('add_ingredient')  # Redirect after successful deletion



def edit_ingredient(request, edit):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    ingredient = get_object_or_404(Ingredient, id=edit)

    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')

        if name:
            ingredient.name = name  # Update the name
        if image:
            ingredient.image = image  # Update the image
        
        ingredient.save()  # Save the changes
        
        return redirect('add_ingredient')  # Redirect after successful edit

    return render(request, 'edit_ingredient.html', {'ingredient': ingredient,'product_types':product_types,'categories':categories}) 



def ingredient_detail(request, ingredients):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    ingredient = get_object_or_404(Ingredient, id=ingredients)  # Fetch the ingredient by ID
    products = Product.objects.filter(ingredients=ingredient)
    reversed_order = reversed(list(products))
    for product in products:
        product.reviews = Review.objects.filter(product=product)
        product.average_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        product.stars_representation = stars(product.average_rating)
        product.slug = slugify(product.heading)
    return render(request, 'ingredient_detail.html', {'ingredient': ingredient,'products':reversed_order,'product_types':product_types,'categories':categories})  # Render the detail page




def add_concerns(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')

        # Create the ingredient with name and image
        Concerns.objects.create(name=name, image=image)
        
        return redirect('add_concerns')  # Redirect after successful addition
    
    concerns = Concerns.objects.all()  # Retrieve all ingredients
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request, 'add_concerns.html',{'concerns':concerns,'product_types':product_types,'categories':categories})  # Render form for adding



def delete_concerns(request, concerns):
    ingredient = get_object_or_404(Concerns, id=concerns)
    ingredient.delete()  # Delete the ingredient
    
    return redirect('add_concerns')  # Redirect after successful deletion



def edit_concerns(request, edit):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    concerns = get_object_or_404(Concerns, id=edit)

    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')

        if name:
            concerns.name = name  # Update the name
        if image:
            concerns.image = image  # Update the image
        
        concerns.save()  # Save the changes
        
        return redirect('add_concerns')  # Redirect after successful edit

    return render(request, 'edit_concerns.html', {'concerns': concerns,'product_types':product_types,'categories':categories}) 



def concern_detail(request, concern):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    concerns = get_object_or_404(Concerns, id=concern)  # Fetch the ingredient by ID
    products = Product.objects.filter(concerns=concerns)
    reversed_order = reversed(list(products))
    for product in products:
        product.reviews = Review.objects.filter(product=product)
        product.average_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        product.stars_representation = stars(product.average_rating)
        product.slug = slugify(product.heading)
    return render(request, 'concern_detail.html', {'concerns': concerns,'products':reversed_order,'product_types':product_types,'categories':categories})  # Render the detail page



def add_slider_content(request):
    if request.method == 'POST':
        
        image = request.FILES.get('image')
        button_text = request.POST.get('button_text')
        button_url = request.POST.get('button_url') 

        # Create the ingredient with name and image
        SwiperSlide.objects.create(button_text=button_text, image=image, button_url=button_url)
        
        return redirect('add_slider_content')  # Redirect after successful addition
    
    slides = SwiperSlide.objects.all()  # Retrieve all ingredients
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request, 'add_sliders.html',{'slides':slides,'product_types':product_types,'categories':categories})  # Render form for adding





def edit_swiper_slide(request, slide_id):
    slide = get_object_or_404(SwiperSlide, id=slide_id)  # Get the Swiper slide by ID
    product_types = ProductType.objects.all()
    categories = Category.objects.all()

    if request.method == 'POST':  # Handle form submission for editing
        image = request.FILES.get('image')  # Updated image
        button_text = request.POST.get('button_text')  # Updated button text
        button_url = request.POST.get('button_url')  # Updated button URL

        # Update the Swiper slide fields
        if image:
            slide.image = image
        slide.button_text = button_text
        slide.button_url = button_url
        
        slide.save()  # Save the changes
        return redirect('add_slider_content')  # Redirect to the list page

    return render(request, 'edit_swiper_slide.html', {'slide': slide,'product_types':product_types,'categories':categories}) 



def delete_swiper_slide(request, slide_id):
    slide = get_object_or_404(SwiperSlide, id=slide_id)  # Get the Swiper slide by ID
    
    slide.delete()  # Delete the Swiper slide
    return redirect('add_slider_content') 



def add_mobile_slider_content(request):
    if request.method == 'POST':
        
        image = request.FILES.get('image')
        button_text = request.POST.get('button_text')
        button_url = request.POST.get('button_url') 

        # Create the ingredient with name and image
        Mobile_slider.objects.create(button_text=button_text, image=image, button_url=button_url)
        
        return redirect('add_mobile_slider_content')  # Redirect after successful addition
    
    slides = Mobile_slider.objects.all()  # Retrieve all ingredients
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request, 'add_responsive swiper.html',{'slides':slides,'product_types':product_types,'categories':categories})


def delete_mobile_slide(request, slide_id):
    slide = get_object_or_404(Mobile_slider, id=slide_id)  # Get the Swiper slide by ID
    
    slide.delete()  # Delete the Swiper slide
    return redirect('add_mobile_slider_content')


def edit_mobile_slide(request, slide_id):
    slide = get_object_or_404(Mobile_slider, id=slide_id)  # Get the Swiper slide by ID
    product_types = ProductType.objects.all()
    categories = Category.objects.all()

    if request.method == 'POST':  # Handle form submission for editing
        image = request.FILES.get('image')  # Updated image
        button_text = request.POST.get('button_text')  # Updated button text
        button_url = request.POST.get('button_url')  # Updated button URL

        # Update the Swiper slide fields
        if image:
            slide.image = image
        slide.button_text = button_text
        slide.button_url = button_url
        
        slide.save()  # Save the changes
        return redirect('add_mobile_slider_content')  # Redirect to the list page

    return render(request, 'edit_mobile_slide.html', {'slide': slide,'product_types':product_types,'categories':categories}) 



def add_find_logo(request):
    if request.method == 'POST':
        
        image = request.FILES.get('image')
        alt_text = request.POST.get('alt_text')

        # Create the ingredient with name and image
        ClientLogo.objects.create(alt_text=alt_text, image=image)
        
        return redirect('add_find_logo')  # Redirect after successful addition
    
    logos = ClientLogo.objects.all()  # Retrieve all ingredients
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request, 'add_find_logo.html',{'logos':logos,'product_types':product_types,'categories':categories})  # Render form for adding



def edit_find_logo(request, slide_id):
    logo = get_object_or_404(ClientLogo, id=slide_id)  # Get the Swiper slide by ID
    product_types = ProductType.objects.all()
    categories = Category.objects.all()

    if request.method == 'POST':  # Handle form submission for editing
        image = request.FILES.get('image')  # Updated image
        alt_text = request.POST.get('alt_text')  # Updated button text
        

        # Update the Swiper slide fields
        if image:
            logo.image = image
        logo.alt_text = alt_text
        
        logo.save()  # Save the changes
        return redirect('add_find_logo')  # Redirect to the list page

    return render(request, 'edit_find_logo.html', {'logo': logo,'product_types':product_types,'categories':categories})


def delete_find_logo(request, slide_id):
    slide = get_object_or_404(ClientLogo, id=slide_id)  # Get the Swiper slide by ID
    
    slide.delete()  # Delete the Swiper slide
    return redirect('add_find_logo')


def home_page_contents(request):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request,'home_page_contents.html',{'product_types':product_types,'categories':categories})


@login_required(login_url='signin')
def add_to_cart_details(request, pk):
    product = get_object_or_404(Product, id=pk)
    user = request.user
    cart_item = Cart.objects.filter(user=user, product=product).first()

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if cart_item:
            cart_item.quantity += quantity
            cart_item.update_quantity_and_total()  # Call the method to save the updated quantity
        else:
            Cart.objects.create(user=user, product=product, quantity=quantity)

        return redirect('cart_page') 

    

def add_hero_section(request):
    if request.method == 'POST':
        heading = request.POST.get('heading')
        text = request.POST.get('description')
        image = request.FILES.get('image')

        herosection = HeroSection.objects.create(heading=heading,paragraph=text,background_image=image)
        herosection.save()
        return redirect('add_hero_section')
    hero = HeroSection.objects.all()
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request,'add_hero_section.html',{'hero':hero,'product_types':product_types,'categories':categories})


def edit_hero_section(request, hero_id):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    hero = get_object_or_404(HeroSection, pk=hero_id)

    if request.method == 'POST':
        hero.heading = request.POST.get('heading')
        hero.paragraph = request.POST.get('description')
        image = request.FILES.get('image') if 'image' in request.FILES else None

        if image:
            hero.background_image = image
        hero.save()
        return redirect('add_hero_section')  # Assuming you have a detail view to redirect to

    return render(request, 'edit_hero_section.html', {'hero': hero,'product_types':product_types,'categories':categories})


def delete_hero_section(request, hero_id):
    hero = get_object_or_404(HeroSection, id=hero_id)  # Get the Swiper slide by ID
    
    hero.delete()  # Delete the Swiper slide
    return redirect('add_hero_section')



def add_jumbotron_section(request):
    if request.method == 'POST':
        heading = request.POST.get('heading')
        text = request.POST.get('description')
        image = request.FILES.get('image')

        herosection = Jumbotron.objects.create(title=heading,text=text,background_image=image)
        herosection.save()
        return redirect('add_jumbotron_section')
    jumbotron = Jumbotron.objects.all()
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request,'add_jumbotron_section.html',{'jumbotron':jumbotron,'product_types':product_types,'categories':categories})



def delete_jumbotron_section(request, jumbotron):
    jumbotrons = get_object_or_404(Jumbotron, id=jumbotron)  # Get the Swiper slide by ID
    
    jumbotrons.delete()  # Delete the Swiper slide
    return redirect('add_jumbotron_section')



def edit_jumbotron_section(request, hero_id):
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    jumbotron = get_object_or_404(Jumbotron, pk=hero_id)

    if request.method == 'POST':
        jumbotron.title = request.POST.get('heading')
        jumbotron.text = request.POST.get('description')
        image = request.FILES.get('image') if 'image' in request.FILES else None

        if image:
            jumbotron.background_image = image
        jumbotron.save()
        return redirect('add_jumbotron_section')  # Assuming you have a detail view to redirect to
    

   

    return render(request, 'edit_jumbotron_section.html', {'jumbotron': jumbotron,'product_types':product_types,'categories':categories})



def add_video(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        video_file = request.FILES.get('video_file')
        
        if product_id and video_file:
            product = Product.objects.get(id=product_id)
            Video.objects.create(product=product, video_file=video_file)
            return redirect('add_video')  # Redirect after posting

    products = Product.objects.all()  # Get all products to populate the select box
    videos = Video.objects.all().select_related('product')
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request, 'add_video.html', {'products': products,'videos':videos,'product_types':product_types,'categories':categories})




def delete_video_section(request, video):
    jumbotrons = get_object_or_404(Video, id=video)  # Get the Swiper slide by ID
    
    jumbotrons.delete()  # Delete the Swiper slide
    return redirect('add_video')



def edit_video(request, pk):
    video = get_object_or_404(Video, pk=pk)
    if request.method == 'POST':
        product_id = request.POST.get('product')
        video_file = request.FILES.get('video_file') if 'video_file' in request.FILES else None

        if product_id:
            video.product_id = product_id
            if video_file:
                video.video_file = video_file
            video.save()
            return redirect('add_video')  # Redirect to the video list view after successful update

    products = Product.objects.all()  # Fetch all products for dropdown
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request, 'edit_video.html', {'video': video, 'products': products,'product_types':product_types,'categories':categories})



def about_us(request):
    sections = Section.objects.all()
    features = WhyMilkFeature.objects.all().order_by('order')
    section = WorkWithUs.objects.all()
    return render(request,'about_us.html',{'sections':sections,'features':features,'section':section})


razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required(login_url='signin')
def checkout_page(request):
    cart_items = Cart.objects.filter(user=request.user)

    # Calculate the total amount for the cart items
    total_amount = sum(item.total_price for item in cart_items)  # Use the `total_price` property from the Cart model

    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'razorpay_key': settings.RAZORPAY_KEY_ID,  # Pass Razorpay API key
    }

    return render(request, 'checkout_page.html', context)




@login_required(login_url='signin')
def process_order(request):
    if request.method == 'POST':
        subtotal = request.POST.get('subtotal', 0)
        subtotal = float(subtotal)  # Convert subtotal to float

        if subtotal <= 0:
            return JsonResponse({'error': 'Invalid total amount. Cannot proceed with payment.'}, status=400)

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        amount_in_paise = int(subtotal * 100)  # Convert to paise

        try:
            # Create a Razorpay order
            razorpay_order = client.order.create({
                'amount': amount_in_paise,
                'currency': 'INR',
                'payment_capture': '1',
            })

            # Return Razorpay order details to the frontend
            return JsonResponse({
                'order_id': razorpay_order['id'],
                'amount': subtotal,
                'currency': 'INR',
                'key': settings.RAZORPAY_KEY_ID,
                'name': 'Moops',
                'description': 'Order Payment',
                'prefill': {
                    'name': request.POST.get('first_name', '') + ' ' + request.POST.get('last_name', ''),
                    'email': request.POST.get('email', ''),
                    'contact': request.POST.get('phone', ''),
                },
                'callback_url': request.build_absolute_uri('/razorpay_callback/'),
            })

        except razorpay.errors.BadRequestError as e:
            print("Razorpay error:", str(e))
            return JsonResponse({'error': 'Failed to create Razorpay order. Please try again.'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=400)








@csrf_exempt
def razorpay_callback(request):
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            print("Parsed callback data:", data)

            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_signature = data.get('razorpay_signature')

            # Verify Razorpay signature
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            print("Payment signature verified successfully.")

            # Save the order and order items only after successful payment
            user = request.user
            cart_items = Cart.objects.filter(user=user)
            total_amount = sum(item.total_price for item in cart_items)

            order = Order.objects.create(
                user=user,
                razorpay_order_id=razorpay_order_id,
                name=data.get('name', ''),
                email=data.get('email', ''),
                phone=data.get('contact', ''),
                total_amount=total_amount,
                status='Processing'  # Update status to Processing after payment
            )

            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.total_price
                )

                # Deduct product quantity
                product = cart_item.product
                if product.quantity >= cart_item.quantity:
                    product.quantity -= cart_item.quantity
                    product.save()
                else:
                    print(f"Insufficient stock for product: {product.heading}")

            # Clear the cart
            cart_items.delete()

            return JsonResponse({'success': True, 'redirect_url': reverse('payment_success')})

        except razorpay.errors.SignatureVerificationError as e:
            print("Signature verification failed:", str(e))
            return JsonResponse({'success': False, 'redirect_url': reverse('payment_failed')}, status=400)

        except Exception as e:
            print("Error in callback:", str(e))
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)








        

    
def payment_success(request):
    return render(request,'payment_success.html')

def payment_failed(request):
    return render(request,'payment_failed.html')


@login_required(login_url='signin')
def user_orders(request):
    # Fetch orders for the logged-in user, ordered by creation date
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    product_types = ProductType.objects.all()
    categories = Category.objects.all()

    # Set up pagination
    items_per_page = 5  # Number of orders per page
    paginator = Paginator(orders, items_per_page)

    # Get the current page number from the request
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,  # Paginated orders
        'product_types': product_types,
        'categories': categories
    }

    return render(request, 'user_orders.html', context)

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def admin_order_management(request):
    orders = Order.objects.all().order_by('-created_at')  # Fetch all orders

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        
        order = get_object_or_404(Order, id=order_id)
        order.status = new_status
        order.save()
        return redirect('admin_order_management')

    return render(request, 'admin_order_management.html', {'orders': orders})



@login_required(login_url='signin')
def add_ingredient_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')

        # Create and save the new ingredient category
        IngredientCategory.objects.create(name=name, image=image)

        return redirect('add_ingredient_category')  # Redirect to a list of 
    
    categories = IngredientCategory.objects.all()

    return render(request, 'add_ingredient_category.html',{'categories':categories})



@login_required(login_url='signin')
def edit_ingredient_category(request, category_id):
    category = get_object_or_404(IngredientCategory, id=category_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')

        # Update the category's fields
        category.name = name
        if image:  # Only update image if a new one is uploaded
            category.image = image
        category.save()

        return redirect('add_ingredient_category')  # Redirect to the list of categories

    return render(request, 'edit_ingredient_category.html', {'category': category})



@login_required(login_url='signin')
def delete_ingredient_category(request, category_id):
    category = get_object_or_404(IngredientCategory, id=category_id)
    category.delete()
    return redirect('add_ingredient_category')



@login_required(login_url='signin')
def add_ingredients(request):
    if request.method == 'POST':
        product_type_id = request.POST.get('product_type')
        categories_id = request.POST.get('categories')
        category_id = request.POST.get('category')
        name = request.POST.get('name')
        price = request.POST.get('price')
        measurement = request.POST.get('measurement')
        image = request.FILES.get('image')

        category = IngredientCategory.objects.get(id=category_id)
        product_type = ProductType.objects.get(id=product_type_id)
        categorys = Category.objects.get(id=categories_id)

        # Create and save the new ingredient
        Ingredients.objects.create(
            categorys=categorys,
            product_type=product_type,
            category=category,
            name=name,
            price=price,
            measurement=measurement,
            image=image
        )

        return redirect('add_ingredients')  # Redirect to a list of ingredients

    ingredient_categories = IngredientCategory.objects.all()
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    ingredients = Ingredients.objects.all()
    return render(request, 'add_ingredients.html', {'ingredient_categories': ingredient_categories,'product_types':product_types,'categories':categories,'ingredients':ingredients})


@login_required(login_url='signin')
def edit_ingredients(request, ingredient_id):
    ingredient = get_object_or_404(Ingredients, id=ingredient_id)

    if request.method == 'POST':
        ingredient.product_type = ProductType.objects.get(id=request.POST.get('product_type'))
        ingredient.categorys = Category.objects.get(id=request.POST.get('categories'))
        ingredient.category = IngredientCategory.objects.get(id=request.POST.get('category'))
        ingredient.name = request.POST.get('name')
        ingredient.price = request.POST.get('price')
        ingredient.measurement = request.POST.get('measurement')

        image = request.FILES.get('image')
        if image:  # Update the image only if a new one is uploaded
            ingredient.image = image

        ingredient.save()
        return redirect('add_ingredients')  # Redirect to the ingredient list

    ingredient_categories = IngredientCategory.objects.all()
    product_types = ProductType.objects.all()
    categories = Category.objects.all()

    return render(request, 'edit_ingredients.html', {
        'ingredient': ingredient,
        'ingredient_categories': ingredient_categories,
        'product_types': product_types,
        'categories': categories
    })


@login_required(login_url='signin')
def delete_ingredient(request, ingredient_id):
    ingredient = get_object_or_404(Ingredients, id=ingredient_id)
    ingredient.delete()
    return redirect('ingredient_list')  # Redirect to the ingredient list



@login_required(login_url='signin')
def get_ingredients_by_type_and_category(request):
    product_type_id = request.GET.get('product_type_id')
    category_id = request.GET.get('category_id')

    # Filter ingredients by product type and category
    ingredients = Ingredients.objects.filter(
        product_type_id=product_type_id,
        category_id=category_id
    ).values('id', 'name', 'price', 'measurement', 'image')

    # Convert image URL to string for AJAX response
    for ingredient in ingredients:
        ingredient['image'] = str(ingredient['image'])

    return JsonResponse(list(ingredients), safe=False)



@login_required(login_url='signin')
def get_categories_by_product_type(request):
    product_type_id = request.GET.get('product_type_id')
    categories = Category.objects.filter(product_type_id=product_type_id).values('id', 'name')
    return JsonResponse(list(categories), safe=False)


@login_required(login_url='signin')
def add_customized_product(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        product_type_id = request.POST.get('product_type')
        category_id = request.POST.get('category')
        ingredient_ids = request.POST.getlist('ingredient_ids')

        # Get the selected product type and category
        product_type = get_object_or_404(ProductType, id=product_type_id)
        category = get_object_or_404(Category, id=category_id)

        # Calculate total price and collect selected ingredients
        total_price = 0
        selected_ingredients = []

        for ingredient_id in ingredient_ids:
            ingredient = Ingredients.objects.get(id=ingredient_id)
            selected_ingredients.append(ingredient)
            total_price += ingredient.price

        # Create a new CustomizedProduct instance linked to the logged-in user
        customized_product = CustomizedProduct.objects.create(
            user=request.user,
            name=product_name,
            product_type=product_type,
            category=category,
            total_price=total_price
        )

        # Add selected ingredients to the customized product
        for ingredient in selected_ingredients:
            customized_product.ingredients.add(ingredient)

        return redirect('customized_products_page')

    # Fetch all product types to display in the form
    product_types = ProductType.objects.all()
    categories = Category.objects.all()

    return render(request, 'add_customized_product.html', {
        'product_types': product_types,
        'categories':categories,
    })




@login_required(login_url='signin')
def customized_products_page(request):
    customized_products = CustomizedProduct.objects.filter(user=request.user)

    return render(request, 'customized_products.html', {
        'customized_products': customized_products
    })





@login_required(login_url='signin')
def add_customized_product_to_cart(request, cp_id):
    # Get the customized product for the logged-in user only
    customized_product = get_object_or_404(CustomizedProduct, id=cp_id, user=request.user)

    try:
        cart_item = CustomizedCart.objects.get(user=request.user, customized_product=customized_product)
        cart_item.quantity += 1
        cart_item.update_total_price()
    except CustomizedCart.DoesNotExist:
        cart_item = CustomizedCart.objects.create(
            user=request.user,
            customized_product=customized_product,
            quantity=1,
            total_price=customized_product.total_price
        )

    return redirect('customized_cart_page')



@login_required(login_url='signin')
def customized_cart_page(request):
    cart_items = CustomizedCart.objects.filter(user=request.user)
    product_types = ProductType.objects.all()
    categories = Category.objects.all()

    return render(request, 'customized_cart.html', {'cart_items': cart_items,'product_types':product_types,'categories':categories})



@login_required(login_url='signin')
def place_customized_order(request):
    cart_items = CustomizedCart.objects.filter(user=request.user)
    total_amount = sum(item.total_price for item in cart_items)

    if request.method == 'POST':
        # Create Razorpay Order
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        amount_in_paise = int(total_amount * 100)  # Convert to paise

        try:
            razorpay_order = client.order.create({
                'amount': amount_in_paise,
                'currency': 'INR',
                'payment_capture': '1',
            })

            # Return Razorpay order details to the frontend
            return JsonResponse({
                'order_id': razorpay_order['id'],
                'amount': total_amount,
                'currency': 'INR',
                'key': settings.RAZORPAY_KEY_ID,
                'name': request.POST['name'],
                'description': 'Customized Order Payment',
                'prefill': {
                    'name': request.POST['name'],
                    'email': request.POST['email'],
                    'contact': request.POST['phone'],
                },
                'callback_url': request.build_absolute_uri('/customized_razorpay_callback/'),
            })

        except razorpay.errors.BadRequestError as e:
            print("Razorpay error:", str(e))
            return JsonResponse({'error': 'Failed to create Razorpay order. Please try again.'}, status=400)

    product_types = ProductType.objects.all()
    categories = Category.objects.all()

    return render(request, 'place_customized_order.html', {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'product_types': product_types,
        'categories': categories,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
    })



@csrf_exempt
def customized_razorpay_callback(request):
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_signature = data.get('razorpay_signature')

            # Verify Razorpay signature
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            # Save the customized order after payment verification
            user = request.user
            cart_items = CustomizedCart.objects.filter(user=user)
            total_amount = sum(item.total_price for item in cart_items)

            # Create the CustomizedOrder
            order = CustomizedOrder.objects.create(
                user=user,
                name=request.POST.get('name', ''),
                address=request.POST.get('address', ''),
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''),
                total_amount=total_amount,
                status='Processing'  # Update status to Processing after payment
            )

            # Save each customized cart item as an order item
            for cart_item in cart_items:
                CustomizedOrderItem.objects.create(
                    order=order,
                    customized_product=cart_item.customized_product,
                    quantity=cart_item.quantity,
                    price=cart_item.total_price
                )
                cart_item.delete()  # Clear the cart item

            return JsonResponse({'success': True, 'redirect_url': reverse('payment_success')})

        except razorpay.errors.SignatureVerificationError as e:
            print("Signature verification failed:", str(e))
            return JsonResponse({'success': False, 'redirect_url': reverse('payment_failed')}, status=400)

        except Exception as e:
            print("Error in callback:", str(e))
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)




@login_required(login_url='signin')
def update_quantity(request, cart_item_id):
    if request.method == 'POST':
        # Get the cart item for the logged-in user
        cart_item = get_object_or_404(CustomizedCart, id=cart_item_id, user=request.user)

        # Get the new quantity from the form
        new_quantity = int(request.POST.get('quantity'))

        # Ensure the new quantity is at least 1
        if new_quantity < 1:
            messages.error(request, "Quantity cannot be less than 1.")
            return redirect('customized_cart_page')

        # Update the quantity and total price
        cart_item.quantity = new_quantity
        cart_item.update_total_price()

        messages.success(request, "Quantity updated successfully.")
        return redirect('customized_cart_page')
    



@login_required(login_url='signin')
def user_customize_orders(request):
    # Get all orders for the logged-in user
    orders = CustomizedOrder.objects.filter(user=request.user).order_by('-created_at')
    product_types = ProductType.objects.all()
    categories = Category.objects.all()
    return render(request, 'user_customize_orders.html', {'orders': orders,'product_types':product_types,'categories':categories})


@user_passes_test(is_admin)
def manage_orders(request):
    # Fetch all orders
    orders = CustomizedOrder.objects.all().order_by('-created_at')

    # Handle status update
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        order = get_object_or_404(CustomizedOrder, id=order_id)
        order.status = new_status
        order.save()
        return redirect('manage_orders')

    return render(request, 'manage_orders.html', {'orders': orders})




@login_required(login_url='signin')
def remove_from_customized_cart(request, item_id):
    # Get the cart item
    cart_item = get_object_or_404(CustomizedCart, id=item_id, user=request.user)

    # Delete the item from the cart
    cart_item.delete()

    return redirect('customized_cart_page')



def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')

        # Save the contact data to the database
        Contact.objects.create(
            name=name,
            email=email,
            phone=phone,
            message=message
        )

        # Display a success message
        messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
        return redirect('contact_view')  # Redirect to the same page or a success page

    return render(request, 'contact_us.html')





@login_required(login_url='signin')  # Ensure only logged-in users can view
def contact_list(request):
    contacts = Contact.objects.all().order_by('-created_at')
    return render(request, 'contact_list.html', {'contacts': contacts})

# Delete a contact entry
@login_required(login_url='signin')  # Ensure only logged-in users can delete
def delete_contact(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id)
    contact.delete()
    return redirect('contact_list')  # Redirect to the list after deletion





def add_timeline_event(request):
    if request.method == 'POST':
        year = request.POST.get('year')
        title = request.POST.get('title')
        description = request.POST.get('description')
        image = request.FILES.get('image')

        # Save the event
        event = TimelineEvent.objects.create(
            year=year,
            title=title,
            description=description,
            image=image
        )
        event.save()
        return redirect('add_timeline_event')
    return render(request,'add_timeline_event.html')




def manage_sections(request):
    sections = Section.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        order = request.POST.get('order', 1)

        # Create a new section
        Section.objects.create(
            title=title,
            description=description,
            image=image,
            order=order
        )

        return redirect('manage_sections')  # Redirect after saving
    


    return render(request, 'manage_sections.html', {'sections': sections})




def edit_section(request, section_id):
    # Get the specific section or return 404 if not found
    section = get_object_or_404(Section, id=section_id)

    if request.method == 'POST':
        # Update section with the new data
        section.title = request.POST.get('title')
        section.description = request.POST.get('description')
        section.order = request.POST.get('order')

        # Update the image if a new one is provided
        if 'image' in request.FILES:
            section.image = request.FILES['image']

        section.save()  # Save the changes
        return redirect('manage_sections')  # Redirect back to the manage page after saving

    return render(request, 'edit_section.html', {'section': section})




def delete_section(request, pk):
    section = get_object_or_404(Section, pk=pk)
    section.delete()
    return redirect('manage_sections')




def manage_why_milk(request):
    features = WhyMilkFeature.objects.all().order_by('order')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        icon = request.FILES.get('icon')
        order = request.POST.get('order', 1)

        WhyMilkFeature.objects.create(
            title=title,
            description=description,
            icon=icon,
            order=order
        )
        return redirect('manage_why_milk')

    return render(request, 'manage_why_milk.html', {'features': features})




def edit_why_milk(request, feature_id):
    feature = get_object_or_404(WhyMilkFeature, id=feature_id)

    if request.method == 'POST':
        feature.title = request.POST.get('title')
        feature.description = request.POST.get('description')
        feature.order = request.POST.get('order')

        if 'icon' in request.FILES:
            feature.icon = request.FILES['icon']

        feature.save()
        return redirect('manage_why_milk')

    return render(request, 'edit_why_milk.html', {'feature': feature})





def delete_why_milk(request, feature_id):
    feature = get_object_or_404(WhyMilkFeature, id=feature_id)
    feature.delete()
    return redirect('manage_why_milk')



def manage_work_with_us(request):
    sections = WorkWithUs.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        contact_email = request.POST.get('contact_email')
        image = request.FILES.get('image')

        # Create a new entry
        WorkWithUs.objects.create(
            title=title,
            description=description,
            contact_email=contact_email,
            image=image
        )

        return redirect('manage_work_with_us')

    return render(request, 'manage_work_with_us.html', {'sections': sections})




def edit_work_with_us(request, section_id):
    section = get_object_or_404(WorkWithUs, id=section_id)

    if request.method == 'POST':
        section.title = request.POST.get('title')
        section.description = request.POST.get('description')
        section.contact_email = request.POST.get('contact_email')

        if 'image' in request.FILES:
            section.image = request.FILES['image']

        section.save()
        return redirect('manage_work_with_us')

    return render(request, 'edit_work_with_us.html', {'section': section})



def delete_work_with_us(request, section_id):
    section = get_object_or_404(WorkWithUs, id=section_id)
    section.delete()
    return redirect('manage_work_with_us')
