import logging

from django.db import models
from django.utils.timezone import now

logger = logging.getLogger('hereditus')

class StoryText(models.Model):
    colony = models.ForeignKey('main_game.Colony', on_delete=models.CASCADE)
    story_text_type = models.CharField(max_length=32, default="default")
    story_text = models.CharField(max_length=1028, default="N/A")
    timestamp = models.DateTimeField(default=now)
    game_round = models.IntegerField(default=-1)
    
    # TODO: Add StoryText to logger whenever created
    
    @property
    def is_new(self):
        return self.game_round + 1 >= self.colony.game.round_number
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            self.game_round = self.colony.game.round_number
        
        super().save(*args, **kwargs)
        
        if is_new:
            logger.debug(f"StoryText for Colony {self.colony.name} of type {self.story_text_type}: {self.story_text}")