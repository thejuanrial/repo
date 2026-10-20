from django.forms import ModelForm
from django import forms

from .models import Listing, Category


class ListingForm(ModelForm):
    title = forms.CharField(label="Título del Producto", max_length=64, widget=forms.TextInput(attrs={'class':'border rounded p-2 w-full mt-2'}))
    category = forms.ChoiceField(label="Categoría", choices=[], widget=forms.Select(attrs={'class':'border rounded p-2 w-full mt-2'}))
    description = forms.CharField(label="Descripción", max_length=512, widget=forms.Textarea(attrs={'class':'border rounded p-2 w-full mt-2'}))
    starting_value = forms.DecimalField(label="Precio", max_digits=10, decimal_places=2, widget=forms.TextInput(attrs={'class':'border rounded p-2 w-full mt-2', 'type':"number", 'step':'0.01'}))
    image = forms.ImageField(label="Imagen del Producto", required=False, widget=forms.FileInput(attrs={'class':'border rounded p-2 w-full'}))
    # time = DateTimeField(input_formats=['%d/%m/%Y %H:%M'], widget=forms.DateTimeInput(attrs={'class':'border rounded p-2 w-full mt-2', 'type':'datetime-local'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load categories dynamically from the database
        categories = Category.objects.filter(is_active=True).values_list('name', flat=True)
        self.fields['category'].choices = [(cat, cat) for cat in categories]

    class Meta:
        model = Listing
        fields = ['title', 'category', 'description', 'starting_value', 'image']