from pathlib import Path
from .crawler.file_walker import FileWalker
from .crawler.ignore_filter import IgnoreFilter
from .database.schema import initialise
from .index.index_manager import IndexManager
from .models import IndexReport
from .parser.file_parser import FileParser

import multiprocessing
import threading

"""
Producer process: continuously reads paths from the paths_queue
parses them using the provided parser,and puts the result in results_queue. 
"""

"""
Thea idea is that we use two buffers: paths_queue where we store the raw paths found at indexing
and the results_queue that contains the parsed FileEntry dataclasses. Also to signal the consumer to stop
we use a sentinel, in our case a None.
"""
def producer_function(paths_queue: multiprocessing.Queue, results_queue: multiprocessing.Queue, parser: FileParser):
    #infinite loop to spawn exactly how many processes for the producer as we want
    #without this we would have an overhead for generating a process for every file
    while True:
        #get the file path from the queue
        file_path = paths_queue.get()
        if file_path is None:  #if we found a sentinel "None"
            results_queue.put(None)  #signal consumer that this producer is done
            break
        try:
            #use this try/except block in order to not terminate the process if there is an error
            #and never reach the sentinel, in this case the Consumer would just wait forever
            parsed_file_entry = parser.parse(file_path) #parse the file
            if parsed_file_entry  is not None:
                 results_queue.put(parsed_file_entry )#put it in the results queue
        except Exception as e:
            results_queue.put(e)
#put this function in here so it does not interfere with the same naming conventions inside the Indexer class

class Indexer:

    def __init__(
        self,
        db_path: str,
        ignore_patterns: list[str],
        walker: FileWalker | None = None,
        parser: FileParser | None = None,
        manager: IndexManager | None = None,
    ) -> None:
        self._db_path = db_path
        ignore_filter = IgnoreFilter(ignore_patterns)
        self._walker = walker or FileWalker(ignore_filter)
        self._parser = parser or FileParser()
        self._manager = manager or IndexManager(db_path)

    def run(self, root: Path, num_processes: int = 4) -> IndexReport:
        initialise(self._db_path)

        report = IndexReport()
        indexed_paths: set[str] = set()

        #bound the paths queue so we do not load a lot of paths into memory at once
        paths_queue = multiprocessing.Queue(maxsize=num_processes * 4)
        results_queue = multiprocessing.Queue()

        #start the producers processes
        producers = [] #track all the producers
        #loop through how many processes we give from the user input
        for _ in range(num_processes):
            #create the given producer process with its given function and the args of the function
            p = multiprocessing.Process(target=producer_function,args=(paths_queue, results_queue, self._parser))
            p.start() #start it
            producers.append(p)

        #start the consumer thread
        #we can use a thread for the consumer because it's safer for writing in the database
        #it is also not CPU I/O bounded and we might want to add multiple producers then, the db would crash
        def consumer_function():
            active_producers = num_processes #create a copy
            while active_producers > 0:
                parsed_file_entry = results_queue.get() #get the file entry from the result queue
                if parsed_file_entry is None: #if we hit a sentinel decrease the number of active producers
                    active_producers -= 1
                    continue

                #when a producer crashes it pushed an exception into the queue so we put it as an error and the file parser will skip it
                if isinstance(parsed_file_entry, Exception):
                    report.add("error") #we add it to the report indexer as an error
                else:
                    indexed_paths.add(parsed_file_entry.path) #add the parsed good path into the set
                    try:
                        self._manager.process(parsed_file_entry, report)#then process it to perfrom DB operations
                    except Exception:
                        report.add("error")

        #the thread will be daemon in order to finish once the main program has stopped as well
        #useful when we want to terminate the program, because otherwise the Consumer might run in the background without noticing
        consumer = threading.Thread(target=consumer_function, daemon=True)
        consumer.start()

        #put the paths into the queue
        for file_path in self._walker.walk(root):
            paths_queue.put(file_path)

        #after we finished the indexing process tell the producers to push some sentinels into the queue
        #so we know to finish the program -> we push exactly the nr of processes we give
        for _ in range(num_processes):
            paths_queue.put(None)

        #wait for the producers to finish
        for p in producers:
            p.join()

        #wait for the consumer to finish
        consumer.join()

        self._manager.delete_stale(indexed_paths, report)

        return report
