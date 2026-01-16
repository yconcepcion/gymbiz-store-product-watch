from django.db import models
from django.contrib.auth import get_user_model
import secrets


class Product(models.Model):
    sku = models.CharField(max_length=120)
    store_provider_url = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    in_stock = models.BooleanField(default=True)

    class Meta:
        db_table = 'products'
        ordering = ['sku']

    def __str__(self):
        return self.sku

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pipeline = None

    def get_pipeline(self):
        if self.pipeline is None:
            from products.service.product_status_pipeline_service import ProductStatusPipelineService
            service = ProductStatusPipelineService()
            self.pipeline = service.find(self)
        return self.pipeline

    def get_current_pipeline(self):
        return self.get_pipeline().first()

    def status(self):
        return self.get_current_pipeline().product_status.label

    def active(self):
        return self.get_current_pipeline().product_status.name == ProductStatus.CREATED


class ProductStatus(models.Model):
    name = models.CharField(max_length=120)
    label = models.CharField(max_length=120)

    class Meta:
        db_table = 'product_status'
        ordering = ['label']

    CREATED = "created"
    DELETED = "deleted"

    def __str__(self):
        return self.label


User = get_user_model()


class ProductStatusPipeline(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='rel_pipeline')
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='rel_product_pipeline')
    product_status = models.ForeignKey(ProductStatus, on_delete=models.PROTECT, related_name='rel_pipeline')
    posted = models.DateTimeField()
    log = models.TextField()

    class Meta:
        db_table = 'product_status_pipeline'
        ordering = ['-posted']

    def __str__(self):
        return "self.posted"


class ApplicationToken(models.Model):
    """
    Token para autenticación de aplicaciones
    """
    app_name = models.CharField(max_length=100, unique=True)
    token = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='app_tokens'
    )

    class Meta:
        verbose_name = "Token de Aplicación"
        verbose_name_plural = "Tokens de Aplicación"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(32)  # Genera token de 64 caracteres
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.app_name} - {self.user.username}"