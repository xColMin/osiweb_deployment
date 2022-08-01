from django.db import models


class Ov(models.Model):
    document = models.FileField(null=True)

