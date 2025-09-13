from django import template
import os

register = template.Library()

@register.filter
def basename(value):
    """Extract the filename from a file path"""
    if value:
        return os.path.basename(str(value))
    return ''

@register.filter
def file_extension(value):
    """Get the file extension"""
    if value:
        return os.path.splitext(str(value))[1]
    return ''

@register.filter
def file_size(value):
    """Format file size in human readable format"""
    if value:
        try:
            size = value.size
            for unit in ['bytes', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return ''
    return ''
