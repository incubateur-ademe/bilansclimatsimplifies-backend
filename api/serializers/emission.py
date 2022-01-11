from rest_framework import serializers
from data.models import Emission


class EmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emission
        fields = ["id", "bilan", "poste", "type", "localisation", "valeur", "unite", "note", "resultat"]
        read_only_fields = ["id", "resultat"]
