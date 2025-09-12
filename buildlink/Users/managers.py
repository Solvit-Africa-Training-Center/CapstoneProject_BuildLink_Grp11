from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    """
    Custom manager for User model where email is the unique identifier
    instead of username.
    """
    def create_user(self, email, full_name, phone, role, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not full_name:
            raise ValueError('The Full Name field must be set')
        if not phone:
            raise ValueError('The Phone field must be set')
        if not role:
            raise ValueError('The Role field must be set')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            full_name=full_name,
            phone=phone,
            role=role,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, phone, role='admin', password=None, **extra_fields):
        """Create and save a superuser with the given details."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('verified', True)

        return self.create_user(
            email=email,
            full_name=full_name,
            phone=phone,
            role=role,
            password=password,
            **extra_fields
        )
