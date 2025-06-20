from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import CustomUserManager
from django.db import models
from django.core.validators import FileExtensionValidator

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('data_entry', 'Data Entry'),
        ('viewer', 'Viewer'),
    ]
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=250, null=True)
    last_name = models.CharField(max_length=250, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    employee_code = models.CharField(max_length=250, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True,
        help_text="Upload a profile picture (JPG, PNG, Max 2MB)"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    

class MPPSahayakAgreement(models.Model):
    mcc = models.CharField(max_length=100)
    mpp_code = models.CharField(max_length=50)
    mpp_name = models.CharField(max_length=100)
    sahayak_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    address = models.TextField()
    mobile_number = models.CharField(max_length=15)
    aadhar = models.CharField(max_length=20)
    pan = models.CharField(max_length=20)
    account_number = models.CharField(max_length=30)
    ifsc_code = models.CharField(max_length=20)
    document = models.FileField(
        upload_to='mpp_sahayak/',
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        help_text="PDF, JPG, or PNG (Max 5MB)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        CustomUser, 
        related_name='created_mppsahayakagreements',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        CustomUser, 
        related_name='updated_mppsahayakagreements',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "MPP/Sahayak Agreement"
        verbose_name_plural = "MPP/Sahayak Agreements"

    def __str__(self):
        return f"{self.mpp_name} - {self.sahayak_name}"


class BaseAgreement(models.Model):
    zone = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    contractor = models.CharField(max_length=100)
    pan = models.CharField(max_length=20)
    type_of_agreement = models.CharField(max_length=100)
    agreement_date = models.DateField()
    start_date = models.DateField()
    end_date = models.DateField()
    tenure_months = models.IntegerField()
    lock_in_period = models.CharField(max_length=100)
    monthly_payout = models.DecimalField(max_digits=12, decimal_places=2)
    document_status = models.CharField(
        max_length=20,
        choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')],
        default='INCOMPLETE'
    )
    document_pending = models.CharField(max_length=255, blank=True, null=True)
    document = models.FileField(
        upload_to='agreements/',
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        help_text="PDF, JPG, or PNG (Max 5MB)",
        max_length=500
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        CustomUser, 
        related_name='created_%(class)s',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        CustomUser, 
        related_name='updated_%(class)s',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        abstract = True


class AMCAgreement(models.Model):
    product = models.CharField(max_length=100)
    contractor = models.CharField(max_length=100)
    pan = models.CharField(max_length=20)
    type_of_agreement = models.CharField(max_length=100)
    agreement_date = models.DateField()
    start_date = models.DateField()
    end_date = models.DateField()
    tenure_months = models.IntegerField()
    lock_in_period = models.CharField(max_length=100)
    monthly_payout = models.DecimalField(max_digits=12, decimal_places=2)
    document_status = models.CharField(
        max_length=20,
        choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')],
        default='INCOMPLETE'
    )
    document_pending = models.CharField(max_length=255, blank=True, null=True)
    document = models.FileField(
        upload_to='amc_agreements/',
        max_length=500,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        help_text="PDF, JPG, or PNG (Max 5MB)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        CustomUser, 
        related_name='created_amcagreements',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        CustomUser, 
        related_name='updated_amcagreements',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.product} - {self.contractor}"
    
    class Meta:
        verbose_name = "AMC Agreement"
        verbose_name_plural = "AMC Agreements"


class ConsultantAgreement(models.Model):
    category = models.CharField(max_length=100)
    contractor = models.CharField(max_length=100)
    pan = models.CharField(max_length=20)
    type_of_agreement = models.CharField(max_length=100)
    agreement_date = models.DateField()
    start_date = models.DateField()
    end_date = models.DateField()
    tenure_months = models.IntegerField()
    lock_in_period = models.CharField(max_length=100)
    monthly_payout = models.DecimalField(max_digits=12, decimal_places=2)
    document_status = models.CharField(
        max_length=20,
        choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')],
        default='INCOMPLETE'
    )
    document_pending = models.CharField(max_length=255, blank=True, null=True)
    document = models.FileField(
        upload_to='consultant_agreements/',
        max_length=500,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        help_text="PDF, JPG, or PNG (Max 5MB)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        CustomUser, 
        related_name='created_consultantagreements',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        CustomUser, 
        related_name='updated_consultantagreements',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.category} - {self.contractor}"
    
    class Meta:
        verbose_name = "Consultant Agreement"
        verbose_name_plural = "Consultant Agreements"
    

    
class InputServicesAgreement(models.Model):
    product = models.CharField(max_length=100)
    contractor = models.CharField(max_length=100)
    pan = models.CharField(max_length=20)
    type_of_agreement = models.CharField(max_length=100)
    agreement_date = models.DateField()
    start_date = models.DateField()
    end_date = models.DateField()
    tenure_months = models.IntegerField()
    lock_in_period = models.CharField(max_length=100)
    monthly_payout = models.DecimalField(max_digits=12, decimal_places=2)
    document_status = models.CharField(
        max_length=20,
        choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')],
        default='INCOMPLETE'
    )
    document_pending = models.CharField(max_length=255, blank=True, null=True)
    document = models.FileField(
        upload_to='input_services_agreements/',
        max_length=500,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        help_text="PDF, JPG, or PNG (Max 5MB)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        CustomUser, 
        related_name='created_inputservicesagreements',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        CustomUser, 
        related_name='updated_inputservicesagreements',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.product} - {self.contractor}"

    class Meta:
        verbose_name = "Input Services Agreement"
        verbose_name_plural = "Input Services Agreements"

class BMCAgreement(BaseAgreement):
    class Meta:
        verbose_name = "BMC Agreement"
        verbose_name_plural = "BMC Agreements"


class CookAgreement(BaseAgreement):
    class Meta:
        verbose_name = "Cook Agreement"
        verbose_name_plural = "Cook Agreements"

class DistributerAgreement(BaseAgreement):
    class Meta:
        verbose_name = "Distributer Agreement"
        verbose_name_plural = "Distributer Agreements"

class MilkSaleAgreement(BaseAgreement):
    class Meta:
        verbose_name = "Milk Sale Agreement"
        verbose_name_plural = "Milk Sale Agreements"

class MCCAgreement(BaseAgreement):
    class Meta:
        verbose_name = "MCC Agreement"
        verbose_name_plural = "MCC Agreements"

class MPACSAgreement(BaseAgreement):
    class Meta:
        verbose_name = "MPACS Agreement"
        verbose_name_plural = "MPACS Agreements"

class RentalBMCAgreement(BaseAgreement):
    class Meta:
        verbose_name = "Rental BMC Agreement"
        verbose_name_plural = "Rental BMC Agreements"

class GodownAgreement(BaseAgreement):
    class Meta:
        verbose_name = "Godown Agreement"
        verbose_name_plural = "Godown Agreements"

class OfficeLeaseAgreement(BaseAgreement):
    class Meta:
        verbose_name = "Office Lease Agreement"
        verbose_name_plural = "Office Lease Agreements"

class GuestHouseAgreement(BaseAgreement):
    class Meta:
        verbose_name = "Guest House Agreement"
        verbose_name_plural = "Guest House Agreements"



class RTAAgreement(BaseAgreement):
    class Meta:
        verbose_name = "RTA Agreement"
        verbose_name_plural = "RTA Agreements"