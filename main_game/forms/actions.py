from typing import cast

from django import forms


class ColonyActionForm(forms.Form):
    player_action = forms.CharField()
    selected_torbs = forms.TypedMultipleChoiceField(coerce=int, required=False)

    def __init__(self, *args, torbs=(), **kwargs):
        super().__init__(*args, **kwargs)
        field = cast(forms.TypedMultipleChoiceField, self.fields["selected_torbs"])
        field.choices = [(torb.pk, torb.pk) for torb in torbs]


class ArmyActionForm(forms.Form):
    player_action = forms.CharField()
    selected_colony = forms.IntegerField(required=False)


class LabActionForm(ColonyActionForm):
    science_points_used = forms.IntegerField(required=False, min_value=0)
    discovery_id = forms.IntegerField(required=False)
