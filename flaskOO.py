from flask import Flask, session, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI

app = Flask(__name__)
app.secret_key = '123456'
client = OpenAI(api_key='')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///preferences.sqlite3'
db = SQLAlchemy(app)
app.app_context().push()

## Padrão criacional dos obejtos PREFERENCIAS, um Factory Method. Decidi usá-lo para saber sempre onde meu objeto está sendo criado;
class fabricaPreferencias:
    @staticmethod
    def criar_pref(nome, rpg_fav, tipoJogo, senha):
        return Preferencia(nome, rpg_fav, tipoJogo, senha)

# padrão criacional de objetos
## contrói a mensagem em partes a partir das preferencias do usuario
class ChatGptBuilder:
    def __init__(self, user):
        self.user = user
        self.prompt = ""

    def with_prompt(self):
        if self.user.tipoJogo == "Mestre" or self.user.tipoJogo == "Meste":
            self.prompt += "O usuário é um mestre, o contador de histórias da mesa, responda a pergunta, e, caso o usuario mencione, na pergunta, sobre o {self.user.rpg_fav} do usuario, responda EXATAMENTE o que ele pediu. Se for montar uma história, monte uma história, se for montar um rpg, monte um rpg"
        elif self.user.tipoJogo == "Player":
            self.prompt += "O usuário é um PLAYER, interprete e responda a pergunta com base no sistema favorito definido por ele, que é {self.user.rpg_fav}. Se o usuário pedir, em sua pergunta, para criar um personagem, gere, além do personagens, valores para os atributos do sistema favorito do usuário."
        else: 
            self.prompt += "Se o usuário não tiver um estilo definido, responda a pergunta genericamente, com a personalidade de um mago."
        return self
    
    def build(self):
        prompt = (
            f" O sistema de rpg favorito do usuário é {self.user.rpg_fav}."
            f" Responda com a personalidade de um sábio "
            f"{self.prompt} "
            f" Se a pergunta for algo desconexo com rpg, faça uma piada sobre seus poderes mágicos e reforce que você pode ajudá-lo em qualquer pergunta sobre rpg!"
        )

        return prompt

# Padrão comportamental mediator;
## define o chat do mago, e adquire o prompt definido no builder. Pode-se considerar um padrão mediator, já que ele interaje entre a criação do prompt e do comando, sem que as duas classes conversem diretamente;
class ChatMago:
    def __init__(self, prompt, comando):
        self.prompt = prompt
        self.comando = comando
    
    def perguntar(self):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            response_format={"type": "text"},
            messages=[
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": self.comando}
            ]
        )
        return response.choices[0].message.content

## Definido para responder o usuário a partir de regras utilizando as preferencias do usuário.


class Preferencia(db.Model):
    __tablename__ = "data"

    
    id = db.Column(db.Integer, primary_key=True) ## adiciona uma linha para numerar os usuários, eu acho?
    nome = db.Column(db.String, nullable=False, unique=True)
    rpg_fav = db.Column(db.String)
    tipoJogo = db.Column(db.String)
    senha = db.Column(db.String, nullable=False)
    
    def __init__(self, nome, rpg_fav, tipoJogo, senha):
        self.nome = nome
        self.rpg_fav = rpg_fav
        self.tipoJogo = tipoJogo
        self.senha = senha

#cria o /perfil
@app.route('/cadastro', methods=['POST','GET'])
def cadastro():
    try:
        ##return render_template('preferencias.html', usuarios=users)
        if request.method == 'POST':
            if 'user_id' in session:
                return redirect(url_for('infos'))
            else:
                if 'nome' in request.form and 'rpg_fav' in request.form and 'tipoJogo' in request.form and 'senha' in request.form:
                    nome = request.form['nome']
                    rpg_fav = ', '.join(request.form.getlist('rpg_fav')) ##Recebe os valores em lista, ao invés de um valor só, e traduz cada valor para var1, var2;
                    tipoJogo = ', '.join(request.form.getlist('tipoJogo'))
                    senha = request.form['senha']
                                        
                    novoUser = fabricaPreferencias.criar_pref(nome=nome, rpg_fav=rpg_fav, tipoJogo=tipoJogo, senha=senha)
                    db.session.add(novoUser)  
                    db.session.commit()
                    
                    return redirect(url_for('infos'))
        return '''
        <!DOCTYPE html>
<html>
<head>
    <title>Preferencias do Usuário</title>
    <style>
        body{
        height: 100vh;
        background: linear-gradient(180deg,#08172e, #000814) repeat;
        background-size: cover;
        background-position: center;
        font-family:'Times New Roman', Times, serif;
        margin: 0; /* Remover margens padrão do corpo */
        display: flex;
        justify-content: center; /* Centralizar na horizontal */
        align-items: center; /* Centralizar na vertical */
    }
    .formulario{
        margin-top: 0px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background-color: #A98A4A;
        background: linear-gradient(180deg,#A98A4A, #766033);
        border-radius: 7%;
        width: 50%;
        padding: 20px;
        gap: 5px; 
    }
    .formulario h1, h2{
        color:#08172e
    }
    .formulario label{
        color:#08172e;
    }
    .formulario input[type="text"], input[type="password"]{
        border-radius: 8px;
        text-align: center;
    }
    input[type="submit"] {
        padding: 5px 10px;
        font-size: 1em;
        border-radius: 7px;
        border: none;
        background-color: #08172e;
        color: #fdf6e3;
        cursor: pointer;
        text-align: center;
        justify-content: center;
    }
    input[type="submit"]:hover {
        background-color: #003381;
    }
    </style>
</head>
<body>
    <div class="formulario">
    <h1>Quais seus gostos sobre rpg? Defina aqui!</h1>
    <form method="POST">

        Nome de Usuário:<br>
            <input type="text" id="nome" name="nome"> 
        <br>
        <br>

        Rpg favorito:<br>
            <input type="checkbox" id="rpg1" name="rpg_fav" value="DnD">
            <label for="rpg1">Dungeons and Dragons <br></label>
            <input type="checkbox" id="rpg2" name="rpg_fav" value="T20">
            <label for="rpg2">Tormenta20 <br></label>
            <input type="checkbox" id="rpg3" name="rpg_fav" value="CoC">
            <label for="rpg3">Call of Cthullhu <br></label>
        
        <br>

        Seu tipo de jogo:<br>
            <input type="checkbox" id="tipojogo1" name="tipoJogo" value="Player">
            <label for="tipojogo1"> Player </label>
            <input type="checkbox" id="tipojogo2" name="tipoJogo" value="Meste">
            <label for="tipojogo2"> Mestre </label> <br>

        <br>
        <label for="senha"> Código-chave </label><br>
        <input type="password" id="senha" name="senha">
            
        <br>
        <br>
        <br>
        <br>
        <input type="submit" value="Enviar">
    </form>
        <form action="/">
            <p><input type=submit value=Voltar>
        </form>
    </div>
</body>
</html>   
        '''
            
    except Exception as e:
        return f"Erro: {str(e)}"

@app.route("/perfil", methods=['GET', 'POST'])
def infos():
    if 'user_id' in session:
        user_id = session['user_id']
        preferenciasUser = Preferencia.query.get(user_id)
        if preferenciasUser:
            return render_template('preferencias.html', prefUser=preferenciasUser)
        else:
            return redirect(url_for('verific'))
    else:
        return redirect(url_for('verific'))
            
@app.route("/deletar", methods=["GET","POST"])
def deletar():
    if request.method == "POST":
        if 'user_id' in session:
            user_id = session['user_id']
            preferenciasUser = Preferencia.query.get(user_id)
            if preferenciasUser:
                db.session.delete(preferenciasUser)
                db.session.commit()
                session.pop('user_id', None)
                return '''
            <!DOCTYPE html>
<html>
<head>
    <title>Obrigado por deletar!</title>
    <style>
        *{
            box-sizing: border-box;
        }
        body{
            background-color: #000814;
        }
        .center{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: linear-gradient(180deg,#001535, #000814);
        }
        .center h1,h2{
            color:#A98A4A;
            text-shadow: 1px 1px 3px #745e33;
        }
        .center button{
            background-color: #745e33;
            text-decoration: none;
            border-radius: 8px;
            transition: background-color 0.3s, transform 0.5s;
            width: 105%;
        }
        .center button:hover{
            background-color: #A98A4A;
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <div class="center">
        <h1> Suas preferencias foram deletadas! </h1>
        <h2> Obrigado por testar a Taverna do Fa!</h2>
    <form method="POST">
        <button type="submit" onclick=" window.location.href = '{{url_for('index')}}'">Início</button>
    </form>
    </div>
</body>
</html>
            '''  
    return redirect(url_for('index'))

## Verifica as informações no mesmo "preferencias.html", e, caso alteradas, podem ser definidas de novo.
@app.route("/atualizar", methods=["GET", "POST"])
def atualizar():
    if request.method == "POST": ## para pegar as novas opções
        if 'user_id' in session:
            user_id = session['user_id'] #define que a sessão atual pode ser alterada
            preferenciasUser = Preferencia.query.get(user_id)
            if preferenciasUser:
                if request.method == "POST":
                    novo_rpg_fav = request.form.getlist('novo_rpg_fav') # recebe a nova informação definida pelo usuário;
                    preferenciasUser.rpg_fav = ', '.join(novo_rpg_fav)
                    
                    novo_tipo_jogo = request.form.getlist('novo_tipo_jogo') #recebe a nova (ou a mesma) informação da checkbox atualizada;
                    preferenciasUser.tipoJogo = ', '.join(novo_tipo_jogo)
                    
                    db.session.commit()
                    return redirect(url_for('infos'))
    return redirect(url_for('verific'))
        
## Abre a tela de login para o usuário.
@app.route("/verific", methods=['GET', 'POST'])
def verific():
    try:
        if request.method == 'POST': ##se o método requisitado for APÓS o envio
            nome = request.form.get('nome') ## define que o nome, no banco de dados, recebe o formulário requisitado "username"
            senha = request.form.get('senha') ## define que o nome, no banco de dados, recebe o formilário resquisitado "senha"
            usuario = Preferencia.query.filter_by(nome=nome, senha=senha).first() ##verifica se existe nome e senha na tabela Usuario, don banco de dados
            if usuario: ## se existir usuario
                session['user_id'] = usuario.id ## entra na sessao como o usuario
                return redirect(url_for('infos')) ## é redirecionado para o perfil
            else:
                return '''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <link href='https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css' rel='stylesheet'>
                    <meta charset="UTF-8">
                    <title>Login</title>
                    <style>
                        .error {
                            color: red;
                            text-align: center;
                            margin-top: 20px;
                        }
                        .error p{
                            color: red;
                        }
                        .error form{
                            color: red;
                            
                        }
                        body{
                            background-color: #000814;
                            height: 100vh;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            margin: 0;
                        }
                        .login{
                            margin: 20px 15px;
                            gap: 10px;
                            margin-left: 80px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            background-color: #967433;
                            width: 35%;
                            border-radius: 35px;
                            box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
                            position: relative;
                            text-align: center;
                        }
                        .login form h1,p{
                            color: #1E3545;
                        }
                        .login input[type=text], .login input[type=password], .login input[type=submit] {
                            display: block;
                            width: calc(100% - 40px);
                            margin: 10px auto;
                            padding: 10px;
                            border-radius: 5px;
                            border: none;
                            text-align: center;
                        }
                        .login input[type=submit]{
                            text-align: center;
                            color: #1E3545;
                            margin: 10px auto;
                        }
                        </style>
                </head>
                <body>
                        <div class="error"><p>Usuário e senha inválidos. Por favor, cadastre seu usuário, ou insira os dados corretos.</p>
                            <form action="/">
                                <p><input type=submit value=Voltar>
                            </form>
                        </div>
                        <div class="login">
                            <form method="post" action="/verific">
                                <h1> Insira login e senha </h1>
                                <p><i class='bx bx-user'></i><input type=text name=nome></p>
                                <p><i class='bx bx-lock-alt' ></i><input type=password name=senha></p>
                                <p><input type=submit value=Login>
                            </form>   
                        </div>
                </body>
                </html>
                '''
        return '''
            <head>
                <link href='https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css' rel='stylesheet'>
                <style>
                    body{
                        background-color: #000814;
                        height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0;
                    }
                    .login{
                        margin: 20px 15px;
                        gap: 10px;
                        margin-left: 80px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background-color: #967433;
                        width: 35%;
                        border-radius: 35px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
                        position: relative;
                        text-align: center;
                    }
                    .login form h1,p{
                        color: #1E3545;
                    }
                    .login input[type=text], .login input[type=password], .login input[type=submit] {
                        display: block;
                        width: calc(100% - 40px);
                        margin: 10px auto;
                        padding: 10px;
                        border-radius: 5px;
                        border: none;
                        text-align: center;
                    }
                    .login input[type=submit]{
                        text-align: center;
                        color: #1E3545;
                        margin: 10px auto;
                    }
                    .login form{
                        color: #1E3545;
                    }
                </style>
            </head>
                <body>
                    <div class="login">
                    <form method="post">
                        <h1> Insira login e senha
                        <p><i class='bx bx-user'></i><input type=text name=nome></p>
                        <p><i class='bx bx-lock-alt' ></i><input type=password name=senha></p>
                        <p><input type=submit value=Login>
                    </form>
                    <form action="/cadastro">
                        <p><input type=submit value=Cadastro>
                    </form>
                    </div>
            </body>
        '''
    except Exception as e:
        return f"Erro: {str(e)}"


# padrão fachada que reestrutura o código, para poder simplificar o método mago, além de permitir a mudança de variáceis sem alterar todo o método, caso necesário.
class FacadeChat:
    def __init__(self, user, comando):
        self.user = user
        self.comando = comando
    
    def obter_resposta(self):
        builder = ChatGptBuilder(self.user)
        prompt = builder.with_prompt().build()
        chat_Mago = ChatMago(prompt, self.comando)
        resposta = chat_Mago.perguntar()
        return resposta

## Pega o padrão builder e joga as escolhas do usuário para dentro dele. Depois, utiliza estes prompts selecionados para CONSTRUIR as respostas e o prompt, e assim enviar a resposta para a pergunta
@app.route("/mestreMago", methods=['POST', 'GET'])
def mago():
    if 'user_id' not in session:
        return redirect(url_for('verific'))
    if request.method == 'POST':
            if 'user_id' in session:
                user_id = session['user_id']
                user = Preferencia.query.get(user_id)
                comando = request.form['questao']

                # reestruturando para apenas convocar o padrão fachada
                chat = FacadeChat(user, comando)
                resposta = chat.obter_resposta()
                
                return render_template('questao.html', resposta = resposta)
            else:
                return redirect(url_for('index'))
    elif request.method == "GET":
        if 'user_id' in session:
            return render_template('questao.html')
        else:
            return redirect(url_for('login'))
                

## Retira o user_id da sessão, mas ainda salva suas informações no banco de dados!
@app.route('/logout')
def logout(): ## FUNCIONANDO PERFEITAMENTE
    session.pop('user_id', None)
    return redirect(url_for('index'))

##rota comum do site, primeira  coisa que abre!
@app.route("/")
def index(): ## FUNCIONANDO PERFEITAMENTE
    return render_template('index.html')

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)