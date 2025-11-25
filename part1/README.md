# Part 1 - Geographic Location Matching

## 📋 Problema

Este módulo resolve o problema de encontrar o **nível administrativo comum mais alto** entre pares de localizações geográficas em Portugal, considerando:

1. **Hierarquia geográfica**: Portugal → Distritos (admin_level 6) → Concelhos (admin_level 7) → Freguesias (admin_level 8)
2. **Ambiguidade**: Algumas cidades têm o mesmo nome em diferentes locais
3. **Informação parcial**: Nem sempre o estado/distrito é fornecido

---

## 🎯 Objetivo

Dado um DataFrame com colunas:
- `id_1`, `id_2`: Identificadores
- `city_1`, `city_2`: Nomes das cidades
- `state_1`, `state_2`: Estados/distritos (podem ser vazios)

Retornar o mesmo DataFrame com duas novas colunas:
- **`expected_level`**: Nível administrativo mais alto onde as duas localizações se encontram
- **`is_ambiguous`**: Flag (0/1) indicando se pelo menos uma localização é ambígua

---

## 📊 Exemplos

### Caso 1: Cidades diferentes com mesmo nome
```
city_1="valadares", state_1="viseu"
city_2="valadares", state_2="porto"
→ expected_level=2 (país), is_ambiguous=0
```

### Caso 2: Cidade sem estado (ambíguo)
```
city_1="valadares", state_1="viseu"
city_2="valadares", state_2=None
→ expected_level=8 (best case: mesma cidade), is_ambiguous=1
```

### Caso 3: Hierarquia (cidade dentro de concelho)
```
city_1="valadares", state_1="viseu"
city_2="sao pedro do sul", state_2="viseu"
→ expected_level=7 (concelho de sao pedro do sul), is_ambiguous=0
```
*Nota: "valadares" está contido em "sao pedro do sul"*

### Caso 4: Cidade inexistente
```
city_1="lugar que nao existe", state_1=None
city_2="valadares", state_2="viseu"
→ expected_level=2 (país), is_ambiguous=0
```

### Caso 5: Estado único (não ambíguo)
```
city_1="valadares", state_1=None
city_2="sao pedro do sul", state_2="viseu"
→ expected_level=7, is_ambiguous=1
```
*Nota: "sao pedro do sul" só existe em 1 local → não ambíguo*
*"valadares" existe em múltiplos locais → ambíguo*

---

## 🏗️ Arquitetura da Solução

### 1. **Pré-processamento do JSON** (`loader.py`)
- Carrega `portugal.json` e converte a árvore em estruturas planas
- Cria índices de lookup rápido (hash tables)

**Estruturas criadas:**
```python
# Lista de localizações
locations = [
    {
        "id": 1,
        "name": "valadares",
        "admin_level": 8,
        "parent_id": 123,
        "ancestors": [1, 123, 456, 789],  # IDs até o país
        "ancestors_names": ["valadares", "sao pedro do sul", "viseu", "portugal"],
        "ancestors_levels": [8, 7, 6, 2]
    },
    ...
]

# Índice por cidade
by_city = {
    "valadares": [id1, id2, id3],  # múltiplas valadares
    "sao pedro do sul": [id4]      # única
}

# Índice por (cidade, estado)
by_city_state = {
    ("valadares", "viseu"): [id1],
    ("valadares", "porto"): [id2]
}
```

### 2. **Resolução de Localizações** (`resolver.py`)
- Lookup de localizações por nome e estado
- Detecção de ambiguidade (múltiplas opções)

### 3. **Processamento do DataFrame** (`processor.py`)
- Aplica lookup para cada linha
- Calcula `expected_level` (best case scenario)
- Determina `is_ambiguous`

### 4. **Utilities** (`utils.py`)
- Normalização de nomes (lowercase, remover acentos)
- Funções auxiliares

---

## 🚀 Performance

### Complexidade
- **Pré-processamento**: O(N) onde N = nº de localizações (~3000 para Portugal)
- **Lookup por linha**: O(1) em média (hash table)
- **Encontrar ancestral comum**: O(log D) onde D = profundidade da árvore (~5)

### Estimativas
- **Portugal (3000 localizações)**:
  - Carregamento: < 1 segundo
  - Processamento de 1M linhas: ~10 segundos

### Escalabilidade
- ✅ Memória: ~0.6 MB para Portugal, ~400 MB para todos os países do mundo
- ✅ Paralelizável: Pode processar chunks do DataFrame em paralelo
- ✅ Extensível: Adicionar novo país = adicionar JSON + recarregar índices

---

## 📁 Estrutura de Ficheiros

```
part1/
├── README.md              # Este ficheiro
├── data/
│   └── portugal.json      # Hierarquia geográfica
├── src/
│   ├── loader.py          # Carrega JSON → estruturas
│   ├── resolver.py        # Lookup de localizações
│   ├── processor.py       # Processa DataFrame
│   └── utils.py           # Funções auxiliares
├── main.py                # Script principal de exemplo
└── test_examples.py       # Testes com casos do enunciado
```

---

## 💡 Uso

```python
from part1.src.processor import GeoProcessor
import pandas as pd

# 1. Inicializar processador (carrega JSON)
processor = GeoProcessor('part1/data/portugal.json')

# 2. Criar DataFrame
df = pd.DataFrame({
    'id_1': [1, 1, 3],
    'id_2': [2, 3, 4],
    'city_1': ['valadares', 'valadares', 'valadares'],
    'city_2': ['valadares', 'valadares', 'valadares'],
    'state_1': ['viseu', 'viseu', None],
    'state_2': ['porto', None, None]
})

# 3. Processar
result = processor.process(df)

# 4. Resultado inclui expected_level e is_ambiguous
print(result)
```

---

## 🔑 Decisões de Design

### 1. **Normalização de Nomes**
- Todos os nomes são convertidos para **lowercase**
- **Acentos são removidos** (ex: "São" → "sao")
- Facilita matching e evita problemas com diferentes encodings

### 2. **Best Case Scenario**
- Quando há ambiguidade, assume-se o **melhor cenário possível**
- Exemplo: "valadares" sem estado assume-se que é o "valadares" correto
- `expected_level` = nível mais profundo (mais específico)

### 3. **Ambiguidade**
- `is_ambiguous = 1` se **qualquer uma** das duas localizações tiver múltiplas opções
- Mesmo que `state` seja único (como "sao pedro do sul"), se a **outra** localização for ambígua, a flag é 1

### 4. **Localizações Inexistentes**
- Se uma localização não existe → `expected_level = 2` (país)
- `is_ambiguous = 0` (não há ambiguidade, simplesmente não existe)

### 5. **Hierarquia**
- Se `loc1` está contido em `loc2` (ou vice-versa):
  - `expected_level` = nível do **contentor** (menos profundo)
  - Exemplo: "valadares (8)" em "sao pedro do sul (7)" → nível 7

---

## 🧪 Testes

Os testes cobrem todos os casos da tabela do enunciado:

1. ✅ Cidades com mesmo nome em estados diferentes
2. ✅ Cidade sem estado (ambíguo)
3. ✅ Ambas as cidades sem estado
4. ✅ Localização inexistente
5. ✅ Hierarquia (cidade dentro de concelho)
6. ✅ Estado único (não ambíguo para esse campo)
7. ✅ Ambiguidade mista

---

## 🔮 Extensões Futuras

### Multi-país
- Adicionar coluna `country` ao DataFrame
- Criar índices separados por país
- Suportar comparações cross-country

### Otimizações
- **Paralelização**: Processar chunks do DataFrame em paralelo
- **Caching**: Cache de lookups repetidos (LRU cache)
- **Base de Dados**: Para datasets muito grandes (> 10M localizações)

### Features Adicionais
- **Fuzzy matching**: Corrigir typos nos nomes das cidades
- **Coordenadas**: Adicionar lat/lon para desambiguação
- **Visualização**: Mapa com as localizações e seus níveis

---

## 📚 Referências

- **Admin Levels (OpenStreetMap)**:
  - Level 2: País
  - Level 4: Regiões Autónomas (Açores, Madeira)
  - Level 6: Distritos
  - Level 7: Concelhos
  - Level 8: Freguesias

---

**Autor**: Solução desenvolvida para o challenge JTA  
**Data**: Novembro 2025
