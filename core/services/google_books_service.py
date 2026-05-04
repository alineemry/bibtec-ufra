import requests
from django.conf import settings

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"


def buscar_livros_similares(titulo, autor=None, limite=4):
    """
    Busca livros similares na API do Google Books baseado no título e autor.
    """
    if not titulo:
        return []
    
    # Construir query de busca
    query = f'intitle:{titulo}'
    if autor:
        query += f'+inauthor:{autor}'
    
    params = {
        'q': query,
        'maxResults': limite,
        'key': settings.GOOGLE_BOOKS_API_KEY,
        'langRestrict': 'pt',
        'orderBy': 'relevance'
    }
    
    try:
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params, timeout=5)
        response.raise_for_status()
        dados = response.json()
        
        livros = []
        for item in dados.get('items', []):
            volume_info = item.get('volumeInfo', {})
            
            # Extrair informações
            titulo_livro = volume_info.get('title', 'Título não disponível')
            autores = volume_info.get('authors', ['Autor não informado'])
            descricao = volume_info.get('description', '')
            capa = volume_info.get('imageLinks', {}).get('thumbnail', '')
            link = volume_info.get('infoLink', '#')
            
            # Evitar duplicar o livro atual
            if titulo_livro.lower() == titulo.lower():
                continue
            
            livros.append({
                'titulo': titulo_livro,
                'autor': ', '.join(autores),
                'descricao': descricao[:200] + '...' if len(descricao) > 200 else descricao,
                'capa_url': capa,
                'link': link,
            })
        
        return livros[:limite]
    
    except requests.RequestException as e:
        print(f"Erro ao consultar Google Books API: {e}")
        return []
    except KeyError as e:
        print(f"Erro ao processar resposta da API: {e}")
        return []