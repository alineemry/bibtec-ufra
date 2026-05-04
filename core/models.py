from django.db import models
from django.contrib.auth.models import User

class Usuario(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil'
    )

    nome = models.CharField(max_length=255)

    tipo = models.CharField(
        max_length=30,
        choices=[
            ('visitante', 'Visitante'),
            ('autenticado', 'Usuário autenticado'),
            ('admin', 'Administrador'),
        ],
        default='autenticado'
    )

    perfil_academico = models.CharField(max_length=100)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    consentimento_recomendacao = models.BooleanField(default=False)
    data_consentimento = models.DateTimeField(null=True, blank=True)
    versao_termo_consentimento = models.CharField(max_length=20, default='1.0')

    class Meta:
        db_table = 'usuario'

# -------------------------------
# ÁREAS DE CONHECIMENTO
# -------------------------------
class AreaConhecimento(models.Model):
    nome = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'area_conhecimento'

    def __str__(self):
        return self.nome
    
# -------------------------------
# PALAVRAS-CHAVE
# -------------------------------
class PalavraChave(models.Model):
    nome = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'palavra_chave'
        managed = False

    def __str__(self):
        return self.nome
    
# ============================================
# RELAÇÃO ÁREA ↔ PALAVRA-CHAVE 
# ============================================
class AreaPalavraChave(models.Model):
    area = models.ForeignKey(
        'AreaConhecimento',
        on_delete=models.CASCADE,
        db_column='area_id'
    )
    palavra_chave = models.ForeignKey(
        'PalavraChave',
        on_delete=models.CASCADE,
        db_column='palavra_chave_id'
    )

    class Meta:
        db_table = 'core_areapalavrachave'
        managed = False

# ============================================
# RELAÇÃO LIVRO ↔ PALAVRA-CHAVE 
# ============================================
class LivroPalavraChave(models.Model):
    id = models.AutoField(primary_key=True)  
    livro = models.ForeignKey(
        'Livro',
        on_delete=models.CASCADE,
        db_column='livro_id'
    )
    palavra_chave = models.ForeignKey(
        'PalavraChave',
        on_delete=models.CASCADE,
        db_column='palavra_chave_id'
    )

    class Meta:
        managed = False
        db_table = 'livro_palavra_chave'
        unique_together = ('livro', 'palavra_chave')

# -------------------------------
# LIVROS
# -------------------------------
class Livro(models.Model):
    id = models.AutoField(primary_key=True)

    titulo = models.CharField(max_length=255)
    autor = models.CharField(max_length=255, null=True, blank=True)
    isbn = models.CharField(max_length=20, null=True, blank=True)
    editora = models.CharField(max_length=255, null=True, blank=True)
    sinopse = models.TextField(null=True, blank=True)
    capa_url = models.CharField(max_length=255, null=True, blank=True)
    quantidade = models.IntegerField(null=True, blank=True)
    ano_publicacao = models.IntegerField(null=True, blank=True)
    data_cadastro = models.DateField(auto_now_add=True)

    areas_conhecimento = models.ManyToManyField(
        'AreaConhecimento',
        through='LivroAreaConhecimento',
        through_fields=('livro', 'area'),
        related_name='livros'
    )
    
    palavras_chave = models.ManyToManyField(
        'PalavraChave',
        through='LivroPalavraChave',
        related_name='livros'
    )

    class Meta:
        managed = False
        db_table = 'livro'

# -------------------------------
# RELAÇÃO LIVRO ↔ ÁREA DE CONHECIMENTO
# -------------------------------
class LivroAreaConhecimento(models.Model):
    livro = models.ForeignKey(
        'Livro',
        on_delete=models.CASCADE,
        db_column='livro_id'
    )
    area = models.ForeignKey(
        'AreaConhecimento',
        on_delete=models.CASCADE,
        db_column='area_id'
    )

    class Meta:
        managed = False
        db_table = 'livro_area_conhecimento'


# -------------------------------
# INTERAÇÕES
# -------------------------------
class InteracaoUsuario(models.Model):
    usuario = models.ForeignKey(
        'Usuario',
        on_delete=models.CASCADE,
        db_column='usuario_id'
    )
    livro = models.ForeignKey(
        'Livro',
        on_delete=models.CASCADE,
        db_column='livro_id'
    )
    tipo_interacao = models.CharField(max_length=20)
    peso = models.IntegerField()
    data_interacao = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'interacao_usuario'


# -------------------------------
# VIEW DE RECOMENDAÇÃO
# -------------------------------
class RecomendacaoLivro(models.Model):
    usuario_id = models.IntegerField()
    livro_id = models.IntegerField(primary_key=True)
    titulo_livro = models.CharField(max_length=255)
    areas_conhecimento = models.CharField(max_length=255)
    score_final = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'vw_recomendacao_livros'


# -------------------------------
# INTERESSE DO USUÁRIO
# -------------------------------
class UsuarioAreaInteresse(models.Model):
    usuario = models.ForeignKey(
        'Usuario',
        on_delete=models.CASCADE,
        db_column='usuario_id'
    )
    area = models.ForeignKey(
        'AreaConhecimento',
        on_delete=models.CASCADE,
        db_column='area_conhecimento_id'
    )

    class Meta:
        managed = False
        db_table = 'usuario_area_interesse'
        unique_together = ('usuario', 'area')