from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Usuario


class Command(BaseCommand):
    help = 'Sincroniza auth_user com a tabela usuario'

    def handle(self, *args, **options):
        total_criados = 0

        for user in User.objects.all():
            if not hasattr(user, 'perfil'):
                # define tipo
                if Usuario.objects.count() == 0:
                    tipo = 'admin'
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()
                else:
                    tipo = 'autenticado'

                Usuario.objects.create(
                    user=user,
                    nome=user.username,
                    tipo=tipo,
                    perfil_academico='Não informado'
                )

                total_criados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Perfil criado para: {user.username}')
                )

        if total_criados == 0:
            self.stdout.write(
                self.style.WARNING('Nenhum usuário precisava de perfil.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Total de perfis criados: {total_criados}')
            )
