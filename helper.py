import datetime, tabuas_atuariais, pyliferisk as lr, parametros as p
from pyliferisk.mortalitytables import RP2000F, RP2000M

# Retorna a diferença entre duas datas
def delta(data_inicial, data_final):
    x = data_final - data_inicial
    return x.days

# Calcula a idade do participante titular
def idade(data_nascimento, data_base):
    return int(round(delta(data_nascimento, data_base) / 365.25))

# Calcula a idade de aposentadoriaa do participante titular, baseado na tábua de
# entrada em aposentadoria do Saúde CAIXA
def idade_aposentadoria(idade, sexo):
    if sexo == 'M':
        return int(round(tabuas_atuariais.APO2020M[idade - 18]))
    else:
        return int(round(tabuas_atuariais.APO2020F[idade - 18]))

# Calcula a idade do conjuge do participante titular, baseado na tábua de composi-
# ção familiar do Saúde CAIXA.
# A idade do conjuge é a soma da idade do titular mais a diferença de idade da 
# idade em que o titular é elegível à aposentadoria
def idade_conjuge(idade, idade_aposentadoria, sexo):
    if sexo == 'M':
        return int(round(idade + tabuas_atuariais.DIFIDADEM[idade_aposentadoria - 18]))
    else:
        return int(round(idade + tabuas_atuariais.DIFIDADEF[idade_aposentadoria - 18]))

def idade_conjuge_br(idade, sexo):
    if sexo == 'M':
        return int(round(idade + tabuas_atuariais.DIFIDADEM[idade - 18]))
    else:
        return int(round(idade + tabuas_atuariais.DIFIDADEF[idade - 18]))

# Idade do dependente temporário
def idade_dependente_temporario(idade, idade_aposentadoria, sexo):
    if sexo == 'M':
        return tabuas_atuariais.DEPTEMPM[idade_aposentadoria] - (idade_aposentadoria - idade)
    else:
        return tabuas_atuariais.DEPTEMPF[idade_aposentadoria] - (idade_aposentadoria - idade)

# Calcula o tempo de serviço do participante titular
def tempo_servico(data_admissao, data_base):
    return delta(data_admissao, data_base) / 365.25

# Crescimento da folha de salários
def crescimento_folha(taxa_crescimento_folha):
    return 1 * (1 + taxa_crescimento_folha)

# Verifica se o participante titular é elegível aos benefícios
def elegibilidade(idade, idade_aposentadoria):
    # TODO Implementar elegibilidade dos PDVEs
    return idade >= idade_aposentadoria

# Verifica se a idade atual do participante o torna elegível
def auxiliar_elegibilidade(idade, idade_aposentadoria):
    return idade == idade_aposentadoria

# Anuidade imediata vitalícia antecidapa mensal (proporcional ao mês)
def mensalizacao(idade, sexo):
    if sexo == 'M':
        mt = lr.Actuarial(nt = RP2000M, perc = p.perc_tabua, i = p.taxa_desconto)
    else:
        mt = lr.Actuarial(nt = RP2000F, perc = p.perc_tabua, i = p.taxa_desconto)

    return 1 - (11 / 24) / lr.annuity(mt, idade, 'w', 0)

# Fator de desconto
def vx(periodo, taxa_desconto):
    return 1 / pow(1 + taxa_desconto, periodo)

def qx(idade, sexo):
    if sexo == 'M':
        mt = lr.MortalityTable(nt = RP2000M, perc = p.perc_tabua)
    else:
        mt = lr.MortalityTable(nt = RP2000F, perc = p.perc_tabua)

    if idade < len(mt.qx):
        return mt.qx[idade] / 1000
    else:
        return 1.0

def wx(elegibilidade, idade, pdve):
    rot2020 = tabuas_atuariais.ROT2020
    if idade > len(rot2020) or pdve == 'S' or elegibilidade:
        return 0.0
    else:
        return rot2020[idade - 18]

def ix(elegibilidade, idade, pdve):
    if elegibilidade or pdve == 'S':
        return 0.0
    else:
        return tabuas_atuariais.LIGHTFRACA[idade]

def qxi(idade):
    return tabuas_atuariais.CSO58[idade]

def tpx(idade, p):
    
    if sexo == 'M':
        mt = lr.MortalityTable(nt = RP2000M, perc = 80)
    else:
        mt = lr.MortalityTable(nt = RP2000F, perc = 80)
    
    return lr.tpx(mt, idade, p)

def perc_casados(idade_aposentadoria, sexo):
    if sexo == 'M':
        return tabuas_atuariais.PERCCASADOSM[idade_aposentadoria - 18]
    else:
        return tabuas_atuariais.PERCCASADOSF[idade_aposentadoria - 18]



