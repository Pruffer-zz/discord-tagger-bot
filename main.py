# References: https://stackoverflow.com/questions/12007686/join-a-list-of-strings-in-python-and-wrap-each-string-in-quotation-marks
#             https://stackoverflow.com/questions/6893968/how-to-get-the-return-value-from-a-thread-in-python
#             https://github.com/Alkl58/szurubooru-auto-tagger
#             https://github.com/Pruffer/discord-file-downloader-bot
#             https://github.com/Pruffer/saucenao-gelbooru-tagger

# Doesn't differenciate between images and other file types. If used with https://github.com/Pruffer/discord-file-downloader-bot, we can add something like...

"""
import imghdr
type = imghdr.what(fileDownload.content)
if (type == "jpeg" || type == "gif" || type == "png"):
	# Continue..
else:
	# Fail..
"""

# I think it's fine to just not check for file types otherwise. That way we won't ever actually download the file to our server.

from bs4 import BeautifulSoup
import requests
import concurrent.futures
import discord
from saucenao_api import SauceNao

## Set to True to use SauceNao instead of IQDB. Mind the daily API limit.
useSauceNao = True

## IQDB Settings start
# Set to true to get results only from Danbooru. Will return *some* tags no matter what, but struggles with paywalled content.
danbooruDefault = True # True by default
## IQDB Settings end

botToken = # Example: "L1ZszTkJX77WicKA27xNpooTSWqqov8y86rNbDkA"
serverId = # Example: 123456789123456789

client = discord.Client()

# Function below borrowed from https://github.com/Alkl58/szurubooru-auto-tagger.
# No license specified.
def getTags(url):
	if useSauceNao == False:
		res = requests.get('https://iqdb.org/?url=' + url)
		soup = BeautifulSoup(res.text, 'html.parser')
		if(danbooruDefault == True):
			elems = soup.select("a[href*=danbooru] > img")
		elif(danbooruDefault == False):
			elems = soup.select('#pages > div:nth-child(2) > table:nth-child(1) > tr:nth-child(2) > td > a > img')
		try:
			tags = elems[0].get('title').split()[5:]
		except:
			tags = ['No tags found, or an error has occured.']
		return tags
	else:
		results = SauceNao(db=25).from_url(url)
		best = ''.join(results[0].urls)
		html = requests.get(best).text
		soup = BeautifulSoup(html, "lxml")
		types = ['general', 'character', 'artist', 'copyright', 'metadata']
		result = dict.fromkeys(types, [])
		resultPrint = ""
		for item in types: 
			try:
				list = soup.find_all("li", attrs={"class": "tag-type-" + item})
				tags = []
				for tag in list:
					for a in tag.find_all("a"):
						if ''.join(a.contents) != '?':
							tags.append(''.join(a.contents))
					result[item] = tags
				resultPrint = resultPrint + "\n**`" + item + "`**:\n" + ', '.join('`{0}`'.format(i) for i in result[item])
			except:
				resultPrint = "`No tags found, or an error has occurred.`"
		return resultPrint

def getMessageLink(guildId, channelId, messageId):
	return 'https://discord.com/channels/' + str(guildId) + '/' + str(channelId) + '/' + str(messageId)

@client.event
async def on_message(message):
	if message.attachments and message.guild.id == serverId:
		for file in message.attachments:
			with concurrent.futures.ThreadPoolExecutor() as executor:
				thread = executor.submit(getTags, ''.join(file.url))
				threadResult = thread.result()
				if useSauceNao == False:
					embedDescription = ', '.join('`{0}`'.format(i) for i in threadResult)
				else:
					embedDescription = threadResult
				embed=discord.Embed(
					title="Image tags",
					url=getMessageLink(message.guild.id, message.channel.id, message.id),
					description=embedDescription,
					color=0x0088ff
				)
				await message.channel.send(embed=embed)

client.run(botToken)
