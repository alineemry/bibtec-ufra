from django.db.models import Count
from django.utils import timezone
from core.models import (
    InteracaoUsuario,
    UsuarioAreaInteresse,
    Livro,
)

# ==========================================
# CONSTANTES
# ==========================================
BONUS_AREA_INTERESSE = 3
BONUS_POPULARIDADE_MAX = 3

BONUS_PERFIL_ACADEMICO = {
    'discente_si': {
        'Engenharia de Software': 3,
        'Gestão de TI': 3,
        'Banco de Dados': 2,
        'Sistemas de Informação': 2,
    },
    'discente_lc': {
        'Educação e Tecnologia': 3,
        'Ensino de Programação': 3,
        'Metodologias de Ensino': 2,
        'Tecnologias Educacionais': 2,
    },
    'docente': {
        'Metodologias Ativas': 3,
        'Avaliação Educacional': 2,
        'Didática da Computação': 3,
        'Tecnologias Assistivas': 2,
    },
    'pesquisador': {
        'Inteligência Artificial': 3,
        'Machine Learning': 3,
        'Data Science': 3,
        'Métodos de Pesquisa': 2,
    },
}


# ==========================================
# FUNÇÃO PARA CALCULAR PESO TEMPORAL
# ==========================================
def calcular_peso_temporal(data_interacao):
    if not data_interacao:
        return 0.5
    
    agora = timezone.now()
    
    if timezone.is_naive(data_interacao):
        data_interacao = timezone.make_aware(data_interacao)
    
    dias_desde_interacao = (agora - data_interacao).days
    
    if dias_desde_interacao <= 30:
        return 1.0
    elif dias_desde_interacao <= 180:
        return 0.7
    elif dias_desde_interacao <= 365:
        return 0.4
    else:
        return 0.2


# ==========================================
# FUNÇÃO AUXILIAR: PALAVRAS DO LIVRO
# ==========================================
def get_palavras_livro(livro):
    return list(livro.palavras_chave.values_list('id', flat=True))


# ==========================================
# PERFIL DO USUÁRIO (USANDO PESO DO BANCO)
# ==========================================
def construir_perfil_usuario(user_id, perfil_academico=None):
    interacoes = InteracaoUsuario.objects.filter(usuario__user_id=user_id)

    perfil = {'areas': {}, 'palavras': {}}

    for interacao in interacoes:
        peso_base = interacao.peso
        peso_temporal = calcular_peso_temporal(interacao.data_interacao)
        peso_final = peso_base * peso_temporal
        
        livro = interacao.livro

        for area in livro.areas_conhecimento.all():
            perfil['areas'][area.id] = perfil['areas'].get(area.id, 0) + peso_final

        for palavra_id in get_palavras_livro(livro):
            perfil['palavras'][palavra_id] = perfil['palavras'].get(palavra_id, 0) + peso_final

    return perfil

# ==========================================
# SCORE DE CONTEÚDO (NORMALIZADO)
# ==========================================
def calcular_score_livro(perfil, livro, perfil_academico=None):
    """
    Calcula o score do livro baseado no perfil do usuário.
    """
    scores_areas = []
    scores_palavras = []

    # Score baseado em interações
    for area in livro.areas_conhecimento.all():
        score_area = perfil['areas'].get(area.id, 0)
        if score_area > 0:
            scores_areas.append(score_area)

    for palavra_id in get_palavras_livro(livro):
        score_palavra = perfil['palavras'].get(palavra_id, 0)
        if score_palavra > 0:
            scores_palavras.append(score_palavra)

    media_areas = sum(scores_areas) / len(scores_areas) if scores_areas else 0
    media_palavras = sum(scores_palavras) / len(scores_palavras) if scores_palavras else 0

    score = media_areas + (media_palavras * 2)

    # Bônus por perfil acadêmico
    if perfil_academico:
        bonus_perfil = BONUS_PERFIL_ACADEMICO.get(perfil_academico, {})
        for area in livro.areas_conhecimento.all():
            score += bonus_perfil.get(area.nome, 0)

    return score

# ==========================================
# EXPLICAÇÃO
# ==========================================
def explicar_recomendacao(perfil, livro, interacoes_usuario=None):
    """
    Gera uma explicação clara do porquê o livro foi recomendado.
    """
    motivos = []
    
    # Verificar áreas em comum
    for area in livro.areas_conhecimento.all():
        if area.id in perfil['areas']:
            score_area = perfil['areas'][area.id]
            motivos.append(f"Você se interessou por {area.nome}")
    
    # Verificar palavras-chave em comum
    for palavra_id in get_palavras_livro(livro):
        if palavra_id in perfil['palavras']:
            from core.models import PalavraChave
            try:
                palavra = PalavraChave.objects.get(id=palavra_id)
                motivos.append(f"Conteúdo relacionado a '{palavra.nome}'")
            except:
                pass
    
    # Se não houver motivos específicos, usar popularidade
    if not motivos:
        motivos.append("Livro popular entre outros usuários")
    
    # Retornar motivos únicos (sem duplicatas) e limitar a 3
    motivos_unicos = []
    for motivo in motivos:
        if motivo not in motivos_unicos:
            motivos_unicos.append(motivo)
    
    return motivos_unicos[:1]


# ==========================================
# POPULARIDADE (COLD START)
# ==========================================
def get_livros_populares(limite=10):
    livros = Livro.objects.annotate(total=Count('interacaousuario')).order_by('-total')[:limite]
    for livro in livros:
        livro.score = livro.total
        livro.explicacao = []
    return livros


# ==========================================
# RECOMENDAÇÃO PRINCIPAL
# ==========================================
def get_recomendacoes_usuario(user_id, limite=10):
    from core.models import Usuario as PerfilUsuario
    
    # Buscar perfil do usuário para obter o perfil_academico
    try:
        perfil_usuario = PerfilUsuario.objects.get(user_id=user_id)
        perfil_academico = perfil_usuario.perfil_academico
    except PerfilUsuario.DoesNotExist:
        perfil_academico = None
    
    perfil = construir_perfil_usuario(user_id, perfil_academico)

    livros_lidos = set(
        InteracaoUsuario.objects.filter(
            usuario__user_id=user_id,
            tipo_interacao='lido'
        ).values_list('livro_id', flat=True)
    )

    # Se não tem interações mas tem áreas de interesse
    if not perfil['areas'] and not perfil['palavras']:
        # Verificar se o usuário selecionou áreas de interesse
        areas_interesse = UsuarioAreaInteresse.objects.filter(
            usuario__user_id=user_id
        ).values_list('area_id', flat=True)
        
        if areas_interesse:
            # Criar perfil artificial baseado nas áreas de interesse
            for area_id in areas_interesse:
                perfil['areas'][area_id] = BONUS_AREA_INTERESSE
        else:
            # Sem nada: retorna populares
            return get_livros_populares(limite)

    livros = Livro.objects.annotate(total_interacoes=Count('interacaousuario'))

    recomendacoes = []

    for livro in livros:
        if livro.id in livros_lidos:
            continue

        score = calcular_score_livro(perfil, livro, perfil_academico)
        score += min(livro.total_interacoes, BONUS_POPULARIDADE_MAX)

        if score > 0:
            livro.score = score
            livro.explicacao = explicar_recomendacao(perfil, livro)
            recomendacoes.append(livro)

    recomendacoes.sort(key=lambda l: l.score, reverse=True)
    return recomendacoes[:limite]

# ==========================================
# SIMILARIDADE
# ==========================================
def calcular_similaridade(livro1, livro2):
    score = 0

    areas1 = set(livro1.areas_conhecimento.values_list('id', flat=True))
    areas2 = set(livro2.areas_conhecimento.values_list('id', flat=True))
    score += len(areas1 & areas2) * 2

    palavras1 = set(get_palavras_livro(livro1))
    palavras2 = set(get_palavras_livro(livro2))
    score += len(palavras1 & palavras2) * 8

    return score


def get_recomendacoes_similares_usuario(user_id, livro_id, limite=5):
    livro_base = Livro.objects.get(id=livro_id)

    areas_base = set(livro_base.areas_conhecimento.values_list('id', flat=True))
    palavras_base = set(get_palavras_livro(livro_base))

    livros = Livro.objects.exclude(id=livro_id)
    similares = []

    for livro in livros:
        areas_livro = set(livro.areas_conhecimento.values_list('id', flat=True))
        palavras_livro = set(get_palavras_livro(livro))

        score = len(areas_base & areas_livro) * 2 + len(palavras_base & palavras_livro) * 8

        if score > 0:
            livro.score = score
            similares.append(livro)

    similares.sort(key=lambda l: l.score, reverse=True)
    return similares[:limite]