import numpy as np
import pandas as pd
import scipy as sp
from pathlib import Path
from dss import DSS as dss_engine

def Shuntmatrix(DSSCircuit, Length: float, fases:np.array) -> np.array:
    Rs = DSSCircuit.Lines.Rmatrix * Length
    Xs = DSSCircuit.Lines.Xmatrix*1j * Length
    Ys_vetor = 1 / (Rs+Xs)
    Bsh_vetor = (DSSCircuit.Lines.Cmatrix * Length * (10**-9) * 2*np.pi * 60)*1j
    Ys_matriz = np.zeros((3, 3), dtype=complex)
    Bsh_matriz = np.zeros((3, 3), dtype=complex)
    i = 0
    for p in fases:
        for m in fases:
            Ys_matriz[p, m] = Ys_vetor[i]
            Bsh_matriz[p, m] = Bsh_vetor[i]
            i += 1
            
    Bsh_matriz = np.imag(Bsh_matriz)
    Gs_matriz = np.real(Ys_matriz)
    Bs_matriz = np.imag(Ys_matriz)
    
    return Gs_matriz, Bs_matriz, Bsh_matriz
        
def Derivadas_inj_pot_at(jacobiana: np.array, fases: np.array, medida_atual: int, index_barra: int, num_buses: int,
                         vet_estados: np.array, barras: pd.DataFrame, nodes: dict, medidas: np.array, Ybus) -> int:
    barra1 = barras['nome_barra'][index_barra]
    
    #Derivada da injeção de potência ativa com relação as tensões
    for fase in fases:
        no1 = nodes[barra1+f'.{fase+1}']
        tensao_estimada = vet_estados[(num_buses+index_barra)*3+fase]
        ang_estimado = vet_estados[(index_barra)*3+fase]
        for index_barra2 in range(len(barras['nome_barra'])):
            barra2 = barras['nome_barra'][index_barra2]
            for m in range(3):
                no2 = nodes[barra2+f'.{m+1}']
                Yij = Ybus[no1, no2]
                Gs = np.real(Yij)
                Bs = np.imag(Yij)
                if no1 == no2:
                    delta = ((tensao_estimada**2)*Gs+medidas[fase]) / tensao_estimada
                else:
                    ang_estimado2 = vet_estados[(index_barra2)*3+m]
                    delta = tensao_estimada*(Gs*np.cos(ang_estimado-ang_estimado2)+Bs*np.sin(ang_estimado-ang_estimado2))
                    
                jacobiana[medida_atual][(num_buses+index_barra2)*3+m - 3] = delta

        #Derivadas de injeção de potência ativa com relação aos ângulos
        for index_barra2 in range(len(barras['nome_barra'])):
            barra2 = barras['nome_barra'][index_barra2]
            for m in range(3):
                no2 = nodes[barra2+f'.{m+1}']
                Yij = Ybus[no1, no2]
                Gs = np.real(Yij)
                Bs = np.imag(Yij)
                if no1 == no2:
                    delta = -Bs*(tensao_estimada**2)
                    for i in range(len(barras['nome_barra'])):
                        barra3 = barras['nome_barra'][i]
                        for n in range(3):
                            no3 = nodes[barra3+f'.{n+1}']
                            Yij = Ybus[no1, no3]
                            if Yij != 0:
                                tensao_estimada2 = vet_estados[(num_buses+i)*3 + n]
                                ang_estimado2 = vet_estados[(i)*3 + n]
                                Gs = np.real(Yij)
                                Bs = np.imag(Yij)
                                delta -= tensao_estimada2*(Gs*np.sin(ang_estimado-ang_estimado2)-Bs*np.cos(ang_estimado-ang_estimado2))
                else:
                    tensao_estimada2 = vet_estados[(num_buses+index_barra2)*3+m]
                    ang_estimado2 = vet_estados[(index_barra2)*3+m]
                    delta = tensao_estimada*tensao_estimada2*(Gs*np.sin(ang_estimado-ang_estimado2)-Bs*np.cos(ang_estimado-ang_estimado2))
                    
                jacobiana[medida_atual][(index_barra2)*3+m - 3] = delta
                
        medida_atual += 1
        
    return medida_atual
        
def Derivadas_inj_pot_rat(jacobiana: np.array, fases: np.array, medida_atual: int, index_barra: int, num_buses: int,
                         vet_estados: np.array, barras: pd.DataFrame, nodes: dict, medidas: np.array, Ybus) -> int:
    barra1 = barras['nome_barra'][index_barra]
    
    #Derivada da injeção de potência reativa com relação as tensões
    for fase in fases:
        no1 = nodes[barra1+f'.{fase+1}']
        tensao_estimada = vet_estados[(num_buses+index_barra)*3+fase]
        ang_estimado = vet_estados[(index_barra)*3+fase]
        for index_barra2 in range(len(barras['nome_barra'])):
            barra2 = barras['nome_barra'][index_barra2]
            for m in range(3):
                no2 = nodes[barra2+f'.{m+1}']
                Yij = Ybus[no1, no2]
                Gs = np.real(Yij)
                Bs = np.imag(Yij)
                if no1 == no2:
                    delta = ((tensao_estimada**2)*(-Bs)+medidas[fase]) / tensao_estimada
                else:
                    ang_estimado2 = vet_estados[(index_barra2)*3+m]
                    delta = tensao_estimada*(Gs*np.sin(ang_estimado-ang_estimado2)-Bs*np.cos(ang_estimado-ang_estimado2))
                    
                jacobiana[medida_atual][(num_buses+index_barra2)*3+m - 3] = delta

        #Derivadas de injeção de potência reativa com relação aos ângulos
        for index_barra2 in range(len(barras['nome_barra'])):
            barra2 = barras['nome_barra'][index_barra2]
            for m in range(3):
                no2 = nodes[barra2+f'.{m+1}']
                Yij = Ybus[no1, no2]
                Gs = np.real(Yij)
                Bs = np.imag(Yij)
                if no1 == no2:
                    medidas_at = barras['Inj_pot_at'][index_barra2]
                    delta = -Gs*tensao_estimada**2+medidas_at[fase]

                else:
                    tensao_estimada2 = vet_estados[(num_buses+index_barra2)*3+m]
                    ang_estimado2 = vet_estados[(index_barra2)*3+m]
                    delta = tensao_estimada*tensao_estimada2*(Gs*np.sin(ang_estimado-ang_estimado2)-Bs*np.cos(ang_estimado-ang_estimado2))
                    
                jacobiana[medida_atual][(index_barra2)*3+m - 3] = delta
                
        medida_atual += 1
                
    return medida_atual

def Derivadas_tensao(jacobiana: np.array, fases: np.array, medida_atual: int, index_barra: int, num_buses: int) -> int:       
    for fase in fases:
        jacobiana[medida_atual][(num_buses*3) + (index_barra*3) + fase - 3] = 1
        medida_atual += 1
    
    return medida_atual

def Derivadas_fluxo_pot_at(jacobiana: np.array, fases: np.array, medida_atual: int, index_barra1: int, linha: int,
                           barras: pd.DataFrame, nodes: dict, vet_estados: np.array, DSSCircuit, Ybus) -> int:
    barra1 = barras['nome_barra'][index_barra1]
    num_buses = DSSCircuit.NumBuses
    DSSCircuit.SetActiveElement(linha)
    Gsmatrix, Bsmatrix, Bshmatrix = Shuntmatrix(DSSCircuit, DSSCircuit.Lines.Length, fases)
    barra2 = DSSCircuit.Lines.Bus2
    index_barra2 = barras[barras['nome_barra'] == barra2].index.values[0]
    
    for fase in fases:
        no1 = nodes[barra1+f'.{fase+1}']

        tensao_estimada = vet_estados[(num_buses*3) + (index_barra1*3) + fase]
        ang_estimado = vet_estados[(index_barra1*3) + fase]

        #Derivada do fluxo de Potência ativa com relação a tensão na barra inicial
        for m in fases:
            no2 = nodes[barra2+f'.{m+1}']
            Yij = Ybus[no1, no2]
            Gs = np.real(Yij)
            Bs = np.imag(Yij)
            Bsh = Bshmatrix[fase, m]
            
            if m == fase:
                delta = tensao_estimada*Gs
                for n in fases:
                    no2 = nodes[barra2+f'.{n+1}']
                    Yij = Ybus[no1, no2]
                    Gs = np.real(Yij)
                    Bs = np.imag(Yij)
                    Bsh = Bshmatrix[fase, n]
                    tensao_estimada2 = vet_estados[(num_buses*3) + (index_barra1*3) + n]
                    tensao_estimada3 = vet_estados[(num_buses*3) + (index_barra2*3) + n]
                    ang_estimado2 = vet_estados[(index_barra1*3) + n]
                    ang_estimado3 = vet_estados[(index_barra2*3) + n]
                    delta += tensao_estimada2*(Gs*np.cos(ang_estimado-ang_estimado2)+(Bs+Bsh)*np.sin(ang_estimado-ang_estimado2))
                    delta -= tensao_estimada3*(Gs*np.cos(ang_estimado-ang_estimado3)+Bs*np.sin(ang_estimado-ang_estimado3))

            else:
                ang_estimado2 = vet_estados[(index_barra1*3) + m]
                delta = tensao_estimada*(Gs*np.cos(ang_estimado-ang_estimado2) + (Bs+Bsh)*np.sin(ang_estimado-ang_estimado2))
                
            jacobiana[medida_atual][(num_buses+index_barra1)*3 + m - 3] = delta
            
        if index_barra1 != 0:
            #Derivada do fluxo de Potência ativa com relação ao ângulo na barra inicial
            for m in fases:
                no2 = nodes[barra2+f'.{m+1}']
                Yij = Ybus[no1, no2]
                Gs = np.real(Yij)
                Bs = np.imag(Yij)
                Bsh = Bshmatrix[fase, m]
                if m == fase:
                    delta = -(tensao_estimada**2)*(Bs+Bsh)
                    for n in fases:
                        no2 = nodes[barra2+f'.{n+1}']
                        Yij = Ybus[no1, no2]
                        Gs = np.real(Yij)
                        Bs = np.imag(Yij)
                        Bsh = Bshmatrix[fase, n]
                        tensao_estimada2 = vet_estados[(num_buses*3) + (index_barra1*3) + n]
                        tensao_estimada3 = vet_estados[(num_buses*3) + (index_barra2*3) + n]
                        ang_estimado2 = vet_estados[(index_barra1*3) + n]
                        ang_estimado3 = vet_estados[(index_barra2*3) + n]
                        delta -= tensao_estimada*tensao_estimada2*(Gs*np.sin(ang_estimado-ang_estimado2)-(Bs+Bsh)*np.cos(ang_estimado-ang_estimado2))
                        delta += tensao_estimada*tensao_estimada3*(Gs*np.sin(ang_estimado-ang_estimado3)-Bs*np.cos(ang_estimado-ang_estimado3))

                else:
                    tensao_estimada2 = vet_estados[(num_buses*3) + (index_barra1*3) + m]
                    ang_estimado2 = vet_estados[(index_barra1*3) + m]
                    delta = tensao_estimada*tensao_estimada2*(Gs*np.sin(ang_estimado-ang_estimado2) - (Bs+Bsh)*np.cos(ang_estimado-ang_estimado2))
                    
                jacobiana[medida_atual][(index_barra1*3) + m - 3] = delta
            
        #Derivada do fluxo de Potência ativa com relação a tensão na barra final
        for m in fases:
            no2 = nodes[barra2+f'.{m+1}']
            Yij = Ybus[no1, no2]
            Gs = np.real(Yij)
            Bs = np.imag(Yij)
            Bsh = Bshmatrix[fase, m]
            ang_estimado2 = vet_estados[(index_barra2*3) + m]
            delta = -tensao_estimada*(Gs*np.cos(ang_estimado-ang_estimado2) + Bs*np.sin(ang_estimado-ang_estimado2))
            jacobiana[medida_atual][num_buses*3 + (index_barra2*3) + m - 3] = delta
            
        if index_barra2 != 0:
            #Derivada do fluxo de Potência ativa com relação ao ângulo na barra final
            for m in fases:
                no2 = nodes[barra2+f'.{m+1}']
                Yij = Ybus[no1, no2]
                Gs = np.real(Yij)
                Bs = np.imag(Yij)
                Bsh = Bshmatrix[fase, m]
                tensao_estimada2 = vet_estados[(num_buses*3) + (index_barra2*3) + m]
                ang_estimado2 = vet_estados[(index_barra2*3) + m]
                delta = tensao_estimada*tensao_estimada2*(Gs*np.sin(ang_estimado-ang_estimado2) - Bs*np.cos(ang_estimado-ang_estimado2))
                jacobiana[medida_atual][(index_barra2*3) + m - 3] = delta
        
        medida_atual += 1
        
    return medida_atual
      
def Derivadas_fluxo_pot_rat(jacobiana: np.array, fases: np.array, medida_atual: int, index_barra1: int, linha: int,
                           barras: pd.DataFrame, nodes: dict, vet_estados: np.array, DSSCircuit, Ybus) -> int:
    barra1 = barras['nome_barra'][index_barra1]
    num_buses = DSSCircuit.NumBuses
    DSSCircuit.SetActiveElement(linha)
    Gsmatrix, Bsmatrix, Bshmatrix = Shuntmatrix(DSSCircuit, DSSCircuit.Lines.Length, fases)
    barra2 = DSSCircuit.Lines.Bus2
    index_barra2 = barras[barras['nome_barra'] == barra2].index.values[0]
    
    for fase in fases:  
        no1 = nodes[barra1+f'.{fase+1}']

        tensao_estimada = vet_estados[(num_buses*3) + (index_barra1*3) + fase]
        ang_estimado = vet_estados[(index_barra1*3) + fase]
        
        #Derivada do fluxo de Potência reativa com relação a tensão na barra inicial
        for m in fases:
            no2 = nodes[barra2+f'.{m+1}']
            Yij = Ybus[no1, no2]
            Gs = np.real(Yij)
            Bs = np.imag(Yij)
            Bsh = Bshmatrix[fase, m]
            if m == fase:
                delta = -tensao_estimada*(Bs+Bsh)
                for n in fases:
                    no2 = nodes[barra2+f'.{n+1}']
                    Yij = Ybus[no1, no2]
                    Gs = np.real(Yij)
                    Bs = np.imag(Yij)
                    Bsh = Bshmatrix[fase, n]
                    tensao_estimada2 = vet_estados[(num_buses*3) + (index_barra1*3) + n]
                    tensao_estimada3 = vet_estados[(num_buses*3) + (index_barra2*3) + n]
                    ang_estimado2 = vet_estados[(index_barra1*3) + n]
                    ang_estimado3 = vet_estados[(index_barra2*3) + n]
                    delta += tensao_estimada2*(Gs*np.sin(ang_estimado-ang_estimado2)-(Bs+Bsh)*np.cos(ang_estimado-ang_estimado2))
                    delta -= tensao_estimada3*(Gs*np.sin(ang_estimado-ang_estimado3)-Bs*np.cos(ang_estimado-ang_estimado3))

            else:
                ang_estimado2 = vet_estados[(index_barra1*3) + m]
                delta = tensao_estimada*(Gs*np.sin(ang_estimado-ang_estimado2)-(Bs+Bsh)*np.cos(ang_estimado-ang_estimado2))
                
            jacobiana[medida_atual][num_buses*3 + (index_barra1*3) + m - 3] = delta
            
        if index_barra1 != 0:
            #Derivada do fluxo de Potência reativa com relação ao ângulo na barra inicial
            for m in fases:
                no2 = nodes[barra2+f'.{m+1}']
                Yij = Ybus[no1, no2]
                Gs = np.real(Yij)
                Bs = np.imag(Yij)
                Bsh = Bshmatrix[fase, m]
                if m == fase:
                    delta = -(tensao_estimada**2)*Gs
                    for n in fases:
                        no2 = nodes[barra2+f'.{n+1}']
                        Yij = Ybus[no1, no2]
                        Gs = np.real(Yij)
                        Bs = np.imag(Yij)
                        Bsh = Bshmatrix[fase, n]
                        tensao_estimada2 = vet_estados[(num_buses*3) + (index_barra1*3) + n]
                        tensao_estimada3 = vet_estados[(num_buses*3) + (index_barra2*3) + n]
                        ang_estimado2 = vet_estados[(index_barra1*3) + n]
                        ang_estimado3 = vet_estados[(index_barra2*3) + n]
                        delta += tensao_estimada*tensao_estimada2*(Gs*np.cos(ang_estimado-ang_estimado2)+(Bs+Bsh)*np.sin(ang_estimado-ang_estimado2))
                        delta -= tensao_estimada*tensao_estimada3*(Gs*np.cos(ang_estimado-ang_estimado3)+Bs*np.sin(ang_estimado-ang_estimado3))
                    
                else:
                    tensao_estimada2 = vet_estados[(num_buses*3) + (index_barra1*3) + m]
                    ang_estimado2 = vet_estados[(index_barra1*3) + m]
                    delta = -tensao_estimada*tensao_estimada2*(Gs*np.cos(ang_estimado-ang_estimado2) + (Bs+Bsh)*np.sin(ang_estimado-ang_estimado2))
                
                jacobiana[medida_atual][(index_barra1*3) + m - 3] = delta
            
        #Derivada do fluxo de Potência reativa com relação a tensão na barra final
        for m in fases:
            no2 = nodes[barra2+f'.{m+1}']
            Yij = Ybus[no1, no2]
            Gs = np.real(Yij)
            Bs = np.imag(Yij)
            Bsh = Bshmatrix[fase, m]
            ang_estimado2 = vet_estados[(index_barra2*3) + m]
            delta = -tensao_estimada*(Gs*np.sin(ang_estimado-ang_estimado2)-Bs*np.cos(ang_estimado-ang_estimado2))
            jacobiana[medida_atual][num_buses*3 + (index_barra2*3) + m - 3] = delta
            
        if index_barra2 != 0:
            #Derivada do fluxo de Potência reativa com relação ao ângulo na barra final
            for m in fases:
                no2 = nodes[barra2+f'.{m+1}']
                Gs = Gsmatrix[fase, m]
                Bs = Bsmatrix[fase, m]
                Bsh = Bshmatrix[fase, m]
                tensao_estimada2 = vet_estados[(num_buses*3) + (index_barra2*3) + m]
                ang_estimado2 = vet_estados[(index_barra2*3) + m]
                delta = tensao_estimada*tensao_estimada2*(Gs*np.cos(ang_estimado-ang_estimado2) + Bs*np.sin(ang_estimado-ang_estimado2))
                jacobiana[medida_atual][(index_barra2*3) + m - 3] = delta
            
        medida_atual += 1
    
    return medida_atual
