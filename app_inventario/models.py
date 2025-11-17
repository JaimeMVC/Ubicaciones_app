from django.db import models

class LocationCheck(models.Model):
    pn=models.CharField(max_length=50)
    ubicacion=models.CharField(max_length=50)
    descripcion=models.CharField(max_length=255, blank=True, null=True)
    is_checked=models.BooleanField(default=False)
    checked_at=models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together=('pn','ubicacion')
        ordering=['pn','ubicacion']
        
class ResultSnapshot(models.Model):
    pn = models.CharField(max_length=50)
    total = models.IntegerField()
    revisadas = models.IntegerField()
    porcentaje = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.pn} | {self.porcentaje}% | {self.created_at.strftime('%Y-%m-%d %H:%M')}"
