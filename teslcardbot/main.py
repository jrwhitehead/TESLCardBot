from bot import TESLCardBot
import argparse
from prawcore.exceptions import PrawcoreException

def log(msg):
    print('tesl-bot-9000 # {}'.format(msg))
		
def main():
    parser = argparse.ArgumentParser(description='The Elder Scrolls: Legends bot for Reddit.')
    # No default value to prevent accidental mayhem
    parser.add_argument('-s', '--target_sub', required=True, help='What subreddit will this instance monitor?')

    args = parser.parse_args()

    log('Started lurking in (/r/{})'.format(args.target_sub))
    bot = TESLCardBot(author='NotGooseFromTopGun', target_sub=args.target_sub)
    
    while True:	
        try:
            bot.start(batch_limit=5, buffer_size=500)

        except PrawcoreException as e:
            log('Reddit seems to be down! Aborting.')
            log(e)
            return
			
        log('Stopped running.')
	
if __name__ == '__main__':
    main()
