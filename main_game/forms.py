from django import forms

from .models import Torb


class NewColonyForm(forms.Form):
    game_id = forms.IntegerField(widget=forms.HiddenInput)
    colony_name = forms.CharField(max_length=63)


ACTION_CHOICES = [
    ("end_turn", "End Turn"),
    ("breed", "Breed"),
    ("gather", "Gather"),
    ("enlist", "Enlist"),
]


class ColonyActionForm(forms.Form):
    player_action = forms.ChoiceField(choices=ACTION_CHOICES)
    selected_torbs = forms.ModelMultipleChoiceField(
        queryset=Torb.objects.none(), required=False
    )

    def __init__(self, *args, torb_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if torb_queryset is not None:
            self.fields["selected_torbs"].queryset = torb_queryset


class ArmyActionForm(forms.Form):
    action = forms.CharField(max_length=20)
    selected_colony = forms.IntegerField(required=False, widget=forms.HiddenInput)

