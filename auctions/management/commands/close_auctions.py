from django.core.management.base import BaseCommand
from django.utils import timezone
from auctions.models import Listing, Bid


class Command(BaseCommand):
    help = 'Close all active auctions (manual trigger, since the model has no end_time field)'

    def handle(self, *args, **kwargs):
        active_auctions = Listing.objects.filter(auction_active=True)
        closed_count = 0
        for auction in active_auctions:
            auction.auction_active = False
            # Assign winner as the highest bidder
            highest_bid = Bid.objects.filter(listing=auction).order_by('-value').first()
            if highest_bid:
                auction.winner = highest_bid.user
            auction.save()
            closed_count += 1
            self.stdout.write(self.style.SUCCESS(f"Auction '{auction.title}' closed successfully."))

        if closed_count == 0:
            self.stdout.write(self.style.WARNING("No active auctions found to close."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Total {closed_count} auction(s) closed."))