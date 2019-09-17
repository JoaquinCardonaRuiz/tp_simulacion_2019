import numpy as np 
import matplotlib.pyplot as plt
big_number = 9999999

class Cliente():
    def __init__(self,t_entrada,prioridad):
        self.demora = 0
        self.t_entrada = t_entrada
        self.prioridad = prioridad

    def salida_sistema(self,reloj):
        self.demora = reloj - self.t_entrada

    def __str__(self):
        if self.prioridad:
            return("Cliente prioritario")
        else:
            return("Cliente")


class Servidor():
    def __init__(self,tms):
        self.tms = tms
        self.cliente = False
        self.tiempo_servicio_acumulado = 0
        self.tiempo_entrada_actual = False

    def ingreso_servidor(self,cliente,reloj):
        self.cliente = cliente
        self.tiempo_entrada_actual = reloj

    def salida_servidor(self,reloj):
        self.cliente = False
        self.tiempo_servicio_acumulado += (reloj - self.tiempo_entrada_actual)


class Cola():
    def __init__(self,clientes,alg):
        self.clientes = clientes
        self.cantidad_clientes = 0
        self.algoritmo = alg
        self.q_t = 0
    
    def calcular_q_t(self,reloj,tue):
        self.q_t += len(self.clientes) * (reloj - tue)

    def ingreso_cola(self,cliente):
        self.clientes.append(cliente)

    def salida_cola(self):
        self.cantidad_clientes += 1

        if self.algoritmo == "FIFO":
            return self.clientes.pop()

        elif self.algoritmo == "LIFO":
            return self.clientes.pop(0)


class Cola_Inicial(Cola):
    def __init__(self,clientes,tma,alg):
        Cola.__init__(self,clientes,alg)
        self.tma = tma


class Linea():
    def __init__(self,colas_entrada,servidores):
        self.colas_entrada = colas_entrada
        self.servidores = servidores



class Simulacion():
    def __init__(self,alg_colas,prioridades):
        """
        Establece la topologia de la simulacion
        Inicializa la simulacion en t = 0
        Establece la lista de eventos y sus tiempos iniciales 
        """
        self.reloj = 0
        #creamos una lista de nombres para llamar al evento correspondiente de lista_eventos
        self.nombres_eventos = ["Arribo", "Partida11", "Partida12", "Partida13", "Partida21", "Partida22", "Partida23"]
        self.clientes = []
        self.tiempo_ultimo_evento = 0
        self.prioridades = prioridades

        #creamos la topologia de la simulacion, estableciendo las lineas, servidores, y colas
        l1 = Linea(Cola_Inicial([],0.8,alg_colas), [Servidor(0.5),Servidor(0.5),Servidor(0.5)])
        l2 = Linea([Cola([],alg_colas),Cola([],alg_colas),Cola([],alg_colas)], [Servidor(0.2),Servidor(0.4),Servidor(0.6)])
        self.lineas = [l1,l2]

        #Creamos la lista de eventos, estableciendo todas las partidas en big_number para evitar partidas de servidores desocupados
        self.lista_eventos = []
        self.lista_eventos.append(np.random.exponential(self.lineas[0].colas_entrada.tma))
        for _ in self.nombres_eventos[1:]:
            self.lista_eventos.append(big_number)

        #Estadisticos
        self.promedio_demora_clientes = []
        self.utilizacion_servidores = []
        self.promedio_clientes_cola = []


    def programa_principal(self):
        """
        Llama a las subrutinas de la simulacion
        E itera hasta que se cumplen las condiciones de finalizacion
        """
        v=False
        while(self.reloj<500):
            if v:print(self.lista_eventos)
            nro_evento = self.tiempos()
            self.eventos(nro_evento)
            if v: self.diagnostico(nro_evento)
            self.estadisticos()
        self.reportes()
        
        return [self.promedio_demora_clientes,
                self.utilizacion_servidores,
                self.promedio_clientes_cola]


    def tiempos(self):
        """
        Avanza el reloj hasta el siguiente evento y devuelve el evento correspondiente
        """

        #Obtenemos el nro de evento del evento que tiene menor tiempo proximo
        nro_evento = self.lista_eventos.index(min(self.lista_eventos))
        #Guardamos el tiempo acutal como tiempo del ultimo evento
        self.tiempo_ultimo_evento = self.reloj
        #Actualizamos el reloj al tiempo del proximo evento
        self.reloj = self.lista_eventos[nro_evento]
        return nro_evento


    def eventos(self,nro_evento):
        """
        Se llama con el argumento del evento correspondiente
        Actualiza el estado del sistema de acuerdo al evento
        Al ocurrir un evento, actualiza lista_eventos
        """

        def arribo():
            #Calculamos el tiempo del siguiente arribo
            self.lista_eventos[nro_evento] = self.reloj + np.random.exponential(self.lineas[0].colas_entrada.tma)

            #Creamos el cliente y decidimos el servidor de la primera linea al que va a ir
            cli = Cliente(self.reloj, (np.random.random() < self.prioridades))
            nro_servidor = self.asignar_servidor()

            #Si hay un servidor vacio:
            if nro_servidor:
                nro_servidor -= 1 #Le restamos uno al nro_servidor para poder usarlo como indice de un arreglo, que comienza en 0

                #Generamos el tiempo de la proxima partida de ese servidor
                self.lista_eventos[nro_servidor+1] = self.reloj + np.random.exponential(self.lineas[0].servidores[nro_servidor].tms)
                #Y realizamos el ingreso al servidor
                self.lineas[0].servidores[nro_servidor].ingreso_servidor(cli,self.reloj)
                
            else:
                #Si no hay un servidor vacio, realizamos el ingreso a la cola
                self.lineas[0].colas_entrada.ingreso_cola(cli)



        def partidas(s):
            #Obtenemos el nro de linea y de servidor del nombre del evento
            n_linea, n_servidor = int(s[-2])-1 ,int(s[-1])-1

            #Calculamos el tiempo de la proxima partida de ese servidor
            self.lista_eventos[nro_evento] = self.reloj + np.random.exponential(self.lineas[n_linea].servidores[n_servidor].tms)
            
            #Si la partida es de un servidor de la primera linea:
            if n_linea == 0:

                #Guardamos el servidor y el cliente que este contiene para facilitar el acceso
                srv = self.lineas[0].servidores[n_servidor]
                cli = srv.cliente

                #Si el servidor en la misma fila(horizontal) de la siguiente linea(vertical) esta ocupado:
                if self.lineas[1].servidores[n_servidor].cliente:
                        #Realizamos el ingreso del cliente a la cola
                    self.lineas[1].colas_entrada[n_servidor].ingreso_cola(cli)

                #Sino:
                else:
                    #Generamos el tiempo de partida del servidor de la siguiente linea en el que el cliente va a ingresar
                    self.lista_eventos[n_servidor+4] = self.reloj + np.random.exponential(self.lineas[n_linea].servidores[n_servidor].tms)
                    #Realizamos el ingreso del cliente al servidor de la siguiente linea
                    self.lineas[1].servidores[n_servidor].ingreso_servidor(cli,self.reloj)

                #Finalmente, realizamos la salida del servidor de la primera linea
                self.lineas[0].servidores[n_servidor].salida_servidor(self.reloj)

                #Ahora, tenemos que realizar el ingreso de un cliente en la cola anterior al servidor de primera linea que acaba de quedar vacio

                #Si la cola de entraada esta vacia
                if self.lineas[0].colas_entrada.clientes == []:
                    #El servidor permanece vacio, y seteamos el tiempo de su proxima partida en infinito
                    self.lista_eventos[n_servidor+1] = big_number

                #Si hay alguien en cola:
                else:
                    #Realizamos su ingreso al servidor
                    self.lineas[0].servidores[n_servidor].ingreso_servidor(self.lineas[0].colas_entrada.salida_cola(), self.reloj)


            #Si la partida es de un servidor de segunda linea:
            elif n_linea == 1:
                #Hacemos tres cosas:
                self.clientes.append(self.lineas[1].servidores[n_servidor].cliente)         #1- Agregamos el cliente a la lista de clientes que completaron su demora
                self.lineas[1].servidores[n_servidor].cliente.salida_sistema(self.reloj)    #2- Llamamos un metodo en Cliente que lo saca del sistema (calcula su demora)
                self.lineas[1].servidores[n_servidor].salida_servidor(self.reloj)           #3- Realizamos la salida del servidor de segunda linea

                #Al igual que en el caso anterior, el servidor queda vacio, y debemos ingresar al siguiente cliente en cola, si es que lo hay
                if self.lineas[1].colas_entrada[n_servidor].clientes == []:
                    self.lista_eventos[n_servidor+4] = big_number
                else:
                    self.lineas[1].servidores[n_servidor].ingreso_servidor(self.lineas[1].colas_entrada[n_servidor].salida_cola(),self.reloj)

        
        def actualizar_q_t():
            """
            Cada vez que ocurre un evento, se llama a esta funcion para calcular q(t), es decir
            pedirle a cada una de las colas que le sume a su q(t) la cantidad de clientes que tiene multiplicado por el tiempo desde el evento anterior
            """
            self.lineas[0].colas_entrada.calcular_q_t(self.reloj,self.tiempo_ultimo_evento)
            for cola in self.lineas[1].colas_entrada:
                cola.calcular_q_t(self.reloj,self.tiempo_ultimo_evento)

        actualizar_q_t()
        evento = self.nombres_eventos[nro_evento]   
        if evento == "Arribo":
            arribo()
        else:
            partidas(evento)
            
            
    def asignar_servidor(self):
        """
        Establece una lista de prioridades para comprobar la disponibilidad de los servidores
        de la primer linea y asigna el servidor correspondiente
        """
        #Si todos los servidores estan ocupados, devuelve False
        #Sino, devuelve nro de servidor
        servidores = [1,2,3]
        np.random.shuffle(servidores)
        for nro_servidor in servidores:
            if not self.lineas[0].servidores[nro_servidor-1].cliente:
                return nro_servidor
        return False


    def estadisticos(self):
        us = []
        for l in self.lineas:
            for s in l.servidores:
                us.append(round(s.tiempo_servicio_acumulado/self.reloj,5))
        self.utilizacion_servidores.append(us)

        d = []
        for cli in self.clientes:
            d.append(cli.demora)
        self.promedio_demora_clientes.append(round(np.average(d),5))
        self.promedio_clientes_cola.append([round(self.lineas[0].colas_entrada.q_t / self.reloj,5)]+[(round(c.q_t/self.reloj,5)) for c in self.lineas[1].colas_entrada])




    def reportes(self):
        """
        Genera los reportes estadisticos al finalizar la simulacion
        """
        print()
        #Utilizacion de servidores:
        utilizacion_servidores = []
        #Para cada servidor de cada linea
        for l in self.lineas:
            for s in l.servidores:
                #Calculamos la utilizacion como el tiempo acumulado en el que el servidor trabajo dividido el tiempo final
                utilizacion_servidores.append(round(s.tiempo_servicio_acumulado/self.reloj,5))


        #Demora de clientes
        demora_clientes = []
        #Para cada cliente que cumplio su demora, obtenemos la demora
        for cli in self.clientes:
            demora_clientes.append(cli.demora)
        #Obtenemos el promedio de esas demoras
        promedio_demora_clientes = round(np.average(demora_clientes),5)


        #Cantidad promedio de clientes en cola:
        #Calculamos la cant promedio de c en cola de entrada:
        promedio_clientes_cola_l1 = round(self.lineas[0].colas_entrada.q_t / self.reloj,5)
        #Y para las tres colas de la siguiente linea
        promedio_clientes_cola_l2 = [(round(c.q_t/self.reloj,5)) for c in self.lineas[1].colas_entrada]

        clientes_prioritarios = 0
        for c in self.clientes:
            if c.prioridad:
                clientes_prioritarios+=1
        clientes_prioritarios=round(clientes_prioritarios/len(self.clientes),5)


        print("Demora promedio de clientes: ",promedio_demora_clientes)
        print("Prom clientes en cola de entrada: ",promedio_clientes_cola_l1)
        print("Prom clientes en cola l2: ",promedio_clientes_cola_l2)
        print("Utlizacion de los servidores: ",utilizacion_servidores)
        print("Proporcion de clientes prioritarios: ",clientes_prioritarios)


    def diagnostico(self,nro_evento):
        """
        En cada iteracion imprime el estado del sistema
        """
        print("Evento: ",self.nombres_eventos[nro_evento],"\n")
        print("="*60)
        print()
        print("Reloj: ",self.reloj)
        print("Cola entrada: ", len(self.lineas[0].colas_entrada.clientes))
        print("Servidor 0,0: ", self.lineas[0].servidores[0].cliente)
        print("Servidor 0,1: ", self.lineas[0].servidores[1].cliente)
        print("Servidor 0,2: ", self.lineas[0].servidores[2].cliente)
        print("Cola 0: ", len(self.lineas[1].colas_entrada[0].clientes))
        print("Cola 1: ", len(self.lineas[1].colas_entrada[1].clientes))
        print("Cola 2: ", len(self.lineas[1].colas_entrada[2].clientes))
        print("Servidor 1,0: ", self.lineas[1].servidores[0].cliente)
        print("Servidor 1,1: ", self.lineas[1].servidores[1].cliente)
        print("Servidor 1,2: ", self.lineas[1].servidores[2].cliente)
        print()
        print("="*60)
        print()


def corridas(alg_colas="FIFO",prioridades=0):
    #TODO: agregar el tiempo del evento para plotear xticks
    #Demora clientes
    r = []
    for i in range(3):
        sim = Simulacion(alg_colas,prioridades)
        r.append(sim.programa_principal())
    colors = ["#602159","#4a8189","#4bf4ae"]
    for corrida in r:
        plt.plot(corrida[0],color = colors.pop(0),linewidth=1.75)
    plt.title("Demora promedio de clientes")
    plt.xticks(list(range(len(corrida[0])))[::100],[int(i*(500/len(corrida[0]))) for i in list(range(len(corrida[0])))[::100]])
    plt.xlabel("Reloj")
    plt.ylabel("Horas")
    plt.show()

    #Utilizacion Servidores
    for servidor in [0,1,2,3,4,5]:
        colors = ["#602159","#4a8189","#4bf4ae"]
        for corrida in r:
            plt.plot([i[servidor] for i in corrida[1]],color = colors.pop(0))
        plt.title("Utilizacion del servidor "+str(servidor))
        plt.show()

    #Promedio clientes en cola:
    for cola in [0,1,2,3]:
        colors = ["#602159","#4a8189","#4bf4ae"]
        for corrida in r:
            plt.plot([i[cola] for i in corrida[2]],color = colors.pop(0))
        plt.title("Promedio de clientes en cola "+str(cola))
        plt.show()


corridas()
#sim = Simulacion(alg_colas = "FIFO", prioridades = 0.03)
#sim.programa_principal()
