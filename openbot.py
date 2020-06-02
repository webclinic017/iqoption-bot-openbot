'''
* Copyright (c) 2020 Jaime Linhares

* Este programa é um software livre; você pode redistribuí-lo e/ou
modificá-lo sob os termos da Licença Pública Geral GNU como publicada
pela Free Software Foundation; na versão 3 da Licença, ou
(a seu critério) qualquer versão posterior.

* Este programa é distribuído na esperança de que possa ser útil,
mas SEM NENHUMA GARANTIA; sem uma garantia implícita de ADEQUAÇÃO
a qualquer MERCADO ou APLICAÇÃO EM PARTICULAR. Veja a
Licença Pública Geral GNU para mais detalhes.

* Você deve ter recebido uma cópia da Licença Pública Geral GNU junto
com este programa. Se não, veja <http://www.gnu.org/licenses/>.

# Função: Realizar Copytrade Digital e Binária conforme Ranking e Valor de Entradas.
# Autor: Jaime Linhares
# Data: 15/05/2020
# Instagram: @jaimelinharesjr / Linkedin: https://www.linkedin.com/in/jaimelinharesjr/
'''

from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.constants import ACTIVES
from threading import Thread
from datetime import *
from dateutil import tz
import userdata
import time, json
import colorful as cf

#### Parâmetros Trade IQ Option ####
par = "EURUSD" # Paridade Padrão
entrada = 10
timeframe = 1
####################################

#### Parâmetros Filtro Ranking #####
pais = "Worldwide"
jogadores = 1000 # Número de Jogadores a se Coletar
####################################

#### Parâmetros Busca Entradas #####
tipoD = 'live-deal-digital-option' # Digital
tipoB = 'live-deal-binary-option-placed' # Binária
valormin = 20 # Define o valor mínimo da entrada a se copiar
####################################
#### Parâmetro Gerais IQ Option ####
user = userdata.LoginData
API = IQ_Option(user["username"], user["password"])
API.connect()

API.change_balance("PRACTICE") # PRACTICE / REAL

while True:
	if API.check_connect() == False:
		print("Erro ao se conectar")
		API.connect()
	else:
		print("Conectado com sucesso")
		break
		
	time.sleep(1)
####################################

######## Variáveis Globais ########
filtro = []
lastplayer = 0
####################################

######### SIGLAS FUNÇÕES ###########
# res = resultado
# pa = par
# ti = tipo (turbo, digital)
# tf = timeframe 
# tv = tipo vela (M1(60), M5(300), M15(900))
# tp = período (total de velas 1 a 1000)
# co = país 
# jo = total de jogadores
# st = stake / entrada
# py = payout
# dr = direção
# lo = loss / perda
# lu = lucro
# seg = segundos
# ta = trades ativa
####################################

###### Função Busca Payout % #######
def payout(pa, ti, tf = 1):
	if ti == 'turbo':
		a = API.get_all_profit()
		return (int(a[par]["turbo"] * 100) / 100)
		
	elif ti == 'digital':
		API.subscribe_strike_list(pa, tf)
		while True:
			d = API.get_digital_current_profit(pa, tf)
			if d != False:
				d = int(d)
				break
			time.sleep(1)
		API.unsubscribe_strike_list(pa, tf)
		return d
####################################

##### Função Filtra o Ranking ######
def filtroRanking(co, jo):
	filtro.clear()
	while True:		
		try:
			ranking = API.get_leader_board(co, 1, jo, 0)

			for n in ranking['result']['positional']:
				id = ranking['result']['positional'][n]['user_id']
				filtro.append(id)
				
		except:
			pass
		time.sleep(180) #Atualiza Ranking a cada 3 minutos.
####################################

#### Função Converte Timestamp2 #####
def converterTimestamp(x, y, z):
	timestamp1, ms1 = divmod(x, 1000)
	timestamp2, ms2 = divmod(y, 1000)
	timestamp3, ms3 = divmod(z, 1000)

	entradacodt = datetime.fromtimestamp(timestamp1) + timedelta(milliseconds=ms1)
	expiracaodt = datetime.fromtimestamp(timestamp2) + timedelta(milliseconds=ms2)
	horaatualdt = datetime.fromtimestamp(timestamp3) + timedelta(milliseconds=ms3)

	entradaco = entradacodt.strftime('%H:%M:%S %d/%m/%Y')
	expiracao = expiracaodt.strftime('%H:%M:%S %d/%m/%Y')
	horaatual = horaatualdt.strftime('%H:%M:%S %d/%m/%Y')


	mintime1 = timedelta(milliseconds=x)
	mintime2 = timedelta(milliseconds=y)	
	mintime3 = timedelta(milliseconds=z)
	min1 = mintime1.seconds
	min2 = mintime2.seconds	
	min3 = mintime3.seconds	

	exptime = min2 - min1
	delaytime = min3 - min1                         
	expminutes = (exptime % 3600) // 60   
	if expminutes == 0:
		expminutes = 1                       


	return [entradaco, expiracao, horaatual, expminutes, delaytime]
####################################

######## Função Buy Normal #########
def normalIQ(pa, st, dr, tf, py, tp):

	print("ENTRADA: $ "+str(round(st, 2))+" | Direção: "+(cf.bold_white_on_green("CALL") if dr == 'call' else cf.bold_white_on_red("PUT")))
	print("\n")	

	if tp == "digital":

		status,id = API.buy_digital_spot(pa, st, dr, tf)

		if status:
			while True:
				status,lc = API.check_win_digital_v2(id)
				
				if status:
					r = lc
					break
		else:
			r = 0						

		return r

	elif tp == "binaria":

		status,id = API.buy(st, pa, dr, tf)

		if status:
			r = API.check_win_v3(id)
		else:
			r = 0

		return r
####################################

### Função de Análise da Entrada ###
def ajustesEntradaDigital(ti):

	global lastplayer

	trades = API.get_live_deal(ti)
	print("Analisando "+str(len(trades))+" jogadas!")

	for trade in list(trades):

		entradacopy = trade['created_at']	
		expiracao = trade['instrument_expiration']	 
		horalocal = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

		timecopy = converterTimestamp(entradacopy, expiracao, horalocal)		

		if trade['instrument_dir'] == "call" and lastplayer != trade['user_id'] and trade['amount_enrolled'] >= float(valormin) and int(timecopy[3]) < 20 and int(timecopy[4]) < 5:
			if trade['user_id'] in filtro:
				lastplayer = trade['user_id']
				tradecall = 1 
				tradetipo = "digital"

				ativo = list(ACTIVES.keys())[list(ACTIVES.values()).index(trade['instrument_active_id'])]
				direcao = 'call'
				tmf = (1 if trade['expiration_type'] == 'PT1M' else (5 if trade['expiration_type'] == 'PT5M' else (15 if trade['expiration_type'] == 'PT15M' else "1")))
				minutos = (60 if trade['expiration_type'] == 'PT1M' else (300 if trade['expiration_type'] == 'PT5M' else (900 if trade['expiration_type'] == 'PT15M' else "1")))
				
				pay = float(payout(ativo, 'digital', tmf) / 100)

				lastplay = trade['instrument_dir'] 
				print("País: "+str(trade['flag'])+" | Valor Apostado: $ "+str(trade['amount_enrolled'])+" | Direção: "+(cf.bold_white_on_green("CALL") if str(trade['instrument_dir']) == 'call' else cf.bold_white_on_red("ERRO"))+" | Nome: "+str(trade['name'])+" | Expiração: "+str(tmf)+"M | Paridade: "+str(ativo))
				print("Hora da Entrada Original: "+str(timecopy[0])+" | Hora Local: "+str(timecopy[2])+" | Delay da Jogada: "+str(timecopy[4])+" seg")						
			
				dcall = Thread(target=normalIQ, args=(str(ativo), int(entrada), str(direcao), int(tmf), float(pay), str(tradetipo)))
				dcall.daemon = True
				dcall.start()

		elif trade['instrument_dir'] == "put" and lastplayer != trade['user_id'] and trade['amount_enrolled'] >= float(valormin) and int(timecopy[3]) < 20 and int(timecopy[4]) < 5:
			if trade['user_id'] in filtro:
				lastplayer = trade['user_id']
				tradeput = 2
				tradetipo = "digital"

				ativo = list(ACTIVES.keys())[list(ACTIVES.values()).index(trade['instrument_active_id'])]
				direcao = 'put'
				tmf = (1 if trade['expiration_type'] == 'PT1M' else (5 if trade['expiration_type'] == 'PT5M' else (15 if trade['expiration_type'] == 'PT15M' else "1")))
				minutos = (60 if trade['expiration_type'] == 'PT1M' else (300 if trade['expiration_type'] == 'PT5M' else (900 if trade['expiration_type'] == 'PT15M' else "1")))

				pay = float(payout(ativo, 'digital', tmf) / 100)

				lastpar = ativo
				lastplay = trade['instrument_dir'] 
				print("País: "+str(trade['flag'])+" | Valor Apostado: $ "+str(trade['amount_enrolled'])+" | Direção: "+(cf.bold_white_on_red("PUT") if str(trade['instrument_dir']) == 'put' else cf.bold_white_on_red("ERRO"))+" | Nome: "+str(trade['name'])+" | Expiração: "+str(tmf)+"M | Paridade: "+str(ativo))
				print("Hora da Entrada Original: "+str(timecopy[0])+" | Hora Local: "+str(timecopy[2])+" | Delay da Jogada: "+str(timecopy[4])+" seg")						

				dput = Thread(target=normalIQ, args=(str(ativo), int(entrada), str(direcao), int(tmf), float(pay), str(tradetipo)))
				dput.daemon = True
				dput.start()

		trades.clear()	
	print("RODADA DIGITAL FINALIZADA!")	
####################################

### Função de Análise da Entrada ###
def ajustesEntradaBinaria(ti):

	global lastplayer

	trades = API.get_live_deal(ti)
	print("Analisando "+str(len(trades))+" jogadas!")

	for trade in list(trades):

		entradacopy = trade['created_at']	
		expiracao = trade['expiration']
		horalocal = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

		timecopy = converterTimestamp(entradacopy, expiracao, horalocal)

		if trade['direction'] == "call" and lastplayer != trade['user_id'] and trade['amount_enrolled'] >= float(valormin) and int(timecopy[3]) < 20 and int(timecopy[4]) < 3:
			if trade['user_id'] in filtro:
				lastplayer = trade['user_id']
				tradecall = 1 
				tradetipo = "binaria"

				ativo = list(ACTIVES.keys())[list(ACTIVES.values()).index(trade['active_id'])]
				direcao = 'call'

				pay = round(payout(ativo, 'turbo', 1), 2)

				lastplay = trade['direction'] 
				print("País: "+str(trade['flag'])+" | Valor Apostado: $ "+str(trade['amount_enrolled'])+" | Direção: "+(cf.bold_white_on_green("CALL") if str(trade['direction']) == 'call' else cf.bold_white_on_red("ERRO"))+" | Nome: "+str(trade['name'])+" | Expiração: "+str(timecopy[3])+"M | Paridade: "+str(ativo))
				print("Hora da Entrada Original: "+str(timecopy[0])+" | Hora Local: "+str(timecopy[2])+" | Delay da Jogada: "+str(timecopy[4])+" seg")
			
				bcall = Thread(target=normalIQ, args=(str(ativo), int(entrada), str(direcao), int(timecopy[3]), float(pay), str(tradetipo)))
				bcall.daemon = True
				bcall.start()

		
		elif trade['direction'] == "put" and lastplayer != trade['user_id'] and trade['amount_enrolled'] >= float(valormin) and int(timecopy[3]) < 20 and int(timecopy[4]) < 3:
			if trade['user_id'] in filtro:
				lastplayer = trade['user_id']
				tradeput = 2 
				tradetipo = "binaria"

				ativo = list(ACTIVES.keys())[list(ACTIVES.values()).index(trade['active_id'])]
				direcao = 'put'

				pay = round(payout(ativo, 'turbo', 1), 2)

				lastplay = trade['direction'] 
				print("País: "+str(trade['flag'])+" | Valor Apostado: $ "+str(trade['amount_enrolled'])+" | Direção: "+(cf.bold_white_on_red("PUT") if str(trade['direction']) == 'put' else cf.bold_white_on_red("ERRO"))+" | Nome: "+str(trade['name'])+" | Expiração: "+str(timecopy[3])+"M | Paridade: "+str(ativo))
				print("Hora da Entrada Original: "+str(timecopy[0])+" | Hora Local: "+str(timecopy[2])+" | Delay da Jogada: "+str(timecopy[4])+" seg")			

				bput = Thread(target=normalIQ, args=(str(ativo), int(entrada), str(direcao), int(timecopy[3]), float(pay), str(tradetipo)))
				bput.daemon = True
				bput.start()

		trades.clear()
	print("RODADA BINÁRIA FINALIZADA!")				
####################################


####### Main Boot IQ Option #######
API.subscribe_live_deal(tipoB, 10)
API.subscribe_live_deal(tipoD, 10)

print("Aguarde, catalogando Ranking ("+str(jogadores)+") jogadores.")
catalogo = Thread(target=filtroRanking, args=(pais, jogadores))
catalogo.daemon = True
catalogo.start()
time.sleep(10)

while True:

	time.sleep(3)
	print("#################################### BUSCANDO COPYTRADE DIGITAL ###############################################")
	ajustesEntradaDigital(tipoD)
	print("###############################################################################################################")
	print("\n")

	time.sleep(3)
	print("#################################### BUSCANDO COPYTRADE BINÁRIA ###############################################")	
	ajustesEntradaBinaria(tipoB)	
	print("###############################################################################################################")	
	print("\n")

API.unscribe_live_deal(tipoD)
API.unscribe_live_deal(tipoB)
####################################