import json
import requests

from . import config
import logging
logger = logging.getLogger(__name__)

SERVER_URL = config.private.MORIARTY_URL + '/rest/executeWorkFlow/'

TEXT_OPINION_STR = {
    '-1.0': "Muy malo",
    '-0.5': "Malo",
    '0.0': "Neutro",
    '0.5': "Bueno",
    '1.0': "Muy bueno",
}


def call_WF(text, textSentiment):
    endpoint = SERVER_URL + config.settings.MORIARTY_WORKFLOW + '?wait=true'

    wordsMin = 10
    wordsMax = 30

    data = {
        'NerBoolean': True,
        'OpinionBoolean': True,
        'SummarizerBoolean': True,
        'ProcessingBoolean': True,
        'CategorizationBoolean': True,
        'wordsMin': wordsMin,
        'wordsMax': wordsMax,
        'algorithm': 'rank',
        'text': text,
        'textSentiment': textSentiment
    }
    data_json = json.dumps(data)
    headers = {'Content-type': 'application/json'}

    try:
        logger.info("Sending Moriarty post request...")
        response = requests.post(endpoint, data=data_json, headers=headers,)
        # timeout=config.settings.MORIARTY_TIMEOUT)
        logger.debug("Moriarty request response code: {}".format(response.status_code))

        response.raise_for_status()
        results = response.json()['results']
        logger.debug(results)
    except requests.HTTPError:
        logger.exception("Moriarty WF request failed with status code {}".format(response.status_code))
        logger.error("text: \t{}".format(text))
        logger.error("textSentiment: \t{}".format(textSentiment))
    except requests.ConnectionError as e:
        logger.error("Moriarty WF request failed: {}".format(e))
    except requests.ReadTimeout:
        logger.error("Moriarty WF request timed-out")
    except requests.RequestException:
        logger.exception("Moriarty WF request failed")
    except TypeError:
        logger.error("Moriarty WF results json parse failed")
        logger.error(response.text)
    else:
        try:
            if results['language'] == 'Spanish':
                return {
                    'places': results['localizacionesList'],
                    'organizations': results['organizacionesList'],
                    'people': results['personasList'],
                    'textOpinion': results.get('opinion', "0.0"),
                    'textOpinionStr': TEXT_OPINION_STR[results.get('opinion', "0.0")],
                    'summary': results['summarizedText'],
                    'textProcessed': results.get('textProcessed'),
                    'categories': results.get('categoriesList')
                }
            else:
                logger.warning("Text not in spanish")
        except KeyError:
            logger.error("Moriarty failed")
            logger.error(response.json()['message'])
            logger.error("results: \t{}".format(results))
