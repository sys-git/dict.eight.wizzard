
from Queue import Empty
from threading import Thread
import Queue
import Skype4Py
import sys
import time

# Here we define a set of call statuses that indicate a call has been either aborted or finished
CallIsFinished = set ([Skype4Py.clsFailed, Skype4Py.clsFinished, Skype4Py.clsMissed, Skype4Py.clsRefused, Skype4Py.clsBusy, Skype4Py.clsCancelled]);

""" A thread class to login to and parse the secure web page, notifying the user when necessary. """
class SkypeNotifier(Thread):
    def __init__(self, skypeTargetName, skypeTargetType, enableDebug=False, testData=None):
        #    Set defaults:
        self.__initDefaults()
        #    Copy in params:
        self.__enableDebug = enableDebug
        self.__testData = testData
        self.__targetName = skypeTargetName
        self.__targetType = skypeTargetType
        super(SkypeNotifier, self).__init__()
        self.setDaemon(True)
        self.start()
    def __initDefaults(self):
        self.__log = []
        #    TODO Set initial defaults:
        # This variable will get its actual value in OnCall handler
        self.__callStatus = 0
        self.__myCall = None
        self.__myChat = None
        self.__cancel = False
        self.__queue = Queue.Queue()
    def __AttachmentStatusText(self, status):
        return self.__skypeInstance.Convert.AttachmentStatusToText(status)
    def __CallStatusText(self, status):
        return self.__skypeInstance.Convert.CallStatusToText(status)
    def __OnCall(self, call, status):
        '''    This handler is fired when status of Call object has changed    '''
        self.__callStatus = status
        if self.__enableDebug==True:
            print 'Call status: ' + self.__CallStatusText(status)
        self.__queue.put_nowait(self.__CallStatusText(status))
    # This handler is fired when Skype attatchment status changes
    def __OnAttach(self, status):
        if self.__enableDebug==True:
            print 'API attachment status: ' + self.__AttachmentStatusText(status)
        if status == Skype4Py.apiAttachAvailable:
            self.__skypeInstance.Attach()
    def __init(self):
        self.__skypeInstance = Skype4Py.Skype()
        self.__skypeInstance.OnAttachmentStatus = self.__OnAttach
        self.__skypeInstance.OnCallStatus = self.__OnCall
        # Starting Skype if it's not running already..
        if not self.__skypeInstance.Client.IsRunning:
            if self.__enableDebug==True:
                print 'Starting Skype..'
            self.__skypeInstance.Client.Start()
        # Attaching to Skype..
        if self.__enableDebug==True:
            print 'Connecting to Skype..'
        self.__skypeInstance.Attach()
    def START(self):
        Found = False
        #    End the existing call...
        if self.__myCall:
            self.END()
        if self.__myChat:
            self.endChat()
        for F in self.__skypeInstance.Friends:
            if F.Handle == self.__targetName:
                Found = True
                if self.__enableDebug==True:
                    print 'Calling ' + F.Handle + '..'
                if self.__targetType=='call':
                    self.__call()
                else:
                    #    TODO chat!
                    self.__chat()
                break
        return Found
    def __call(self):
        self.__myCall = self.__skypeInstance.PlaceCall(self.__targetName)
    def __chat(self):
        self.__myChat = self.__skypeInstance.CreateChatWith(self.__targetName)
    def sendMessage(self, message):
        '''    Used to notify the user of something!    '''
        if self.__myChat:
            try:
                self.__myChat.SendMessage(message)
            except:
                print'Failed to send the message over skype!'
        else:
            #    'call' and therefore don't care!
            pass
    def END(self):
        if self.__targetType=='call':
            try:
                try:
                    self.__myCall.Finish()
                    if self.__enableDebug:
                        print 'Call to ' + self.__targetName + ' finished !'
                except:
                    print 'Failed to finish call - is it finished already ?!!'
            finally:
                self.__myCall = None
        else:
            #    'chat':
            self.__myChat.Leave()
    def run(self):
        '''    Thread termination indicates a ended call.    '''
        self.__init()
        while self.__cancel == False:
            try:
                msg = self.__queue.get(block=True, timeout=0.1)
            except Empty, _e:
                continue
            if msg:
                if msg=='Cancelled':
                    if self.__targetType=='call':
                        if self.__myCall:
                            if self.__callStatus in CallIsFinished:
                                self.__cancel = True
                    else:
                        #    'chat'.
                        if self.__myChat:
                            self.__cancel = True
        return
    def waitUntilEndOfCall(self):
        '''    Loop until CallStatus gets one of "call terminated" values in OnCall handler.    '''
        if self.__targetType=='call':
            if self.__myCall:
                self.join()
        else:
            #    'chat'.
            if self.__myChat:
                self.__myChat.Leave()

def testSkype(name, type_):
    # Creating Skype object and assigning event handlers..
    s = SkypeNotifier(name, type_, enableDebug=True)
    
    # Checking if what we got from command line parameter is present in our contact list
    Found = s.START()
    
    if not Found:
        print 'Call target not found in contact list'
        sys.exit()

    s.sendMessage('Hello Mum !')

    # Loop until CallStatus gets one of "call terminated" values in OnCall handler
    if type_=='call':
        s.waitUntilEndOfCall()
    else:
        time.sleep(5)
    s.END()
    print 'Finished test!'

if __name__ == "__main__":
#    testSkype('francishorsmantest', 'call')
    testSkype('francishorsmantest', 'chat')
    raw_input('Press any key to exit this program.')

