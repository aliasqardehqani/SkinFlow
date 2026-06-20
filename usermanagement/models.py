import uuid
from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone

from .managers import UserManager
from .validators import validate_iranian_phone


# ─────────────────────────────────────────────
# 1. User (‌Base Auth model)
# ─────────────────────────────────────────────

class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        CLIENT = 'client',     'مراجعه‌کننده'
        CONSULTANT = 'consultant', 'مشاور'
        SUPPORT    = 'support',    'پشتیبان'
        ADMIN      = 'admin',      'مدیر'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(
                     max_length=11,
                     unique=True,
                     validators=[validate_iranian_phone],
                     verbose_name='شماره موبایل'
                 )
    email = models.EmailField(
                     unique=True,
                     null=True,
                     blank=True,
                     verbose_name='ایمیل'
                 )
    role = models.CharField(
                     max_length=20,
                     choices=Role.choices,
                     default=Role.CLIENT,
                     verbose_name='نقش'
                 )
    is_verified = models.BooleanField(default=False, verbose_name='تایید شده')
    is_active   = models.BooleanField(default=True,  verbose_name='فعال')
    is_staff    = models.BooleanField(default=False, verbose_name='کارمند')
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')
    updated_at  = models.DateTimeField(auto_now=True,     verbose_name='آخرین ویرایش')
    last_login  = models.DateTimeField(null=True, blank=True, verbose_name='آخرین ورود')

    USERNAME_FIELD  = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table    = 'users'
        verbose_name      = 'کاربر'
        verbose_name_plural = 'کاربران'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.phone} ({self.get_role_display()})'

    # ── helpers ──────────────────────────────
    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def is_consultant(self):
        return self.role == self.Role.CONSULTANT

    @property
    def is_support(self):
        return self.role == self.Role.SUPPORT

    def get_profile(self):
        """
        پروفایل مرتبط با نقش کاربر را برمی‌گرداند.
        """
        profile_map = {
            self.Role.CLIENT:     'client_profile',
            self.Role.CONSULTANT: 'consultant_profile',
            self.Role.SUPPORT:    'support_profile',
            self.Role.ADMIN:      'admin_profile',
        }
        return getattr(self, profile_map.get(self.role), None)


# ─────────────────────────────────────────────
# 2. OTP
# ─────────────────────────────────────────────

class OTP(models.Model):

    class Purpose(models.TextChoices):
        REGISTER       = 'register',        'ثبت‌نام'
        LOGIN          = 'login',           'ورود'
        RESET_PASSWORD = 'reset_password',  'بازیابی رمز'
        VERIFY_EMAIL   = 'verify_email',    'تایید ایمیل'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(
                      User,
                      on_delete=models.CASCADE,
                      related_name='otps',
                      verbose_name='کاربر'
                  )
    code        = models.CharField(max_length=6, verbose_name='کد')
    purpose     = models.CharField(max_length=20, choices=Purpose.choices, verbose_name='هدف')
    is_used     = models.BooleanField(default=False, verbose_name='استفاده شده')
    attempt_count = models.PositiveSmallIntegerField(default=0, verbose_name='تعداد تلاش')
    expires_at  = models.DateTimeField(verbose_name='انقضا')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'otps'
        verbose_name = 'OTP'
        verbose_name_plural = 'OTPها'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.phone} | {self.purpose} | {self.code}'

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired and self.attempt_count < 3

    def send(self):
        """
        TODO: متد ارسال OTP — فعلاً فقط در لاگ چاپ می‌شود.
        """
        print(f'[OTP] ارسال به {self.user.phone}: کد = {self.code}')


# ─────────────────────────────────────────────
# 3. پروفایل مشترک (Abstract)
# ─────────────────────────────────────────────

class BaseProfile(models.Model):
    first_name = models.CharField(max_length=100, verbose_name='نام')
    last_name  = models.CharField(max_length=100, verbose_name='نام خانوادگی')
    avatar     = models.ImageField(
                     upload_to='avatars/%Y/%m/',
                     null=True, blank=True,
                     verbose_name='تصویر پروفایل'
                 )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()


# ─────────────────────────────────────────────
# 4. ClientProfile
# ─────────────────────────────────────────────

class ClientProfile(BaseProfile):

    class Gender(models.TextChoices):
        MALE    = 'male',   'مرد'
        FEMALE  = 'female', 'زن'
        OTHER   = 'other',  'سایر'

    user       = models.OneToOneField(
                     User,
                     on_delete=models.CASCADE,
                     related_name='client_profile',
                     limit_choices_to={'role': User.Role.CLIENT},
                     verbose_name='کاربر'
                 )
    gender     = models.CharField(
                     max_length=10,
                     choices=Gender.choices,
                     null=True, blank=True,
                     verbose_name='جنسیت'
                 )
    birth_date = models.DateField(null=True, blank=True, verbose_name='تاریخ تولد')
    timezone   = models.CharField(
                     max_length=50,
                     default='Asia/Tehran',
                     verbose_name='منطقه زمانی'
                 )
    preferred_language = models.CharField(
                             max_length=10,
                             default='fa',
                             verbose_name='زبان ترجیحی'
                         )

    class Meta:
        db_table = 'client_profiles'
        verbose_name = 'پروفایل مراجعه‌کننده'
        verbose_name_plural = 'پروفایل مراجعه‌کنندگان'

    def __str__(self):
        return f'{self.full_name} — {self.user.phone}'


# ─────────────────────────────────────────────
# 5. ConsultantProfile
# ─────────────────────────────────────────────

class ConsultantProfile(BaseProfile):

    user               = models.OneToOneField(
                             User,
                             on_delete=models.CASCADE,
                             related_name='consultant_profile',
                             limit_choices_to={'role': User.Role.CONSULTANT},
                             verbose_name='کاربر'
                         )
    bio                = models.TextField(null=True, blank=True, verbose_name='بیوگرافی')
    specialties        = models.JSONField(default=list, verbose_name='تخصص‌ها')
    # مثال: ['acne', 'anti_aging', 'sensitive_skin']
    license_number     = models.CharField(
                             max_length=50,
                             null=True, blank=True,
                             verbose_name='شماره پروانه'
                         )
    years_of_experience = models.PositiveSmallIntegerField(
                              null=True, blank=True,
                              verbose_name='سال‌های تجربه'
                          )
    is_available       = models.BooleanField(default=True, verbose_name='در دسترس')
    average_rating     = models.DecimalField(
                             max_digits=3, decimal_places=2,
                             default=0.00,
                             verbose_name='میانگین امتیاز'
                         )
    total_sessions     = models.PositiveIntegerField(default=0, verbose_name='کل جلسات')

    class Meta:
        db_table = 'consultant_profiles'
        verbose_name = 'پروفایل مشاور'
        verbose_name_plural = 'پروفایل مشاوران'

    def __str__(self):
        return f'دکتر {self.full_name}'


# ─────────────────────────────────────────────
# 6. SupportProfile
# ─────────────────────────────────────────────

class SupportProfile(BaseProfile):

    user = models.OneToOneField(
               User,
               on_delete=models.CASCADE,
               related_name='support_profile',
               limit_choices_to={'role': User.Role.SUPPORT},
               verbose_name='کاربر'
           )

    class Meta:
        db_table = 'support_profiles'
        verbose_name = 'پروفایل پشتیبان'
        verbose_name_plural = 'پروفایل پشتیبانان'

    def __str__(self):
        return self.full_name


# ─────────────────────────────────────────────
# 7. AdminProfile
# ─────────────────────────────────────────────

class AdminProfile(BaseProfile):

    PERMISSION_CHOICES = [
        ('manage_users',    'مدیریت کاربران'),
        ('manage_products', 'مدیریت محصولات'),
        ('manage_consults', 'مدیریت مشاوره‌ها'),
        ('view_reports',    'مشاهده گزارش‌ها'),
        ('manage_content',  'مدیریت محتوا'),
        ('manage_plans',    'مدیریت تعرفه‌ها'),
    ]

    user        = models.OneToOneField(
                      User,
                      on_delete=models.CASCADE,
                      related_name='admin_profile',
                      limit_choices_to={'role': User.Role.ADMIN},
                      verbose_name='کاربر'
                  )
    permissions = models.JSONField(default=list, verbose_name='دسترسی‌ها')

    class Meta:
        db_table = 'admin_profiles'
        verbose_name = 'پروفایل مدیر'
        verbose_name_plural = 'پروفایل مدیران'

    def __str__(self):
        return self.full_name

    def has_perm(self, perm):
        return perm in self.permissions


# ─────────────────────────────────────────────
# 8. UserAddress
# ─────────────────────────────────────────────

class UserAddress(models.Model):

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(
                      User,
                      on_delete=models.CASCADE,
                      related_name='addresses',
                      verbose_name='کاربر'
                  )
    label       = models.CharField(
                      max_length=50,
                      null=True, blank=True,
                      verbose_name='برچسب'
                  )  # مثال: خانه، محل کار
    province    = models.CharField(max_length=100, verbose_name='استان')
    city        = models.CharField(max_length=100, verbose_name='شهر')
    street      = models.TextField(verbose_name='آدرس')
    postal_code = models.CharField(max_length=10, verbose_name='کد پستی')
    is_default  = models.BooleanField(default=False, verbose_name='پیش‌فرض')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_addresses'
        verbose_name = 'آدرس'
        verbose_name_plural = 'آدرس‌ها'

    def __str__(self):
        return f'{self.user.phone} — {self.city} ({self.label or "بدون برچسب"})'

    def save(self, *args, **kwargs):
        """
        اگر این آدرس به عنوان پیش‌فرض ذخیره شود،
        بقیه آدرس‌های همین کاربر از پیش‌فرض خارج می‌شوند.
        """
        if self.is_default:
            UserAddress.objects.filter(
                user=self.user, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
# 9. NotificationPreference
# ─────────────────────────────────────────────

class NotificationPreference(models.Model):

    user                = models.OneToOneField(
                              User,
                              on_delete=models.CASCADE,
                              related_name='notification_preference',
                              verbose_name='کاربر'
                          )
    sms_enabled         = models.BooleanField(default=True,  verbose_name='پیامک')
    email_enabled       = models.BooleanField(default=True,  verbose_name='ایمیل')
    push_enabled        = models.BooleanField(default=True,  verbose_name='پوش نوتیفیکیشن')
    appointment_reminder = models.BooleanField(default=True, verbose_name='یادآوری نوبت')
    message_alerts      = models.BooleanField(default=True,  verbose_name='اعلان پیام')
    order_updates       = models.BooleanField(default=True,  verbose_name='به‌روزرسانی سفارش')
    progress_nudges     = models.BooleanField(default=True,  verbose_name='یادآوری پیشرفت درمان')

    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'تنظیمات اعلان'
        verbose_name_plural = 'تنظیمات اعلان‌ها'

    def __str__(self):
        return f'تنظیمات اعلان — {self.user.phone}'