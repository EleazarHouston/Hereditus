from django.db import models
import logging

logger = logging.getLogger('hereditus')

class Game(models.Model):
    starting_torbs = models.IntegerField(default=4)
    description = models.CharField(max_length=256, null=True)
    round_number = models.IntegerField(default=1)
    
    def __str__(self):
        return self.description
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            logger.info(f"A new Game '{self.description}' was made")
    
    def next_round(self):
        
        # have whatever calls this by default check if all colonies are ready
        # do combat here
        
        for colony in self.colony_set.all():
            colony.new_round(round_number = self.round_number)
            
        # Done in a separate loop because web GUIs are updated when ready value is updated
        for colony in self.colony_set.all():
            colony.ready = False
            colony.save()
        self.round_number += 1
        self.save()
        logger.debug(f"Next round processed successfully")
    
    def check_ready_status(self):
        logger.debug(f"Checking colonies ready statuses")
            if not colony.ready:
                return False
        logger.debug(f"All colonies are ready for the next round")
        self.next_round()