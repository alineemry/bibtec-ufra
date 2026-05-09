from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from .models import AreaConhecimento, AreaPalavraChave, PalavraChave, UsuarioAreaInteresse, Usuario
from django.db.models import ProtectedError
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.core.paginator import Paginator

from core.services.google_books_service import buscar_livros_similares

from .forms import (
    LivroForm,
    AreaForm,
    PalavraChaveForm,
    UsuarioAreasForm,
    AtualizarUsuarioForm
)

from core.services.recomendacao_service import (
    get_recomendacoes_usuario,
    get_recomendacoes_similares_usuario
)
from core.forms import CadastroUsuarioForm
from core.models import (
    Usuario,
    AreaConhecimento,
    UsuarioAreaInteresse,
    Livro,
    InteracaoUsuario
)
from core.utils import usuario_tem_areas


# ============================================================
# AUTENTICAÇÃO
# ============================================================

def logout_usuario(request):
    """Realiza logout do usuário e redireciona para tela de login."""
    logout(request)
    return redirect('login')

def cadastro_usuario(request):
    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST)
        
        # DEBUG: veja o que está chegando
        print("Dados recebidos:", request.POST)
        
        if form.is_valid():
            print("Formulário válido!")
            
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            
            perfil = user.perfil
            perfil.nome = form.cleaned_data['nome']
            perfil.perfil_academico = form.cleaned_data['perfil_academico']
            perfil.tipo = 'autenticado'
            perfil.consentimento_recomendacao = form.cleaned_data['consentimento_recomendacao']
            perfil.data_consentimento = timezone.now()
            perfil.versao_termo_consentimento = '1.0'
            perfil.save()
            
            login(request, user)
            return redirect('core:selecionar_areas_interesse')
        else:
            # DEBUG: veja os erros
            print("Erros do formulário:", form.errors)
            
            # Adicionar mensagem de erro para o usuário
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = CadastroUsuarioForm()
    
    return render(request, 'core/cadastro.html', {'form': form})

# ============================================================
# FLUXO PRINCIPAL DO USUÁRIO
# ============================================================

@login_required
def pos_login(request):
    """
    Após login, verifica se usuário já selecionou áreas de interesse.
    """
    usuario = request.user.perfil

    if not usuario_tem_areas(usuario):
        return redirect('core:selecionar_areas_interesse')

    return redirect('core:recomendacoes')


@login_required
def recomendacoes_usuario(request):
    """
    Página inicial do sistema.
    Exibe livros disponíveis e recomendações personalizadas.
    """
    usuario = request.user.perfil

    if not usuario_tem_areas(usuario):
        return redirect('core:selecionar_areas_interesse')

    recomendacoes = get_recomendacoes_usuario(request.user.id)[:5]
    livros_acervo = Livro.objects.all()[:5]

    return render(request, 'core/home.html', {
        'recomendacoes': recomendacoes,
        'livros_acervo': livros_acervo
    })

# Todos os livros e todas as recomendações
@login_required
def todos_livros(request):
    """
    Lista completa de livros do acervo para usuários autenticados.
    """
    lista_livros = Livro.objects.all().order_by('titulo')
    paginator = Paginator(lista_livros, 15)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/todos_livros.html', {
        'page_obj': page_obj
    })

@login_required
def todas_recomendacoes(request):
    """
    Lista completa de recomendações personalizadas do usuário.
    """
    lista_recomendacoes = get_recomendacoes_usuario(request.user.id)
    paginator = Paginator(lista_recomendacoes, 15)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/todas_recomendacoes.html', {
        'page_obj': page_obj
    })

# ============================================================
# PERFIL DO USUÁRIO
# ============================================================
@login_required
def atualizar_perfil(request):
    """
    Permite ao usuário autenticado atualizar:
    nome, nome de usuário, e-mail, perfil acadêmico e senha.
    """
    user = request.user
    perfil = request.user.perfil

    if request.method == 'POST':
        form = AtualizarUsuarioForm(request.POST, user=user)

        if form.is_valid():
            user.username = form.cleaned_data['username']
            user.email = form.cleaned_data['email']
            user.save()

            perfil.nome = form.cleaned_data['nome']
            perfil.perfil_academico = form.cleaned_data['perfil_academico']  # NOVO
            perfil.save()

            nova_senha = form.cleaned_data.get('nova_senha')
            if nova_senha:
                user.set_password(nova_senha)
                user.save()
                login(request, user)
        
            messages.success(request, 'Seus dados foram atualizados com sucesso.')
            return redirect('core:meu_perfil')
    else:
        form = AtualizarUsuarioForm(user=user)

    return render(request, 'core/atualizar_perfil.html', {
        'form': form
    })
    
@login_required
def meu_perfil(request):
    """
    Exibe a área do perfil do usuário com seus dados
    e opções de gerenciamento.
    """
    perfil = request.user.perfil

    return render(request, 'core/meu_perfil.html', {
        'perfil_usuario': perfil,
        'user_auth': request.user,
    })
    
@login_required
def excluir_propria_conta(request):
    """
    Permite que o usuário autenticado exclua sua própria conta.
    Se for o último administrador, a exclusão não é permitida.
    """
    user = request.user

    if request.method == 'POST':
        if user.is_staff and User.objects.filter(is_staff=True).count() == 1:
            messages.error(
                request,
                'Não é possível excluir a conta do último administrador do sistema.'
            )
            return redirect('core:meu_perfil')

        logout(request)
        user.delete()

        messages.success(request, 'Sua conta foi excluída com sucesso.')
        return redirect('login')

    return render(request, 'core/excluir_conta_confirmar.html')

# ============================================================
# ÁREAS DE INTERESSE
# ============================================================

@login_required
def selecionar_areas_interesse(request):
    """
    Permite ao usuário selecionar suas áreas de interesse
    para personalização das recomendações.
    """
    usuario = request.user.perfil

    if request.method == 'POST':
        areas_ids = request.POST.getlist('areas')

        UsuarioAreaInteresse.objects.filter(usuario=usuario).delete()

        for area_id in areas_ids:
            UsuarioAreaInteresse.objects.create(
                usuario=usuario,
                area_id=area_id
            )

        return redirect('core:recomendacoes')

    areas = AreaConhecimento.objects.all()
    return render(request, 'core/selecionar_areas_interesse.html', {
        'areas': areas
    })

@login_required
def usuario_areas(request):
    usuario = request.user.perfil  # <- AQUI está a correção

    areas_iniciais = AreaConhecimento.objects.filter(
        usuarioareainteresse__usuario=usuario
    )

    if request.method == 'POST':
        form = UsuarioAreasForm(request.POST)
        if form.is_valid():
            UsuarioAreaInteresse.objects.filter(usuario=usuario).delete()

            for area in form.cleaned_data['areas']:
                UsuarioAreaInteresse.objects.create(
                    usuario=usuario,
                    area=area
                )

            messages.success(request, "Preferências atualizadas.")
            return redirect('core:recomendacoes')
    else:
        form = UsuarioAreasForm(initial={'areas': areas_iniciais})

    return render(request, 'core/usuario_areas.html', {'form': form})

# ============================================================
# LIVROS
# ============================================================
@login_required
def detalhe_livro(request, livro_id):
    livro = get_object_or_404(Livro, id=livro_id)
    usuario = request.user.perfil
    
    # Registrar visualização
    InteracaoUsuario.objects.create(
        usuario=usuario,
        livro=livro,
        tipo_interacao='visualizacao',
        peso=1,
        data_interacao=timezone.now()
    )
    
    # Estado atual na estante
    estado_atual = InteracaoUsuario.objects.filter(
        usuario=usuario,
        livro=livro,
        tipo_interacao__in=['quero_ler', 'lendo', 'lido']
    ).order_by('-data_interacao').first()
    
    # Recomendações
    recomendados = get_recomendacoes_similares_usuario(request.user.id, livro.id)
    recomendacoes_externas = buscar_livros_similares(livro.titulo, livro.autor, limite=4)
    
    voltar_url = request.META.get('HTTP_REFERER', '')
    
    mostrar_voltar = 'buscar' in voltar_url or 'busca' in voltar_url
    
    return render(request, 'core/detalhe_livro.html', {
        'livro': livro,
        'estado_atual': estado_atual.tipo_interacao if estado_atual else None,
        'recomendados': recomendados,
        'recomendacoes_externas': recomendacoes_externas,
        'voltar_url': voltar_url,  
        'mostrar_voltar': mostrar_voltar, 
    })
    
@login_required
def registrar_interacao(request, livro_id):
    """
    Registra interações do usuário com livros:
    visualização, quero ler, lendo ou lido.
    """
    if request.method != 'POST':
        return redirect('core:detalhe_livro', livro_id=livro_id)

    tipo = request.POST.get('tipo')

    if not tipo:
        return redirect('core:detalhe_livro', livro_id=livro_id)

    usuario = request.user.perfil
    livro = get_object_or_404(Livro, id=livro_id)

    PESOS_INTERACAO = {
        'visualizacao': 1,
        'quero_ler': 2,
        'lendo': 3,
        'lido': 5
    }

    peso = PESOS_INTERACAO.get(tipo, 0)

    # Se for mudança de estado, remove o anterior
    if tipo in ['quero_ler', 'lendo', 'lido']:
        InteracaoUsuario.objects.filter(
            usuario=usuario,
            livro=livro,
            tipo_interacao__in=['quero_ler', 'lendo', 'lido']
        ).delete()

    InteracaoUsuario.objects.create(
        usuario=usuario,
        livro=livro,
        tipo_interacao=tipo,
        peso=peso,
        data_interacao=timezone.now()
    )

    return redirect('core:detalhe_livro', livro_id=livro_id)


# ============================================================
# ESTANTE
# ============================================================

@login_required
def estante_usuario(request):
    """Exibe a estante do usuário organizada por status."""
    usuario = request.user.perfil

    estante = {
        'quero_ler': InteracaoUsuario.objects.filter(
            usuario=usuario,
            tipo_interacao='quero_ler'
        ).select_related('livro'),

        'lendo': InteracaoUsuario.objects.filter(
            usuario=usuario,
            tipo_interacao='lendo'
        ).select_related('livro'),

        'lido': InteracaoUsuario.objects.filter(
            usuario=usuario,
            tipo_interacao='lido'
        ).select_related('livro'),
    }

    return render(request, 'core/estante.html', {
        'estante': estante
    })

@login_required
def mover_interacao(request, livro_id):
    """Move um livro para outra categoria na estante"""
    if request.method != 'POST':
        return redirect('core:estante')
    
    livro = get_object_or_404(Livro, id=livro_id)
    usuario = request.user.perfil
    novo_status = request.POST.get('novo_status')
    
    if novo_status not in ['quero_ler', 'lendo', 'lido']:
        messages.error(request, 'Status inválido.')
        return redirect('core:estante')
    
    # Atualizar ou criar interação
    interacao, created = InteracaoUsuario.objects.update_or_create(
        usuario=usuario,
        livro=livro,
        defaults={
            'tipo_interacao': novo_status,
            'peso': PESOS_INTERACAO.get(novo_status, 1),
            'data_interacao': timezone.now()
        }
    )
    
    messages.success(request, f'Livro movido para "{novo_status}" com sucesso.')
    return redirect('core:estante')


@login_required
def remover_interacao(request, livro_id):
    """Remove um livro completamente da estante"""
    if request.method != 'POST':
        return redirect('core:estante')
    
    livro = get_object_or_404(Livro, id=livro_id)
    usuario = request.user.perfil
    
    # Remover todas as interações deste livro com este usuário
    InteracaoUsuario.objects.filter(usuario=usuario, livro=livro).delete()
    
    messages.success(request, 'Livro removido da sua estante.')
    return redirect('core:estante')

# ============================================================
# BUSCA
# ============================================================
@login_required
def buscar_livros(request):
    """
    Permite busca por título, autor, área do conhecimento ou palavra-chave.
    """
    termo = request.GET.get('q', '')
    area_id = request.GET.get('area')
    palavra_id = request.GET.get('palavra')
    page_number = request.GET.get('page', 1)

    livros = Livro.objects.all()

    # BUSCA TEXTUAL: título, autor, área ou palavra-chave
    if termo:
        livros = livros.filter(
            Q(titulo__icontains=termo) |
            Q(autor__icontains=termo) |
            Q(areas_conhecimento__nome__icontains=termo) |
            Q(palavras_chave__nome__icontains=termo)
        ).distinct()

    # Filtro específico por área (dropdown)
    if area_id:
        livros = livros.filter(areas_conhecimento__id=area_id)

    # Filtro específico por palavra-chave (dropdown)
    if palavra_id:
        livros = livros.filter(palavras_chave__id=palavra_id)

    # PAGINAÇÃO:
    paginator = Paginator(livros, 10)
    page_obj = paginator.get_page(page_number)

    # Buscar livros já visualizados pelo usuário
    livros_visualizados = set(
        InteracaoUsuario.objects.filter(
            usuario__user_id=request.user.id,
            tipo_interacao='visualizacao'
        ).values_list('livro_id', flat=True)
    )

    areas = AreaConhecimento.objects.all()
    palavras = PalavraChave.objects.all()

    return render(request, 'core/busca.html', {
        'page_obj': page_obj,  
        'termo': termo,
        'areas': areas,
        'area_selecionada': area_id,
        'palavras': palavras,
        'palavra_selecionada': palavra_id,
        'livros_visualizados': livros_visualizados,
    })

# ============================================================
# ÁREA ADMINISTRATIVA (APENAS STAFF)
# ============================================================

@staff_member_required
def admin_livros_lista(request):
    termo = request.GET.get('q', '').strip()

    livros = Livro.objects.all().order_by('titulo')

    if termo:
        livros = livros.filter(
            Q(titulo__icontains=termo) |
            Q(autor__icontains=termo) |
            Q(isbn__icontains=termo)
        )

    # Paginação: 
    paginator = Paginator(livros, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/livros_lista.html', {
        'page_obj': page_obj,
        'termo': termo
    })

@staff_member_required
def admin_livro_criar(request):
    if request.method == 'POST':
        form = LivroForm(request.POST)
        if form.is_valid():
            livro = form.save()
            
            # Salvar áreas
            livro.areas_conhecimento.set(form.cleaned_data['areas_conhecimento'])
            
            # Salvar palavras-chave
            livro.palavras_chave.set(form.cleaned_data['palavras_chave'])
            
            return redirect('core:admin_livros_lista')
    else:
        form = LivroForm()
    
    return render(request, 'core/livro_form.html', {'form': form})


@staff_member_required
def admin_livro_editar(request, id):
    livro = get_object_or_404(Livro, pk=id)
    
    if request.method == 'POST':
        form = LivroForm(request.POST, instance=livro)
        if form.is_valid():
            livro = form.save()
            
            # Salvar áreas
            livro.areas_conhecimento.set(form.cleaned_data['areas_conhecimento'])
            
            # ADICIONE: Salvar palavras-chave
            livro.palavras_chave.set(form.cleaned_data['palavras_chave'])
            
            return redirect('core:admin_livros_lista')
    else:
        form = LivroForm(instance=livro)
    
    return render(request, 'core/livro_form.html', {'form': form})

@staff_member_required
def admin_livro_excluir(request, id):
    livro = get_object_or_404(Livro, pk=id)

    if request.method == 'POST':
        livro.delete()
        return redirect('core:admin_livros_lista')

    return render(request, 'core/livro_confirm_delete.html', {'livro': livro})

# ADMINISTRAÇÃO DE USUÁRIOS

@staff_member_required
def admin_usuarios_lista(request):
    termo = request.GET.get('q', '').strip()

    usuarios = User.objects.all().order_by('username')

    if termo:
        usuarios = usuarios.filter(
            Q(username__icontains=termo) |
            Q(email__icontains=termo)
        )

    # Paginação: 
    paginator = Paginator(usuarios, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/usuarios_lista.html', {
        'page_obj': page_obj,
        'termo': termo
    })

@staff_member_required
def admin_usuario_promover(request, id):
    usuario = get_object_or_404(User, id=id)

    if not usuario.is_superuser:
        usuario.is_staff = True
        usuario.save()
        messages.success(request, "Usuário promovido a administrador.")

    return redirect('core:admin_usuarios_lista')

@staff_member_required
def admin_usuario_rebaixar(request, id):
    usuario = get_object_or_404(User, id=id)

    if usuario == request.user:
        messages.error(request, "Você não pode remover seus próprios privilégios.")
        return redirect('core:admin_usuarios_lista')

    if usuario.is_superuser:
        messages.error(request, "Não é possível rebaixar um superusuário.")
        return redirect('core:admin_usuarios_lista')

    usuario.is_staff = False
    usuario.save()

    messages.warning(request, "Usuário removido da administração.")
    return redirect('core:admin_usuarios_lista')

@staff_member_required
def admin_usuario_excluir(request, id):
    usuario = get_object_or_404(User, id=id)

    # Não permitir excluir a própria conta
    if usuario == request.user:
        messages.error(request, "Você não pode excluir sua própria conta.")
        return redirect('core:admin_usuarios_lista')

    # Não permitir excluir superusuário
    if usuario.is_superuser:
        messages.error(request, "Não é possível excluir um superusuário.")
        return redirect('core:admin_usuarios_lista')

    # Só verifica quantidade de admins SE o usuário for admin
    if usuario.is_staff:
        total_admins = User.objects.filter(is_staff=True).count()

        if total_admins == 1:
            messages.error(request, "Não é possível remover o último administrador.")
            return redirect('core:admin_usuarios_lista')

    usuario.delete()
    messages.success(request, "Usuário excluído com sucesso.")

    return redirect('core:admin_usuarios_lista')



# ADMINISTRAÇÃO DE ÁREAS E PALAVRAS-CHAVE
@staff_member_required
def admin_areas_lista(request):
    termo = request.GET.get('q', '').strip()

    areas = AreaConhecimento.objects.all().order_by('nome')

    if termo:
        areas = areas.filter(nome__icontains=termo)

    # Paginação: 
    paginator = Paginator(areas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/areas_lista.html', {
        'page_obj': page_obj,
        'termo': termo
    })
    
@staff_member_required
def admin_area_criar(request):
    if request.method == 'POST':
        form = AreaForm(request.POST)
        if form.is_valid():
            area = form.save()

            palavras = form.cleaned_data['palavras_chave']
            for palavra in palavras:
                AreaPalavraChave.objects.create(
                    area=area,
                    palavra_chave=palavra
                )

            messages.success(request, "Área criada com sucesso.")
            return redirect('core:admin_areas_lista')
    else:
        form = AreaForm()

    return render(request, 'core/area_form.html', {'form': form})

@staff_member_required
def admin_area_editar(request, id):
    area = get_object_or_404(AreaConhecimento, id=id)

    palavras_iniciais = PalavraChave.objects.filter(
        areapalavrachave__area=area
    )

    if request.method == 'POST':
        form = AreaForm(request.POST, instance=area)
        if form.is_valid():
            area = form.save()

            # limpar relações antigas
            AreaPalavraChave.objects.filter(area=area).delete()

            # recriar com base no formulário
            palavras = form.cleaned_data['palavras_chave']
            for palavra in palavras:
                AreaPalavraChave.objects.create(
                    area=area,
                    palavra_chave=palavra
                )

            messages.success(request, "Área atualizada.")
            return redirect('core:admin_areas_lista')
    else:
        form = AreaForm(
            instance=area,
            initial={'palavras_chave': palavras_iniciais}
        )

    return render(request, 'core/area_form.html', {'form': form})

@staff_member_required
def admin_area_excluir(request, id):
    area = get_object_or_404(AreaConhecimento, id=id)

    try:
        area.delete()
    except IntegrityError:
        messages.error(
            request,
            "Não é possível excluir esta área porque ela está associada a livros."
        )
        return redirect('core:admin_areas_lista')

    messages.success(request, "Área excluída com sucesso.")
    return redirect('core:admin_areas_lista')

@staff_member_required
def admin_palavras_lista(request):
    termo = request.GET.get('q', '').strip()

    palavras = PalavraChave.objects.all().order_by('nome')

    if termo:
        palavras = palavras.filter(nome__icontains=termo)

    # Paginação: 10 palavras por página
    paginator = Paginator(palavras, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/palavras_lista.html', {
        'page_obj': page_obj,
        'termo': termo
    })

@staff_member_required
def admin_palavra_criar(request):
    if request.method == 'POST':
        form = PalavraChaveForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Palavra-chave cadastrada.")
            return redirect('core:admin_palavras_lista')
    else:
        form = PalavraChaveForm()

    return render(request, 'core/palavras_form.html', {
        'form': form
    })


@staff_member_required
def admin_palavra_editar(request, id):
    palavra = get_object_or_404(PalavraChave, id=id)

    if request.method == 'POST':
        form = PalavraChaveForm(request.POST, instance=palavra)
        if form.is_valid():
            form.save()
            messages.success(request, "Palavra-chave atualizada.")
            return redirect('core:admin_palavras_lista')
    else:
        form = PalavraChaveForm(instance=palavra)

    return render(request, 'core/palavras_form.html', {
        'form': form
    })

@staff_member_required
def admin_palavra_excluir(request, id):
    palavra = get_object_or_404(PalavraChave, id=id)

    if AreaPalavraChave.objects.filter(palavra_chave=palavra).exists():
        messages.error(
            request,
            "Não é possível excluir: palavra vinculada a áreas."
        )
        return redirect('core:admin_palavras_lista')

    palavra.delete()
    messages.success(request, "Palavra-chave excluída.")
    return redirect('core:admin_palavras_lista')

# RECUPERAÇÃO DE SENHA
"""
class RecuperarSenhaView(auth_views.PasswordResetView):
    template_name = 'core/recuperar_senha.html'
    email_template_name = 'core/emails/recuperar_senha_email.txt'
    subject_template_name = 'core/emails/recuperar_senha_subject.txt'
    success_url = reverse_lazy('core:recuperar_senha_enviado')


class RecuperarSenhaEnviadoView(auth_views.PasswordResetDoneView):
    template_name = 'core/recuperar_senha_enviado.html'


class RedefinirSenhaView(auth_views.PasswordResetConfirmView):
    template_name = 'core/redefinir_senha.html'
    success_url = reverse_lazy('core:redefinir_senha_concluido')


class RedefinirSenhaConcluidoView(auth_views.PasswordResetCompleteView):
    template_name = 'core/redefinir_senha_concluido.html'
"""

# USUÁRIO CONVIDADO (PÚBLICO)  

def todos_livros_publico(request):
    """
    Lista completa de livros do acervo para visitantes.
    """
    lista_livros = Livro.objects.all().order_by('titulo')
    paginator = Paginator(lista_livros, 15)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/todos_livros_publico.html', {
        'page_obj': page_obj
    })
    
def pagina_inicial_convidado(request):
    """
    Página inicial pública para visitantes.
    Exibe apenas livros disponíveis no acervo.
    """
    
    lista_livros = Livro.objects.all().order_by('titulo')
    paginator = Paginator(lista_livros, 15)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/home_convidado.html', {
        'page_obj': page_obj
    })

def buscar_livros_publico(request):
    """
    Busca pública para visitantes.
    Permite busca por título, autor e área do conhecimento.
    """
    termo = request.GET.get('q', '')
    area_id = request.GET.get('area')

    livros = Livro.objects.all()

    if termo:
        livros = livros.filter(
            Q(titulo__icontains=termo) |
            Q(autor__icontains=termo)
        ).distinct()

    if area_id:
        livros = livros.filter(
            areas_conhecimento__id=area_id
        ).distinct()

    areas = AreaConhecimento.objects.all()

    return render(request, 'core/busca_publica.html', {
        'livros': livros,
        'termo': termo,
        'areas': areas,
        'area_selecionada': area_id
    })

def detalhe_livro_publico(request, livro_id):
    """
    Exibe detalhes do livro para visitante,
    sem registrar interações e sem recomendações personalizadas.
    """
    livro = get_object_or_404(Livro, id=livro_id)

    return render(request, 'core/detalhe_livro_publico.html', {
        'livro': livro
    })

def recuperar_senha_indisponivel(request):
    return render(request, 'core/recuperar_senha_indisponivel.html')