from django.db import models


class Cc(models.Model):
    document = models.FileField(null=True)
