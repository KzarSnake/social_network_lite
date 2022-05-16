from django.utils import timezone


def year(request):
    date = timezone.now()
    return {'year': date.year}
