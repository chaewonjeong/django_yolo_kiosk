from django.db import models


class Product(models.Model):
    name = models.TextField()
    price = models.IntegerField()
    class_id = models.IntegerField()

    def __str__(self):
        return self.name
