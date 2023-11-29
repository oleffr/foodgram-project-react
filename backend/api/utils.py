import csv

from django.http import HttpResponse


def download_csv(queryset):
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition':
                 'attachment;filename="shopping_cart.csv"'},)
    writer = csv.DictWriter(response,
                            fieldnames=queryset.first().keys())
    writer.writeheader()
    writer.writerows(queryset)
    return response
