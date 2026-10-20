from django import template
import datetime
from auctions.models import SiteConfiguration

register = template.Library()

@register.filter
def timedelta_format(value):
    hours, remainder = divmod(value.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return "{:02}:{:02}:{:02}".format(hours, minutes, seconds)

@register.filter
def format_usd(value):
    """Formatea monto en USD con separadores de miles y 2 decimales."""
    try:
        usd_val = float(value)
        return f"{usd_val:,.2f}"
    except (ValueError, TypeError):
        return "0.00"

@register.filter
def to_bs(value, custom_rate=None):
    """Convierte un monto en USD a Bolívares (Bs.) según la tasa configurada."""
    try:
        usd_val = float(value)
        if custom_rate:
            rate = float(custom_rate)
        else:
            config = SiteConfiguration.get_config()
            rate = float(config.usd_to_bs_rate)
        bs_val = usd_val * rate
        # Formato numérico estándar: miles con punto y decimales con coma
        formatted = f"{bs_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return formatted
    except (ValueError, TypeError):
        return "0,00"

@register.filter
def to_eur(value, custom_eur_rate=None):
    """Convierte un monto en USD a Euros (EUR) a través de la paridad en Bolívares."""
    try:
        usd_val = float(value)
        config = SiteConfiguration.get_config()
        usd_to_bs = float(config.usd_to_bs_rate)
        eur_to_bs = float(custom_eur_rate) if custom_eur_rate else float(config.eur_to_bs_rate)
        if eur_to_bs > 0:
            eur_val = (usd_val * usd_to_bs) / eur_to_bs
        else:
            eur_val = 0.0
        # Formato europeo estándar
        formatted = f"{eur_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return formatted
    except (ValueError, TypeError):
        return "0,00"
