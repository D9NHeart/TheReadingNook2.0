# The Reading Nook

The Reading Nook é uma aplicação interativa desenvolvida em Python com a biblioteca Pygame, projetada para gamificar a experiência de leitura. Através de uma interface gráfica em estilo pixel art, os utilizadores podem gerir a sua biblioteca digital, acompanhar o progresso das páginas lidas e estabelecer desafios de leitura com metas temporais.

## Funcionalidades Principais

* **Quarto Virtual Interativo:** Interface gráfica imersiva que serve como o menu principal do utilizador.
* **Gestão de Biblioteca (Estante):** Interface para visualização de livros adicionados, exibição de metadados (título, autor) e acompanhamento do progresso em tempo real.
* **Sistema de Desafios:** Permite a criação de metas de leitura com definição de páginas e datas limite, fornecendo feedback visual através de barras de progresso.
* **Persistência de Dados:** Integração com banco de dados SQLite para o armazenamento seguro de utilizadores, sessões, livros e histórico de leitura.

---

## Capturas de Tela do Jogo

<img width="1596" height="931" alt="Screenshot 2026-06-26 223411" src="https://github.com/user-attachments/assets/ea342199-3058-467f-a235-23bc91dcfd1b" />
### Menu Principal / Quarto Virtual

<img width="1601" height="936" alt="Screenshot 2026-06-26 193153" src="https://github.com/user-attachments/assets/cc7e00f7-2cec-45ee-93cc-d0fc400428bd" />
<img width="1596" height="895" alt="image" src="https://github.com/user-attachments/assets/a6983625-2787-40c5-b2af-4899932d864f" />
<img width="1596" height="895" alt="image" src="https://github.com/user-attachments/assets/c186582e-6dcb-4596-9bb4-2c2863091e61" />
<img width="1595" height="892" alt="image" src="https://github.com/user-attachments/assets/c1827281-52d0-4f41-9d30-38ad6b388e46" />

### Biblioteca e Estante de Livros


<img width="1595" height="900" alt="image" src="https://github.com/user-attachments/assets/2e79bf9d-abaf-4fbc-9ec5-a398bfe7ab11" />
<img width="1592" height="896" alt="image" src="https://github.com/user-attachments/assets/8968a7df-0a6e-42d6-9828-95a9c6adebf4" />
### Painel de Desafios
---

## O que foi produzido nesta Release

Nesta versão do projeto, foram implementados e refinados os seguintes componentes estruturais:

1. **Arquitetura de Telas (State Pattern):** Centralização do fluxo do jogo no arquivo principal, gerenciando de forma limpa as transições entre autenticação, menu principal, leitor e configurações.
2. **Sistema de Interface Gráfica (GUI):** Renderização de componentes customizados como botões e painéis com detecção de colisão do rato e efeitos de foco (hover).
3. **Módulo de Base de Dados (`database.py`):** Estruturação das tabelas de utilizadores, livros e progresso de leitura, utilizando restrições de integridade (chaves primárias, estrangeiras e indexações únicas).
4. **Persistência de Sessão:** Implementação de ficheiro local de configuração para manter o utilizador ligado entre execuções consecutivas da aplicação.
5. **Correção de Renderização de Camadas:** Ajuste no ciclo de desenho (`draw`) para garantir a exibição correta das imagens de fundo texturizadas em paralelo com as superfícies interativas.

---

## Como Executar o Projeto

### Pré-requisitos
* Python 3.10 ou superior instalado.
* Biblioteca Pygame (especificada no arquivo de dependências).

### Instalação
1. Clone o repositório para a sua máquina local:
   ```bash
   git clone [https://github.com/D9NHeart/TheReadingNook2.0](https://github.com/D9NHeart/TheReadingNook2.0)

2. Instale as dependências necessárias:
    pip install -r requirements.txt
   
### Execução
Para iniciar a aplicação, execute o script principal a partir da raiz do projeto:

No Windows:

   Bash
  python the_reading_nook/reading_nook/main.py
  (Ou utilize o ficheiro automatizado run_windows.bat)

No macOS / Linux:

  Bash
  python3 the_reading_nook/reading_nook/main.py
 (Ou utilize o ficheiro automatizado run_macos_linux.sh)
