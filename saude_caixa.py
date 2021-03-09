import pandas as pd, helper as h, datetime as dt, pyliferisk as lr, \
    tabuas_atuariais as t, parametros as p
from pyliferisk.mortalitytables import RP2000F, RP2000M

# Base de dados em Excel
df = pd.read_excel(io = r'saude_caixa.xlsx', sheet_name = 'Plan1')

# Itera por cada participante na base de dados
for i in df.index:
    # Totais dos passivos
    total_programado_titular = 0
    total_programado_conjuge = 0
    total_invalidez = 0
    total_reversao_invalidez = 0
    total_pensao_morte = 0
    total_programado_temp = 0
    total_reversao_invalidez_temp = 0
    total_pensao_morte_temp = 0
    total_custo_normal = 0

    # Dados dos participantes
    carteira = df['carteira'][i]
    sexo = df['sexo'][i]
    idade = h.idade(df['data_nascimento'][i], p.data_base)
    tempo_servico = h.tempo_servico(df['data_admissao'][i], p.data_base)
    tipo_dependente = df['tipo_dependente'][i]
    relacao_dependencia = df['relacao_dependencia'][i]
    condicao_participante = df['condicao_participante'][i]
    pdve_temporario = df['pdve_temporario'][i]
    idade_aposentadoria = h.idade_aposentadoria(idade, sexo)
    idade_conjuge = h.idade_conjuge(idade, idade_aposentadoria, sexo)
    idade_conjuge_br = h.idade_conjuge_br(idade, sexo)
    idade_dependente_temporario = h.idade_dependente_temporario(idade, idade_aposentadoria, sexo)

    # Valores do primeiro período
    elegibilidade = h.elegibilidade(idade, idade_aposentadoria)
    auxiliar_elegibilidade = h.auxiliar_elegibilidade(idade, idade_aposentadoria)
    rateio = 1.0
    crescimento_folha = h.crescimento_folha(p.taxa_crescimento_folha)

    # Custos posicionados
    custo_posicionado_titular = crescimento_folha * (p.custo_medio * pow(1 + p.aging_factor, \
        idade - p.idade_media))
    custo_posicionado_conjuge = crescimento_folha * (p.custo_medio * pow(1 + p.aging_factor, \
        idade_conjuge - p.idade_media))
    custo_posicionado_temp = crescimento_folha * (p.custo_medio * (pow(1 + p.aging_factor, \
        idade_dependente_temporario - idade_media)))

    mensalizacao = h.mensalizacao(idade, sexo)
    mensalizacao_conjuge = h.mensalizacao(idade_conjuge, 'F' if sexo == 'M' else 'M')

    qx = h.qx(idade, sexo)
    qy = h.qx(idade, 'F' if sexo == 'M' else 'M')
    ix = h.ix(elegibilidade, idade, pdve_temporario)
    wx = h.wx(elegibilidade, idade, pdve_temporario)
    qxi = h.qxi(idade)
    tpx = h.tpx(idade, 0)
    tpx_aux_conj = 1.0
    tpy = 1.0
    tpix = 1.0
    tpwx = 1.0
    tpxaa = 1.0
    tpxaa_aposentadoria = 1.0
    tpyaa = 1.0
    tpyaa_aposentadoria = 1.0
    vx = h.vx(0, p.taxa_desconto)
    perc_casados = h.perc_casados(idade_aposentadoria, sexo)
    
    # Beneficios
    passivo_titular = custo_posicionado_titular * tpx * tpix * tpwx * rateio * \
        vx * p.fator_capacidade * mensalizacao if elegibilidade else 0   
    passivo_conjuge = custo_posicionado_conjuge * perc_casados * tpx_aux_conj * \
        tpix * tpwx * tpy * p.fator_capacidade * rateio * vx * mensalizacao_conjuge if elegibilidade else 0

    print(carteira, tpx, passivo_conjuge, passivo_titular)
    """
    # Valores a partir do segundo período
    for j in range(idade + 1, 122):
        
        idade_conjuge += 1
        elegibilidade = h.elegibilidade(j, idade_aposentadoria)
        auxiliar_elegibilidade = h.auxiliar_elegibilidade(j, idade_aposentadoria)
        qx = h.qx(j, sexo)
        qy = h.qx(idade_conjuge, sexo)
        ix = h.ix(elegibilidade, j, pdve_temporario)
        wx = h.wx(elegibilidade, j, pdve_temporario)
        qxi = h.qxi(idade)

        # Funções biométricas do período anterior
        qx_anterior = h.qx(j - 1, sexo)
        qy_anterior = h.qx(idade_conjuge - 1, sexo)
        ix_anterior = h.ix(elegibilidade, j - 1, pdve_temporario)
        wx_anterior = h.wx(elegibilidade, j - 1, pdve_temporario)
        qxi_anterior = h.qxi(j - 1)
        # As seguintes funções usam as variáveis biométricas do período anterior
        tpx *= (1 - qx_anterior)
        tpx_aux_conj = tpx if elegibilidade and auxiliar_elegibilidade else tpx_aux_conj * (1 - qx)
        if (elegibilidade and auxiliar_elegibilidade) or \
            (not elegibilidade and not auxiliar_elegibilidade):
            tpy = 1.0
        else:
            tpy *= (1 - qy_anterior)

        tpix *= (1 - ix_anterior)
        tpwx *= (1 - wx_anterior)
        tpxaa = 
        vx = h.vx(j - idade, p.taxa_desconto)
    """

        








