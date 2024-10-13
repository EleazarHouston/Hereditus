from django.db import models

class StoryText(models.Model):
    colony = models.ForeignKey('main_game.Colony', on_delete=models.CASCADE)
    story_text_type = models.CharField(max_length=32, default="default")
    story_text = models.CharField(max_length=1028, default="N/A")
    timestamp = models.DateTimeField()
    
    # TODO: Add StoryText to logger whenever created