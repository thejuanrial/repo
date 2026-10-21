from django.forms import ModelForm
from django import forms

from .models import Listing, Category


class ListingForm(ModelForm):
    title = forms.CharField(
        label="Título del Producto",
        max_length=64,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3.5 py-2.5 rounded-xl text-sm bg-neutral-50 dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-white placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Ej: iPhone 14 Pro Max 256GB'
        })
    )
    category = forms.ChoiceField(
        label="Categoría",
        choices=[],
        widget=forms.Select(attrs={
            'class': 'w-full px-3.5 py-2.5 rounded-xl text-sm bg-neutral-50 dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    description = forms.CharField(
        label="Descripción del Producto",
        max_length=512,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3.5 py-2.5 rounded-xl text-sm bg-neutral-50 dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-white placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 4,
            'placeholder': 'Detalles del estado, especificaciones, garantía y condiciones del producto...'
        })
    )
    starting_value = forms.DecimalField(
        label="Precio de Venta ($ USD)",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3.5 py-2.5 rounded-xl text-sm bg-neutral-50 dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-white placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00'
        })
    )
    image = forms.ImageField(
        label="Fotografía del Producto",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full text-xs text-neutral-600 dark:text-neutral-300 file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-neutral-900 file:text-white dark:file:bg-white dark:file:text-neutral-900 hover:file:opacity-90 cursor-pointer'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cargar categorías activas de la base de datos
        cats = list(Category.objects.filter(is_active=True).values_list('name', flat=True))
        if not cats:
            # Sembrar categorías iniciales si aún no existen para no bloquear la publicación
            default_categories = ['General', 'Tecnología', 'Moda', 'Hogar', 'Vehículos', 'Coleccionables']
            for cat_name in default_categories:
                Category.objects.get_or_create(name=cat_name, defaults={'description': f'Productos de {cat_name}'})
            cats = list(Category.objects.filter(is_active=True).values_list('name', flat=True))
        
        self.fields['category'].choices = [('', '-- Seleccione una Categoría --')] + [(c, c) for c in cats]

    class Meta:
        model = Listing
        fields = ['title', 'category', 'description', 'starting_value', 'image']