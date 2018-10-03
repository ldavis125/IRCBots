"""
==============================================================================================================================

           Name: artBot
         Author: ldavis
Current Version: 1.3.5
   Date Written: February 2018
    Description: A simple irc bot that prints out from a selection of ASCII art messages, along with a calming quote by
        the one and only Bob Ross. artBot also sends out a message whenever lunchtime or break arrives. The structure of
        artBot was inspired by jnguyen's work on Seahorse and MemeBot, and also noahsiano's current revision of theCount.

==============================================================================================================================
"""

import random
import re
import json

import datetime
from enum import Enum

from twisted.words.protocols import irc
from twisted.internet import task, reactor, protocol

class DayOfWeek(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

with open(r'config.json') as file:
    config = json.load(file)

class ArtBot(irc.IRCClient):
    nickname = config['nick']

    def __init__(self):
        self.painting = False
        
        self.humpdayPaintingQueued = False

        self.humpday = DayOfWeek.WEDNESDAY

        self.lunchtimePaintingQueued = False
        self.breaktimePaintingQueued = False
        self.teatimePaintingQueued = False

        self.dailyEventTime= datetime.time(hour=config['daily-event-time']['hour'],
                                        minute=config['daily-event-time']['minute'])
        self.lunchtime = datetime.time(hour=config['lunchtime']['hour'],
                                        minute=config['lunchtime']['minute'])
        self.breaktime = datetime.time(hour=config['breaktime']['hour'],
                                        minute=config['breaktime']['minute'])
        self.teatime = datetime.time(hour=config['teatime']['hour'],
                                        minute=config['teatime']['minute'])

        self.tags = []
        self.loadTags()

        lc = task.LoopingCall(self.scheduleEvents)
        lc.start(60)

    def signedOn(self):
        self.join(config['art-channel'])
        self.join(config['tea-channel'])

        print('Channel: ' + config['art-channel'])
        print('Channel: ' + config['tea-channel'])
        print('Nickname: ' + config['nick'])
    
    def luserClient(self, info):
        print(info)

    def userJoined(self, user, channel):
        print('Joined:', channel, user)

    def userLeft(self, user, channel):
        print('LEFT:', channel, user)

    def userQuit(self, user, quitMessage):
        print('QUIT:', user)

    def userRenamed(self, oldName, newName):
        print(oldName + ' has been renamed to ' + newName)

    def privmsg(self, user, channel, message):
        if not self.isArtChannel(channel):
            return

        message = irc.stripFormatting(message).lower()
        
        if self.isHelpCommand(message):
            self.printHelpMessage()
        elif self.isListTagsCommand(message):
            self.printTags()
        elif self.isPaintCommand(message):
            self.paintMessageByNumArgs(message)

    def isArtChannel(self, channel):
        return channel == config['art-channel']

    def isHelpCommand(self, message):
        return re.match('^' + config['nick'] + ',\s+help$', message)

    def isListTagsCommand(self, message):
        return re.match('^' + config['nick'] + ',\s+list-tags$', message)

    def isPaintCommand(self, message):
        return re.match('^' + config['nick'] + ',\s+paint.*$', message)

    def printHelpMessage(self):
        if self.painting:
            return

        self.msg(config['art-channel'], 'List of commands:')
        self.msg(config['art-channel'], '\x02artBot, help:\x02 Ask me for help')
        self.msg(config['art-channel'], '\x02artBot, paint <tag>:\x02 Paint ASCII message by tag (random by default)')
        self.msg(config['art-channel'], '\x02artBot, list-tags:\x02 Lists all message tags for painting')

    def printTags(self):
        if self.painting:
            return

        self.msg(config['art-channel'], 'Here is a list of available tags (artBot, paint <tag>):')
        
        line = ', '.join(sorted(self.tags))
        self.msg(config['art-channel'], line)

    def paintMessageByNumArgs(self, message):
        args = message.split()
        if len(args) == 2:
            self.paintMessageRandom()
        else:
            self.paintMessageByTag(args[2])

    def paintLunchtimeMessage(self):
        if self.painting:
            self.lunchtimePaintingQueued = True
            return

        self.paintMessage(config['art-channel'], config['lunchtime-painting'], False)

    def paintBreaktimeMessage(self):
        if self.painting:
            self.breaktimePaintingQueued = True
            return

        self.paintMessage(config['art-channel'], config['breaktime-painting'], False)

    def paintTeatimeMessage(self):
        if self.painting:
            self.teatimePaintingQueued = True
            return

        self.paintMessage(config['tea-channel'], config['teatime-painting'], False)

    def paintHumpdayMessage(self):
        if self.painting:
            self.humpdayPaintingQueued = True
            return

        self.paintMessage(config['art-channel'], config['humpday-painting'], False)

    def paintMessageRandom(self):
        painting = random.choice(config['paintings'])
        self.paintMessage(config['art-channel'], painting['message'], painting['coloredMessage'])

    def paintMessageByTag(self, tag):
        for painting in config['paintings']:
            if re.match('^' + tag + '$', painting['tag']):
                self.paintMessage(config['art-channel'], painting['message'], painting['coloredMessage'])
                break

    def paintMessage(self, channel, message, coloredMessage):
        if self.painting:
            return

        # set to 1 so that the first line is painted at the same moment
        # artBot logs on
        numSeconds = 1
        reactor.callLater(numSeconds, self.enablePainting)

        for msg in message:
            if coloredMessage:
                msg = msg.replace('^k', '\03')

            reactor.callLater(numSeconds, self.printDelayedMessage, channel, msg)
            numSeconds += 2

        reactor.callLater(numSeconds, self.printDelayedMessage, channel, self.getQuote())
        reactor.callLater(numSeconds, self.disablePainting)

    def getQuote(self):
        quote = random.choice(config['quotes'])
        return quote + ' - Bob Ross'

    def printDelayedMessage(self, channel, message):
        self.msg(channel, message)

    def enablePainting(self):
        self.painting = True

    def disablePainting(self):
        self.painting = False

    def loadTags(self):
        for painting in config['paintings']:
            self.tags.append(painting['tag'])

    def paintingEventQueued(self):
        if self.humpdayPaintingQueued:
            self.humpdayPaintingQueued = False
            self.paintHumpdayMessage()
            return True

        if self.lunchtimePaintingQueued:
            self.lunchtimePaintingQueued = False
            self.paintLunchtimeMessage()
            return True
        elif self.breaktimePaintingQueued:
            self.breaktimePaintingQueued = False
            self.paintBreaktimeMessage()
            return True
        elif self.teatimePaintingQueued:
            self.teatimePaintingQueued = False
            self.paintTeatimeMessage()
            return True

        return False

    def paintEventMessageIfTime(self, dayOfWeek, hour, minute):
        # Weekly events
        if hour == self.dailyEventTime.hour and minute == self.dailyEventTime.minute:
            if dayOfWeek == self.humpday:
                self.paintHumpdayMessage()
        
        # Daily events
        if hour == self.lunchtime.hour and minute == self.lunchtime.minute:
            self.paintLunchtimeMessage()
        elif hour == self.breaktime.hour and minute == self.breaktime.minute:
            self.paintBreaktimeMessage()
        elif hour == self.teatime.hour and minute == self.teatime.minute:
            self.paintTeatimeMessage()

    def scheduleEvents(self):
        today = datetime.datetime.today().weekday()
        if self.paintingEventQueued() \
                or today == DayOfWeek.SATURDAY \
                or today == DayOfWeek.SUNDAY:
            return

        time = datetime.datetime.time(datetime.datetime.now())
        self.paintEventMessageIfTime(today, time.hour, time.minute)

def main():
    server = config['server']
    port = 6667

    client = protocol.ClientFactory()
    client.protocol = ArtBot

    reactor.connectTCP(server, port, client)
    reactor.run()

if __name__ == '__main__':
    main()
