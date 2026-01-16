from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .models import ApplicationToken
from .serializers import (
    ApplicationTokenSerializer,
    CreateApplicationTokenSerializer, ProductSerializer
)
from .permissions import IsApplicationAuthenticated
from .service.product_service import ProductService


class CreateApplicationTokenView(generics.CreateAPIView):
    """
    Vista para crear nuevos tokens (requiere autenticación de usuario normal)
    """
    queryset = ApplicationToken.objects.all()
    serializer_class = CreateApplicationTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ListApplicationTokensView(generics.ListAPIView):
    """
    Lista tokens del usuario autenticado
    """
    serializer_class = ApplicationTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ApplicationToken.objects.filter(user=self.request.user)


class RevokeApplicationTokenView(generics.DestroyAPIView):
    """
    Revocar (desactivar) un token
    """
    queryset = ApplicationToken.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ApplicationToken.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


@api_view(['GET'])
@permission_classes([IsApplicationAuthenticated])
def get_product_by_sku(request, sku):
    """
    Get product by SKU using GET method

    Parameters:
    - sku: Product SKU code

    Returns:
    - Product data: id, sku, url, price

    Example:
    GET /api/products/sku/0003456/
    """

    try:
        service = ProductService()
        product = service.find_by_sku(sku)

        if product is None:
            return Response({
                'success': False,
                'error': 'Product not found',
                'message': f'No product found with SKU: {sku}',
                'sku': sku
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductSerializer(product)
        return Response({
            'success': True,
            'data': serializer.data
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
