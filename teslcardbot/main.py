from bot import TESLCardBot
import argparse
from prawcore.exceptions import PrawcoreException

def log(self, msg):
    print('tesl-bot-9000 # {}'.format(msg))
		
def main():
    parser = argparse.ArgumentParser(description='The Elder Scrolls: Legends bot for Reddit.')
    # No default value to prevent accidental mayhem
    parser.add_argument('-s', '--target_sub', required=True, help='What subreddit will this instance monitor?')

    args = parser.parse_args()

    self.log('Started lurking in (/r/{})'.format(args.target_sub))
    bot = TESLCardBot(author='NotGooseFromTopGun', target_sub=args.target_sub)
	
    try:
        bot.start(batch_limit=5, buffer_size=500)

    except PrawcoreException as e:
        self.log('Reddit seems to be down! Aborting.')
        self.log(e)
			
    self.log('Stopped running.')
	
if __name__ == '__main__':
    main()
