from django import template
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def split(value, delimiter=None):
    """Split a string into a list using the given delimiter"""
    if delimiter is None:
        delimiter = ' '
    return value.split(delimiter)

@register.filter
def get_item(lst, index):
    """Get item from list by index"""
    try:
        return lst[index]
    except (IndexError, TypeError):
        return ''

@register.filter
def get_status_percentage(status):
    """Calculate progress percentage based on status"""
    status_order = ['pending', 'picked', 'on_way', 'delivered']
    try:
        progress = ((status_order.index(status) + 1) / len(status_order)) * 100
        return int(progress)
    except ValueError:
        # For on_hold and custom_hold, return appropriate progress
        if status == 'on_hold':
            return 25
        elif status == 'custom_hold':
            return 25
        return 0

@register.filter
def days_since(date):
    """Calculate days since given date"""
    if not date:
        return 0
    if isinstance(date, str):
        date = datetime.fromisoformat(date.replace('Z', '+00:00'))
    delta = datetime.now().date() - date.date()
    return delta.days

@register.filter
def format_currency(value):
    """Format value as currency"""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return f"${0:.2f}"

@register.filter
def truncate_words(value, num_words):
    """Truncate string to specified number of words"""
    if not value:
        return ""
    words = value.split()
    if len(words) > num_words:
        return ' '.join(words[:num_words]) + '...'
    return value

@register.simple_tag
def get_timeline_data(shipment):
    """Generate timeline data for shipment with all status options"""
    timeline_steps = [
        {
            'key': 'pending',
            'name': 'Order Processing',
            'description': 'Order received and being processed',
            'icon': 'receipt',
            'active': shipment.status == 'pending',
            'completed': shipment.status in ['picked', 'on_hold', 'on_way', 'custom_hold', 'delivered']
        },
        {
            'key': 'picked',
            'name': 'Picked Up',
            'description': 'Package collected by courier',
            'icon': 'shopping-bag',
            'active': shipment.status == 'picked',
            'completed': shipment.status in ['on_hold', 'on_way', 'custom_hold', 'delivered']
        },
        {
            'key': 'on_way',
            'name': 'In Transit',
            'description': 'Shipment is on the way to destination',
            'icon': 'truck',
            'active': shipment.status == 'on_way',
            'completed': shipment.status in ['custom_hold', 'delivered']
        },
        {
            'key': 'delivered',
            'name': 'Delivered',
            'description': 'Package delivered successfully',
            'icon': 'check-circle',
            'active': shipment.status == 'delivered',
            'completed': shipment.status == 'delivered'
        }
    ]
    
    # Add hold statuses as special cases
    if shipment.status in ['on_hold', 'custom_hold']:
        for step in timeline_steps:
            if step['key'] == 'picked':
                step['active'] = False
                step['completed'] = True
                break
    
    return timeline_steps

@register.simple_tag
def get_simulated_updates(shipment):
    """Generate simulated real-time updates"""
    updates = []
    
    # Base updates for all statuses
    updates.append({
        'time': 'Just now',
        'location': shipment.current_location,
        'message': 'Package scanned at current facility',
        'icon': 'map-marker-alt'
    })
    
    # Status-specific updates
    if shipment.status in ['picked', 'on_hold', 'on_way', 'custom_hold', 'delivered']:
        updates.append({
            'time': '2 hours ago',
            'location': 'Distribution Center',
            'message': 'Departed from sorting facility',
            'icon': 'truck'
        })
    
    if shipment.status in ['on_way', 'custom_hold', 'delivered']:
        updates.append({
            'time': '5 hours ago',
            'location': 'Main Hub',
            'message': 'Arrived at regional hub',
            'icon': 'warehouse'
        })
    
    if shipment.status == 'on_hold':
        updates.append({
            'time': '1 hour ago',
            'location': 'Processing Center',
            'message': 'Shipment placed on hold for review',
            'icon': 'pause-circle'
        })
    
    if shipment.status == 'custom_hold':
        updates.append({
            'time': '1 hour ago',
            'location': 'Customs Office',
            'message': 'Custom clearance in progress',
            'icon': 'file-alt'
        })
    
    if shipment.status == 'delivered':
        updates.append({
            'time': '30 minutes ago',
            'location': 'Final Destination',
            'message': 'Successfully delivered to recipient',
            'icon': 'check-circle'
        })
    
    return updates

@register.filter
def status_badge_class(status):
    """Return CSS class for status badge"""
    status_classes = {
        'pending': 'bg-gray-100 text-gray-800',
        'picked': 'bg-blue-100 text-blue-800',
        'on_hold': 'bg-orange-100 text-orange-800',
        'on_way': 'bg-yellow-100 text-yellow-800',
        'custom_hold': 'bg-red-100 text-red-800',
        'delivered': 'bg-green-100 text-green-800',
    }
    return status_classes.get(status, 'bg-gray-100 text-gray-800')

@register.filter
def payment_status_class(status):
    """Return CSS class for payment status"""
    status_classes = {
        'not_required': 'bg-gray-100 text-gray-800',
        'awaiting_payment': 'bg-yellow-100 text-yellow-800',
        'paid': 'bg-green-100 text-green-800',
    }
    return status_classes.get(status, 'bg-gray-100 text-gray-800')

@register.simple_tag
def random_animation_delay(index):
    """Generate random animation delay for staggered effects"""
    delays = ['0s', '0.1s', '0.2s', '0.3s', '0.4s', '0.5s']
    return delays[index % len(delays)]

@register.filter
def phone_format(phone):
    """Format phone number for display"""
    if not phone:
        return ""
    return f"+1 {phone}"

@register.filter
def encrypt_email(email):
    """Basic email obfuscation"""
    if not email:
        return ""
    parts = email.split('@')
    if len(parts) == 2:
        return f"{parts[0][:3]}***@{parts[1]}"
    return email

@register.filter
def status_icon(status):
    """Get appropriate icon for status"""
    icons = {
        'pending': 'clock',
        'picked': 'shopping-bag',
        'on_hold': 'pause-circle',
        'on_way': 'truck',
        'custom_hold': 'file-alt',
        'delivered': 'check-circle',
    }
    return icons.get(status, 'question-circle')