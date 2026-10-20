from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    address = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='images/', blank=True, null=True)
    

class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class SiteConfiguration(models.Model):
    # --- Configuración General del Sitio ---
    site_name = models.CharField(max_length=128, default='BidBazaar')
    site_tagline = models.CharField(max_length=256, blank=True, default='Su plataforma de compra y venta en línea')
    currency_symbol = models.CharField(max_length=10, default='$')
    copyright_text = models.CharField(max_length=256, default='Todos los derechos reservados')
    contact_email = models.EmailField(blank=True, default='')
    site_logo = models.ImageField(upload_to='site/', blank=True, null=True)

    # --- Configuración de Divisas Multi-moneda ---
    # Moneda principal: USD ($)
    # Moneda secundaria: Bolívar (Bs)
    # Moneda terciaria: Euro (EUR)
    usd_to_bs_rate = models.DecimalField(max_digits=12, decimal_places=4, default=45.0000)
    eur_to_bs_rate = models.DecimalField(max_digits=12, decimal_places=4, default=48.5000)
    show_currency_conversion = models.BooleanField(default=True)
    enable_otp_verification = models.BooleanField(default=False)

    def to_bs(self, usd_amount):
        try:
            val = float(usd_amount) * float(self.usd_to_bs_rate)
            return f"{val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except (ValueError, TypeError):
            return "0,00"

    def to_eur(self, usd_amount):
        try:
            if float(self.eur_to_bs_rate) > 0:
                val = (float(usd_amount) * float(self.usd_to_bs_rate)) / float(self.eur_to_bs_rate)
                return f"{val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            return "0,00"
        except (ValueError, TypeError):
            return "0,00"

    def eur_to_usd_rate(self):
        try:
            if float(self.usd_to_bs_rate) > 0:
                return round(float(self.eur_to_bs_rate) / float(self.usd_to_bs_rate), 4)
            return 1.0
        except (ValueError, TypeError):
            return 1.0

    # --- Barra de Anuncio Superior ---
    show_announcement = models.BooleanField(default=False)
    announcement_text = models.CharField(max_length=256, blank=True, default="¡Bienvenido a nuestra plataforma de compra y venta!")
    announcement_link = models.CharField(max_length=256, blank=True, default="")

    # --- Sección Hero (Encabezado Principal) ---
    show_hero = models.BooleanField(default=True)
    hero_title = models.CharField(max_length=256, default='Bienvenido a BidBazaar')
    hero_subtitle = models.TextField(blank=True, default='Descubra artículos únicos, productos de calidad y grandes oportunidades cada día.')
    hero_image = models.ImageField(upload_to='hero/', blank=True, null=True)
    hero_cta_text = models.CharField(max_length=64, default='Explorar Productos')
    hero_cta_url = models.CharField(max_length=128, default='#productos')
    hero_secondary_cta_text = models.CharField(max_length=64, default='Vender Producto')
    hero_secondary_cta_url = models.CharField(max_length=128, default='/create_listing/')

    # --- Sección de Tarjetas Informativas / Beneficios ---
    show_features = models.BooleanField(default=True)
    features_title = models.CharField(max_length=128, default='¿Por qué elegirnos?')
    features_subtitle = models.CharField(max_length=256, default='La plataforma más confiable para comprar y vender')
    feature_1_title = models.CharField(max_length=128, default='Compra Directa')
    feature_1_desc = models.TextField(default='Navegue por una selección curada de productos a precios fijos y transparentes.')
    feature_2_title = models.CharField(max_length=128, default='Gran Variedad')
    feature_2_desc = models.TextField(default='Descubra una amplia variedad de artículos desde tecnología hasta coleccionables y más.')
    feature_3_title = models.CharField(max_length=128, default='Compra Segura')
    feature_3_desc = models.TextField(default='Priorizamos la transparencia, la integridad y la seguridad en cada compra y venta.')
    feature_4_title = models.CharField(max_length=128, default='Venda sus Productos')
    feature_4_desc = models.TextField(default='Convierta sus artículos en dinero vendiendo con nosotros. Publique sus productos y cierre ventas con facilidad.')

    # --- Sección de Categorías en Portada ---
    show_categories_preview = models.BooleanField(default=True)
    categories_section_title = models.CharField(max_length=128, default='Explorar por Categoría')

    # --- Sección de Productos en Portada ---
    show_listings = models.BooleanField(default=True)
    listings_section_title = models.CharField(max_length=128, default='Productos Destacados')
    listings_section_subtitle = models.CharField(max_length=256, blank=True, default='Artículos disponibles para compra directa')
    listings_limit = models.IntegerField(default=8)
    listings_order = models.CharField(max_length=32, default='recent')

    # --- Banner de Llamado a la Acción (CTA Inferior) ---
    show_cta_banner = models.BooleanField(default=True)
    cta_banner_title = models.CharField(max_length=256, default='¿Listo para comenzar a comprar o vender?')
    cta_banner_text = models.TextField(default='Cree su cuenta gratuita en segundos y comience a comprar y vender con total comodidad.')
    cta_banner_button_text = models.CharField(max_length=64, default='Registrarse Ahora')
    cta_banner_button_url = models.CharField(max_length=128, default='/register/')

    class Meta:
        verbose_name = 'Configuración del Sitio'
        verbose_name_plural = 'Configuración del Sitio'
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Singleton pattern - always use pk=1
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_config(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config


class Listing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    title = models.CharField(max_length=64)
    category = models.CharField(max_length=64)
    description = models.CharField(max_length=512)
    starting_value = models.DecimalField(max_digits=10, decimal_places=2)
    auction_active = models.BooleanField(default=True)
    winner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="won", null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to="images/")
    created_at = models.DateTimeField(default=timezone.now)
    
    @property
    def price(self):
        return self.starting_value

    @property
    def is_available(self):
        return self.auction_active

    @property
    def buyer(self):
        return self.winner

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.created_at.tzinfo:
            self.created_at = timezone.make_aware(self.created_at)
        super().save(*args, **kwargs)
    

class Watch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchList")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="watchers")
    def __str__(self):
        return f"{self.user} tiene en favoritos a {self.listing}"

class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    value = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user} compró {self.listing} por {self.value}"
    
    def save(self, *args, **kwargs):
        if not self.created_at.tzinfo:
            self.created_at = timezone.make_aware(self.created_at)
        super().save(*args, **kwargs)

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    comment = models.CharField(max_length=512)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user}: {self.comment[:50]}"
    
    def save(self, *args, **kwargs):
        if not self.created_at.tzinfo:
            self.created_at = timezone.make_aware(self.created_at)
        super().save(*args, **kwargs)