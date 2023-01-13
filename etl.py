
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

        url = 'https://www.conab.gov.br/info-agro/custos-de-producao/planilhas-de-custo-de-producao/item/download/42998_ccb0d1f5aa84efd0c88c80383f54844b'
        wget.download(url)
        archive = 'Soja_Serie_Historica_1997-2022.xls'

        for cidade in [f'{city[0:len(city)-5]}-MT' for city in cidades_mt]:
            #try:
            custo_anual = pd.DataFrame()
            for year in range(self.begin, self.end + 1):
                if year == range(self.begin, self.end + 1)[1]:
                    custos_ano_base = pd.read_excel(archive, sheet_name = f'OGM-{cidade}-{year}', skiprows = 7, usecols = ['B,H'])
                    custos_ano_base.columns = ['Conta', f'{year}']
                    custo_anual = pd.concat([custo_anual, custos_ano_base])
                else:
                    if year > 2021:
                        custos = pd.read_excel(archive, sheet_name = f'OGM-{cidade}-{year}', skiprows = 7, usecols = ['B,H'])
                        custos.columns = ['Conta', f'{year}']
                        custo_anual = custo_anual.merge(custos, how = 'full', on = 'Conta').fillna(0, inplace=True)
                    if year < 2021:
                        custos = pd.read_excel(archive, sheet_name = f'OGM-{cidade}-{year}', skiprows = 6)
                        custos = custos[custos.columns[0:2]]
                        custos.columns = ['Conta', f'{year}']
                        custo_anual = custo_anual.merge(custos, how = 'full', on = 'Conta')
            custo_anual.to_csv(f'tabelas/custos/custo_anual_{cidade}_de_{self.begin}_ate_{self.end}.csv')
                
            #except: print(f'A cidade {cidade} não consta nos registros de custos da Conab')
