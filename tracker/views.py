from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Shipment, PaymentProof, PDFStamp, SiteSettings
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, cm
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from io import BytesIO
import os

def home(request):
    site_settings = SiteSettings.load()
    context = {
        'site_settings': site_settings
    }
    return render(request, 'tracker/home.html', context)

def track_shipment(request):
    tracking_number = request.GET.get('tracking_number')
    shipment = None
    proof_uploaded = None
    
    if tracking_number:
        shipment = Shipment.objects.filter(tracking_number=tracking_number).first()
        if shipment:
            proof_uploaded = PaymentProof.objects.filter(shipment=shipment).first()
    
    context = {
        'shipment': shipment,
        'proof_uploaded': proof_uploaded,
        'tracking_number': tracking_number
    }
    return render(request, 'tracker/result.html', context)

def upload_payment_proof(request, tracking_number):
    shipment = get_object_or_404(Shipment, tracking_number=tracking_number)
    
    if request.method == 'POST' and request.FILES.get('proof'):
        PaymentProof.objects.update_or_create(
            shipment=shipment,
            defaults={
                'image': request.FILES['proof'],
                'is_verified': False
            }
        )
        shipment.payment_status = 'awaiting_payment'
        shipment.save()
        return redirect(f'/track/?tracking_number={tracking_number}')
    
    return render(request, 'tracker/upload_payment.html', {'shipment': shipment})

def print_preview(request, tracking_number):
    """PDF Preview Page"""
    shipment = get_object_or_404(Shipment, tracking_number=tracking_number)
    return render(request, 'tracker/print_preview.html', {'shipment': shipment})

def print_tracking_pdf(request, tracking_number):
    """Generate PDF for shipment tracking details with stamps and signatures"""
    shipment = get_object_or_404(Shipment, tracking_number=tracking_number)
    site_settings = SiteSettings.load()  # Get the site settings
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center aligned
        textColor=colors.HexColor('#1E40AF')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=12,
        textColor=colors.HexColor('#1E40AF')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    bold_style = ParagraphStyle(
        'CustomBold',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Add Company Logo and Header - NOW USING DYNAMIC SETTINGS
    try:
        if site_settings.company_logo:
            logo = Image(site_settings.company_logo.path, width=2*inch, height=1*inch)
            story.append(logo)
            story.append(Spacer(1, 10))
    except:
        pass
    
    # Use dynamic company name instead of hardcoded "GLOBALTRACK PRO"
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2563EB'),
        alignment=1,
        spaceAfter=10
    )
    story.append(Paragraph(site_settings.company_name.upper(), header_style))
    story.append(Paragraph("Professional Shipping & Logistics", normal_style))
    story.append(Spacer(1, 20))
    
    # Title - USING DYNAMIC PDF HEADER TITLE
    story.append(Paragraph(site_settings.pdf_header_title, title_style))
    story.append(Spacer(1, 20))
    
    # Tracking Info Table - Fixed to remove HTML tags
    tracking_data = [
        ['Tracking Number:', shipment.tracking_number, 'Status:', shipment.get_status_display()],
        ['Date Created:', shipment.date_created.strftime('%Y-%m-%d %H:%M'), 'Last Updated:', shipment.last_updated.strftime('%Y-%m-%d %H:%M')],
    ]
    
    if shipment.estimated_delivery:
        tracking_data.append(['Estimated Delivery:', shipment.estimated_delivery.strftime('%Y-%m-%d'), '', ''])
    
    tracking_table = Table(tracking_data, colWidths=[2*inch, 2.5*inch, 1.5*inch, 2*inch])
    tracking_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(tracking_table)
    story.append(Spacer(1, 20))
    
    # Sender and Receiver Information - Fixed to remove HTML tags
    story.append(Paragraph("SENDER & RECEIVER INFORMATION", heading_style))
    
    contact_data = [
        ['SENDER INFORMATION', 'RECEIVER INFORMATION'],
        [f"Name: {shipment.sender_name}", f"Name: {shipment.receiver_name}"],
        [f"Address: {shipment.sender_address}", f"Address: {shipment.receiver_address}"],
        [f"Email: {shipment.sender_email}", f"Email: {shipment.receiver_email}"],
        [f"Phone: {shipment.sender_phone}", f"Phone: {shipment.receiver_phone}"],
    ]
    
    contact_table = Table(contact_data, colWidths=[3.5*inch, 3.5*inch])
    contact_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1E40AF')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 11),
        ('BACKGROUND', (0, 1), (1, -1), colors.white),
        ('FONTNAME', (0, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (1, -1), 9),
        ('GRID', (0, 0), (1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (1, -1), 'TOP'),
    ]))
    story.append(contact_table)
    story.append(Spacer(1, 20))
    
    # Shipment Details
    story.append(Paragraph("SHIPMENT DETAILS", heading_style))
    
    shipment_data = [
        ['Origin:', shipment.origin, 'Destination:', shipment.destination],
        ['Current Location:', shipment.current_location, 'Parcel Weight:', f"{shipment.parcel_weight} kg"],
    ]
    
    if shipment.parcel_description:
        shipment_data.append(['Description:', shipment.parcel_description, '', ''])
    
    shipment_table = Table(shipment_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2*inch])
    shipment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(shipment_table)
    story.append(Spacer(1, 15))
    
    # Payment Information (if required and shown)
    if shipment.require_payment and shipment.show_payment_info:
        story.append(Paragraph("PAYMENT INFORMATION", heading_style))
        
        payment_data = [
            ['Payment Method:', shipment.get_payment_method_display().upper(), 'Payment Status:', shipment.get_payment_status_display()],
            ['Shipment Cost:', f"${shipment.shipment_cost}", 'Clearance Cost:', f"${shipment.clearance_cost}"],
            ['Total Amount:', f"${shipment.total_cost}", 'Wallet Address:', shipment.crypto_wallet],
        ]
        
        payment_table = Table(payment_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2.5*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (2, 2), (2, 2), 'Helvetica-Bold'),  # Make Total Amount bold
        ]))
        story.append(payment_table)
        story.append(Spacer(1, 15))
    
    # Remarks - Fixed to remove HTML tags
    if shipment.remarks:
        story.append(Paragraph("REMARKS", heading_style))
        # Clean the remarks text by removing any HTML tags
        clean_remarks = shipment.remarks.replace('<b>', '').replace('</b>', '')
        story.append(Paragraph(clean_remarks, normal_style))
        story.append(Spacer(1, 20))
    
    # Add parcel image if exists
    if shipment.parcel_image:
        story.append(Paragraph("PARCEL IMAGE", heading_style))
        try:
            parcel_img = Image(shipment.parcel_image.path, width=4*inch, height=3*inch)
            story.append(parcel_img)
            story.append(Spacer(1, 15))
        except:
            pass
    
    # Add stamps and signatures
    active_stamp = PDFStamp.objects.filter(is_active=True).first()
    if active_stamp:
        story.append(Spacer(1, 30))
        
        # Create stamp table
        stamp_elements = []
        
        # Add stamp image if exists
        if active_stamp.stamp_image:
            try:
                stamp_img = Image(active_stamp.stamp_image.path, width=1.5*inch, height=1.5*inch)
                stamp_elements.append(stamp_img)
            except:
                stamp_elements.append(Paragraph("OFFICIAL STAMP", bold_style))
        else:
            stamp_elements.append(Paragraph("OFFICIAL STAMP", bold_style))
        
        # Add signature image if exists
        if active_stamp.signature_image:
            try:
                signature_img = Image(active_stamp.signature_image.path, width=2*inch, height=0.5*inch)
                stamp_elements.append(signature_img)
            except:
                stamp_elements.append(Paragraph("AUTHORIZED SIGNATURE", bold_style))
        else:
            stamp_elements.append(Paragraph("AUTHORIZED SIGNATURE", bold_style))
        
        # Create a table for stamps and signatures
        stamp_data = [
            ['', ''],
            stamp_elements,
            ['Official Stamp', 'Authorized Signature']
        ]
        
        stamp_table = Table(stamp_data, colWidths=[3*inch, 3*inch])
        stamp_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 2), (-1, 2), 10),
            ('VALIGN', (0, 1), (-1, 1), 'MIDDLE'),
        ]))
        story.append(stamp_table)
    
    # Footer with DYNAMIC company information
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray,
        alignment=1
    )
    
    company_info_style = ParagraphStyle(
        'CompanyInfo',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        alignment=1,
        spaceAfter=3
    )
    
    # USING DYNAMIC SITE SETTINGS FOR FOOTER
    story.append(Paragraph(site_settings.company_name, company_info_style))
    story.append(Paragraph(f"Email: {site_settings.contact_email} | Phone: {site_settings.contact_phone}", footer_style))
    story.append(Paragraph(site_settings.website_url, footer_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(site_settings.pdf_footer_text, footer_style))
    story.append(Paragraph("Thank you for using our services!", footer_style))
    
    doc.build(story)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="tracking_{tracking_number}.pdf"'
    return response

@login_required
def admin_dashboard(request):
    shipments = Shipment.objects.all().order_by('-date_created')
    pending_proofs = PaymentProof.objects.filter(is_verified=False)
    
    context = {
        'shipments': shipments,
        'pending_proofs': pending_proofs,
    }
    return render(request, 'tracker/admin_dashboard.html', context)

@login_required
def verify_payment(request, proof_id):
    proof = get_object_or_404(PaymentProof, id=proof_id)
    proof.is_verified = True
    proof.save()
    
    shipment = proof.shipment
    shipment.payment_status = 'paid'
    shipment.save()
    
    return redirect('admin_dashboard')


from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
import json
from .models import Shipment, PaymentProof, PDFStamp
from .forms import ShipmentForm, PDFStampForm, SiteSettingsForm

def admin_required(function=None):
    """Decorator for views that require admin access"""
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url='/admin/login/'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

@login_required
@admin_required
def admin_dashboard(request):
    """Admin dashboard with overview statistics"""
    # Calculate statistics
    total_shipments = Shipment.objects.count()
    pending_shipments = Shipment.objects.filter(status='pending').count()
    delivered_shipments = Shipment.objects.filter(status='delivered').count()
    pending_payments = PaymentProof.objects.filter(is_verified=False).count()
    
    # Revenue calculations
    total_revenue = Shipment.objects.filter(payment_status='paid').aggregate(
        total=Sum('total_cost')
    )['total'] or 0
    
    # Recent shipments
    recent_shipments = Shipment.objects.all().order_by('-date_created')[:5]
    
    # Shipments by status
    status_stats = Shipment.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Weekly stats
    week_ago = timezone.now() - timedelta(days=7)
    weekly_shipments = Shipment.objects.filter(date_created__gte=week_ago).count()
    weekly_revenue = Shipment.objects.filter(
        date_created__gte=week_ago, 
        payment_status='paid'
    ).aggregate(total=Sum('total_cost'))['total'] or 0
    
    context = {
        'total_shipments': total_shipments,
        'pending_shipments': pending_shipments,
        'delivered_shipments': delivered_shipments,
        'pending_payments': pending_payments,
        'total_revenue': total_revenue,
        'weekly_shipments': weekly_shipments,
        'weekly_revenue': weekly_revenue,
        'recent_shipments': recent_shipments,
        'status_stats': status_stats,
    }
    return render(request, 'tracker/admin/dashboard.html', context)

@login_required
@admin_required
def admin_shipments(request):
    """Manage all shipments"""
    shipments = Shipment.objects.all().order_by('-date_created')
    
    # Filtering
    status_filter = request.GET.get('status', '')
    payment_filter = request.GET.get('payment_status', '')
    
    if status_filter:
        shipments = shipments.filter(status=status_filter)
    if payment_filter:
        shipments = shipments.filter(payment_status=payment_filter)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        shipments = shipments.filter(
            Q(tracking_number__icontains=search_query) |
            Q(sender_name__icontains=search_query) |
            Q(receiver_name__icontains=search_query)
        )
    
    context = {
        'shipments': shipments,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'search_query': search_query,
    }
    return render(request, 'tracker/admin/shipments.html', context)

@login_required
@admin_required
def admin_create_shipment(request):
    """Create new shipment"""
    if request.method == 'POST':
        form = ShipmentForm(request.POST, request.FILES)
        if form.is_valid():
            shipment = form.save()
            messages.success(request, f'Shipment {shipment.tracking_number} created successfully!')
            return redirect('admin_shipments')
    else:
        form = ShipmentForm()
    
    context = {'form': form}
    return render(request, 'tracker/admin/shipment_form.html', context)

@login_required
@admin_required
def admin_edit_shipment(request, shipment_id):
    """Edit existing shipment"""
    shipment = get_object_or_404(Shipment, id=shipment_id)
    
    if request.method == 'POST':
        form = ShipmentForm(request.POST, request.FILES, instance=shipment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Shipment {shipment.tracking_number} updated successfully!')
            return redirect('admin_shipments')
    else:
        form = ShipmentForm(instance=shipment)
    
    context = {'form': form, 'shipment': shipment}
    return render(request, 'tracker/admin/shipment_form.html', context)

@login_required
@admin_required
def admin_delete_shipment(request, shipment_id):
    """Delete shipment"""
    shipment = get_object_or_404(Shipment, id=shipment_id)
    
    if request.method == 'POST':
        tracking_number = shipment.tracking_number
        shipment.delete()
        messages.success(request, f'Shipment {tracking_number} deleted successfully!')
        return redirect('admin_shipments')
    
    context = {'shipment': shipment}
    return render(request, 'tracker/admin/delete_shipment.html', context)

@login_required
@admin_required
def admin_payments(request):
    """Manage payment proofs"""
    pending_proofs = PaymentProof.objects.filter(is_verified=False).order_by('-date_uploaded')
    verified_proofs = PaymentProof.objects.filter(is_verified=True).order_by('-date_uploaded')[:10]
    
    context = {
        'pending_proofs': pending_proofs,
        'verified_proofs': verified_proofs,
    }
    return render(request, 'tracker/admin/payments.html', context)

@login_required
@admin_required
def verify_payment(request, proof_id):
    """Verify payment proof"""
    proof = get_object_or_404(PaymentProof, id=proof_id)
    proof.is_verified = True
    proof.save()
    
    shipment = proof.shipment
    shipment.payment_status = 'paid'
    shipment.save()
    
    messages.success(request, f'Payment for {shipment.tracking_number} verified successfully!')
    return redirect('admin_payments')

@login_required
@admin_required
def reject_payment(request, proof_id):
    """Reject payment proof"""
    proof = get_object_or_404(PaymentProof, id=proof_id)
    tracking_number = proof.shipment.tracking_number
    proof.delete()
    
    messages.success(request, f'Payment proof for {tracking_number} rejected and removed!')
    return redirect('admin_payments')

@login_required
@admin_required
def admin_stats(request):
    """Detailed statistics and analytics"""
    # Time-based statistics
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Shipment statistics
    total_shipments = Shipment.objects.count()
    today_shipments = Shipment.objects.filter(date_created__date=today).count()
    weekly_shipments = Shipment.objects.filter(date_created__date__gte=week_ago).count()
    monthly_shipments = Shipment.objects.filter(date_created__date__gte=month_ago).count()
    
    # Revenue statistics
    total_revenue = Shipment.objects.filter(payment_status='paid').aggregate(
        total=Sum('total_cost')
    )['total'] or 0
    
    weekly_revenue = Shipment.objects.filter(
        date_created__date__gte=week_ago,
        payment_status='paid'
    ).aggregate(total=Sum('total_cost'))['total'] or 0
    
    monthly_revenue = Shipment.objects.filter(
        date_created__date__gte=month_ago,
        payment_status='paid'
    ).aggregate(total=Sum('total_cost'))['total'] or 0
    
    # Status distribution
    status_distribution = Shipment.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Payment status distribution
    payment_distribution = Shipment.objects.values('payment_status').annotate(
        count=Count('id')
    ).order_by('payment_status')
    
    # Recent activity
    recent_activity = Shipment.objects.all().order_by('-last_updated')[:10]
    
    context = {
        'total_shipments': total_shipments,
        'today_shipments': today_shipments,
        'weekly_shipments': weekly_shipments,
        'monthly_shipments': monthly_shipments,
        'total_revenue': total_revenue,
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue,
        'status_distribution': status_distribution,
        'payment_distribution': payment_distribution,
        'recent_activity': recent_activity,
    }
    return render(request, 'tracker/admin/stats.html', context)

@login_required
@admin_required
def admin_settings(request):
    """Admin settings and configuration"""
    stamps = PDFStamp.objects.all()
    editing_stamp = None
    
    # Get or create site settings
    site_settings = SiteSettings.load()
    site_settings_form = SiteSettingsForm(instance=site_settings)
    
    if request.method == 'POST':
        # Handle stamp creation
        if 'create_stamp' in request.POST:
            form = PDFStampForm(request.POST, request.FILES)
            if form.is_valid():
                if form.cleaned_data.get('is_active'):
                    PDFStamp.objects.filter(is_active=True).update(is_active=False)
                form.save()
                messages.success(request, 'PDF stamp created successfully!')
                return redirect('admin_settings')
        
        # Handle stamp update
        elif 'update_stamp' in request.POST:
            stamp_id = request.POST.get('stamp_id')
            stamp = get_object_or_404(PDFStamp, id=stamp_id)
            form = PDFStampForm(request.POST, request.FILES, instance=stamp)
            if form.is_valid():
                if form.cleaned_data.get('is_active'):
                    PDFStamp.objects.filter(is_active=True).exclude(id=stamp_id).update(is_active=False)
                form.save()
                messages.success(request, 'PDF stamp updated successfully!')
                return redirect('admin_settings')
        
        # Handle stamp activation
        elif 'activate_stamp' in request.POST:
            stamp_id = request.POST.get('stamp_id')
            stamp = get_object_or_404(PDFStamp, id=stamp_id)
            PDFStamp.objects.filter(is_active=True).update(is_active=False)
            stamp.is_active = True
            stamp.save()
            messages.success(request, f'Stamp "{stamp.name}" activated successfully!')
            return redirect('admin_settings')
        
        # Handle stamp deletion
        elif 'delete_stamp' in request.POST:
            stamp_id = request.POST.get('stamp_id')
            stamp = get_object_or_404(PDFStamp, id=stamp_id)
            stamp_name = stamp.name
            stamp.delete()
            messages.success(request, f'Stamp "{stamp_name}" deleted successfully!')
            return redirect('admin_settings')
        
        # Handle site settings update
        elif 'update_site_settings' in request.POST:
            site_settings_form = SiteSettingsForm(request.POST, request.FILES, instance=site_settings)
            if site_settings_form.is_valid():
                site_settings_form.save()
                messages.success(request, 'Site settings updated successfully!')
                return redirect('admin_settings')
    
    # Handle edit request for stamps
    if 'edit_stamp' in request.GET:
        stamp_id = request.GET.get('stamp_id')
        try:
            editing_stamp = PDFStamp.objects.get(id=stamp_id)
        except PDFStamp.DoesNotExist:
            messages.error(request, 'Stamp not found.')
    
    form = PDFStampForm()
    
    # Get stats for the sidebar
    total_shipments = Shipment.objects.count()
    pending_payments_count = PaymentProof.objects.filter(is_verified=False).count()
    active_stamps_count = PDFStamp.objects.filter(is_active=True).count()
    
    context = {
        'stamps': stamps,
        'form': form,
        'editing_stamp': editing_stamp,
        'site_settings_form': site_settings_form,
        'site_settings': site_settings,
        'total_shipments': total_shipments,
        'pending_payments_count': pending_payments_count,
        'active_stamps_count': active_stamps_count,
    }
    return render(request, 'tracker/admin/settings.html', context)