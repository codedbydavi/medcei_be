# 🏥 MEDCEi - Backend API

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

API RESTful desenvolvida em **Python** para alimentar o sistema **MEDCEi**. Este backend gerencia a lógica de negócios, autenticação de utilizadores e calculos matemáticos.

## 📋 Sobre o Projeto

O backend fornece endpoints seguros em JSON para o frontend React, gerenciando:
* Autenticação e Autorização.
* Gerenciamento de dados (CRUD).
* Regras de negócio do sistema MEDCEi.

## 🚀 Tecnologias Utilizadas

* **Linguagem:** Python 3.x
* **Framework:** [Flask]
* **Banco de Dados:** [MySQL]
* **ORM:** [SQLAlchemy]
* **Autenticação:** [JWT]

## ⚙️ Pré-requisitos

* [Python](https://www.python.org/) (Versão 3.8 ou superior)
* [Pip](https://pypi.org/project/pip/) (Gerenciador de pacotes)
* Virtualenv (Recomendado)

## 🔧 Instalação e Configuração

1. **Clone o repositório**
   ```bash
   git clone [https://github.com/seu-usuario/medcei-backend.git](https://github.com/seu-usuario/medcei-backend.git)
   cd medcei-backend

2. **Crie o Ambiente Virtual (Virtualenv) É uma boa prática isolar as dependências do projeto.**

    # Windows
    python -m venv venv
    .\venv\Scripts\activate
    
    # Linux / macOS
    python3 -m venv venv
    source venv/bin/activate

3. **Instale as dependências**

    pip install -r requirements.txt

4. **Configuração de Variáveis de Ambiente Crie um arquivo .env na raiz do projeto com base nas suas configurações locais:**

    # Exemplo de configuração
    DATABASE_URL="postgresql://usuario:senha@localhost:5432/medcei_db"
    SECRET_KEY="sua-chave-secreta-super-segura"
    DEBUG=True

🤝 Contribuição
    Faça o Fork.
    
    Crie a Branch (git checkout -b feature/NovaFeature).
    
    Commit (git commit -m 'Add: Nova Feature').
  
  Push (git push origin feature/NovaFeature).
  
  Abra um Pull Request.
