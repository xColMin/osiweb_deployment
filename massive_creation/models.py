from django.db import models


class Mc(models.Model):
    document = models.FileField(null=True)
