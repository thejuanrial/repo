from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.db.models import Count, Q
from django.http import  HttpResponseRedirect, Http404, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import User, Listing, Watch, Bid, Comment, Category, SiteConfiguration
from .forms import ListingForm
from .utils import *
from django.utils import timezone
# from datetime import timedelta
import random
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
import datetime, calendar
from django.template.loader import render_to_string


def index(request):
    config = SiteConfiguration.get_config()
    listings_qs = Listing.objects.filter(auction_active=True)

    # Ordenación dinámica según la configuración
    if config.listings_order == 'price_high':
        listings_list = list(listings_qs.order_by('-starting_value'))
    elif config.listings_order == 'price_low':
        listings_list = list(listings_qs.order_by('starting_value'))
    elif config.listings_order == 'most_bids':
        listings_qs = listings_qs.annotate(num_bids=Count('bids')).order_by('-num_bids')
        listings_list = list(listings_qs)
    else:  # 'recent' por defecto
        listings_qs = listings_qs.order_by('-created_at')
        listings_list = list(listings_qs)

    # Límite de productos a mostrar
    if config.listings_limit and config.listings_limit > 0:
        listings_list = listings_list[:config.listings_limit]

    categories = Category.objects.filter(is_active=True)

    return render(request, "auctions/index.html", {
        "listings": listings_list,
        "categories": categories,
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        
        # Check if authentication successful
        if user is not None:
            login(request, user)
            if user.is_superuser or user.is_staff:
                return HttpResponseRedirect(reverse("admin_view"))
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/authentication/login.html", {
                "message": "Nombre de usuario y/o contraseña inválidos."
            })
    else:
        return render(request, "auctions/authentication/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    config = SiteConfiguration.get_config()
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirmation = request.POST.get('confirmation')

        # Basic validation
        if not username or not password:
            return render(request, 'auctions/authentication/register.html', {'message': 'Por favor complete todos los campos obligatorios.'})

        if User.objects.filter(username=username).exists():
            return render(request, 'auctions/authentication/register.html', {'message': 'El nombre de usuario ya está registrado. Por favor elija otro.'})

        if password != confirmation:
            return render(request, 'auctions/authentication/register.html', {'message': 'Las contraseñas no coinciden.'})

        # Si la verificación OTP está deshabilitada (modo directo: solo registrar los datos y listo)
        if not config.enable_otp_verification:
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password)
            )
            login(request, user)
            messages.success(request, f"¡Bienvenido {username}! Su cuenta ha sido creada exitosamente.")
            return redirect('index')

        # Modo con OTP habilitado
        otp = random.randint(100000, 999999)
        request.session['otp'] = otp
        request.session['username'] = username
        request.session['email'] = email
        request.session['password'] = password
        
        html_content = render_to_string('auctions/mail/otp_mail.html', {'username': username, 'otp': otp})

        # Send OTP via email with error handling so external SMTP blocks don't crash the server
        sender_email = getattr(settings, 'EMAIL_HOST_USER', 'bidbazaar2024@gmail.com')
        try:
            send_mail(
                'Su código OTP de verificación de cuenta',
                'Use el siguiente código OTP para verificar su cuenta:',
                sender_email,
                [email],
                html_message=html_content,
                fail_silently=False,
            )
        except Exception:
            messages.warning(request, f"Su código de verificación temporal es: {otp}")

        # Redirect to OTP verification page
        return redirect('otp_verification')

    return render(request, 'auctions/authentication/register.html')

def otp_verification(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        if int(user_otp) == request.session.get('otp', 0):
            # Create user if OTP verification succeeds
            user = User.objects.create(
                username=request.session['username'],
                email=request.session['email'],
                password=make_password(request.session['password'])
            )
            user.save()
            # Set a session variable to indicate OTP verification success
            request.session['otp_verified'] = True
            return redirect('otp_success')  # Redirect to the success page
        else:
            return render(request, 'auctions/authentication/otp_authentication.html', {'error': 'Código OTP no válido'})
    return render(request, 'auctions/authentication/otp_authentication.html')



def otp_success(request):
    # Show success page, client-side redirect to login after 5 seconds
    return render(request, 'auctions/authentication/otp_success.html')

def forgot_password(request):
    config = SiteConfiguration.get_config()
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        
        # Check if user exists - handle DoesNotExist gracefully
        try:
            user = User.objects.get(username=username, email=email)
        except User.DoesNotExist:
            return render(request, 'auctions/authentication/forgot_password.html', {'message': 'Nombre de usuario y/o correo electrónico no válidos.'})
        
        # Si la verificación OTP está deshabilitada en la configuración, restablecer directamente
        if not config.enable_otp_verification:
            new_password = User.objects.make_random_password()
            user.set_password(new_password)
            user.save()
            return render(request, 'auctions/authentication/password_reset_successful.html', {
                'direct_reset': True,
                'temp_password': new_password,
                'username': username
            })

        # Generate OTP
        otp = random.randint(100000, 999999)
        
        request.session['otp'] = otp
        request.session['username'] = username
        request.session['email'] = email
        
        html_content = render_to_string('auctions/mail/forgot_password_mail.html', {'username': username, 'otp': otp})
        sender_email = getattr(settings, 'EMAIL_HOST_USER', 'bidbazaar2024@gmail.com')
        try:
            send_mail(
                'Su código OTP de verificación de cuenta',
                'Use el siguiente código OTP para verificar su cuenta:',
                sender_email,
                [email],
                html_message=html_content,
                fail_silently=False,
            )
        except Exception as e:
            return render(request, 'auctions/authentication/forgot_password.html', {'message': 'Error al enviar el correo. Por favor intente más tarde.'})
        
        return redirect('password_otp')
        
    return render(request, 'auctions/authentication/forgot_password.html')

def password_otp(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        
        # Check if OTP is provided
        if user_otp is None:
            return render(request, 'auctions/authentication/otp_authentication.html', {'error': 'El código OTP es obligatorio'})
        
        # Check if OTP is a valid integer
        try:
            otp = int(user_otp)
        except ValueError:
            return render(request, 'auctions/authentication/otp_authentication.html', {'error': 'Formato de OTP no válido'})
        
        # Check OTP against session OTP
        if otp == request.session.get('otp', 0):
            # Set a session variable to indicate OTP verification success
            request.session['otp_verified'] = True
            
            username = request.session['username']
            email = request.session['email']
            
            # Generate a new password
            password = User.objects.make_random_password()
            user = User.objects.get(username=username, email=email)
            user.set_password(password)
            user.save()
            
            html_content = render_to_string('auctions/mail/new_password_mail.html', {'username': username, 'password': password})
            
            sender_email = getattr(settings, 'EMAIL_HOST_USER', 'bidbazaar2024@gmail.com')
            try:
                send_mail(
                    'Su nueva contraseña temporal',
                    'Use su nueva contraseña temporal para iniciar sesión:',
                    sender_email,
                    [email],
                    html_message=html_content,
                    fail_silently=False,
                )
            except Exception:
                pass
            
            return redirect('password_reset_success')  # Redirect to the success page
        else:
            return render(request, 'auctions/authentication/otp_authentication.html', {'error': 'Código OTP no válido'})
        
    return render(request, 'auctions/authentication/otp_authentication.html')

def password_reset_success(request):
    return render(request, 'auctions/authentication/password_reset_successful.html')

@login_required(redirect_field_name='index')
def create_listing(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("index"))

    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = Listing(
                user=request.user,
                title=form.cleaned_data["title"],
                category=form.cleaned_data["category"],
                description=form.cleaned_data["description"],
                starting_value=form.cleaned_data["starting_value"],
                image=form.cleaned_data["image"]
            )
            listing.save()
            message = f"Su producto '{listing.title}' fue publicado exitosamente."
            messages.success(request, message)
            return redirect("index")
        else:
            return render(request, "auctions/createListing.html", {'form': form})

    return render(request, "auctions/createListing.html", {'form': ListingForm})

def view_listing(request, listing_id, error_message=False):
    listing = get_object_or_404(Listing, pk=listing_id)
    isActive = listing.auction_active

    user_authenticated = request.user.is_authenticated
    if user_authenticated:    
        watchExists = Watch.objects.filter(user=request.user, listing=listing_id).exists()
        isOwner = listing.user == request.user
    else:
        watchExists = False
        isOwner = False

    return render(request, "auctions/listingView.html", {
        'user_authenticated': user_authenticated,
        'listing': listing,
        'watch': watchExists,
        'current_price': listing.starting_value,
        'owner': isOwner,
        'active': isActive,
        'buyer': listing.winner,
        'comments': Comment.objects.filter(listing=listing).order_by('-created_at'),
        'error_message': error_message,
    })

@login_required(redirect_field_name='index')
def watch(request, listing_id):
    # Agregar o remover de lista de favoritos
    watch = Watch.objects.filter(user=request.user, listing_id=listing_id)
    if watch.exists():
        watch.delete()
        messages.info(request, "Producto removido de sus favoritos.")
    else:
        watch = Watch(user=request.user, listing_id=listing_id)
        watch.save()
        messages.success(request, "Producto añadido a sus favoritos.")
    
    return HttpResponseRedirect(reverse("listing", args=(listing_id,)))

@login_required(redirect_field_name='index')
def bid(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    if not listing.auction_active:
        messages.error(request, "Este producto ya no está disponible o ha sido vendido.")
        return redirect("listing", listing_id=listing.id)

    if listing.user == request.user:
        messages.error(request, "No puedes comprar un producto que tú mismo publicaste.")
        return redirect("listing", listing_id=listing.id)

    if request.method == "POST":
        # Ejecutar compra directa inmediata
        listing.auction_active = False
        listing.winner = request.user
        listing.save()

        # Registrar transacción de compra
        new_purchase = Bid(user=request.user, listing=listing, value=listing.starting_value)
        new_purchase.save()

        messages.success(request, f"¡Felicitaciones! Has comprado exitosamente '{listing.title}'.")
        return redirect("won_listings")

    return redirect("listing", listing_id=listing.id)

@login_required(redirect_field_name='index')
def close_auction(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    if listing.user != request.user and not (request.user.is_superuser or request.user.is_staff):
        return HttpResponseForbidden("No tiene permiso para modificar esta publicación.")

    if request.method == "POST":
        if listing.auction_active:
            listing.auction_active = False
            listing.save()
            messages.info(request, f"El producto '{listing.title}' ha sido marcado como no disponible.")
        else:
            listing.auction_active = True
            listing.save()
            messages.success(request, f"El producto '{listing.title}' ha sido reactivado como disponible.")

    return redirect("listing", listing_id=listing.id)

@login_required(redirect_field_name='index')
def comment(request, listing_id):
    comment_text = request.POST.get('comment', '').strip()
    if comment_text:
        comment = Comment(user=request.user, listing_id=listing_id, comment=comment_text)
        comment.save()
        messages.success(request, "Tu pregunta o comentario fue enviado exitosamente.")
    return HttpResponseRedirect(reverse("listing", args=(listing_id,)))

@login_required(redirect_field_name='index')
def your_listings(request):
    listings = Listing.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "auctions/profile/yourListings.html", {
        'listings': listings,
    })

@login_required(redirect_field_name='index')
def won_listings(request):
    listings = Listing.objects.filter(winner=request.user).order_by('-created_at')
    return render(request, "auctions/profile/wonListings.html", {
        'listings': listings,
    })

@login_required(redirect_field_name='index')
def watch_list(request):
    watched_listing_ids = Watch.objects.filter(user=request.user).values_list('listing_id', flat=True)
    listings = Listing.objects.filter(id__in=watched_listing_ids).order_by('-created_at')
    return render(request, "auctions/profile/watchList.html", {
        'listings': listings
    })

def categories(request):
    categories = Listing.objects.values_list('category', flat=True).distinct().order_by('category')
    return render(request, "auctions/categories.html", {
        'categories': list(categories)
    })

def category(request, category):
    active_listings = Listing.objects.filter(category=category, auction_active=True).order_by('-created_at')
    inactive_listings = Listing.objects.filter(category=category, auction_active=False).order_by('-created_at')
    
    return render(request, "auctions/category.html", {
        'category': category,
        'active_listings': active_listings,
        'inactive_listings': inactive_listings,
    })

@login_required
def view_profile(request):
    user = request.user
    return render(request, "auctions/profile/view_profile.html", {'user': user})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST['first_name']
        user.last_name = request.POST['last_name']
        user.email = request.POST['email']
        user.address = request.POST.get('address', '')  # Use get() method to handle cases where address is not provided

        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']

        user.save()
        return HttpResponseRedirect(reverse('view_profile'))
    return render(request, 'auctions/profile/edit_profile.html', {'user': request.user})


@login_required
def edit_password(request):
    if request.method == 'POST':
        user = request.user
        original_password = request.POST['original_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']
        
        # Check if the original password provided by the user is correct
        if authenticate(username=user.username, password=original_password):
            # Check if the new password and confirmation match
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                return HttpResponseRedirect(reverse('view_profile'))
            else:
                return render(request, 'auctions/profile/edit_password.html', {'error': 'Las nuevas contraseñas no coinciden'})
        else:
            return render(request, 'auctions/profile/edit_password.html', {'error': 'La contraseña actual no es correcta'})

    return render(request, 'auctions/profile/edit_password.html')

def is_superuser(user):
    # Permite acceso a administradores y personal de staff
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@user_passes_test(is_superuser, login_url='/forbidden/')
def admin_view(request):
    
    users = User.objects.all()
    listings = Listing.objects.all()
    total_users = User.objects.count()
    total_listings = Listing.objects.count()
    active_listings = Listing.objects.filter(auction_active=True).count()
    inactive_listings = Listing.objects.filter(auction_active=False).count()
            
    context = {
        'users': users,
        'listings': listings,
        'total_users': total_users,
        'total_listings': total_listings,
        'active_listings': active_listings,
        'inactive_listings': inactive_listings,
    }
    return render(request, 'auctions/admin/admin_dashboard.html', context)

@user_passes_test(is_superuser, login_url='/forbidden/')
def manage_users(request):
    users = User.objects.all()
    return render(request, 'auctions/admin/manage_users.html', {'users': users})

@user_passes_test(is_superuser, login_url='/forbidden/')
def manage_listings(request):
    listings = Listing.objects.all()
    query = request.GET.get('q')
    if query:
        # Filter listings based on title or description containing the search query
        listings = Listing.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))
    else:
        listings = Listing.objects.all()
    return render(request, 'auctions/admin/manage_listings.html', {'listings': listings})

@user_passes_test(is_superuser, login_url='/forbidden/')
def deactivate_listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    if request.method == 'POST':
        listing.auction_active = False
        listing.save()
        return redirect('manage_listings')

@user_passes_test(is_superuser, login_url='/forbidden/')
def delete_listing(request, listing_id):
    try:
        listing = Listing.objects.get(pk=listing_id)
    except Listing.DoesNotExist:
        raise Http404("La publicación no existe")
    
    if request.method == 'POST':
        listing.delete()
        return redirect('manage_listings')  # Redirect to admin dashboard or any other desired page
    # Handle GET request if needed

@user_passes_test(is_superuser, login_url='/forbidden/')
def reports(request):
    # User Reports
    # Data for user-wise listings
    user_wise_listings = (
        User.objects.annotate(total_listings=Count('listings'))
        .values('username', 'total_listings')
    )
    
    # Data for user registration reports
    today = timezone.now().date()
    last_seven_days = today - timezone.timedelta(days=6)
    user_registration_data = (
        User.objects.filter(date_joined__date__range=[last_seven_days, today])
        .values('date_joined__date')
        .annotate(total_registrations=Count('id'))
    )
    
    # Data for user registration reports (last 3 months)
    this_month = today.replace(day=1)
    last_three_months = [this_month - timezone.timedelta(days=i*30) for i in range(3)]
    
    user_registration_data_3_months = (
        User.objects.filter(date_joined__date__range=[last_three_months[2], today])
        .values('date_joined__month')
        .annotate(total_registrations=Count('id'))
    )
    
    # Listings created in the last 7 days
    today = timezone.now().date()
    last_week = today - timezone.timedelta(days=6)
    day_wise_listings = (
        Listing.objects.filter(created_at__date__range=[last_week, today])
        .values('created_at__date')
        .annotate(count=Count('id'))
    )
    
    # Listings created in the last 3 months
    this_month = today.replace(day=1)
    last_three_months = [this_month - timezone.timedelta(days=i*30) for i in range(3)]
    month_wise_listings = (
        Listing.objects.filter(created_at__date__range=[last_three_months[2], today])
        .values('created_at__month')
        .annotate(count=Count('id'))
    )
    month_names = [calendar.month_name[month['created_at__month']] for month in month_wise_listings]
    
    # Data for category reports
    category_data = (
        Listing.objects.values('category')
        .annotate(total_listings=Count('id'))
        .order_by('-total_listings')
    )
    
    #Bids Reports
    most_bid_item = Listing.objects.annotate(num_bids=Count('bids')).order_by('-num_bids').first()
    least_bid_item = Listing.objects.annotate(num_bids=Count('bids')).order_by('num_bids').first()
    # Query to get the top bidders
    top_bidders = User.objects.annotate(num_bids=Count('bids')).order_by('-num_bids')[:10]

    context = {
        'day_wise_listings': day_wise_listings,
        'month_wise_listings': month_wise_listings,
        'month_names': month_names,
        'user_wise_listings': user_wise_listings,
        'user_registration_data': user_registration_data,
        'user_registration_data_3_months': user_registration_data_3_months,
        'category_data': category_data,
        'most_bid_item': most_bid_item,
        'least_bid_item': least_bid_item,
        'top_bidders': top_bidders,
    }
    
    return render(request, 'auctions/admin/reports.html', context)

def forbidden_view(request):
    return render(request,"auctions/admin/forbidden.html")


# ============================================================
# CATEGORY MANAGEMENT
# ============================================================

@user_passes_test(is_superuser, login_url='/forbidden/')
def manage_categories(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name:
            Category.objects.get_or_create(name=name, defaults={'description': description})
            messages.success(request, f'Categoría "{name}" creada exitosamente.')
        return redirect('manage_categories')
    
    categories = Category.objects.all()
    return render(request, 'auctions/admin/manage_categories.html', {'categories': categories})

@user_passes_test(is_superuser, login_url='/forbidden/')
def edit_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    if request.method == 'POST':
        category.name = request.POST.get('name', category.name).strip()
        category.description = request.POST.get('description', '').strip()
        category.is_active = request.POST.get('is_active') == 'on'
        category.save()
        messages.success(request, f'Categoría "{category.name}" actualizada exitosamente.')
        return redirect('manage_categories')
    return render(request, 'auctions/admin/edit_category.html', {'category': category})

@user_passes_test(is_superuser, login_url='/forbidden/')
def delete_category(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=category_id)
        messages.success(request, f'Categoría "{category.name}" eliminada exitosamente.')
        category.delete()
    return redirect('manage_categories')


# ============================================================
# USER MANAGEMENT (ENHANCED)
# ============================================================

@user_passes_test(is_superuser, login_url='/forbidden/')
def admin_create_user(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        address = request.POST.get('address', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'

        if not username:
            return render(request, 'auctions/admin/admin_create_user.html', {
                'error': 'El nombre de usuario es obligatorio.',
                'form_data': request.POST
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'auctions/admin/admin_create_user.html', {
                'error': f'El usuario "{username}" ya existe.',
                'form_data': request.POST
            })

        if email and User.objects.filter(email=email).exists():
            return render(request, 'auctions/admin/admin_create_user.html', {
                'error': f'El correo electrónico "{email}" ya está registrado.',
                'form_data': request.POST
            })

        if not password or len(password) < 4:
            return render(request, 'auctions/admin/admin_create_user.html', {
                'error': 'La contraseña debe tener al menos 4 caracteres.',
                'form_data': request.POST
            })

        new_user = User(
            username=username,
            email=email,
            password=make_password(password),
            first_name=first_name,
            last_name=last_name,
            address=address,
            is_active=is_active,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
        if 'profile_picture' in request.FILES:
            new_user.profile_picture = request.FILES['profile_picture']

        new_user.save()
        messages.success(request, f'Usuario "{new_user.username}" creado exitosamente.')
        return redirect('manage_users')

    return render(request, 'auctions/admin/admin_create_user.html')

@user_passes_test(is_superuser, login_url='/forbidden/')
def admin_edit_user(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        user_obj.first_name = request.POST.get('first_name', '')
        user_obj.last_name = request.POST.get('last_name', '')
        user_obj.email = request.POST.get('email', '')
        user_obj.address = request.POST.get('address', '')
        user_obj.is_active = request.POST.get('is_active') == 'on'
        user_obj.is_staff = request.POST.get('is_staff') == 'on'
        user_obj.is_superuser = request.POST.get('is_superuser') == 'on'
        if 'profile_picture' in request.FILES:
            user_obj.profile_picture = request.FILES['profile_picture']
        user_obj.save()
        messages.success(request, f'Usuario "{user_obj.username}" actualizado exitosamente.')
        return redirect('manage_users')
    return render(request, 'auctions/admin/edit_user.html', {'user_obj': user_obj})

@user_passes_test(is_superuser, login_url='/forbidden/')
def admin_delete_user(request, user_id):
    if request.method == 'POST':
        user_obj = get_object_or_404(User, pk=user_id)
        if user_obj != request.user:
            messages.success(request, f'Usuario "{user_obj.username}" eliminado exitosamente.')
            user_obj.delete()
        else:
            messages.error(request, 'No puede eliminar su propia cuenta.')
    return redirect('manage_users')

@user_passes_test(is_superuser, login_url='/forbidden/')
def admin_toggle_user(request, user_id):
    if request.method == 'POST':
        user_obj = get_object_or_404(User, pk=user_id)
        if user_obj != request.user:
            user_obj.is_active = not user_obj.is_active
            user_obj.save()
            status = 'activado' if user_obj.is_active else 'desactivado'
            messages.success(request, f'Usuario "{user_obj.username}" {status} exitosamente.')
        else:
            messages.error(request, 'No puede desactivar su propia cuenta.')
    return redirect('manage_users')


# ============================================================
# LISTING MANAGEMENT (ENHANCED)
# ============================================================

@user_passes_test(is_superuser, login_url='/forbidden/')
def admin_create_listing(request):
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.user = request.user
            listing.save()
            messages.success(request, f'Producto "{listing.title}" publicado exitosamente.')
            return redirect('manage_listings')
        return render(request, 'auctions/admin/admin_create_listing.html', {'form': form})
    return render(request, 'auctions/admin/admin_create_listing.html', {'form': ListingForm()})

@user_passes_test(is_superuser, login_url='/forbidden/')
def admin_edit_listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    if request.method == 'POST':
        listing.title = request.POST.get('title', listing.title)
        listing.category = request.POST.get('category', listing.category)
        listing.description = request.POST.get('description', listing.description)
        listing.starting_value = request.POST.get('starting_value', listing.starting_value)
        listing.auction_active = request.POST.get('auction_active') == 'on'
        if 'image' in request.FILES:
            listing.image = request.FILES['image']
        listing.save()
        messages.success(request, f'Producto "{listing.title}" actualizado exitosamente.')
        return redirect('manage_listings')
    categories = Category.objects.filter(is_active=True)
    return render(request, 'auctions/admin/admin_edit_listing.html', {'listing': listing, 'categories': categories})

@user_passes_test(is_superuser, login_url='/forbidden/')
def reactivate_listing(request, listing_id):
    if request.method == 'POST':
        listing = get_object_or_404(Listing, pk=listing_id)
        listing.auction_active = True
        listing.winner = None
        listing.save()
        messages.success(request, f'Producto "{listing.title}" reactivado exitosamente.')
    return redirect('manage_listings')


# ============================================================
# COMMENTS MANAGEMENT
# ============================================================

@user_passes_test(is_superuser, login_url='/forbidden/')
def manage_comments(request):
    query = request.GET.get('q', '')
    comments_list = Comment.objects.select_related('user', 'listing').all().order_by('-created_at')
    if query:
        comments_list = comments_list.filter(
            Q(comment__icontains=query) | 
            Q(user__username__icontains=query) | 
            Q(listing__title__icontains=query)
        )
    return render(request, 'auctions/admin/manage_comments.html', {'comments_list': comments_list, 'query': query})

@user_passes_test(is_superuser, login_url='/forbidden/')
def admin_delete_comment(request, comment_id):
    if request.method == 'POST':
        comment_obj = get_object_or_404(Comment, pk=comment_id)
        comment_obj.delete()
        messages.success(request, 'Comentario eliminado exitosamente.')
    return redirect('manage_comments')


# ============================================================
# BIDS / PURCHASES MANAGEMENT
# ============================================================

@user_passes_test(is_superuser, login_url='/forbidden/')
def manage_bids(request):
    query = request.GET.get('q', '')
    bids_list = Bid.objects.select_related('user', 'listing').all().order_by('-created_at')
    if query:
        bids_list = bids_list.filter(
            Q(user__username__icontains=query) | 
            Q(listing__title__icontains=query)
        )
    return render(request, 'auctions/admin/manage_bids.html', {'bids_list': bids_list, 'query': query})

@user_passes_test(is_superuser, login_url='/forbidden/')
def admin_delete_bid(request, bid_id):
    if request.method == 'POST':
        bid_obj = get_object_or_404(Bid, pk=bid_id)
        bid_obj.delete()
        messages.success(request, 'Registro de compra eliminado exitosamente.')
    return redirect('manage_bids')


# ============================================================
# SITE CONFIGURATION
# ============================================================

@user_passes_test(is_superuser, login_url='/forbidden/')
def admin_site_config(request):
    config = SiteConfiguration.get_config()
    if request.method == 'POST':
        config.site_name = request.POST.get('site_name', config.site_name)
        config.site_tagline = request.POST.get('site_tagline', config.site_tagline)
        config.currency_symbol = request.POST.get('currency_symbol', config.currency_symbol)
        config.copyright_text = request.POST.get('copyright_text', config.copyright_text)
        config.contact_email = request.POST.get('contact_email', config.contact_email)

        # Multi-divisas (USD $, Bolívares Bs, Euros EUR)
        try:
            usd_rate = float(request.POST.get('usd_to_bs_rate', config.usd_to_bs_rate))
            if usd_rate > 0:
                config.usd_to_bs_rate = usd_rate
        except (ValueError, TypeError):
            pass

        try:
            eur_rate = float(request.POST.get('eur_to_bs_rate', config.eur_to_bs_rate))
            if eur_rate > 0:
                config.eur_to_bs_rate = eur_rate
        except (ValueError, TypeError):
            pass

        config.show_currency_conversion = request.POST.get('show_currency_conversion') == 'on'
        config.enable_otp_verification = request.POST.get('enable_otp_verification') == 'on'

        if 'site_logo' in request.FILES:
            config.site_logo = request.FILES['site_logo']
        config.save()
        messages.success(request, 'Configuración general y tasas de divisas actualizadas exitosamente.')
        return redirect('admin_site_config')
    return render(request, 'auctions/admin/site_config.html', {'config': config})


# ============================================================
# HOMEPAGE CUSTOMIZATION
# ============================================================

@user_passes_test(is_superuser, login_url='/forbidden/')
def admin_customize_home(request):
    config = SiteConfiguration.get_config()
    if request.method == 'POST':
        # Barra de Anuncio
        config.show_announcement = request.POST.get('show_announcement') == 'on'
        config.announcement_text = request.POST.get('announcement_text', config.announcement_text).strip()
        config.announcement_link = request.POST.get('announcement_link', config.announcement_link).strip()

        # Sección Hero
        config.show_hero = request.POST.get('show_hero') == 'on'
        config.hero_title = request.POST.get('hero_title', config.hero_title).strip()
        config.hero_subtitle = request.POST.get('hero_subtitle', config.hero_subtitle).strip()
        if 'hero_image' in request.FILES:
            config.hero_image = request.FILES['hero_image']
        config.hero_cta_text = request.POST.get('hero_cta_text', config.hero_cta_text).strip()
        config.hero_cta_url = request.POST.get('hero_cta_url', config.hero_cta_url).strip()
        config.hero_secondary_cta_text = request.POST.get('hero_secondary_cta_text', config.hero_secondary_cta_text).strip()
        config.hero_secondary_cta_url = request.POST.get('hero_secondary_cta_url', config.hero_secondary_cta_url).strip()

        # Sección de Beneficios / Características
        config.show_features = request.POST.get('show_features') == 'on'
        config.features_title = request.POST.get('features_title', config.features_title).strip()
        config.features_subtitle = request.POST.get('features_subtitle', config.features_subtitle).strip()
        config.feature_1_title = request.POST.get('feature_1_title', config.feature_1_title).strip()
        config.feature_1_desc = request.POST.get('feature_1_desc', config.feature_1_desc).strip()
        config.feature_2_title = request.POST.get('feature_2_title', config.feature_2_title).strip()
        config.feature_2_desc = request.POST.get('feature_2_desc', config.feature_2_desc).strip()
        config.feature_3_title = request.POST.get('feature_3_title', config.feature_3_title).strip()
        config.feature_3_desc = request.POST.get('feature_3_desc', config.feature_3_desc).strip()
        config.feature_4_title = request.POST.get('feature_4_title', config.feature_4_title).strip()
        config.feature_4_desc = request.POST.get('feature_4_desc', config.feature_4_desc).strip()

        # Sección de Categorías en Portada
        config.show_categories_preview = request.POST.get('show_categories_preview') == 'on'
        config.categories_section_title = request.POST.get('categories_section_title', config.categories_section_title).strip()

        # Sección de Productos
        config.show_listings = request.POST.get('show_listings') == 'on'
        config.listings_section_title = request.POST.get('listings_section_title', config.listings_section_title).strip()
        config.listings_section_subtitle = request.POST.get('listings_section_subtitle', config.listings_section_subtitle).strip()
        try:
            config.listings_limit = int(request.POST.get('listings_limit', 8))
        except (ValueError, TypeError):
            config.listings_limit = 8
        config.listings_order = request.POST.get('listings_order', 'recent')

        # Banner de Registro / CTA
        config.show_cta_banner = request.POST.get('show_cta_banner') == 'on'
        config.cta_banner_title = request.POST.get('cta_banner_title', config.cta_banner_title).strip()
        config.cta_banner_text = request.POST.get('cta_banner_text', config.cta_banner_text).strip()
        config.cta_banner_button_text = request.POST.get('cta_banner_button_text', config.cta_banner_button_text).strip()
        config.cta_banner_button_url = request.POST.get('cta_banner_button_url', config.cta_banner_button_url).strip()

        config.save()
        messages.success(request, 'Configuración de la portada guardada exitosamente.')
        return redirect('admin_customize_home')

    return render(request, 'auctions/admin/customize_home.html', {'config': config})