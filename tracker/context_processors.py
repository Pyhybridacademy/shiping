from .models import PaymentProof, PDFStamp, Shipment

from .models import SiteSettings

def site_settings(request):
    return {
        'site_settings': SiteSettings.load()
    }

def admin_context(request):
    if request.user.is_authenticated and request.user.is_staff:
        pending_payments_count = PaymentProof.objects.filter(is_verified=False).count()
        active_stamps_count = PDFStamp.objects.filter(is_active=True).count()
        total_shipments = Shipment.objects.count()
        
        return {
            'pending_payments_count': pending_payments_count,
            'active_stamps_count': active_stamps_count,
            'total_shipments': total_shipments,
        }
    return {}