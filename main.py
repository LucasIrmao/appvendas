from kivy.app import App
from kivy.lang import Builder
from telas import *
from botoes import *
import requests
from bannervenda import BannerVenda
import os
import certifi
from functools import partial
from myfirebase import MyFirebase
from bannervendedor import BannerVendedor
from datetime import date

os.environ["SSl_CERT_FILE"] = certifi.where()

GUI = Builder.load_file("main.kv")
class MainApp(App):
    cliente = None
    produto = None
    unidade = None

    def build(self):
        self.firebase = MyFirebase()
        return GUI

    def on_start(self):
        arquivos = os.listdir("icones/fotos_perfil")
        lista_fotos = self.root.ids['fotoperfilpage']
        fotos_lista = lista_fotos.ids['lista_fotos_perfil']
        for foto in arquivos:
            imagem = ImageButton(source=f"icones/fotos_perfil/{foto}", on_release=partial(self.mudar_foto_perfil, foto))
            fotos_lista.add_widget(imagem)
        # Pegar foto do cliente :
        arquivo = os.listdir("icones/fotos_clientes")
        pagina_adicionarvenda = self.root.ids["adicionarvendaspage"]
        lista_clientes = pagina_adicionarvenda.ids["lista_clientes"]
        for foto_cliente in arquivo:
            image = ImageButton(source=f"icones/fotos_clientes/{foto_cliente}",
                                on_release=partial(self.selecionar_cliente, foto_cliente))
            label = LabelButton(text=foto_cliente.replace(".png", " ").capitalize(),
                                on_release=partial(self.selecionar_cliente, foto_cliente))
            lista_clientes.add_widget(image)
            lista_clientes.add_widget(label)

        # Lista produtos :
        arquivo = os.listdir("icones/fotos_produtos")
        pagina_adicionarvenda = self.root.ids["adicionarvendaspage"]
        lista_produtos = pagina_adicionarvenda.ids["lista_produtos"]
        
        for foto_produto in arquivo:
            image = ImageButton(source=f"icones/fotos_produtos/{foto_produto}",
                                on_release=partial(self.selecionar_produto, foto_produto))
            label = LabelButton(text=foto_produto.replace(".png", " ").capitalize(),
                                on_release=partial(self.selecionar_produto, foto_produto))
            lista_produtos.add_widget(image)
            lista_produtos.add_widget(label)
               

        # adicionar datas :
        pagina_adicionarvenda = self.root.ids["adicionarvendaspage"]
        data = pagina_adicionarvenda.ids["label_data"]
        data.text = f"Data: {date.today().strftime('%d/%m/%Y')}"

        self.pegar_infos_usuario()

    def pegar_infos_usuario(self):
        try:
            with open("refreshtoken.txt", "r") as arquivo:
                refresh_token = arquivo.read()
                local_id, id_token = self.firebase.trocar_toker(refresh_token)
                self.local_id = local_id
                self.id_token = id_token
            # Puxando o banco de dados
            requisicao = requests.get(f"https://appvendas-81a96-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}")
            link = requisicao.json()
            # mudando a imagem de perfil
            avatar = link['avatar']
            self.avatar = avatar
            foto_perfil = self.root.ids["foto_perfil"]
            foto_perfil.source = f"icones/fotos_perfil/{avatar}"

            # mudando id:
            id_vendedor = link['id_vendedor']
            self.id_vendedor = id_vendedor
            pagina_ajustes = self.root.ids["configuracao"]
            pagina_ajustes.ids["id_vendedor"].text = f"Seu ID único: {id_vendedor}"

            # total de vendas :
            total_vendas = link['total_vendas']
            self.total_vendas = total_vendas
            homepage = self.root.ids["homepage"]
            homepage.ids["label_total_vendas"].text = f"[color=#000000]Total de Vendas:[/color] R$ [b]{total_vendas}[/b]"
            # lista de venda
            vendas = link['vendas']
            self.vendas = vendas
            try:
                for id_venda in vendas:
                    venda = vendas[id_venda]
                    banner = BannerVenda(cliente=venda['cliente'], data=venda['data'],
                                         foto_cliente=venda['foto_cliente'], foto_produto=venda['foto_produto'],
                                         preco=venda['preco'], produto=venda['produto'],
                                         quantidade=venda['quantidade'], unidade=venda['unidade'])
                    pagina = self.root.ids["homepage"]
                    lista_vendas = pagina.ids['lista_vendas']
                    lista_vendas.add_widget(banner)

            except Exception as erro:
                print(erro)
            self.mudar_tela("homepage")

            # preencher equipe de vendedores
            equipe = link["equipe"]
            self.equipe = equipe
            lista_equipe = equipe.split(",")
            pagina_listavendedores = self.root.ids["listarvendedorespage"]
            lista_vendedores = pagina_listavendedores.ids["lista_vendedores"]

            for id_vendedor_equipe in lista_equipe:
                if id_vendedor_equipe != "":
                    banner_vendedor = BannerVendedor(id_vendedor=id_vendedor_equipe)
                    lista_vendedores.add_widget(banner_vendedor)

        except:
            pass

    def mudar_tela(self, id_tela):
        gerenciador_telas = self.root.ids["screen_manager"]
        gerenciador_telas.current = id_tela

        # atualizar imagem no ap

    def mudar_foto_perfil(self, foto, *args):
        foto_perfil = self.root.ids["foto_perfil"]
        foto_perfil.source = f"icones/fotos_perfil/{foto}"

        # atualizar no banco de dados

        info = f'{{"avatar": "{foto}"}}'

        rjson = requests.patch(f"https://appvendas-81a96-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}",
                               data=info)

        self.mudar_tela("configuracao")

    def adicionar_vendedor(self, id_vendedor_adicionado):
        link = f'https://appvendas-81a96-default-rtdb.firebaseio.com/.json?orderBy="id_vendedor"&equalTo="{id_vendedor_adicionado}"'
        requisicao = requests.get(link)
        requisicao_dic = requisicao.json()

        pagina_addvendedor = self.root.ids["adicionarvendedorpage"]
        text_certo = pagina_addvendedor.ids["mensagem_outro_vendedor"]

        if requisicao_dic == {}:
            text_certo.text = "Usuário não encontrado"
        else:
            equipe = self.equipe.split(",")
            if id_vendedor_adicionado in equipe:
                text_certo.text = "Vendedor já faz parte da equipe"
            else:
                self.equipe = self.equipe + f",{id_vendedor_adicionado}"
                info = f'{{ "equipe": "{self.equipe}"}}'
                requests.patch(f"https://appvendas-81a96-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}", data=info)
                text_certo.text = "Vendedor adicionado com sucesso"

                # Adicionar um novo banner na lista de vendedores

                pagina_listavendedores = self.root.ids["listarvendedorespage"]
                lista_vendedores = pagina_listavendedores.ids["lista_vendedores"]
                banner_vendedor = BannerVendedor(id_vendedor=id_vendedor_adicionado)
                lista_vendedores.add_widget(banner_vendedor)


    def selecionar_produto (self, foto_produto, *args):
        self.produto = foto_produto.replace(".png", "")
        pagina_adicionarvenda = self.root.ids["adicionarvendaspage"]
        lista_produtos = pagina_adicionarvenda.ids["lista_produtos"]
        for item in lista_produtos.children:
            item.color =(0, 207 / 255, 219 / 255, 1)
            try:
                texto = item.text
                texto = texto.lower() + ".png"
                if foto_produto == texto:
                   item.color = (1, 0, 0, 1)
            except:
                pass

    def selecionar_cliente(self, foto_cliente, *args):
        self.cliente = foto_cliente.replace(".png", "")
        # pintar de branco todas as outras letras
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        lista_clientes = pagina_adicionarvendas.ids["lista_clientes"]

        for item in lista_clientes.children:
            item.color = (0, 207 / 255, 219 / 255, 1)
            try:
                texto = item.text
                texto = texto.lower() + ".png"
                if foto_cliente == texto:
                    texto.color = (0, 207 / 255, 219 / 255, 1)
            except:
                pass

    def selecionar_unidade(self, id_label, *args):
        self.unidade = id_label.replace("unidades_", "")
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]

        pagina_adicionarvendas.ids["unidades_kg"].color = (1, 1, 1, 1)
        pagina_adicionarvendas.ids["unidades_unidades"].color = (1, 1, 1, 1)
        pagina_adicionarvendas.ids["unidades_litros"].color = (1, 1, 1, 1)
        pagina_adicionarvendas.ids[id_label].color = (0, 207 / 255, 219 / 255, 1)


    def adicionar_venda(self, *args):
        produto = self.produto
        unidade = self.unidade
        cliente = self.cliente
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        data = pagina_adicionarvendas.ids["label_data"].text.replace("Data: ", "")
        preco = pagina_adicionarvendas.ids["preco_total"].text
        quantidade = pagina_adicionarvendas.ids["quantidade_total"].text

        if not cliente:
            pagina_adicionarvendas.ids["label_selecione_cliente"].color = (1, 0, 0, 1)
        if not produto:
            pagina_adicionarvendas.ids["label_selecione_produto"].color = (1, 0, 0, 1)

        if not unidade:
            pagina_adicionarvendas.ids["unidades_kg"].color = (1, 0, 0, 1)
            pagina_adicionarvendas.ids["unidades_unidades"].color = (1, 0, 0, 1)
            pagina_adicionarvendas.ids["unidades_litros"].color = (1, 0, 0, 1)

        if not preco:
            pagina_adicionarvendas.ids["label_preco"].color = (1, 0, 0, 1)
        else:
            try:
                preco = float(preco)
            except:
                pagina_adicionarvendas.ids["label_preco"].color = (1, 0, 0, 1)

        if not quantidade:
            pagina_adicionarvendas.ids["label_quantidade"].color = (1, 0, 0, 1)
        else:
            try:
                quantidade = float(quantidade)
            except:
                pagina_adicionarvendas.ids["label_quantidade"].color = (1, 0, 0, 1)

        if cliente and produto and unidade and preco and quantidade and (type(preco) == float) and (type(quantidade) ==float):
            foto_produto = produto + ".png"
            foto_cliente = cliente + ".png"

            # Mandando as vendas pro banco de dados :

            info = f'{{"cliente": "{cliente}", "produto": "{produto}", "data": "{data}", "unidade": "{unidade}","foto_cliente": "{foto_cliente}"' \
                   f',"foto_produto": "{foto_produto}", "preco": "{preco}", "quantidade": "{quantidade}"}}'
            requests.post(f"https://appvendas-81a96-default-rtdb.firebaseio.com/{self.local_id}/vendas.json?auth={self.id_token}", data=info)
            # atualizando o banner de vendas:

            banner = BannerVenda(cliente=cliente, produto=produto, foto_cliente=foto_cliente, foto_produto=foto_produto,
                                 data=data, preco=preco, quantidade=quantidade, unidade=unidade)
            pagina_homepage = self.root.ids["homepage"]
            lista_vendas = pagina_homepage.ids["lista_vendas"]
            lista_vendas.add_widget(banner)


            # atualizar total de vendas
            link = requests.get(f"https://appvendas-81a96-default-rtdb.firebaseio.com/{self.local_id}/total_vendas.json?auth={self.id_token}")
            total_vendas = float(link.json())
            total_vendas += preco
            info = f'{{"total_vendas": "{total_vendas}"}}'
            requests.patch(f"https://appvendas-81a96-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}", data=info)
            homepage = self.root.ids["homepage"]
            homepage.ids["label_total_vendas"].text = f"[color=#000000]Total de Vendas:[/color] R$ [b]{total_vendas}[/b]"
            self.mudar_tela("homepage")

        self.produto = None
        self.unidade = None
        self.cliente = None

    def carregar_todasasvendas(self):
        # preencher infos da homepage :
        # Puxando o banco de dados

        pagina_todasvendas = self.root.ids["todasvendaspage"]
        lista_vendas = pagina_todasvendas.ids["lista_vendas"]

        for item in list(lista_vendas.children):
            lista_vendas.remove_widget(item)

        link = requests.get(f'https://appvendas-81a96-default-rtdb.firebaseio.com/.json?orderBy="id_vendedor"')
        requisicao = link.json()

        # mudar foto de perfil :

        foto_perfil = self.root.ids["foto_perfil"]
        foto_perfil.source = f"icones/fotos_perfil/hash.png"
        # banner venda

        total_vendas = 0
        for id_novo in requisicao:
            try:
                vendas = requisicao[id_novo]["vendas"]
                for id_venda in vendas:
                    venda = vendas[id_venda]
                    total_vendas += float(venda["preco"])
                    banner = BannerVenda(cliente=venda['cliente'], data=venda['data'],
                                         foto_cliente=venda['foto_cliente'], foto_produto=venda['foto_produto'],
                                         preco=venda['preco'], produto=venda['produto'],
                                         quantidade=venda['quantidade'], unidade=venda['unidade'])
                    lista_vendas.add_widget(banner)
            except:
                pass
         # total de vendas :
        pagina_todasvendas.ids["label_total_vendas"].text = f"[color=#000000]Total de Vendas:[/color] R$ [b]{total_vendas}[/b]"
        self.mudar_tela("todasvendaspage")

    def voltar_infos(self, id_tela):
        foto_perfil = self.root.ids["foto_perfil"]
        foto_perfil.source = f"icones/fotos_perfil/{self.avatar}"
        self.mudar_tela(id_tela)

    def carregar_vendas_vendedor(self, dic_id_vendedor, *args):
        try:
            pagina_vendas_outro_vendedor = self.root.ids["vendasoutrovendedor"]
            lista_vendas = pagina_vendas_outro_vendedor.ids["lista_vendas"]
            vendas = dic_id_vendedor["vendas"]
            # Limpar lista de vendas anteriores
            for item in list(lista_vendas.children):
                lista_vendas.remove_widget(item)
            for id_venda in vendas:
                venda = vendas[id_venda]
                banner = BannerVenda(cliente=venda['cliente'], data=venda['data'],
                                     foto_cliente=venda['foto_cliente'], foto_produto=venda['foto_produto'],
                                     preco=venda['preco'], produto=venda['produto'],
                                     quantidade=venda['quantidade'], unidade=venda['unidade'])
                lista_vendas.add_widget(banner)
        except:
            pass
        # total_vendas
        total_vendas = dic_id_vendedor["total_vendas"]
        pagina_vendas_outro_vendedor.ids["label_total_vendas"].text = f"[color=#000000]Total de Vendas:[/color] R$ [b]{total_vendas}[/b]"
        self.mudar_tela("vendasoutrovendedor")

        foto_perfil = self.root.ids["foto_perfil"]
        avatar = dic_id_vendedor["avatar"]
        foto_perfil.source = f"icones/fotos_perfil/{avatar}"


MainApp().run()
