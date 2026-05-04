from django import forms
from django.contrib.auth.models import User
from .models import Livro, AreaConhecimento, PalavraChave
from django.contrib.auth.forms import UserCreationForm
import re

class CadastroUsuarioForm(forms.Form):
    nome = forms.CharField(max_length=255, label='Nome')
    username = forms.CharField(max_length=150, label='Nome de usuário')
    email = forms.EmailField(label='E-mail')
    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Senha'
    )
    confirmar_senha = forms.CharField(
        widget=forms.PasswordInput,
        label='Confirmar senha'
    )

    perfil_academico = forms.ChoiceField(
        choices=[
            ('discente_si', 'Discente de Sistemas de Informação'),
            ('discente_lc', 'Discente de Licenciatura em Computação'),
            ('docente', 'Docente'),
            ('pesquisador', 'Pesquisador'),
        ],
        label='Perfil acadêmico'
    )

    consentimento_recomendacao = forms.BooleanField(
        required=True,
        label='Li e aceito o Termo de Consentimento para uso dos meus dados nas recomendações acadêmicas.',
        error_messages={
            'required': 'Você precisa aceitar o Termo de Consentimento para concluir o cadastro.'
        }
    )

    def clean_username(self):
        username = self.cleaned_data['username']

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nome de usuário já está em uso.')

        return username

    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este e-mail já está em uso.')

        return email

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        
        # Garantir que password não é vazio
        if not password:
            raise forms.ValidationError('A senha é obrigatória.')
        
        if len(password) < 8:
            raise forms.ValidationError('A senha deve ter no mínimo 8 caracteres.')
        
        if not re.search(r'[A-Za-z]', password):
            raise forms.ValidationError('A senha deve conter pelo menos uma letra.')
        
        if not re.search(r'\d', password):
            raise forms.ValidationError('A senha deve conter pelo menos um número.')
        
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmar_senha = cleaned_data.get('confirmar_senha')

        if password and confirmar_senha and password != confirmar_senha:
            self.add_error(
                'confirmar_senha',
                'As senhas não coincidem.'
            )

        return cleaned_data

class LivroForm(forms.ModelForm):
    areas_conhecimento = forms.ModelMultipleChoiceField(
        queryset=AreaConhecimento.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Áreas de conhecimento"
    )
    
    palavras_chave = forms.ModelMultipleChoiceField(
        queryset=PalavraChave.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Palavras-chave"
    )

    class Meta:
        model = Livro
        fields = [
            'titulo',
            'autor',
            'isbn',
            'editora',
            'sinopse',
            'capa_url',
            'quantidade',
            'ano_publicacao',
            'areas_conhecimento',
            'palavras_chave',  
        ]

class AreaForm(forms.ModelForm):
    palavras_chave = forms.ModelMultipleChoiceField(
        queryset=PalavraChave.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Palavras-chave associadas"
    )

    class Meta:
        model = AreaConhecimento
        fields = ['nome', 'palavras_chave']


class PalavraChaveForm(forms.ModelForm):
    class Meta:
        model = PalavraChave
        fields = ['nome']


class UsuarioAreasForm(forms.Form):
    areas = forms.ModelMultipleChoiceField(
        queryset=AreaConhecimento.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Selecione suas áreas de interesse"
    )

class AtualizarUsuarioForm(forms.Form):
    nome = forms.CharField(max_length=255, label="Nome")
    username = forms.CharField(max_length=150, label="Nome de usuário")
    email = forms.EmailField(label="E-mail")
    
    perfil_academico = forms.ChoiceField(
        choices=[
            ('discente_si', 'Discente de Sistemas de Informação'),
            ('discente_lc', 'Discente de Licenciatura em Computação'),
            ('docente', 'Docente'),
            ('pesquisador', 'Pesquisador'),
        ],
        label="Perfil acadêmico",
        required=True
    )

    senha_atual = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="Senha atual"
    )
    nova_senha = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="Nova senha"
    )
    confirmar_nova_senha = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="Confirmar nova senha"
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if user:
            perfil = user.perfil
            self.fields['nome'].initial = getattr(perfil, 'nome', '')
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.email
            self.fields['perfil_academico'].initial = getattr(perfil, 'perfil_academico', 'discente_si')

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if not username:
            return username

        qs = User.objects.filter(username__iexact=username)

        if self.user:
            qs = qs.exclude(id=self.user.id)

        if qs.exists():
            raise forms.ValidationError('Este nome de usuário já está em uso.')

        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if not email:
            return email

        qs = User.objects.filter(email__iexact=email)

        if self.user:
            qs = qs.exclude(id=self.user.id)

        if qs.exists():
            raise forms.ValidationError('Este e-mail já está em uso.')

        return email

    def clean(self):
        cleaned_data = super().clean()
        senha_atual = cleaned_data.get('senha_atual')
        nova_senha = cleaned_data.get('nova_senha')
        confirmar_nova_senha = cleaned_data.get('confirmar_nova_senha')

        if nova_senha or confirmar_nova_senha:
            if not senha_atual:
                self.add_error(
                    'senha_atual',
                    'Informe sua senha atual para alterar a senha.'
                )

            if self.user and senha_atual and not self.user.check_password(senha_atual):
                self.add_error('senha_atual', 'Senha atual incorreta.')

            if not nova_senha:
                self.add_error('nova_senha', 'Informe a nova senha.')

            if not confirmar_nova_senha:
                self.add_error('confirmar_nova_senha', 'Confirme a nova senha.')

            if (
                nova_senha and
                confirmar_nova_senha and
                nova_senha != confirmar_nova_senha
            ):
                self.add_error(
                    'confirmar_nova_senha',
                    'As senhas não coincidem.'
                )

        return cleaned_data