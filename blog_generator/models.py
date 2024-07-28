from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class BlogPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    youtube_title = models.CharField(max_length=300)
    youtube_link = models.URLField()
    generated_content = models.TextField()
    transcription = models.TextField(default='') 
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def _str_(self):
        return self.youtube_title
    