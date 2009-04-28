import threading
import time

class EventQueue(threading.Thread):
    """
    EventQueue processes events (functions with arguments) added to a its internal queue.
    Processing may be paused, resumed and replayed.

    self.exit() must be called to terminate execution, otherwise program will hang
    on exit.
    """
    def __init__(self, finished_queue_callback=None):
        # must call parent's constructor explicitly
        threading.Thread.__init__(self)
        
        # When finish processing queue, callback will be called.
        # Only called when queue is filled with items and all items are processed.
        # If queue is finished and refilled, callback will be called again.
        self.finished_queue_callback=finished_queue_callback
        
        # list of events, which are triples containing function, args and kwargs
        # events are never removed from queue
        self.queue = []
        # place in queue
        # @invariant: 0 <= self.index <= len(self.queue)
        self.index = 0
        # pause between no-ops so thread doesn't spin its wheels
        self.nap_time = .2
        # keeps track of paused or running state
        self.running = False
        # keeps track of alive or exit state
        self.exiting = False
    
    def reset(self):
        """
        Reset instance to state immediately following construction
        """
        self.queue = []
        self.index = 0
        self.nap_time = .2
        self.running = False
        self.exiting = False

    def add(self, function, *args, **kwargs):
        '''
        Queue the call to function.
        @param function: function to call
        @param args: ordered arguments for function
        @param kwargs: named arguments for function
        
        For example, to add a call to the following function
            def foo( name, age, is_human=True )
        one would call add like so:
            add( foo, 'diN0bot', 22, is_human=False )
        '''
        self.queue.append( (function, args, kwargs) )
    
    def pause(self):
        """
        Stops event processing, but does not exit. Use self.resume() to 
        resume event processing.
        """
        self.running = False
    
    def go(self):
        """
        Resumes event processing.
        """
        self.running = True
    
    def backup(self):
        """
        Backs up by one event.
        If alrady at beginning, nothing happens.
        """
        self.index -= 1
        if self.index < 0:
            self.index = 0
    
    def exit(self):
        """
        Exits the thread as soon as the current call returns, possibly 
        preventing some calls from being executed.
        """
        self.exiting = True
    
    def has_work(self):
        """
        Returns True if has events to process, False otherwise.
        Does not check running or exiting state.
        """
        return self.index < len(self.queue)

    def run(self):
        """
        a blocking loop which continually processes events in the queue
        """
        done_work = False
        while not self.exiting:
            # take a nap if paused or has no events to process
            # otherwise process next event
            if self.running and self.has_work():
                done_work = True
                function, args, kwargs = self.queue[self.index]
                self.index += 1
                
                # process event!
                function(*args, **kwargs)
                
                # @TODO error handling. should bounce back to controller and gui
                #try:
                #    function(*a, **kw)
                #except Exception, error:
                #    self.error(error, function, a, kw)
            else:
                if done_work and not self.has_work() and self.finished_queue_callback:
                    self.finished_queue_callback()
                    done_work = False
                time.sleep(self.nap_time)
                
        sys.exit(0)
