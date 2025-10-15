from django import forms
from .models import Shipment, PDFStamp

class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = [
            'tracking_number', 'sender_name', 'sender_address', 'sender_email', 'sender_phone',
            'receiver_name', 'receiver_address', 'receiver_email', 'receiver_phone',
            'origin', 'destination', 'current_location', 'status', 'remarks',
            'parcel_description', 'parcel_weight', 'parcel_image',
            'require_payment', 'show_payment_info', 'payment_method',
            'shipment_cost', 'clearance_cost', 'crypto_wallet', 'payment_status',
            'estimated_delivery'
        ]
        widgets = {
            'sender_address': forms.Textarea(attrs={'rows': 3}),
            'receiver_address': forms.Textarea(attrs={'rows': 3}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
            'parcel_description': forms.Textarea(attrs={'rows': 3}),
            'crypto_wallet': forms.Textarea(attrs={'rows': 2}),
            'estimated_delivery': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_tracking_number(self):
        tracking_number = self.cleaned_data['tracking_number']
        if self.instance.pk is None:  # Creating new shipment
            if Shipment.objects.filter(tracking_number=tracking_number).exists():
                raise forms.ValidationError('A shipment with this tracking number already exists.')
        return tracking_number

class PDFStampForm(forms.ModelForm):
    class Meta:
        model = PDFStamp
        fields = ['name', 'stamp_image', 'signature_image', 'is_active']


# Add this to your forms.py
from django import forms
from .models import SiteSettings

class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'site_name', 'company_name', 'contact_email', 'contact_phone',
            'company_address', 'website_url', 'facebook_url', 'twitter_url',
            'linkedin_url', 'pdf_header_title', 'pdf_footer_text', 'company_logo'
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-input'}),
            'company_name': forms.TextInput(attrs={'class': 'form-input'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-input'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-input'}),
            'company_address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'website_url': forms.URLInput(attrs={'class': 'form-input'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-input'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-input'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-input'}),
            'pdf_header_title': forms.TextInput(attrs={'class': 'form-input'}),
            'pdf_footer_text': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }