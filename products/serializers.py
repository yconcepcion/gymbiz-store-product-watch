from rest_framework import serializers
from .models import ApplicationToken, Product


class ApplicationTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationToken
        fields = ['id', 'app_name', 'token', 'is_active', 'created_at', 'last_used']
        read_only_fields = ['token', 'created_at', 'last_used']


class CreateApplicationTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationToken
        fields = ['app_name']

    def create(self, validated_data):
        # El token se genera automáticamente en el save() del modelo
        return ApplicationToken.objects.create(
            app_name=validated_data['app_name'],
            user=self.context['request'].user
        )


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'sku', 'store_provider_url', 'price', 'in_stock', 'status']
