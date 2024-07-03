from django.db import models

class Player(models.Model):
    original_name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255, unique=True)
    wiki_url = models.URLField()
    full_record = models.TextField()
    club_career = models.TextField()
    intl_career = models.TextField()

    def __str__(self):
        return self.original_name