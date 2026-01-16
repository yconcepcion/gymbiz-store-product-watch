from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext as _
from django.contrib import messages
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
import csv
import io
import json

from products.models import Product, ApplicationToken, ProductStatus
from products.service.product_service import ProductService
from products.service.product_status_pipeline_service import ProductStatusPipelineService
from products.unit.action.create_product import CreateProductAction
from products.unit.action.update_product import UpdateProductAction

PAGE_VAR = "p"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'store_provider_url', 'price', 'in_stock', 'status']

    search_fields = ['sku', 'store_provider_url']

    list_filter = [
        'in_stock'
    ]

    actions = ['change_status_deleted_product', 'change_status_created_product']

    def change_status(self, request, queryset, status):
        try:
            for product in queryset:
                update_product_action = UpdateProductAction()
                update_product_action.set(
                    request.user,
                    product.pk,
                    product.sku,
                    product.store_provider_url,
                    product.price,
                    product.in_stock,
                    status
                )
                update_product_action.execute()

                self.message_user(
                    request,
                    f"Status cambiados correctamente."
                )
        except Exception as e:
            self.message_user(
                request,
                f"Ha ocurrido un error al tratar de cambiar el estado."
            )

    def change_status_deleted_product(self, request, queryset):
        self.change_status(request, queryset, ProductStatus.DELETED)

    change_status_deleted_product.short_description = "Change product status to Deleted"

    def change_status_created_product(self, request, queryset):
        self.change_status(request, queryset, ProductStatus.CREATED)

    change_status_created_product.short_description = "Change product status to Created"

    def save_model(self, request, obj, form, change):
        if not change:
            create_product = CreateProductAction()
            create_product.set(request.user, obj.sku, obj.store_provider_url, obj.price, obj.in_stock)
            create_product.execute()
        else:
            update_product = UpdateProductAction()
            update_product.set(request.user, obj.id, obj.sku, obj.store_provider_url, obj.price, obj.in_stock, None)
            update_product.execute()

        # messages.success(request, f"Producto '{obj.sku}' guardado exitosamente!")

    def delete_model(self, request, obj):
        pass

    def history_view(self, request, object_id, extra_context=None):
        from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION

        model = self.model
        opts = model._meta

        # Obtener el objeto
        obj = self.get_object(request, object_id)

        if obj is None:
            return self._get_obj_does_not_exist_redirect(request, opts, object_id)

        # Obtener historial personalizado
        pipeline_service = ProductStatusPipelineService()
        action_list = pipeline_service.find_all_by_product_id(object_id)

        # Formatear para que sea compatible con el template del admin
        formatted_action_list = []
        for action in action_list:
            # Parsear el JSON del log
            try:
                log_data = json.loads(action.log)
                changes = log_data.get('changes', [])
                notes = log_data.get('notes', '')
            except:
                changes = []
                notes = action.log  # Mostrar como texto plano si no es JSON

            # Crear mensaje de cambio formateado
            change_message = self._format_change_message(changes, obj)
            if notes:
                change_message = f"{change_message}\n\nNotas: {notes}" if change_message else f"Notas: {notes}"

            formatted_action_list.append({
                'action_time': action.posted,
                'user': action.user,
                'change_message': change_message,
                'action_flag': CHANGE,  # Usar constante de Django para cambios
                'is_addition': False,
                'is_change': True,
                'is_deletion': False,
                'get_change_message': change_message,
                'get_edited_object': lambda: obj,
                'get_admin_url': lambda: f'/admin/products/product/{object_id}/change/',
            })

        paginator = self.get_paginator(request, formatted_action_list, 100)
        page_number = request.GET.get(PAGE_VAR, 1)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(page_obj.number)

        context = {
            **self.admin_site.each_context(request),
            'title': _('Change history: %s') % obj,
            'action_list': page_obj,
            "page_range": page_range,
            "page_var": PAGE_VAR,
            "pagination_required": paginator.count > 100,
            'module_name': str(opts.verbose_name_plural),
            'object': obj,
            'opts': opts,
            'preserved_filters': self.get_preserved_filters(request),
        }

        return TemplateResponse(request,
            self.object_history_template
            or [
                "admin/object_history.html",
            ],
            context)

    def _format_change_message(self, changes, product):
        if not changes:
            return product.status

        messages = []
        for change in changes:
            field = change.get('field', '')
            from_val = change.get('from', 'N/A')
            to_val = change.get('to', 'N/A')

            # Formatear según el tipo de campo
            if field == 'price':
                from_val = f"${float(from_val):,.2f}" if from_val is not None and from_val != 'N/A' else 'N/A'
                to_val = f"${float(to_val):,.2f}" if to_val is not None and to_val != 'N/A' else 'N/A'

            messages.append(f"{field}: {from_val} -> {to_val}")

        return "\n".join(messages)

    def changelist_view(self, request, extra_context=None):
        # Obtener el contexto normal
        response = super().changelist_view(request, extra_context)

        # Modificar el contenido de la respuesta
        if hasattr(response, 'render'):
            response.content = self._add_import_button_to_content(
                response.rendered_content if hasattr(response, 'rendered_content')
                else response.content.decode('utf-8')
            )

        return response

    def _add_import_button_to_content(self, content):
        """Inyectar botones en el HTML del admin"""

        # Buscar el objeto tools en el HTML
        import re

        # Patrón para encontrar object-tools
        pattern = r'(<ul class="object-tools">)(.*?)(</ul>)'

        # HTML de los botones personalizados
        custom_buttons = '''
        <li>
            <a href="{}" class="button">
                Import products
            </a>
        </li>
        '''.format(reverse('admin:import_products'))

        # Reemplazar en el contenido
        def replace_match(match):
            return match.group(1) + custom_buttons + match.group(2) + match.group(3)

        return re.sub(pattern, replace_match, content, flags=re.DOTALL)

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                'import/',
                self.admin_site.admin_view(self.import_view),
                name='import_products'
            )
        ]

        return custom_urls + urls

    def import_view(self, request):
        """
        Maneja GET (formulario) y POST (procesar) en una sola función
        sin necesidad de template externo
        """

        # ===== POST: Procesar archivo =====
        if request.method == 'POST':
            file = request.FILES.get('csv_file')

            if not file:
                # Si no hay archivo, mostrar error y volver a mostrar formulario
                error_html = self._render_import_form(request, "❌ Por favor selecciona un archivo CSV")
                return HttpResponse(error_html)

            try:
                # Procesar CSV
                decoded_file = file.read().decode('utf-8-sig')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)

                service = ProductService()
                results = []
                for row in reader:
                    sku = row.get('sku', None)
                    store_provider_url = json.loads(row.get('store_provider_url_list', None))[0]
                    product = service.find_by_sku(sku)
                    if product:
                        update_product = UpdateProductAction()
                        update_product.set(request.user, product.pk, sku, store_provider_url, None, None, None)
                        update_product.execute()
                    else:
                        create_product = CreateProductAction()
                        create_product.set(request.user, sku, store_provider_url, None, True)
                        create_product.execute()

                    results.append(f"Procesado: {row.get('sku', 'Sin sku')}")

                # Mostrar resultados y botón para volver
                success_html = f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Importación Completada</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; }}
                        .success {{ color: #28a745; font-size: 24px; margin: 20px 0; }}
                        .results {{ text-align: left; max-width: 600px; margin: 30px auto; }}
                        .btn {{ 
                            background: #4a6fa5; color: white; padding: 10px 20px;
                            text-decoration: none; border-radius: 4px; display: inline-block;
                            margin: 20px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="success">Importación completada exitosamente!</div>
                    <div class="results">
                        <h3>Resultados:</h3>
                        <ul>
                            {"".join(f"<li>{r}</li>" for r in results[:10])}
                            {f"<li>... y {len(results) - 10} más</li>" if len(results) > 10 else ""}
                        </ul>
                    </div>
                    <a href="{reverse('admin:products_product_changelist')}" class="btn">
                        Volver al listado de productos
                    </a>
                </body>
                </html>
                '''

                return HttpResponse(success_html)

            except Exception as e:
                error_html = self._render_import_form(
                    request,
                    f"❌ Error al procesar archivo: {str(e)}"
                )
                return HttpResponse(error_html)

        # ===== GET: Mostrar formulario =====
        return HttpResponse(self._render_import_form(request))

    def _render_import_form(self, request, error_message=None):
        """Genera HTML del formulario de importación"""

        form_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Importar Productos</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                .container {{ max-width: 500px; margin: 0 auto; }}
                .error {{ color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 4px; }}
                form {{ margin: 20px 0; }}
                .btn {{ 
                    background: #28a745; color: white; padding: 10px 20px;
                    border: none; border-radius: 4px; cursor: pointer;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Importar Productos</h1>

                {f'<div class="error">{error_message}</div>' if error_message else ''}

                <form method="post" enctype="multipart/form-data">
                    <input type="hidden" name="csrfmiddlewaretoken" value="{request.META.get('CSRF_COOKIE', '')}">

                    <p><strong>Selecciona un archivo CSV:</strong></p>
                    <input type="file" name="csv_file" accept=".csv" required>
                    <br><br>

                    <button type="submit" class="btn">Subir e Importar</button>
                    <a href="{reverse('admin:products_product_changelist')}" 
                       style="margin-left: 10px; color: #666;">Cancelar</a>
                </form>

                <p><small>💡 El CSV debe tener encabezados: sku, store_provider_url_list</small></p>
            </div>
        </body>
        </html>
        '''

        return form_html


@admin.register(ApplicationToken)
class ApplicationTokenAdmin(admin.ModelAdmin):
    """
    Configuración del admin para ApplicationToken
    """
    # Campos a mostrar en la lista
    list_display = [
        'app_name',
        'user',
        'truncated_token',
        'is_active',
        'created_at',
        'last_used',
        'token_age_days'
    ]

    # Filtros laterales
    list_filter = [
        'is_active',
        'created_at',
        'last_used',
        'user'
    ]

    # Búsqueda
    search_fields = [
        'app_name',
        'token',
        'user__username',
        'user__email'
    ]

    # Campos de solo lectura
    readonly_fields = [
        'token',
        'created_at',
        'last_used',
        'token_preview'
    ]

    # Campos en el formulario de edición
    fieldsets = (
        ('Información de la Aplicación', {
            'fields': ('app_name', 'user', 'is_active')
        }),
        ('Información del Token', {
            'fields': ('token_preview', 'created_at', 'last_used'),
            'classes': ('collapse',)  # Se puede colapsar
        }),
    )

    # Ordenamiento por defecto
    ordering = ('-created_at',)

    # Acciones personalizadas
    actions = ['deactivate_tokens', 'activate_tokens']

    # Formulario de creación
    def get_fieldsets(self, request, obj=None):
        if not obj:  # Si es creación
            return (
                ('Información de la Aplicación', {
                    'fields': ('app_name', 'user')
                }),
            )
        return super().get_fieldsets(request, obj)

    # Métodos personalizados para list_display
    def truncated_token(self, obj):
        """Muestra solo los primeros y últimos caracteres del token"""
        if len(obj.token) > 20:
            return f"{obj.token[:8]}...{obj.token[-8:]}"
        return obj.token

    truncated_token.short_description = 'Token'
    truncated_token.admin_order_field = 'token'

    def token_preview(self, obj):
        """Muestra el token completo en el formulario de edición"""
        return format_html(
            '<code style="word-break: break-all; background: #f5f5f5; padding: 5px; display: block;">{}</code>',
            obj.token
        )

    token_preview.short_description = 'Vista previa del Token'

    def token_age_days(self, obj):
        """Muestra la antigüedad del token en días"""
        from django.utils import timezone
        if obj.created_at:
            delta = timezone.now() - obj.created_at
            return f"{delta.days} días"
        return "N/A"

    token_age_days.short_description = 'Antigüedad'
    token_age_days.admin_order_field = 'created_at'

    # Acciones personalizadas
    def deactivate_tokens(self, request, queryset):
        """Desactivar tokens seleccionados"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{updated} tokens han sido desactivados correctamente."
        )

    deactivate_tokens.short_description = "Desactivar tokens seleccionados"

    def activate_tokens(self, request, queryset):
        """Activar tokens seleccionados"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f"{updated} tokens han sido activados correctamente."
        )

    activate_tokens.short_description = "Activar tokens seleccionados"

    # Personalizar el formulario de creación
    def save_model(self, request, obj, form, change):
        """Generar automáticamente el token si es nuevo"""
        if not change:  # Solo para nuevos objetos
            # El token se genera automáticamente en el save() del modelo
            pass
        super().save_model(request, obj, form, change)

    # Permisos personalizados
    def has_delete_permission(self, request, obj=None):
        """Permitir eliminar tokens"""
        return True

    def get_readonly_fields(self, request, obj=None):
        """Hacer el token de solo lectura en edición"""
        if obj:  # Si ya existe
            return self.readonly_fields + ['app_name', 'user']
        return self.readonly_fields
