from .models import SiteConfiguration


def site_config(request):
    """Make site configuration available in all templates."""
    return {'site_config': SiteConfiguration.get_config()}
