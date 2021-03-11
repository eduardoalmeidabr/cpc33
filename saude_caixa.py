import pandas as pd, helper as h, datetime as dt, pyliferisk as lr, \
    tabuas_atuariais as t, parametros as p
from pyliferisk.mortalitytables import RP2000F, RP2000M

# Base de dados em Excel
df = pd.read_excel(io = r'saude_caixa.xlsx', sheet_name = 'Plan1')

# Itera por cada participante na base de dados
for i in range(1): # df.index:
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
    tempo_servico_fixo = tempo_servico
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
    elegibilidade_anterior = h.elegibilidade(idade - 1, idade_aposentadoria)
    auxiliar_elegibilidade_anterior = h.auxiliar_elegibilidade(idade - 1, idade_aposentadoria)
    rateio = 1.0
    crescimento_folha = h.crescimento_folha(0, p.taxa_crescimento_folha)

    # Custo posicionado
    custo_posicionado_titular = p.custo_medio * pow(1 + p.aging_factor, idade - p.idade_media)
    custo_posicionado_conjuge = p.custo_medio * pow(1 + p.aging_factor, idade_conjuge - p.idade_media)
    custo_posicionado_temp = p.custo_medio * pow(1 + p.aging_factor, idade_dependente_temporario - p.idade_media)

    # Custos médios posicionados
    custo_medio_posicionado_titular = crescimento_folha * custo_posicionado_titular
    custo_medio_posicionado_conjuge = crescimento_folha * custo_posicionado_conjuge
    custo_medio_posicionado_temp = crescimento_folha * custo_posicionado_temp

    mensalizacao = h.mensalizacao(idade, sexo)
    mensalizacao_conjuge = h.mensalizacao(idade_conjuge, 'F' if sexo == 'M' else 'M')

    qx = h.qx(idade, sexo)
    qy = h.qx(idade, 'F' if sexo == 'M' else 'M')
    qy_br = h.qx(idade, 'F' if sexo == 'M' else 'M')
    qz = h.qx(idade_dependente_temporario, sexo)
    ix = h.ix(elegibilidade, idade, pdve_temporario)
    wx = h.wx(elegibilidade, idade, pdve_temporario)
    qxi = h.qxi(idade)

    qx_anterior = h.qx(idade - 1, sexo)
    qy_anterior = h.qx(idade - 1, 'F' if sexo == 'M' else 'M')
    qz_anterior = h.qx(idade_dependente_temporario - 1, sexo)
    ix_anterior = h.ix(elegibilidade, idade - 1, pdve_temporario)
    wx_anterior = h.wx(elegibilidade, idade - 1, pdve_temporario)
    qxi_anterior = h.qxi(idade - 1)

    tpx = 1.0
    tpx_aux_conj = 1.0
    tpy = 1.0
    tpz = 1.0
    tpix = 1.0
    tpwx = 1.0
    tpxaa = 1.0
    tpxaa_aposentadoria = 1.0
    tpyaa = 1.0
    tpyaa_aposentadoria = 1.0
    vx = h.vx(0, p.taxa_desconto)
    perc_casados = h.perc_casados(idade_aposentadoria, sexo)

    # Beneficios
    beneficio_invalidez_titular = 0.0 if elegibilidade else custo_posicionado_titular
    beneficio_invalidez_conjuge = 0.0 if elegibilidade else custo_posicionado_conjuge

    # Funções auxiliares
    auxiliar_invalidez_titular = tpxaa_aposentadoria * beneficio_invalidez_titular * \
        rateio * ix
    auxiliar_invalidez_conjuge = tpxaa_aposentadoria * beneficio_invalidez_conjuge * \
        ix * rateio
    auxiliar_pensao_morte_ativo = tpxaa * beneficio_invalidez_conjuge * \
        rateio * qx
    auxiliar_reversao_invalidez_temp = custo_posicionado_temp * tpxaa_aposentadoria * \
        rateio * ix
    auxiliar_pensao_morte_temp = tpxaa * custo_posicionado_temp * rateio * qx

    # Passivos
    passivo_titular = 0.0 if not elegibilidade else custo_posicionado_titular * tpx * tpix * tpwx * rateio * \
        vx * p.fator_capacidade * mensalizacao
    passivo_conjuge = 0.0 if elegibilidade else custo_posicionado_conjuge * perc_casados * tpx_aux_conj * \
        tpix * tpwx * tpy * p.fator_capacidade * rateio * vx * mensalizacao_conjuge
    passivo_aposentadoria_invalidez = auxiliar_invalidez_titular * vx * p.fator_capacidade * mensalizacao
    passivo_reversao_invalidez = auxiliar_invalidez_conjuge * perc_casados * vx * \
        p.fator_capacidade * mensalizacao
    passivo_pensao_morte = auxiliar_pensao_morte_ativo * perc_casados * vx * p.fator_capacidade * \
        mensalizacao
    passivo_programado_temporario = custo_posicionado_temp * tpx_aux_conj * tpix * \
        tpwx * vx * rateio * p.fator_capacidade * perc_casados * mensalizacao_conjuge
    passivo_reversao_invalidez_temp = auxiliar_reversao_invalidez_temp * perc_casados * \
        vx * p.fator_capacidade * mensalizacao
    passivo_pensao_morte_temp = auxiliar_pensao_morte_temp * perc_casados * vx * \
        p.fator_capacidade * mensalizacao

    # Valores a partir do segundo período
    for j in range(idade + 1, 121):
        print(carteira, crescimento_folha, custo_medio_posicionado_titular)
        # Totais dos passivos
        total_programado_titular += passivo_titular
        total_programado_conjuge += passivo_conjuge
        total_invalidez += passivo_aposentadoria_invalidez
        total_reversao_invalidez += passivo_reversao_invalidez
        total_pensao_morte += passivo_pensao_morte
        total_programado_temp += passivo_programado_temporario
        total_reversao_invalidez_temp += passivo_reversao_invalidez_temp
        total_pensao_morte_temp += passivo_pensao_morte_temp

        # Valores do primeiro período
        idade_conjuge += 1
        idade_dependente_temporario += 1
        idade_conjuge_br = h.idade_conjuge_br(j, sexo)
        elegibilidade = h.elegibilidade(j, idade_aposentadoria)
        auxiliar_elegibilidade = h.auxiliar_elegibilidade(j, idade_aposentadoria)
        elegibilidade_anterior = h.elegibilidade(j - 1, idade_aposentadoria)
        auxiliar_elegibilidade_anterior = h.auxiliar_elegibilidade(j - 1, idade_aposentadoria)
        rateio = tempo_servico_fixo / tempo_servico
        crescimento_folha *= h.crescimento_folha(j - idade, p.taxa_crescimento_folha)

        qx = h.qx(j, sexo)
        qy = h.qx(j, 'F' if sexo == 'M' else 'M')
        qy_br = h.qx(j, 'F' if sexo == 'M' else 'M')
        qz = h.qx(idade_dependente_temporario, sexo)
        ix = h.ix(elegibilidade, idade, pdve_temporario)
        wx = h.wx(elegibilidade, idade, pdve_temporario)
        qxi = h.qxi(idade)

        qx_anterior = h.qx(j - 1, sexo)
        qy_anterior = h.qx(j - 1, 'F' if sexo == 'M' else 'M')
        qz_anterior = h.qx(idade_dependente_temporario - 1, sexo)
        ix_anterior = h.ix(elegibilidade, j - 1, pdve_temporario)
        wx_anterior = h.wx(elegibilidade, j - 1, pdve_temporario)
        qxi_anterior = h.qxi(j - 1)
    
        tpx *= (1 - qx_anterior)
        tpx_aux_conj = tpx_aux_conj if elegibilidade or not auxiliar_elegibilidade else tpx_aux_conj * (1 - qx_anterior)
        tpy *= (1 - qy_anterior)
        tpz = 1.0 if (elegibilidade and auxiliar_elegibilidade) or \
            (not elegibilidade and not auxiliar_elegibilidade) else tpz * (1 - qz_anterior)
        tpix *= (1 - ix_anterior)
        tpwx *= (1 - wx_anterior)
        tpxaa = tpxaa * (1 - qx_anterior) if elegibilidade_anterior else tpxaa * (1 - (qx_anterior + ix_anterior + wx_anterior))
        tpxaa_aposentadoria = tpxaa_aposentadoria if elegibilidade_anterior else tpxaa
        # TODO Verificar o qy_br_anterior como calcula
        tpyaa = tpyaa * (1 - qy_br) if elegibilidade_anterior else tpyaa * (1 - (qy_br + ix_anterior + wx_anterior))
        tpyaa_aposentadoria = tpyaa_aposentadoria if elegibilidade_anterior else tpyaa
        vx = h.vx(j - idade, p.taxa_desconto)
        tempo_servico += 1

        # Custos médios posicionados
        custo_medio_posicionado_titular = crescimento_folha * custo_posicionado_titular
        custo_medio_posicionado_conjuge = crescimento_folha * custo_posicionado_conjuge
        custo_medio_posicionado_temp = crescimento_folha * custo_posicionado_temp

        # Beneficios
        beneficio_invalidez_titular = 0.0 if elegibilidade else custo_posicionado_titular
        beneficio_invalidez_conjuge = 0.0 if elegibilidade else custo_posicionado_conjuge

        # Funções auxiliares
        # TODO Atualizar as fórmulas das funções auxiliares
        auxiliar_invalidez_titular = tpxaa_aposentadoria * beneficio_invalidez_titular * \
            rateio * ix
        auxiliar_invalidez_conjuge = tpxaa_aposentadoria * beneficio_invalidez_conjuge * \
            ix * rateio
        auxiliar_pensao_morte_ativo = tpxaa * beneficio_invalidez_conjuge * \
            rateio * qx
        auxiliar_reversao_invalidez_temp = custo_posicionado_temp * tpxaa_aposentadoria * \
            rateio * ix
        auxiliar_pensao_morte_temp = tpxaa * custo_posicionado_temp * rateio * qx

        # Passivos
        passivo_titular = 0.0 if not elegibilidade else custo_posicionado_titular * tpx * tpix * tpwx * rateio * \
            vx * p.fator_capacidade * mensalizacao  
        passivo_conjuge = 0.0 if not elegibilidade else custo_posicionado_conjuge * perc_casados * tpx_aux_conj * \
            tpix * tpwx * tpy * p.fator_capacidade * rateio * vx * mensalizacao_conjuge
        passivo_aposentadoria_invalidez = auxiliar_invalidez_titular * vx * p.fator_capacidade * mensalizacao
        passivo_reversao_invalidez = auxiliar_invalidez_conjuge * perc_casados * vx * \
            p.fator_capacidade * mensalizacao
        passivo_pensao_morte = auxiliar_pensao_morte_ativo * perc_casados * vx * p.fator_capacidade * \
            mensalizacao
        passivo_programado_temporario = custo_posicionado_temp * tpx_aux_conj * tpix * \
            tpwx * vx * rateio * p.fator_capacidade * perc_casados * mensalizacao_conjuge
        passivo_reversao_invalidez_temp = auxiliar_reversao_invalidez_temp * perc_casados * \
            vx * p.fator_capacidade * mensalizacao
        passivo_pensao_morte_temp = auxiliar_pensao_morte_temp * perc_casados * vx * \
            p.fator_capacidade * mensalizacao

        
