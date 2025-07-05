# cards/utils.py - Image optimization and processing utilities
import os
from PIL import Image, ImageOps
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


class ImageProcessor:
    """Advanced image processing utilities"""

    # Supported formats
    SUPPORTED_FORMATS = ['JPEG', 'PNG', 'WebP', 'AVIF']

    # Image size limits
    MAX_SIZES = {
        'profile': (400, 400),  # Profile photos
        'logo': (200, 100),  # Company logos
        'banner': (800, 300),  # Banner images
        'qr': (300, 300),  # QR codes
    }

    # Quality settings
    QUALITY_SETTINGS = {
        'high': 95,
        'medium': 85,
        'low': 70,
        'thumbnail': 60
    }

    @staticmethod
    def optimize_image(image_file, image_type='profile', quality='medium', format_output='JPEG'):
        """
        Optimize image with compression and resizing

        Args:
            image_file: Django UploadedFile or PIL Image
            image_type: 'profile', 'logo', 'banner', 'qr'
            quality: 'high', 'medium', 'low', 'thumbnail'
            format_output: 'JPEG', 'PNG', 'WebP', 'AVIF'

        Returns:
            ContentFile: Optimized image ready for Django
        """
        try:
            # Open image
            if hasattr(image_file, 'read'):
                img = Image.open(image_file)
            else:
                img = image_file

            # Convert RGBA to RGB for JPEG
            if format_output == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background

            # Get target size
            max_size = ImageProcessor.MAX_SIZES.get(image_type, (800, 600))

            # Resize maintaining aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Auto-orient based on EXIF data
            img = ImageOps.exif_transpose(img)

            # Optimize and save
            output = BytesIO()

            save_kwargs = {
                'format': format_output,
                'optimize': True,
                'quality': ImageProcessor.QUALITY_SETTINGS[quality]
            }

            # Format-specific optimizations
            if format_output == 'PNG':
                save_kwargs.update({'compress_level': 6})
            elif format_output == 'WebP':
                save_kwargs.update({'method': 6, 'lossless': False})
            elif format_output == 'AVIF':
                save_kwargs.update({'quality': save_kwargs['quality'] + 5})  # AVIF is more efficient

            img.save(output, **save_kwargs)
            output.seek(0)

            # Generate filename
            file_extension = format_output.lower()
            if file_extension == 'jpeg':
                file_extension = 'jpg'

            return ContentFile(output.getvalue())

        except Exception as e:
            print(f"Image optimization error: {e}")
            return image_file  # Return original if optimization fails

    @staticmethod
    def create_thumbnail(image_file, size=(150, 150)):
        """Create a thumbnail version"""
        return ImageProcessor.optimize_image(
            image_file,
            image_type='thumbnail',
            quality='thumbnail'
        )

    @staticmethod
    def crop_center(image_file, crop_size):
        """
        Crop image fr   e1qacom center to specified size

        Args:
            image_file: Image file
            crop_size: Tuple (width, height)
        """
        try:
            img = Image.open(image_file) if hasattr(image_file, 'read') else image_file

            # Calculate center crop coordinates
            width, height = img.size
            crop_width, crop_height = crop_size

            left = (width - crop_width) // 2
            top = (height - crop_height) // 2
            right = left + crop_width
            bottom = top + crop_height

            # Crop the image
            cropped = img.crop((left, top, right, bottom))

            # Save to BytesIO
            output = BytesIO()
            cropped.save(output, format='JPEG', quality=90, optimize=True)
            output.seek(0)

            return ContentFile(output.getvalue())

        except Exception as e:
            print(f"Cropping error: {e}")
            return image_file

    @staticmethod
    def get_image_info(image_file):
        """Get detailed image information"""
        try:
            img = Image.open(image_file) if hasattr(image_file, 'read') else image_file

            return {
                'size': img.size,
                'format': img.format,
                'mode': img.mode,
                'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
                'file_size': len(image_file.read()) if hasattr(image_file, 'read') else 0
            }
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def validate_image(image_file, max_file_size=5 * 1024 * 1024):  # 5MB default
        """
        Validate uploaded image

        Args:
            image_file: Uploaded file
            max_file_size: Maximum file size in bytes

        Returns:
            dict: Validation result
        """
        try:
            # Check file size
            if hasattr(image_file, 'size') and image_file.size > max_file_size:
                return {
                    'valid': False,
                    'error': f'File too large. Max size: {max_file_size // (1024 * 1024)}MB'
                }

            # Check if it's a valid image
            img = Image.open(image_file)
            img.verify()  # Verify it's a valid image

            # Reset file pointer after verify
            if hasattr(image_file, 'seek'):
                image_file.seek(0)

            # Check format
            if img.format not in ImageProcessor.SUPPORTED_FORMATS:
                return {
                    'valid': False,
                    'error': f'Unsupported format. Supported: {", ".join(ImageProcessor.SUPPORTED_FORMATS)}'
                }

            return {'valid': True, 'format': img.format, 'size': img.size}

        except Exception as e:
            return {'valid': False, 'error': f'Invalid image file: {str(e)}'}


def process_uploaded_image(image_field, image_type='profile', auto_optimize=True):
    """
    Process uploaded image with automatic optimization

    Usage in models:
    def save(self, *args, **kwargs):
        if self.profile_photo:
            self.profile_photo = process_uploaded_image(self.profile_photo, 'profile')
        super().save(*args, **kwargs)
    """
    if not image_field or not auto_optimize:
        return image_field

    try:
        # Validate first
        validation = ImageProcessor.validate_image(image_field)
        if not validation['valid']:
            raise ValueError(validation['error'])

        # Optimize the image
        optimized = ImageProcessor.optimize_image(
            image_field,
            image_type=image_type,
            quality='medium',
            format_output='JPEG'
        )

        # Generate new filename
        original_name = getattr(image_field, 'name', 'image.jpg')
        name_parts = original_name.rsplit('.', 1)
        new_name = f"{name_parts[0]}_optimized.jpg"

        # Create new file
        optimized.name = new_name
        return optimized

    except Exception as e:
        print(f"Image processing error: {e}")
        return image_field  # Return original if processing fails