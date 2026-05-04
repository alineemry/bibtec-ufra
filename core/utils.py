from core.models import UsuarioAreaInteresse

def usuario_tem_areas(usuario):
    return UsuarioAreaInteresse.objects.filter(usuario=usuario).exists()
