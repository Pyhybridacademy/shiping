from django.contrib import admin
from .models import Shipment, PaymentProof, PDFStamp

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['tracking_number', 'sender_name', 'receiver_name', 'status', 'payment_status', 'current_location', 'date_created']
    list_filter = ['status', 'payment_status', 'require_payment', 'show_payment_info', 'payment_method', 'date_created']
    search_fields = ['tracking_number', 'sender_name', 'receiver_name', 'origin', 'destination']
    readonly_fields = ['total_cost', 'date_created', 'last_updated']
    
    fieldsets = (
        ('Tracking Information', {
            'fields': ('tracking_number', 'estimated_delivery')
        }),
        ('Sender Information', {
            'fields': ('sender_name', 'sender_address', 'sender_email', 'sender_phone')
        }),
        ('Receiver Information', {
            'fields': ('receiver_name', 'receiver_address', 'receiver_email', 'receiver_phone')
        }),
        ('Shipment Details', {
            'fields': ('origin', 'destination', 'current_location', 'parcel_description', 'parcel_weight')
        }),
        ('Status', {
            'fields': ('status', 'remarks')
        }),
        ('Parcel Image', {
            'fields': ('parcel_image',)
        }),
        ('Payment Settings', {
            'fields': ('require_payment', 'show_payment_info', 'payment_method', 'shipment_cost', 'clearance_cost', 'total_cost', 'crypto_wallet', 'payment_status')
        }),
        ('Timestamps', {
            'fields': ('date_created', 'last_updated'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        obj.total_cost = obj.shipment_cost + obj.clearance_cost
        super().save_model(request, obj, form, change)


@admin.register(PaymentProof)
class PaymentProofAdmin(admin.ModelAdmin):
    list_display = ['shipment', 'date_uploaded', 'is_verified']
    list_filter = ['is_verified', 'date_uploaded']
    search_fields = ['shipment__tracking_number']
    readonly_fields = ['date_uploaded']
    
    actions = ['mark_as_verified']
    
    def mark_as_verified(self, request, queryset):
        for proof in queryset:
            proof.is_verified = True
            proof.save()
            proof.shipment.payment_status = 'paid'
            proof.shipment.save()
        self.message_user(request, f"{queryset.count()} payment(s) verified successfully.")
    
    mark_as_verified.short_description = "Mark selected proofs as verified"


@admin.register(PDFStamp)
class PDFStampAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
