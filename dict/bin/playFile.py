
from threading import Thread
import Queue
import os
import pygame
import traceback

class myCustomNotifier(Thread):
    """ This class plays a given sound upon request if conditions are met.
        It also dumps output to a file. """
    def __init__(self, config):#filename=None,historyFilename='output/history.txt',enableDebug=True):
        self._config = config
        self.__enableDebug = config.options.get("enableDebug")
        self.__noSound = config.options.get("noSoundOnEvent")
        self.__noPrintToFile = config.options.get("noPrintToFile")
        self.__mySound = None
        self.__cancel = False
        self.__historyFilename = os.path.realpath(config.options.get("historyFilename"))

        """ Create our internal message queue. """
        self.__queue = Queue.Queue()
        self.__preloadSound(config.options.get("soundsRunning"))
        Thread.__init__(self)
        self._print('myCustomNotifier:__init__() - OK.')
        return

    def _notifyUser(self,data,taskList=None):
        """ Override this method to notify the user - graphically. """
        if data:
            print data
        return

    def _print(self,data,toFile=False,filename=None,important=False,taskList=None):
        if (self.__enableDebug == True) or (important == True) or taskList:
            self._notifyUser(data,taskList)

        """ Store the debug to a file if required. """
        if self.__noPrintToFile == True:
            if toFile==True and filename and len(filename)>0:
                try:
                    fp = open(filename,'a')
                    if fp:
                        fp.write(data)
                        fp.write('\r\n')
                finally:
                    if fp:
                        fp.close()
        return

    def __stopSound(self):
        """ Stop the currently playing sound. """
        self.__mySound.stop()
        return

    def __playSound(self):
        """ Play the pre-loaded sound file. """
        played = False
        if self.__mySound:
            self.__mySound.play()
            played = True
        return played

    def __loadSound(self,filename=None):
        """ Load a WAV sound file ready to be played. """

        sound = None
        if filename:
            class NoneSound:
                def play(self): pass
            if not pygame.mixer:
                sound = NoneSound()
            else:
                try:
                    sound = pygame.mixer.Sound(filename)
                except pygame.error, message:
                    self._print('Cannot load sound: %(FILENAME)s due to %(MSG)s.' %{'FILENAME':filename,'MSG':message})
            self._print('myCustomNotifier:__loadSound() - Loaded, OK.')
        return sound

    def __preloadSound(self,filename=None,mixSound=False):
        """ If we're playing a sound already -> stop it first!
            Returns the filename of the loaded sound, or None if not loaded. """

        if self.__mySound and (mixSound == False):
            self._print('LOAD_SOUND: stopping sound first !')
            """ Stop any previous sound playing. """
            self.__stopSound()

        """ Now load the sound. """
        self.__mySound = self.__loadSound(filename)

        """ Bow store the sound and it's name. """
        if self.__mySound:
            self.__mySoundName = filename
        else:
            self.__mySoundName = None
        return self.__mySound

    def run(self):
        """ Wait for a message on our message queue then action it. """
        self._print('myCustomNotifier:__init__() - OK.')
        while self.__cancel == False:
            msg = self.__getMessage()
            if msg and (self.__cancel == False):
                self._print('myCustomNotifier:run() - OK.')
                # Play the sound etc...
                (data,storeToFile,playSound,sound,taskList) = msg
                self.__outputResults(data,storeToFile,playSound,sound,taskList)
        return

    """
    def playWindowsFile(self,filename):
        # play an mp3 using Windows Media Player via an OCX control.
        if not self._mp:
            self._mp = Dispatch("WMPlayer.OCX")
            tune = self._mp.newMedia(filename)
            self._mp.currentPlaylist.appendItem(tune)
        self._mp.controls.play()
        #raw_input("Press Enter to stop playing")
        #self._mp.controls.stop()
        return
    """

    def __getMessage(self,nowait=False):
        """ Get a message from our internal message queue. """
        msg = None
        if self.__queue:
            try:
                if nowait == True:
                    msg = self.__queue.get_nowait()
                else:
                    msg = self.__queue.get()
            except:
                pass
        return msg

    def __putMessage(self,msg,nowait=True):
        """ Put a message onto our internal message queue. """
        self._print('myCustomNotifier:__putMessage() - ...')
        if self.__queue:
            if nowait == True:
                self.__queue.put_nowait(msg)
            else:
                self.__queue.put(msg)
        self._print('myCustomNotifier:__putMessage() - OK.')
        return

    def outputResults(self,data,storeToFile=True,playSound=True,sound=None,taskList=None):
        """ Asynchronous entry to the main method. """
        #print 'putting: ', data
        self.__putMessage((data,storeToFile,playSound,sound,taskList))
        return
    
    def __outputResults_storeToFile(self,filename,data):
        """ Store the data to the file if required. """
        try:
            fp = open(filename,'a')
            if fp:
                fp.write(data)
                fp.write('\r\n')
            else:
                pass
        except Exception, _e:
            pass
        finally:
            if fp:
                fp.close()
        return

    def __outputResults_actionSound(self,sound):
        """ Play the sound (preLoaded yet or not). """
        self._print('ACTION: ')
        if sound:
            self._print('ACTION: have a sound to play')
        if (self.__mySound and (sound == self.__mySoundName) and len(self.__mySoundName)>0) or not sound:
            """ being asked to play the same sound as the one which is already preloaded. """
            self._print('ACTION: playing existing sound')
        else:
            """ being asked to play a new sound, so load it. """
            self._print('ACTION: asked to play new sound, loading it')
            self.__mySound = self.__preloadSound(sound)
        
        self._print('ACTION: playing sound')
        """ Now play the sound. """
        self.__playSound()
        return

    """ override this method to provide advanced sound configuration handling and logic. """
    def _outputResults_determineSoundAction(self,data,taskList):
        """ Determine if we need to produce a sound (doesn't override the 'sound'). """
        playSound = True

        """ ToDo - Do our funky stuff in here. """

        return playSound
    
    def __outputResults(self,data,storeToFile,playSound,sound,taskList):
        """ Display logic to alert the user - 'sound' may be None -> play preloaded sound. """
        self._print('__outputResults(data=%(DATA)s,storeToFile=%(STF)d,playSound=%(PS)d,sound=%(SOUND)s,taskList=%(TL)s.'%{'DATA':data,'STF':storeToFile,'PS':playSound,'SOUND':sound,'TL':taskList})
        if data:
            self._print('got data !')
            if playSound == True and (self.__noSound == False):
                self._print('determining sound action !')
                if self._outputResults_determineSoundAction(data,taskList) == True:
                    self._print('sound actioned')
                    self.__outputResults_actionSound(sound)

            """ Display the alert to the user. """
            self._print(data,important=True,taskList=taskList)

            """ For storing to the file, strip out the extra lines. """
            data = data.strip()

            if storeToFile == True and self.__historyFilename:
                self.__outputResults_storeToFile(self.__historyFilename, data)
        else:
            """ No alert data, so nothing to do ! """
            pass
        return

def test2():
    clock = pygame.time.Clock()
    try:
        pygame.init()
        obj = myCustomNotifier('bin/error.wav',enableDebug=False)
        if obj:
            obj.start()
            oddCount = 0
            internalCount = 0
            while internalCount < 100:
                clock.tick(1)
                if oddCount == 1:
                    sound = 'bin/error.wav'
                    oddCount = 0
                else:
                    sound = 'bin/new_task.wav'
                    oddCount += 1
                internalCount += 1
                obj.outputResults('hello world !',sound=sound)
    except:
        traceback.print_exc()
    return

def test1():
    clock = pygame.time.Clock()
    try:
        pygame.init()
        #print 'Init status: ', pygame.mixer.get_init()
        mySoundObj = myCustomNotifier('bin/error.wav')
        mySoundObj.start()
        while 1:
            clock.tick(60)
    except:
        traceback.print_exc()
    return

if __name__ == "__main__":
    test2()
    print 'done'        



