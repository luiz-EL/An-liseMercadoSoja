
class data_get():
    def __init__(self, begin: int, end:int):
        self.begin = begin
        self.end = end

    def soy(self):
        import sidrapy
        import pandas as pd
        # Importanto tabela com os municípios do Mato Grosso
        municípios = pd.read_csv('tabelas/municipios_mt.csv')
        municípios_cd = ','.join(str(cd) for cd in municípios['cd'])

        # Importando dados da colheita municipal do MT
        soja = sidrapy.get_table(
            table_code = '5457',
            territorial_level = '6',
            ibge_territorial_code = municípios_cd,
            period = f'{self.begin}-{self.end}',
            classification = '782/40124',
            variable = '214,215,8331,1008331'
        )[['D2N', 'D1N', 'D3N', 'MN', 'V']]

        # Formatando DataFrame
        soja.columns = soja.iloc[0] # Renomeando Colunas 
        soja.drop(0, inplace=True)

        soja['Variável'] = [f'{var} ({medida})' for medida, var in zip(soja['Unidade de Medida'], soja['Variável'])] # Concatenando Variável e Unidade de Medida
        soja.drop(axis = 1, columns = ['Unidade de Medida'], inplace = True)

        soja['Valor'] = soja['Valor'].replace('-', 0) # Mudando valores '..' para 0
        soja['Valor'] = [float(val) for val in soja['Valor']]

        soja_pivoted = pd.pivot_table(soja, values = 'Valor', index = ['Ano', 'Município'], columns = 'Variável')
        soja_pivoted.to_csv(f'tabelas/prod_soja_mt_{self.begin}_{self.end}.csv')
    
    def costs(self, cidades_mt: list):
        import wget
        import pandas as pd
        import os

        dirs = os.listdir()
        archive = 'Soja_Serie_Historica_1997-2022.xls'
        url = 'https://www.conab.gov.br/info-agro/custos-de-producao/planilhas-de-custo-de-producao/item/download/42998_ccb0d1f5aa84efd0c88c80383f54844b'

        if archive not in dirs: wget.download(url)
        else: pass 

        for cidade in [f'{city[0:len(city)-5]}-MT' for city in cidades_mt]:
            try:
                custo_anual = pd.DataFrame(columns = ['Despesa', 'Valor por Hectare', 'Ano'])
                for year in range(self.begin, self.end + 1):
                    if year == range(self.begin, self.end + 1)[1]:
                        # Importando planilha
                        custos_ano_base = pd.read_excel(archive, sheet_name = f'OGM-{cidade}-{year}', skiprows = 8, header = None)

                        # Limpando dados
                        custos_ano_base = custos_ano_base[[1,7]].fillna(0)
                        custos_ano_base.drop(index = custos_ano_base.index[[-2,-1]], inplace = True)

                        # Formatando dataframe
                        custos_ano_base.columns = ['Despesa', 'Valor por Hectare']
                        custos_ano_base['Ano'] = [year]*len(custos_ano_base.index)

                        # Concatenação
                        custo_anual = pd.concat([custo_anual, custos_ano_base])
                    else:
                        if year < 2021:
                            # Importando planilha
                            custos = pd.read_excel(archive, sheet_name = f'OGM-{cidade}-{year}', skiprows = 8, header = None)

                            # Limpando dados
                            custos = custos[[1,7]].fillna(0)
                            custos.drop(index = custos.index[[-2, -1]], inplace=True)

                            # Formatando dataframe
                            custos.columns = ['Despesa', 'Valor por Hectare']
                            custos['Ano'] = [year]*len(custos.index)

                            # Concatenação
                            custo_anual = pd.concat([custo_anual, custos])

                        if year >= 2021:
                            # Importando planilha
                            custos = pd.read_excel(archive, sheet_name = f'OGM-{cidade}-{year}', skiprows = 7, header = None)

                            # Limpando os dados
                            custos = custos[[0,1]].fillna(0)
                            custos.drop(index = custos.index[[-2, -1]], inplace=True)

                            # Formatando dataframe
                            custos.columns = ['Despesa', 'Valor por Hectare']
                            custos['Ano'] = [year]*len(custos.index)
                            
                            # Concatenando
                            custo_anual = pd.concat([custo_anual, custos])
                # Formatando coluna Despesa
                desp_clean = []

                for desp in custo_anual['Despesa']:
                    if '\t' in desp:
                        desp_clean.append(desp.replace('\t', '').strip())
                    else: desp_clean.append(desp)
                custo_anual['Despesa'] = desp_clean

                for desp in custo_anual['Despesa']:
                    try: int(desp[0])
                    except: custo_anual.drop(custo_anual[custo_anual['Despesa'] == desp].index, inplace = True)

                # Novas colunas para as despesas
                new_cols = custo_anual['Despesa'].str.split('-', expand = True)
                new_cols.columns = ['cd_despesa', 'ds_despesa', '0', '1']
                custos_cidade = pd.concat([custo_anual, new_cols], axis = 1).drop(columns = 'Despesa', axis = 1)

                custos_cidade['cd_despesa'] =  [float(cd) for cd in custos_cidade['cd_despesa']]

                custos_cidade_pivoted = pd.pivot_table(custos_cidade, columns = ['Ano'], values = 'Valor por Hectare', index = ['cd_despesa','ds_despesa']).sort_index(level = 0)   
                custos_cidade_pivoted.to_excel(f'tabelas/custos/custos_prod_soja_{cidade}_{self.begin}_{self.end}.xlsx', index = True)
                #custo_anual.to_excel(f'tabelas/custos/custos_prod_soja_{cidade}_{self.begin}_{self.end}.xlsx', index = True)
                
            except: print(f'A cidade {cidade} não consta nos registros de custos da Conab')

data_get(2018,2022).costs(['Sorriso (MT)', 'Diamantino (MT)', 'Sapezal (MT)', 'Nova Mutum (MT)', 'C. Novo do Parecis (MT)', 'Nova Ubiratã (MT)', 'Querência (MT)', 'P. do Leste (MT)', 'Canarana (MT)', 'Campo Verde (MT)'])
