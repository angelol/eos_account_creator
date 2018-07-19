import sys, traceback, time
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

class ConsoleExceptionMiddleware:
    def process_exception(self, request, exception):
        exc_info = sys.exc_info()
        print ("######################## Exception #############################")
        print ('\n'.join(traceback.format_exception(*(exc_info or sys.exc_info()))))
        print ("################################################################")

class TimeRequestsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.begin = time.time()
        return None

    def process_response(self, request, response):
        end = time.time()
        if hasattr(request, 'begin'):
            duration = end - request.begin

            time_taken = sum(float(q['time']) for q in connection.queries) * 1000
            print ('%s %s took %.0f ms and %s queries. Time spent in SQL: %s ms' % (request.method, request.get_full_path(), duration*1000, len(connection.queries), time_taken))
                
        return response
        
class MyMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Cache-Control'] = "no-cache, max-age=0, must-revalidate, no-store"
        return response
        
