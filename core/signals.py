from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Usuario

@receiver(post_save, sender=User)
def criar_usuario_automatico(sender, instance, created, **kwargs):
    if not created:
        return

    # primeiro usuário vira admin
    if User.objects.count() == 1:
        tipo = 'admin'
        instance.is_staff = True
        instance.is_superuser = True
        instance.save()
    else:
        tipo = 'autenticado'

    Usuario.objects.create(
        user=instance,
        nome=instance.username,  # depois você pode melhorar isso
        tipo=tipo,
        perfil_academico='Não informado'
    )