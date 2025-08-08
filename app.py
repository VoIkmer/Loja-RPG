import json
import random
import math
from flask import Flask, render_template, request

# Inicializa o aplicativo Flask
app = Flask(__name__)

def carregar_itens():
    """Carrega os itens do arquivo JSON e os agrupa por custo de sorte."""
    with open('itens.json', 'r', encoding='utf-8') as f:
        itens = json.load(f)
    
    itens_por_sorte = {}
    for item in itens:
        sorte = item['custo_de_sorte']
        if sorte not in itens_por_sorte:
            itens_por_sorte[sorte] = []
        itens_por_sorte[sorte].append(item)
    return itens_por_sorte

# --- LÓGICA DE PRÊMIO MÁXIMO (SORTE 20+) TOTALMENTE REFEITA ---
def gerar_itens_especiais(itens_por_sorte):
    """
    Gera uma loja de prêmio máximo aleatória, garantindo itens de alta raridade.
    """
    loja = []
    # Tenta adicionar itens de raridades específicas
    try:
        # 1 Lendário (Custo de Sorte 10)
        if itens_por_sorte.get(10):
            loja.append(random.choice(itens_por_sorte[10]))
        # 2 Épicos (Custo de Sorte 8 ou 9)
        opcoes_epicas = itens_por_sorte.get(8, []) + itens_por_sorte.get(9, [])
        if len(opcoes_epicas) >= 2:
            loja.extend(random.sample(opcoes_epicas, 2))
        # 2 Raros (Custo de Sorte 5, 6 ou 7)
        opcoes_raras = itens_por_sorte.get(5, []) + itens_por_sorte.get(6, []) + itens_por_sorte.get(7, [])
        if len(opcoes_raras) >= 2:
            loja.extend(random.sample(opcoes_raras, 2))
    except Exception as e:
        print(f"Erro ao gerar itens especiais: {e}")

    # Garante que a loja tenha 5 itens, preenchendo com opções de backup se necessário
    while len(loja) < 5:
        loja.append(random.choice(itens_por_sorte.get(1, [{}])) ) # Adiciona um item comum se tudo falhar

    return loja[:5]

# --- LÓGICA PARA SORTE 5-19 TOTALMENTE REFEITA ---
def gerar_itens_comuns(sorte_total, itens_por_sorte):
    """
    Tenta gerar uma lista de ATÉ 5 itens, forçando itens de maior raridade
    com base na Sorte Total.
    """
    # Define o nível mínimo de "qualidade" dos itens com base na sorte
    min_custo_requerido = 1
    if sorte_total >= 16: # Rolagens muito altas
        min_custo_requerido = 5 # Força no mínimo itens Raros (sorte 5+)
    elif sorte_total >= 12: # Rolagens altas
        min_custo_requerido = 3 # Permite Comuns de Sorte alta, mas prioriza melhores

    for _ in range(200): # Mais tentativas para a lógica mais rígida
        loja_tentativa = []
        sorte_restante = sorte_total
        itens_a_colocar = 5
        
        tentativa_atual_min_custo = min_custo_requerido

        while sorte_restante > 0 and itens_a_colocar > 0:
            max_pick = sorte_restante - (itens_a_colocar - 1)
            
            # Filtra as opções para serem IGUAIS OU MAIORES que a qualidade mínima
            opcoes_validas = [s for s in itens_por_sorte.keys() if tentativa_atual_min_custo <= s <= max_pick]

            # Se a regra for muito rígida e não houver opções, relaxa a regra SÓ para esta escolha
            if not opcoes_validas:
                opcoes_validas = [s for s in itens_por_sorte.keys() if s <= max_pick]
                if not opcoes_validas:
                    break # Falha real, não há como continuar

            pesos = [s**3 for s in opcoes_validas] # Mantém o peso agressivo
            custo_escolhido = random.choices(opcoes_validas, weights=pesos, k=1)[0]
            
            item_escolhido = random.choice(itens_por_sorte[custo_escolhido])
            loja_tentativa.append(item_escolhido)
            sorte_restante -= custo_escolhido
            itens_a_colocar -= 1
        
        if sorte_restante == 0:
            return loja_tentativa

    print(f"Não foi possível encontrar uma combinação para sorte {sorte_total}. Tentando uma busca mais simples.")
    # Se a lógica principal falhar, roda uma vez a lógica antiga como backup
    return gerar_itens_simples(sorte_total, itens_por_sorte) if sorte_total < 5 else []


def gerar_itens_simples(sorte_total, itens_por_sorte):
    """Gera uma lista de 'sorte_total' itens com custo 1 (para sorte 1 a 4)."""
    loja = []
    if 1 not in itens_por_sorte or not itens_por_sorte[1]:
        return []
    itens_de_sorte_1 = itens_por_sorte[1]
    for _ in range(sorte_total):
        loja.append(random.choice(itens_de_sorte_1))
    return loja


@app.route('/', methods=['GET', 'POST'])
def loja_rpg():
    itens_loja = []
    mensagem_erro = ""
    sorte_total = 0
    d20_rolado = None
    bonus = 0

    if request.method == 'POST':
        try:
            d20_rolado = random.randint(1, 20)
            
            bonus_str = request.form.get('bonus_sorte', '0')
            try:
                bonus = int(bonus_str)
            except (ValueError, TypeError):
                bonus = 0

            sorte_total = d20_rolado + bonus
            if sorte_total < 0: sorte_total = 0
            
            itens_por_sorte = carregar_itens()

            if sorte_total >= 20:
                itens_loja = gerar_itens_especiais(itens_por_sorte)
            elif sorte_total >= 5:
                itens_loja = gerar_itens_comuns(sorte_total, itens_por_sorte)
            elif sorte_total > 0:
                itens_loja = gerar_itens_simples(sorte_total, itens_por_sorte)
            
            if sorte_total > 0 and not itens_loja:
                mensagem_erro = f"O Vendedor Rogério procurou em seus estoques, mas por um azar do destino, não encontrou uma boa combinação de itens para a sua sorte de {sorte_total}."

        except Exception as e:
            mensagem_erro = f"Ocorreu um erro inesperado: {e}"
            
    return render_template('index.html', 
                           items=itens_loja, 
                           sorte_total=sorte_total, 
                           error_message=mensagem_erro,
                           d20_roll=d20_rolado,
                           bonus=bonus)

if __name__ == '__main__':
    app.run(debug=True)