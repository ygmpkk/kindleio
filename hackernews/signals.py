from django.dispatch import Signal

points_updated = Signal(providing_args=["pre_points"])
file_saved = Signal()
