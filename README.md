<div align="center">

# 🔎 Rey Search

### Busca rápida, organizada e local em arquivos `.TXT`

**Uma ferramenta desktop para Windows 10/11, feita em Python e Tkinter, com interface roxa e foco em simplicidade.**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Plataforma-Windows%2010%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Interface](https://img.shields.io/badge/Interface-Tkinter-8B5CF6?style=for-the-badge)
![Dependencies](https://img.shields.io/badge/Dependências-stdlib-22C55E?style=for-the-badge)

</div>

---

## ✨ Sobre o projeto

O **Rey Search** pesquisa uma ou várias palavras-chave em arquivos de texto `.txt` dentro de uma pasta. Você pode incluir subpastas, ajustar o modo de correspondência, acompanhar o progresso e exportar os resultados para analisar depois.

A interface foi construída com **Tkinter**, biblioteca gráfica incluída na distribuição padrão do Python para Windows. O motor de busca roda em uma thread separada para manter a janela responsiva durante pesquisas longas.

## 🚀 Funcionalidades

- **Busca em lote:** procura várias palavras-chave separadas por vírgulas.
- **Busca recursiva opcional:** inclui ou não as subpastas da pasta escolhida.
- **Opções de correspondência:** ignorar/diferenciar maiúsculas e minúsculas, palavra inteira e expressões regulares (`regex`).
- **Resultados detalhados:** caminho do arquivo, número da linha, palavras encontradas e conteúdo da linha.
- **Estatísticas:** arquivos analisados, arquivos com correspondências, ocorrências, erros e tempo decorrido.
- **Interface responsiva:** busca executada em thread separada, com botão para solicitar cancelamento.
- **Logs em tempo real:** mensagens coloridas por nível e arquivo diário em `logs/reysearch_AAAA-MM-DD.log`.
- **Exportação:** salve os resultados como TXT, CSV ou JSON.
- **Acesso rápido:** dê duplo clique em um resultado para abrir o arquivo no aplicativo padrão do Windows.
- **Tolerância a erros:** problemas de permissão e leitura são registrados sem interromper toda a pesquisa; tenta UTF-8 e usa Latin-1 como alternativa.
- **Arquivos grandes:** leitura linha a linha, sem carregar o arquivo inteiro na memória.

## 🖥️ Pré-requisitos

- Windows 10 ou Windows 11.
- Python **3.10 ou superior** para executar a partir do código-fonte.
- Tkinter, incluído no instalador oficial do Python para Windows.

> O projeto não precisa de bibliotecas externas para funcionar. O `requirements.txt` está incluído para deixar isso explícito.

## 📦 Instalação e execução

### 1. Baixe o projeto

Baixe o ZIP pelo botão **Code → Download ZIP** do GitHub e extraia a pasta para um local de sua preferência.

### 2. Abra um terminal na pasta

No Explorador de Arquivos, entre na pasta do projeto, clique na barra de endereço, digite `powershell` e pressione Enter.

### 3. Inicie o aplicativo

```powershell
python main.py
```

Se o comando `python` não estiver disponível, tente:

```powershell
py main.py
```

## 🧭 Como usar

1. Clique em **Procurar pasta** e selecione o diretório com os arquivos `.txt`.
2. Digite uma palavra ou várias, separadas por vírgula. Exemplo: `erro, timeout, conexão recusada`.
3. Configure as opções de busca:
   - **Buscar em subpastas:** pesquisa também nos diretórios internos.
   - **Diferenciar maiúsculas:** diferencia `Erro` de `erro`.
   - **Palavra inteira:** exige limites de palavra.
   - **Usar regex:** interpreta cada entrada como uma expressão regular do Python.
4. Clique em **INICIAR BUSCA**.
5. Acompanhe os resultados e os logs. Clique em **PARAR** para solicitar o cancelamento.
6. Dê duplo clique em um resultado para abrir o arquivo.
7. Clique em **Exportar resultados** e escolha TXT, CSV ou JSON.

### Exemplo de busca

Para encontrar linhas que contenham `login`, `token` ou `falha` em arquivos `.txt`, digite:

```text
login, token, falha
```

Cada palavra-chave é testada separadamente. Se uma linha corresponder a mais de uma palavra, todas as correspondências serão indicadas.

## 🧰 Gerar um executável `.EXE`

Para distribuir o aplicativo sem pedir que o usuário instale Python, use o [PyInstaller](https://pyinstaller.org/).

### Instale o PyInstaller

```powershell
python -m pip install pyinstaller
```

### Gere um executável em pasta

Execute na pasta que contém `main.py`:

```powershell
python -m PyInstaller --noconfirm --clean --windowed --name "Rey Search" main.py
```

O resultado será criado dentro da pasta `dist`. Esse modo gera uma pasta com o executável e os componentes necessários.

### Gere um único arquivo EXE

```powershell
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "Rey Search" main.py
```

O arquivo único ficará em `dist\Rey Search.exe`.

> **Dica:** o PyInstaller deve ser executado no Windows para gerar um `.exe` para Windows. Se quiser usar um ícone próprio, crie um arquivo `.ico` e acrescente `--icon "rey-search.ico"` ao comando.

## 📁 Estrutura do projeto

```text
rey-search/
├── main.py             # Ponto de entrada do aplicativo
├── ui.py               # Interface gráfica e interação com o usuário
├── search_engine.py    # Motor de busca e processamento dos TXT
├── logger.py           # Logs para arquivo e interface
├── requirements.txt    # Dependências externas (nenhuma)
├── README.md           # Documentação do projeto
└── logs/
    └── .gitkeep        # Mantém a pasta de logs no repositório
```

## 📝 Logs e diagnóstico

O aplicativo cria um arquivo de log diário na pasta `logs`, com timestamp, nível e mensagem. Os níveis incluem `INFO`, `WARNING`, `ERROR` e `SUCCESS`.

Se um arquivo não puder ser lido, o caminho e o erro serão registrados e o programa continuará com os próximos arquivos sempre que possível.

## ⚙️ Notas técnicas e limitações

- O conteúdo é lido linha a linha com o buffering padrão do Python, evitando carregar arquivos de centenas de megabytes integralmente na memória.
- A opção de regex usa a sintaxe do módulo `re` da biblioteca padrão.
- O cancelamento é verificado durante a varredura e entre linhas. Uma única linha excepcionalmente grande pode atrasar a resposta ao cancelamento.
- A opção **Palavra inteira** usa limites de palavra (`\b`) da expressão regular; o comportamento pode variar em casos específicos de Unicode.
- Em modo sem subpastas, somente arquivos `.txt` diretamente dentro da pasta escolhida são analisados.
- Os resultados exportados podem conter trechos de texto dos arquivos pesquisados. Confira o destino antes de compartilhar uma exportação.

## 🛣️ Ideias para evoluções futuras

- Filtros por tamanho e data de modificação.
- Limite configurável de resultados.
- Navegação entre ocorrências e destaque da palavra encontrada.
- Testes automatizados para os modos de busca.
- Ícone `.ico` e instalador do Windows.

## 🤝 Contribuições

Sugestões e melhorias são bem-vindas. Abra uma **Issue** descrevendo o comportamento esperado, o que aconteceu e, se possível, passos para reproduzir o problema. Para contribuir com código, envie um Pull Request com uma descrição objetiva das mudanças.

## 📄 Licença

Nenhuma licença foi definida neste projeto ainda. Antes de redistribuir ou incorporar o código em outro produto, defina uma licença apropriada no arquivo `LICENSE`.

---

<div align="center">

**Rey Search** · desenvolvido para tornar buscas em arquivos TXT mais simples.

</div>
