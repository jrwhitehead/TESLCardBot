from bot import TESLCardBot
import argparse
from prawcore.exceptions import PrawcoreException
		
def main():
    parser = argparse.ArgumentParser(description='The Elder Scrolls: Legends bot for Reddit.')
    # No default value to prevent accidental mayhem
    parser.add_argument('-s', '--target_sub', required=True, help='What subreddit will this instance monitor?')

    args = parser.parse_args()


    bot = TESLCardBot(author='NotGooseFromTopGun', target_sub=args.target_sub)
    bot.log('Started lurking in (/r/{})'.format(args.target_sub))
	
    while True:	
        try:
            bot.start(batch_limit=5, buffer_size=500)

        except PrawcoreException as e:
            bot.log('Reddit seems to be down! Aborting.')
            bot.log(e)
            return
			
        bot.log('Stopped running.')
	
if __name__ == '__main__':
    main()
