from django.contrib.auth.backends import ModelBackend


class StaffAdminBackend(ModelBackend):
    """Give active staff complete site-management permissions."""

    def has_perm(self, user_obj, perm, obj=None):
        if user_obj.is_active and user_obj.is_staff:
            return True
        return super().has_perm(user_obj, perm, obj)

    def has_module_perms(self, user_obj, app_label):
        if user_obj.is_active and user_obj.is_staff:
            return True
        return super().has_module_perms(user_obj, app_label)
