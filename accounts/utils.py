from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User
from kindleio.accounts.models import UserProfile


def create_or_update_user(user_id, attr):
    """
    Currently, attr must be one of ("douban", "twitter")
    """
    if not user_id or not attr:
        return

    if attr not in ("douban", "twitter"):
        return
    
    username = attr + "_" + user_id
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
    else:
        user = User.objects.create_user(username=username)

    try:
        profile = user.get_profile()
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    attr_name = attr + '_id'
    if getattr(profile, attr_name) != user_id:
        setattr(profile, attr_name, user_id)
        profile.save()
    user_logged_in.send(sender=user.__class__, user=user)
    return user

