import psycopg2
import re
from collections import Counter

DATABASE_URL = "postgresql://postgres:XxZQPaZldEKDJyEKcDFQNsNMEDlvToFm@turntable.proxy.rlwy.net:53607/railway"

# Palavras comuns para ignorar (stopwords)
STOPWORDS = {
    'de', 'da', 'do', 'das', 'dos', 'a', 'e', 'o', 'que', 'para', 'com', 'em', 'um', 'uma',
    'os', 'as', 'ao', 'aos', 'na', 'no', 'nas', 'nos', 'por', 'para', 'sem', 'sob', 'sobre',
    'apos', 'ate', 'pos', 'entre', 'atraves', 'compreende', 'inclui', 'incluindo', 'seu',
    'sua', 'seus', 'suas', 'meu', 'minha', 'nosso', 'nossa', 'voce', 'ele', 'ela', 'eles',
    'elas', 'isso', 'aquilo', 'este', 'esta', 'estes', 'estas', 'esse', 'essa', 'esses', 'essas',
    'livro', 'guia', 'manual', 'introducao', 'fundamentos', 'basico', 'basica', 'avancado'
}

# Mapeamento de palavras-chave para categorias (expandir conforme necessário)
PALAVRAS_CATEGORIAS = {
    # Programacao
    'python': 'Programacao',
    'java': 'Programacao', 
    'javascript': 'Programacao',
    'c++': 'Programacao',
    'c#': 'Programacao',
    'php': 'Programacao',
    'ruby': 'Programacao',
    'go': 'Programacao',
    'rust': 'Programacao',
    'swift': 'Programacao',
    'kotlin': 'Programacao',
    'algoritmo': 'Programacao',
    'logica': 'Programacao',
    'programacao': 'Programacao',
    'codigo': 'Programacao',
    'linguagem': 'Programacao',
    
    # Banco de Dados
    'sql': 'Banco de Dados',
    'postgresql': 'Banco de Dados',
    'mysql': 'Banco de Dados',
    'oracle': 'Banco de Dados',
    'mongodb': 'Banco de Dados',
    'banco de dados': 'Banco de Dados',
    'database': 'Banco de Dados',
    'nosql': 'Banco de Dados',
    
    # Engenharia de Software
    'engenharia de software': 'Engenharia de Software',
    'uml': 'Engenharia de Software',
    'metodologia ageis': 'Engenharia de Software',
    'scrum': 'Engenharia de Software',
    'kanban': 'Engenharia de Software',
    'requisitos': 'Engenharia de Software',
    
    # Redes
    'rede': 'Redes de Computadores',
    'tcp/ip': 'Redes de Computadores',
    'protocolo': 'Redes de Computadores',
    'comunicacao': 'Redes de Computadores',
    'roteamento': 'Redes de Computadores',
    
    # IA
    'inteligencia artificial': 'Inteligencia Artificial',
    'machine learning': 'Inteligencia Artificial',
    'aprendizado de maquina': 'Inteligencia Artificial',
    'redes neurais': 'Inteligencia Artificial',
    'deep learning': 'Inteligencia Artificial',
    
    # Web
    'web': 'Desenvolvimento Web',
    'html': 'Desenvolvimento Web',
    'css': 'Desenvolvimento Web',
    'react': 'Desenvolvimento Web',
    'angular': 'Desenvolvimento Web',
    
    # Mobile
    'android': 'Desenvolvimento Mobile',
    'ios': 'Desenvolvimento Mobile',
    'flutter': 'Desenvolvimento Mobile',
    
    # Seguranca
    'seguranca': 'Seguranca da Informacao',
    'criptografia': 'Seguranca da Informacao',
    'hacker': 'Seguranca da Informacao',
    'firewall': 'Seguranca da Informacao',
    
    # Dados
    'data science': 'Ciencia de Dados',
    'big data': 'Ciencia de Dados',
    'analise de dados': 'Ciencia de Dados',
    'estatistica': 'Estatistica',
}

def extrair_palavras(texto):
    """Extrai palavras relevantes do texto"""
    if not texto:
        return []
    texto = texto.lower()
    # Remove acentos simples
    texto = re.sub(r'[áãâà]', 'a', texto)
    texto = re.sub(r'[éêè]', 'e', texto)
    texto = re.sub(r'[íìî]', 'i', texto)
    texto = re.sub(r'[óõôò]', 'o', texto)
    texto = re.sub(r'[úùû]', 'u', texto)
    texto = re.sub(r'ç', 'c', texto)
    
    palavras = re.findall(r'[a-z]+(?: [a-z]+)?', texto)
    return [p for p in palavras if len(p) > 2 and p not in STOPWORDS]

def associar_palavras_e_areas():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Buscar livros sem palavras-chave
    cursor.execute("""
        SELECT l.id, l.titulo, l.autor
        FROM livro l
        LEFT JOIN livro_palavra_chave lpc ON l.id = lpc.livro_id
        WHERE lpc.palavra_chave_id IS NULL
    """)
    livros = cursor.fetchall()
    
    print(f"Processando {len(livros)} livros...")
    
    total_palavras = 0
    
    for livro_id, titulo, autor in livros:
        texto = f"{titulo} {autor if autor else ''}"
        palavras = extrair_palavras(texto)
        
        # Limitar a 5 palavras por livro
        for palavra in list(set(palavras))[:5]:
            if len(palavra) > 2:
                # Inserir palavra
                cursor.execute("""
                    INSERT INTO palavra_chave (nome) 
                    VALUES (%s) 
                    ON CONFLICT (nome) DO NOTHING
                """, (palavra,))
                
                # Associar palavra ao livro
                cursor.execute("""
                    INSERT INTO livro_palavra_chave (livro_id, palavra_chave_id)
                    SELECT %s, id FROM palavra_chave WHERE nome = %s
                    ON CONFLICT DO NOTHING
                """, (livro_id, palavra))
                
                total_palavras += 1
        
        if palavras:
            print(f"✅ {titulo[:40]}... -> {palavras[:3]}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n📊 Total de associações criadas: {total_palavras}")

if __name__ == "__main__":
    associar_palavras_e_areas()