from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('cadastro/', views.cadastro_usuario, name='cadastro'),
    path('pos-login/', views.pos_login, name='pos_login'),
    path('recomendacoes/', views.recomendacoes_usuario, name='recomendacoes'),
    path('selecionar-areas-interesse/', views.selecionar_areas_interesse, name='selecionar_areas_interesse'),
    path('livro/<int:livro_id>/', views.detalhe_livro, name='detalhe_livro'),
    path('livro/<int:livro_id>/interacao/', views.registrar_interacao, name='registrar_interacao'),
    path('estante/', views.estante_usuario, name='estante'),
    path('estante/mover/<int:livro_id>/', views.mover_interacao, name='mover_interacao'),
    path('estante/remover/<int:livro_id>/', views.remover_interacao, name='remover_interacao'),
    path('buscar/', views.buscar_livros, name='buscar_livros'),
    path('logout/', views.logout_usuario, name='logout'),
    path('minhas-areas/', views.usuario_areas, name='usuario_areas'),
    
    path('livros/', views.todos_livros, name='todos_livros'),
    path('recomendacoes/todas/', views.todas_recomendacoes, name='todas_recomendacoes'),

    # perfil do usuário
    path('perfil/', views.meu_perfil, name='meu_perfil'),
    path('perfil/editar/', views.atualizar_perfil, name='atualizar_perfil'),
    path('perfil/excluir/', views.excluir_propria_conta, name='excluir_propria_conta'),

    # painel admin do sistema
    path('usuarios/', views.admin_usuarios_lista, name='admin_usuarios_lista'),
    path('usuarios/promover/<int:id>/', views.admin_usuario_promover, name='admin_usuario_promover'),
    path('usuarios/rebaixar/<int:id>/', views.admin_usuario_rebaixar, name='admin_usuario_rebaixar'),
    path('usuarios/excluir/<int:id>/', views.admin_usuario_excluir, name='admin_usuario_excluir'),

    path('painel/livros/', views.admin_livros_lista, name='admin_livros_lista'),
    path('painel/livros/novo/', views.admin_livro_criar, name='admin_livro_criar'),
    path('painel/livros/editar/<int:id>/', views.admin_livro_editar, name='admin_livro_editar'),
    path('painel/livros/excluir/<int:id>/', views.admin_livro_excluir, name='admin_livro_excluir'),

    path('painel/areas/', views.admin_areas_lista, name='admin_areas_lista'),
    path('painel/areas/nova/', views.admin_area_criar, name='admin_area_criar'),
    path('painel/areas/editar/<int:id>/', views.admin_area_editar, name='admin_area_editar'),
    path('painel/areas/excluir/<int:id>/', views.admin_area_excluir, name='admin_area_excluir'),

    path('painel/palavras/', views.admin_palavras_lista, name='admin_palavras_lista'),
    path('painel/palavras/nova/', views.admin_palavra_criar, name='admin_palavra_criar'),
    path('painel/palavras/editar/<int:id>/', views.admin_palavra_editar, name='admin_palavra_editar'),
    path('painel/palavras/excluir/<int:id>/', views.admin_palavra_excluir, name='admin_palavra_excluir'),

    # recuperação de senha
    path('recuperar-senha/', views.recuperar_senha_indisponivel, name='recuperar_senha'),
    
    
    # path('recuperar-senha/', views.RecuperarSenhaView.as_view(), name='recuperar_senha'),
    # path('recuperar-senha/enviado/', views.RecuperarSenhaEnviadoView.as_view(), name='recuperar_senha_enviado'),
    # path('redefinir-senha/<uidb64>/<token>/', views.RedefinirSenhaView.as_view(), name='redefinir_senha'),
    # path('redefinir-senha/concluido/', views.RedefinirSenhaConcluidoView.as_view(), name='redefinir_senha_concluido'),
    
    
    # usuário convidado
    path('convidado/', views.pagina_inicial_convidado, name='pagina_inicial_convidado'),
    path('convidado/buscar/', views.buscar_livros_publico, name='buscar_livros_publico'),
    path('convidado/livro/<int:livro_id>/', views.detalhe_livro_publico, name='detalhe_livro_publico'),
    path('convidado/livros/', views.todos_livros_publico, name='todos_livros_publico'),
]