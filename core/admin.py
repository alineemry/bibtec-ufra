from django.contrib import admin
from django import forms
from .models import Livro, AreaConhecimento, Usuario, PalavraChave, LivroPalavraChave

# Formulário personalizado para o admin de livros
class LivroAdminForm(forms.ModelForm):
    areas_conhecimento = forms.ModelMultipleChoiceField(
        queryset=AreaConhecimento.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple('Áreas', is_stacked=False),
        required=False,
        label="Áreas de conhecimento"
    )
    
    palavras_chave = forms.ModelMultipleChoiceField(
        queryset=PalavraChave.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple('Palavras-chave', is_stacked=False),
        required=False,
        label="Palavras-chave"
    )
    
    class Meta:
        model = Livro
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['areas_conhecimento'].initial = self.instance.areas_conhecimento.all()
            self.fields['palavras_chave'].initial = self.instance.palavras_chave.all()
    
    def save(self, commit=True):
        livro = super().save(commit=commit)
        if commit:
            livro.areas_conhecimento.set(self.cleaned_data['areas_conhecimento'])
            livro.palavras_chave.set(self.cleaned_data['palavras_chave'])
        return livro

# 📚 Livro Admin
@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    form = LivroAdminForm
    list_display = ('titulo', 'autor', 'editora', 'ano_publicacao')
    search_fields = ('titulo', 'autor')
    list_filter = ('areas_conhecimento',)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form

# 🧠 Áreas
@admin.register(AreaConhecimento)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

# 🏷️ Palavras-chave 
@admin.register(PalavraChave)
class PalavraChaveAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

# 👤 Usuário
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'nome', 'perfil_academico')