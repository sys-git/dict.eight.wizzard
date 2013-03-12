import traceback
import os
import Queue
import pygame
from threading import Thread
from dict.bin.playFile import myCustomNotifier
r"""
    TODO

    move processArgs() into ConfigLoader.




"""

#
#   4 OPTIONS TO MODIFY + SKYPE OPTIONS TO MODIFY >>>
#

""" This is how often (in seconds) the logged in web page is reloaded: between 5 seconds and 1 hour. """
DEFAULT_REFRESH_PERIOD = 10

"""
    Change to <True> to disable adaptive sound - so get a beep every 'DEFAULT_REFRESH_PERIOD'
        if tasks are available (none to be completed):
"""
DISABLE_ADAPTIVE_SOUND = False

""" Change to <True> to kill the sound """
NO_SOUND_ON_EVENT = False

""" Change to <False> to only notify - no downloading! """
DOWNLOAD_AND_ORDER_TASKS = True

""" Skype options to change: """
SKYPE_NOTIFIER = "True"
#    'call' / 'chat'.
SKYPE_TYPE = 'call'
SKYPE_CALLEE = 'skypeTargetName'
USE_SKYPE_THREASHOLD = "False"
#    1 MByte in bytes (1024*1024):
SKYPE_THREASHOLD = 1048576

#
#   <<< ONLY OPTIONS TO MODIFY:
#
#

""" Standard import modules: """
""" My import modules: """
from mechanize import Browser
#from dict.bin.playFile import *
from dict.bin.FileCodec import decode
from dict.bin.SkypeNotifier import SkypeNotifier
#from types import *
import sys
import time
import shutil

""" Default values for various things: """
#    Sounds:
SOUND__ERROR_FILE__DOT_WAV = 'bin/error.wav'
SOUND__NEW_TASK = 'bin/new_task.wav'
SOUND__PROGRAM_RUNNING = 'bin/running.wav'
SOUND__PROGRAM_ENDING = 'bin/ending.wav'
PLAY_SOUND__PROGRAM_ENDING = 'True'

#    Logs:
DEFAULT_ERROR_FILENAME = 'logs/error.txt'
DEFAULT_HISTORY_FILENAME = 'logs/history.txt'

#    Misc:
DEFAULT_BOMB_OUT = True
DEFAULT_SINGLE_REFRESH = 0
DEFAULT_MINIMUM_REFRESH_PERIOD = 7
DEFAULT_MAXIMUM_REFRESH_PERIOD = 3600
DEFAULT_MECHANIZER_DEBUG = 'False'
DEFAULT_ARGUMENT_DELIMETER = '='
DEFAULT_ARGUMENT_COMMENT = '#'

#    Internal dictionary keys
DICT_KEY__AVAILABLE = 'Available'
DICT_KEY__TO_COMPLETE = 'To complete'

#    Task specific:
DEFAULT_FILE_EXTENSION = '.wma'
DEFAULT_NOTIFICATION_SEPERATOR = '\n\n'
DEFAULT_LOGIN_RETRY_TIMEOUT = '60'
DEFAULT_FALLBACK_DELAY = '1000'
DEFAULT_PYGAME_LOOP_TICK = '100'
DEFAULT_PYGAME_FPS = '60'

#    File and directory locations:
DEFAULT_TASK_CACHE_DIR = 'files/cache/'
DEFAULT_TASK_TRANSCRIPTION_DIR = 'files/transcribing/'
DEFAULT_TASK_ARCHIVE_DIR = 'files/archive/'
DEFAULT_COMMS_IN = 'comms/in/'
DEFAULT_COMMS_OUT = 'comms/out/'

#    UI Command communications:
DEFAULT_TRANSCRIPTION_UPLOAD_FILE = 'upload'
DEFAULT_TRANSCRIPTION_REQUEST_FILE = 'request'
DEFAULT_TRANSCRIPTION_REQUEST_COMMAND = 'command'
DEFAULT_TRANSCRIPTION_RESPONSE_FILE = 'response'

#    Config file specific:
DEFAULT_PASSWORD = ''
DEFAULT_TRANSCRIBE_FILE = 'False'
DEFAULT_TRANSCRIBE_FILE_METHOD = 'new'

""" Testing parameters: """
IN_DEBUG_MODE = False

DEFUALT_TEST_WEB_PAGE = False
TEST_DATA1 = 'logged in as SOMEONE,\nNo tasks available.'
TEST_DATA2 = 'logged in as SOMEONE,\nTranscripts available\nselect task\nradio<123456>&nbsp;123456</td>'
TEST_DATA3 = 'logged in as SOMEONE,\nTranscripts available\nselect task\nradio<987654>&nbsp;987654</td>\nradio<999999>&nbsp;999999</td>'
TEST_DATA4 = 'logged in as SOMEONE,\nTranscripts available\n>Task 123456 must be completed first!\nselect task\n\nradio<255157>&nbsp;255157</td>'
TEST_DATA5 = 'logged in as SOMEONE,\nTranscripts available\n>Task 999999 must be completed first!\nselect task\nradio<123456>&nbsp;123456</td>\nradio<987654>&nbsp;987654</td>'
TEST_DATA6 = 'logged in as SOMEONE,\nTranscripts available\nselect task\nradio<123456>&nbsp;123456</td>\nradio<777777>&nbsp;777777</td>'
TEST_DATA = TEST_DATA3
SCENARIO__NO_TASKS = 'Tasks=0'
SCENARIO__ONE_TASK_AVAILABLE = 'Tasks=1'
SCENARIO__TWO_TASKS_AVAILABLE = 'Tasks=2'
SCENARIO__COMPLETE_ONE_TASK_AND_ONE_TASKS_AVAILABLE = 'Complete=1,Tasks=1'
SCENARIO__COMPLETE_ONE_TASK_AND_TWO_TASKS_AVAILABLE = 'Complete=1,Tasks=2'
SCENARIO__ALPHA = 'Alpha' # 1.3.5.4.6.1
DEFAULT_TEST_SCENARIO = SCENARIO__ALPHA
TEST_ORDERED_TASKS = False

""" A test class for providing data to test the mechanizer. """
class testData(Thread):
    def __init__(self,debugEnabled=False,scenario=SCENARIO__NO_TASKS):
        self.__cancel = False
        self.__debugEnabled = debugEnabled
        self.__scenario = scenario
        self.__testData = {}
        self.__testData['index'] = 0
        self.__lastData = None
        self.__queue = Queue.Queue()
        super(testData, self).__init__()
        return

    def __getNoTasks(self):
        data = TEST_DATA1
        return data

    def __getOneTaskAvailable(self):
        data = TEST_DATA2
        return data

    def __getTwoTaskAvailable(self):
        data = TEST_DATA3
        return data

    def __getCompleteOneTaskAndOneTaskAvailable(self):
        data = TEST_DATA4
        return data

    def __getCompleteOneTaskAndTwoTaskAvailable(self):
        data = TEST_DATA5
        return data

    def __getAlpha(self):
        data = None
        while data == None:
            if self.__testData['index'] == 0:
                data = TEST_DATA1
            elif self.__testData['index'] == 1:
                data = TEST_DATA3
            elif self.__testData['index'] == 2:
                data = TEST_DATA5
            elif self.__testData['index'] == 3:
                data = TEST_DATA4
            elif self.__testData['index'] == 4:
                data = TEST_DATA6
            elif self.__testData['index'] == 5:
                data = TEST_DATA1
            else:
                self.__testData['index'] = 0
        return data

    def __getUNKNOWN(self):
        data = None
        if self.__testData['index'] == 0:
            data = TEST_DATA1
        elif self.__testData['index'] == 1:
            data = TEST_DATA2
        elif self.__testData['index'] == 2:
            data = TEST_DATA3
        return data

    def _print(self,data,important=False):
        if (self.__debugEnabled==True) and (data and len(data)>0) or (important==True):
            print data
        return

    def get(self):
        """ Get the next set of data to be returned from the web site. """
        data = None

        """ Do our funky stuff depending on the current scenario and it's data. """
        if self.__scenario == SCENARIO__NO_TASKS:
            data = self.__getNoTasks()
        elif self.__scenario == SCENARIO__ONE_TASK_AVAILABLE:
            data = self.__getOneTaskAvailable()
        elif self.__scenario == SCENARIO__TWO_TASKS_AVAILABLE:
            data = self.__getTwoTaskAvailable()
        elif self.__scenario == SCENARIO__COMPLETE_ONE_TASK_AND_ONE_TASKS_AVAILABLE:
            data = self.__getCompleteOneTaskAndOneTaskAvailable()
        elif self.__scenario == SCENARIO__COMPLETE_ONE_TASK_AND_TWO_TASKS_AVAILABLE:
            data = self.__getCompleteOneTaskAndTwoTaskAvailable()
        elif self.__scenario == SCENARIO__ALPHA:
            data = self.__getAlpha()

        """ Keep a record of what we've returned. """
        self.__lastData = data

        """ Increment the scenario index. """
        self.__testData['index'] += 1
        
        self._print('Got Data: %(DATA)s.'%{'DATA':data},important=False)
        return data

    def put(self,msg):
        """ Post an event to the threads internal message queue """
        self.__putMessage(msg)
        return
        
    def run(self):
        """ Overridden Threads' run method to do the actual work. """
        while self.__cancel == False:
            msg = self.__getMessage()
            if msg and (self.__cancel == False):
                self.__processInternalMessage(msg)
        return

    def terminate(self):
        """ Method to allow for timer termination after the next timer event. """
        self.__cancel = True
        return

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
        #    self._print('myCustomNotifier:__putMessage() - ...')
        if self.__queue:
            if nowait == True:
                self.__queue.put_nowait(msg)
            else:
                self.__queue.put(msg)
        #    self._print('myCustomNotifier:__putMessage() - OK.')
        return

    def __processInternalMessage(self,msg):
        """ ToDo - override this method to allow dynamic changing of test data. """
        return
    
""" basic common method for getting the initial output string. """
def getRootString(data=None):
    if IN_DEBUG_MODE == True:
        return time.strftime("%H:%M:%S (%d %b %Y - %a)", time.gmtime())
    else:
        return time.strftime("%H:%M (%d %b %Y - %a)", time.gmtime())

""" Derived class for notifying the user of events. """
class myNote(myCustomNotifier):
    def __init__(self,filename=None,historyFilename='history.txt',enableDebug=True):
        """ Call the base-class's __init__() method. """
        myCustomNotifier.__init__(self,filename,historyFilename,enableDebug)
        self.__latestTasks = {DICT_KEY__AVAILABLE:[],DICT_KEY__TO_COMPLETE:[]}
        return

    def _outputResults_determineSoundAction(self,data,taskList):
        """ Overridden method to determine if we need to play a sound or not. """
        playSound = False
        
        if DISABLE_ADAPTIVE_SOUND == False:
            if taskList:
                if taskList[DICT_KEY__TO_COMPLETE] == None:
                    if len(taskList[DICT_KEY__AVAILABLE])>0:
                        if self.__findNewTasks(taskList,self.__latestTasks) == True:
                            """ Only ever play a sound IF we don't need to complete any first! """
                            playSound = True
                    self.__latestTasks[DICT_KEY__AVAILABLE] = taskList[DICT_KEY__AVAILABLE]
                self.__latestTasks[DICT_KEY__TO_COMPLETE] = taskList[DICT_KEY__TO_COMPLETE]
            else:
                """ Play the given sound. """
                playSound = True
        if NO_SOUND_ON_EVENT == False:
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
            for anItem in new[DICT_KEY__AVAILABLE]:
                if self.__listItemExist(anItem,old[DICT_KEY__AVAILABLE]) == False:
                    return True
        return False

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
        super(myTimer, self).__init__()
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
    def __init__(self,opts,enableDebug=False,notifier=None,skypeNotifier=None,testData=None):
        #    Set defaults:
        self.__initDefaults()

        #    Copy in params:
        self.__enableDebug = enableDebug
        self.__notifier = notifier
        self.__skypeNotifier = skypeNotifier
        self.__testData = testData
        
        #    Copy in overriding params:
        self.__applyConfiguration(opts)
        super(searchWebSites, self).__init__()

    def __initDefaults(self):
        self.__log = []
        #    Set initial defaults:
        self.__httpsRefreshMin = DEFAULT_MINIMUM_REFRESH_PERIOD
        self.__httpsRefreshMax = DEFAULT_MAXIMUM_REFRESH_PERIOD
        self.__httpsRefresh = DEFAULT_REFRESH_PERIOD
        self.__loginErrorCount = 0
        self.__cancel = False
        self.__host = ""
        self.__username = ""
        self.__password = ""
        self.__fileExtension = DEFAULT_FILE_EXTENSION
        self.__downloadDir = "http://www.google.com"
        self.__notification_seperator = DEFAULT_NOTIFICATION_SEPERATOR
        self.__loginRetryTimeout = DEFAULT_LOGIN_RETRY_TIMEOUT
        self.__fallbackDelay = DEFAULT_FALLBACK_DELAY
        self.__taskCacheDir = DEFAULT_TASK_CACHE_DIR
        self.__taskTranscriptionDir = DEFAULT_TASK_TRANSCRIPTION_DIR
        self.__taskArchiveDir = DEFAULT_TASK_ARCHIVE_DIR
        self.__commsInDir = DEFAULT_COMMS_IN
        self.__commsOutDir = DEFAULT_COMMS_OUT
        self.__transcribeFile = DEFAULT_TRANSCRIBE_FILE
        self.__transcribeFileMethod = DEFAULT_TRANSCRIBE_FILE_METHOD

    def __applyConfiguration(self, opts):
        if opts:
            self.log('Applying configuration'+dumpConfiguration(opts), important=True)
            #    Override configuration params:
            keys = opts.keys()

            if 'page_refresh' in keys:
                self.__httpsRefresh = int(opts['page_refresh'])
            if 'host' in keys:
                self.__host = opts['host']
            if 'username' in keys:
                self.__username = opts['username']
            if 'password' in keys:
                self.__password = opts['password']
            if 'file_extension' in keys:
                self.__fileExtension = opts['file_extension']
            if 'download_directory' in keys:
                self.__downloadDir = opts['download_directory']
            if 'notification_seperator' in keys:
                self.__notification_seperator = opts['notification_seperator']
            if 'login_retry' in keys:
                self.__loginRetryTimeout = int(opts['login_retry_timeout'])
            if 'login_retry' in keys:
                self.__fallbackDelay = int(opts['fallback_delay'])
            if 'pygame_loop_tick' in keys:
                self.__pygameLoopTick = int(opts['pygame_loop_tick'])
            if 'task_cache_dir' in keys:
                self.__taskCacheDir = opts['task_cache_dir']
            if 'task_transcription_dir' in keys:
                self.__taskTranscriptionDir = opts['task_transcription_dir']
            if 'task_archive_dir' in keys:
                self.__taskArchiveDir = opts['task_archive_dir']
            if 'comms_in' in keys:
                self.__commsInDir = opts['comms_in']
            if 'comms_out' in keys:
                self.__commsOutDir = opts['comms_out']
            if 'transcribe_file' in keys:
                self.__transcribeFile = self.getBoolean(opts['transcribe_file'])
            if 'transcribe_file_method' in keys:
                self.__transcribeFileMethod = self.getBoolean(opts['transcribe_file_method'])

    def getBoolean(self, value):
        # TODO FIXME Do this!
        return value

    def log(self, txt, important=False):
        self._print(txt, important)
        self.__log.append(txt)

    def terminate(self):
        """ Method to allow for thread termination after the next run loop. """
        self.__cancel = True

    def _bombOut(self,text,Fatal=DEFAULT_BOMB_OUT):
        """ Provide a dump report and optionally bomb out on the given error. """
        self.log('Bombing out:\n'+text)
        
        traceback.print_exc()
        if Fatal and Fatal == True:
            if text and len(text) > 0:
                sys.exit(text)
            else:
                sys.exit('mechaniser Bombing out for unknown reason !!!')

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

    def _parseWebPage(self, browser, data):
        """ The basic logic to parse the html returned when we've logged into the secure login page. """
        self.log('parsing web page: '+data)
        
        if TEST_ORDERED_TASKS==True:
            tmp1 = {}
            tmp1[DICT_KEY__AVAILABLE] = [1035486, 1035487, 1035488, 1035489, 1035490]
            tmp1[DICT_KEY__TO_COMPLETE] = None
            self.__gotTasks(browser, 'test !', False, SOUND__NEW_TASK, tmp1)
            self.__checkForTranscribeRequest(browser)
        
        error = False
        if data:
            myTaskList = {}
            myTaskList[DICT_KEY__AVAILABLE] = []
            myTaskList[DICT_KEY__TO_COMPLETE] = None
            dataLines = data.splitlines()
            rootName = getRootString()
            if data.lower().find('logged in as') != -1:
                if data.find('No tasks available') != -1:
                    rootName += ' -> No tasks.'
                    if self.__notifier:
                        self.__notifier.outputResults(rootName,playSound=False)
                else:
                    playSound = False
                    taskToComplete = None
                    for aLine in dataLines:
                        if aLine.lower().find('must be completed first') != -1:
                            pre,_,post = aLine.lower().partition('must be completed first')
                            pre,_,post = pre.lower().partition('>task ')
                            if len(post)>0:
                                taskToComplete = post.strip()
                                myTaskList[DICT_KEY__TO_COMPLETE] = taskToComplete
                    if data.lower().find('select task') != -1:
#                        count = data.count('radio')
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
                                myTaskList[DICT_KEY__AVAILABLE].append(aTask)
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
                                    myTaskList[DICT_KEY__AVAILABLE].append(aTask)
                                rootName = rootName[:-1]
                        rootName = DEFAULT_NOTIFICATION_SEPERATOR + rootName
                        rootName += DEFAULT_NOTIFICATION_SEPERATOR
                        
                        """ Download the tasks and notify the user as appropriate. """
                        self.__gotTasks(browser, rootName, playSound, SOUND__NEW_TASK, myTaskList)
                    else:
                        rootName += ' -> To complete: - '
                        rootName += '%(TASK)s.'%{'TASK':taskToComplete}
                        rootName += DEFAULT_NOTIFICATION_SEPERATOR + rootName
                        rootName += DEFAULT_NOTIFICATION_SEPERATOR
                        if self.__notifier:
                            self.__notifier.outputResults(rootName,playSound=False,taskList=myTaskList)
                """ Now move all files which are not available into the archive dir. """
                self.__archiveUnavailableFiles(myTaskList)
            else:
                rootName += ' -> ERROR: - Unable to parse web page - happens every other refresh!'
                if self.__notifier:
                    self.__notifier.outputResults(rootName,playSound=True,sound=SOUND__ERROR_FILE__DOT_WAV)
                error = True
                print data
        return error

    def __gotTasks(self, browser, rootName, playSound, sound, myTaskList):
        if self.__notifier:
            self.__notifier.outputResults(rootName,playSound=playSound,sound=SOUND__NEW_TASK,taskList=myTaskList)

        if DOWNLOAD_AND_ORDER_TASKS==True:
            """ Can only download tasks when there are non <To complete>! """
            if (not myTaskList[DICT_KEY__TO_COMPLETE]) or (len(myTaskList[DICT_KEY__TO_COMPLETE])==0):
                """    Now download the available tasks to our cache. """
                orderedTaskList = self.__downloadTasksAndOrder(browser, myTaskList)
        
                if (len(myTaskList[DICT_KEY__AVAILABLE])>0):
                    rootName = 'Ordered Tasks (Largest 1st): ' + rootName
                    #    Notify the user via sound and stdout:
                    self.__notifyNormal(rootName, orderedTaskList)
                    #    Notify the user via Skype:
                    self.__notifySkype(rootName, orderedTaskList)

    def __notifyNormal(self, rootName, orderedTaskList):
        if self.__notifier:
            #    Notify the user as normal (sound has already been played if required so no point playing it again!):
            self.__notifier.outputResults(rootName, playSound=False, taskList=orderedTaskList)

    def __notifySkype(self, rootName, orderedTaskList):
        if self.__skypeNotifier:
            message = 'NEW TASK !'
            if (orderedTaskList)>1:
                message = 'NEW TASKs !'
            notify = True
            if USE_SKYPE_THREASHOLD:
                (_name, size) = orderedTaskList[0]
                if size<SKYPE_THREASHOLD:
                    notify=False
                    self._print( 'Largest file size is: ' + size + ' which doesn\'t breach the Skype notification threashold of: ' + SKYPE_THREASHOLD )
                else:
                    sz = size / (1024)
                    message = 'Task: ' + sz + ' KiloBytes !'
            if notify==True:
                try:
                    self.__skypeNotifier.START()
                    #    Send a message in case we're chatting not calling!
                    self.__skypeNotifier.sendMessage(message)
                except:
                    self._print( 'Failed to notify the user via Skype!' )
                    traceback.print_exc()

    def __downloadTasksAndOrder(self, browser, myTaskList):
        self.__downloadTasks(browser, myTaskList)

        """ Get the contents of self.__taskCacheDir as a list of IDs. """
        result = []
        for filename in os.listdir(self.__taskCacheDir):
            if filename.endswith(DEFAULT_FILE_EXTENSION):
                try:
                    path = self.__taskCacheDir + '/' + filename
                    attribs = os.stat(path)
                    size = attribs.st_size
                    result.append((filename.rstrip(DEFAULT_FILE_EXTENSION), size))
                except:
                    pass

        return self.__orderTasksBySize(result)

    def __getDownloadedTasks(self):
        """ Get all tasks from the cache. """
        taskIDs = []

        for filename in os.listdir(self.__taskCacheDir):
            if filename.endswith(DEFAULT_FILE_EXTENSION):
                taskIDs.append((filename.rstrip(DEFAULT_FILE_EXTENSION)))

        return taskIDs
    
    def __downloadTasks(self, br, myTaskList):
        downloadedAlready = self.__getDownloadedTasks()

        tasks = myTaskList[DICT_KEY__AVAILABLE]
        for aTask in tasks:
            theTaskString = ''
            theTaskString = '%(TASK)s'%{"TASK":aTask}
            ##    Download the task ?
            if theTaskString not in downloadedAlready:
                """    Follow link to download the file """
                self.log('Attempting to download file: '+theTaskString)
                downloadLink = self.__downloadDir+theTaskString
                response = br.open(downloadLink)
                fileContent = response.wrapped.fp.read()
                if fileContent:
                    self.__saveFileToCache(self.__taskCacheDir+theTaskString+DEFAULT_FILE_EXTENSION, fileContent)
                    downloadedAlready.append(theTaskString)
                
                """ Now go 'BACK' in the browser history to the logged-in page! """
                br.back()

    def __saveFileToCache(self, aTask, fileContent):
        f = None
        try:
            try:
                f = open(aTask, 'w+b')
                f.write(fileContent)
                self.log('Saved file to cache: '+aTask)
            except:
                traceback.print_exc()
        finally:
            if f:
                f.close()

    def __orderTasksBySize(self, myTaskList):
        result = []
        
        for task in myTaskList:
            result = self.__addLargestTask(task, result)
        
        tasks = []
        for aTask in result:
            tasks.append(aTask)

        return tasks
            
    def __addLargestTask(self, task, result):
        (_name, size) = task
        newResult = []
    
        if len(result)==0:
            newResult.append(task)
            return newResult
    
        addTasks = True
        for a in result:
            (_n, s) = a
            if size>s and (addTasks==True):
                newResult.append(task)
                newResult.append(a)
                ##    Now make sure we append all the rest!
                addTasks = False
            else:
                newResult.append(a)
    
        """ If the task is the smallest one, add it to the end. """
        if task not in newResult:
            newResult.append(task)
    
        return newResult

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
            self.log('Logging into website: '+hostname+':user='+username+':password='+password)
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
            self.log('Failed to log into website!')
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
            rootName += ' -> ERROR - Failed to create the timer, sleeping for 1 second and going anyway.'
            self._print(rootName,important=False)
            time.sleep(DEFAULT_FALLBACK_DELAY)
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
        self.log('Reading response from web page')
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
    
    def __checkForTranscribeUpload(self, browser):
        self.log('Checking for transcription upload requests')
        request = None
        fp = None
        try:
            try:
                filename = self.__commsInDir+DEFAULT_TRANSCRIPTION_UPLOAD_FILE
                fp = open(filename, 'r')
                request = fp.read()
            except:
                """ Don't care - nothing to do! """
                pass
        finally:
            if fp:
                fp.close()
            if request:
                """ Now remove the file! """
                os.remove(filename)
        if request:
            """ TODO FIXME Open the file with the given path and upload it !!! """
            lines = request.splitlines()
            fileIn = ''
            fileOut = ''
            for line in lines:
                if line.startswith('in')==True:
                    line = line.lstrip('in')
                    _, match, post = line.partition('=')
                    if match and post:
                        fileIn = post.strip()
                if line.startswith('out')==True:
                    line = line.lstrip('out')
                    _, match, post = line.partition('=')
                    if match and post:
                        fileOut = post.strip()
            self.log('We are told to upload the contents of the file:\n'+fileIn.strip()+'and move it to:\n'+fileOut.strip())

    def __checkForTranscribeRequest(self, browser):
        """ Check the comms/in location for commands. 
            If we successfully mark the WMA file as transcribing, move it to the transcribing dir. """
        self.log('Checking for transcription requests')
        request = None
        fp = None
        try:
            try:
                filename = self.__commsInDir+DEFAULT_TRANSCRIPTION_REQUEST_FILE
                fp = open(filename, 'r')
                request = fp.read()
            except:
                """ Don't care - nothing to do! """
                pass
        finally:
            if fp:
                fp.close()
            if request:
                """ Now remove the file! """
                os.remove(filename)

        if request:
            """ Mark the checkbox and action the file as transcribed. """
            if self.__doTranscribeFile(browser, request):
                """ Move the WMA file from the cache to the transcribing dir. """
                theRequest = request.strip()
                filename = theRequest + DEFAULT_FILE_EXTENSION
                src = self.__taskCacheDir + filename
                dest = self.__taskTranscriptionDir + filename
                
                try:
                    shutil.move(src, dest)
                except:
                    """ Failed to move the WMA file - BUT we are still transcribing it! """
                    self._print('Failed to copy the file: <'+filename+'> to the transcription dir: <'+self.__taskTranscriptionDir+'>.', True)
                
                """ Now notify the UI that the file is ready. """
                filename = self.__commsOutDir + DEFAULT_TRANSCRIPTION_RESPONSE_FILE
                fp = None
                try:
                    fp = open(filename, 'w')
                    fp.write(theRequest)
                finally:
                    if fp:
                        fp.close()
            else:
                #    Failed - Task may have been taken already, internet down etc.
                pass
    
    def __doTranscribeFile(self, browser, request):
        """ Return True if we managed to check the radio button. """
        self.log('Transcribing file: '+request)
        if self.__transcribeFileMethod=='old':
            self.__transcribeFileOriginal(browser, request)
        else:
            self.__transcribeFileALT(browser, request)
    
    def __transcribeFileOriginal(self, browser, request):
        """ Return True if we managed to check the radio button. """
        self.log('Transcribing file (original way): '+request)
        
        try:
            #    browser.select_form(name="FormName")

            for form in browser.forms():
                print form
                if form.name == 'FormName':
                    form.find_control(name="TaskID", kind="radio").value = [request]
                    result = True;
                    if self.__transcribeFile==True:
                        try:
                            self.__checkTranscribeResponse(browser.submit())
                        except:
                            #    Error occurred when processing the form action -
                            #    May be the task has been taken ?!
                            traceback.print_exc()
                            result = False
 
                        #    Now go back() and reload the page!
                        browser.back()
                    return result
        except:
            rootName = getRootString()
            rootName += ' -> ERROR - Failed to mark task <'+request+'> (original way) as transcribed!'
            self._print(rootName,important=True)
        return False
    
    def __transcribeFileALT(self, browser, request):
        """ Return True if we managed to check the radio button. """
        self.log('Transcribing file (new way): '+request)
        
        try:
            browser.select_form(name="FormName")
            
            browser.find_control(name="TaskID").value = ["request"]
            
            if self.__transcribeFile==True:
                try:
                    self.__checkTranscribeResponse(browser.submit())
                except:
                    #    Error occurred when processing the form action!
                    traceback.print_exc()
                    return False
     
                #    Now go back() and reload the page!
                browser.back()
            return True
        except:
            rootName = getRootString()
            rootName += ' -> ERROR - Failed to mark task <'+request+'> (new way) as transcribed!'
            self._print(rootName,important=True)
        return False
    
    def __checkTranscribeResponse(self, response):
        """
            TODO Check the response type is not a 403 and contains the correct data!
            If the page is not as expected, throw an exception!
        """
        self.log('Checking Transcription response: '+response)
        return True

    def __archiveUnavailableFiles(self, tasks):
        #    The cache should contain only the 'Available' tasks.
        #    All others are moved to the archive.
        taskIDs = tasks[DICT_KEY__AVAILABLE]
        activeTaskId = tasks[DICT_KEY__TO_COMPLETE]
        existingFiles = []

        for filename in os.listdir(self.__taskCacheDir):
            if filename.endswith(DEFAULT_FILE_EXTENSION):
                try:
                    existingFiles.append(filename.rstrip(DEFAULT_FILE_EXTENSION))
                except:
                    pass

        for existingFile in existingFiles:
            srcDir = self.__taskCacheDir
            if activeTaskId and (existingFile in activeTaskId):
                #    Need to move the active task into the transcribing directory - must have been actioned manually
                #    by the user on their website!
                srcDir = self.__taskTranscriptionDir

            if (existingFile not in taskIDs) or (activeTaskId and (existingFile in activeTaskId)):
                filename = existingFile + DEFAULT_FILE_EXTENSION
                src = srcDir + filename
                dest = DEFAULT_TASK_ARCHIVE_DIR + filename
                
                try:
                    shutil.move(src, dest)
                    self.log('Archived file: '+existingFile)
                except:
                    """ Failed to move the WMA file. """
                    self._print('Failed to copy the file: <'+filename+'> from the transcription dir: <'+self.__taskTranscriptionDir+'> to the archive dir: <'+DEFAULT_TASK_ARCHIVE_DIR+'>.', True)
    
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
                error = self._parseWebPage(br, LogedInWebPageData)

                if error == True:
                    """ There was an error parsing the web page, try logging in again. """
                    return
                else:
                    """ Should we let dict8 know that we wish to transcribe a file? """
                    self.__checkForTranscribeRequest(br)

                    """ Should we upload the given transcription to dict8 ? """
                    self.__checkForTranscribeUpload(br)
                    
                    """ Set the timer going to reload the web page. """
                    self.__waitOnTimer(myDelay)
                    """ The given time has passed now. """

                    #    Now reload the web page and read it again.
                    #    Only works if we do a browser.back() after downloading one of the files!
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

    def __websiteActionOld(self,hostname,username,password):
        """ Method to perform this threads' main action. """
        br, response = self.__websiteLogin(hostname, username, password)

        if response and br:
            LogedInWebPageData = response.read()
            if DEFUALT_TEST_WEB_PAGE == True:
                self._parseWebPage(TEST_DATA[:])
            else:
                self._parseWebPage(LogedInWebPageData)
            if self.__httpsRefresh > DEFAULT_SINGLE_REFRESH:
                self.__myQueue = Queue.Queue()
                myDelay = self.__calcDelay(self.__httpsRefresh)
                watchdogTimer = myTimer(myDelay,self.__myQueue)
                watchdogTimer.start()
                errCount = 0
                while self.__cancel == False:
                    try:
                        self.__myQueue.get()
                        self._print('Watchdog timer event.')
                        response = br.reload()
                        errCount = 0
                        LogedInWebPageData = response.read()
                        if DEFUALT_TEST_WEB_PAGE == True:
                            self._parseWebPage(TEST_DATA[:])
                        else:
                            self._parseWebPage(LogedInWebPageData)
                    except:
                        self._print('oh dear!')
                        if errCount == 10:
                            rootName = getRootString()
                            rootName += " -> ERROR - Failed to reload the web page 10 times !"
                            raise 
                        errCount += 1
                        rootName = getRootString()
                        rootName += ' -> ERROR - Failed to load the web page, sleeping for 1 minute and trying again.'
                        self._print(rootName,important=True)
                        self._bombOut(rootName,Fatal=False)
                        time.sleep(60)
                watchdogTimer.terminate()
        return

    def run(self):
        """ Overridden Thread's run method to do the actual work. """
        while self.__cancel == False:
            self.__checkTermination()

            if self.__loginErrorCount == 10:
                """ Failed to login to the web page 10 times in-a-row, better wait a while and retry. """
                rootName = getRootString()
                rootName += ' -> ERROR - Failed to login to the web page 10 times in-a-row, waiting 1 minute and retrying.'
                self._print(rootName,important=True)

                """ Wait for the given time before attempting a relogin. """
                self.__waitOnTimer(DEFAULT_LOGIN_RETRY_TIMEOUT)
                self.__loginErrorCount = 0

            try:
                self.__websiteAction(self.__host,self.__username,self.__password)
            except:
                rootName = getRootString()
                rootName += ' -> ERROR - Starting again.'
                self._bombOut(rootName,Fatal=False)
        return

    def __checkTermination(self):
        (requester, terminateRequired) = self.__getTerminationRequest()
        if terminateRequired==True:
            rootName = getRootString()
            rootName += ' -> Terminating the mechanizer by request: <'+requester+'>.'
            self._bombOut(rootName,Fatal=True)

    def __getRequestCommand(self):
        request = None
        fp = None
        try:
            try:
                filename = self.__commsInDir+DEFAULT_TRANSCRIPTION_REQUEST_COMMAND
                fp = open(filename, 'r')
                request = fp.read()
            except:
                """ Don't care - nothing to do! """
                pass
        finally:
            if fp:
                fp.close()
        return request

    def __getTerminationRequest(self):
        request = self.__getRequestCommand()
        (requester, terminate) = self.__parseRequest(request, {'command':'terminate', 'arg':'requester'})
        
        if terminate==True:
            #    Delete the file from disc!
            filename = self.__commsInDir+DEFAULT_TRANSCRIPTION_REQUEST_COMMAND
            try:
                os.remove(filename)
            finally:
                self.__print('Failed to remove the command file: <'+self.__commsInDir+DEFAULT_TRANSCRIPTION_REQUEST_COMMAND+'>', important=True)
        return (requester, terminate)

    def __parseRequest(self, request, params):
        try:
            if request:
                ##    Parse the file for a command params['terminate'] with arg ['requester'].
                ##    For now, just return the terminate command!
                lines = request.splitlines()
                for line in lines:
                    line = line.strip()
                    ##    Terminate:    'terminate requester=<> reason=<>'
                    cmd = params['command']
                    _,_,post = line.partition(cmd)
                    arg = params['arg']
                    if post:
                        if arg:
                            _,_,post = post.partition(arg)
                            requester = None
                            if post:
                                requester = post.strip()
                            return (requester, True)
                        else:
                            return (None, True)
                    else:
                        #    Does the match exist on it's own?
                        if line.find(cmd)!=-1:
                            ##    Got it!
                            return (None, True)
        except:
            pass
    
        return (None, False)

def downloadTestWavFile():
    name = 'incomingmessageBGH.wav'
    link = 'http://www.dailywav.com/0409/'+name
    br = Browser()
    response = br.open(link)
    fileContent = response.wrapped.fp.read()

    f = None
    try:
        f = open('C:/tmp/'+name, 'w+b')
        f.write(fileContent)
    finally:
        if f:
            f.close()

def decryptFile(contents):
    """ 
        Decrypt file with default password: DEFAULT_PASSWORD
        TODO Edit then save the file with default password!
    """
    try:
        contents = decode(DEFAULT_PASSWORD, contents)
    except Exception, _e:
        pass
    return contents

def loadArgsFromFile(filename):
    """ Load configuration into a dictionary. """
    args = {}
    #    Now decrypt the file if applicable
    opts = decryptFile(open(filename).read())
    for line in opts.splitlines():
        line = line.strip()
        if not line.startswith(DEFAULT_ARGUMENT_COMMENT):
            pre, match, post = line.partition(DEFAULT_ARGUMENT_DELIMETER)
            if pre and match and post:
                args[pre.strip()] = post.strip()
    return args

def loadArgs():
    args = {}
    for arg in sys.argv[1:]:
        try:
            return loadArgsFromFile(arg)
        except:
            traceback.print_exc()
    return args

def processArgs():
    pygameLoopTick = DEFAULT_PYGAME_LOOP_TICK
    historyFilename = DEFAULT_HISTORY_FILENAME
    mechanizerDebug = DEFAULT_MECHANIZER_DEBUG
    pygameFps = DEFAULT_PYGAME_FPS
    soundProgrammeRunning = SOUND__PROGRAM_RUNNING
    soundProgrammeEnding = SOUND__PROGRAM_ENDING
    playSoundProgrammeEnding = PLAY_SOUND__PROGRAM_ENDING
    notifyUsingSkype = SKYPE_NOTIFIER
    skypeType = SKYPE_TYPE
    skypeTargetCallee = SKYPE_CALLEE

    #    Args contains some or all of the config we need.
    args = loadArgs()
    keys = args.keys()

    #    Set the values we must have!
    if 'pygame_loop_tick' not in keys:
        args['pygame_loop_tick'] = pygameLoopTick
    if 'history_log' not in keys:
        args['history_log'] = historyFilename
    if 'mechanizer_debug' not in keys:
        args['mechanizer_debug'] = mechanizerDebug
    if 'pygame_fps' not in keys:
        args['pygame_fps'] = pygameFps
    if 'sound_programme_running' not in keys:
        args['sound_programme_running'] = soundProgrammeRunning
    if 'sound_programme_ending' not in keys:
        args['sound_programme_ending'] = soundProgrammeEnding
    if 'play_sound_programme_ending' not in keys:
        args['play_sound_programme_ending'] = playSoundProgrammeEnding
    if 'notify_using_skype' not in keys:
        args['notify_using_skype'] = notifyUsingSkype
    if 'skype_target_type' not in keys:
        args['skype_target_type'] = skypeType
    if 'skype_target_name' not in keys:
        args['skype_target_name'] = skypeTargetCallee
    return args

def getBooleanProperty(args, name):
    if args[name]=='1' or args[name].lower()=='true':
        return True
    return False

def dumpConfiguration(d):
    txt = ''
    for key in d.keys():
        txt = txt+key+' = '+d[key]+'\n'
    return txt
    
"""
    Change program structure: New thread for getting the web page.
    Send a message to the main pygame loop in __main__ when data arrived.
    pygame then actions the notifier.
"""
def run(config):
    #    Process any args we may have
    args = processArgs()

    pygameLoopTick = int(args['pygame_loop_tick'])
    historyFile = args['history_log']
    _mechanizerDebug = args['mechanizer_debug']
    pygameFps = int(args['pygame_fps'])
    soundProgrammeRunning = args['sound_programme_running']
    soundProgrammeEnding = args['sound_programme_ending']
    playSoundProgrammeEnding = getBooleanProperty(args, 'play_sound_programme_ending')
    notifyUsingSkype = getBooleanProperty(args, 'notify_using_skype')
    skypeTargetName = args['skype_target_name']
    skypeTargetType = args['skype_target_type']
    skypeNote = None
    if notifyUsingSkype==True:
        skypeNote = SkypeNotifier(skypeTargetName, skypeTargetType, enableDebug=False)
    pygame.init()
    pygame.mixer.init()

    clock = pygame.time.Clock()
    nf = myNote(filename=soundProgrammeRunning,historyFilename=historyFile,enableDebug=False)
    if nf:
        timeStart = getRootString()
        nf.outputResults('%(TIME)s -> Program running'%{'TIME':timeStart}, playSound=True, sound=soundProgrammeRunning)

        myTestData = testData(scenario=DEFAULT_TEST_SCENARIO)

        obj = searchWebSites(args, enableDebug=False,notifier=nf,skypeNotifier=skypeNote,testData=myTestData)
        obj.start()

        myQueue = Queue.Queue()
        myTime = myTimer(1,myQueue)
        myTime.start()
        nf.start()
        while 1:
            try:
                clock.tick(pygameFps)
                _timerEvent = myQueue.get()
            except:
                time.sleep(pygameLoopTick)
            
        """ Wait for all except the notifier threads to terminate... """
        obj.terminate()
        obj.join()
        myTime.terminate()
        myTime.join()
        
        try:
            if skypeNote:
                skypeNote.END()
        except:
            print 'Failed to terminate the Skype notifier!'

        timeEnd = getRootString()
        nf.outputResults('Program end time: %(TIME)s...'%{'TIME':timeEnd},playSound=playSoundProgrammeEnding,sound=soundProgrammeEnding)
        time.sleep(5)
        nf.terminate()

        """ Now wait for the notifier thread to terminate then exit the program. """
        nf.join()

        raw_input('Press any key to exit this program.')

