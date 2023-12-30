#Imports
from botcity.web import WebBot, Browser, By
from botcity.maestro import *
from botcity.web.util import element_as_select
from botcity.web.parsers import table_to_dict
from botcity.plugins.excel import BotExcelPlugin

# Disable errors if we are not connected to Maestro
BotMaestroSDK.RAISE_NOT_CONNECTED = False

#Create a excel instance and add a header row
excel = BotExcelPlugin()
excel.add_row(['Cidade', 'População'])

def main():

    maestro = BotMaestroSDK.from_sys_args()
    execution = maestro.get_execution()

    #Uncomment to authenticate
    # maestro.login(server='', 
    #               login='', 
    #               key='')

    print(f"Task ID is: {execution.task_id}")
    print(f"Task Parameters are: {execution.parameters}")

    bot = WebBot()

    # Configure whether or not to run on headless mode
    bot.headless = False

    # Uncomment to change the default Browser to Firefox
    bot.browser = Browser.CHROME

    bot.driver_path = "./resources/chromedriver.exe"

    #Open browser and navigate to correios website
    bot.browse("https://buscacepinter.correios.com.br/app/faixa_cep_uf_localidade/index.php")

    #Select state PR
    dropuf = element_as_select(bot.find_element("//select[@id='uf']", By.XPATH))
    dropuf.select_by_value('PR')

    #Click search button
    btnpesquisar = bot.find_element("//button[@id='btn_pesquisar']", By.XPATH)
    btnpesquisar.click()

    bot.wait(3000)

    #Get table and save as dictionary
    tblresultado = bot.find_element("//table[@id='resultado-DNEC']", By.XPATH)
    tbldados = table_to_dict(table=tblresultado)

    #Navigate to IBGE website
    bot.navigate_to('https://cidades.ibge.gov.br/brasil/panorama')
    bot.wait(3000)

    #Avoid duplicity and limit to 5 rows
    cidade_anterior = ''
    contador = 0

    for row in tbldados:

        str_cidade = row['localidade']
        str_estado = 'PR'

        if contador < 5:

            if str_cidade == cidade_anterior:
                print(f'Skip {str_cidade}')
                pass

            else:
                #Click search box and type city name
                cmppesquisa = bot.find_element("//input[@placeholder='O que você procura?']", By.XPATH)
                cmppesquisa.send_keys(str_cidade)

                #Select city
                rstpesquisa = bot.find_element(f"//a[span[contains(text(), '{str_cidade}')] and span[contains(text(), '{str_estado}')]]", By.XPATH)
                rstpesquisa.click()

                bot.wait(2000)

                #Get population value
                poptxt = bot.find_element("//div[@class='indicador__valor']", By.XPATH)
                str_populacao = poptxt.text
                
                #Save results in an excel sheet
                excel.add_row([str_cidade, str_populacao])
                maestro.new_log_entry(activity_label='CIDADES', values={"cidade": f"{str_cidade}", 
                                                                        "populacao": f"{str_populacao}"})

                cidade_anterior = str_cidade
                contador += 1
        else:
            break
    
    #Save excel file
    excel.write('./resources/resultado.xlsx')

    bot.stop_browser()

    #Uncomment if running in Maestro
    # maestro.finish_task(
    #     task_id=execution.task_id,
    #     status=AutomationTaskFinishStatus.SUCCESS,
    #     message="Sucesso!"
    # )


def not_found(label):
    print(f"Element not found: {label}")


if __name__ == '__main__':
    main()
