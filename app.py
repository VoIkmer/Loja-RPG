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

def gerar_itens_especiais(itens_por_sorte):
    """Gera a lista de itens para sorte 20+ (sempre 5 itens)."""
    loja = []
    if 5 in itens_por_sorte and len(itens_por_sorte.get(5, [])) >= 2:
        loja.extend(random.sample(itens_por_sorte[5], 2))
    if 4 in itens_por_sorte and len(itens_por_sorte.get(4, [])) >= 2:
        loja.extend(random.sample(itens_por_sorte[4], 2))
    if 2 in itens_por_sorte and len(itens_por_sorte.get(2, [])) >= 1:
        loja.extend(random.sample(itens_por_sorte[2], 1))
    return loja

def gerar_itens_comuns(sorte_total, itens_por_sorte):
    """Tenta gerar uma lista de ATÉ 5 itens para sorte 5 a 19."""
    for _ in range(50): 
        loja_tentativa = []
        sorte_restante = sorte_total
        itens_a_colocar = 5
        while sorte_restante > 0 and itens_a_colocar > 0:
            max_pick = sorte_restante - (itens_a_colocar - 1)
            opcoes_validas = [s for s in itens_por_sorte.keys() if s <= max_pick]
            if not opcoes_validas:
                break 
            custo_escolhido = random.choice(opcoes_validas)
            item_escolhido = random.choice(itens_por_sorte[custo_escolhido])
            loja_tentativa.append(item_escolhido)
            sorte_restante -= custo_escolhido
            itens_a_colocar -= 1
        if sorte_restante == 0:
            return loja_tentativa
    print(f"Não foi possível encontrar uma combinação para sorte {sorte_total} após 50 tentativas.")
    return []

def gerar_itens_simples(sorte_total, itens_por_sorte):
    """Gera uma lista de 'sorte_total' itens com custo 1 (para sorte 1 a 4)."""
    loja = []
    if 1 not in itens_por_sorte or not itens_por_sorte[1]:
        print(f"AVISO: Tentativa de gerar {sorte_total} itens simples, mas não há itens com 'custo_de_sorte: 1' no JSON.")
        return []
    itens_de_sorte_1 = itens_por_sorte[1]
    for _ in range(sorte_total):
        loja.append(random.choice(itens_de_sorte_1))
    return loja


@app.route('/', methods=['GET', 'POST'])
def loja_rpg():
    # Inicializa todas as variáveis que serão enviadas ao template
    itens_loja = []
    mensagem_erro = ""
    sorte_total = 0
    d20_rolado = None
    bonus = 0

    if request.method == 'POST':
        try:
            # --- LÓGICA ATUALIZADA ---
            # 1. Rola o dado 1d20
            d20_rolado = random.randint(1, 20)
            
            # 2. Pega o bônus do formulário de forma segura
            bonus_str = request.form.get('bonus_sorte', '0')
            bonus = int(bonus_str) if bonus_str.isdigit() else 0

            # 3. Calcula a sorte total
            sorte_total = d20_rolado + bonus
            if sorte_total < 0: sorte_total = 0 # Garante que a sorte não seja negativa
            
            # --- FIM DA LÓGICA ATUALIZADA ---
            
            itens_por_sorte = carregar_itens()

            if sorte_total >= 20:
                itens_loja = gerar_itens_especiais(itens_por_sorte)
            elif sorte_total >= 5:
                itens_loja = gerar_itens_comuns(sorte_total, itens_por_sorte)
            elif sorte_total > 0:
                itens_loja = gerar_itens_simples(sorte_total, itens_por_sorte)
            
            if sorte_total > 0 and not itens_loja:
                mensagem_erro = f"O vendedor procurou em seus estoques, mas por um azar do destino, não encontrou uma boa combinação de itens para a sua sorte de {sorte_total}."

        except (ValueError, TypeError):
            # Fallback em caso de erro inesperado
            mensagem_erro = "Ocorreu um erro ao processar sua sorte."
            
    # Passa as novas variáveis (d20_rolado, bonus) para o template
    return render_template('index.html', 
                           items=itens_loja, 
                           sorte_total=sorte_total, 
                           error_message=mensagem_erro,
                           d20_roll=d20_rolado,
                           bonus=bonus)

if __name__ == '__main__':
    app.run(debug=True)