import json, zlib

__all__ = [
    "compactar_lista",
    "descompactar_lista"
]

# Códigos de Retorno
CODES = {
    "SUCESSO": 0,
    "ERRO_ARQUIVO": 1,           # Erro geral relacionado ao arquivo (leitura/escrita)
    "ERRO_CODIFICACAO": 2,       # Erro durante a codificação dos dados
    "ERRO_DECODIFICACAO": 3,     # Erro durante a decodificação dos dados
    "ERRO_CONSTRUCAO_ARVORE": 4, # Erro na construção da árvore de Huffman
    "ERRO_FORMATO_DADOS": 5      # Erro no formato dos dados do arquivo
}

# Funções de Acesso
def compactar_lista(lista_dicionarios, arquivo):
    """
    Compacta uma lista de dicionários e salva em um arquivo binário já aberto.

    Args:
        lista_dicionarios (list of dict): A lista de dicionários a ser compactada.
        arquivo (file-like object): Um objeto de arquivo binário aberto para escrita.

    Returns:
        tuple: Uma tupla contendo um código de retorno e o retorno em si.
    """
    try:
        lista_string = str(lista_dicionarios)
        frequencias = _calcular_frequencias(lista_string)
        arvore_huffman = _construir_arvore_huffman(frequencias)
        codigo_huffman = _gerar_codigo_huffman(arvore_huffman)
        texto_codificado = _codificar_lista(lista_string, codigo_huffman)
        _escrever_binario(texto_codificado, codigo_huffman, arquivo)
        return CODES["SUCESSO"]
    except (OSError, IOError):
        return CODES["ERRO_ARQUIVO"]
    except ValueError:
        return CODES["ERRO_CODIFICACAO"]
    except Exception:
        return CODES["ERRO_CODIFICACAO"]

def descompactar_lista(arquivo):
    """
    Lê um arquivo binário compactado e retorna a lista de dicionários descompactada.

    Args:
        arquivo (file-like object): Um objeto de arquivo binário aberto para leitura.

    Returns:
        tuple: Uma tupla contendo um código de retorno e o retorno em si.
    """
    try:
        texto_codificado, codigo_huffman = _ler_binario(arquivo)
        texto_decodificado = _decodificar_texto(texto_codificado, codigo_huffman)
        lista_decodificada = _texto_para_lista(texto_decodificado)
        return (CODES["SUCESSO"], lista_decodificada)
    except (OSError, IOError) as e:
        return (CODES["ERRO_ARQUIVO"], [])
    except ValueError as e:
        return (CODES["ERRO_DECODIFICACAO"], str(e))
    except Exception as e:
        return (CODES["ERRO_DECODIFICACAO"], str(e))


# Funções Internas (Auxiliares)
def _calcular_frequencias(representacao_lista):
    """
    Calcula a frequência de cada caractere na string JSON que representa a lista de dicionários.

    Args:
        representacao_lista (str): A string JSON representando a lista de dicionários.

    Returns:
        dict: Um dicionário com a frequência de cada caractere encontrado na string JSON.
    """
    frequencias = {}
    for caractere in representacao_lista:
        frequencias[caractere] = frequencias.get(caractere, 0) + 1
    
    return frequencias

def _construir_arvore_huffman(frequencias):
    """
    Constrói a árvore de Huffman usando uma lista de prioridade manual.

    Args:
        frequencias (dict): Um dicionário com a frequência de cada caractere.

    Returns:
        list of tuples: A árvore de Huffman representada como uma lista de tuplas (caractere, código).
    """
    heap = [[freq, [simbolo, ""]] for simbolo, freq in frequencias.items()]
    
    while len(heap) > 1:
        heap.sort()
        lo = heap.pop(0)
        hi = heap.pop(0)
        
        for par in lo[1:]:
            par[1] = '0' + par[1]
        for par in hi[1:]:
            par[1] = '1' + par[1]
        
        heap.append([lo[0] + hi[0]] + lo[1:] + hi[1:])
    
    return sorted(heap[0][1:], key=lambda p: (len(p[-1]), p))

def _gerar_codigo_huffman(arvore_huffman):
    """
    Gera um dicionário de códigos de Huffman a partir da árvore.

    Args:
        arvore_huffman (list of tuples): A árvore de Huffman representada como uma lista de tuplas (caractere, código).

    Returns:
        dict: Um dicionário com os códigos de Huffman para cada caractere.
    """
    return {simbolo: codigo for simbolo, codigo in arvore_huffman}

def _codificar_lista(representacao_lista, codigo_huffman):
    """
    Codifica a string JSON que representa a lista de dicionários utilizando os códigos de Huffman.

    Args:
        representacao_lista (str): A string JSON representando a lista de dicionários.
        codigo_huffman (dict): Um dicionário com os códigos de Huffman para cada caractere.

    Returns:
        str: O texto codificado resultante da codificação da string JSON.
    """
    texto_codificado = ""
    
    for caractere in representacao_lista:
        if caractere in codigo_huffman:
            texto_codificado += codigo_huffman[caractere]
        else:
            raise ValueError(f"Caractere '{caractere}' não encontrado no código de Huffman.")
    
    return texto_codificado

def _decodificar_texto(texto_codificado, codigo_huffman):
    """
    Decodifica o texto codificado utilizando o código de Huffman.

    Args:
        texto_codificado (str): O texto codificado a ser decodificado.
        codigo_huffman (dict): Um dicionário com os códigos de Huffman para cada caractere.

    Returns:
        str: O texto decodificado.
    """
    # Inverte o dicionário de códigos de Huffman para decodificação
    codigo_invertido = {codigo: simbolo for simbolo, codigo in codigo_huffman.items()}
    
    simbolo_atual = ""
    texto_decodificado = ""
    
    for bit in texto_codificado:
        simbolo_atual += bit
        
        # Verifica se o prefixo atual corresponde a um símbolo no código invertido
        if simbolo_atual in codigo_invertido:
            texto_decodificado += codigo_invertido[simbolo_atual]
            simbolo_atual = ""
    
    return texto_decodificado

def _texto_para_lista(texto):
    """
    Converte o texto decodificado de volta para uma lista de dicionários.

    Args:
        texto (str): O texto decodificado em formato JSON a ser convertido em lista de dicionários.

    Returns:
        list of dict: A lista de dicionários resultante da conversão do texto.
    """
    try:
        texto = texto.replace("'",'"')
        lista_dicionarios = json.loads(texto)
        if not isinstance(lista_dicionarios, list):
            raise ValueError("O texto JSON não representa uma lista.")
        for item in lista_dicionarios:
            if not isinstance(item, dict):
                raise ValueError("Os itens na lista JSON não são dicionários.")
        return lista_dicionarios
    except json.JSONDecodeError:
        raise ValueError("Erro ao decodificar o texto JSON.")

def _escrever_binario(texto_codificado, codigo_huffman, arquivo):
    """
    Escreve o texto codificado e o código de Huffman manualmente em um arquivo binário já aberto.

    Args:
        texto_codificado (str): O texto codificado a ser escrito no arquivo.
        codigo_huffman (dict): Um dicionário com os códigos de Huffman para cada caractere.
        arquivo (file-like object): Um objeto de arquivo binário aberto para escrita.

    Returns:
        None: A função não retorna nada. Os dados são escritos no arquivo.
    """
    try:
        tamanho = len(texto_codificado)
        arquivo.write(tamanho.to_bytes(4, 'little')) 
        
        valor = int(texto_codificado, 2).to_bytes((tamanho + 7) // 8, 'big')
        arquivo.write(valor)
        
        json_data = json.dumps(codigo_huffman).encode('utf-8')
        compressed_data = zlib.compress(json_data)
        
        arquivo.write(len(compressed_data).to_bytes(4, 'little'))  
        
        arquivo.write(compressed_data)
    except (OSError, IOError) as e:
        raise RuntimeError(f"Erro ao escrever no arquivo: {e}")


def _ler_binario(arquivo):
    """
    Lê o texto codificado e o código de Huffman manualmente de um arquivo binário já aberto.

    Args:
        arquivo (file-like object): Um objeto de arquivo binário aberto para leitura.

    Returns:
        tuple: Uma tupla contendo o texto codificado (str) e o dicionário de códigos de Huffman (dict).
    """
    try:
        tamanho = int.from_bytes(arquivo.read(4), 'little')
        
        num_bytes = (tamanho + 7) // 8
        
        valor = arquivo.read(num_bytes)
        texto_codificado = bin(int.from_bytes(valor, 'big'))[2:].zfill(tamanho)
        
        tamanho_comprimido = int.from_bytes(arquivo.read(4), 'little')
        
        conteudo_comprimido = arquivo.read(tamanho_comprimido)
        json_data = zlib.decompress(conteudo_comprimido).decode('utf-8')
        codigo_huffman = json.loads(json_data)
        
        return texto_codificado, codigo_huffman
    except (OSError, IOError) as e:
        raise RuntimeError(f"Erro ao ler o arquivo: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Erro no formato dos dados do arquivo: {e}")