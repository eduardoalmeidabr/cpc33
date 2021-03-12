import pandas as pd
import helper as h
import datetime as dt
import pyliferisk as lr
import tabuas_atuariais as t
import parametros as p
import time
from pyliferisk.mortalitytables import RP2000F, RP2000M
from progress.bar import IncrementalBar

"""
!IMPORTANT Necessário implementar a lógica dos PDVEs e revisitar as fórmulas e
modelagem da planilha Excel
"""

# Base de dados em Excel
df = pd.read_excel(io = r'saude_caixa.xlsx', sheet_name = 'dados_ativos')

# Cria uma lista com os valores totais para exportar para o Excel
reservas_individuais = []

bar = IncrementalBar('Processing', max = len(df.index))

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
    tempo_servico_fixo = tempo_servico
    tipo_dependente = df['tipo_dependente'][i]
    relacao_dependencia = df['relacao_dependencia'][i]
    condicao_participante = df['condicao_participante'][i]
    pdve_temporario = df['pdve_temporario'][i]
    idade_aposentadoria = h.idade_aposentadoria(idade, sexo)
    idade_conjuge = h.idade_conjuge(idade, idade_aposentadoria, sexo)
    idade_conjuge_br = h.idade_conjuge_br(idade, sexo)
    idade_conjuge_br_anterior = h.idade_conjuge_br(idade - 1, sexo)
    idade_dependente_temporario = h.idade_dependente_temporario(idade, idade_aposentadoria, sexo)

    # Valores do primeiro período
    elegibilidade = h.elegibilidade(idade, idade_aposentadoria)
    auxiliar_elegibilidade = h.auxiliar_elegibilidade(idade, idade_aposentadoria)
    elegibilidade_anterior = h.elegibilidade(idade - 1, idade_aposentadoria)
    auxiliar_elegibilidade_anterior = h.auxiliar_elegibilidade(idade - 1, idade_aposentadoria)
    rateio = 1.0

    # Custo posicionado
    custo_posicionado_titular = p.custo_medio * pow(1 + p.aging_factor, idade - p.idade_media)
    custo_posicionado_conjuge = p.custo_medio * pow(1 + p.aging_factor, idade_conjuge - p.idade_media)
    custo_posicionado_temp = 0.0 if idade_dependente_temporario < 0 else p.custo_medio * pow(1 + p.aging_factor, idade_dependente_temporario - p.idade_media)

    # Custos médios posicionados
    custo_medio_posicionado_titular = custo_posicionado_titular * pow(1 + p.taxa_crescimento_folha, 0)
    custo_medio_posicionado_conjuge = custo_posicionado_conjuge * pow(1 + p.taxa_crescimento_folha, 0)
    custo_medio_posicionado_temp = custo_posicionado_temp * pow(1 + p.taxa_crescimento_folha, 0)

    mensalizacao = h.mensalizacao(idade, sexo)
    mensalizacao_conjuge = h.mensalizacao(idade_conjuge, 'F' if sexo == 'M' else 'M')
    mensalizacao_conjuge_2 = h.mensalizacao(idade, 'F' if sexo == 'M' else 'M')
    """
    O passivo programado do dependente temporário está usando o fator de mensa-
    lização a partir da idade do conjuge e do sexo do titular, o que é algo que 
    deve ser revisitado. No entanto, foi mantida a "lógica" aqui para os resultados
    se aproximarem daqueles do Excel.
    """
    mensalizacao_3 = h.mensalizacao(idade_conjuge, sexo)

    qx = h.qx(idade, sexo)
    qy = h.qx(idade_conjuge, 'F' if sexo == 'M' else 'M')
    qy_br = h.qx(idade_conjuge_br, 'F' if sexo == 'M' else 'M')
    qz = h.qx(idade_dependente_temporario, sexo)
    ix = h.ix(elegibilidade, idade, pdve_temporario)
    wx = h.wx(elegibilidade, idade, pdve_temporario)
    qxi = h.qxi(idade)

    qx_anterior = h.qx(idade - 1, sexo)
    qy_anterior = h.qx(idade_conjuge - 1, 'F' if sexo == 'M' else 'M')
    qy_br_anterior = h.qx(idade_conjuge_br_anterior, 'F' if sexo == 'M' else 'M')
    qz_anterior = h.qx(idade_dependente_temporario - 1, sexo)
    ix_anterior = h.ix(elegibilidade_anterior, idade - 1, pdve_temporario)
    wx_anterior = h.wx(elegibilidade_anterior, idade - 1, pdve_temporario)
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
    # Para os benefícios de risco, é utilizada a idade atual do empregado
    # para calcular o percentual de casados
    perc_casados_2 = h.perc_casados(idade, sexo)

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
    auxiliar_pensao_morte_temp = 0.0 if elegibilidade else tpxaa * custo_posicionado_temp * rateio * qx

    # Passivos
    passivo_titular = 0.0 if not elegibilidade else custo_posicionado_titular * tpx * tpix * tpwx * rateio * \
        vx * p.fator_capacidade * mensalizacao

    passivo_conjuge = 0.0 if not elegibilidade else custo_posicionado_conjuge * perc_casados * tpx_aux_conj * \
        tpix * tpwx * tpy * p.fator_capacidade * rateio * vx * mensalizacao_conjuge

    passivo_aposentadoria_invalidez = auxiliar_invalidez_titular * vx * p.fator_capacidade * mensalizacao

    passivo_reversao_invalidez = auxiliar_invalidez_conjuge * perc_casados_2 * vx * \
        p.fator_capacidade * mensalizacao_conjuge_2

    passivo_pensao_morte = auxiliar_pensao_morte_ativo * perc_casados_2 * vx * p.fator_capacidade * \
        mensalizacao_conjuge_2

    # Beneficio programado do dependente temporário. Usa-se o perc. casados da idade
    # de aposentadoria
    passivo_programado_temporario = 0.0 if not elegibilidade or idade_dependente_temporario > 23 else \
        custo_medio_posicionado_temp * tpx_aux_conj * tpix * \
        tpwx * vx * rateio * p.fator_capacidade * perc_casados * mensalizacao_3

    passivo_reversao_invalidez_temp = auxiliar_reversao_invalidez_temp * perc_casados_2 * \
        vx * p.fator_capacidade * mensalizacao

    passivo_pensao_morte_temp = auxiliar_pensao_morte_temp * perc_casados_2 * vx * \
        p.fator_capacidade * mensalizacao

    # Valores a partir do segundo período
    for j in range(idade + 1, 121):
        # Totais dos passivos
        total_programado_titular += passivo_titular
        total_programado_conjuge += passivo_conjuge
        total_invalidez += passivo_aposentadoria_invalidez
        total_reversao_invalidez += passivo_reversao_invalidez
        total_pensao_morte += passivo_pensao_morte
        total_programado_temp += passivo_programado_temporario
        total_reversao_invalidez_temp += passivo_reversao_invalidez_temp
        total_pensao_morte_temp += passivo_pensao_morte_temp

        # Cria lista multidimensional com os valores das reservas dos participantes
        reservas_individuais.append([carteira, total_programado_titular, \
            total_programado_conjuge, total_invalidez, total_reversao_invalidez, \
            total_pensao_morte, total_pensao_morte, total_programado_temp, \
            total_reversao_invalidez_temp, total_pensao_morte_temp])

        # Valores do primeiro período
        idade_conjuge += 1
        idade_dependente_temporario += 1
        idade_conjuge_br = h.idade_conjuge_br(j, sexo)
        idade_conjuge_br_anterior = h.idade_conjuge_br(j - 1, sexo)
        tempo_servico = tempo_servico if elegibilidade else tempo_servico + 1
        elegibilidade = h.elegibilidade(j, idade_aposentadoria)
        auxiliar_elegibilidade = h.auxiliar_elegibilidade(j, idade_aposentadoria)
        elegibilidade_anterior = h.elegibilidade(j - 1, idade_aposentadoria)
        auxiliar_elegibilidade_anterior = h.auxiliar_elegibilidade(j - 1, idade_aposentadoria)
        rateio = tempo_servico_fixo / tempo_servico
        perc_casados_2 = h.perc_casados(j, sexo)

        qx = h.qx(j, sexo)
        qy = h.qx(idade_conjuge, 'F' if sexo == 'M' else 'M')
        qy_br = h.qx(idade_conjuge_br, 'F' if sexo == 'M' else 'M')
        qz = h.qx(idade_dependente_temporario, sexo)
        ix = h.ix(elegibilidade, j, pdve_temporario)
        wx = h.wx(elegibilidade, j, pdve_temporario)
        qxi = h.qxi(j)

        qx_anterior = h.qx(j - 1, sexo)
        qy_anterior = h.qx(idade_conjuge - 1, 'F' if sexo == 'M' else 'M')
        qy_br_anterior = h.qx(idade_conjuge_br_anterior, 'F' if sexo == 'M' else 'M')
        qz_anterior = h.qx(idade_dependente_temporario - 1, sexo)
        ix_anterior = h.ix(elegibilidade_anterior, j - 1, pdve_temporario)
        wx_anterior = h.wx(elegibilidade_anterior, j - 1, pdve_temporario)
        qxi_anterior = h.qxi(j - 1)

        tpx *= (1 - qx_anterior)
        tpx_aux_conj = tpx_aux_conj if elegibilidade and not auxiliar_elegibilidade else tpx_aux_conj * (1 - qx_anterior)
        tpy = 1.0 if (elegibilidade and auxiliar_elegibilidade) or (not elegibilidade \
            and not auxiliar_elegibilidade) else tpy * (1 - qy_anterior)
        tpz = 1.0 if (elegibilidade and auxiliar_elegibilidade) or \
            (not elegibilidade and not auxiliar_elegibilidade) else tpz * (1 - qz_anterior)
        tpix *= (1 - ix_anterior)
        tpwx *= (1 - wx_anterior)
        tpxaa = tpxaa * (1 - qx_anterior) if elegibilidade_anterior else tpxaa * (1 - (qx_anterior + ix_anterior + wx_anterior))
        tpxaa_aposentadoria = tpxaa_aposentadoria if elegibilidade_anterior else tpxaa
        tpyaa = tpyaa * (1 - qy_br_anterior) if elegibilidade_anterior else tpyaa * (1 - (qy_br_anterior + ix_anterior + wx_anterior))
        tpyaa_aposentadoria = tpyaa_aposentadoria if elegibilidade_anterior else tpyaa
        vx = h.vx(j - idade, p.taxa_desconto)

        # Custos médios posicionados
        custo_medio_posicionado_titular = custo_posicionado_titular * pow(1 + p.taxa_crescimento_folha, j - idade)
        custo_medio_posicionado_conjuge = custo_posicionado_conjuge * pow(1 + p.taxa_crescimento_folha, j - idade)
        custo_medio_posicionado_temp = custo_posicionado_temp * pow(1 + p.taxa_crescimento_folha, j - idade)

        # Beneficios
        beneficio_invalidez_titular = 0.0 if elegibilidade else custo_posicionado_titular
        beneficio_invalidez_conjuge = 0.0 if elegibilidade else custo_posicionado_conjuge

        # Funções auxiliares
        auxiliar_invalidez_titular = auxiliar_invalidez_titular * (1 - qxi_anterior) if elegibilidade_anterior else \
            auxiliar_invalidez_titular * (1 - qxi_anterior) + tpxaa_aposentadoria * beneficio_invalidez_titular * \
            rateio * ix
        # Atualizar qy_br r criar qy_br_anterior
        auxiliar_invalidez_conjuge = auxiliar_invalidez_conjuge * (1 - qy_br_anterior) if elegibilidade_anterior else \
            auxiliar_invalidez_conjuge * (1 - qy_br_anterior) + tpxaa_aposentadoria * beneficio_invalidez_conjuge * ix * rateio
        # ----------
        auxiliar_pensao_morte_ativo = auxiliar_pensao_morte_ativo * (1 - qy_br_anterior) + tpxaa * beneficio_invalidez_conjuge * rateio * qx
        # -----------
        auxiliar_reversao_invalidez_temp = 0.0 if idade_dependente_temporario > 23 else auxiliar_reversao_invalidez_temp * (1 - qz_anterior) if elegibilidade_anterior else \
            auxiliar_reversao_invalidez_temp * (1 - qz_anterior) + custo_posicionado_temp * tpxaa_aposentadoria * rateio * ix
        # -----------
        auxiliar_pensao_morte_temp = 0.0 if elegibilidade or idade_dependente_temporario > 23 else auxiliar_pensao_morte_temp * (1 - qz_anterior) if elegibilidade_anterior else \
            auxiliar_pensao_morte_temp * (1 - qz_anterior) + tpxaa * custo_posicionado_temp * rateio * qx

        # Passivo programado do titular
        passivo_titular = 0.0 if not elegibilidade else custo_posicionado_titular * tpx * tpix * tpwx * rateio * \
            vx * p.fator_capacidade * mensalizacao

        # Passivos do conjuge
        passivo_conjuge = 0.0 if not elegibilidade else custo_posicionado_conjuge * perc_casados * tpx_aux_conj * \
            tpix * tpwx * tpy * p.fator_capacidade * rateio * vx * mensalizacao_conjuge

        passivo_aposentadoria_invalidez = auxiliar_invalidez_titular * vx * p.fator_capacidade * mensalizacao

        passivo_reversao_invalidez = auxiliar_invalidez_conjuge * perc_casados_2 * vx * \
            p.fator_capacidade * mensalizacao_conjuge_2

        passivo_pensao_morte = auxiliar_pensao_morte_ativo * perc_casados_2 * vx * p.fator_capacidade * \
            mensalizacao_conjuge_2

        # Passivos do dependente temporário
        passivo_programado_temporario = 0.0 if not elegibilidade or idade_dependente_temporario > 23 else \
            custo_medio_posicionado_temp * tpx_aux_conj * tpix * \
            tpwx * vx * rateio * p.fator_capacidade * perc_casados * mensalizacao_3

        passivo_reversao_invalidez_temp = auxiliar_reversao_invalidez_temp * perc_casados_2 * \
            vx * p.fator_capacidade * mensalizacao

        passivo_pensao_morte_temp = auxiliar_pensao_morte_temp * perc_casados_2 * vx * \
            p.fator_capacidade * mensalizacao
    
    bar.next()

bar.finish()

# Cria dataframe com os totais dos passivos
resultados = pd.DataFrame(reservas_individuais, columns = ["Carteira", "Passivo Programado Titular", \
    "Passivo Programado Conjuge", "Passivo Por Invalidez", "Passivo Reversão Invalidez - Conjuge", \
    "Passivo Programado Temporário", "Reversão INvalidez Temporário", "Pensão Por Morte Temporário"])

# Insere dataframe no Excel
resultados.to_excel(io = r'saude_caixa', sheet_name='reservas_individuais', index = False, header = True)
