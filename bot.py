"""
WARNING:

Please make sure you install the bot with `pip install -e .` in order to get all the dependencies
on your Python environment.

Also, if you are using PyCharm or another IDE, make sure that you use the SAME Python interpreter
as your IDE.

If you get an error like:
```
ModuleNotFoundError: No module named 'botcity'
```

This means that you are likely using a different Python interpreter than the one used to install the bot.
To fix this, you can either:
- Use the same interpreter as your IDE and install your bot with `pip install --upgrade -r requirements.txt`
- Use the same interpreter as the one used to install the bot (`pip install --upgrade -r requirements.txt`)

Please refer to the documentation for more information at https://documentation.botcity.dev/
"""

# Import for the Web Bot
from botcity.web import WebBot, Browser, By

# Import for integration with BotCity Maestro SDK
from botcity.maestro import *
from botcity.web.util import element_as_select
from botcity.web.parsers import table_to_dict
from botcity.plugins.excel import BotExcelPlugin

# Disable errors if we are not connected to Maestro
BotMaestroSDK.RAISE_NOT_CONNECTED = False

excel = BotExcelPlugin()
excel.add_row(['Cidade', 'População'])

def main():
    # Runner passes the server url, the id of the task being executed,
    # the access token and the parameters that this task receives (when applicable).
    maestro = BotMaestroSDK.from_sys_args()
    ## Fetch the BotExecution with details from the task, including parameters
    execution = maestro.get_execution()

    # maestro.login(server='https://developers.botcity.dev', 
    #               login='e6cf8e96-7313-4a85-b35c-7c254b4eb91d', 
    #               key='E6C_FZX7F3NBGM3MZVTMJAXP')

    print(f"Task ID is: {execution.task_id}")
    print(f"Task Parameters are: {execution.parameters}")

    bot = WebBot()

    # Configure whether or not to run on headless mode
    bot.headless = False

    # Uncomment to change the default Browser to Firefox
    bot.browser = Browser.CHROME

    # Uncomment to set the WebDriver path
    bot.driver_path = "./resources/chromedriver.exe"

    bot.browse("https://buscacepinter.correios.com.br/app/faixa_cep_uf_localidade/index.php")

    dropuf = element_as_select(bot.find_element("//select[@id='uf']", By.XPATH))
    dropuf.select_by_value('PR')

    btnpesquisar = bot.find_element("//button[@id='btn_pesquisar']", By.XPATH)
    btnpesquisar.click()

    bot.wait(3000)
    print('Aguardando 3 segundos')

    tblresultado = bot.find_element("//table[@id='resultado-DNEC']", By.XPATH)
    tbldados = table_to_dict(table=tblresultado)

    bot.navigate_to('https://cidades.ibge.gov.br/brasil/panorama')
    bot.wait(3000)

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
                cmppesquisa = bot.find_element("//input[@placeholder='O que você procura?']", By.XPATH)
                cmppesquisa.send_keys(str_cidade)

                rstpesquisa = bot.find_element(f"//a[span[contains(text(), '{str_cidade}')] and span[contains(text(), '{str_estado}')]]", By.XPATH)
                rstpesquisa.click()

                bot.wait(2000)

                poptxt = bot.find_element("//div[@class='indicador__valor']", By.XPATH)
                str_populacao = poptxt.text
                
                excel.add_row([str_cidade, str_populacao])
                maestro.new_log_entry(activity_label='CIDADES', values={"cidade": f"{str_cidade}", 
                                                                        "populacao": f"{str_populacao}"})

                cidade_anterior = str_cidade
                contador += 1
        else:
            break

    excel.write('./resources/resultado.xlsx')

    bot.stop_browser()

    maestro.finish_task(
        task_id=execution.task_id,
        status=AutomationTaskFinishStatus.SUCCESS,
        message="Sucesso!"
    )


def not_found(label):
    print(f"Element not found: {label}")


if __name__ == '__main__':
    main()
