from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('شماره موبایل الزامی است')
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(phone=phone, **extra_fields)
        
        if password:
            user.set_password(password)
        else:
            user.save(using=self._db)
            return user
        
    def create_superuser(self, phone, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('role', 'admin')

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser باید is_staff=True داشته باشد.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser باید is_superuser=True داشته باشد.')

        return self.create_user(phone, password, **extra_fields)
        