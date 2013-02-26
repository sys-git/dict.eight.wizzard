#
#   2 OPTIONS TO MODIFY >>>
#
from dict.bin.playFile import myCustomNotifier
from mechanize import Browser
from pygame.locals import *
from threading import Thread
from types import *
import Queue
import os
import pygame
import time
import traceback

""" Modify the python path to point to the /bin directory. """
if __name__ == "__main__":
    __dirname,__filename = os.path.split(sys.argv[0])
    sys.path.insert(0,os.path.join(__dirname,'bin'))

""" Testing parameters: """
IN_DEBUG_MODE = False
DEFUALT_TEST_WEB_PAGE = False

""" basic common method for getting the initial output string. """
def getRootString(data=None):
    if IN_DEBUG_MODE == True:
        return time.strftime("%H:%M:%S (%d %b %Y - %a)", time.gmtime())
    else:
        return time.strftime("%H:%M (%d %b %Y - %a)", time.gmtime())

""" Derived class for notifying the user of events. """
class myNote(myCustomNotifier):
    def __init__(self, config, pygameData=None):
        """ Call the base-class's __init__() method. """
        myCustomNotifier.__init__(self, config)
        self.__latestTasks = {'Available':[],'To complete':[]}
        self.__pygameData = pygameData

    def _outputResults_determineSoundAction(self,data,taskList):
        """ Overridden method to determine if we need to play a sound or not. """
        playSound = False
        
        if self._config.options.get("disableAdaptiveSound") == False:
            if taskList:
                if taskList['To complete'] == None:
                    if len(taskList['Available'])>0:
                        if self.__findNewTasks(taskList,self.__latestTasks) == True:
                            """ Only ever play a sound IF we don't need to complete any first! """
                            playSound = True
                    self.__latestTasks['Available'] = taskList['Available']
                self.__latestTasks['To complete'] = taskList['To complete']
            else:
                """ Play the given sound. """
                playSound = True
        if self._config.options.get("noSoundOnEvent") == False:
            if playSound == True:
                playSound = True

        self._print('Determined that we should playSound = ', playSound)
        return playSound

    def __listItemExist(self,item,theList):
        """ Does 'theList' contain the 'item'? """
        for i in theList:
            if i == item:
                return True
        return False

    def __findNewTasks(self,new,old):
        """ Return 'True' if an item in 'new' does not exist in 'old'. """
        if new and old and isinstance(new,dict) and isinstance(old,dict):
            for anItem in new['Available']:
                if self.__listItemExist(anItem,old['Available']) == False:
                    return True
        return False

    def _notifyUser(self,data,taskList=None):
        """ Overridden method to determine if we need to play a sound or not. """

        """
        pygameData['clock']
        pygameData['screen']
        pygameData['background']
        """

        if not self.__pygameData:
            myCustomNotifier._notifyUser(self,data)
        else:
            """ Data contains the raw text which we parsed (and used to go to stdout),
                taskList contains the 'Available' and 'To Complete' fields. """
            if data:
                """ Get arid of any CR and/or LF in the text string """
                data = data.strip()
                #print data
            if taskList:
                #print taskList
                pass

            """ This simply renders the raw text to our window. """
            background = self.__pygameData['background']
            if pygame.font:
                font = pygame.font.Font(None,18)
                text = font.render(data,1,(10,10,10))
                textpos = text.get_rect(centerx=background.get_width()/2)
                background.fill((250, 250, 250))
                background.blit(text,textpos)

                if taskList and not taskList['To complete'] and len(taskList['Available'])>0:
                    # No tasks to complete, Let the user know there are NEW tasks available !
                    newText = 'NEW Available tasks !'
                    font = pygame.font.Font(None,30)
                    text = font.render(newText,1,(10,10,10))
                    textpos = text.get_rect(centery=background.get_height()/2,centerx=background.get_width()/2)
                    background.blit(text,textpos)
                    #newText = ''
                    #for i in taskList['Available']:
                    #    newText += ' %(TASK) -'
                    #if len(newText)>0:
                    #    newText = newText[:-1]
                    #font = pygame.font.Font(None,26)
                    #text = font.render(newText,1,(10,10,10))
                    #textpos = text.get_rect(centery=background.get_height()*(1/4),centerx=background.get_width()/2)
                    #background.blit(text,textpos)
                

""" A basic timer class to send a msg to the 'msgQueue' upon firing.
    If no message queue is provided, one is created """
class myTimer(Thread):
    def __init__(self,seconds,msgQueue=None,debug=None,data=None,singleShot=True):
        self.__singleShot = singleShot
        self.__runTime = seconds
        if msgQueue:
            self.__queue = msgQueue
        else:
            self.__queue = Queue.Queue()
        self.__cancel = False
        Thread.__init__(self)
        return

    def run(self):
        """ Overridden Thread class's run method to do the actual work. """
        while self.__cancel == False:
            time.sleep(self.__runTime)

            if self.__cancel == False:
                timeNow = getRootString()
                self.__putMessage(('times up',self.__runTime,timeNow))
                if self.__singleShot == True:
                    self.terminate()
                    """ We should now fall out on the next time round this loop! """
        return

    def __putMessage(self,msg,nowait=True):
        """ Put a message onto the given message queue -> Format is: msg=(text,timerTime,timeWhenFired).
            Don't put the message if we've been asked to cancel. """
        if self.__queue and (self.__cancel == False):
            if nowait == True:
                self.__queue.put_nowait(msg)
            else:
                self.__queue.put(msg)
        return

    def wait(self):
        """ Wait for the timer to expire. """
        self.__queue.get()

        """ If we're a single shot timer, stop ourselves now we've fired. """
        if self.__singleShot == True:
            self.terminate()
        return

    def terminate(self):
        """ Method to allow for timer termination after the next timer event. """
        self.__cancel = True
        return

    def cancel(self):
        """ Depreciated method for cancelling. """
        self.terminate()
        return

""" A thread class to login to and parse the secure web page, notifying the user when necessary. """
class searchWebSites(Thread):
    def __init__(self, config, notifier=None, testData=None):
        self._config = config
        self.__testData = testData
        self.__loginErrorCount = 0
        self.__enableDebug = self._config.options.get("enableDebug")
        self.__cancel = False
        self.__host = self._config.options.get("defaultWebsiteAddress")
        self.__username = self._config.options.get("defaultWebsiteUsername")
        self.__password = self._config.options.get("defaultWebsitePassword")
        self.__notifier = notifier
        self.__httpsRefreshMin = self._config.options.get("defaultminimumRefreshPeriod")
        self.__httpsRefreshMax = self._config.options.get("defaultmaximumRefreshPeriod")
        self.__httpsRefresh = self._config.options.get("defaultRefreshPeriod")
        Thread.__init__(self)

    def terminate(self):
        """ Method to allow for thread termination after the next run loop. """
        self.__cancel = True

    def _bombOut(self,text,Fatal=True):
        """ Provide a dump report and optionally bomb out on the given error. """
        if IN_DEBUG_MODE == True:
            traceback.print_exc()
        if Fatal and Fatal == True:
            if text and len(text) > 0:
                sys.exit(text)
            else:
                sys.exit('mechaniser Bombing out for unknown reason !!!')

    def __checkFormTypeIsImage(self,control):
        if control:
            if control.type == 'image':
                return True
        return False

    def __uniqueList(self,listData,ordered=True):
        newList = None
        tmpDict = {}

        if listData:
            newList = []
            if len(listData) != 0:
                for anItem in listData:
                    tmpDict[anItem] = 1
                newList = tmpDict.keys()
                if ordered == True:
                    newList.sort()
        return newList

    def _parseWebPage(self,data):
        """ The basic logic to parse the html returned when we've logged into the secure login page. """
        error = False
        if data:
            myTaskList = {}
            myTaskList['Available'] = []
            myTaskList['To complete'] = None
            dataLines = data.splitlines()
            rootName = getRootString()
            if data.lower().find('logged in as') != -1:
                if data.find('No tasks available') != -1:
                    rootName += ' -> No tasks.'
                    if self.__notifier:
                        self.__notifier.outputResults(rootName,playSound=False,taskList=myTaskList)
                else:
                    playSound = False
                    taskToComplete = None
                    for aLine in dataLines:
                        if aLine.lower().find('must be completed first') != -1:
                            pre,_,post = aLine.lower().partition('must be completed first')
                            pre,_,post = pre.lower().partition('>task ')
                            if len(post)>0:
                                taskToComplete = post.strip()
                                myTaskList['To complete'] = taskToComplete
                    if data.lower().find('select task') != -1:
                        _ = data.count('radio')
                        TaskIDs = []
                        for aLine in dataLines:
                            if aLine.lower().find('radio') != -1:
                                pre, _, post = aLine.lower().partition('&nbsp;')
                                if len(post)>0:
                                    pre, _, post = post.partition('</td>')
                                    numericalTaskId = pre.strip()
                                    TaskIDs.append(numericalTaskId)
                        if len(TaskIDs)>0:
                            TaskIDs = self.__uniqueList(TaskIDs)
                        if not taskToComplete:
                            rootName += ' -> Available: - '
                            for aTask in TaskIDs:
                                rootName += ' %(TASK)s,'%{'TASK':aTask}
                                myTaskList['Available'].append(aTask)
                            if len(TaskIDs)>0:
                                rootName = rootName[:-1]
                            playSound = True
                        else:
                            rootName += ' -> To complete: - '
                            rootName += '%(TASK)s'%{'TASK':taskToComplete}
                            if len(TaskIDs)>0:
                                rootName += ', Available: - '
                                try:
                                    TaskIDs.remove(taskToComplete)
                                except:
                                    pass
                                for aTask in TaskIDs:
                                    rootName += ' %(TASK)s,'%{'TASK':aTask}
                                    myTaskList['Available'].append(aTask)
                                rootName = rootName[:-1]
                        if not taskToComplete:
                            rootName = self._config.get("defaultNotificationSeperator") + rootName
                            rootName += self._config.get("defaultNotificationSeperator")
                        if self.__notifier:
                            self.__notifier.outputResults(rootName,playSound=playSound,sound=self._config.get("soundNew"),taskList=myTaskList)
                    else:
                        rootName += ' -> To complete: - '
                        rootName += '%(TASK)s.'%{'TASK':taskToComplete}
                        rootName += self._config.get("defaultNotificationSeperator") + rootName
                        rootName += self._config.get("defaultNotificationSeperator")
                        if self.__notifier:
                            self.__notifier.outputResults(rootName,playSound=False,taskList=myTaskList)
            else:
                rootName += ' -> ERROR: - Unable to parse web page.'
                if self.__notifier:
                    self.__notifier.outputResults(rootName,playSound=True,sound=self._config.get("soundError"))
                error = True
        return error

    def __calcDelay(self,periodInSeconds):
        """ Calculate the delay before we reload the web page. """
        if periodInSeconds < self.__httpsRefreshMin:
            delay = self.__httpsRefreshMin
        elif periodInSeconds > self.__httpsRefreshMax:
            delay = self.__httpsRefreshMax
        else:
            delay = periodInSeconds
        return delay

    def __websiteLogin(self,hostname,username,password):
        """ Login to the secure web page. """
        try:
            br = Browser()
            br.open(hostname)
            br.select_form(name="FormName")
            br["UserName"] = username
            br["Password"] = password
            response = br.submit()  
        except:
            response = None
            br = None
            rootName = getRootString()
            rootName += ' -> ERROR - Failed to login to the web page.'
            self._print(rootName,important=False)
            self._bombOut(rootName,Fatal=False)
        return br, response

    def _print(self,data,important=False):
        """ Print out the data if it's important ! """
        if (self.__enableDebug==True and data and len(data)>0) or (important==True):
            print data
        return

    def __waitOnTimer(self,aDelay):
        """ A function to wait for 'aDelay' seconds.  """

        """ Create the temporary message queue. """
        my_timer = myTimer(aDelay,singleShot=True)

        if my_timer:
            """ Now start the timer. """
            my_timer.start()

            """ Now wait for the timer event to expire. """
            my_timer.wait()

            self._print('Watchdog timer event.',important=False)

            """ Now cancel the timer, just-in-case. """
            my_timer.cancel()
        else:
            """ Just sleep if there's a problem with the timer. """
            rootName = getRootString()
            rootName += ' -> ERROR - Failed to create the timer, sleeping for 1 minute and going anyway.'
            self._print(rootName,important=False)
            time.sleep(aDelay)
        return

    def _getTestData(self):
        data = None
        if self.__testData:
            """ Do our funky stuff in this object. """
            data = self.__testData.get()
        return data

    def _readResponse(self,response):
        """ Read the web page - or provide a test page. """
        data = None
        if response:
            if DEFUALT_TEST_WEB_PAGE == True:
                tmpData = self._getTestData()
                if tmpData:
                    data = tmpData
                else:
                    data = response.read()
            else:
                data = response.read()
        return data

    def __websiteAction(self,hostname,username,password):
        """ Method to perform this threads' main action. """

        """ Login to the web page in the first place! """
        br, response = self.__websiteLogin(hostname, username, password)

        """ If we've logged in, perform our actions. """
        if response and br:
            self.__loginErrorCount = 0

            """ Read the web page contents. """
            LogedInWebPageData = self._readResponse(response)

            """ Calculate the timer delay. """
            myDelay = self.__calcDelay(self.__httpsRefresh)

            errCount = 0
            while (self.__cancel == False) and (errCount < 10):
                """ Parse the web page and perform any actions. """
                error = self._parseWebPage(LogedInWebPageData)

                if error == True:
                    """ There was an error parsing the web page, try logging in again. """
                    return
                else:
                    """ Set the timer going to reload the web page. """
                    self.__waitOnTimer(myDelay)
                    """ The given time has passed now. """

                    """ Now reload the web page and read it again. """
                    response = br.reload()
                    if response:
                        LogedInWebPageData = self._readResponse(response)
                        errCount = 0
                    else:
                        LogedInWebPageData = None
                        """ When the error count reaches 10, we'll relogin again. """
                        errCount += 1
                        rootName = getRootString()
                        rootName += " -> ERROR - Failed to reload the web page 10 times !"
                        self._print(rootName,important=True)
                        raise 
        else:
            """ Failed to login to the web page, just try again! """
            rootName = getRootString()
            rootName += " -> ERROR - Failed to login to the web page !"
            self._print(rootName,important=False)
            self.__loginErrorCount += 1
        return

    def run(self):
        """ Overridden Thread's run method to do the actual work. """
        while self.__cancel == False:
            if self.__loginErrorCount == 10:
                """ Failed to login to the web page 10 times in-a-row, better wait a while and retry. """
                rootName = getRootString()
                rootName += ' -> ERROR - Failed to login to the web page 10 times in-a-row, waiting 1 minute and retrying.'
                self._print(rootName,important=True)

                """ Wait for the given time before attempting a relogin. """
                self.__waitOnTimer(self._config.get("defaultLoginRetryTimeout"))
                self.__loginErrorCount = 0

            try:
                self.__websiteAction(self.__host,self.__username,self.__password)
            except:
                rootName = getRootString()
                rootName += ' -> ERROR - Starting again.'
                self._bombOut(rootName,Fatal=False)
        return

"""
    Change program structure: New thread for getting the web page.
    Send a message to the main pygame loop in __main__ when data arrived.
    pygame then actions the notifier.
"""

def run(config={}):
#Initialize Everything
    pygame.init()
    screen = pygame.display.set_mode((768, 60))
    pygame.display.set_caption('Transcription task checker')
    pygame.mouse.set_visible(0)
#Create The Backgound
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((250, 250, 250))
#Put Text On The Background, Centered
    if pygame.font:
        font = pygame.font.Font(None, 26)
        text = font.render("Press return and wait for your tasks notifications", 1, (10, 10, 10))
        textpos = text.get_rect(centerx=background.get_width()/2)
        background.blit(text, textpos)
#Display The Background
    screen.blit(background, (0, 0))
    pygame.display.flip()
#Prepare Game Objects
    clock = pygame.time.Clock()

    pygameData={}
    pygameData['clock'] = clock
    pygameData['screen'] = screen
    pygameData['background'] = background

#APPLICATION CONTROL LOGIC
    nf = myNote(config, pygameData=pygameData)
    timeStart = getRootString()
    nf.outputResults('%(TIME)s -> Program running'%{'TIME':timeStart})

#    from dict.bin.testData import testData
#    myTestData = testData()
#    myTestData.start()

    obj = searchWebSites(config, nf)
#    result = obj.start()

#    myQueue = Queue.Queue()
#    myTime = myTimer(1,myQueue)
#    myTime.start()
    nf.start()

#Main Loop
    while 1:
        try:
            clock.tick(10)
#            timerEvent = myQueue.get()
        except:
            time.sleep(1)

#Handle Input Events
        for event in pygame.event.get():
            if event.type == QUIT:
                break
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                break
            elif event.type == MOUSEBUTTONDOWN:
                pass

#Draw Everything
        screen.blit(background, (0, 0))
        pygame.display.flip()


            
    """ Wait for all except the notifier threads to terminate... """
    obj.terminate()
    obj.join()
#    myTime.terminate()
#    myTime.join()
    
    timeEnd = getRootString()
    nf.outputResults('Program end time: %(TIME)s...'%{'TIME':timeEnd},playSound=True,sound=config.options.get("soundsEnding"))
    time.sleep(5)
    nf.terminate()

    """ Now wait for the notifier thread to terminate then exit the program. """
    nf.join()

    raw_input('Press any key to exit this program.')
if __name__ == "__main__":
    run()
