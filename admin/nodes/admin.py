from django.contrib import admin
from django.utils import timezone
from .models import Node, Edge, Claim


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    """
    Admin for editing Node display properties.
    Editable: name, descrip, image, thumbnail, entType
    Read-only: nodeUri (identity of the node)
    """
    list_display = ['id', 'name', 'nodeUri_short', 'entType', 'has_image', 'editedAt']
    list_filter = ['entType']
    search_fields = ['name', 'nodeUri', 'descrip']
    ordering = ['-id']

    # Only these fields are editable
    fields = ['nodeUri', 'entType', 'name', 'descrip', 'image', 'thumbnail', 'editedAt', 'editedBy']
    readonly_fields = ['nodeUri', 'editedAt', 'editedBy']  # entType is now editable

    def nodeUri_short(self, obj):
        uri = obj.nodeUri or ''
        return uri[:60] + '...' if len(uri) > 60 else uri
    nodeUri_short.short_description = 'Node URI'

    def has_image(self, obj):
        return bool(obj.image or obj.thumbnail)
    has_image.boolean = True
    has_image.short_description = 'Has Image'

    def save_model(self, request, obj, form, change):
        """Track who edited and when."""
        obj.editedAt = timezone.now()
        obj.editedBy = request.user.username
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        """Nodes are created by the pipeline, not manually."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Nodes should not be deleted via admin."""
        return False


@admin.register(Edge)
class EdgeAdmin(admin.ModelAdmin):
    """Read-only view of edges for reference."""
    list_display = ['id', 'get_start_name', 'label', 'get_end_name', 'claimId']
    list_filter = ['label']
    search_fields = ['startNode__name', 'endNode__name', 'label']
    ordering = ['-id']

    def get_start_name(self, obj):
        return obj.startNode.name if obj.startNode else '-'
    get_start_name.short_description = 'From'

    def get_end_name(self, obj):
        return obj.endNode.name if obj.endNode else '-'
    get_end_name.short_description = 'To'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    """Read-only view of claims for reference."""
    list_display = ['id', 'subject_short', 'claim', 'object_short', 'createdAt']
    list_filter = ['claim']
    search_fields = ['subject', 'claim', 'object', 'statement']
    ordering = ['-id']

    def subject_short(self, obj):
        s = obj.subject or ''
        return s[:40] + '...' if len(s) > 40 else s
    subject_short.short_description = 'Subject'

    def object_short(self, obj):
        o = obj.object or ''
        return o[:40] + '...' if len(o) > 40 else o
    object_short.short_description = 'Object'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# Customize admin site
admin.site.site_header = 'LinkedTrust Admin'
admin.site.site_title = 'LinkedTrust'
admin.site.index_title = 'Manage Node Display Properties'
